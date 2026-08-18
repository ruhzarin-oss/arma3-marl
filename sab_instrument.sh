#!/bin/bash
# ⚠️ LES SABOTAGES D INSTRUMENT AVANT LA PORTE ⟨Fable, 18/08⟩ : ils certifient le DETECTEUR
# que la ligne 2 de la porte va employer. Regle 18 — le cas echouant s execute avant que le
# critere juge. 15 min contre 75 : si le detecteur est infirme, on l apprend au prix bas.
# PREDICTIONS PRE-ENREGISTREES :
#   gel     → PLANTE 3/3, a l etape T4, detecte vers 30-36 s (et non 60)
#   lenteur → VERT 3/3, duree relevee > 90 s (sinon le controle n a pas mordu)
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/sabinstrument; mkdir -p $D; : > $D/JOURNAL.txt
echo "socle $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf)  commit $(git rev-parse --short HEAD)" | tee -a $D/JOURNAL.txt
for m in gel lenteur; do
  for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
  echo "═══ sabotage « $m » $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
  HMT_SESSION="_I$m" timeout 900 ./.venv/bin/python -u prevol.py 3 $m 45 > $D/$m.txt 2>&1
  echo "  code retour : $?" | tee -a $D/JOURNAL.txt
  tail -8 $D/$m.txt | tee -a $D/JOURNAL.txt
done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ TERMINE $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
