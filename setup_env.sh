#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
cd ~/arma3-marl
echo "[1/4] Creation du venv Python 3.12 (uv)..."
uv venv --python 3.12 .venv
echo "[2/4] Installation de PyTorch + Gymnasium + PettingZoo + NumPy..."
uv pip install --python .venv/bin/python torch gymnasium pettingzoo numpy
echo "[3/4] Verification de l'environnement..."
.venv/bin/python - <<'PYEOF'
import torch, gymnasium, pettingzoo, numpy
print("python   :", __import__("sys").version.split()[0])
print("torch    :", torch.__version__)
print("CUDA dispo:", torch.cuda.is_available())
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        print("   GPU", i, ":", torch.cuda.get_device_name(i))
print("gymnasium:", gymnasium.__version__)
print("pettingzoo:", pettingzoo.__version__)
print("numpy    :", numpy.__version__)
PYEOF
echo "[4/4] OK - environnement pret dans ~/arma3-marl/.venv"
