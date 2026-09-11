#!/bin/bash
# Refuse de partir si un piege connu est present. Usage : controle_avant_run.sh <job.json>
#
# ! LES RESIDUS SONT PAR BANC, PAS ABSOLUS (08/09/2026).
# Le projet Drone tourne en parallele du projet Arma : son editeur Unreal est un OUTIL DE TRAVAIL,
# pas un residu. Un controle qui refuse tout job des qu'Unreal tourne bloquerait toutes les nuits
# Arma. Le job declare donc ce qu'il TOLERE ; ce qui n'est pas tolere reste un refus.
#   "tolere": ["UnrealEditor", "vmware-vmx"]
# Ce qui n'est jamais tolerable garde son refus : un client arma3_x64 vole le pont de l'instance.
set -u
H=/mnt/data/hmt; JOB=${1:-}; ERR=0
TL=/mnt/c/Windows/System32/tasklist.exe
[ -f $H/.temoin ] || { echo "REFUS: temoin absent, /mnt/data n'est pas le bon disque"; ERR=1; }
[ -n "$JOB" ] && [ -f "$JOB" ] || { echo "REFUS: job introuvable '$JOB'"; exit 1; }
python3 - "$JOB" <<'EOF' || ERR=1
import json,sys
j=json.load(open(sys.argv[1]))
for k in ("banc","graines","instance","plafond_s"):
    if k not in j: print("REFUS: champ manquant :",k); sys.exit(1)
# ! LA REGLE DE NON-SINGULARITE A DEUX FORMES, PAS UNE.
# Deux graines distinctes protegent d un monde particulier. Mais une VIGNETTE
# veut l inverse : le MEME monde rejoue, parce que l alea du moteur n est pas
# seme et qu un episode n est pas reproductible. Rejouer 20 fois la graine 7
# mesure l etendue des issues A MONDE FIXE - et sans ce chiffre, aucune
# comparaison a un episode unique n est attribuable.
# Ce qui reste interdit dans les deux cas : UN seul episode.
g=len(set(j["graines"])); r=int(j.get("repetitions",1))
if r<1: print("REFUS: repetitions vaut",r,", minimum 1"); sys.exit(1)
if g<2 and r<5:
    print("REFUS: episode singulier -", g, "graine(s) distincte(s) et", r, "repetition(s).")
    print("       il faut AU MOINS DEUX GRAINES DISTINCTES (il en manque", 2-g, ")")
    print("       OU repetitions >= 5 (il en manque", 5-r, ")")
    sys.exit(1)
EOF
B=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['banc'])" "$JOB")
[ -x "$H/depot/bancs/$B/lancer.sh" ] || { echo "REFUS: banc $B sans lancer.sh executable dans le depot"; ERR=1; }
[ -z "$(git -C $H/depot status --short bancs/$B outils)" ] || { echo "REFUS: bancs/$B ou outils/ non commites"; ERR=1; }

# --- residus : ce que le job ne tolere pas
TOL=$(python3 -c "import json,sys;print(' '.join(json.load(open(sys.argv[1])).get('tolere',[])))" "$JOB")
# --- le LABO (instance 9) : un serveur de plus change la charge du run. Refus, sauf "labo" tolere.
PL=$H/etat/labo_arma.pid
INSTJ=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('instance'))" "$JOB")
if [ -s "$PL" ] && [ "$INSTJ" != "9" ]; then
  PLABO=$(tr -dc 0-9 < "$PL")
  if "$TL" /FI "PID eq $PLABO" 2>/dev/null | grep -qi arma3server; then
    echo " $TOL " | grep -qi " labo " || { echo "REFUS: le serveur du labo tourne (PID $PLABO) et le job ne tolere pas \"labo\""; ERR=1; }
  fi
fi
SNAP=$("$TL" 2>/dev/null | grep -Eio 'UnrealEditor[A-Za-z-]*|vmware-vmx|arma3_x64\.exe' | sort | uniq -c | tr '\n' ' ')
for p in UnrealEditor vmware-vmx 'arma3_x64\.exe'; do
  nom=$(echo "$p" | sed 's/\\\.exe//')
  echo " $TOL " | grep -qi " $nom " && continue
  "$TL" 2>/dev/null | grep -Eqi "$p" && { echo "REFUS: $nom tourne et n'est pas dans \"tolere\" du job (voir C:\\hmt\\stop)"; ERR=1; }
done
[ -n "$SNAP" ] && echo "  charge concurrente au lancement : $SNAP"

LIBRE=$(df --output=avail -BG /mnt/data | tail -n 1 | tr -dc 0-9)
[ "${LIBRE:-0}" -gt 50 ] || { echo "REFUS: ${LIBRE:-?} Go libres, minimum 50"; ERR=1; }
[ $ERR = 0 ] && echo "CONTROLE OK"
exit $ERR
