#!/bin/bash
# CHACAL : une graine, un palier, un episode. Ecrit <run>/g<G>/resultat.json
# Repris de chacal_nuit.sh : chemins absolus, rien de masque, arret par PID.
set -uo pipefail
R=$1; G=$2; JOB=$3; OUT=$R/g$G
PWSH=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
lit() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2],sys.argv[3]))" "$JOB" "$1" "${2:-}"; }
INST=$(lit instance 3); PLAFOND=$(lit plafond_s 16000)
# LAMBS est indispensable : sans lui la porte lambs_actif refuse l'episode (mesure du 07/09, run 1125).
MODS=$(lit mods '!Workshop\@CBA_A3;C:\hmt_mods\@LAMBS_Danger')
PROFIL=/mnt/c/Users/Younes/hmtech$INST; PORT=$((2402 + 10*INST))
ARMA='C:\Program Files (x86)\Steam\steamapps\common\Arma 3\arma3server_x64.exe'
[ -f "$PROFIL/server.cfg" ] || { echo "profil hmtech$INST sans server.cfg"; exit 1; }

# ! TOUT PARAMETRE NON ECRIT PAR LE JOB EST UN RESTE DE LA SESSION PRECEDENTE.
# Deux fois en deux jours : CHACAL_DEPART = 3 le 07/09 (approche non jouee, detachement detruit),
# puis CHACAL_BRAS = 1 le 08/09 (BRAS TEMOIN : ni observation ni articulation, donc le PLAN n'a
# jamais ete joue alors qu'on croyait le mesurer). Le lanceur ecrit donc TOUS les parametres de
# mission a chaque lancement, avec les valeurs du corpus par defaut. Rien n'est laisse au hasard.
PAL=$(lit palier 0); DEPART=$(lit depart 1); IMMORTEL=$(lit immortel 0); JOUR=$(lit jour 0)
ECHELLE=$(lit echelle 100); DTCS=$(lit dtcs 100)
HMG=$(lit hmg -1); ASSAUT_X=$(lit assaut_x 100)   # -1 = valeur du palier ; 100 = plafond inchange
BRAS_NOM=$(lit bras PLAN)                       # PLAN (le plan en six phases) ou NUL (le temoin)
case "$BRAS_NOM" in
  PLAN) BRAS=0 ;; NUL) BRAS=1 ;;
  *) echo "job invalide : bras vaut '$BRAS_NOM', attendu PLAN ou NUL"; exit 1 ;;
esac
ecrire_param() {   # ecrit la cle si elle existe, l'ajoute sinon
  local k=$1 v=$2
  if grep -q "CHACAL_$k = " "$PROFIL/server.cfg"; then
    sed -i "s/CHACAL_$k = [0-9]*;/CHACAL_$k = ${v};/" "$PROFIL/server.cfg"
  else
    sed -i "0,/class Params/s//class Params/" "$PROFIL/server.cfg"
    sed -i "s/CHACAL_GRAINE = \([0-9]*\);/CHACAL_GRAINE = \1;\n            CHACAL_$k = ${v};/" "$PROFIL/server.cfg"
  fi
}
grep -q CHACAL_GRAINE "$PROFIL/server.cfg" || { echo "server.cfg de hmtech$INST sans CHACAL_GRAINE"; exit 1; }
ecrire_param GRAINE "$G"; ecrire_param PALIER "$PAL"; ecrire_param DEPART "$DEPART"
ecrire_param IMMORTEL "$IMMORTEL"; ecrire_param JOUR "$JOUR"; ecrire_param BRAS "$BRAS"
ecrire_param ECHELLE "$ECHELLE"; ecrire_param DTCS "$DTCS"
ecrire_param HMG "$HMG"; ecrire_param ASSAUT_X "$ASSAUT_X"
echo "server.cfg : $(grep -o 'CHACAL_[A-Z_]* = [0-9]*' "$PROFIL/server.cfg" | tr '\n' ' ') (bras=$BRAS_NOM)"


