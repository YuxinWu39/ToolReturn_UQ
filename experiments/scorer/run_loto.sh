#!/usr/bin/env bash
# P5: train the LOTO ensemble (6 held-out tables x K seeds) then score every P4 eval file. GPU recommended.
#   K=5 bash run_loto.sh            # full P5
#   K=1 EPOCHS=1 bash run_loto.sh   # quick pilot
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-../.venv/bin/python}
mkdir -p ../results
export PYTHONPATH="$(cd .. && pwd):${PYTHONPATH:-}"
K=${K:-5}; EPOCHS=${EPOCHS:-3}
OUT=${OUT:-../../models/scorer}
TABLES="public_penguins_v3.csv public_auto_mpg_v4.csv public_bike_v4.csv public_wine_quality.csv public_abalone.csv public_student.csv"
[ -n "${SKIP_BUILD:-}" ] || $PY build_dataset.py > ../results/scorer_build.log 2>&1
for t in $TABLES; do
  for s in $(seq 0 $((K-1))); do
    name="${t%.csv}_s$s"
    [ -f "$OUT/$name/meta.json" ] && { echo "skip $name"; continue; }
    $PY train_scorer.py --holdout-table "$t" --seed "$s" --epochs "$EPOCHS" ${TRAIN_ARGS:-} --out "$OUT/$name" 2>&1 | grep -v "Warning\|warn\|Loading" | tail -3
  done
done
MEMBERS=$(for t in $TABLES; do for s in $(seq 0 $((K-1))); do echo -n "$OUT/${t%.csv}_s$s "; done; done)
for ev in ../../data/ours/scorer/eval_*_T*.jsonl; do
  case "$ev" in *_scorer.jsonl) continue;; esac
  $PY score_scorer.py --members $MEMBERS --eval "$ev" 2>&1 | grep -v "Warning\|warn\|Loading" | tee "../results/scorer_$(basename "$ev" .jsonl).log"
done
