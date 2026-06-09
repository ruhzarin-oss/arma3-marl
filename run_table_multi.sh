#!/bin/bash
# ÉTAPE 2 — TABLE MULTI-SITUATIONS (la PORTE) : M1-M7 × n=16 sur skilled_hunt + skilled_qrf.
# Combinée à skilled (étape 1), on regarde si le GAGNANT change selon la défense.
set -u
SB=/mnt/data/harmattan-sandbox
PY=/mnt/steam/harmattan/venvs/rl/bin/python
N=16
OUT=/home/younes/arma3-marl/table_multi.jsonl
: > "$OUT"
cd /home/younes/arma3-marl

echo "[t2] $(date +%H:%M:%S) boot $N serveurs..."
bash "$SB/multi_server.sh" $N >/dev/null 2>&1
for w in $(seq 1 48); do
  ready=0; for i in $(seq 0 $((N-1))); do grep -q "read from directory" "$SB/logs/server${i}.out" 2>/dev/null && ready=$((ready+1)); done
  [ "$ready" -ge "$N" ] && { echo "[t2] $N/$N missions chargées"; break; }
  sleep 5
done
sleep 15

for EN in skilled_hunt skilled_qrf; do
  for M in M1 M2 M3 M4 M5 M6 M7; do
    echo "[t2] $(date +%H:%M:%S) ### $M vs $EN (n=16) ###"
    $PY run_maneuver.py --maneuver $M --servers $N --reps 16 --out "$OUT" --max_steps 500 --enemy $EN || echo "[t2] ERREUR $M/$EN (continue)"
  done
done

pkill -9 -f arma3server_x64
echo "[t2] $(date +%H:%M:%S) === SYNTHÈSE MULTI-SITUATIONS + VERDICT PORTE ==="
$PY - <<'PYEOF'
import json, collections
NAMES={"M1":"appui-assaut","M2":"double-env","M3":"env-simple","M4":"massé","M5":"feinte","M6":"infiltration","M7":"échelonnée"}
def load(path):
    r=collections.defaultdict(lambda: collections.defaultdict(list))
    for line in open(path):
        try: o=json.loads(line)
        except: continue
        if "mil" in o: r[o["enemy"]][o["man"]].append(o["mil"])
    return r
data=collections.defaultdict(dict)
for path in ("/home/younes/arma3-marl/table_skilled.jsonl","/home/younes/arma3-marl/table_multi.jsonl"):
    try:
        for en,mans in load(path).items():
            for m,v in mans.items(): data[en][m]=100*sum(v)/len(v)
    except FileNotFoundError: pass
order=["M1","M2","M3","M4","M5","M6","M7"]
defs=[d for d in ("skilled","skilled_hunt","skilled_qrf") if d in data]
print("manœuvre        " + "".join("%-13s"%d for d in defs))
for m in order:
    print("%-3s %-12s "%(m,NAMES[m]) + "".join("%5.1f        "%data[d].get(m,float('nan')) for d in defs))
print("\n--- GAGNANT par défense ---")
winners={}
for d in defs:
    best=max(data[d], key=lambda m: data[d][m]); winners[d]=best
    print("  %-13s -> %s (%s, %.1f%%)"%(d,best,NAMES[best],data[d][best]))
uniq=set(winners.values())
print("\n=== VERDICT PORTE ===")
if len(uniq)>1:
    print("  Le GAGNANT CHANGE selon la défense (%s) -> SIGNAL DE SÉLECTION -> étape 3 (officier) JUSTIFIÉE."%", ".join("%s:%s"%(d,winners[d]) for d in defs))
else:
    w=list(uniq)[0]
    print("  MÊME gagnant partout (%s) -> pas de problème de sélection -> déployer %s FIXE (le comparer au scripté 72%%)."%(w,w))
PYEOF
echo "[t2] $(date +%H:%M:%S) FINI"
