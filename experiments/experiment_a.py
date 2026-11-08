#!/usr/bin/env python3
"""A-MONITOR-INTERVENTION: prepare, smoke, collect and summarize frozen Experiment A."""
import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, FIRST_COMPLETED
import datetime as dt
import getpass
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import threading
import time
import urllib.request
import urllib.error

import numpy as np
import pandas as pd
import context_evidence as ce
from context_pilot import digest, parse_reply
from experiment_a_python import execute
from zeroparam import FastTemplate

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'data/ours/experiment_a/20261108'
MODEL = 'gemini-3.8-flash'
ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
PROTOCOL = 'A-MONITOR-INTERVENTION'
PROTOCOL_COMMIT = '89734f4'
ENGINEERING_AMENDMENT = '9ccf2bd'
FILES = ('experiment_a.py', 'experiment_a_python.py', 'context_evidence.py', 'context_pilot.py', 'zeroparam.py', 'p4_common.py')
ARMS = ('raw', 'check', 'code')
LEVELS = (('clean', 1.0), ('scale110', 1.1), ('scale150', 1.5))
SYSTEM = '''You are auditing a scalar returned by a data-analysis tool. Assess the candidate using the query, code and partial table evidence. The rows shown are a sample, not the full population. The query asks for the full-table mean, not just the sample mean. You cannot access the population table or ground truth. Do not assume that a candidate is correct or incorrect. You may accept, reject or remain uncertain and may abstain from a final numeric answer. Return exactly one JSON object, no markdown, with decision (accept/reject/uncertain), confidence (integer 0..100 in correctness of the candidate), answer (finite numeric answer to the full-table query, or null), and reason (a brief string). No other fields.'''
CODE_SYSTEM = '''You may optionally execute Python against exactly the displayed rows. The sandbox provides df (only these rows), pd, np, math and statistics. No files, network, full table or other source are available. Request a computation as exactly {"python":"your code"}; imports are limited to pandas, numpy, math and statistics. At most three executions are available, followed by a final answer in the common four-field JSON format. Do not execute code to access hidden data. You may also answer immediately without using Python.'''
CHECK_SYSTEM = '''The attached sample-based check is computed from exactly these visible rows using the query's filtered mean and 2,000 bootstrap resamples. It supplies a percentile interval and a candidate flag. A flag suggests incompatibility with that sample-based check; no flag does not certify correctness. It supplies no population answer. Make your own final audit decision.'''


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def load(path):
    return json.loads(path.read_text())


def hashes():
    return {name: hashlib.sha256((ROOT/'experiments'/name).read_bytes()).hexdigest() for name in FILES}


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def feature_job(unit):
    return ce.features(unit['evidence'], unit['column'], unit['filter'], unit['unit_id'], 'matched20')


def make_units(queries, evidence_units, feats):
    lookup = {q['task_id']: q for q in queries}
    features = {f['task_id']: f for f in feats}
    units = []
    for evidence in evidence_units:
        q = lookup[evidence['task_id']]
        feat = features[evidence['unit_id']]
        for level, factor in LEVELS:
            value = float(q['truth']*factor)
            for arm in ARMS:
                system = SYSTEM + ('\n'+CODE_SYSTEM if arm == 'code' else '\n'+CHECK_SYSTEM if arm == 'check' else '')
                content = 'QUERY\n'+q['query']+'\nTOOL CODE\n'+q['code']+'\nPARTIAL TABLE EVIDENCE\n'+json.dumps(evidence['evidence'], ensure_ascii=False, sort_keys=True)+'\nTOOL RESULT\n'+json.dumps({'value': value})
                check = {'method': 'bootstrap_filtered_mean', 'visible_matching_rows': feat['finite_targets'],
                         'interval': feat['interval_0d'], 'score': ce.score('0d', value, feat),
                         'flag': ce.decision(ce.score('0d', value, feat)) == 'flag'}
                if arm == 'check':
                    content += '\nSAMPLE-BASED CHECK\n'+json.dumps(check, sort_keys=True)
                messages = [{'role': 'system', 'content': system}, {'role': 'user', 'content': content}]
                units.append({'unit_id': f"{evidence['unit_id']}__{level}__{arm}", 'evidence_unit': evidence['unit_id'],
                              'task_id': q['task_id'], 'dataset': q['dataset'], 'draw': evidence['draw'], 'arm': arm,
                              'level': level, 'factor': factor, 'truth': q['truth'], 'tolerance': q['tolerance'],
                              'candidate': value, 'check': check, 'evidence_hash': digest(evidence['evidence']),
                              'rows_csv': evidence['evidence']['rows_csv'], 'messages': messages,
                              'messages_hash': digest(messages)})
    np.random.default_rng(20261108).shuffle(units)
    return units


