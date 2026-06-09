#!/bin/bash
# Confirmation enveloppe M3 (manœuvre gagnante) aux extrêmes : normal (vs scripté 72%) + pro (plancher).
set -u
SB=/mnt/data/harmattan-sandbox; PY=/mnt/steam/harmattan/venvs/rl/bin/python; N=16
OUT=/home/younes/arma3-marl/m3_curve.jsonl; : > "$OUT"
cd /home/younes/arma3-marl
echo "[m3] $(date +%H:%M:%S) boot $N..."; bash "$SB/multi_server.sh" $N >/dev/null 2>&1
for w in $(seq 1 48); do r=0; for i in $(seq 0 $((N-1))); do grep -q "read from directory" "$SB/logs/server${i}.out" 2>/dev/null && r=$((r+1)); done; [ "$r" -ge "$N" ] && break; sleep 5; done; sleep 15
for EN in normal pro; do
  echo "[m3] $(date +%H:%M:%S) ### M3 vs $EN (n=16) ###"
  $PY run_maneuver.py --maneuver M3 --servers $N --reps 16 --out "$OUT" --max_steps 500 --enemy $EN || echo "[m3] ERR $EN"
done
pkill -9 -f arma3server_x64
echo "[m3] $(date +%H:%M:%S) === ENVELOPPE M3 ==="
$PY - <<'PY'
import json,collections
r=collections.defaultdict(list)
for l in open("/home/younes/arma3-marl/m3_curve.jsonl"):
 try:o=json.loads(l)
 except:continue
 if "mil" in o: r[o["enemy"]].append(o["mil"])
for en in ("normal","pro"):
 if r[en]: print("  M3 vs %-7s : %.1f%% (n=%d)"%(en,100*sum(r[en])/len(r[en]),len(r[en])))
print("  [rappel mesuré] skilled 62.5 | skilled_hunt 50 | skilled_qrf 25 | scripté@normal 72")
PY
echo "[m3] $(date +%H:%M:%S) FINI"
