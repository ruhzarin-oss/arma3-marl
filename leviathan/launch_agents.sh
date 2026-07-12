#!/usr/bin/env bash
# launch_agents.sh — rallume la CHAINE AGENTS en mode PAIX : soldats=agents qui tiennent + general Qwen.
LEV=/home/younes/arma3-marl/leviathan
V=/home/younes/arma3-marl/.venv/bin/python
pkill -f fob_driver.py 2>/dev/null
pkill -f general_qwen.py 2>/dev/null
pkill -f agents_hold.py 2>/dev/null
rm -f "$LEV/world_state.json" "$LEV/general_orders.json"
sleep 1
cd "$LEV" || exit 1

# 1) les SOLDATS deviennent des AGENTS qui tiennent (maitre du pont)
setsid "$V" agents_hold.py --steps 1500 --wake 500 </dev/null >/tmp/agents_hold.log 2>&1 &
echo "$(date +%T) agents_hold lance (pid $!)"

# 2) attendre que world_state soit expose
for i in $(seq 1 45); do
  [ -f "$LEV/world_state.json" ] && { echo "$(date +%T) world_state pret"; break; }
  sleep 2
done

# 3) le GENERAL Qwen commande (lit world_state, pas le pont)
setsid "$V" general_qwen.py --loop --period 10 </dev/null >/tmp/agents_general.log 2>&1 &
echo "$(date +%T) general --loop lance (pid $!)"
echo "$(date +%T) CHAINE AGENTS RALLUMEE (mode paix)"
