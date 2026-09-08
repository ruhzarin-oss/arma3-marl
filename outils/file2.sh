#!/bin/bash
# Avale le plus ancien job de la file, UN PAR INSTANCE. Lance par HMT_RUN toutes les 10 min.
#
# ⭐ 08/09 — LA FILE DEVIENT PAR INSTANCE. Avant, un seul job tournait, TOUS PROJETS CONFONDUS :
# un episode CHACAL de 3 h par graine bloquait le gymnase pendant des heures pour des travaux
# qui ne se concernent pas. Or les deux n ont meme pas besoin de la meme machine : chacal tient
# l instance 3 (profil hmtech3, port 2432), les bancs de certification l instance 0 (hmtech0,
# port 2402). Profils, ports et missions distincts. Ce qui les serialisait etait un choix du
# lanceur, pas une contrainte physique.
#
# ⚠️ CE QUI NE CHANGE PAS : une instance ne prend jamais deux jobs. Le verrou existe toujours,
# il est seulement POSE AU BON ENDROIT. Et un job depose a la racine de queue/ (l ancien mode)
# continue de marcher : il est traite comme avant, avec un verrou global.
set -uo pipefail
H=/mnt/data/hmt
[ -f $H/.temoin ] || exit 3
exec >> $H/etat/file.log 2>&1
mkdir -p $H/queue/en_cours $H/queue/faits $H/queue/refuses

inst_de() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('instance','?'))" "$1" 2>/dev/null; }

# Un job par instance : on prend le plus ancien dont l INSTANCE est libre.
CHOISI=""
for J in $(ls -tr $H/queue/*.json 2>/dev/null); do
  I=$(inst_de "$J")
  [ "$I" = "?" ] && { echo "$(date -Is) IGNORE $(basename "$J") : pas de champ instance"; continue; }
  OCC=0
  for E in $(ls $H/queue/en_cours/*.json 2>/dev/null); do
    [ "$(inst_de "$E")" = "$I" ] && OCC=1
  done
  if [ "$OCC" = "1" ]; then
    echo "$(date -Is) ATTEND $(basename "$J") : l instance $I est occupee"
  else
    CHOISI="$J"; break
  fi
done
[ -z "$CHOISI" ] && exit 0

mv "$CHOISI" $H/queue/en_cours/
E=$H/queue/en_cours/$(basename "$CHOISI")
echo "$(date -Is) PRISE $(basename "$CHOISI") sur l instance $(inst_de "$E")"
bash $H/depot/outils/run.sh "$E"; RC=$?
if [ $RC = 2 ]; then
  mv "$E" $H/queue/refuses/
  echo "$(date -Is) REFUSE $(basename "$CHOISI") : le controle d'avant-run a dit non, job range dans queue/refuses"
else
  mv "$E" $H/queue/faits/
  echo "$(date -Is) FINI $(basename "$CHOISI") code=$RC"
fi
