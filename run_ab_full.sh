#!/bin/bash
# ORCHESTRATION DE NUIT — A/B propre brouillard vs omniscient, jusqu'au verdict de transfert Arma.
# 1) attend la fin de la ligue BROUILLARD (league_fog, déjà lancée)
# 2) lance l'omniscient APPARIÉ (league_omni, mêmes réglages, sight=1e9)
# 3) boot 16 serveurs Arma
# 4) éval les DEUX bras (camp0) contre la même réf fixe (league_learner.pt) sous brouillard Arma
# 5) coupe les serveurs, écrit ab_verdict.txt
set -u
SB=/mnt/data/harmattan-sandbox
PY=/mnt/steam/harmattan/venvs/rl/bin/python
cd /home/younes/arma3-marl

echo "[full] $(date +%H:%M:%S) attente fin ligue BROUILLARD (league_fog)..."
while pgrep -f "train_league_gpu.py.*--save league_fog" >/dev/null 2>&1; do sleep 30; done
echo "[full] $(date +%H:%M:%S) brouillard terminé."

echo "[full] $(date +%H:%M:%S) lancement OMNISCIENT apparié (league_omni, sight=1e9)..."
$PY train_league_gpu.py --iters 300 --envs 98304 --sight 1e9 --save league_omni
echo "[full] $(date +%H:%M:%S) omniscient terminé."

echo "[full] $(date +%H:%M:%S) boot 16 serveurs pour l'éval..."
bash "$SB/multi_server.sh" 16 >/dev/null 2>&1
for w in $(seq 1 48); do
  ready=0
  for i in $(seq 0 15); do grep -q "read from directory" "$SB/logs/server${i}.out" 2>/dev/null && ready=$((ready+1)); done
  [ "$ready" -ge 16 ] && { echo "[full] 16/16 missions chargées"; break; }
  sleep 5
done
sleep 15

echo "[full] $(date +%H:%M:%S) ÉVAL BROUILLARD..."
$PY eval_koth_arma.py --brain league_fog_learner.pt  --ref league_learner.pt --servers 16 --steps 300 --out ab_eval_fog.json  --label FOG
echo "[full] $(date +%H:%M:%S) ÉVAL OMNISCIENT..."
$PY eval_koth_arma.py --brain league_omni_learner.pt --ref league_learner.pt --servers 16 --steps 300 --out ab_eval_omni.json --label OMNI

echo "[full] $(date +%H:%M:%S) coupe les serveurs."
pkill -9 -f arma3server_x64

echo "[full] $(date +%H:%M:%S) === VERDICT A/B ==="
$PY - <<'PYEOF'
import json
def g(f):
    try: return json.load(open(f))
    except Exception as e: return {"err": str(e)}
fog = g("ab_eval_fog.json"); omni = g("ab_eval_omni.json")
L = []
L.append("VERDICT A/B — transfert Arma KOTH (cerveau=camp0 vs ref fixe league_learner, sous brouillard)")
wf = fog.get("winrate_camp0"); wo = omni.get("winrate_camp0")
L.append("  BROUILLARD : winrate=%s  (parties décidées=%s, captures=%s)" % (wf, fog.get("n_decided"), fog.get("captures")))
L.append("  OMNISCIENT : winrate=%s  (parties décidées=%s, captures=%s)" % (wo, omni.get("n_decided"), omni.get("captures")))
if isinstance(wf, (int, float)) and isinstance(wo, (int, float)):
    d = wf - wo
    L.append("  ÉCART (fog - omni) = %+.3f" % d)
    if d > 0.05:
        L.append("  -> HYPOTHÈSE CONFIRMÉE : entraîner SOUS BROUILLARD transfère mieux au réel. Étape 2 (mémoire GRU) justifiée pour aller plus loin.")
    elif d < -0.05:
        L.append("  -> RÉFUTÉE : l'omniscient transfère mieux. Surprise -> creuser (le brouillard mémoryless dégrade peut-être trop).")
    else:
        L.append("  -> NON CONCLUANT (|écart|<0.05) : effet faible. La MÉMOIRE (étape 2) est probablement le vrai verrou, pas la seule vision.")
else:
    L.append("  -> ÉVAL INCOMPLÈTE (voir ab_eval_*.json / logs). " + str(fog.get("err", "")) + " " + str(omni.get("err", "")))
open("ab_verdict.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
PYEOF
echo "[full] $(date +%H:%M:%S) FINI -- verdict dans ab_verdict.txt"
