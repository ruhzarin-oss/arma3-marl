#!/bin/bash
# PORTE ZERO - une graine, N repetitions d UNE case (intention x ratio).
# Ecrit <run>/g<G>/resultat.json
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
INST=$(lit instance 0); REPS=$(lit reps 4); DUR=$(lit duree 600); PLAFOND=$(lit plafond_s 16000)
INTENT=$(lit intention 0); RATIO=$(lit ratio 0)
MODS=$(lit mods '!Workshop\@CBA_A3;C:\hmt_mods\@LAMBS_Danger')
PROFIL=/mnt/c/Users/Younes/hmtech$INST; PORT=$((2402 + 10*INST))
ARMA='C:\Program Files (x86)\Steam\steamapps\common\Arma 3\arma3server_x64.exe'

[ "$INST" = "3" ] && { echo "REFUS: l instance 3 est celle de chacal, choisir une autre"; exit 1; }
[ -f "$PROFIL/server.cfg" ] || { echo "profil hmtech$INST sans server.cfg"; exit 1; }
[ "$REPS" -ge 2 ] || { echo "REFUS: $REPS repetitions, il en faut au moins 2 par case"; exit 1; }

# --- la mission part du DEPOT, jamais editee sur place ---------------------
rm -rf "$MPM/PORTE0.Altis"
cp -r "$H/depot/bancs/porte0/mission.Altis" "$MPM/PORTE0.Altis" || { echo "copie de mission ratee"; exit 1; }

# --- le server.cfg est ECRIT, pas suppose ---------------------------------
python3 - "$PROFIL/server.cfg" "$G" "$REPS" "$DUR" "$INTENT" "$RATIO" <<'PY'
import re, sys
cfg, g, reps, dur, intent, ratio = sys.argv[1:7]
t = open(cfg, encoding="utf-8", errors="ignore").read()
t = re.sub(r'template\s*=\s*"[^"]*"', 'template = "PORTE0.Altis"', t)
bloc = ("            P0_GRAINE = %s;\n            P0_REPS = %s;\n            P0_DUREE = %s;\n"
        "            P0_INTENTION = %s;\n            P0_RATIO = %s;\n" % (g, reps, dur, intent, ratio))
t = re.sub(r'\n\s*P0_[A-Z_]+\s*=\s*\d+;', '', t)
t = re.sub(r'\n\s*N1_[A-Z_]+\s*=\s*\d+;', '', t)
t = re.sub(r'(class\s+Params\s*\{)', r'\1\n' + bloc.rstrip('\n'), t, count=1)
if "P0_GRAINE" not in t:
    t = re.sub(r'(template\s*=\s*"PORTE0.Altis";)',
               r'\1\n        class Params {\n' + bloc + '        };', t, count=1)
open(cfg, "w", encoding="utf-8").write(t)
print("server.cfg : PORTE0.Altis, P0_GRAINE=%s REPS=%s DUREE=%s INTENTION=%s RATIO=%s"
      % (g, reps, dur, intent, ratio))
PY

mkdir -p "$OUT"; rm -f "$PROFIL"/*.rpt
PID=$("$PWSH" -NoProfile -Command "\$p=Start-Process -FilePath '$ARMA' -WorkingDirectory 'C:\Program Files (x86)\Steam\steamapps\common\Arma 3' -ArgumentList '-config=C:\Users\Younes\hmtech$INST\server.cfg','-profiles=C:\Users\Younes\hmtech$INST','-name=hmtech$INST','-port=$PORT','-world=Altis','-noSound','-autoInit',\"-mod=$MODS\" -PassThru; \$p.Id" | tr -d '\r ')
[[ "$PID" =~ ^[0-9]+$ ]] || { echo "lancement rate : $PID"; exit 1; }
echo "$PID" > "$OUT/pid"; echo "serveur hmtech$INST PID $PID graine $G intention $INTENT ratio $RATIO port $PORT"

t0=$(date +%s); f=""
while true; do
  sleep 20
  f=$(ls -t "$PROFIL"/*.rpt 2>/dev/null | head -n 1)
  [ -n "$f" ] && grep -aq "PORTE0|FINI|" "$f" && break
  [ $(( $(date +%s) - t0 )) -gt "$PLAFOND" ] && { echo "plafond $PLAFOND s atteint"; break; }
  "$PWSH" -NoProfile -Command "if (-not (Get-Process -Id $PID -ErrorAction SilentlyContinue)) { exit 1 }" || { echo "le serveur est mort avant la fin"; break; }
done
"$PWSH" -NoProfile -Command "Stop-Process -Id $PID -Force -ErrorAction SilentlyContinue"
sleep 5
[ -n "$f" ] || { echo "AUCUN RPT"; echo '{"verdict":"REFUSE","cause":"AUCUN_RPT"}' > "$OUT/resultat.json"; exit 1; }
mv "$f" "$OUT/serveur.rpt"
python3 "$H/depot/bancs/porte0/lire.py" "$OUT/serveur.rpt" "$G" > "$OUT/resultat.json" 2> "$OUT/lire.err"
grep -q '"verdict"' "$OUT/resultat.json" || { echo "lecture sans verdict, voir lire.err"; exit 1; }
echo "graine $G : $(grep -o '\"verdict\": \"[A-Z]*\"' "$OUT/resultat.json" | head -n 1)"
