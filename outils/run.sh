#!/bin/bash
# Un run = un job, N graines, un FIN.json. Usage : run.sh <job.json>
set -uo pipefail
H=/mnt/data/hmt; JOB=$1
bash $H/depot/outils/controle_avant_run.sh "$JOB" || { echo "controle refuse pour $(basename "$JOB")"; exit 2; }
B=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['banc'])" "$JOB")
R=$H/runs/$(date +%Y-%m-%d_%H%M)_$B
mkdir -p "$R"; cp "$JOB" "$R/job.json"
# La charge concurrente est ARCHIVEE : un run joue pendant que le projet Drone occupe le GPU
# n'est pas comparable a un run joue sur machine vide. On ne l'interdit pas, on l'ecrit.
/mnt/c/Windows/System32/tasklist.exe 2>/dev/null | grep -Eio 'UnrealEditor[A-Za-z-]*|vmware-vmx|arma3server_x64\.exe|arma3_x64\.exe' | sort | uniq -c > "$R/charge_au_lancement.txt"
exec >> "$R/run.log" 2>&1
echo "DEBUT $(date -Is) commit=$(git -C $H/depot rev-parse --short HEAD) job=$(basename "$JOB")"
echo "charge au lancement : $(tr '\n' ' ' < "$R/charge_au_lancement.txt")"
t0=$(date +%s); RC=0
for G in $(python3 -c "import json,sys;print(*json.load(open(sys.argv[1]))['graines'])" "$R/job.json"); do
  mkdir -p "$R/g$G"
  echo "--- graine $G $(date -Is)"
  bash "$H/depot/bancs/$B/lancer.sh" "$R" "$G" "$R/job.json" || { echo "graine $G : code $?"; RC=1; }
done
python3 - "$R" "$RC" "$t0" <<'EOF'
import json,sys,time,glob,os
r,rc,t0=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
res={f.split('/')[-2]:json.load(open(f)) for f in sorted(glob.glob(r+"/g*/resultat.json"))}
n=len(json.load(open(r+"/job.json"))["graines"])
ch=open(r+"/charge_au_lancement.txt").read().split() if os.path.exists(r+"/charge_au_lancement.txt") else []
fin={"fin":time.strftime("%Y-%m-%dT%H:%M:%S"),"duree_s":int(time.time())-t0,"code":rc,
     "graines_attendues":n,"graines_lues":len(res),
     "charge_au_lancement":" ".join(ch),
     "verdict":"COMPLET" if rc==0 and len(res)==n else "ECHEC","resultats":res}
json.dump(fin,open(r+"/FIN.json","w"),indent=1,ensure_ascii=False)
print("FIN",fin["verdict"],fin["duree_s"],"s")
EOF
python3 $H/depot/outils/etat.py 2>&1 | tail -n 1
