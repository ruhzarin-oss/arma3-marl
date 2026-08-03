#!/usr/bin/env bash
# v4.sh — JALON 3, LE CHANGEMENT UNIQUE EST LE MONDE.
# Criteres : CRITERES_JALON3.md (c1b8640ce73ee2dc). Recompense gelee, hyperparametres
# identiques a v3. Seule difference : monde_mission.py certifie (4 correctifs depuis v3).
# La seule courbe qui compte est celle du banc, invoquee tous les 100 pas d iteration.
# PORTE D ARRET ANTICIPE : a 100 iterations, PRENDRE au banc >= 15 % ou on arrete.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1

for etape in 100 200 300 400; do
  echo "########## ENTRAINEMENT JUSQU A $etape ITERATIONS ##########"
  reprise=""
  [ $etape -gt 100 ] && reprise="--reprise mission_v4.pt"
  $PY train_mission.py --iters 100 --envs 4096 --D 8 --seed 0 --out mission_v4.pt $reprise \
      2>&1 | grep -vE "Warning|warn" | tail -3
  echo "--- BANC CERTIFIE (le compteur interne n a pas voix au chapitre) ---"
  bash eval_checkpoint.sh mission_v4.pt 1000
  if [ $etape -eq 100 ]; then
    taux=$($PY - <<'PY'
import json, glob
eps = []
for f in glob.glob('/home/younes/arma3-marl/leviathan/journaux/ckpt_mission_v4_prendre_g1000.jsonl'):
    recs = [json.loads(l) for l in open(f)]
    ent = [r for r in recs if r['type']=='entete']
    if not ent: continue
    run = ent[-1]['run']
    eps = [r for r in recs if r['type']=='episode' and r.get('run')==run]
print('%.1f' % (100.0*sum(1 for e in eps if e['succes_monde'])/max(len(eps),1)))
PY
)
    echo ""
    echo "=== PORTE D ARRET ANTICIPE : PRENDRE = $taux % (seuil 15,0) ==="
    depasse=$($PY -c "print(1 if float('$taux') >= 15.0 else 0)")
    if [ "$depasse" != "1" ]; then
      echo "  >>> PORTE REFUSEE. On arrete ici : on ne brule pas 26 M de pas une deuxieme fois."
      echo "      L hypothese <<le monde casse empechait l apprentissage>> TOMBE."
      echo "      Levier suivant, changement unique de v5 : DENSITE DE RECOMPENSE,"
      echo "      faconnage a l evenement de prise, sous forme potentielle."
      echo "V4_ARRETE"
      exit 0
    fi
    echo "  >>> porte franchie, on va au bout."
  fi
done
echo "V4_DONE"
