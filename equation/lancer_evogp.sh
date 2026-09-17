#!/bin/bash
# lance EvoGP ( evogp puis evogp_p01 ) sur le test A puis le test B, un seul processus GPU, depuis le code commite
set -e
E=/mnt/data/hmt/equation; D=/mnt/data/hmt/depot/equation
mkdir -p $E/code_evogp $E/resultats $E/journaux
cp $D/*.py $E/code_evogp/
cd $E/code_evogp
export OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore
PY=/mnt/data/hmt/evogp/env/bin/python
setsid nohup bash -c "$PY banc_synthetique.py --algos evogp,evogp_p01 --sortie ../resultats/synthetique_evogp.jsonl | grep -v 'Generation limit'; \
  $PY banc_arma.py /mnt/c/hmt/tmp/equation/arma_choix.parquet ../resultats/arma_evogp.jsonl evogp,evogp_p01 2>&1 | grep -v 'Generation limit' > ../resultats/lecture_arma_evogp.txt; echo FINI_EVOGP" \
  > $E/journaux/processus_evogp.log 2>&1 < /dev/null &
sleep 20; tail -3 $E/journaux/processus_evogp.log
