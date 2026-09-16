#!/bin/bash
# Par campagne : jobs finis sur 32, jobs refuses, episodes acceptes et refuses.
L=/mnt/data/hmt/etat/file.log
for c in P2 P1 P4 P3 P6; do
  F=$(grep -c "FINI 2026-09-17_CHOIX_[0-9]*_$c" $L); R=$(grep -c "REFUSE 2026-09-17_CHOIX_[0-9]*_$c" $L)
  A=0; X=0
  for d in $(grep -l "\"campagne\": *\"CHOIX-$c-17-09\"" /mnt/data/hmt/runs/2026-09-17_*/job.json 2>/dev/null | xargs -r -n1 dirname); do
    A=$((A + $(grep -l '"verdict": "ACCEPTE"' $d/g*/resultat.json 2>/dev/null | wc -l))); X=$((X + $(grep -l '"verdict": "REFUSE"' $d/g*/resultat.json 2>/dev/null | wc -l)))
  done
  printf "%s:%s/32,r%s,a%s,x%s " $c $F $R $A $X
done
echo
