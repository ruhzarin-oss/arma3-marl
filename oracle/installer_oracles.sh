#!/bin/bash
# Deux environnements separes : BoTorch ( torch ) et QDax ( JAX ). Rien n'est touche dans l'environnement d'EvoGP.
B=/mnt/data/hmt/oracle; mkdir -p $B; cd $B
MM=/mnt/data/hmt/evogp/bin/micromamba; export MAMBA_ROOT_PREFIX=/mnt/data/hmt/evogp/mamba
echo "== botorch $(date +%H:%M)"
[ -d $B/env_botorch ] || $MM create -y -q -p $B/env_botorch -c conda-forge python=3.12 pip
$B/env_botorch/bin/python -m pip install -q torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
$B/env_botorch/bin/python -m pip install -q botorch numpy scipy 2>&1 | tail -2
$B/env_botorch/bin/python -c "import torch, botorch, gpytorch; print('BOTORCH_OK', botorch.__version__, gpytorch.__version__, torch.cuda.is_available())"
echo "== qdax $(date +%H:%M)"
[ -d $B/env_qdax ] || $MM create -y -q -p $B/env_qdax -c conda-forge python=3.11 pip
$B/env_qdax/bin/python -m pip install -q "jax[cuda12]" 2>&1 | tail -2
$B/env_qdax/bin/python -m pip install -q qdax 2>&1 | tail -3
XLA_PYTHON_CLIENT_PREALLOCATE=false $B/env_qdax/bin/python -c "import jax, qdax; print('QDAX_OK', qdax.__version__ if hasattr(qdax,'__version__') else '?', jax.__version__, jax.devices())"
echo "== fini $(date +%H:%M)"
