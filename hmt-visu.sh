#!/bin/bash
# hmt-visu.sh — SERVEUR VISUEL dédié (mission HMT-EcoleDeGuerre.Altis, port 2302).
# Boot 1 serveur séparé des 16 serveurs de mesure (qui restent sur HarmattanBridge*).
# Rejoindre avec le client Arma : Multijoueur -> LAN -> 127.0.0.1:2302 (ou IP Tailscale).
# Puis lancer une op tracée :  cd ~/arma3-marl && venv-rl run_op_visual.py --maneuver M2
# ⚠️ multi_server.sh fait pkill -9 arma3server_x64 : relancer la table TUE aussi ce serveur.
SB=/mnt/data/harmattan-sandbox
MIS="HMT-EcoleDeGuerre.Altis"
PORT=2302

pkill -f "profiles_visu" 2>/dev/null; sleep 2
rm -f "$SB/arma3server/mpmissions/$MIS/hmt_bridge/"cmd_*.sqf
CFG="$SB/staging/server_visu.cfg"
sed "s/HarmattanBridge\.Altis/$MIS/g" "$SB/staging/server.cfg" > "$CFG"
mkdir -p "$SB/profiles_visu"
: > "$SB/logs/visu.out"
cd "$SB/arma3server"
LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 -config="$CFG" -profiles="$SB/profiles_visu" \
  -port=$PORT -world=Altis -autoInit >> "$SB/logs/visu.out" 2>&1 < /dev/null &
disown
echo "serveur visuel lance : mission $MIS port $PORT (log $SB/logs/visu.out)"
echo "attente du chargement..."
for w in $(seq 1 36); do
  grep -q "read from directory" "$SB/logs/visu.out" 2>/dev/null && { echo "mission chargee."; exit 0; }
  sleep 5
done
echo "⚠️ mission pas confirmee chargee apres 180s — verifier $SB/logs/visu.out"
