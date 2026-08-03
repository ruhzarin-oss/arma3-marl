#!/bin/bash
# La certification : les MEMES doctrines, dans le vrai jeu. Serveur neuf d'abord.
LEV=/home/younes/arma3-marl/leviathan
bash $LEV/relancer_meltemi.sh >/dev/null 2>&1
for i in $(seq 1 30); do ss -tlnp 2>/dev/null | grep -q 5826 && break; sleep 5; done
sleep 10
cd $LEV
for D in frontal flanc; do
  echo "=== doctrine $D ==="
  python3 banc_arma.py --theatre altis --doctrine $D --seances 3 --duree 200
  sleep 5
done
echo CERTIF_TERMINEE
