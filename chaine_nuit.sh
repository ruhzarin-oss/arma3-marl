#!/bin/bash
# ═══ L ENCHAINEMENT DE LA NUIT ⟨20/08⟩ ═══════════════════════════════════════════════════
# Les trois demandent le SERVEUR : ils ne peuvent pas tourner ensemble, ils se tueraient.
#   1. la douzaine de verification  (deja lancee — on attend qu elle finisse)
#   2. la sonde du gel              (la collision fabriquee : voir la garde AGIR)
#   3. la nuit politique 2 x 67     (n ~ 107 comme le natif, pour que la resolution
#                                    de 12 points de l ecart soit atteignable)
# ⚠️ Chaque etape ARCHIVE avant que la suivante ne reutilise les noms de session.
cd /home/younes/arma3-marl || exit 1
J=/mnt/data/chaine_nuit.txt; : > $J
dire() { echo "$(date +%H:%M) $*" | tee -a $J; }

dire "attente de la douzaine..."
while pgrep -f douzaine_coups.sh > /dev/null; do sleep 20; done
dire "douzaine finie"
mkdir -p /mnt/data/preuves/2026-08-20_douzaine
cp -p /mnt/data/douzaine/* /mnt/data/preuves/2026-08-20_douzaine/ 2>/dev/null
dire "douzaine archivee"

for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
dire "SONDE DU GEL — collision fabriquee"
timeout 1800 ./.venv/bin/python -u sonde_gel.py > /mnt/data/sonde_gel.txt 2>&1
dire "sonde gel finie (code $?)"
mkdir -p /mnt/data/preuves/2026-08-20_sonde_gel
cp -p /mnt/data/sonde_gel.txt /mnt/data/harmattan-sandbox/logs/serverSGEL.out /mnt/data/preuves/2026-08-20_sonde_gel/ 2>/dev/null

for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
# ⚠️ ARCHIVER L ANCIEN AVANT QUE LA NUIT NE REUTILISE LES NOMS — lecon du 19/08.
mkdir -p /mnt/data/preuves/2026-08-20_politique_ancienne
cp -p /mnt/data/politique/* /mnt/data/preuves/2026-08-20_politique_ancienne/ 2>/dev/null
rm -f /mnt/data/politique/p*_e*.txt /mnt/data/politique/p*_e*.npz 2>/dev/null
dire "NUIT POLITIQUE — 2 x 67, canal inchange, minuteur derive 640 s"
bash rejeu.sh >> $J 2>&1
dire "═══ CHAINE TERMINEE ═══"
