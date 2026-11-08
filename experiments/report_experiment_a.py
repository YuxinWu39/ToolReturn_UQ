#!/usr/bin/env python3
"""Protocol-faithful final analysis of completed Experiment A records; no model requests."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import context_evidence as ce
from context_pilot import digest, parse_reply
from experiment_a import ARMS, LEVELS, DEFAULT, load, save


def effect(rows, intervention, control, valid_only=False):
    lookup={(r['evidence_unit'],r['arm'],r['level']):r for r in rows}
    records=[]
    for ident in sorted({r['evidence_unit'] for r in rows}):
        cells=[lookup[(ident,a,l)] for a in (intervention,control) for l,_ in LEVELS]
        if valid_only and not all(r['valid'] for r in cells):
            continue
        scores=[]
        for group in (cells[:3],cells[3:]):
            accept=[int(r['decision']=='accept') for r in group]
            scores.append((accept[0]-(accept[1]+accept[2])/2,accept[0]))
        records.append({'task_id':cells[0]['task_id'],'dataset':cells[0]['dataset'],
                        'discrimination':scores[0][0]-scores[1][0], 'clean_acceptance':scores[0][1]-scores[1][1]})
    if not records:
        return {'status':'no-complete-valid-triplets','queries':0,'tables':0}
    frame=pd.DataFrame(records)
    query=frame.groupby(['dataset','task_id'])[['discrimination','clean_acceptance']].mean()
    table=query.groupby('dataset').mean()
    means=table.to_numpy()
    draws=means[np.random.default_rng(1).integers(len(means),size=(2000,len(means)))].mean(axis=1)
    result={'status':'descriptive-paired-table-bootstrap','queries':len(query),'evidence_units':len(records),
            'tables':len(table),'per_table':table.to_dict(orient='index')}
    for i,key in enumerate(('discrimination','clean_acceptance')):
        result[key]={'mean':float(means[:,i].mean()),'ci95':np.percentile(draws[:,i],[2.5,97.5]).tolist()}
    return result


def cell(rows):
    n=len(rows)
    return {'n':n,'valid':sum(r['valid'] for r in rows),
            **{d:sum(r['decision']==d for r in rows) for d in ('accept','reject','uncertain','invalid')},
            'correct_numeric':sum(r['correct'] for r in rows),'adopted_wrong':sum(r['adopted_wrong'] for r in rows),
            'wrong_numeric':sum(r['valid'] and r['answer'] is not None and not r['correct'] for r in rows),
            'null':sum(r['valid'] and r['answer'] is None for r in rows),
            'numeric_answer_coverage':sum(r['valid'] and r['answer'] is not None for r in rows)/n if n else None}


def analyze(output):
    manifest=load(output/'manifest.json'); mh=digest(manifest)
    rows=[]; costs={a:{'completed_trajectories':0,'logical_requests':0,'http_attempts':0,
                      'failed_http_attempts':0,'python_calls':0,'python_errors':0,
                      'prompt_tokens':0,'completion_tokens':0,'total_tokens':0,'http_seconds':0.,'tool_seconds':0.}
                  for a in ARMS}
    responses=[]
    missing=[]
    for u in manifest['units']:
        path=output/'responses'/(u['unit_id']+'.json')
        if not path.exists():
            missing.append(u['unit_id']);continue
        r=load(path)
        assert r['unit_id']==u['unit_id'] and r['manifest_hash']==mh and r['initial_messages_hash']==u['messages_hash']
        assert len(r['calls']) <= (4 if u['arm']=='code' else 1)
        assert len(r['tools']) <= (3 if u['arm']=='code' else 0)
        c=costs[u['arm']]
        c['completed_trajectories']+=int(r['status']=='completed')
        c['python_calls']+=len(r['tools']);c['python_errors']+=sum(t['result']['error'] for t in r['tools'])
        c['tool_seconds']+=sum(t.get('elapsed_seconds',0) for t in r['tools'])
        for call in r['calls']:
            c['logical_requests']+=int(bool(call['attempts']))
            c['http_attempts']+=len(call['attempts'])
            c['failed_http_attempts']+=sum(x['status']!='success' for x in call['attempts'])
            c['http_seconds']+=sum(x.get('elapsed_seconds',0) for x in call['attempts'])
            for key in ('prompt_tokens','completion_tokens','total_tokens'):
                c[key]+=(call.get('provider_response',{}).get('usage') or {}).get(key,0) or 0
        if r['status']!='completed':
            c['incomplete_trajectories']=c.get('incomplete_trajectories',0)+1
            missing.append(u['unit_id']);continue
        expected_messages=u['messages']
        for index,call in enumerate(r['calls']):
            assert call['messages']==expected_messages
            payload={'model':manifest.get('model','gemini-3.8-flash'),'messages':expected_messages,'max_tokens':1536,'reasoning_effort':'low'}
            assert call['payload_hash']==digest(payload)
            assert len(call['attempts'])<=3
            provider=call['provider_response'];choice=(provider.get('choices') or [{}])[0]
            raw=(choice.get('message') or {}).get('content') or ''
            if index<len(r['tools']):
                t=r['tools'][index]
                assert json.loads(raw)=={'python':t['code']}
                expected_messages=expected_messages+[{'role':'assistant','content':raw},
                       {'role':'user','content':'VISIBLE-ROWS PYTHON RESULT\n'+t['result']['output']+
                        ('\nTool budget exhausted. Give the final four-field JSON now.' if index==2 else '')}]
        choice=(r['calls'][-1]['provider_response'].get('choices') or [{}])[0]
        raw=(choice.get('message') or {}).get('content') or ''
        parsed=parse_reply(raw)
        if choice.get('finish_reason') in ('length','content_filter') or (choice.get('message') or {}).get('refusal'):
            parsed=None
        assert r['raw']==raw and r['parsed']==parsed and r['valid']==(parsed is not None)
        answer=parsed['answer'] if parsed else None
        correct=bool(parsed and answer is not None and abs(answer-u['truth'])<=u['tolerance'])
        adopted=bool(parsed and answer is not None and u['level']!='clean' and abs(answer-u['candidate'])<=u['tolerance'] and not correct)
        rows.append({k:u[k] for k in ('unit_id','evidence_unit','task_id','dataset','draw','arm','level')} |
                    {'valid':parsed is not None,'decision':parsed['decision'] if parsed else 'invalid',
                     'answer':answer,'correct':correct,'adopted_wrong':adopted,
                     'candidate_flag':u['check']['flag'],'finish_reason':choice.get('finish_reason')})
        responses.append(r)
    if missing:
        progress={'status':'incomplete-no-primary-efficacy-analysis','completed':len(rows),
                  'expected':manifest['expected'],'missing_unit_ids':missing,'costs_so_far':costs}
        lookup={(r['evidence_unit'],r['arm'],r['level']):r for r in rows}
        ids={r['evidence_unit'] for r in rows if all((r['evidence_unit'],a,l) in lookup for a in ('raw','check') for l,_ in LEVELS)}
        common=[r for r in rows if r['evidence_unit'] in ids and r['arm'] in ('raw','check')]
        progress['interim_completed_common_cell_sensitivity']=effect(common,'check','raw') if common else {'status':'no-completed-common-evidence-units'}
        save(output/'analysis_status.json',progress)
        print(json.dumps({'status':progress['status'],'completed':len(rows),'expected':manifest['expected']}))
        return progress
    summary={'protocol':manifest['protocol'],'manifest_hash':mh,'completed':len(rows),'expected':manifest['expected'],
             'cells':{a:{l:cell([r for r in rows if r['arm']==a and r['level']==l]) for l,_ in LEVELS} for a in ARMS},
             'costs':costs,'new_queries':False,'confidence_auroc':'not-estimated','primary':None}
    if manifest['expected']!=810:
        summary['status']='engineering-smoke-excluded-from-efficacy'
        save(output/'summary.json',summary)
        print(json.dumps(summary,indent=2))
        return summary
    primary=effect(rows,'check','raw')
    primary['registered_joint_rule_met']=bool(primary['discrimination']['ci95'][0]>0 and primary['clean_acceptance']['ci95'][0]>=-.05)
    summary.update(status='final-descriptive-intervention',primary=primary,
                   valid_triplet_sensitivity=effect(rows,'check','raw',True),
                   secondary={name:effect(rows,a,b) for name,a,b in [('code_minus_raw','code','raw'),('code_minus_check','code','check')]},
                   per_table={d:{a:{l:cell([r for r in rows if r['dataset']==d and r['arm']==a and r['level']==l]) for l,_ in LEVELS} for a in ARMS} for d in sorted({r['dataset'] for r in rows})})
    direct=[{'task_id':u['evidence_unit'],'dataset':u['dataset'],'role':u['level'],'score':u['check']['score']} for u in manifest['units'] if u['arm']=='check']
    summary['direct_monitor']={'sanity':manifest['sanity'], 'detection':ce.auc_summary(direct,tuple(x[0] for x in LEVELS)),
                              'flag_counts':{l:{'n':sum(u['arm']=='check' and u['level']==l for u in manifest['units']),
                                               'flag':sum(u['arm']=='check' and u['level']==l and u['check']['flag'] for u in manifest['units'])} for l,_ in LEVELS}}
    b=[r for r in rows if r['arm']=='check']
    summary['flag_following']={'accepted_flagged':sum(r['candidate_flag'] and r['decision']=='accept' for r in b),
                               'flagged':sum(r['candidate_flag'] for r in b),
                               'rejected_compatible':sum(not r['candidate_flag'] and r['decision']=='reject' for r in b)}
    summary['limits']=['Reused selected queries/six public tables; no fresh-table generalization.',
                      'Three row draws/query are not extra queries or tables; one model sequence/cell.',
                      'B-A tests a full check-aid package, not a warning-versus-statistical-content mechanism.',
                      'C has extra computation and requests; no equal-cost or placement-superiority claim.',
                      'No end-to-end recovery policy evaluated; null is not correct; confidence efficacy withheld.',
                      'Six-table bootstrap intervals are descriptive; no calibrated noninferiority or acceptance probability.']
    save(output/'scored.json',rows);save(output/'summary.json',summary)
    def fmt(x):return f'{x:.3f}'
    lines=['# Gemini Experiment A: paired monitor intervention','','Final analysis of 810 completed trajectories; 30 selected queries, three row draws, six tables.','',
           '| Arm | Candidate | Accept | Reject | Uncertain | Invalid | Correct numeric | Null |','|---|---|---:|---:|---:|---:|---:|---:|']
    for a in ARMS:
        for l,_ in LEVELS:
            x=summary['cells'][a][l]
            lines.append(f"| {a} | {l} | {x['accept']}/{x['n']} | {x['reject']} | {x['uncertain']} | {x['invalid']} | {x['correct_numeric']} | {x['null']} |")
    lines+=['','## Registered primary: check minus raw','']
    for key in ('discrimination','clean_acceptance'):
        x=primary[key];lines.append(f"- {key}: {fmt(x['mean'])}, descriptive interval {x['ci95']}.")
    lines += [f"- Joint benefit rule met: {primary['registered_joint_rule_met']}.",'',
              'Joint rule requires discrimination lower bound >0 and clean-acceptance lower bound >=−0.05. Passing does not establish population noninferiority or deployed net benefit.','',
              '## Request and tool cost','', '| Arm | Logical requests | HTTP attempts | Python calls | Python errors | Prompt tokens | Completion tokens | Reported total tokens |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for a,c in costs.items():
        lines.append(f"| {a} | {c['logical_requests']} | {c['http_attempts']} | {c['python_calls']} | {c['python_errors']} | {c['prompt_tokens']} | {c['completion_tokens']} | {c['total_tokens']} |")
    lines+=['','Usage fields are preserved as returned; total may include reasoning categories not separately itemized. HTTP time includes failed attempts; tool time is separate. No currency-cost or equal-budget claim.','', '## Limits','']+['- '+x for x in summary['limits']]
    (output/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'completed':len(rows),'primary':primary,'costs':costs},indent=2))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=DEFAULT)
    analyze(p.parse_args().output)
