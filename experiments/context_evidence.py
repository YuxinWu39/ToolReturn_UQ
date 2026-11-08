#!/usr/bin/env python3
"""A-CTX-EVIDENCE: statistical checks using only the frozen, displayed CSV rows.

No model requests. Truth is used in evaluation/sanity construction, never features.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import datetime as dt
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import platform
import subprocess

import numpy as np
import pandas as pd

from context_pilot import digest, validate_manifest
from p4_common import auc_or_none, within_table
from zeroparam import bootstrap_0d, interval_score, rule_0a, template_stat

ROOT = Path(__file__).resolve().parents[1]
CONTEXTS = ('head5', 'random20', 'matched20')
METHODS = ('0a', '0d')
THRESHOLD = 1e-9
BOOTSTRAPS = 2000
PROTOCOL_COMMIT = 'f94ffbb'


def hashfile(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n'
    tmp = p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(text)
    tmp.replace(p)


def displayed_evidence(unit):
    assert digest(unit['messages']) == unit['messages_hash']
    body = unit['messages'][1]['content']
    text = body.split('PARTIAL TABLE EVIDENCE\n', 1)[1].split('\nTOOL RESULT\n', 1)[0]
    evidence = json.loads(text)
    assert digest(evidence) == unit['context_hash']
    return evidence


def features(evidence, column, flt, task_id, context, B=BOOTSTRAPS):
    """Restricted feature API: no truth, labels, model decisions, or dataset path."""
    df = pd.read_csv(io.StringIO(evidence['rows_csv']))
    assert list(df.columns) == evidence['columns']
    matched = df[flt[0]].astype(str) == flt[1]
    target = pd.to_numeric(df.loc[matched, column], errors='coerce').to_numpy(float)
    values = target[np.isfinite(target)]
    seed = 20261107 + int(hashlib.sha256((task_id+'|'+context).encode()).hexdigest()[:8], 16)
    stat = template_stat('mean', column, flt, None)
    interval = bootstrap_0d(stat, df, evidence['shape'][0], B, np.random.default_rng(seed), scale_sum=False)
    if interval is not None and not all(math.isfinite(x) for x in interval):
        interval = None
    return {'task_id': task_id, 'context': context, 'evidence_hash': digest(evidence),
            'shown_rows': len(df), 'matching_rows': int(matched.sum()), 'finite_targets': len(values),
            'values': values.tolist(), 'sample_mean': float(values.mean()) if len(values) else None,
            'interval_0d': list(interval) if interval is not None else None,
            'displayed_table_rows': evidence['shape'][0], 'seed': seed, 'bootstrap_draws': B,
            'parsed_dtypes': {c: str(t) for c,t in df.dtypes.items()}}


def score(method, value, feat):
    if method == '0a':
        result = rule_0a('mean', value, feat['values'], feat['displayed_table_rows'])
    elif method == '0d':
        result = interval_score(value, feat['interval_0d'])
    else:
        raise ValueError(method)
    return float(result) if result is not None and math.isfinite(result) else None


def decision(value):
    if value is None or not math.isfinite(value):
        return 'unscorable'
    return 'flag' if value > THRESHOLD else 'compatible'


def events_for_query(q, context, feat):
    events = []
    for method in METHODS:
        for role, y in [('clean', q['truth']), ('corrupted', q['corrupted']),
                        ('sanity_hi', q['truth']*1000), ('sanity_lo', q['truth']/1000)]:
            value = score(method, y, feat)
            events.append({'task_id': q['task_id'], 'dataset': q['dataset'], 'context': context,
                           'severity': q['severity'], 'method': method, 'role': role, 'value': y,
                           'score': value, 'decision': decision(value), 'evidence_hash': feat['evidence_hash']})
    return events


def auc_summary(events, roles):
    """Same-task support across every requested role; missing is never a normal score."""
    subsets = {r: {e['task_id']: e for e in events if e['role']==r and e['score'] is not None} for r in roles}
    ids = set.intersection(*(set(v) for v in subsets.values()))
    data = [{**subsets[r][t], 'label': int(r!='clean')} for r in roles for t in sorted(ids)]
    frame = pd.DataFrame(data, columns=['dataset', 'label', 'score'])
    point, ci, tables = within_table(frame, 'score')
    return {'within_table': point, 'ci95': ci, 'tables': tables, 'paired_queries': len(ids),
            'pooled': auc_or_none(frame, 'label', 'score'),
            'per_table': {d: auc_or_none(x, 'label', 'score') for d,x in frame.groupby('dataset')}}


def passes_sanity(auc):
    return auc is not None and auc > .95


def summarize_cell(events, parent_gate=None):
    sanity = auc_summary(events, ('clean','sanity_hi','sanity_lo'))
    local_gate = passes_sanity(sanity['within_table'])
    gate = local_gate and parent_gate is not False
    policy = {}
    for role in ('clean','corrupted'):
        rows = [e for e in events if e['role']==role]
        policy[role] = {'n': len(rows), **{d:sum(e['decision']==d for e in rows)
                                         for d in ('flag','compatible','unscorable')}}
    detection = auc_summary(events, ('clean','corrupted')) if gate else {
        'within_table': None, 'ci95': None, 'pooled': None,
        'status': 'withheld: parent context or local sanity gate failed'}
    per_table = {}
    for dataset in sorted({e['dataset'] for e in events}):
        rows = [e for e in events if e['dataset']==dataset]
        per_table[dataset] = {'policy': {r: {d:sum(e['role']==r and e['decision']==d for e in rows)
                                           for d in ('flag','compatible','unscorable')}
                                        for r in ('clean','corrupted')},
                              'detection': auc_summary(rows, ('clean','corrupted')) if gate else None}
    return {'sanity_pass': gate, 'local_sanity_pass': local_gate,
            'parent_context_sanity_pass': parent_gate, 'sanity': sanity,
            'sanity_high_only': auc_summary(events, ('clean','sanity_hi')),
            'sanity_low_only': auc_summary(events, ('clean','sanity_lo')),
            'detection': detection, 'policy': policy,
            'policy_status': 'descriptive, sanity passed' if gate else 'gate-failed diagnostic only',
            'per_table': per_table}


def cluster_difference(records):
    by = {}
    for r in records:
        by.setdefault(r['dataset'], []).append(r['difference'])
    means = np.array([np.mean(v) for _,v in sorted(by.items())])
    if not len(means):
        return {'mean': None, 'ci95': None, 'queries': 0, 'tables': 0, 'per_table': {}}
    boots = np.random.default_rng(1).choice(means,(2000,len(means)),replace=True).mean(axis=1)
    return {'mean': float(means.mean()), 'ci95': np.quantile(boots,[.025,.975]).tolist(),
            'queries': len(records), 'tables': len(means),
            'per_table': {d: float(np.mean(v)) for d,v in by.items()}}


def model_comparison(events, model_rows, gate, valid_only=False):
    if not gate:
        return {'mean': None, 'status': 'withheld: baseline failed sanity'}
    lookup = {(r['task_id'],r['label']):r for r in model_rows}
    scores = {(r['task_id'],r['role']):r for r in events if r['role'] in ('clean','corrupted')}
    records, invalid = [], 0
    breakdown = {role: {'model':{d:0 for d in ('accept','reject','uncertain','invalid')},
                        'baseline':{d:0 for d in ('compatible','flag','unscorable')}}
                 for role in ('clean','corrupted')}
    for task in sorted({r['task_id'] for r in events}):
        a,b = scores[(task,'clean')],scores[(task,'corrupted')]
        pair = [lookup.get((task,i)) for i in (0,1)]
        if a['score'] is None or b['score'] is None or any(r is None for r in pair):
            continue
        if valid_only and not all(r['valid'] for r in pair):
            continue
        invalid += sum(not r['valid'] for r in pair)
        for role,base,model_cell in zip(('clean','corrupted'),(a,b),pair):
            breakdown[role]['baseline'][base['decision']] += 1
            breakdown[role]['model'][model_cell['decision']] += 1
        baseline = int(a['decision']=='compatible')-int(b['decision']=='compatible')
        model = int(pair[0]['decision']=='accept')-int(pair[1]['decision']=='accept')
        records.append({'task_id':task,'dataset':a['dataset'],'difference':baseline-model})
    return {**cluster_difference(records), 'invalid_model_cells':invalid,
            'common_support_decisions':breakdown,
            'scope':'compatibility policy versus prompted accept decisions, not equivalent probabilities'}


def context_comparison(events, a, b, gates):
    if not gates[a] or not gates[b]:
        return {'mean':None,'status':'withheld: at least one context failed sanity'}
    lookup = {(r['task_id'],r['context'],r['role']):r for r in events}
    records = []
    for task in sorted({r['task_id'] for r in events}):
        cells = [lookup[(task,c,r)] for c in (a,b) for r in ('clean','corrupted')]
        if any(e['score'] is None for e in cells):
            continue
        compatible = [int(e['decision']=='compatible') for e in cells]
        records.append({'dataset':cells[0]['dataset'],
                        'difference':compatible[0]-compatible[1]-compatible[2]+compatible[3]})
    return cluster_difference(records)


def summarize(events, feats, model_rows):
    methods = {}
    for method in METHODS:
        methods[method] = {}
        for context in CONTEXTS:
            sub = [e for e in events if e['method']==method and e['context']==context]
            cell = summarize_cell(sub)
            cell['per_severity'] = {s:summarize_cell([e for e in sub if e['severity']==s],
                                                     parent_gate=cell['sanity_pass'])
                                    for s in ('subtle','plausible')}
            cell['model_comparison'] = {}
            for model,rows in model_rows.items():
                rows = [r for r in rows if r['context']==context]
                cell['model_comparison'][model] = {
                    'all_model_formats':model_comparison(sub,rows,cell['sanity_pass']),
                    'valid_model_pairs':model_comparison(sub,rows,cell['sanity_pass'],True)}
            methods[method][context] = cell
    contrasts = {}
    for method in METHODS:
        sub = [e for e in events if e['method']==method and e['role'] in ('clean','corrupted')]
        gates = {c:methods[method][c]['sanity_pass'] for c in CONTEXTS}
        contrasts[method] = {a+'_minus_'+b:context_comparison(sub,a,b,gates)
                            for a,b in [('matched20','random20'),('random20','head5'),('matched20','head5')]}
    return {'protocol':'A-CTX-EVIDENCE', 'events':len(events), 'query_contexts':len(feats),
            'methods':methods, 'context_policy_contrasts':contrasts,
            'effective_samples':[{k:f[k] for k in ('task_id','context','shown_rows','matching_rows','finite_targets','sample_mean')}
                                  for f in feats],
            'limitations':['Reused selected twelve queries, six table clusters, no fresh LLM data.',
                           'Sample range/bootstrap intervals are not population guarantees.',
                           'Qwen raw responses not archived here; comparison uses scored records.',
                           'A failure of these methods does not prove information-theoretic impossibility.']}


def run(root, output, workers):
    if (output/'summary.json').exists():
        raise ValueError('This experiment already has output; do not outcome-selectively rerun')
    folder = root/'data/ours/context_pilot/20261107'
    manifest = json.loads((folder/'manifest.json').read_text())
    validate_manifest(manifest)
    assert digest(manifest)=='7263b5dcd25ccf3c4463ffe6778243a3f953a153c55f0c493d9714cd0dc99983'
    config = {'protocol_commit':PROTOCOL_COMMIT,
              'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
              'manifest_hash':digest(manifest), 'bootstrap_draws':BOOTSTRAPS, 'threshold':THRESHOLD,
              'source_hashes':{n:hashfile(root/'experiments'/n) for n in
                               ('context_evidence.py','zeroparam.py','p4_common.py','context_pilot.py')},
              'versions':{'python':platform.python_version(),**{p:importlib.metadata.version(p)
                                                            for p in ('numpy','pandas','scikit-learn')}},
              'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'model_scored_hashes':{n:hashfile(folder/n/'scored_responses.json')
                                     for n in ('gemini-3.8-flash','qwen3-8b')}}
    save(output/'config.json',config)
    clean = {(u['task_id'],u['context']):u for u in manifest['units'] if u['label']==0}
    queries = {q['task_id']:q for q in manifest['selected_queries']}
    futures, feats = {}, []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for (task,context),u in clean.items():
            q = queries[task]
            evidence = displayed_evidence(u)
            futures[pool.submit(features,evidence,q['column'],q['filter'],task,context)] = (task,context)
        for future in as_completed(futures):
            feat = future.result()
            feats.append(feat)
            if len(feats)%6==0:
                print(json.dumps({'query_contexts_complete':len(feats),'expected':36}),flush=True)
    feats.sort(key=lambda f:(f['task_id'],f['context']))
    events = [e for f in feats for e in events_for_query(queries[f['task_id']],f['context'],f)]
    assert len(feats)==36 and len(events)==288
    models = {n:json.loads((folder/n/'scored_responses.json').read_text())
              for n in ('gemini-3.8-flash','qwen3-8b')}
    summary = summarize(events,feats,models)
    summary['audit'] = config | {'finished_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    save(output/'features.json',feats)
    save(output/'events.json',events)
    save(output/'summary.json',summary)
    print(json.dumps({'primary_0d_matched20':{k:summary['methods']['0d']['matched20'][k]
                                           for k in ('sanity_pass','sanity','detection','policy')},
                      'output':str(output)},indent=2),flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,default=ROOT/'data/ours/context_evidence/20261107')
    p.add_argument('--workers',type=int,choices=range(1,5),default=4)
    a=p.parse_args()
    run(a.root,a.output,a.workers)


if __name__=='__main__':
    main()
