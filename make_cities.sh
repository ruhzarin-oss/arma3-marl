#!/bin/bash
# Jeu de cartes OSM du benchmark (train + test DISJOINTS), cf PROTOCOL.md.
# Reproductible : relancer regenere exactement le meme jeu.
cd ~/arma3-marl || exit 1
PY=.venv/bin/python

gen () {   # $1=name $2=lat $3=lon
  echo "=== $1 ($2, $3) ==="
  if $PY osm_to_replica.py --lat "$2" --lon "$3" --W 200 --name "$1" > "/tmp/gen_$1.log" 2>&1; then
    $PY -c "import numpy as np; d=np.load('replica_$1.npz'); s=d['solid']; h=d['solidh']; t=int(s.sum()); z=int((s&(h<=0)).sum()); print('    %.1f%% bati | %d cases solides | transparents %d | hauteur med %.0f / max %.0f m'%(100*s.mean(),t,z,float(np.median(h[s])) if t else 0,float(h.max())))"
  else
    echo "    ECHEC (voir /tmp/gen_$1.log)"; tail -2 "/tmp/gen_$1.log"
  fi
}

echo "########## TRAIN ##########"
gen denver  39.7475 -104.9950
gen chicago 41.8790  -87.6330
gen paris   48.8590    2.3470
gen madrid  40.4160   -3.7030
echo "########## TEST (disjoint) ##########"
gen newyork 40.7540  -73.9860
gen london  51.5150   -0.0880
gen lille   50.6310    3.0630
echo "########## FINI ##########"
