#!/bin/bash
# CHACAL : une graine, un palier, un episode. Ecrit <run>/g<G>/resultat.json
# Repris de chacal_nuit.sh : chemins absolus, rien de masque, arret par PID.
set -uo pipefail
R=$1; G=$2; JOB=$3; OUT=$R/g$G
PWSH=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
lit() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2],sys.argv[3]))" "$JOB" "$1" "${2:-}"; }
INST=$(lit instance 3); PAL=$(lit palier 0); PLAFOND=$(lit plafond_s 16000)
# LAMBS est indispensable : sans lui la porte lambs_actif refuse l'episode (mesure du 07/09, run 1125).
MODS=$(lit mods '!Workshop\@CBA_A3;C:\hmt_mods\@LAMBS_Danger')
PROFIL=/mnt/c/Users/Younes/hmtech$INST; PORT=$((2402 + 10*INST))
ARMA='C:\Program Files (x86)\Steam\steamapps\common\Arma 3\arma3server_x64.exe'
[ -f "$PROFIL/server.cfg" ] || { echo "profil hmtech$INST sans server.cfg"; exit 1; }
grep -q CHACAL_GRAINE "$PROFIL/server.cfg" || { echo "server.cfg de hmtech$INST sans CHACAL_GRAINE"; exit 1; }
sed -i "s/CHACAL_GRAINE = [0-9]*;/CHACAL_GRAINE = ${G};/" "$PROFIL/server.cfg"
if grep -q CHACAL_PALIER "$PROFIL/server.cfg"; then
  sed -i "s/CHACAL_PALIER = [0-9]*;/CHACAL_PALIER = ${PAL};/" "$PROFIL/server.cfg"
else
  sed -i "s/CHACAL_GRAINE = \([0-9]*\);/CHACAL_GRAINE = \1;\n            CHACAL_PALIER = ${PAL};/" "$PROFIL/server.cfg"
fi
# ! TOUT PARAMETRE NON ECRIT PAR LE JOB EST UN RESTE DE LA SESSION PRECEDENTE.
# Mesure du 07/09 (run 1355) : CHACAL_DEPART = 3 traine dans server.cfg depuis une
# session de mise au point ; les deux episodes ont saute l'approche (hors_corpus) et
# le detachement a ete detruit par la HMG en 86 s. Le lanceur ecrit donc DEPART,
# IMMORTEL et JOUR a chaque lancement, avec les valeurs du corpus par defaut.
DEPART=$(lit depart 1); IMMORTEL=$(lit immortel 0); JOUR=$(lit jour 0)
for kv in "DEPART=$DEPART" "IMMORTEL=$IMMORTEL" "JOUR=$JOUR"; do
  k=${kv%%=*}; v=${kv#*=}
  grep -q "CHACAL_$k = " "$PROFIL/server.cfg" && sed -i "s/CHACAL_$k = [0-9]*;/CHACAL_$k = ${v};/" "$PROFIL/server.cfg"
done
echo "server.cfg : $(grep -o 'CHACAL_[A-Z_]* = [0-9]*' "$PROFIL/server.cfg" | tr '\n' ' ')"
mkdir -p "$OUT"; mkdir -p "/mnt/c/hmt_bridge/i$INST"
rm -f "$PROFIL"/*.rpt
PID=$("$PWSH" -NoProfile -Command "\$env:HMT_BRIDGE_WIN='C:\hmt_bridge\i$INST'; \$p=Start-Process -FilePath '$ARMA' -WorkingDirectory 'C:\Program Files (x86)\Steam\steamapps\common\Arma 3' -ArgumentList '-config=C:\Users\Younes\hmtech$INST\server.cfg','-profiles=C:\Users\Younes\hmtech$INST','-name=hmtech$INST','-port=$PORT','-world=Altis','-noSound','-autoInit',\"-mod=$MODS\" -PassThru; \$p.Id" | tr -d '\r ')
[[ "$PID" =~ ^[0-9]+$ ]] || { echo "lancement rate : $PID"; exit 1; }
echo "$PID" > "$OUT/pid"; echo "serveur hmtech$INST PID $PID graine $G palier $PAL port $PORT"
t0=$(date +%s); f=""
while true; do
  sleep 20
  f=$(ls -t "$PROFIL"/*.rpt 2>/dev/null | head -n 1)
  [ -n "$f" ] && grep -aq "CHACAL|FINI|" "$f" && break
  [ $(( $(date +%s) - t0 )) -gt "$PLAFOND" ] && { echo "plafond $PLAFOND s atteint"; break; }
  "$PWSH" -NoProfile -Command "if (-not (Get-Process -Id $PID -ErrorAction SilentlyContinue)) { exit 1 }" || { echo "le serveur est mort avant la fin"; break; }
done
"$PWSH" -NoProfile -Command "Stop-Process -Id $PID -Force -ErrorAction SilentlyContinue"
sleep 5
[ -n "$f" ] || { echo "AUCUN RPT"; echo '{"verdict":"REFUSE","cause":"AUCUN_RPT"}' > "$OUT/resultat.json"; exit 1; }
mv "$f" "$OUT/serveur.rpt"
python3 /mnt/data/hmt/depot/bancs/chacal/lire.py "$OUT/serveur.rpt" "$OUT/extrait" "$G" > "$OUT/resultat.json" 2> "$OUT/lire.err"
grep -q '"verdict"' "$OUT/resultat.json" || { echo "lecture sans verdict, voir lire.err"; exit 1; }
echo "graine $G : $(grep -o '"verdict": "[A-Z]*"' "$OUT/resultat.json" | head -n 1)"
