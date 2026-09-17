#!/bin/bash
# banc des oracles : 3 processus ( simples, botorch x 2 variantes, qdax x 2 variantes ), repetitions 0 a 19
set -e
O=/mnt/data/hmt/oracle; D=/mnt/data/hmt/depot/oracle
mkdir -p $O/resultats $O/journaux; cp $D/*.py $O/code/
cd $O/code
export OMP_NUM_THREADS=2 XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONWARNINGS=ignore
setsid nohup bash -c "/mnt/data/hmt/equation/.venv/bin/python oracles_simples.py $O/resultats/simples.jsonl 20; echo FINI_SIMPLES" > $O/journaux/simples.log 2>&1 < /dev/null &
setsid nohup bash -c "for v in ts_court ts; do for m in W0_nul W1_aiguille W2_quatre W3_large_faible; do $O/env_botorch/bin/python oracle_botorch.py $O/resultats/botorch.jsonl \$m 20 0 \$v; done; done; echo FINI_BOTORCH" > $O/journaux/botorch.log 2>&1 < /dev/null &
setsid nohup bash -c "for v in me4 me8; do for m in W0_nul W1_aiguille W2_quatre W3_large_faible; do $O/env_qdax/bin/python oracle_qdax.py $O/resultats/qdax.jsonl \$m 20 0 \$v; done; done; echo FINI_QDAX" > $O/journaux/qdax.log 2>&1 < /dev/null &
sleep 10; pgrep -af "oracle_|oracles_simples" | grep -v pgrep | cut -c1-120
