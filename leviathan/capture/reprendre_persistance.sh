#!/usr/bin/env bash
# reprendre_persistance.sh — relance le monde persistant et ses lecteurs.
#
# ORDRE CRITIQUE : les lecteurs demarrent AUSSITOT que le journal existe, AVANT que la mission ne
# lance la capture. Premiere version fautive : elle attendait quatre minutes apres le lancement,
# alors que la capture demarre 35 s apres l ouverture de la mission — trois minutes d apparitions
# perdues, d ou 26 % de fantomes et 13,6 % de morts sans tueur (le tueur n avait pas d apparition
# enregistree, donc il comptait comme non recense). Meme defaut que le 31/07 au matin, revenu par
# une autre porte : le lecteur doit TOUJOURS preceder ce qu il ecoute.
#
# REGLE DE CHARGE, mesuree : 12 instances de banc + 1 persistante = charge 41 sur 24 fils, avec des
# connexions qui lachent. Le banc est prioritaire, la persistance prend les miettes.
set -u
SB=/mnt/data/harmattan-sandbox
CAP=/home/younes/arma3-marl/leviathan/capture
PY=/home/younes/env_isaaclab/bin/python3
M=${1:-2}

pkill -f "capture_tail.py --journal" 2>/dev/null   # un lecteur orphelin suivrait un journal mort
sleep 2
bash $SB/persist_lancer.sh $M

# le journal est cree par le lanceur : on attend juste qu il existe, puis on ecoute.
for i in $(seq 0 $((M-1))); do
  for _ in $(seq 1 30); do [ -f "$SB/logs/serverP$i.out" ] && break; sleep 1; done
done
SESSION=$(date +%Y%m%d_%H%M%S)
for i in $(seq 0 $((M-1))); do
  setsid nohup $PY $CAP/capture_tail.py --journal $SB/logs/serverP$i.out \
    --instance 10$i --dt 0.2 --horodatage $SESSION > $SB/logs/tail_P$i.out 2>&1 &
  disown
done
sleep 10
echo "persistance reprise : $M instances, session $SESSION (lecteurs branches AVANT la capture)"
pgrep -af "capture_tail.py --journal" | sed 's/.*--journal //;s/ --dt.*//'
