#!/bin/bash
# lancer_live.sh — LANCE LE BANC LIVE SANS SE MENTIR.
#
# ATTENTION, piege paye le 11/08 : tuer le serveur ne suffit pas, il faut ATTENDRE que le
# port soit rendu. Sinon le serveur neuf ne peut pas se lier, il meurt, et le pilote parle
# a l ANCIEN — dont l actuateur a un compteur HMT_NN deja avance. Il attend alors la commande
# n+1 pendant que le pilote envoie la commande 1 : plus rien ne passe, dans les deux sens,
# et aucun message d erreur ne le dit.
cd /home/younes/arma3-marl
for P in $(pgrep -f "[b]anc_live\.py"); do kill "$P" 2>/dev/null; done
for P in $(pgrep -x arma3server_x64); do
  if tr '\0' ' ' < /proc/$P/cmdline | grep -q -- "-port=6062"; then kill "$P"; fi
done
for i in $(seq 1 40); do
  vivant=0
  for P in $(pgrep -x arma3server_x64); do
    if tr '\0' ' ' < /proc/$P/cmdline | grep -q -- "-port=6062"; then vivant=1; fi
  done
  libre=1
  ss -ltn 2>/dev/null | grep -q ":5830 " && libre=0
  [ "$vivant" = 0 ] && [ "$libre" = 1 ] && break
  sleep 1
done
if ss -ltn 2>/dev/null | grep -q ":5830 "; then
  echo "REFUS : le port 5830 est encore pris. On ne lance pas un pilote qui parlera au mort."
  exit 1
fi
echo "ports rendus apres ${i}s"
setsid nohup ./.venv/bin/python banc_live.py > /tmp/banc_live.txt 2>&1 < /dev/null &
sleep 4
echo "PID : $(pgrep -f '[b]anc_live\.py' | head -1)"
