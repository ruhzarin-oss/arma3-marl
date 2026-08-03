#!/usr/bin/env bash
# etalon_j1.sh — PORTE E4 : l etalon, 6 doctrines x 2 verbes forces, graine 3.
# Criteres : CRITERES_JALON1.md. 1024 episodes par cellule, mode episode, permute 0.
# Le forcage du verbe apparie les deux passes : memes missions, seule la contrainte change.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
GRAINE="${GRAINE:-3}"; EPISODES="${EPISODES:-1024}"

echo "=== ETALON J1 — graine $GRAINE, $EPISODES episodes par cellule, 12 passes ==="
for d in frontal_delibere appui_mouvement debordement_simple debordement_double infiltration bonds_alternes; do
  for v in prendre infiltrer; do
    # INTERDIT N 7 : on n efface jamais un journal. Il est en ajout seul et
    # l analyse ne lit que le dernier run, identifie par son uuid.
    timeout 900 $PY banc_mission.py --pilote "doctrine:$d" --verbe "$v" \
        --episodes "$EPISODES" --graine "$GRAINE" --D 8 --pas 80 --mode episode --permute 0 \
        2>&1 | grep -vE "Warning|warn" | grep -E "succes|BANC_DONE" | head -1
  done
done
echo ""
echo "=== ANALYSE (recalcul du predicat + appariement + ecart a la table) ==="
$PY analyse_journal.py "journaux/j1_*_p0_g${GRAINE}.jsonl" --apparier
echo ""
$PY - <<'PY'
import json, glob, collections, sys
PUB = {'frontal_delibere':(44.0,7.6),'appui_mouvement':(49.8,14.5),
       'debordement_simple':(54.3,32.2),'debordement_double':(54.3,31.7),
       'infiltration':(53.0,18.1),'bonds_alternes':(24.8,9.6)}
import os
g = os.environ.get('GRAINE','3')
hors = []; total = 0
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/journaux/j1_*_p0_g%s.jsonl' % g)):
    eps = [json.loads(l) for l in open(f)]
    ent = [e for e in eps if e['type']=='entete'][-1]
    ep  = [e for e in eps if e['type']=='episode']
    nom = ent['pilote'].split(':')[1]
    if nom not in PUB: continue
    par = collections.defaultdict(list)
    for e in ep: par[e['verbe_nom']].append(e)
    for v, lot in par.items():
        total += 1
        t = 100.0*sum(1 for e in lot if e['succes_monde'])/len(lot)
        att = PUB[nom][0 if v=='prendre' else 1]
        if abs(t-att) > 3.0: hors.append((nom, v, t, att, t-att))
print('=== VERDICT E4 (critere : 12 cellules sur 12 dans +/- 3,0 points) ===')
print('  cellules mesurees : %d | hors tolerance : %d' % (total, len(hors)))
for n,v,t,a,e in hors:
    print('    %-22s %-10s mesure %5.1f  publie %5.1f  ecart %+5.1f' % (n,v,t,a,e))
if total == 12 and not hors:
    print('  >>> A PRIORI CONFIRME. Instrument etalonne. Passage a E5.')
elif hors:
    print('  >>> LA MESURE REPRODUCTIBLE GAGNE. On ne bricole pas l instrument pour retomber')
    print('      sur la table. Bissection autorisee (3 parametres), puis AMENDEMENT 4 soumis')
    print('      a Younes. Il tranche, pas moi.')
else:
    print('  >>> COMPTE DE CELLULES INATTENDU : %d au lieu de 12. On ne conclut pas.' % total)
PY
echo "ETALON_J1_DONE"
