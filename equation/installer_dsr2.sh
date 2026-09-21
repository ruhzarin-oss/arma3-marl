#!/bin/bash
# Suite de l installation de DSR : l edition de liens echouait ( le Python 3.7 de conda passe --sysroot=/ au lieur de conda, qui cherche /lib64/libc.so.6,
# absent d Ubuntu ). On donne a distutils une commande de lien sans ce sysroot, puis on remet numpy a la version exigee par dso.
set -uo pipefail
R=/mnt/data/hmt/dsr; exec >> $R/installation.log 2>&1
echo "=== SUITE $(date)"; E=$R/env; export PATH=$E/bin:$PATH CC=$E/bin/x86_64-conda-linux-gnu-gcc CXX=$E/bin/x86_64-conda-linux-gnu-g++
export LDSHARED="$CC -pthread -shared -L$E/lib -Wl,-rpath=$E/lib"
export CFLAGS="-I $($E/bin/python -c 'import numpy; print(numpy.get_include())')"
nice -n 19 $E/bin/pip install --no-input -e $R/deep-symbolic-optimization/dso || exit 1
nice -n 19 $E/bin/pip install --no-input --no-deps "numpy==1.19.5" || exit 1
cd $R && OMP_NUM_THREADS=1 TF_CPP_MIN_LOG_LEVEL=3 nice -n 19 $E/bin/python - <<'P' || exit 1
import warnings; warnings.filterwarnings("ignore")
import numpy as np
from dso import DeepSymbolicRegressor
from dso.functions import function_map
print("numpy", np.__version__, "| jetons :", sorted(k for k in function_map if isinstance(k, str)))
for k in ("min", "max", "neg"): print(k, "arite", function_map[k].arity)
try:
    from dso import cyfunc; print("cyfunc : compile")
except Exception as e: print("cyfunc absent :", e)
P
echo "INSTALLATION_DSR_OK $(date)"
