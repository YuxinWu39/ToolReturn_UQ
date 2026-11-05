#!/usr/bin/env bash
# Day 1-3: everything that runs on the existing ToxicBench trajectories without a GPU.
# Resumable: re-run the same command after an interruption. Exact commands recorded here (A7).
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
OUT=${OUT:-results}
mkdir -p "$OUT"

"$PY" inventory.py   --strict --out "$OUT/inventory.json"
"$PY" taxonomy.py    --boot 2000 --out "$OUT/taxonomy"
"$PY" range_check.py --boot 2000 --exec-boot 100 --out "$OUT/range_check"
