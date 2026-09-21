#!/bin/bash
# Installe Deep Symbolic Optimization ( DSR, dso-org ) dans un environnement SEPARE : Python 3.7 + TensorFlow 1.14 ( CPU ), comme l exige son setup.py.
set -uo pipefail
R=/mnt/data/hmt/dsr; mkdir -p $R; exec > $R/installation.log 2>&1
date; MM=/mnt/data/hmt/evogp/bin/micromamba; export MAMBA_ROOT_PREFIX=/mnt/data/hmt/evogp/mamba
[ -d $R/env ] || nice -n 19 $MM create -y -p $R/env -c conda-forge python=3.7 pip git c-compiler cxx-compiler || exit 1
E=$R/env; export PATH=$E/bin:$PATH CC=$E/bin/x86_64-conda-linux-gnu-gcc CXX=$E/bin/x86_64-conda-linux-gnu-g++
nice -n 19 $E/bin/pip install --no-input "numpy==1.19.5" "cython<3" "protobuf==3.20.3" "tensorflow==1.14.0" "numba==0.53.1" "scikit-learn" "sympy" "pandas" "h5py<3" || exit 1
[ -d $R/deep-symbolic-optimization ] || git clone --depth 1 https://github.com/dso-org/deep-symbolic-optimization.git $R/deep-symbolic-optimization || exit 1
export CFLAGS="-I $($E/bin/python -c 'import numpy; print(numpy.get_include())')"
nice -n 19 $E/bin/pip install --no-input -e $R/deep-symbolic-optimization/dso || exit 1
cd $R && OMP_NUM_THREADS=1 nice -n 19 $E/bin/python - <<'P' || exit 1
import numpy as np, warnings; warnings.filterwarnings("ignore")
from dso import DeepSymbolicRegressor
from dso.functions import function_map
print("jetons :", sorted(k for k in function_map if isinstance(k, str)))
for k in ("min", "max", "neg"): print(k, "arite", function_map[k].arity)
P
date; echo INSTALLATION_DSR_OK
