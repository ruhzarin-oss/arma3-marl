#!/usr/bin/env bash
# audit_boutons.sh — un PROCESSUS PAR BOUTON : un assert CUDA empoisonne tout le contexte,
# donc un bouton qui plante ne doit pas emporter les suivants.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
PY=/home/younes/env_isaaclab/bin/python3
export CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1
EP="${EP:-150}"

rm -f "$LEV"/audit_*.json
echo "=== AUDIT DES BOUTONS — un processus par bouton, $EP episodes, graine 7 ==="
echo ""
printf '  %-18s %-30s %-30s  verdict\n' bouton 'valeur basse' 'valeur haute'
printf '  %s\n' '--------------------------------------------------------------------------------------------'
for b in $($PY audit_boutons.py 2>/dev/null); do
  timeout 240 $PY audit_boutons.py --bouton "$b" --episodes "$EP" 2>/dev/null \
    || printf '  %-18s %-30s %-30s  PLANTE (assert CUDA)\n' "$b" '-' '-'
done

echo ""
$PY - <<'PY'
import json, glob, os
LEV='/home/younes/arma3-marl/leviathan'
tous=[json.load(open(f)) for f in sorted(glob.glob(LEV+'/audit_*.json')) if 'boutons' not in f]
act=[d['bouton'] for d in tous if d['verdict']=='actif']
ine=[d['bouton'] for d in tous if d['verdict']=='INERTE']
ref=[d['bouton'] for d in tous if d['verdict']=='REFUSE']
print('=== BILAN ===')
print('  actifs  : %2d  %s' % (len(act), act))
print('  INERTES : %2d  %s' % (len(ine), ine))
if ref: print('  refuses : %2d  %s' % (len(ref), ref))
n=len(act)+len(ine)
if n:
    print('')
    print('  >>> %d bouton(s) sur %d testes ne changent RIEN dans la configuration des bancs.' % (len(ine), n))
    print('      Tout resultat attribue a l un d eux est une lecture, pas une mesure.')
json.dump({d['bouton']: d for d in tous}, open(LEV+'/audit_boutons.json','w'), indent=1)
PY
echo "AUDIT_DONE"
