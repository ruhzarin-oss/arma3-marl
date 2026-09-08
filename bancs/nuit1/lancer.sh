#!/bin/bash
# NUIT 1 - une graine, N episodes en ABBA. Ecrit <run>/g<G>/resultat.json
# Modele : bancs/chacal/lancer.sh. Chemins absolus, rien de masque, arret par PID.
#
# ! CE LANCEUR DEPLOIE SA PROPRE MISSION ET ECRIT SON PROPRE `template`.
# Le lanceur de chacal documente la lecon : " tout parametre non ecrit par le job est
# un reste de la session precedente " ( DEPART = 3 traine, deux episodes perdus ).
# Le template en est un : les profils hmtech0-2 pointent sur EchellePol. On ne suppose
# pas qu il est bon, on l ECRIT.
set -uo pipefail
R=$1; G=$2; JOB=$3; OUT=$R/g$G
H=/mnt/data/hmt
PWSH=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
MPM="/mnt/c/Program Files (x86)/Steam/steamapps/common/Arma 3/mpmissions"
lit() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2],sys.argv[3]))" "$JOB" "$1" "${2:-}"; }
INST=$(lit instance 0); EPI=$(lit episodes 24); DUR=$(lit duree 300); PLAFOND=$(lit plafond_s 16000)
MODS=$(lit mods '!Workshop\@CBA_A3;C:\hmt_mods\@LAMBS_Danger')
PROFIL=/mnt/c/Users/Younes/hmtech$INST; PORT=$((2402 + 10*INST))
ARMA='C:\Program Files (x86)\Steam\steamapps\common\Arma 3\arma3server_x64.exe'

[ "$INST" = "3" ] && { echo "REFUS: l instance 3 est celle de chacal, choisir une autre"; exit 1; }
[ -f "$PROFIL/server.cfg" ] || { echo "profil hmtech$INST sans server.cfg"; exit 1; }
[ $((EPI % 4)) -eq 0 ] || { echo "REFUS: $EPI episodes n est pas un multiple de 4, l ABBA serait desequilibre"; exit 1; }

# --- la mission part du DEPOT, jamais editee sur place ---------------------
rm -rf "$MPM/NUIT1.Altis"
cp -r "$H/depot/bancs/nuit1/mission.Altis" "$MPM/NUIT1.Altis" || { echo "copie de mission ratee"; exit 1; }

# --- le server.cfg est ECRIT, pas suppose ---------------------------------
python3 - "$PROFIL/server.cfg" "$G" "$EPI" "$DUR" <<'PY'
import re, sys
cfg, g, epi, dur = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
t = open(cfg, encoding="utf-8", errors="ignore").read()
t = re.sub(r'template\s*=\s*"[^"]*"', 'template = "NUIT1.Altis"', t)
bloc = "            N1_GRAINE = %s;\n            N1_EPISODES = %s;\n            N1_DUREE = %s;\n" % (g, epi, dur)
t = re.sub(r'\n\s*N1_[A-Z_]+\s*=\s*\d+;', '', t)          # on efface d abord les restes
t = re.sub(r'(class\s+Params\s*\{)', r'\1\n' + bloc.rstrip('\n'), t, count=1)
if "N1_GRAINE" not in t:                                    # pas de class Params : on en pose une
    t = re.sub(r'(template\s*=\s*"NUIT1.Altis";)',
               r'\1\n        class Params {\n' + bloc + '        };', t, count=1)
open(cfg, "w", encoding="utf-8").write(t)
print("server.cfg ecrit : template NUIT1.Altis, N1_GRAINE=%s N1_EPISODES=%s N1_DUREE=%s" % (g, epi, dur))
PY

mkdir -p "$OUT"; rm -f "$PROFIL"/*.rpt
PID=$("$PWSH" -NoProfile -Command "\$p=Start-Process -FilePath '$ARMA' -WorkingDirectory 'C:\Program Files (x86)\Steam\steamapps\common\Arma 3' -ArgumentList '-config=C:\Users\Younes\hmtech$INST\server.cfg','-profiles=C:\Users\Younes\hmtech$INST','-name=hmtech$INST','-port=$PORT','-world=Altis','-noSound','-autoInit',\"-mod=$MODS\" -PassThru; \$p.Id" | tr -d '\r ')
[[ "$PID" =~ ^[0-9]+$ ]] || { echo "lancement rate : $PID"; exit 1; }
echo "$PID" > "$OUT/pid"; echo "serveur hmtech$INST PID $PID graine $G episodes $EPI port $PORT"

t0=$(date +%s); f=""
while true; do
  sleep 20
  f=$(ls -t "$PROFIL"/*.rpt 2>/dev/null | head -n 1)
  [ -n "$f" ] && grep -aq "NUIT1|FINI|" "$f" && break
  [ $(( $(date +%s) - t0 )) -gt "$PLAFOND" ] && { echo "plafond $PLAFOND s atteint"; break; }
  "$PWSH" -NoProfile -Command "if (-not (Get-Process -Id $PID -ErrorAction SilentlyContinue)) { exit 1 }" || { echo "le serveur est mort avant la fin"; break; }
done
"$PWSH" -NoProfile -Command "Stop-Process -Id $PID -Force -ErrorAction SilentlyContinue"
sleep 5
[ -n "$f" ] || { echo "AUCUN RPT"; echo '{"verdict":"REFUSE","cause":"AUCUN_RPT"}' > "$OUT/resultat.json"; exit 1; }
mv "$f" "$OUT/serveur.rpt"
python3 "$H/depot/bancs/nuit1/lire.py" "$OUT/serveur.rpt" "$G" > "$OUT/resultat.json" 2> "$OUT/lire.err"
grep -q '"verdict"' "$OUT/resultat.json" || { echo "lecture sans verdict, voir lire.err"; exit 1; }
echo "graine $G : $(grep -o '\"verdict\": \"[A-Z]*\"' "$OUT/resultat.json" | head -n 1)"
