#!/bin/bash
# ═══ LA SONDE DU PONT — le pont dégradé à la naissance explique-t-il le destin ? ═══
#
# HYPOTHÈSE, assemblée en LISANT le code (revue du 17/08), donc elle entre par une sonde à
# signatures pré-écrites et JAMAIS en verdict ⟨cliquet du 17/08⟩.
#
# CE QUI EST DÉJÀ EXCLU : le bind. S'il avait échoué, le pont ne se serait pas connecté et la
# session aurait avorté — or les sessions mortes créaient bien leur scène. Reste les JETÉS.
#
# SIGNATURES ÉCRITES AVANT DE LANCER
#   (a) LE PONT EST LA CAUSE ......... les mortes ont `jetes > 0`, les vivantes `jetes = 0`,
#                                      SÉPARATION NETTE (chevauchement nul).
#   (b) L'HYPOTHÈSE MEURT ............ `jetes = 0` partout, ou `jetes > 0` partout sans lien
#                                      avec le destin.
#   (c) INDÉCIS ...................... les jetés corrèlent sans séparer — on ne conclut pas,
#                                      et on ne rejoue pas la même sonde en espérant mieux.
#
# n : 12 sessions × 6 tirages, comme la sonde d'unité, pour que les tables se comparent.
# ⚠️ ÈRE 1.2 : ces sessions ne se mélangent PAS avec celles d'ère 1.1 dans une même table.
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/pont; mkdir -p $D
{ echo "socle : $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)"
  echo "pont  : $(stat -c%s /mnt/data/harmattan-sandbox/arma3server/hmt_native_x64.so) o  sha256 $(sha256sum /mnt/data/harmattan-sandbox/arma3server/hmt_native_x64.so | cut -c1-24)"
  echo "commit: $(git rev-parse --short HEAD)"; } > $D/EMPREINTE.txt
cat $D/EMPREINTE.txt
for s in $(seq 1 12); do
  # ⚠️ on ne tue que ce qu'on a lancé — machine partagée.
  if [ -f $D/mes_pids ]; then while read pid; do kill $pid 2>/dev/null; done < $D/mes_pids; fi
  : > $D/mes_pids; sleep 3
  echo "session $s  $(date +%H:%M:%S)  load=$(cut -d' ' -f1 /proc/loadavg)" | tee -a $D/JOURNAL.txt
  HMT_SESSION="_p$s" timeout 400 ./.venv/bin/python -u prevol.py 6 natif 45 > $D/s${s}.txt 2>&1
  pgrep -f arma3server_x64 > $D/mes_pids 2>/dev/null
  R=$(grep -ac "T5 IMMOBILE" $D/s${s}.txt); V=$(grep -a "── 6 tirages" $D/s${s}.txt | grep -o "[0-9]* verts" | head -1)
  P=$(grep -a "pont fin" $D/s${s}.txt | tail -1 | cut -c1-90)
  echo "  → s$s : $V, $R rouges T5 | $P" | tee -a $D/JOURNAL.txt
done
if [ -f $D/mes_pids ]; then while read pid; do kill $pid 2>/dev/null; done < $D/mes_pids; fi
echo "═══ SONDE DU PONT TERMINEE — $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
