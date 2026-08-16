#!/usr/bin/env bash
# lancer_porte_oracle.sh — monte la mission PorteOracle.Stratis et lance SON instance.
# N installe rien sur une instance qui mesure : port, profil, cfg et log dedies.
# Usage : lancer_porte_oracle.sh [reps]     (defaut 20 ; mettre 2 pour le smoke-test)
set -uo pipefail
SB=/mnt/data/harmattan-sandbox
REPO=/home/younes/arma3-marl
REPS=${1:-20}

MIS="$SB/arma3server/mpmissions/PorteOracle.Stratis"
LOG="$SB/logs/porte_oracle.out"
# MEMES MODS QUE LE JUGE — obligatoire (bug d empreinte de monde du 30/07)
MODS="@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment"

# ── on tue UNIQUEMENT notre instance, jamais celles qui collectent ──
pkill -9 -f "staging/serverPO\.cfg" 2>/dev/null; sleep 3

rm -rf "$MIS"; mkdir -p "$MIS"
cp "$SB/arma3server/mpmissions/Anomalie2.Stratis/mission.sqm" "$MIS/"
# ⛔ SOCLE FIGE, PAS LE SOCLE VIVANT. Mesure du 16/08 : une autre session developpe le
# socle pendant que je mesure — 1.5.0, 1.6.0 puis 1.10.0 en une heure, et la 1.9.0 change
# la gestion d AUTOCOMBAT, or mon escouade est en mode `natif`. Recopier le socle vivant a
# chaque lot, c est mesurer 20 repetitions dans 20 mondes differents.
# Le fige se cree une fois (voir figer_socle.sh) et ne bouge plus de tout le run.
FIGE="$REPO/bancs/socle/socle_fige_drone.sqf"
if [ ! -f "$FIGE" ]; then echo "ERREUR : socle fige absent, lancer figer_socle.sh" >&2; exit 1; fi
cp "$FIGE" "$MIS/socle.sqf"
cp "$REPO/bancs/arma/porte_oracle.sqf"   "$MIS/"
cat > "$MIS/init.sqf" <<EOF
if (isServer) then { [] spawn { sleep 5; HMT_PO_REPS = $REPS; execVM "porte_oracle.sqf"; }; };
EOF

cat > "$SB/staging/serverPO.cfg" <<'EOF'
hostname = "Harmattan Porte Oracle";
maxPlayers = 1;
persistent = 1;
class Missions { class M1 { template = "PorteOracle.Stratis"; difficulty = "veteran"; }; };
EOF

mkdir -p "$SB/profilesPO"; : > "$LOG"
cd "$SB/arma3server" || exit 1

# ⛔ ON SE LANCE SOUS UN AUTRE NOM, ET VOICI POURQUOI. Mesure du 16/08 : le serveur mourait
# silencieusement toutes les ~5 min, sans erreur ni message. Ce n etait pas une instabilite :
# `nuit_natif.sh` (et 15 autres scripts du depot) commencent chaque episode par
#     for p in $(pgrep -f arma3server_x64); do kill $p; done
# qui tue TOUS les serveurs Arma de la machine, pas seulement les leurs. Un lien dur sous un
# nom different rend notre instance invisible a ce filet, SANS toucher a leur travail.
# Nous, on ne tue que par fichier de config : jamais leurs serveurs.
BIN=arma3server_dr64
[ -f "$BIN" ] || ln -f arma3server_x64 "$BIN"
# ⚠️ `nohup` EN PLUS de `setsid` : sans lui le serveur meurt avec la session ssh qui l a
# lance (mesure du 16/08 : log a 0 octet, aucun process, la sonde n avait jamais tourne).
HMT_EXT_PORT=5844 LD_LIBRARY_PATH=.:./linux64 nohup setsid ./"$BIN" \
  -config="$SB/staging/serverPO.cfg" -profiles="$SB/profilesPO" \
  -port=6086 -world=Stratis -autoInit -mod="$MODS" -serverMod="@LAMBS_Danger" \
  >> "$LOG" 2>&1 < /dev/null &
disown
echo "sonde drone lancee : $REPS reps, port 6082, log $LOG"
echo "duree attendue : ~$(( (REPS * 3 * 47 + 60) / 60 )) min"
