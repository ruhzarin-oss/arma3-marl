#!/bin/bash
# SONDE-BRACKET frontière (dimension LÉTALITÉ, effectif constant 28) : M2,M4 × {skilled, skilled_hunt} × n=8.
# Encadre le ~50% ET isole le rôle de la boucle de chasse, en une seule sonde. Détaché + log.
set -u
SB=/mnt/data/harmattan-sandbox
PY=/mnt/steam/harmattan/venvs/rl/bin/python
N=16
OUT=/home/younes/arma3-marl/probe_skill.jsonl
: > "$OUT"
cd /home/younes/arma3-marl

echo "[probe2] $(date +%H:%M:%S) boot $N serveurs..."
bash "$SB/multi_server.sh" $N >/dev/null 2>&1
for w in $(seq 1 48); do
  ready=0; for i in $(seq 0 $((N-1))); do grep -q "read from directory" "$SB/logs/server${i}.out" 2>/dev/null && ready=$((ready+1)); done
  [ "$ready" -ge "$N" ] && { echo "[probe2] $N/$N missions chargées"; break; }
  sleep 5
done
sleep 15

for EN in skilled skilled_hunt; do
  for M in M2 M4; do
    echo "[probe2] $(date +%H:%M:%S) ### $M vs $EN (n=8) ###"
    $PY run_maneuver.py --maneuver $M --servers $N --reps 8 --out "$OUT" --max_steps 500 --enemy $EN
  done
done

pkill -9 -f arma3server_x64
echo "[probe2] $(date +%H:%M:%S) === SYNTHÈSE ==="
$PY - <<'PYEOF'
import json, collections
rows = collections.defaultdict(list)
for line in open("/home/younes/arma3-marl/probe_skill.jsonl"):
    r = json.loads(line)
    if "mil" in r: rows[(r["enemy"], r["man"])].append(r)
print("défense       manœuvre |  n | mil% | garr% | pertes%")
for (en, m), rs in sorted(rows.items()):
    n=len(rs); mil=100*sum(x["mil"] for x in rs)/n; gp=100*sum(x["garr_pris"] for x in rs)/n; pe=100*sum(x["pertes"] for x in rs)/n
    print("%-13s %-8s | %2d | %4.0f | %5.0f | %5.0f" % (en, m, n, mil, gp, pe))
for en in ("skilled","skilled_hunt"):
    a=rows.get((en,"M2"),[]); b=rows.get((en,"M4"),[])
    if a and b:
        pm2=100*sum(x["mil"] for x in a)/len(a); pm4=100*sum(x["mil"] for x in b)/len(b)
        print("%-12s : M2=%.0f%% M4=%.0f%% | écart %.0f pts | moy %.0f%%" % (en,pm2,pm4,abs(pm2-pm4),(pm2+pm4)/2))
print("Frontière = défense dont la MOYENNE ~50% ET l'écart M2-M4 net (=signal de sélection).")
PYEOF
echo "[probe2] $(date +%H:%M:%S) FINI"
