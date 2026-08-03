#!/bin/bash
# Le re-verdict de l'arc attend que la 3090 se libere. Lancer maintenant tuerait une case
# d'entrainement par manque de memoire — c'est deja arrive une fois ce soir.
cd /home/younes/arma3-marl
while pgrep -f 'lire_carte.py --bras' >/dev/null; do sleep 120; done
sleep 30
echo "=== 3090 liberee a $(date +%H:%M) ==="

echo '--- non-regression : sans latence, le monde doit etre INCHANGE ---'
./.venv/bin/python leviathan/reverdict_arc.py --eval 1024 --latences 4.1   --out reverdict_arc_ouvre.json
