#!/usr/bin/env python3
"""A-MONITOR-QWEN: Qwen3-8B replication of Experiment A raw/check arms on the frozen Gemini inputs.

prepare  derive the 540-unit raw/check manifest from the frozen Gemini manifest (no edits to messages)
smoke    send the 4 raw/check synthetic smoke units (engineering only, excluded from efficacy)
run      collect against a local vLLM endpoint (loopback / SSM port-forward); resumable
report   protocol-identical paired analysis plus the registered exploratory flag-only policy
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
import json
from pathlib import Path
import platform
import threading
import time

import numpy as np
import pandas as pd
import context_evidence as ce
import experiment_a as ea
from context_pilot import digest, parse_reply
from report_experiment_a import effect, cell

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'data/ours/experiment_a/20261108'
DEFAULT = ROOT/'data/ours/experiment_a/20261108_qwen3-8b'
PARENT_DIGEST = '350f5a3b18b97b434b517e9b08011f19c6c92c682e71abebde214ef66dcc6a07'
PROTOCOL = 'A-MONITOR-QWEN'
MODEL = 'qwen3-8b'
ARMS = ('raw', 'check')
LEVELS = ea.LEVELS
FILES = ('experiment_a_qwen.py', 'experiment_a.py', 'report_experiment_a.py', 'context_evidence.py', 'context_pilot.py', 'zeroparam.py')


def source_hashes():
    return {n: hashlib.sha256((ROOT/'experiments'/n).read_bytes()).hexdigest() for n in FILES}


def payload_for(messages):
    return {'model': MODEL, 'messages': messages, 'max_tokens': 1536, 'temperature': 0.7, 'seed': 0,
            'chat_template_kwargs': {'enable_thinking': False}}


def prepare(output, parent=PARENT, expected_digest=PARENT_DIGEST, expected=540):
    if (output/'manifest.json').exists():
        raise ValueError('frozen manifest exists; never overwrite')
    m = ea.load(parent/'manifest.json')
    if expected_digest is not None and digest(m) != expected_digest:
        raise ValueError('parent manifest digest mismatch')
    units = [u for u in m['units'] if u['arm'] in ARMS]
    manifest = {'protocol': PROTOCOL, 'parent_protocol': m['protocol'], 'parent_manifest_digest': digest(m),
                'model': MODEL, 'sampling': {k: v for k, v in payload_for([]).items() if k not in ('model', 'messages')},
                'source_hashes': source_hashes(), 'queries': m.get('queries'), 'sanity': m.get('sanity'),
                'units': units, 'expected': expected}
    assert len(units) == expected and len({u['unit_id'] for u in units}) == expected
    ea.save(output/'manifest.json', manifest)
    print(json.dumps({'manifest_digest': digest(manifest), 'units': len(units)}))


def run(output, base_url, workers):
    manifest = ea.load(output/'manifest.json')
    mh = digest(manifest)
    for u in manifest['units']:
        assert digest(u['messages']) == u['messages_hash'] and u['arm'] in ARMS
    ea.ENDPOINT = base_url.rstrip('/')+'/chat/completions'
    config = {'manifest_digest': mh, 'model': MODEL, 'endpoint': ea.ENDPOINT, 'source_hashes': manifest['source_hashes']}
    if (output/'config.json').exists() and ea.load(output/'config.json') != config:
        raise ValueError('resume config mismatch')
    if manifest['source_hashes'] != source_hashes():
        raise ValueError('runner changed since freeze')
    ea.save(output/'config.json', config)
    todo, done_n = [], 0
    for u in manifest['units']:
        p = output/'responses'/(u['unit_id']+'.json')
        if p.exists() and ea.load(p)['status'] == 'completed':
            done_n += 1
        else:
            todo.append(u)
    stop = threading.Event()

    def one(u):
        path = output/'responses'/(u['unit_id']+'.json')
        rec = ea.load(path) if path.exists() else {'unit_id': u['unit_id'], 'manifest_hash': mh,
              'initial_messages_hash': u['messages_hash'], 'started_utc': ea.utc(), 'calls': [], 'status': 'partial'}
        assert rec['manifest_hash'] == mh and rec['initial_messages_hash'] == u['messages_hash']
        payload = payload_for(u['messages'])
        if not rec['calls']:
            rec['calls'].append({'payload_hash': digest(payload), 'messages': u['messages'], 'attempts': []})
        call = rec['calls'][0]
        assert call['payload_hash'] == digest(payload)
        checkpoint = lambda: ea.save(path, rec)
        start = time.monotonic()
        if stop.is_set() and 'provider_response' not in call:
            raise ea.TransportFailure('halted after another failure')
        try:
            body = call.get('provider_response') or ea.request(payload, 'EMPTY', call, checkpoint)
        except ea.TransportFailure as exc:
            rec.update(status='transport_failure', error=str(exc)); checkpoint(); raise
        choice = (body.get('choices') or [{}])[0]
        raw = (choice.get('message') or {}).get('content') or ''
        parsed = None if choice.get('finish_reason') in ('length', 'content_filter') else parse_reply(raw)
        rec.update(status='completed', raw=raw, parsed=parsed, valid=parsed is not None,
                   response_model=body.get('model'), finish_reason=choice.get('finish_reason'),
                   ended_utc=ea.utc(), elapsed_seconds=time.monotonic()-start)
        if parsed is None:
            rec['terminal_reason'] = 'truncated' if choice.get('finish_reason') == 'length' else 'invalid-final'
        checkpoint()
        return rec

    with ThreadPoolExecutor(max_workers=workers) as pool:
        cursor, pending = iter(todo), {}
        for _ in range(workers):
            u = next(cursor, None)
            if u:
                pending[pool.submit(one, u)] = u
        while pending:
            ready, _ = wait(pending, return_when=FIRST_COMPLETED)
            for f in ready:
                pending.pop(f)
                try:
                    f.result()
                except Exception:
                    stop.set()
                    ea.save(output/'status.json', {'status': 'stopped-on-error', 'completed': done_n, 'expected': manifest['expected'], 'updated_utc': ea.utc()})
                    raise
                done_n += 1
                ea.save(output/'status.json', {'status': 'collecting' if done_n < manifest['expected'] else 'complete',
                                               'completed': done_n, 'expected': manifest['expected'], 'updated_utc': ea.utc()})
                if done_n % 30 == 0 or done_n == manifest['expected']:
                    print(json.dumps({'completed': done_n, 'expected': manifest['expected']}), flush=True)
                u = next(cursor, None)
                if u:
                    pending[pool.submit(one, u)] = u


def flag_only(units):
    """Exploratory registered policy: accept iff the 0d flag is absent; same rows as the check arm."""
    return [{'evidence_unit': u['evidence_unit'], 'task_id': u['task_id'], 'dataset': u['dataset'], 'arm': 'flag_only',
             'level': u['level'], 'decision': 'reject' if u['check']['flag'] else 'accept', 'valid': True}
            for u in units if u['arm'] == 'check']


def score_rows(manifest, output):
    mh = digest(manifest)
    rows, missing = [], []
    for u in manifest['units']:
        p = output/'responses'/(u['unit_id']+'.json')
        if not p.exists():
            missing.append(u['unit_id']); continue
        r = ea.load(p)
        assert r['manifest_hash'] == mh and r['initial_messages_hash'] == u['messages_hash']
        if r['status'] != 'completed':
            missing.append(u['unit_id']); continue
        call = r['calls'][0]
        assert call['messages'] == u['messages'] and call['payload_hash'] == digest(payload_for(u['messages']))
        choice = (call['provider_response'].get('choices') or [{}])[0]
        raw = (choice.get('message') or {}).get('content') or ''
        parsed = None if choice.get('finish_reason') in ('length', 'content_filter') else parse_reply(raw)
        assert r['raw'] == raw and r['parsed'] == parsed
        answer = parsed['answer'] if parsed else None
        correct = bool(parsed and answer is not None and abs(answer-u['truth']) <= u['tolerance'])
        adopted = bool(parsed and answer is not None and u['level'] != 'clean' and abs(answer-u['candidate']) <= u['tolerance'] and not correct)
        rows.append({k: u[k] for k in ('unit_id', 'evidence_unit', 'task_id', 'dataset', 'draw', 'arm', 'level')} |
                    {'valid': parsed is not None, 'decision': parsed['decision'] if parsed else 'invalid', 'answer': answer,
                     'correct': correct, 'adopted_wrong': adopted, 'candidate_flag': u['check']['flag'],
                     'finish_reason': choice.get('finish_reason'), 'usage': call['provider_response'].get('usage')})
    return rows, missing


def report(output):
    manifest = ea.load(output/'manifest.json')
    rows, missing = score_rows(manifest, output)
    if missing:
        ea.save(output/'analysis_status.json', {'status': 'incomplete-no-primary-efficacy-analysis', 'completed': len(rows), 'expected': manifest['expected']})
        print(json.dumps({'status': 'incomplete', 'completed': len(rows), 'missing': len(missing)}))
        return
    if manifest['expected'] != 540:
        summary = {'status': 'engineering-smoke-excluded-from-efficacy', 'completed': len(rows),
                   'cells': {a: {l: cell([r for r in rows if r['arm'] == a and r['level'] == l]) for l, _ in LEVELS} for a in ARMS}}
        ea.save(output/'summary.json', summary); print(json.dumps(summary, indent=2)); return
    primary = effect(rows, 'check', 'raw')
    primary['registered_joint_rule_met'] = bool(primary['discrimination']['ci95'][0] > 0 and primary['clean_acceptance']['ci95'][0] >= -.05)
    units = manifest['units']
    policy = flag_only(units)
    gem_rows = json.loads((PARENT/'scored.json').read_text())
    gem = [r for r in gem_rows if r['arm'] in ARMS]
    b = [r for r in rows if r['arm'] == 'check']
    usage = {a: {k: sum((r['usage'] or {}).get(k, 0) or 0 for r in rows if r['arm'] == a) for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')} for a in ARMS}
    summary = {
        'protocol': PROTOCOL, 'manifest_digest': digest(manifest), 'parent_manifest_digest': manifest['parent_manifest_digest'],
        'model': MODEL, 'sampling': manifest['sampling'], 'completed': len(rows), 'expected': manifest['expected'],
        'status': 'final-descriptive-intervention',
        'cells': {a: {l: cell([r for r in rows if r['arm'] == a and r['level'] == l]) for l, _ in LEVELS} for a in ARMS},
        'primary': primary, 'valid_triplet_sensitivity': effect(rows, 'check', 'raw', True),
        'flag_following': {'accepted_flagged': sum(r['candidate_flag'] and r['decision'] == 'accept' for r in b),
                           'flagged': sum(r['candidate_flag'] for r in b),
                           'rejected_compatible': sum(not r['candidate_flag'] and r['decision'] == 'reject' for r in b),
                           'compatible': sum(not r['candidate_flag'] for r in b)},
        'exploratory_flag_only': {
            'note': 'Registered in A-MONITOR-QWEN after seeing Gemini results; exploratory, descriptive.',
            'qwen3-8b': {'check_minus_flag_only': effect(rows+policy, 'check', 'flag_only'),
                         'flag_only_minus_raw': effect(rows+policy, 'flag_only', 'raw')},
            'gemini-3.8-flash': {'check_minus_flag_only': effect(gem+policy, 'check', 'flag_only'),
                                 'flag_only_minus_raw': effect(gem+policy, 'flag_only', 'raw')}},
        'usage': usage,
        'analysis_provenance': {'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__},
        'limits': ['Same 30 reused queries/six tables as Gemini Experiment A; no fresh-table generalization.',
                   'Three row draws/query are not extra queries or tables; one completion per cell.',
                   'B-A tests the full check-aid package, not warning text versus statistical content.',
                   'Flag-only comparison was specified after seeing Gemini results; exploratory.',
                   'Qwen and Gemini sampling settings differ; no model-comparison test.',
                   'No end-to-end recovery, cost or runtime-placement claim; null is not correct.']}
    # flag-following by level, explicit
    summary['flag_following']['by_level'] = {l: {('flagged' if f else 'compatible'): {d: sum(r['level'] == l and r['candidate_flag'] == f and r['decision'] == d for r in b)
                                                  for d in ('accept', 'reject', 'uncertain', 'invalid')} for f in (True, False)} for l, _ in LEVELS}
    ea.save(output/'scored.json', [{k: v for k, v in r.items() if k != 'usage'} for r in rows])
    ea.save(output/'summary.json', summary)
    fmt = lambda x: f'{x:.3f}'
    ci = lambda x: '[' + ', '.join(fmt(v) for v in x) + ']'
    lines = ['# Qwen3-8B Experiment A replication (raw/check arms)', '',
             f"{len(rows)} completed trajectories on the frozen Gemini Experiment A inputs; 30 queries, three row draws, six tables.", '',
             '| Arm | Candidate | Accept | Reject | Uncertain | Invalid | Correct numeric | Null |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for a in ARMS:
        for l, _ in LEVELS:
            x = summary['cells'][a][l]
            lines.append(f"| {a} | {l} | {x['accept']}/{x['n']} | {x['reject']} | {x['uncertain']} | {x['invalid']} | {x['correct_numeric']} | {x['null']} |")
    lines += ['', '## Registered primary: check minus raw', '']
    for k in ('discrimination', 'clean_acceptance'):
        lines.append(f"- {k}: {fmt(primary[k]['mean'])} {ci(primary[k]['ci95'])}")
    lines += [f"- Joint benefit rule met: {primary['registered_joint_rule_met']}.", '',
              '## Exploratory: flag-only policy (accept iff 0d flag absent)', '',
              '| Model | check minus flag-only [95%] | flag-only minus raw [95%] |', '|---|---|---|']
    for name in ('qwen3-8b', 'gemini-3.8-flash'):
        e = summary['exploratory_flag_only'][name]
        lines.append(f"| {name} | {fmt(e['check_minus_flag_only']['discrimination']['mean'])} {ci(e['check_minus_flag_only']['discrimination']['ci95'])} | "
                     f"{fmt(e['flag_only_minus_raw']['discrimination']['mean'])} {ci(e['flag_only_minus_raw']['discrimination']['ci95'])} |")
    ff = summary['flag_following']
    lines += ['', f"Flag following (check arm): accepted {ff['accepted_flagged']}/{ff['flagged']} flagged candidates; rejected {ff['rejected_compatible']}/{ff['compatible']} compatible candidates.",
              '', '## Limits', ''] + ['- '+x for x in summary['limits']]
    (output/'report.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('prepare', 'smoke', 'run', 'report'))
    p.add_argument('--output', type=Path, default=DEFAULT)
    p.add_argument('--base-url', default='http://127.0.0.1:8000/v1')
    p.add_argument('--workers', type=int, default=8)
    a = p.parse_args()
    if a.action == 'prepare':
        prepare(a.output)
    elif a.action == 'smoke':
        out = a.output/'smoke'
        if not (out/'manifest.json').exists():
            prepare(out, PARENT/'smoke', None, 4)
        run(out, a.base_url, 2)
        report(out)
    elif a.action == 'run':
        run(a.output, a.base_url, a.workers)
    else:
        report(a.output)


if __name__ == '__main__':
    main()