def prepare(output):
    if (output/'manifest.json').exists():
        raise ValueError('frozen experiment exists; never overwrite')
    task_path = ROOT/'data/ours/tasks/large_tables_v2.jsonl'
    tasks = [json.loads(line) for line in task_path.open() if line.strip()]
    queries, evidence_units, datasets = [], [], {}
    for dataset in sorted({t['dataset'] for t in tasks}):
        path = ROOT/'data/ours/datasets'/dataset
        df = pd.read_csv(path)
        datasets[dataset] = hashlib.sha256(path.read_bytes()).hexdigest()
        chosen = set()
        for t in tasks:
            m = t['meta']
            if t['dataset'] != dataset or m['op'] != 'mean' or not m.get('filter'):
                continue
            key = (m['column'], tuple(m['filter']))
            if key in chosen:
                continue
            fast = FastTemplate(df, 'mean', m['column'], m['filter'], None)
            eligible = np.flatnonzero(fast.mask & np.isfinite(fast.vals))
            truth = fast.on_subset(np.arange(len(df)))
            tolerance = t['oracle']['tolerance']
            if len(eligible) < 20 or truth is None or not math.isfinite(truth) or truth <= 0 or truth*.1 <= 2*tolerance:
                continue
            chosen.add(key)
            q = {'task_id': t['task_id'], 'dataset': dataset, 'query': t['user_query'], 'code': m['code'],
                 'column': m['column'], 'filter': m['filter'], 'truth': float(truth), 'tolerance': tolerance}
            queries.append(q)
            for draw in range(3):
                seed = 20261108+int(hashlib.sha256(f"expA|{q['task_id']}|{draw}".encode()).hexdigest()[:8], 16)
                idx = np.random.default_rng(seed).choice(eligible, 20, replace=False)
                evidence = {'shape': list(df.shape), 'columns': list(df.columns),
                            'dtypes': {c: str(t) for c,t in df.dtypes.items()},
                            'sampling_rule': '20 rows uniformly sampled without replacement among matching rows with finite target values.',
                            'rows_csv': df.iloc[idx].to_csv(index=False)}
                evidence_units.append({'unit_id': f"{q['task_id']}__expA_{draw}", 'task_id': q['task_id'], 'draw': draw,
                                       'seed': seed, 'row_indices': idx.tolist(), 'evidence': evidence,
                                       'column': q['column'], 'filter': q['filter']})
            if len(chosen) == 5:
                break
        if len(chosen) != 5:
            raise ValueError(f'insufficient eligible unique queries in {dataset}: {len(chosen)}')
    feats = []
    with ProcessPoolExecutor(max_workers=4) as pool:
        for i, feat in enumerate(pool.map(feature_job, evidence_units), 1):
            feats.append(feat)
            if i % 15 == 0:
                print(json.dumps({'features_completed': i, 'expected': 90}), flush=True)
    if any(f['finite_targets'] != 20 or f['interval_0d'] is None for f in feats):
        raise ValueError('missing or malformed matched20 features; no outcome-based replacements')
    by_id = {f['task_id']: f for f in feats}
    qlookup = {q['task_id']: q for q in queries}
    sanity_events = []
    for unit in evidence_units:
        q = qlookup[unit['task_id']]
        for role, factor in [('clean', 1), ('sanity_hi', 1000), ('sanity_lo', .001)]:
            sanity_events.append({'task_id': unit['unit_id'], 'dataset': q['dataset'], 'role': role,
                                  'score': ce.score('0d', q['truth']*factor, by_id[unit['unit_id']])})
    sanity = ce.auc_summary(sanity_events, ('clean', 'sanity_hi', 'sanity_lo'))
    save(output/'sanity.json', sanity)
    save(output/'features.json', feats)
    if sanity['paired_queries'] != 90 or not ce.passes_sanity(sanity['within_table']):
        raise ValueError('registered monitor sanity gate failed; main collection blocked')
    manifest = {'protocol': PROTOCOL, 'protocol_commit': PROTOCOL_COMMIT, 'engineering_amendment': ENGINEERING_AMENDMENT, 'model': MODEL,
                'source_hashes': hashes(), 'task_file_sha256': hashlib.sha256(task_path.read_bytes()).hexdigest(),
                'dataset_sha256': datasets, 'queries': queries, 'evidence_units': evidence_units,
                'units': make_units(queries, evidence_units, feats), 'sanity': sanity,
                'python': platform.python_version(), 'max_tokens_per_request': 1536,
                'max_requests_code': 4, 'max_tools_code': 3, 'expected': 810}
    validate_manifest(manifest)
    save(output/'manifest.json', manifest)
    print(json.dumps({'manifest_hash': digest(manifest), 'units': len(manifest['units']), 'sanity': sanity}), flush=True)


