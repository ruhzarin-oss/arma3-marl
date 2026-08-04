#!/usr/bin/env bash
# relancer_banc150.sh — serveur neuf pour le banc a 150 m.
# ⟨on cible le processus par son NOM EXACT : un pgrep -f sur la ligne de commande matche
#  aussi le shell qui porte le motif, et on se tue soi-meme. Paye le 04/08.⟩
set -u
LOGS=/mnt/data/harmattan-sandbox/logs
SRV=/mnt/data/harmattan-sandbox/arma3server

cp -f "$LOGS/serverBA.out" "$LOGS/serverBA_banc80.out" 2>/dev/null || true

pkill -x arma3server_x64 2>/dev/null || true
for i in $(seq 1 20); do pgrep -x arma3server_x64 >/dev/null || break; sleep 1; done
if pgrep -x arma3server_x64 >/dev/null; then
  echo "!! le serveur refuse de s arreter"; exit 2
fi
echo "serveur arrete"

: > "$LOGS/serverBA.out"
cd "$SRV" || exit 2
nohup ./arma3server_x64 \
  -config=/mnt/data/harmattan-sandbox/staging/serverBA.cfg \
  -profiles=/mnt/data/harmattan-sandbox/profilesBA \
  -port=6002 -world=Stratis -autoInit \
  -mod="@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment" \
  -serverMod=@LAMBS_Danger \
  >> "$LOGS/serverBA.out" 2>&1 &
disown
sleep 30
pgrep -x arma3server_x64 >/dev/null && echo "serveur reparti, PID $(pgrep -x arma3server_x64)" || { echo "!! non reparti"; exit 2; }
echo "--- premieres lignes du banc ---"
grep "HMT|B150" "$LOGS/serverBA.out" | head -5
