#!/bin/bash
# LA LENTEUR SEULE — le gel est deja certifie (PLANTE 3/3 a l etape T4, socle 2.10.0), inutile
# de le repayer. PREDICTIONS PRE-ENREGISTREES, socle 2.11.0 :
#   · VERT 3/3 — la lenteur allonge sans figer, la patience-au-progres doit la laisser passer
#   · duree relevee > 90 s — sinon le controle n a pas mordu et il ne prouve rien
#   · aucun silence individuel au-dessus de 27 s (pire cas T4 : 17 + 10)
cd /home/younes/arma3-marl || exit 1
D=/mnt/data/sabinstrument; mkdir -p $D
echo "═══ lenteur seule — socle $(grep -o 'HMT_SOCLE_VERSION = \"[^\"]*\"' bancs/socle/socle.sqf) commit $(git rev-parse --short HEAD) — $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 3
HMT_SESSION="_Ilent2" timeout 900 ./.venv/bin/python -u prevol.py 3 lenteur 45 > $D/lenteur2.txt 2>&1
echo "  code retour : $?" | tee -a $D/JOURNAL.txt
tail -10 $D/lenteur2.txt | tee -a $D/JOURNAL.txt
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
echo "═══ TERMINE $(date +%H:%M) ═══" | tee -a $D/JOURNAL.txt
