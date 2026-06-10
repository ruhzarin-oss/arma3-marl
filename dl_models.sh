#!/bin/bash
cd /home/younes/arma3-marl
for m in Qwen/Qwen2.5-7B-Instruct Qwen/Qwen2.5-14B-Instruct; do
  echo "DL $m $(date +%H:%M)"
  .venv/bin/python -c "from huggingface_hub import snapshot_download; print(snapshot_download(\"$m\"))" 2>&1 | tail -2
done
echo "DL_DONE $(date +%H:%M)"
