#!/bin/bash
# ÉTAPE 1 — TABLE PRÉCISE au cran-frontière `skilled` : M1-M7 × n=16. Taux + classement réel.
# Robuste : continue-on-error par manœuvre, log persistant, nettoie les serveurs à la fin.
set -u
SB=/mnt/data/harmattan-sandbox
PY=/mnt/steam/harmattan/venvs/rl/bin/python
N=16
OUT=/home/younes/arma3-marl/table_skilled.jsonl
: > "$OUT"
cd /home/younes/arma3-marl

echo "[t1] $(date +%H:%M:%S) boot $N serveurs..."
bash "$SB/multi_server.sh" $N >/dev/null 2>&1
for w in $(seq 1 48); do
  ready=0; for i in $(seq 0 $((N-1))); do grep -q "read from directory" "$SB/logs/server${i}.out" 2>/dev/null && ready=$((ready+1)); done
  [ "$ready" -ge "$N" ] && { echo "[t1] $N/$N missions chargées"; break; }
  sleep 5
done
sleep 15

for M in M1 M2 M3 M4 M5 M6 M7; do
  echo "[t1] $(date +%H:%M:%S) ### $M vs skilled (n=16) ###"
  $PY run_maneuver.py --maneuver $M --servers $N --reps 16 --out "$OUT" --max_steps 500 --enemy skilled || echo "[t1] ERREUR sur $M (continue)"
done

pkill -9 -f arma3server_x64
echo "[t1] $(date +%H:%M:%S) === SYNTHÈSE TABLE SKILLED (n=16) ==="
$PY - <<'PYEOF'
import json, collections
rows = collections.defaultdict(list)
for line in open("/home/younes/arma3-marl/table_skilled.jsonl"):
    try: r = json.loads(line)
    except: continue
    if "mil" in r: rows[r["man"]].append(r)
NAMES={"M1":"appui-assaut","M2":"double-env","M3":"env-simple","M4":"massé","M5":"feinte","M6":"infiltration","M7":"échelonnée"}
res=[]
for m,rs in rows.items():
    n=len(rs); res.append((m,100*sum(x["mil"] for x in rs)/n,100*sum(x["garr_pris"] for x in rs)/n,100*sum(x["pertes"] for x in rs)/n,n))
res.sort(key=lambda x:-x[1])
print("rang manœuvre            n  mil%  garr% pertes%")
for i,(m,mil,gp,pe,n) in enumerate(res,1):
    print("%2d  %-3s %-14s %2d %5.1f %5.1f %5.1f" % (i,m,NAMES.get(m,""),n,mil,gp,pe))
if res:
    print("\nMEILLEURE: %s (%.1f%%)  PIRE: %s (%.1f%%)  ÉCART: %.1f pts" % (res[0][0],res[0][1],res[-1][0],res[-1][1],res[0][1]-res[-1][1]))
PYEOF
echo "[t1] $(date +%H:%M:%S) FINI"
