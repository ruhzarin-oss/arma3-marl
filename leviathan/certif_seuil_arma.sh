#!/usr/bin/env bash
# certif_seuil_arma.sh — LE SEUIL DE MANOEUVRE TRANSFERE-T-IL SUR ARMA ?
# Attaquants FIXES a 12 (le plus petit effectif dans la bande, sonde du 28/07).
# Garnison variable : D = 8, 12, 16, 24 -> rapport D/A = 0.67, 1.00, 1.33, 2.00.
# Le sandbox place le seuil a D/A = 2. On regarde si Arma bascule au meme rapport.
# Criteres : CRITERES_CERTIF_SEUIL_ARMA_V2.md (8f6e129af26fecf8).
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
export HMT_THEATRE=altis
NAG="${NAG:-12}"
DS="${DS:-8 12 16 24}"
MODES="${MODES:-frontal envelop}"
REPS="${REPS:-3}"
STEPS="${STEPS:-60}"

echo "=== CERTIFICATION DU SEUIL : A=$NAG fixe, D=$DS, modes=$MODES, $REPS reps ==="
for rep in $(seq 1 "$REPS"); do
  for d in $DS; do
    for mode in $MODES; do
      out="certif_${NAG}v${d}_${mode}_${rep}.json"
      echo "--- A=$NAG D=$d $mode rep=$rep"
      timeout 180 python3 poser_fob.py "$d" 2>&1 | tail -1
      timeout 180 python3 envelop_arma.py setup --theatre altis --nag "$NAG" >/dev/null 2>&1
      timeout 420 python3 envelop_arma.py run --theatre altis --mode "$mode" --nag "$NAG" \
          --steps "$STEPS" --offset 45 --standoff 70 --flank 0.45 --assault_tick 24 \
          --out "$out" 2>&1 | tail -1
      timeout 150 python3 envelop_arma.py disarm --theatre altis >/dev/null 2>&1
    done
  done
done

echo ""
python3 - <<'PY'
import json, glob, re, collections
LEV = '/home/younes/arma3-marl/leviathan'
agg = collections.defaultdict(list)
for f in sorted(glob.glob(LEV + '/certif_*v*_*_*.json')):
    m = re.search(r'certif_(\d+)v(\d+)_(\w+)_(\d+)\.json', f)
    if not m: continue
    agg[(int(m.group(2)), m.group(3))].append(json.load(open(f))['metrics'])

def taux(o, cle):
    return sum(1 for x in o if x[cle]) / len(o)

Ds = sorted({d for d, _ in agg})
NAG = 12
print('=== RESULTATS : prise et cout par rapport de forces ===')
print('   D    D/A    prise frontal   prise envelop   prise fl/fr   pertes fr   pertes fl   cout fl/fr   bande ?')
lignes = {}
for d in Ds:
    fr = agg.get((d, 'frontal'), []); fl = agg.get((d, 'envelop'), [])
    if not fr or not fl: continue
    pfr, pfl = taux(fr, 'took'), taux(fl, 'took')
    lfr = sum(x['west_losses'] for x in fr) / len(fr)
    lfl = sum(x['west_losses'] for x in fl) / len(fl)
    rp = pfl / pfr if pfr > 0 else float('inf')
    # cout = pertes par PRISE reussie ; si aucune prise, non defini
    cfr = (sum(x['west_losses'] for x in fr if x['took']) / max(1, sum(1 for x in fr if x['took']))) if pfr > 0 else float('nan')
    cfl = (sum(x['west_losses'] for x in fl if x['took']) / max(1, sum(1 for x in fl if x['took']))) if pfl > 0 else float('nan')
    rc = cfl / cfr if cfr == cfr and cfr else float('nan')
    dans = 0.25 <= pfr <= 0.75
    lignes[d] = {'prise_frontal': pfr, 'prise_envelop': pfl, 'rapport_prise': rp,
                 'pertes_frontal': lfr, 'pertes_envelop': lfl, 'rapport_cout': rc,
                 'dans_bande': bool(dans), 'n_frontal': len(fr), 'n_envelop': len(fl)}
    print('  %3d   %4.2f       %5.0f%%          %5.0f%%        x%5.2f      %5.2f       %5.2f      x%5.2f     %s'
          % (d, d / NAG, 100*pfr, 100*pfl, rp, lfr, lfl, rc, 'OUI' if dans else 'non'))

print('')
print('=== LECTURE (criteres figes 8f6e129af26fecf8, non negociables) ===')
bande = [d for d in lignes if lignes[d]['dans_bande']]
if not bande:
    print('  >>> RIEN DANS LA BANDE : aucune cellule ne separe. On ne lit aucun ratio.')
else:
    print('  bande discriminante : D = %s (D/A = %s)' % (bande, [round(d/NAG,2) for d in bande]))
    bascule = [d for d in sorted(bande) if lignes[d]['rapport_prise'] >= 1.50]
    if bascule:
        d = bascule[0]
        print('  >>> BASCULE A D/A = %.2f (D=%d) : le flanc achete la PRISE.' % (d/NAG, d))
        if abs(d/NAG - 2.0) < 0.25:
            print('      LE SEUIL DU SANDBOX TRANSFERE EN RAPPORT (predit D/A=2).', flush=True)
            print('      L echelle absolue est fausse, le RAPPORT est juste.', flush=True)
        else:
            print('      Seuil DECALE : le sandbox predisait D/A=2, Arma dit %.2f.' % (d/NAG))
            print('      On consigne le rapport d Arma. On ne retouche pas le sandbox.')
    else:
        print('  >>> AUCUNE BASCULE dans la bande : le seuil est un artefact du sandbox.')
        print('      C est un resultat, pas un echec.')
json.dump(lignes, open(LEV + '/certif_seuil_arma.json', 'w'), indent=1, default=str)
print('')
print('-> %s/certif_seuil_arma.json' % LEV)
PY
echo "CERTIF_DONE"
