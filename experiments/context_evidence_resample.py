#!/usr/bin/env python3
"""A-CTX-RESAMPLE: freeze independent matched20 draws, then reuse the fixed checker.

Full tables are read only by prepare(), the evidence provider. Workers in run()
receive frozen twenty-row evidence, never a population table or truth.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess

import numpy as np
import pandas as pd

import context_evidence as ce
from context_pilot import digest, validate_manifest

ROOT=Path(__file__).resolve().parents[1]
SOURCE_NAMES=('context_evidence_resample.py','context_evidence.py','zeroparam.py','p4_common.py','context_pilot.py')


def fingerprints(root):
    return {n:ce.hashfile(root/'experiments'/n) for n in SOURCE_NAMES}


def sample_evidence(df,q,draw):
    eligible=np.flatnonzero((df[q['filter'][0]].astype(str)==q['filter'][1]).to_numpy()
                            & np.isfinite(pd.to_numeric(df[q['column']],errors='coerce').to_numpy(float)))
    if len(eligible)<20:raise ValueError('Fewer than 20 eligible rows')
    seed=20261108+int(hashlib.sha256((q['task_id']+'|draw|'+str(draw)).encode()).hexdigest()[:8],16)
    idx=np.random.default_rng(seed).choice(eligible,20,replace=False)
    evidence={'shape':list(df.shape),'columns':list(df.columns),
              'dtypes':{c:str(t) for c,t in df.dtypes.items()},
              'sampling_rule':'20 rows uniformly sampled without replacement from rows satisfying the query filter and having a finite numeric target.',
              'rows_csv':df.iloc[idx].to_csv(index=False)}
    return {'task_id':q['task_id']+f'__draw_{draw:02d}','original_task_id':q['task_id'],
            'draw':draw,'seed':seed,'row_indices':idx.tolist(),'evidence':evidence,'evidence_hash':digest(evidence)}


def prepare(root,output):
    if (output/'manifest.json').exists():raise ValueError('Frozen evidence already exists')
    original=root/'data/ours/context_pilot/20261107/manifest.json'
    m=json.loads(original.read_text());validate_manifest(m)
    assert digest(m)=='7263b5dcd25ccf3c4463ffe6778243a3f953a153c55f0c493d9714cd0dc99983'
    tables={}
    for dataset,sha in m['dataset_hashes'].items():
        path=root/'data/ours/datasets'/dataset
        assert ce.hashfile(path)==sha
        tables[dataset]=pd.read_csv(path)
    units=[sample_evidence(tables[q['dataset']],q,draw) for q in m['selected_queries'] for draw in range(20)]
    frozen={'protocol':'A-CTX-RESAMPLE','protocol_commit':'7f6400e','original_manifest_hash':digest(m),
            'source_hashes':fingerprints(root),'dataset_hashes':m['dataset_hashes'],
            'selected_queries':m['selected_queries'],'units':units,
            'provider_code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()}
    ce.save(output/'manifest.json',frozen)
    print(json.dumps({'frozen_units':len(units),'manifest_hash':digest(frozen)}),flush=True)


def flag_rates(events):
    result={}
    for role in ('clean','corrupted'):
        rows=[e for e in events if e['role']==role]
        stat=ce.cluster_difference([{'dataset':e['dataset'],'difference':int(e['decision']=='flag')} for e in rows])
        stat['draw_units']=stat.pop('queries')
        stat['flags']=sum(e['decision']=='flag' for e in rows)
        stat['unscorable']=sum(e['decision']=='unscorable' for e in rows)
        result[role]=stat
    return result


def summarize(events):
    methods={}
    for method in ce.METHODS:
        rows=[e for e in events if e['method']==method]
        cell=ce.summarize_cell(rows)
        cell['flag_rates']=flag_rates(rows)
        cell['per_severity']={s:ce.summarize_cell([e for e in rows if e['severity']==s],parent_gate=cell['sanity_pass'])
                              for s in ('subtle','plausible')}
        cell['per_query']={}
        for task in sorted({e['original_task_id'] for e in rows}):
            sub=[e for e in rows if e['original_task_id']==task]
            cell['per_query'][task]={role:{'n':sum(e['role']==role for e in sub),
                **{d:sum(e['role']==role and e['decision']==d for e in sub)
                   for d in ('flag','compatible','unscorable')}} for role in ('clean','corrupted')}
        methods[method]=cell
    return {'protocol':'A-CTX-RESAMPLE','original_queries':12,'draws_per_query':20,'table_clusters':6,
            'query_draw_units':240,'events':len(events),'methods':methods,
            'model_comparison':None,'model_comparison_status':'No new model replies to these rows; old replies not reused.'}


def run(root,output,workers):
    if (output/'summary.json').exists():raise ValueError('Fixed experiment already completed')
    m=json.loads((output/'manifest.json').read_text())
    assert m['source_hashes']==fingerprints(root)
    assert len(m['units'])==240 and len({u['task_id'] for u in m['units']})==240
    qlookup={q['task_id']:q for q in m['selected_queries']}
    config={'protocol_commit':m['protocol_commit'],'manifest_hash':digest(m),
            'source_hashes':fingerprints(root),'bootstrap_draws':2000,'threshold':ce.THRESHOLD,
            'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
            'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'versions':{'python':platform.python_version(),**{p:importlib.metadata.version(p) for p in ('numpy','pandas','scikit-learn')}}}
    ce.save(output/'config.json',config)
    feats=[]
    units={u['task_id']:u for u in m['units']}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending={}
        for u in m['units']:
            assert digest(u['evidence'])==u['evidence_hash']
            q=qlookup[u['original_task_id']]
            pending[pool.submit(ce.features,u['evidence'],q['column'],q['filter'],u['task_id'],'matched20')]=u
        for future in as_completed(pending):
            u=pending[future];f=future.result()
            f.update(original_task_id=u['original_task_id'],draw=u['draw'])
            feats.append(f)
            if len(feats)%24==0:print(json.dumps({'query_draws_complete':len(feats),'expected':240}),flush=True)
    feats.sort(key=lambda f:f['task_id'])
    events=[]
    for f in feats:
        q=qlookup[f['original_task_id']]|{'task_id':f['task_id']}
        es=ce.events_for_query(q,'matched20',f)
        for e in es:e.update(original_task_id=f['original_task_id'],draw=f['draw'])
        events.extend(es)
    assert len(events)==1920
    summary=summarize(events)
    summary['audit']=config|{'finished_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    ce.save(output/'features.json',feats);ce.save(output/'events.json',events);ce.save(output/'summary.json',summary)
    print(json.dumps({'primary_0d':{k:summary['methods']['0d'][k]
                                    for k in ('sanity_pass','sanity','detection','policy','flag_rates')}},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('prepare','run'))
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--output',type=Path,default=ROOT/'data/ours/context_evidence_resample/20261107')
    p.add_argument('--workers',type=int,choices=range(1,5),default=4)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.root,a.output)
    else:run(a.root,a.output,a.workers)
