#!/usr/bin/env bash
# test_fumee.sh — LA FUMEE FAIT-ELLE FRANCHIR LA LIGNE D ASSAUT FINAL ?
# Cellule A=12 vs D=12 : 0 prise sur 3 au run de certification, arret a 58-60 m puis 36-50 m
# a 150 pas. Une seule variable ajoutee : --smoke. Tout le reste identique.
# Seuil pre-enregistre : >=2 operations sur 3 RESOLUES (prise OU aneantissement) => la fumee
# est la cle du dernier bond. <2/3 => il faudra un ordre d assaut final explicite.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
for rep in 1 2 3; do
  echo "--- A=12 D=12 frontal FUMEE rep=$rep"
  timeout 180 python3 poser_fob.py 12 2>&1 | tail -1
  timeout 180 python3 envelop_arma.py setup --theatre altis --nag 12 >/dev/null 2>&1
  timeout 900 python3 envelop_arma.py run --theatre altis --mode frontal --nag 12 \
      --steps 150 --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
      --smoke --smoke_dist 45 --out fumee_${rep}.json 2>&1 | tail -1
  timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
done
echo ""
python3 - <<'PY'
import json, glob
res = [json.load(open(f))['metrics'] for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/fumee_*.json'))]
print(' rep  pris  west_fin  dist_min  east_neutralises  grenades')
for i, m in enumerate(res, 1):
    print('  %d   %5s   %2d/%2d      %3d m         %d/%d           %s'
          % (i, m['took'], m['west_end'], m['west_start'], m['min_fob_dist'],
             m['east_neutralized'], m['east_start'], m.get('smoke_grenades', 0)))
resolus = sum(1 for m in res if m['took'] or m['west_end'] == 0)
print('\n  resolus : %d/%d  (critere pre-enregistre : >=2/3)' % (resolus, len(res)))
print('  >>> ' + ('LA FUMEE FAIT FRANCHIR LE DERNIER BOND. Elle entre au protocole.'
                  if resolus >= 2 else
                  'LA FUMEE NE SUFFIT PAS. Il faut un ordre d assaut final explicite.'))
PY
echo "FUMEE_DONE"
