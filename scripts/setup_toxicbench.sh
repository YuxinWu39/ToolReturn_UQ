#!/usr/bin/env bash
# Clone ToxicBench (MIT code, CC BY 4.0 data) at the commit this repo was developed against.
# It is a read-only dependency: never edit files under data/toxicbench/.
set -euo pipefail
cd "$(dirname "$0")/.."
COMMIT=b85bcfbfc277ef92faffdeadc16df70baa8493df
if [ ! -d data/toxicbench/.git ]; then
  git clone https://github.com/turambar928/Toxic_Tool_Bench.git data/toxicbench
fi
git -C data/toxicbench checkout -q "$COMMIT"
echo "ToxicBench at $(git -C data/toxicbench rev-parse --short HEAD)"
