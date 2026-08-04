#!/usr/bin/env bash
# relancer_reprise3.sh — repart sur les 3 configurations qui manquent au banc n°3.
# Le serveur a asserte le 04/08 a 21h01 pendant la config 18.
#
# ⟨on cible le processus par son NOM EXACT : un pgrep -f sur la ligne de commande matche
#  aussi le shell qui porte le motif, et on se tue soi-meme. Paye le 04/08.⟩
set -u
LOGS=/mnt/data/harmattan-sandbox/logs
SRV=/mnt/data/harmattan-sandbox/arma3server
MIS="$SRV/mpmissions/BancArma.Stratis"
DEPOT=/home/younes/arma3-marl/bancs/arma

# LA PARTIE 1 DOIT DEJA ETRE A L ABRI. Le relancement vide serverBA.out.
if [ ! -s "$LOGS/serverBA_escouade3_partie1.out" ]; then
  echo "REFUS : serverBA_escouade3_partie1.out absent ou vide. 17 configurations seraient perdues."
  exit 1
fi
echo "partie 1 a l abri : $(grep -c '|essai|' "$LOGS/serverBA_escouade3_partie1.out") essais"

pkill -x arma3server_x64 2>/dev/null || true
for i in $(seq 1 20); do pgrep -x arma3server_x64 >/dev/null || break; sleep 1; done
if pgrep -x arma3server_x64 >/dev/null; then echo "!! le serveur refuse de s arreter"; exit 2; fi

# LE SQF DES MISSIONS VIT HORS GIT : on recopie depuis le depot, jamais l'inverse.
cp -f "$DEPOT/banc_escouade3_reprise.sqf"    "$MIS/" || exit 2
cp -f "$DEPOT/donnees_escouade3_reprise.sqf" "$MIS/" || exit 2
printf 'if (isServer) then { [] spawn { sleep 6; execVM "banc_escouade3_reprise.sqf"; }; };\n' > "$MIS/init.sqf"
cp -f "$MIS/init.sqf" "$DEPOT/init.sqf"
echo "mission basculee sur banc_escouade3_reprise.sqf"

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
sleep 45
pgrep -x arma3server_x64 >/dev/null || { echo "!! non reparti"; exit 2; }
echo "serveur reparti, PID $(pgrep -x arma3server_x64)"

for i in $(seq 1 30); do
  grep -qE "HMT\|ESC3\|(debut|ECHEC)" "$LOGS/serverBA.out" && break
  sleep 5
done
echo "--- premieres lignes de la reprise ---"
grep "HMT|ESC3" "$LOGS/serverBA.out" | head -4
if grep -q "HMT|ESC3|ECHEC" "$LOGS/serverBA.out"; then echo "!! ECHEC AU DEMARRAGE"; exit 2; fi
grep -q "HMT|ESC3|debut|3|configs" "$LOGS/serverBA.out" \
  && echo "OK : 3 configurations chargees (18, 19, 20), ~14 min" \
  || echo "!! la reprise n a pas annonce 3 configs"
