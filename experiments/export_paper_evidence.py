#!/usr/bin/env python3
"""Export already reported results and evidence pointers; no fitting or new estimates."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def export(root):
    sources, claims = {}, []

    def source(path, pointer):
        raw = (root / path).read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        sources[path] = sha
        value = json.loads(raw)
        for component in pointer.split('/')[1:]:
            component = component.replace('~1', '/').replace('~0', '~')
            value = value[int(component)] if isinstance(value, list) else value[component]
        return {'file': path, 'sha256': sha, 'json_pointer': pointer, 'value': value}

    def claim(identifier, statement, limits, entries):
        refs = [source(path, pointer) for path, pointer in entries]
        claims.append({'id': identifier, 'statement': statement, 'limits': limits, 'evidence': refs})
        return [r['value'] for r in refs]

    base = 'data/ours/context_pilot/20261107'
    models = {}
    for model in ('gemini-3.8-flash', 'qwen3-8b'):
        cells, contrasts, valid, n = claim(
            'pilot:' + model,
            'No stable matched20-minus-random20 acceptance-discrimination benefit established.',
            'Selected 12 queries, 6 tables; one completion/cell; not equivalence or absence of effect.',
            [(f'{base}/{model}/summary.json', '/' + key) for key in
             ('cells', 'primary_acceptance_discrimination_contrasts', 'valid', 'n')])
        models[model] = dict(cells=cells, contrasts=contrasts, valid=valid, n=n)
    frozen = {}
    for method in ('0a', '0d'):
        for context in ('head5', 'random20', 'matched20'):
            keys = ('sanity_pass', 'sanity', 'detection', 'policy')
            vals = claim(f'frozen:{method}:{context}',
                         'Extractable statistical signal is reported only after the context-specific sanity gate.',
                         'Same displayed rows; structured query and extra computation differ from model prompting.',
                         [('data/ours/context_evidence/20261107/summary.json', f'/methods/{method}/{context}/{key}') for key in keys])
            frozen[method, context] = dict(zip(keys, vals))
    draws = {}
    for method in ('0a', '0d'):
        keys = ('sanity_pass', 'sanity', 'detection', 'policy', 'per_severity')
        vals = claim('row-draw:' + method,
                     'Statistical signal persists in a selected-query mixture over 20 row draws per query.',
                     'Still 12 queries and 6 tables, no new model replies; severity and query are confounded.',
                     [('data/ours/context_evidence_resample/20261107/summary.json', f'/methods/{method}/{key}') for key in keys])
        draws[method] = dict(zip(keys, vals))
    claim('archive', 'All 72 original replies per model have been verified against frozen requests and scoring.',
          'Archive consistency is not external attestation of weights or a model-sampling replication.',
          [(f'{base}/raw_archive_audit.json', '/models/' + model + '/' + key)
           for model in models for key in ('raw_responses_verified', 'raw_responses_missing')])
    scorer = json.loads((root/'data/ours/revision_cached/20261107/summary.json').read_text())['scorer']
    gates = {}
    for name in sorted(scorer):
        keys = ('clean_coverage', 'gate_pass', 'registered_gain')
        vals = claim('scorer:' + name,
                     'This cached scorer configuration fails detector eligibility gates; its real-corruption gain is withheld.',
                     'No inference about learned UQ as a method family; no new training.',
                     [('data/ours/revision_cached/20261107/summary.json', f'/scorer/{name}/{key}') for key in keys])
        gates[name] = dict(zip(keys, vals))

    def fmt(x):
        return 'withheld' if x is None else f'{x:.3f}'

    def ci(v):
        return '[' + ', '.join(fmt(x) for x in v) + ']'

    tables = {}
    lines = ['| Model | Context | Clean accept / 12 | Corrupted accept / 12 | Uncertain (clean / corrupt) | Invalid (clean / corrupt) |',
             '|---|---|---:|---:|---|---|']
    for model, m in models.items():
        for context in ('head5', 'random20', 'matched20'):
            a, b = m['cells'][context]['0'], m['cells'][context]['1']
            lines.append(f"| {model} | {context} | {a['accept']} | {b['accept']} | {a['uncertain']} / {b['uncertain']} | {a['invalid']} / {b['invalid']} |")
    tables['pilot'] = '\n'.join(lines)
    lines = ['| Model | Matched20 minus random20 | Descriptive 95% interval | Queries / tables |', '|---|---:|---|---|']
    for model, m in models.items():
        c = m['contrasts']['matched20_minus_random20']
        lines.append(f"| {model} | {fmt(c['mean'])} | {ci(c['ci95'])} | {c['queries']} / {c['tables']} |")
    tables['contrasts'] = '\n'.join(lines)
    lines = ['| Evidence | Check | Sanity AUROC | Within-table AUROC [95% interval] | Pooled AUROC | Corrupt flags | Clean flags | Unscorable (clean / corrupt) |', '|---|---|---:|---|---:|---|---|---|']
    for label, cells in [('Original matched20', {m:frozen[m, 'matched20'] for m in ('0a', '0d')}), ('20 draws/query', draws)]:
        for method, c in cells.items():
            assert c['sanity_pass'], 'never export ungated real-corruption efficacy'
            d, a, b = c['detection'], c['policy']['clean'], c['policy']['corrupted']
            lines.append(f"| {label} | {method} | {fmt(c['sanity']['within_table'])} | {fmt(d['within_table'])} {ci(d['ci95'])} | {fmt(d['pooled'])} | {b['flag']}/{b['n']} | {a['flag']}/{a['n']} | {a['unscorable']} / {b['unscorable']} |")
    tables['statistics'] = '\n'.join(lines)
    lines = ['| Context | Check | Sanity AUROC | Paired queries / tables (sanity) | Real-corruption efficacy |', '|---|---|---:|---|---|']
    for (method, context), c in frozen.items():
        s = c['sanity']
        lines.append(f"| {context} | {method} | {fmt(s['within_table'])} | {s['paired_queries']} / {s['tables']} | {'eligible' if c['sanity_pass'] else 'withheld'} |")
    tables['gates'] = '\n'.join(lines)
    lines = ['| Check | Query slice | Corrupt flags | Clean flags | Within-table AUROC [95% interval] |', '|---|---|---|---|---|']
    for method, c in draws.items():
        for name in ('subtle', 'plausible'):
            cell = c['per_severity'][name]
            assert cell['sanity_pass']
            a, b, d = cell['policy']['clean'], cell['policy']['corrupted'], cell['detection']
            lines.append(f"| {method} | {name} | {b['flag']}/{b['n']} | {a['flag']}/{a['n']} | {fmt(d['within_table'])} {ci(d['ci95'])} |")
    tables['severity'] = '\n'.join(lines)
    lines = ['| Cached scorer | Clean interval coverage | Gate | Common P+S tasks / tables | Real-corruption gain |', '|---|---:|---|---|---|']
    for name, c in gates.items():
        g = c['registered_gain']
        lines.append(f"| {name.removeprefix('eval_').removesuffix('_scorer')} | {fmt(c['clean_coverage'])} | {'pass' if c['gate_pass'] else 'fail'} | {g['common_tasks']} / {g['common_tables']} | {g['status']} |")
    tables['scorer'] = '\n'.join(lines)
    # Free-running agent adoption (P4/A-P4b/A-P4-Gemini trajectories). Counting only, no estimation.
    import sys
    sys.path.insert(0, str(root/'experiments'))
    from p4_common import exposure_before

    def used(r):
        return bool(r['metrics'].get('poisoned_answer_used'))

    adoption_sets = [('qwen3-4b', 'T0_agent'), ('qwen3-4b', 'T1'), ('qwen3-4b', 'T3'),
                     ('qwen3-8b', 'T0_agent'), ('qwen3-8b', 'T1'), ('gemini-3.8-flash', 'T1')]
    adoption = {}
    for agent, tier in adoption_sets:
        path = f'data/ours/p4/{agent}/{tier}/toxic_seed0.jsonl'
        raw = (root/path).read_bytes()
        sources[path] = hashlib.sha256(raw).hexdigest()
        runs = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
        fired = [r for r in runs if any(e.get('was_poisoned') for e in r['tool_events'])]
        seen = [r for r in fired if exposure_before(r, next(e for e in r['tool_events'] if e.get('was_poisoned')))['rows'] > 0]
        unseen = [r for r in fired if r not in seen]
        value = {'runs': len(runs), 'fired': len(fired), 'used': sum(map(used, fired)),
                 'seen': len(seen), 'seen_used': sum(map(used, seen)),
                 'unseen': len(unseen), 'unseen_used': sum(map(used, unseen))}
        claims.append({'id': f'adoption:{agent}:{tier}',
                       'statement': 'Counts of poisoned-answer use among toxic runs where the poison fired, split by whether any preview rows were shown before the poisoned call.',
                       'limits': 'Automatic poisoned_answer_used metric; poison_once; preview exposure reconstructed from logged events; not a causal effect of previewing.',
                       'evidence': [{'file': path, 'sha256': sources[path], 'json_pointer': None, 'value': value}]})
        adoption[agent, tier] = value

    def frac(a, b):
        return f'{a}/{b} ({100 * a / b:.0f}%)' if b else 'n/a'

    lines = ['| Agent | Preview tier | Poison fired / runs | Corrupted value used | Used, rows previewed | Used, no rows previewed |',
             '|---|---|---|---|---|---|']
    for (agent, tier), v in adoption.items():
        lines.append(f"| {agent} | {tier} | {v['fired']}/{v['runs']} | {frac(v['used'], v['fired'])} | {frac(v['seen_used'], v['seen'])} | {frac(v['unseen_used'], v['unseen'])} |")
    tables['adoption'] = '\n'.join(lines)

    ks = ('5', '10', '20', '50', '100', '200')
    curve, sanity = claim('ksweep',
                          'Offline row-budget sweep on 168 tasks computable at every k: within-table AUROC by visible random rows.',
                          'Random rows (agents see head rows); 0o/0o* are privileged full-table Monte Carlo references, not optimality bounds.',
                          [('data/ours/ksweep2/summary.json', '/curve_common_tasks'),
                           ('data/ours/ksweep2/summary.json', '/k')])
    lines = ['| Check (within-table AUROC) | ' + ' | '.join(f'k={k}' for k in ks) + ' |', '|---|' + '---:|' * len(ks)]
    for method, label in (('0d', '0d bootstrap check (visible rows only)'),
                          ('0o_star', '0o* privileged reference (knows k-row sampling law)'),
                          ('0o', '0o privileged reference (knows population answer)')):
        lines.append(f'| {label} | ' + ' | '.join(fmt(curve[k][method]['within_table']) for k in ks) + ' |')
    lines.append('| min sanity AUROC (0d, high/low) | ' + ' | '.join(
        fmt(min(sanity[k]['sanity']['0d']['s_hi'], sanity[k]['sanity']['0d']['s_lo'])) for k in ks) + ' |')
    tables['ksweep'] = '\n'.join(lines)

    # Experiment A (A-MONITOR-INTERVENTION, Gemini) and its Qwen3-8B raw/check replication (A-MONITOR-QWEN).
    expa = {}
    for model, folder in (('gemini-3.8-flash', 'data/ours/experiment_a/20261108'),
                          ('qwen3-8b', 'data/ours/experiment_a/20261108_qwen3-8b')):
        cells, primary, direct, follow = claim(
            'monitor:' + model,
            'Paired check-aid intervention on 30 reused queries x 3 matched20 draws; primary check-minus-raw acceptance discrimination.',
            'Six descriptive table clusters; reused queries; upward corruption only; abstention is not correction; no deployment claim.',
            [(f'{folder}/summary.json', '/cells'), (f'{folder}/summary.json', '/primary'),
             ('data/ours/experiment_a/20261108/summary.json', '/direct_monitor/flag_counts'),
             (f'{folder}/summary.json', '/flag_following')])
        expa[model] = dict(cells=cells, primary=primary, flags=direct, follow=follow)
    flag_only, = claim('monitor:flag-only',
                       'Exploratory flag-only policy (accept iff 0d flag absent) versus each model with the check aid.',
                       'Registered in A-MONITOR-QWEN after Gemini results were seen; exploratory, descriptive.',
                       [('data/ours/experiment_a/20261108_qwen3-8b/summary.json', '/exploratory_flag_only')])

    def acc(c, levels):
        return sum(c[l]['accept'] for l in levels), sum(c[l]['n'] for l in levels)

    lines = ['| Decision maker | Clean accepted | x1.10 accepted | x1.50 accepted | Discrimination change [95% interval] |',
             '|---|---:|---:|---:|---|']
    for model, e in expa.items():
        for arm in ('raw', 'check'):
            c = e['cells'][arm]
            change = 'reference' if arm == 'raw' else \
                f"{fmt(e['primary']['discrimination']['mean'])} {ci(e['primary']['discrimination']['ci95'])} vs raw"
            lines.append(f"| {model}, {'rows only' if arm == 'raw' else 'rows + check'} | {'/'.join(map(str, acc(c, ['clean'])))} | "
                         f"{'/'.join(map(str, acc(c, ['scale110'])))} | {'/'.join(map(str, acc(c, ['scale150'])))} | {change} |")
    f = expa['gemini-3.8-flash']['flags']
    lines.append(f"| 0d flag alone (no model) | {f['clean']['n'] - f['clean']['flag']}/{f['clean']['n']} | "
                 f"{f['scale110']['n'] - f['scale110']['flag']}/{f['scale110']['n']} | {f['scale150']['n'] - f['scale150']['flag']}/{f['scale150']['n']} | "
                 + '; '.join(f"{fmt(flag_only[m]['flag_only_minus_raw']['discrimination']['mean'])} "
                             f"{ci(flag_only[m]['flag_only_minus_raw']['discrimination']['ci95'])} vs {m} raw" for m in expa) + ' |')
    tables['monitor'] = '\n'.join(lines)
    lines = ['| Model | Rows + check minus flag alone [95% interval] | Flagged candidates accepted | Compatible candidates rejected |',
             '|---|---|---:|---:|']
    for model in expa:
        d = flag_only[model]['check_minus_flag_only']['discrimination']
        ff, n = expa[model]['follow'], sum(c['n'] for c in expa[model]['cells']['check'].values())
        lines.append(f"| {model} | {fmt(d['mean'])} {ci(d['ci95'])} | {ff['accepted_flagged']}/{ff['flagged']} | {ff['rejected_compatible']}/{n - ff['flagged']} |")
    tables['flagonly'] = '\n'.join(lines)

    provenance, = claim('datasets', 'Versioned source exports, counts, licenses and hashes are documented.',
                         'These describe the saved exports, not arbitrary later upstream dataset versions.',
                         [('data/ours/datasets/PROVENANCE.json', '')])
    urls = {'public_penguins_v3.csv':'https://doi.org/10.5281/zenodo.3960218',
            'public_auto_mpg_v4.csv':'https://doi.org/10.24432/C5859H',
            'public_bike_v4.csv':'https://doi.org/10.24432/C5W894',
            'public_wine_quality.csv':'https://doi.org/10.24432/C56S3T',
            'public_abalone.csv':'https://doi.org/10.24432/C55C7W',
            'public_student.csv':'https://doi.org/10.24432/C5TG7T'}
    lines = ['| Versioned CSV export | Rows | License | Dataset citation | SHA-256 prefix |',
             '|---|---:|---|---|---|']
    for name, meta in provenance.items():
        lines.append(f"| `{name}` | {meta['rows']} | {meta['license']} | [{meta['cite']}]({urls[name]}) | `{meta['sha256'][:12]}` |")
    tables['datasets'] = '\n'.join(lines)
    evidence = {'schema': 'paper-evidence/1.0', 'scope': 'export of existing reported results, no new estimates or model calls',
                'source_sha256': sources, 'claims': claims}
    return evidence, tables


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check', action='store_true', help='verify saved evidence and generated manuscript tables without writing')
    a = p.parse_args()
    evidence, tables = export(ROOT)
    folder = ROOT/'paper'
    path = folder/'manuscript.md'
    original = path.read_text()
    revised = original
    for name, table in tables.items():
        pattern = rf'<!-- BEGIN GENERATED:{name} -->.*?<!-- END GENERATED:{name} -->'
        block = f'<!-- BEGIN GENERATED:{name} -->\n{table}\n<!-- END GENERATED:{name} -->'
        revised, count = re.subn(pattern, lambda m:block, revised, flags=re.S)
        if count != 1:
            raise ValueError(f'expected one manuscript table block: {name}')
    encoded = json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n'
    if a.check:
        if original != revised or (folder/'evidence.json').read_text() != encoded:
            raise SystemExit('Evidence or manuscript table drift; run export_paper_evidence.py')
        print(f'PASS: {len(evidence["claims"])} evidence entries, {len(evidence["source_sha256"])} hashed inputs, {len(tables)} manuscript tables')
    else:
        (folder/'evidence.json').write_text(encoded)
        path.write_text(revised)
        print('Exported existing evidence and generated manuscript tables; no new estimates')


if __name__ == '__main__':
    main()
