#!/usr/bin/env python3
"""Verify existing A-CTX-PILOT records; no new model calls or signal estimates.

Recomputes the registered behavioral contrast from scored records. Missing raw
responses are an audit limitation, not evidence that a model run failed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def digest(x):
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()).hexdigest()


def close(a, b, tol):
    return a is not None and abs(a-b) <= tol


def contrast(rows, queries, a, b, valid_only=False):
    lookup = {(r['task_id'],r['context'],r['label']):r for r in rows}
    per_table = {}
    for q in queries:
        cells = [lookup[(q['task_id'],c,label)] for c in (a,b) for label in (0,1)]
        if valid_only and not all(r['valid'] for r in cells):
            continue
        outcomes = [int(r['decision']=='accept') for r in cells]
        difference = (outcomes[0]-outcomes[1])-(outcomes[2]-outcomes[3])
        per_table.setdefault(q['dataset'],[]).append(difference)
    means = np.array([np.mean(x) for _,x in sorted(per_table.items())])
    boot = np.random.default_rng(1).choice(means,(2000,len(means)),replace=True).mean(axis=1)
    return {'mean':float(means.mean()), 'ci95':np.quantile(boot,[.025,.975]).tolist(),
            'queries':sum(map(len,per_table.values())), 'tables':len(means),
            'per_table':{k:float(np.mean(v)) for k,v in per_table.items()}}


def audit(root):
    sys.path.insert(0,str(root/'experiments'))
    from context_pilot import parse_reply, validate_manifest
    base = root/'data/ours/context_pilot/20261107'
    m = json.loads((base/'manifest.json').read_text())
    validate_manifest(m)
    units = {u['unit_id']:u for u in m['units']}
    output = {'kind':'verification of already collected results; no new experiment',
              'manifest_canonical_hash':digest(m),
              'manifest_file_hash':hashlib.sha256((base/'manifest.json').read_bytes()).hexdigest(), 'models':{}}
    for model in ('gemini-3.8-flash','qwen3-8b'):
        folder = base/model
        config = json.loads((folder/'config.json').read_text())
        summary = json.loads((folder/'summary.json').read_text())
        rows = json.loads((folder/'scored_responses.json').read_text())
        assert config['manifest_hash']==summary['manifest_hash']==digest(m)
        assert config['source_hashes']==m['source_hashes']
        assert len(rows)==72 and {r['unit_id'] for r in rows}==set(units)
        raw_verified, cells, raw_hashes, fingerprints = 0, {}, {}, set()
        for r in rows:
            u = units[r['unit_id']]
            for key in ('task_id','dataset','context','label','severity'):
                assert r[key]==u[key], (model,r['unit_id'],key)
            correct = bool(r['valid'] and close(r['answer'],u['truth'],u['tolerance']))
            adopted = bool(r['valid'] and u['label'] and close(r['answer'],u['delivered_value'],u['tolerance']) and not correct)
            assert r['correct']==correct and r['adopted_wrong']==adopted
            rawfile = folder/'responses'/(u['unit_id']+'.json')
            if rawfile.exists():
                raw = json.loads(rawfile.read_text())
                assert raw['manifest_hash']==digest(m) and raw['messages_hash']==u['messages_hash']
                assert raw['unit_id']==u['unit_id'] and raw['status']=='completed'
                payload = {'model':config['model'], 'messages':u['messages'], 'max_tokens':config['max_tokens']}
                if model=='gemini-3.8-flash':
                    payload['reasoning_effort']='low'
                else:
                    payload.update(temperature=.7, seed=0)
                if model.startswith('qwen3'):
                    payload['chat_template_kwargs']={'enable_thinking':False}
                assert raw['payload_hash']==digest(payload), (model,u['unit_id'],'payload hash')
                provider = raw['provider_response']
                choice = provider['choices'][0]
                assert raw['raw']==(choice['message'].get('content') or '')
                assert raw['finish_reason']==r['finish_reason']==choice['finish_reason']
                assert raw['response_model']==r['response_model']==provider['model']
                assert raw['usage']==r['usage']==provider['usage']
                if provider.get('system_fingerprint'):
                    fingerprints.add(provider['system_fingerprint'])
                raw_hashes[rawfile.name]=hashlib.sha256(rawfile.read_bytes()).hexdigest()
                parsed = parse_reply(raw['raw'])
                assert raw['parsed']==parsed
                assert r['valid']==(parsed is not None)
                for key in ('decision','confidence','answer'):
                    expected = parsed[key] if parsed else ('invalid' if key=='decision' else None)
                    assert r[key]==expected
                raw_verified += 1
        for c in ('head5','random20','matched20'):
            cells[c] = {}
            for label in (0,1):
                subset = [r for r in rows if r['context']==c and r['label']==label]
                counts = {key:sum(r['decision']==key for r in subset) for key in ('accept','reject','uncertain','invalid')}
                for key,value in counts.items():
                    assert summary['cells'][c][str(label)][key]==value
                cells[c][str(label)] = {'n':len(subset),**counts,
                    'correct':sum(r['correct'] for r in subset),
                    'adopted_wrong':sum(r['adopted_wrong'] for r in subset),
                    'valid_null_answers':sum(r['valid'] and r['answer'] is None for r in subset)}
        results = {}
        for a,b in (('matched20','random20'),('matched20','head5'),('random20','head5')):
            name = a+'_minus_'+b
            results[name] = contrast(rows,m['selected_queries'],a,b)
            sensitivity = contrast(rows,m['selected_queries'],a,b,True)
            assert results[name]==summary['primary_acceptance_discrimination_contrasts'][name]
            assert sensitivity==summary['valid_pair_sensitivity'][name]
        rejects = [r for r in rows if r['valid'] and r['decision']=='reject']
        uncertain = [r for r in rows if r['valid'] and r['decision']=='uncertain']
        output['models'][model] = {'n':len(rows),'valid':sum(r['valid'] for r in rows),
            'raw_responses_verified':raw_verified,'raw_responses_missing':72-raw_verified,
            'raw_file_sha256':raw_hashes,'provider_fingerprints':sorted(fingerprints),
            'raw_payload_and_provider_metadata_verified':raw_verified,
            'configuration_hashes_match':True,'scored_counts_and_contrasts_match':True,
            'cells':cells,'contrasts':results,
            'reject_confidences':[r['confidence'] for r in rejects],
            'uncertain_confidences':[r['confidence'] for r in uncertain],
            'claim_limits':['No live signal sanity arm; confidence AUROC withheld.',
                            'Twelve selected queries and six tables; one sample/completion per cell.',
                            'No equivalence claim or cross-model robustness ranking.']}
    return output


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--output',type=Path)
    a = p.parse_args()
    result = audit(a.root)
    data = json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if a.output:
        a.output.write_text(data)
        print(a.output)
    else:
        print(data,end='')
