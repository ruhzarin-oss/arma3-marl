#!/bin/bash
# Un run = un job, N graines, un FIN.json. Usage : run.sh <job.json>
set -uo pipefail
H=/mnt/data/hmt; JOB=$1
bash $H/depot/outils/controle_avant_run.sh "$JOB" || exit 2
B=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['banc'])" "$JOB")
R=$H/runs/$(date +%Y-%m-%d_%H%M)_$B
mkdir -p "$R"; cp "$JOB" "$R/job.json"
exec >> "$R/run.log" 2>&1
echo "DEBUT $(date -Is) commit=$(git -C $H/depot rev-parse --short HEAD) job=$(basename "$JOB")"
t0=$(date +%s); RC=0
for G in $(python3 -c "import json,sys;print(*json.load(open(sys.argv[1]))['graines'])" "$R/job.json"); do
  mkdir -p "$R/g$G"
  echo "--- graine $G $(date -Is)"
  bash "$H/depot/bancs/$B/lancer.sh" "$R" "$G" "$R/job.json" || { echo "graine $G : code $?"; RC=1; }
done
python3 - "$R" "$RC" "$t0" <<'EOF'
import json,sys,time,glob
r,rc,t0=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
res={f.split('/')[-2]:json.load(open(f)) for f in sorted(glob.glob(r+"/g*/resultat.json"))}
n=len(json.load(open(r+"/job.json"))["graines"])
fin={"fin":time.strftime("%Y-%m-%dT%H:%M:%S"),"duree_s":int(time.time())-t0,"code":rc,
     "graines_attendues":n,"graines_lues":len(res),
     "verdict":"COMPLET" if rc==0 and len(res)==n else "ECHEC","resultats":res}
json.dump(fin,open(r+"/FIN.json","w"),indent=1,ensure_ascii=False)
print("FIN",fin["verdict"],fin["duree_s"],"s")
EOF
python3 $H/depot/outils/etat.py 2>&1 | tail -n 1
