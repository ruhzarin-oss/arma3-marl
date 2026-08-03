#!/usr/bin/env bash
# chaine_nuit.sh — les deux bancs Arma restants, a la suite, un seul serveur a la fois.
#   1) COURBE N2 : la suppression, sur ALTIS, cellules certifiees (terre, >= 700 m)
#   2) BALAYAGE DE RATIO : le point FIBUA certifie, sur STRATIS (FOB Maxwell)
# Les pkill sont ici, dans un fichier sur disque : lances depuis une commande ssh, le motif
# figurerait dans la ligne de commande et le script se tuerait lui-meme (arrive 3 fois).
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2

echo "########## 1/2 — COURBE N2 : SUPPRESSION (Altis) ##########"
bash lancer_banc.sh mesurer_suppression.py --theatre altis --reps 6 --duree 40 \
     --paires 2 --dist 100 --dsup 120 --out courbe_suppression.json
echo "########## fin 1/2 ##########"

echo "########## 2/2 — BALAYAGE DE RATIO (Stratis, FOB Maxwell) ##########"
pkill -f 'server_altis.cfg' 2>/dev/null
sleep 8
bash /mnt/data/harmattan-sandbox/launch_fob.sh
for i in $(seq 1 40); do
  ss -tlnp 2>/dev/null | grep -q 5816 && break
  sleep 5
done
sleep 20
if ! timeout 60 python3 - <<'PY'
import sys
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre
Q = chr(34); P = chr(37)
b = NativeBridge(port=theatre.use('stratis').PORT)
r = b.query('(format [' + Q + 'E monde=' + P + '1 est=' + P + '2' + Q + ', worldName, count (allUnits select {side _x == east})]) call HMT_EMIT;',
            r'E monde=(\S+) est=(\d+)', want=1, timeout=30)
b.close()
print(r[-1].group(0) if r else 'PAS DE REPONSE')
sys.exit(0 if r else 1)
PY
then
  echo "!! pont Stratis muet — balayage non engage"
  exit 2
fi
NAGS="8 12 18" MODES="frontal supfront envelop" REPS=2 STEPS=60 bash balayage_ratio.sh
echo "########## fin 2/2 ##########"
echo CHAINE_DONE
