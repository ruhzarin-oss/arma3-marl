#!/usr/bin/env bash
# launch_demo.sh — demo live : combat FS-agents vs defenseurs-agents, dirige par le GENERAL Qwen.
# Le DRIVER reste seul maitre du pont ; le GENERAL lit world_state.json (pas de collision).
LEV=/home/younes/arma3-marl/leviathan
V=/home/younes/arma3-marl/.venv/bin/python
LOGD=/tmp/demo_driver.log
LOGG=/tmp/demo_general.log

pkill -f fob_driver.py 2>/dev/null
pkill -f general_qwen.py 2>/dev/null
rm -f "$LEV/world_state.json" "$LEV/general_orders.json"
sleep 1
cd "$LEV" || exit 1

# 1) DRIVER --fight (spawn FS sur Maxwell + arme les defenseurs + ecrit world_state + lit le focus)
setsid "$V" fob_driver.py --fight --steps 140 </dev/null >"$LOGD" 2>&1 &
DPID=$!
echo "$(date +%T) driver --fight lance (pid $DPID)"

# 2) attendre que le driver expose la situation (world_state frais) avant de lancer le general
for i in $(seq 1 45); do
  [ -f "$LEV/world_state.json" ] && { echo "$(date +%T) world_state pret (apres ${i}x2s)"; break; }
  kill -0 $DPID 2>/dev/null || { echo "$(date +%T) driver mort avant world_state (voir $LOGD)"; exit 1; }
  sleep 2
done

# 3) GENERAL --loop (lit world_state, ne touche jamais le pont -> zero collision)
setsid "$V" general_qwen.py --loop --period 8 </dev/null >"$LOGG" 2>&1 &
GPID=$!
echo "$(date +%T) general --loop lance (pid $GPID)"

# 4) suivre le combat jusqu'a la fin du driver, puis couper le general
wait $DPID
kill $GPID 2>/dev/null
echo "$(date +%T) DEMO TERMINEE"
