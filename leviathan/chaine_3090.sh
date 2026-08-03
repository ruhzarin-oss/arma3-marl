#!/usr/bin/env bash
# chaine_3090.sh — la chaine GPU de la nuit, dans l'ordre arbitre.
#   G1 rituel des etalons   (en TETE : rien ne se mesure sur un monde non etalonne)
#   G2 re-verdict de l'arc corrige
#   G3 relance de conv g9   (APRES le re-verdict, pas en concurrence)
#   rejeu 3 (agent au champ)
#   G4 page du matin
#
# CINQ processus tiennent sur cette carte, PAS SIX. On attend que les cases finissent.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd /home/younes/arma3-marl || exit 2
J=/tmp/nuit_journal.txt
PY=./.venv/bin/python

echo "" | tee -a "$J"
echo "===== CHAINE 3090 : attente de la liberation de la carte =====" | tee -a "$J"
while pgrep -f 'lire_carte.py --bras' >/dev/null; do sleep 60; done
sleep 30
echo "===== 3090 liberee a $(date '+%H:%M') =====" | tee -a "$J"

echo "" | tee -a "$J"
echo "##### G1 — RITUEL DES ETALONS #####" | tee -a "$J"
timeout -k 60 5400 $PY "$LEV/etalons.py" --poser --eval 1024 2>&1 | tee -a "$J"
echo "G1 : code ${PIPESTATUS[0]}" | tee -a "$J"

echo "" | tee -a "$J"
echo "##### G2 — RE-VERDICT DE L'ARC CORRIGE #####" | tee -a "$J"
timeout -k 60 7200 $PY "$LEV/reverdict_arc2.py" --eval 1024 --latences 2.0,6.0 \
        --out reverdict_arc2.json 2>&1 | tee -a "$J"
echo "G2 : code ${PIPESTATUS[0]}" | tee -a "$J"

echo "" | tee -a "$J"
echo "##### rejeu 3 — l'agent au champ #####" | tee -a "$J"
timeout -k 30 900 $PY "$LEV/rejeu_agent.py" 2>&1 | tee -a "$J"
if [ -s "$LEV/rejeu3_agent_champ.json" ]; then
  (cd "$LEV" && timeout 300 python3 replay_player.py rejeu3_agent_champ.json \
       --out rejeu3_agent_champ.html >/dev/null 2>&1) \
    && echo "  -> leviathan/rejeu3_agent_champ.html" | tee -a "$J"
fi

echo "" | tee -a "$J"
echo "##### G3 — relance de conv g9 #####" | tee -a "$J"
nohup $PY "$LEV/lire_carte.py" --bras conv --graine 9 --sans_repere --rounds 150 \
      --K 8 --ne 1024 --eval 300 --out carte_conv_g9.json > /tmp/carte_conv_g9.log 2>&1 &
echo "conv g9 relancee a $(date '+%H:%M')" | tee -a "$J"

echo "" | tee -a "$J"
echo "##### G4 — page du matin (premiere ecriture) #####" | tee -a "$J"
python3 "$LEV/page_du_matin.py" 2>&1 | tail -3 | tee -a "$J"

# conv g9 finira plus tard : on reecrira la page quand elle aura fini (ou a 7h30).
( LIMITE=$(( $(date +%s) + 21600 ))
  while pgrep -f 'lire_carte.py --bras conv --graine 9' >/dev/null; do
    [ "$(date +%s)" -ge "$LIMITE" ] && break
    sleep 120
  done
  sleep 20
  python3 "$LEV/page_du_matin.py" >> "$J" 2>&1
  echo "PAGE_DU_MATIN_FINALE $(date '+%H:%M')" >> "$J" ) &

echo "CHAINE_3090_DONE" | tee -a "$J"
