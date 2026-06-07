#!/bin/bash
# Table v3 (OP-1 SOCLE) : harnais purgé {QRF-sur-garnison + géo sèche}. 16 serveurs, 7 manœuvres × 16 ops.
# Sortie SÉPARÉE de la v2 (table_maneuvers.jsonl archivée intacte) + synthèse par FAMILLES (la question pré-enregistrée).
SB=/mnt/data/harmattan-sandbox
PY=/mnt/steam/harmattan/venvs/rl/bin/python
N=16; REPS=16
OUT=/home/younes/arma3-marl/table_maneuvers_v3.jsonl
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
sleep 15

for M in M1 M2 M3 M4 M5 M6 M7; do
  echo ""; echo "############ V3 MESURE $M ############"
  $PY run_maneuver.py --maneuver $M --servers $N --reps $REPS --out "$OUT" --max_steps 500
done

echo ""; echo "############ SYNTHÈSE TABLE V3 ############"
$PY - <<'PYEOF'
import json, collections
rows = collections.defaultdict(list)
for line in open("/home/younes/arma3-marl/table_maneuvers_v3.jsonl"):
    r = json.loads(line)
    if "mil" in r: rows[r["man"]].append(r)
NAMES = {"M1":"appui-assaut(réf)","M2":"double-env","M3":"env-simple","M4":"assaut-massé",
         "M5":"feinte","M6":"infiltration","M7":"échelonnée"}
PRED = {"M1":"50-70","M2":"45-60","M3":"25-45","M4":"20-40","M5":"35-55","M6":"35-55","M7":"15-35"}
print("%-4s %-18s %4s %7s %7s %7s %7s  %s" % ("man","nom","n","mil%","cplx%","QRF%","pertes","préd"))
for m in ["M1","M2","M3","M4","M5","M6","M7"]:
    rs = rows.get(m, [])
    if not rs: print("%-4s %-18s  (aucune donnée)" % (m, NAMES[m])); continue
    n=len(rs); mil=100*sum(x["mil"] for x in rs)/n; gp=100*sum(x["garr_pris"] for x in rs)/n
    qs=100*sum(x["qrf_spawn"] for x in rs)/n; pe=100*sum(x["pertes"] for x in rs)/n
    print("%-4s %-18s %4d %6.1f %6.1f %6.1f %6.0f   %s" % (m, NAMES[m], n, mil, gp, qs, pe, PRED[m]))
# --- la question pré-enregistrée : familles poolées ---
import math
A = [x for m in ("M1","M2","M5","M6") for x in rows.get(m, [])]
B = [x for m in ("M3","M4","M7") for x in rows.get(m, [])]
if A and B:
    pa = sum(x["mil"] for x in A)/len(A); pb = sum(x["mil"] for x in B)/len(B)
    se = math.sqrt(pa*(1-pa)/len(A) + pb*(1-pb)/len(B)); z = (pa-pb)/se if se else 0
    print("\nFAMILLE A (multi-axes, n=%d) : %.1f%%  |  FAMILLE B (fragmentée, n=%d) : %.1f%%" % (len(A),100*pa,len(B),100*pb))
    print("ÉCART %.1f pts (z=%.2f) -> seuils pré-enregistrés : ≥15=CONFIRMÉE · 5-15=AFFAIBLIE · <5/inversion=ARTEFACT" % (100*(pa-pb), z))
# vérif du fix : garnison prise => QRF affrontée ?
taken = [x for m in rows for x in rows[m] if x["garr_pris"]]
if taken:
    print("VÉRIF FIX : QRF affrontée dans %.0f%% des ops à garnison prise (attendu ~100)" % (100*sum(x["qrf_spawn"] for x in taken)/len(taken)))
PYEOF
echo "############ FIN TABLE V3 ############"
