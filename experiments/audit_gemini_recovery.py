import argparse
import collections
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Exploratory chronology audit of recorded Gemini recovery runs.")
parser.add_argument("--path", type=Path, default=Path(__file__).resolve().parents[1] /
                    "data/ours/p4/gemini-3.8-flash/T1/toxic_seed0.jsonl")
args = parser.parse_args()
path = args.path
counts = collections.Counter()
errors = collections.Counter()
examples = collections.defaultdict(list)
for line in path.open():
    row = json.loads(line)
    if not row['metrics']['recovery']:
        continue
    counts['recovery_runs'] += 1
    poisoned = next(event for event in row['tool_events'] if event['was_poisoned'])
    later = [event for event in row['tool_events'] if event['step'] > poisoned['step']]
    python = [event for event in later if event['tool_name'] == 'python_exec']
    failing = [event for event in later if event['returned_observation'].startswith('ERROR:')]
    if failing:
        counts['any_error_after_poison'] += 1
    if python:
        category = 'first_post_poison_python_error' if python[0]['returned_observation'].startswith('ERROR:') else 'first_post_poison_python_success'
        counts[category] += 1
        examples[category].append(row['task_id'])
    if failing and any(event['step'] < failing[0]['step'] and not event['returned_observation'].startswith('ERROR:') for event in python):
        counts['successful_python_before_first_later_error'] += 1
    for event in failing:
        errors[event['returned_observation'].split(':', 2)[1].strip()] += 1
result = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'status': 'exploratory_recount_of_existing_traces', 'counts': dict(counts),
          'error_events_by_class': dict(errors), 'task_ids_by_first_python_outcome': dict(examples),
          'caution': 'Later errors cannot explain the initiation of an earlier successful check. Successful execution is not a validated annotation of intentional verification or semantic correctness.'}
print(json.dumps(result, indent=2))
