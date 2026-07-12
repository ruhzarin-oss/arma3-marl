#!/bin/bash
# Jeu de cartes OSM du benchmark (cf PROTOCOL.md). Reproductible.
#  - TRAIN / TEST : urbain, sol plat (elev=0).
#  - RUGGED : terrain vallonne, elev rempli depuis un MNT SRTM (--dem).
cd ~/arma3-marl || exit 1
PY=.venv/bin/python

gen () {   # $1=name $2=lat $3=lon  (sol plat)
  echo "=== $1 ($2, $3) ==="
  if $PY osm_to_replica.py --lat "$2" --lon "$3" --W 200 --name "$1" > "/tmp/gen_$1.log" 2>&1; then
    $PY -c "import numpy as np; d=np.load('replica_$1.npz'); s=d['solid']; h=d['solidh']; t=int(s.sum()); z=int((s&(h<=0)).sum()); print('    %.1f%% bati | %d solides | transparents %d | h med %.0f / max %.0f m'%(100*s.mean(),t,z,float(np.median(h[s])) if t else 0,float(h.max())))"
  else echo "    ECHEC (/tmp/gen_$1.log)"; tail -2 "/tmp/gen_$1.log"; fi
}
gend () {  # $1=name $2=lat $3=lon  (relief MNT)
  echo "=== $1 ($2, $3) [relief] ==="
  if $PY osm_to_replica.py --lat "$2" --lon "$3" --W 200 --name "$1" --dem > "/tmp/gen_$1.log" 2>&1; then
    $PY -c "import numpy as np; d=np.load('replica_$1.npz'); e=d['elev']; s=d['solid']; print('    relief %.0f m (std %.0f) | %.1f%% bati | transparents %d'%(float(e.max()),float(e.std()),100*s.mean(),int((s&(d['solidh']<=0)).sum())))"
  else echo "    ECHEC (/tmp/gen_$1.log)"; tail -2 "/tmp/gen_$1.log"; fi
}

echo "########## TRAIN (urbain plat) ##########"
gen denver  39.7475 -104.9950
gen chicago 41.8790  -87.6330
gen paris   48.8590    2.3470
gen madrid  40.4160   -3.7030
echo "########## TEST (urbain plat, disjoint) ##########"
gen newyork 40.7540  -73.9860
gen london  51.5150   -0.0880
gen lille   50.6310    3.0630
echo "########## TEST RELIEF (vallonne, --dem) ##########"
gend athens    37.9715 23.7257
gend delphi    38.4824 22.5010
gend santorini 36.4187 25.4310
echo "########## FINI ##########"