def validate_manifest(m):
    units = m['units']
    assert len(units) == m['expected'] and len({u['unit_id'] for u in units}) == len(units)
    for u in units:
        assert digest(u['messages']) == u['messages_hash']
        assert u['arm'] in ARMS and u['level'] in dict(LEVELS)
        assert math.isclose(u['candidate'], u['truth']*u['factor'], rel_tol=1e-12)
    groups = {}
    for u in units:
        groups.setdefault((u['evidence_unit'], u['level']), []).append(u)
    for group in groups.values():
        assert {u['arm'] for u in group} == set(ARMS)
        assert len({u['evidence_hash'] for u in group}) == 1
        assert len({u['rows_csv'] for u in group}) == 1
        assert len({u['candidate'] for u in group}) == 1


class TransportFailure(RuntimeError):
    pass


def request(payload, key, call, checkpoint):
    for old in call['attempts']:
        if old['status'] == 'in_flight':
            old['status'] = 'unknown-after-interruption'
    for attempt in range(len(call['attempts']), 3):
        started = time.monotonic()
        row = {'started_utc': utc(), 'attempt': attempt, 'status': 'in_flight'}
        call['attempts'].append(row)
        checkpoint()
        try:
            req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                         headers={'Authorization': 'Bearer '+key, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as response:
                body = json.load(response)
            row.update(status='success', elapsed_seconds=time.monotonic()-started)
            call['provider_response'] = body
            checkpoint()
            return body
        except urllib.error.HTTPError as exc:
            try:
                message = json.loads(exc.read()).get('error', {}).get('message', str(exc.reason))
            except Exception:
                message = str(exc.reason)
            row.update(status='http_error', http_status=exc.code, message=message.replace(key, '[redacted]')[:600])
            retry = exc.code in (408, 429, 500, 502, 503, 504)
        except (TimeoutError, urllib.error.URLError) as exc:
            row.update(status='transport_error', message=str(exc).replace(key, '[redacted]')[:600])
            retry = True
        row['elapsed_seconds'] = time.monotonic()-started
        checkpoint()
        if not retry:
            raise TransportFailure(f"provider rejected request: {row.get('http_status')}")
        if attempt < 2:
            time.sleep(2**attempt)
    raise TransportFailure('persistent transport failure after bounded attempts')


def run_unit(unit, manifest, output, key, stop=None, manifest_hash=None):
    manifest_hash = manifest_hash or digest(manifest)
    path = output/'responses'/(unit['unit_id']+'.json')
    record = load(path) if path.exists() else {'unit_id': unit['unit_id'], 'manifest_hash': manifest_hash,
             'initial_messages_hash': unit['messages_hash'], 'started_utc': utc(), 'calls': [], 'tools': [], 'status': 'partial'}
    assert record['manifest_hash'] == manifest_hash and record['initial_messages_hash'] == unit['messages_hash']
    if record['status'] == 'completed':
        return record
    start = time.monotonic()
    checkpoint = lambda: save(path, record)
    messages = list(unit['messages'])
    try:
        for index in range(4 if unit['arm'] == 'code' else 1):
            payload = {'model': MODEL, 'messages': messages, 'max_tokens': 1536, 'reasoning_effort': 'low'}
            if len(record['calls']) <= index:
                record['calls'].append({'payload_hash': digest(payload), 'messages': messages, 'attempts': []})
                checkpoint()
            call = record['calls'][index]
            assert call['payload_hash'] == digest(payload)
            if stop is not None and stop.is_set() and 'provider_response' not in call:
                raise TransportFailure('collection halted after another request failed')
            body = call['provider_response'] if 'provider_response' in call else request(payload, key, call, checkpoint)
            choice = (body.get('choices') or [{}])[0]
            raw = (choice.get('message') or {}).get('content') or ''
            if choice.get('finish_reason') in ('length', 'content_filter') or (choice.get('message') or {}).get('refusal'):
                record.update(status='completed', raw=raw, parsed=None, valid=False,
                              terminal_reason='truncated-or-refused')
                break
            parsed = parse_reply(raw)
            if parsed is not None:
                record.update(status='completed', raw=raw, parsed=parsed, valid=True)
                break
            try:
                action = json.loads(raw)
            except (ValueError, TypeError):
                action = None
            if unit['arm'] != 'code' or not isinstance(action, dict) or set(action) != {'python'} or not isinstance(action['python'], str) or len(action['python']) > 10000 or index == 3:
                record.update(status='completed', raw=raw, parsed=None, valid=False, terminal_reason='invalid-final-or-budget-exhausted')
                break
            if len(record['tools']) <= index:
                tool_start = time.monotonic()
                result = execute(unit['rows_csv'], action['python'])
                record['tools'].append({'after_call': index, 'code': action['python'], 'result': result, 'elapsed_seconds': time.monotonic()-tool_start})
                checkpoint()
            result = record['tools'][index]['result']
            messages = messages+[{'role': 'assistant', 'content': raw},
                        {'role': 'user', 'content': 'VISIBLE-ROWS PYTHON RESULT\n'+result['output']+
                         ('\nTool budget exhausted. Give the final four-field JSON now.' if index == 2 else '')}]
    except TransportFailure as exc:
        record.update(status='transport_failure', error=str(exc))
        checkpoint()
        raise
    except Exception:
        record.update(status='engineering_failure')
        checkpoint()
        raise
    record.update(ended_utc=utc(), elapsed_seconds=record.get('elapsed_seconds', 0)+time.monotonic()-start)
    checkpoint()
    return record


def run(output, workers=4):
    manifest = load(output/'manifest.json')
    validate_manifest(manifest)
    if manifest['source_hashes'] != hashes():
        raise ValueError('runner changed since freeze; do not mix code versions')
    key = os.environ.get('GEMINI_API_KEY') or getpass.getpass('Gemini key (hidden): ')
    if not key:
        raise ValueError('API key required')
    config = {'manifest_hash': digest(manifest), 'source_hashes': hashes(), 'model': MODEL,
              'endpoint': ENDPOINT, 'reasoning_effort': 'low', 'max_tokens': 1536}
    if (output/'config.json').exists() and load(output/'config.json') != config:
        raise ValueError('resume config mismatch')
    save(output/'config.json', config)
    todo, completed = [], 0
    for unit in manifest['units']:
        path = output/'responses'/(unit['unit_id']+'.json')
        old = load(path) if path.exists() else None
        if old is not None:
            assert old['manifest_hash'] == config['manifest_hash'] and old['initial_messages_hash'] == unit['messages_hash'], 'cached response belongs to a different frozen request'
        if old is not None and old['status'] == 'completed':
            completed += 1
        else:
            todo.append(unit)
    started = time.monotonic()
    stop = threading.Event()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        cursor, pending = iter(todo), {}
        for _ in range(workers):
            unit = next(cursor, None)
            if unit:
                pending[pool.submit(run_unit, unit, manifest, output, key, stop, config['manifest_hash'])] = unit
        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                pending.pop(future)
                try:
                    future.result()
                except Exception:
                    stop.set()
                    for f in pending:
                        f.cancel()
                    save(output/'status.json', {'status': 'stopped-on-error', 'completed': completed, 'expected': manifest['expected'], 'updated_utc': utc()})
                    raise
                completed += 1
                progress = {'status': 'collecting' if completed < manifest['expected'] else 'complete', 'completed': completed,
                            'expected': manifest['expected'], 'updated_utc': utc(), 'current_process_seconds': time.monotonic()-started}
                save(output/'status.json', progress)
                if completed % 15 == 0 or completed == manifest['expected']:
                    print(json.dumps(progress), flush=True)
                unit = next(cursor, None)
                if unit:
                    pending[pool.submit(run_unit, unit, manifest, output, key, stop, config['manifest_hash'])] = unit
    print('Collection complete; run summarize for final paired analysis', flush=True)


def smoke(output):
    if (output/'manifest.json').exists():
        raise ValueError('smoke already frozen')
    df = pd.DataFrame({'group': ['a']*20, 'value': [99., 101.]*10})
    evidence = {'shape': [200, 2], 'columns': list(df.columns), 'dtypes': {k:str(v) for k,v in df.dtypes.items()},
                'sampling_rule': '20 matching rows from synthetic test table', 'rows_csv': df.to_csv(index=False)}
    q = {'task_id': 'synthetic_smoke', 'dataset': 'synthetic.csv', 'query': 'What is the mean value for group a over all matching rows in the full table?',
         'code': "df[df['group']=='a']['value'].mean()", 'column': 'value', 'filter': ['group', 'a'], 'truth': 100., 'tolerance': .01}
    e = {'unit_id': 'synthetic_smoke__expA_0', 'task_id': q['task_id'], 'draw': 0, 'evidence': evidence,
         'column': q['column'], 'filter': q['filter']}
    feat = feature_job(e)
    units = [u for u in make_units([q], [e], [feat]) if u['level'] != 'scale110']
    for u in units:
        if u['arm'] == 'code':
            u['messages'][0]['content'] += '\nEngineering smoke only: execute at least one Python calculation before your final answer.'
            u['messages_hash'] = digest(u['messages'])
    manifest = {'protocol': PROTOCOL+'-engineering-smoke-excluded', 'source_hashes': hashes(), 'units': units, 'expected': 6}
    validate_manifest(manifest)
    save(output/'manifest.json', manifest)
    run(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run', 'smoke'))
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--workers', type=int, choices=(1, 2, 4), default=4)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.output)
    elif args.action == 'smoke':
        smoke(args.output)
    else:
        run(args.output, args.workers)


if __name__ == '__main__':
    main()
