#!/bin/bash
# lance le banc d'equation ( test A et test B ) en 2 processus, depuis le code commite dans le depot
set -e
E=/mnt/data/hmt/equation; D=/mnt/data/hmt/depot/equation
mkdir -p $E/code $E/resultats $E/journaux
cp $D/*.py $E/code/
cd $E/code
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONWARNINGS=ignore
PY=$E/.venv/bin/python
setsid nohup bash -c "$PY banc_synthetique.py --algos l1,arbre --sortie ../resultats/synthetique.jsonl; \
  $PY banc_arma.py /mnt/c/hmt/tmp/equation/arma_choix.parquet ../resultats/arma.jsonl > ../resultats/lecture_arma.txt 2>&1; \
  $PY banc_synthetique.py --algos gplearn --formules F0,F1 --sortie ../resultats/synthetique.jsonl; echo FINI_1" \
  > $E/journaux/processus_1.log 2>&1 < /dev/null &
setsid nohup bash -c "$PY banc_synthetique.py --algos gplearn --formules F2,F3 --sortie ../resultats/synthetique_2.jsonl; echo FINI_2" \
  > $E/journaux/processus_2.log 2>&1 < /dev/null &
sleep 5; pgrep -af banc_ | grep -v pgrep
