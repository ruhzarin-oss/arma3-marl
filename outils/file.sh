#!/bin/bash
# Avale le plus ancien job de la file, un seul par appel. Lance par la tache HMT_RUN toutes les 10 min.
H=/mnt/data/hmt
[ -f $H/.temoin ] || exit 3
exec >> $H/etat/file.log 2>&1
mkdir -p $H/queue/en_cours $H/queue/faits
J=$(ls $H/queue/*.json 2>/dev/null | head -n 1)
[ -z "$J" ] && exit 0
[ -n "$(ls $H/queue/en_cours/*.json 2>/dev/null)" ] && { echo "$(date -Is) un job est deja en cours"; exit 0; }
mv "$J" $H/queue/en_cours/
E=$H/queue/en_cours/$(basename "$J")
echo "$(date -Is) PRISE $(basename "$J")"
bash $H/depot/outils/run.sh "$E"; RC=$?
if [ $RC = 2 ]; then
  mkdir -p $H/queue/refuses; mv "$E" $H/queue/refuses/
  echo "$(date -Is) REFUSE $(basename "$J") : le controle d'avant-run a dit non, job range dans queue/refuses"
else
  mv "$E" $H/queue/faits/
  echo "$(date -Is) FINI $(basename "$J") code=$RC"
fi
