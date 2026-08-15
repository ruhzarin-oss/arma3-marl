#!/bin/bash
cd /home/younes/arma3-marl
L=/mnt/data/harmattan-sandbox/logs
# ── 1. attendre la fin des baselines ──
while pgrep -f "un_bras.sh" > /dev/null; do sleep 30; done
echo "=== baselines terminees ==="
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
sleep 8
# ── 2. LE VERBE : le feu force mord-il ? (~12 min) ──
echo "=== BANC DU FEU FORCE ==="
sed -i "s/template *= *\"[A-Za-z0-9_.]*\"/template = \"FeuForce.Stratis\"/" $L/../staging/serverSI.cfg
rm -f $L/feu_force.out
bash relancer.sh 6002 $L/../staging/serverSI.cfg $L/../profilesSI $L/feu_force.out 2>&1 | tail -1
for w in $(seq 1 240); do grep -q "HMT|FF|TERMINE" $L/feu_force.out 2>/dev/null && break; sleep 5; done
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done
sleep 8
# ── 3. LE GESTE : le feu-et-mouvement scripte (~45 min) ──
echo "=== BRAS SCRIPTE ==="
bash /mnt/c/Users/Public/un_bras.sh script 20
echo "=== CHAINE TERMINEE ==="
