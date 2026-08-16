#!/usr/bin/env bash
# lancer_sonde_drone.sh — monte la mission SondeDrone.Stratis et lance SON instance.
# N installe rien sur une instance qui mesure : port, profil, cfg et log dedies.
# Usage : lancer_sonde_drone.sh [reps]     (defaut 20 ; mettre 2 pour le smoke-test)
set -uo pipefail
SB=/mnt/data/harmattan-sandbox
REPO=/home/younes/arma3-marl
REPS=${1:-20}

MIS="$SB/arma3server/mpmissions/SondeDrone.Stratis"
LOG="$SB/logs/sonde_drone.out"
# MEMES MODS QUE LE JUGE — obligatoire (bug d empreinte de monde du 30/07)
MODS="@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment"

# ── on tue UNIQUEMENT notre instance, jamais celles qui collectent ──
pkill -9 -f "staging/serverDR\.cfg" 2>/dev/null; sleep 3

rm -rf "$MIS"; mkdir -p "$MIS"
cp "$SB/arma3server/mpmissions/Anomalie2.Stratis/mission.sqm" "$MIS/"
cp "$REPO/bancs/socle/socle.sqf"        "$MIS/"
cp "$REPO/bancs/arma/sonde_drone.sqf"   "$MIS/"
cat > "$MIS/init.sqf" <<EOF
if (isServer) then { [] spawn { sleep 5; HMT_DR_REPS = $REPS; execVM "sonde_drone.sqf"; }; };
EOF

cat > "$SB/staging/serverDR.cfg" <<'EOF'
hostname = "Harmattan Sonde Drone";
maxPlayers = 1;
persistent = 1;
class Missions { class M1 { template = "SondeDrone.Stratis"; difficulty = "veteran"; }; };
EOF

mkdir -p "$SB/profilesDR"; : > "$LOG"
cd "$SB/arma3server" || exit 1
# ⚠️ `nohup` EN PLUS de `setsid` : sans lui le serveur meurt avec la session ssh qui l a
# lance (mesure du 16/08 : log a 0 octet, aucun process, la sonde n avait jamais tourne).
HMT_EXT_PORT=5840 LD_LIBRARY_PATH=.:./linux64 nohup setsid ./arma3server_x64 \
  -config="$SB/staging/serverDR.cfg" -profiles="$SB/profilesDR" \
  -port=6082 -world=Stratis -autoInit -mod="$MODS" -serverMod="@LAMBS_Danger" \
  >> "$LOG" 2>&1 < /dev/null &
disown
echo "sonde drone lancee : $REPS reps, port 6082, log $LOG"
echo "duree attendue : ~$(( (REPS * 3 * 58 + 60) / 60 )) min"
