#!/bin/bash
cd /home/younes/arma3-marl
echo "=== install stack QLoRA+GRPO ==="; date
.venv/bin/pip install -q transformers peft bitsandbytes trl accelerate datasets 2>&1 | tail -5
echo "PIP_DONE"; .venv/bin/python -c "import transformers,peft,trl,bitsandbytes as bnb; print('transformers',transformers.__version__,'peft',peft.__version__,'bnb',bnb.__version__)" 2>&1 | tail -3
echo "=== download Qwen2.5-14B-Instruct (~28 Go) ==="; date
.venv/bin/python -c "from huggingface_hub import snapshot_download; p=snapshot_download('Qwen/Qwen2.5-14B-Instruct'); print('MODEL_AT', p)" 2>&1 | tail -5
echo "SETUP_DONE"; date
