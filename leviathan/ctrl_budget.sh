#!/usr/bin/env bash
# ctrl_budget.sh — ETAPE 2 DE L ARCHITECTE : le controle a un seul changement.
# v5 gele, PAS de couche reactive, et le budget POUSSE A L INFINI donc jamais contraignant.
# Porte : arrivee >= 20 % => la machinerie v5 est saine et le budget est le coupable.
# Arrivee < 5 % => v5 a casse autre chose, et on bissecte le diff v4 -> v5 avant toute depense.
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
B="${B:-1000000}"; G="${G:-0}"
mkdir -p ckpt
for etape in 100 200 300 400; do
  reprise=""; iter0=$((etape-100))
  [ $iter0 -gt 0 ] && reprise="--reprise ckpt/ctrl_B${B}_g${G}_${iter0}.pt"
  $PY train_mission.py --iters 100 --envs 4096 --D 8 --seed $G --budget --Bfixe $B \
      --iters_total 400 --iter0 $iter0 --out ckpt/ctrl_B${B}_g${G}_${etape}.pt $reprise \
      2>&1 | grep -vE "Warning|warn" | tail -1
  $PY banc_mission.py --pilote "reseau:ckpt/ctrl_B${B}_g${G}_${etape}.pt" --episodes 2048 \
      --graine 1000 --pas 80 --budget $B \
      --journal "journaux/ctrl_B${B}_g${G}_${etape}.jsonl" >/dev/null 2>&1
  $PY - <<'PY2'
import json, glob, os
f = sorted(glob.glob('/home/younes/arma3-marl/leviathan/journaux/ctrl_B*_g*_*.jsonl'),
           key=os.path.getmtime)[-1]
r = [json.loads(l) for l in open(f)]
run = [x for x in r if x['type'] == 'entete'][-1]['run']
e = [x for x in r if x['type'] == 'episode' and x.get('run') == run]
a = 100.0 * sum(1 for x in e if x.get('arrive')) / max(len(e), 1)
s = 100.0 * sum(1 for x in e if x['succes_monde']) / max(len(e), 1)
print('  %-34s ARRIVEE %5.1f%%   succes %5.1f%%' % (os.path.basename(f)[:-6], a, s))
PY2
done
echo "CTRL_BUDGET_DONE"
