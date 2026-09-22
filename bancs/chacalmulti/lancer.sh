#!/bin/bash
# CHACAL MULTI : un episode = K cellules de la phase 2 dans un seul serveur. Ecrit <run>/g<E>/resultat.json et, par
# cellule, <run>/g<E>/c<k>/resultat.json lu par le lecteur du banc seul.
# Repris de bancs/chacaloracle/lancer.sh : meme demarrage, meme deploiement prouve, meme empreinte.
# Le numero passe en « graine » est celui de l EPISODE ; les graines des mondes sont dans job["episodes"][E].
set -uo pipefail
R=$1; E=$2; JOB=$3; SOUS=${4:-g$E}; OUT=$R/$SOUS
H=/mnt/data/hmt
PWSH=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
lit() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2],sys.argv[3]))" "$JOB" "$1" "${2:-}"; }
INST=$(lit instance 3); PLAFOND=$(lit plafond_s 5400)
MODS=$(lit mods '!Workshop\@CBA_A3;C:\hmt_mods\@LAMBS_Danger')
PROFIL=/mnt/c/Users/Younes/hmtech$INST; PORT=$((2402 + 10*INST))
SRC_CFG="$PROFIL/server.cfg"; CFG="$PROFIL/server_multi.cfg"
[ -f "$SRC_CFG" ] || { echo "profil hmtech$INST sans server.cfg"; exit 1; }
ARMA='C:\Program Files (x86)\Steam\steamapps\common\Arma 3\arma3server_x64.exe'
mkdir -p "$OUT"

# ! LES PARAMETRES : la classe Params de server_multi.cfg est REECRITE EN ENTIER a chaque episode. Les parametres
# communs portent les memes noms et les memes valeurs par defaut que le lanceur du banc seul ; chaque cellule en
# surcharge quelques-uns ( MULTI_C<k>_<NOM> ). Rien n est laisse d une session precedente.
python3 $H/depot/bancs/chacalmulti/parametres.py "$SRC_CFG" "$CFG" "$JOB" "$E" > "$OUT/parametres.txt" || { cat "$OUT/parametres.txt"; echo "parametres refuses"; exit 1; }
tail -n 3 "$OUT/parametres.txt"

# ! DEPLOIEMENT PROUVE ( voir bancs/chacaloracle/lancer.sh, mesure du 08/09 ) : le depot doit etre ce qui tourne.
DEP=$H/depot/bancs/chacalmulti/mission.Altis
MPM="/mnt/c/Program Files (x86)/Steam/steamapps/common/Arma 3/MPMissions/CHACALMULTI.Altis"
N=$(find "$DEP" -name '*.sqf' | wc -l)
[ "$N" -ge 90 ] || { echo "depot incomplet : $N sqf, 90 attendus"; exit 1; }
if ! diff -rq "$DEP" "$MPM" >/dev/null 2>&1; then
  rm -rf "$MPM.neuf"; cp -r "$DEP" "$MPM.neuf"
  find "$MPM.neuf" -name '._*' -delete
  rm -rf "$MPM.vieux"; [ -d "$MPM" ] && mv "$MPM" "$MPM.vieux"
  mv "$MPM.neuf" "$MPM"; rm -rf "$MPM.vieux"
  echo "mission deployee depuis le depot"
else
  echo "mission deja a jour"
fi
if ! diff -rq "$DEP" "$MPM" >/dev/null 2>&1; then
  echo "DEPLOIEMENT NON PROUVE : la mission jouee differe du depot"; diff -rq "$DEP" "$MPM" 2>&1 | head -n 5; exit 1
fi
EMPREINTE=$(cd "$DEP" && find . \( -name '*.sqf' -o -name '*.ext' -o -name '*.sqm' \) | sort | xargs cat | md5sum | cut -c1-12)
echo "empreinte de la mission : $EMPREINTE"; echo "$EMPREINTE" > "$R/empreinte_mission.txt"

mkdir -p "/mnt/c/hmt_bridge/i$INST"
rm -f "$PROFIL"/*.rpt
PID=$("$PWSH" -NoProfile -Command "\$env:HMT_BRIDGE_WIN='C:\hmt_bridge\i$INST'; \$p=Start-Process -FilePath '$ARMA' -WorkingDirectory 'C:\Program Files (x86)\Steam\steamapps\common\Arma 3' -ArgumentList '-config=C:\Users\Younes\hmtech$INST\server_multi.cfg','-profiles=C:\Users\Younes\hmtech$INST','-name=hmtech$INST','-port=$PORT','-world=Altis','-noSound','-autoInit',\"-mod=$MODS\" -PassThru; \$p.Id" | tr -d '\r ')
[[ "$PID" =~ ^[0-9]+$ ]] || { echo "lancement rate : $PID"; exit 1; }
echo "$PID" > "$OUT/pid"; echo "serveur hmtech$INST PID $PID episode $E port $PORT"
t0=$(date +%s); f=""
while true; do
  sleep 20
  f=$(ls -t "$PROFIL"/*.rpt 2>/dev/null | head -n 1)
  [ -n "$f" ] && grep -aq "M|0|MULTI|FINI|" "$f" && break
  [ $(( $(date +%s) - t0 )) -gt "$PLAFOND" ] && { echo "plafond $PLAFOND s atteint"; break; }
  "$PWSH" -NoProfile -Command "if (-not (Get-Process -Id $PID -ErrorAction SilentlyContinue)) { exit 1 }" || { echo "le serveur est mort avant la fin"; break; }
done
"$PWSH" -NoProfile -Command "Stop-Process -Id $PID -Force -ErrorAction SilentlyContinue"
sleep 5
[ -n "$f" ] || { echo "AUCUN RPT"; echo '{"verdict":"REFUSE","cause":"AUCUN_RPT"}' > "$OUT/resultat.json"; exit 1; }
mv "$f" "$OUT/serveur.rpt"
echo "duree murale $(( $(date +%s) - t0 )) s" > "$OUT/duree.txt"
python3 $H/depot/bancs/chacalmulti/lire_multi.py "$OUT/serveur.rpt" "$OUT" "$JOB" "$E" > "$OUT/resultat.json" 2> "$OUT/lire.err"
grep -q '"verdict"' "$OUT/resultat.json" || { echo "lecture sans verdict, voir lire.err"; tail -n 5 "$OUT/lire.err"; exit 1; }
python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print('episode', sys.argv[2], ':', d['verdict'], '|', d.get('resume',''))" "$OUT/resultat.json" "$E"
