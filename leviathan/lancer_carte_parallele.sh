#!/usr/bin/env bash
# Les SIX cases en parallele sur la 3090, au lieu de six en file.
#
# Mesure : une case = ~50 min, et la carte reste a 30 % d'usage avec 2,9 Go pris sur 24.
# Le goulot n'est pas le GPU mais Python qui lance de petits noyaux — six processus
# comblent les trous les uns des autres. 5 heures deviennent une heure.
#
# Rien d'autre ne change : memes graines, meme carte, memes criteres figes
# (CRITERES_CARTE_TYPEE.md, empreinte c9ed30b25c7a8573). Seule l'ordonnance change.
set -u
LEV=/home/younes/arma3-marl/leviathan
cd /home/younes/arma3-marl || exit 2

echo "[1/3] arret du run sequentiel en cours"
pkill -f 'lire_carte.py --graines' 2>/dev/null
sleep 3

echo "[2/3] contre-epreuve, UNE seule fois (elle ne depend pas du bras)"
./.venv/bin/python leviathan/lire_carte.py --bras dense --graine -1 --graines 0 \
  --out carte_repere.json > /tmp/carte_repere.log 2>&1
grep -E 'repere scripte|CONTRE-EPREUVE' /tmp/carte_repere.log | sed 's/^/  /'

echo "[3/3] lancement des six cases"
for BRAS in dense conv; do
  for G in 7 8 9; do
    nohup ./.venv/bin/python leviathan/lire_carte.py \
      --bras "$BRAS" --graine "$G" --sans_repere \
      --rounds 150 --K 8 --ne 1024 --eval 300 \
      --out "carte_${BRAS}_g${G}.json" \
      > "/tmp/carte_${BRAS}_g${G}.log" 2>&1 &
    sleep 4
  done
done
sleep 20
echo "  processus actifs : $(pgrep -fc 'lire_carte.py --bras')"
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader | tail -1 | sed 's/^/  3090 : /'