# ! DEPLOIEMENT : LE DEPOT DOIT ETRE CE QUI TOURNE.
# Le serveur charge MPMissions, pas le depot. Sans cette etape on mesure une mission qu'on n'a
# pas versionnee — le piege qui a coute la mission le 04/09 et 7 bancs le 03/08. On copie dans
# un sas, on compte, on bascule, et on inscrit l'empreinte dans le run.
DEP=/mnt/data/hmt/depot/bancs/chacal/mission.Altis
MPM="/mnt/c/Program Files (x86)/Steam/steamapps/common/Arma 3/MPMissions/CHACAL.Altis"
N=$(find "$DEP" -name '*.sqf' | wc -l)
[ "$N" -ge 9 ] || { echo "depot incomplet : $N sqf, 9 attendus"; exit 1; }
if ! diff -rq "$DEP" "$MPM" >/dev/null 2>&1; then
  rm -rf "$MPM.neuf"; cp -r "$DEP" "$MPM.neuf"
  find "$MPM.neuf" -name '._*' -delete
  M=$(find "$MPM.neuf" -name '*.sqf' | wc -l)
  [ "$M" -ge 9 ] || { echo "copie incomplete : $M sqf"; rm -rf "$MPM.neuf"; exit 1; }
  rm -rf "$MPM.vieux"; [ -d "$MPM" ] && mv "$MPM" "$MPM.vieux"
  mv "$MPM.neuf" "$MPM"; rm -rf "$MPM.vieux"
  echo "mission deployee depuis le depot ($M sqf)"
else
  echo "mission deja a jour"
fi
EMPREINTE=$(cd "$DEP" && find . \( -name '*.sqf' -o -name '*.ext' -o -name '*.sqm' \) | sort | xargs cat | md5sum | cut -c1-12)
echo "empreinte de la mission : $EMPREINTE"
echo "$EMPREINTE" > "$R/empreinte_mission.txt"

mkdir -p "$OUT"; mkdir -p "/mnt/c/hmt_bridge/i$INST"
rm -f "$PROFIL"/*.rpt
PID=$("$PWSH" -NoProfile -Command "\$env:HMT_BRIDGE_WIN='C:\hmt_bridge\i$INST'; \$p=Start-Process -FilePath '$ARMA' -WorkingDirectory 'C:\Program Files (x86)\Steam\steamapps\common\Arma 3' -ArgumentList '-config=C:\Users\Younes\hmtech$INST\server.cfg','-profiles=C:\Users\Younes\hmtech$INST','-name=hmtech$INST','-port=$PORT','-world=Altis','-noSound','-autoInit',\"-mod=$MODS\" -PassThru; \$p.Id" | tr -d '\r ')
[[ "$PID" =~ ^[0-9]+$ ]] || { echo "lancement rate : $PID"; exit 1; }
echo "$PID" > "$OUT/pid"; echo "serveur hmtech$INST PID $PID graine $G palier $PAL bras $BRAS_NOM port $PORT"
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

# ! CONTROLE D IDENTITE : l'episode joue est-il celui qu'on a DEMANDE ?
# C'est ce controle qui manquait le 08/09 : le corpus a ete lu comme « le plan echoue » alors que
# le bras temoin tournait. Un desaccord entre le job et l'en-tete du RPT rend l'episode REFUSE.
python3 - "$OUT/resultat.json" "$G" "$PAL" "$BRAS_NOM" "$DEPART" <<'PY'
import json,sys
p,g,pal,bras,dep = sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5]
d=json.load(open(p)); e=d.get("entete",{})
ecarts=[]
for cle,attendu in (("graine",g),("palier",pal),("bras",bras),("depart",None)):
    if attendu is None: continue
    obtenu=str(e.get(cle,"?"))
    if obtenu!=str(attendu): ecarts.append(f"{cle} demande {attendu}, joue {obtenu}")
if ecarts:
    d["verdict"]="REFUSE"; d["cause_refus"]="EPISODE_NON_CONFORME_AU_JOB: "+" ; ".join(ecarts)
    json.dump(d,open(p,"w"),indent=1,ensure_ascii=False)
    print("  !! EPISODE REFUSE :", "; ".join(ecarts)); sys.exit(1)
print("  identite conforme au job : graine",g,"palier",pal,"bras",bras)
PY
echo "graine $G : $(grep -o '"verdict": "[A-Z]*"' "$OUT/resultat.json" | head -n 1)"
