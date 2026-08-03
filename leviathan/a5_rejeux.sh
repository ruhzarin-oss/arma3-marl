#!/usr/bin/env bash
# a5_rejeux.sh — CUISSON des rejeux. On les cuit, on ne les juge pas :
# le jugement a l'oeil est le travail de Younes.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd "$LEV" || exit 2
echo "=== CUISSON DES REJEUX ==="

# --- 1. le meilleur flanc Arma : l'episode envelop qui a PRIS au moindre cout
MEILLEUR=$(python3 - <<'PY'
import glob, json, os
best = None
for f in glob.glob('/home/younes/arma3-marl/leviathan/ecl_*_envelop_*.json') + \
         glob.glob('/home/younes/arma3-marl/leviathan/ratio_*_envelop_*.json'):
    try:
        m = json.load(open(f))['metrics']
    except Exception:
        continue
    # priorite : avoir PRIS ; puis peu de pertes ; puis avoir penetre loin
    cle = (0 if m.get('took') else 1, m.get('west_losses', 99), m.get('min_fob_dist', 999))
    if best is None or cle < best[0]:
        best = (cle, f)
print(best[1] if best else '')
PY
)
if [ -n "$MEILLEUR" ]; then
  echo "  rejeu 1 — meilleur flanc Arma : $(basename "$MEILLEUR")"
  python3 replay_player.py "$MEILLEUR" --out rejeu1_flanc_arma.html >/dev/null 2>&1 \
    && echo "     -> leviathan/rejeu1_flanc_arma.html" \
    || echo "     !! lecteur en echec"
else
  echo "  rejeu 1 — AUCUN episode de flanc disponible"
fi

# --- 2. un episode de suppression, SI la courbe n2 a abouti
if [ -s courbe_suppression_12.json ] || [ -s courbe_suppression_04.json ]; then
  echo "  rejeu 2 — la courbe n2 a produit des chiffres, mais elle n'ecrit PAS de trames"
  echo "     (mesurer_suppression.py compte des balles, il ne journalise pas les positions)"
  echo "     -> rejeu non cuisinable en l'etat. Dit tel quel, sans maquillage."
else
  echo "  rejeu 2 — la courbe n2 n'a rien produit : rien a cuire."
fi

# --- 3. l'agent au champ qui se faufile (sandbox) : cuit par le rejeu GPU, plus tard
echo "  rejeu 3 — agent sandbox : cuit en fin de chaine 3090 (il attend un .pt entraine)"
echo "A5_DONE"
