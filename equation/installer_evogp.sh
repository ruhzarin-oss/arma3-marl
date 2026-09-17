#!/bin/bash
# installe EvoGP sans sudo : micromamba -> python 3.12 + CUDA 12.6 + gcc 13, torch cu126, compile les noyaux pour la 3090 ( 8.6 )
set -e
B=/mnt/data/hmt/evogp; mkdir -p $B/bin && cd $B
echo "== micromamba $(date +%H:%M)"
[ -x bin/micromamba ] || curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj bin/micromamba
export MAMBA_ROOT_PREFIX=$B/mamba
[ -d $B/env ] || bin/micromamba create -y -q -p $B/env -c conda-forge python=3.12 cuda-toolkit=12.6 gcc_linux-64=13 gxx_linux-64=13 ninja git setuptools wheel
E=$B/env
echo "== torch $(date +%H:%M)"
$E/bin/python -m pip install -q torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
$E/bin/python -m pip install -q numpy pandas pyarrow sympy scikit-learn==1.5.2
echo "== evogp $(date +%H:%M)"
export CUDA_HOME=$E PATH=$E/bin:$PATH CC=$E/bin/x86_64-conda-linux-gnu-gcc CXX=$E/bin/x86_64-conda-linux-gnu-g++ TORCH_CUDA_ARCH_LIST="8.6" MAX_JOBS=2
$E/bin/python -m pip install git+https://github.com/EMI-Group/evogp.git --no-build-isolation 2>&1 | tail -5
$E/bin/python -c "import torch, evogp; print('EVOGP_OK', torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
echo "== fini $(date +%H:%M)"
