#!/bin/bash
cd /home/younes/arma3-marl
L=/mnt/data/harmattan-sandbox/logs
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 8
# 1. LE VERBE, repare : l arme est-elle en main et la boucle tire-t-elle ?
echo "=== FEU FORCE (repare) ==="
sed -i "s/template *= *\"[A-Za-z0-9_.]*\"/template = \"FeuForce.Stratis\"/" $L/../staging/serverSI.cfg
rm -f $L/feu_force.out
bash relancer.sh 6002 $L/../staging/serverSI.cfg $L/../profilesSI $L/feu_force.out 2>&1 | tail -1
for w in $(seq 1 300); do grep -qE "HMT.FF.(TERMINE|ECHEC)" $L/feu_force.out 2>/dev/null && break; sleep 5; done
grep -E "HMT.FF.(ARME|ECHEC)" $L/feu_force.out | head -2
for p in $(pgrep -f arma3server_x64); do kill $p 2>/dev/null; done; sleep 8
# 2. LE GESTE, avec l arme en main
echo "=== BRAS SCRIPTE (arme en main) ==="
bash /mnt/c/Users/Public/un_bras.sh script 20
# 3. LE NATIF, avec FSM rendu
echo "=== BRAS NATIF (FSM rendu) ==="
bash /mnt/c/Users/Public/un_bras.sh natif 20
echo "=== CHAINE 3 TERMINEE ==="
