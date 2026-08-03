#!/usr/bin/env bash
# sonder_regime_arma.sh — OU LE COMBAT SE RESOUT-IL SUR ARMA ?
# Garnison FIXE a 8. On fait varier le nombre d ATTAQUANTS. Mode frontal seulement :
# on cherche la bande ou la prise frontale tombe entre 25 % et 75 %, seule zone ou un
# A/B peut separer quoi que ce soit. Lecon de JALON 2 (14/06) : hors bande, les chiffres
# sont des combats figes.
# Criteres : CRITERES_CERTIF_SEUIL_ARMA.md (b764211cf2e274ca), section BANDE DISCRIMINANTE.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
NAGS="${NAGS:-4 8 12 18}"
REPS="${REPS:-2}"
STEPS="${STEPS:-60}"
D="${D:-8}"

echo "=== SONDE DE REGIME : garnison D=$D fixe, attaquants variables, mode frontal ==="
for rep in $(seq 1 "$REPS"); do
  for nag in $NAGS; do
    out="regime_${nag}v${D}_${rep}.json"
    echo "--- nag=$nag vs D=$D rep=$rep"
    timeout 150 python3 poser_fob.py "$D" 2>&1 | tail -1
    timeout 150 python3 envelop_arma.py setup --theatre altis --nag "$nag" >/dev/null 2>&1
    timeout 420 python3 envelop_arma.py run --theatre altis --mode frontal --nag "$nag" \
        --steps "$STEPS" --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
        --out "$out" 2>&1 | tail -2
    timeout 120 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
  done
done

echo ""
echo "=== BILAN : prise frontale par effectif ==="
python3 - <<'PY'
import json, glob, re, collections
agg = collections.defaultdict(list)
for f in sorted(glob.glob('/home/younes/arma3-marl/leviathan/regime_*v*_*.json')):
    m = re.search(r'regime_(\d+)v(\d+)_(\d+)\.json', f)
    if not m: continue
    d = json.load(open(f))['metrics']
    agg[int(m.group(1))].append(d)
print('  nag   ops   prise   pertes WEST   EAST neutralises   dans la bande 25-75 % ?')
for nag in sorted(agg):
    o = agg[nag]; n = len(o)
    prise = sum(1 for x in o if x['took']) / n
    pw = sum(x['west_losses'] for x in o) / n
    pe = sum(x['east_neutralized'] for x in o) / n
    dans = 0.25 <= prise <= 0.75
    print('  %3d   %3d   %5.0f%%      %5.2f            %5.2f            %s'
          % (nag, n, 100*prise, pw, pe, 'OUI' if dans else 'non'))
bande = [n for n in sorted(agg) if 0.25 <= sum(1 for x in agg[n] if x['took'])/len(agg[n]) <= 0.75]
print('')
print('  BANDE DISCRIMINANTE : nag = %s' % (bande if bande else 'AUCUN — le banc ne separe rien sur cette plage'))
PY
echo "SONDE_DONE"
