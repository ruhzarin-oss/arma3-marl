#!/bin/bash
# Un tour du diable. Appele par diable/tick.ps1 ( tache Windows HMT_DIABLE ). Copie figee : editer le depot
# pendant un tour ne touche pas le tour en cours ( meme remede que file3.sh, 08/09 ).
cd /mnt/data/hmt/depot || exit 1
exec /mnt/data/hmt/evogp/env/bin/python -m diable.tick "$@" 2>&1 | grep -v -E "ConvergenceWarning|warnings.warn|OptimizeWarning|opt_res"
