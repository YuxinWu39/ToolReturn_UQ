#!/usr/bin/env bash
# Start an OpenAI-compatible vLLM server for the P4 agent runs (needs one >= 24 GB GPU, e.g. an A10G).
# The server binds to 127.0.0.1 only. To reach it from another machine, use an SSH tunnel:
#   ssh -L 8000:127.0.0.1:8000 <gpu-host>
#   MODEL=Qwen/Qwen3-8B SERVED=qwen3-8b bash scripts/serve_vllm.sh
set -euo pipefail
MODEL=${MODEL:-Qwen/Qwen3-4B}
SERVED=${SERVED:-qwen3-4b}
PORT=${PORT:-8000}
MAXLEN=${MAXLEN:-16384}

python3 -m pip install -q "vllm>=0.10" "huggingface_hub[cli]"
hf download "$MODEL" >/dev/null

# --enable-auto-tool-choice + hermes parser give OpenAI-style tool calls for Qwen3.
nohup vllm serve "$MODEL" --host 127.0.0.1 --port "$PORT" \
  --max-model-len "$MAXLEN" --gpu-memory-utilization 0.90 --dtype bfloat16 \
  --enable-auto-tool-choice --tool-call-parser hermes \
  --served-model-name "$SERVED" > vllm.log 2>&1 &
for _ in $(seq 1 90); do
  if curl -sf "http://127.0.0.1:$PORT/v1/models" >/dev/null; then echo "vLLM up on 127.0.0.1:$PORT"; exit 0; fi
  sleep 10
done
echo "vLLM did not come up; tail of vllm.log:"; tail -40 vllm.log; exit 1
