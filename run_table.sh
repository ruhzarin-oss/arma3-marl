#!/bin/bash
# Table empirique de masse : boot 16 serveurs Arma, mesure les 7 manœuvres séquentiellement.
SB=/mnt/data/harmattan-sandbox
PY=/mnt/steam/harmattan/venvs/rl/bin/python
N=16; REPS=16
OUT=/home/younes/arma3-marl/table_maneuvers.jsonl
: > "$OUT"
cd /home/younes/arma3-marl

echo "[boot] lancement de $N serveurs..."
bash "$SB/multi_server.sh" $N

echo "[boot] attente du chargement des missions (max 240s)..."
for w in $(seq 1 48); do
  ready=0
  for i in $(seq 0 $((N-1))); do
    grep -q "read from directory" "$SB/logs/server${i}.out" 2>/dev/null && ready=$((ready+1))
  done
  echo "[boot] $ready/$N missions chargées (${w}x5s)"
  [ "$ready" -ge "$N" ] && break
  sleep 5
done
sleep 15   # marge pour que le script de pont soit vivant sur tous

for M in M1 M2 M3 M4 M5 M6 M7; do
  echo ""; echo "############ MESURE $M ############"
  $PY run_maneuver.py --maneuver $M --servers $N --reps $REPS --out "$OUT" --max_steps 500
done

echo ""; echo "############ SYNTHÈSE TABLE ############"
$PY - <<'PYEOF'
import json, collections
rows = collections.defaultdict(list)
for line in open("/home/younes/arma3-marl/table_maneuvers.jsonl"):
    r = json.loads(line)
    if "mil" in r: rows[r["man"]].append(r)
NAMES = {"M1":"appui-assaut(réf)","M2":"double-env","M3":"env-simple","M4":"assaut-massé",
         "M5":"feinte","M6":"infiltration","M7":"échelonnée"}
print("%-4s %-20s %5s %8s %8s %8s %6s" % ("man","nom","n","mil%","cplx%","QRF%","pertes"))
for m in ["M1","M2","M3","M4","M5","M6","M7"]:
    rs = rows.get(m, [])
    if not rs: print("%-4s %-20s   (aucune donnée)" % (m, NAMES[m])); continue
    n=len(rs); mil=100*sum(x["mil"] for x in rs)/n; gp=100*sum(x["garr_pris"] for x in rs)/n
    qs=100*sum(x["qrf_spawn"] for x in rs)/n; pe=100*sum(x["pertes"] for x in rs)/n
    print("%-4s %-20s %5d %7.1f %7.1f %7.1f %5.0f" % (m, NAMES[m], n, mil, gp, qs, pe))
print("\n[baseline M1 scriptée = 72% militaire]")
PYEOF
echo "############ FIN TABLE ############"
