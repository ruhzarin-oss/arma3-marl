#!/bin/bash
# lance PySR et DSR sur le test A ( amendement 2 ) : 2 processus a 1 thread, priorite basse, depuis le code commite dans le depot
set -e
E=/mnt/data/hmt/equation; D=/mnt/data/hmt/depot/equation
mkdir -p $E/code_pysr $E/code_dsr $E/resultats $E/journaux
cp $D/*.py $E/code_pysr/; cp $D/*.py $E/code_dsr/
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 PYTHONWARNINGS=ignore TF_CPP_MIN_LOG_LEVEL=3
cat > $E/processus_pysr.sh <<'P'
#!/bin/bash
R=/mnt/data/hmt/pysr; export JULIA_DEPOT_PATH=$R/julia_depot PYTHON_JULIAPKG_PROJECT=$R/julia_projet JULIA_NUM_THREADS=1
cd /mnt/data/hmt/equation/code_pysr && nice -n 19 $R/env/bin/python banc_synthetique.py --algos pysr --sortie ../resultats/synthetique_pysr.jsonl; echo FINI_PYSR
cd /mnt/data/hmt/equation/code_dsr && nice -n 19 /mnt/data/hmt/dsr/env/bin/python banc_synthetique.py --algos dsr_100k --tailles 500 --sortie ../resultats/synthetique_dsr_100k.jsonl 2>&1 | grep -E '^dsr_100k '; echo FINI_DSR_100K
P
cat > $E/processus_dsr.sh <<'P'
#!/bin/bash
cd /mnt/data/hmt/equation/code_dsr && nice -n 19 /mnt/data/hmt/dsr/env/bin/python banc_synthetique.py --algos dsr --sortie ../resultats/synthetique_dsr.jsonl 2>&1 | grep -E '^dsr '; echo FINI_DSR
P
pgrep -f 'banc_synthetique.py --algos (pysr|dsr)' >/dev/null && { echo "deja en cours"; exit 1; }
setsid nohup bash $E/processus_pysr.sh > $E/journaux/processus_pysr.log 2>&1 < /dev/null &
setsid nohup bash $E/processus_dsr.sh > $E/journaux/processus_dsr.log 2>&1 < /dev/null &
sleep 8; pgrep -af 'banc_synthetique.py' | cut -c1-120
