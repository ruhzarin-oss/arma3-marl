#!/usr/bin/env bash
# lancer_banc4.sh — bascule du banc d'escouade n°3 vers le n°4.
#
# ⟨on cible le processus par son NOM EXACT : un pgrep -f sur la ligne de commande matche
#  aussi le shell qui porte le motif, et on se tue soi-meme. Paye le 04/08.⟩
#
# GARDE-FOU : refuse de partir tant que le banc n°3 n'a pas ecrit TERMINE. Couper un run
# pre-enregistre parce qu'on voit venir son echec, c'est encore regarder les donnees pour
# decider. `--force` existe, il faut le taper a la main.
set -u
LOGS=/mnt/data/harmattan-sandbox/logs
SRV=/mnt/data/harmattan-sandbox/arma3server
MIS="$SRV/mpmissions/BancArma.Stratis"
DEPOT=/home/younes/arma3-marl/bancs/arma

if ! grep -q "HMT|ESC3|TERMINE" "$LOGS/serverBA.out" 2>/dev/null; then
  if [ "${1:-}" != "--force" ]; then
    echo "REFUS : le banc n°3 n'a pas fini."
    echo "  dernier essai : $(grep '|essai|' "$LOGS/serverBA.out" | tail -1 | cut -c1-70)"
    echo "  configs vues  : $(grep -c '|config|' "$LOGS/serverBA.out") / 20"
    echo "  relancer avec --force uniquement si vous decidez d'abandonner le banc n°3."
    exit 1
  fi
  echo "!! --force : le banc n°3 est abandonne avant la fin. C'est une decision, pas un accident."
fi

# LE JOURNAL DU BANC 3 EST ARCHIVE AVANT TOUT. Sept bancs ont deja ete perdus.
ARCH="$LOGS/serverBA_escouade3.out"
cp -f "$LOGS/serverBA.out" "$ARCH" || exit 2
echo "banc n°3 archive : $ARCH ($(wc -l < "$ARCH") lignes, $(grep -c '|essai|' "$ARCH") essais)"

# LE SQF DES MISSIONS VIT HORS GIT : on recopie depuis le depot, jamais l'inverse.
cp -f "$DEPOT/banc_escouade4.sqf"     "$MIS/" || exit 2
cp -f "$DEPOT/donnees_escouade4.sqf"  "$MIS/" || exit 2
printf 'if (isServer) then { [] spawn { sleep 6; execVM "banc_escouade4.sqf"; }; };\n' > "$MIS/init.sqf"
cp -f "$MIS/init.sqf" "$DEPOT/init.sqf"
echo "mission basculee sur banc_escouade4.sqf"

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
sleep 45
pgrep -x arma3server_x64 >/dev/null || { echo "!! non reparti"; exit 2; }
echo "serveur reparti, PID $(pgrep -x arma3server_x64)"

# SMOKE TEST : le banc doit avoir CHARGE SES DONNEES et annonce 20 configs.
# Un banc qui demarre sans donnees tourne a vide pendant 96 min sans rien dire.
for i in $(seq 1 30); do
  grep -q "HMT|ESC4|debut" "$LOGS/serverBA.out" && break
  grep -q "HMT|ESC4|ECHEC" "$LOGS/serverBA.out" && break
  sleep 5
done
echo "--- premieres lignes du banc n°4 ---"
grep "HMT|ESC4" "$LOGS/serverBA.out" | head -5
if grep -q "HMT|ESC4|ECHEC" "$LOGS/serverBA.out"; then echo "!! ECHEC AU DEMARRAGE"; exit 2; fi
grep -q "HMT|ESC4|debut|20|configs" "$LOGS/serverBA.out" \
  && echo "OK : 20 configurations chargees, 6 bras, ~96 min" \
  || echo "!! le banc n'a pas annonce 20 configs — verifier donnees_escouade4.sqf"
