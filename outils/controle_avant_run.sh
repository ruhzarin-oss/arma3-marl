#!/bin/bash
# Refuse de partir si un piege connu est present. Usage : controle_avant_run.sh <job.json>
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
if len(set(j["graines"]))<2: print("REFUS: il faut au moins deux graines distinctes"); sys.exit(1)
EOF
B=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['banc'])" "$JOB")
[ -x "$H/depot/bancs/$B/lancer.sh" ] || { echo "REFUS: banc $B sans lancer.sh executable dans le depot"; ERR=1; }
[ -z "$(git -C $H/depot status --short bancs/$B outils)" ] || { echo "REFUS: bancs/$B ou outils/ non commites"; ERR=1; }
"$TL" 2>/dev/null | grep -Eqi 'UnrealEditor|vmware-vmx|arma3_x64\.exe' && { echo "REFUS: residu present (Unreal, VM ou client Arma), voir C:\\hmt\\stop"; ERR=1; }
LIBRE=$(df --output=avail -BG /mnt/data | tail -n 1 | tr -dc 0-9)
[ "${LIBRE:-0}" -gt 50 ] || { echo "REFUS: ${LIBRE:-?} Go libres, minimum 50"; ERR=1; }
[ $ERR = 0 ] && echo "CONTROLE OK"
exit $ERR
