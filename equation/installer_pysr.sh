#!/bin/bash
# Installe PySR ( + Julia, tire par juliapkg ) dans un environnement SEPARE, sans droits administrateur. Meme recette que installer_evogp.sh.
set -uo pipefail
R=/mnt/data/hmt/pysr; mkdir -p $R; exec > $R/installation.log 2>&1
date; MM=/mnt/data/hmt/evogp/bin/micromamba; [ -x $MM ] || MM=$(ls /mnt/data/hmt/evogp/bin/* | head -n 1)
export MAMBA_ROOT_PREFIX=/mnt/data/hmt/evogp/mamba
nice -n 19 $MM create -y -p $R/env -c conda-forge python=3.12 numpy scikit-learn pip || exit 1
export JULIA_DEPOT_PATH=$R/julia_depot PYTHON_JULIAPKG_PROJECT=$R/julia_projet JULIA_NUM_THREADS=1
nice -n 19 $R/env/bin/pip install --no-input pysr || exit 1
# premier import : juliapkg telecharge Julia et SymbolicRegression.jl, puis precompile ( long, une seule fois )
nice -n 19 $R/env/bin/python -c "import pysr; print('pysr', pysr.__version__); from pysr import PySRRegressor; import numpy as np; X=np.random.rand(100,2); y=X[:,0]*2; m=PySRRegressor(niterations=2, populations=2, progress=False, verbosity=0, parallelism='serial', deterministic=True, random_state=0, temp_equation_file=True); m.fit(X,y); print(m.get_best().equation)" || exit 1
date; echo INSTALLATION_PYSR_OK
