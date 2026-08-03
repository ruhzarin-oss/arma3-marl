#!/usr/bin/env bash
# frontiere_budget.sh — LA FRONTIERE PAR BUDGET, sans aucun entrainement.
# Jusqu ou peut-on serrer le budget de dose avant qu une solution CONNUE devienne impossible ?
# Le plus petit budget ou une doctrine reussit encore fixe B_min. En deca, on enseignerait
# l immobilite — c est la seule facon dont v5 peut echouer, et elle est bornee par cette
# mesure prealable, pas par une intuition. Criteres : CRITERES_V5_BUDGET.md 9274c81a3842a5e5
set -u
cd /home/younes/arma3-marl/leviathan || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
echo "=== FRONTIERE PAR BUDGET — 6 doctrines x 8 niveaux, 1024 episodes ==="
printf "  %-22s" "doctrine"
for b in 0.6 0.9 1.2 1.6 2.2 3.0 4.2 6.0; do printf "%8s" "B=$b"; done; echo
for d in frontal_delibere appui_mouvement debordement_simple debordement_double infiltration bonds_alternes; do
  printf "  %-22s" "$d"
  for b in 0.6 0.9 1.2 1.6 2.2 3.0 4.2 6.0; do
    $PY banc_mission.py --pilote "doctrine:$d" --episodes 1024 --graine 5 --pas 80         --budget $b --journal "journaux/front_${d}_b${b}.jsonl" >/dev/null 2>&1
    t=$($PY - <<PY2
import json
f=journaux/front__b.jsonl
r=[json.loads(l) for l in open(f)]
run=[x for x in r if x[type]==entete][-1][run]
e=[x for x in r if x[type]==episode and x.get(run)==run]
print(%.0f % (100.0*sum(1 for x in e if x[succes_monde])/max(len(e),1)))
PY2
)
    printf "%7s%%" "$t"
  done
  echo
done
echo "FRONTIERE_DONE"
