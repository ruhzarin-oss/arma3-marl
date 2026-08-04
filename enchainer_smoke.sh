#!/usr/bin/env bash
# enchainer_smoke.sh — laisser finir le pilote d'escouade, puis lancer le smoke test.
set -u
LOGS=/mnt/data/harmattan-sandbox/logs
M=/mnt/data/harmattan-sandbox/arma3server/mpmissions/BancArma.Stratis

echo "[1/4] attente de la fin du pilote escouade"
for i in $(seq 1 40); do
  grep -q "HMT|ESC|TERMINE" "$LOGS/serverBA.out" && { echo "  pilote termine"; break; }
  pgrep -x arma3server_x64 >/dev/null || { echo "  !! serveur mort"; break; }
  sleep 30
done
echo "  essais escouade : $(grep -c 'HMT|ESC|essai' "$LOGS/serverBA.out")/100"

echo "[2/4] archivage du journal du pilote"
cp -f "$LOGS/serverBA.out" "$LOGS/serverBA_escouade_pilote.out"

echo "[3/4] bascule sur le smoke test"
echo 'if (isServer) then { [] spawn { sleep 6; execVM "smoke_liberation.sqf"; }; };' > "$M/init.sqf"
bash /home/younes/arma3-marl/relancer_banc150.sh 2>&1 | tail -2

echo "[4/4] attente du smoke test"
for i in $(seq 1 30); do
  grep -q "HMT|SMOKE|TERMINE" "$LOGS/serverBA.out" && { echo "  SMOKE TERMINE"; break; }
  pgrep -x arma3server_x64 >/dev/null || { echo "  !! serveur mort"; break; }
  sleep 20
done
echo "--- releves smoke : $(grep -c 'HMT|SMOKE|releve' "$LOGS/serverBA.out") ---"
grep -E "HMT\|SMOKE\|(phase|liberation|tirs_comptes|ECHEC|terrain)" "$LOGS/serverBA.out"
