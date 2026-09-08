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
# ⛔ MESURE DU 08/09 — LA SELECTION PAR INSTANCE NE SUFFISAIT PAS. La tache HMT_RUN etait en
# `MultipleInstances = IgnoreNew` : tant qu un job tournait, tout declenchement suivant etait
# IGNORE et ce script n etait meme jamais appele. La file par instance etait du code mort.
# Il a fallu passer la tache en `Parallel` — et alors deux appels simultanes peuvent choisir
# le meme job, ou deux jobs de la meme instance. D ou le VERROU ATOMIQUE ci-dessous : `mkdir`
# reussit chez un seul processus. Le verrou par en_cours, lui, se lit APRES coup et ne protege
# de rien contre une course.
#
# ⚠️ CE QUI NE CHANGE PAS : une instance ne prend jamais deux jobs. Le verrou existe toujours,
# il est seulement POSE AU BON ENDROIT. Et un job depose a la racine de queue/ (l ancien mode)
# continue de marcher exactement comme avant.
set -uo pipefail
H=/mnt/data/hmt
[ -f $H/.temoin ] || exit 3
exec >> $H/etat/file.log 2>&1
mkdir -p $H/queue/en_cours $H/queue/faits $H/queue/refuses $H/queue/verrous
VERROUS=$H/queue/verrous

inst_de() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('instance','?'))" "$1" 2>/dev/null; }

MIEN=""
libere() { [ -n "$MIEN" ] && rm -rf "$VERROUS/$MIEN"; }
trap libere EXIT

# Un verrou dont le processus est mort ne protege plus rien, il bloque. On le retire — mais on
# le DIT, parce qu un verrou mort veut dire qu un run est parti sans rendre la main.
for V in "$VERROUS"/i*; do
  [ -d "$V" ] || continue
  P=$(cat "$V/pid" 2>/dev/null || true)
  if [ -z "$P" ] || ! kill -0 "$P" 2>/dev/null; then
    echo "$(date -Is) VERROU MORT $(basename "$V") (pid ${P:-vide} absent) — retire"
    rm -rf "$V"
  fi
done

# ⚠️ PLAFOND. La parallelisation Arma a ete MESUREE : x1,86 a DEUX instances, et rien au-dessus
# de 13 % ensuite. On ne depasse pas ce qui a ete mesure — au-dela, on ajouterait du bruit de
# charge dans des mesures censees etre comparables.
MAX=2
VIVANTS=$(ls -1d "$VERROUS"/i* 2>/dev/null | wc -l)
if [ "$VIVANTS" -ge "$MAX" ]; then
  echo "$(date -Is) PLAFOND $VIVANTS/$MAX jobs en vol — rien pris"; exit 0
fi

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
  elif mkdir "$VERROUS/i$I" 2>/dev/null; then
    echo $$ > "$VERROUS/i$I/pid"; MIEN="i$I"; CHOISI="$J"; break
  else
    echo "$(date -Is) ATTEND $(basename "$J") : verrou i$I tenu par un autre appel"
  fi
done
[ -z "$CHOISI" ] && exit 0

mv "$CHOISI" $H/queue/en_cours/
E=$H/queue/en_cours/$(basename "$CHOISI")
echo "$(date -Is) PRISE $(basename "$CHOISI") sur l instance $(inst_de "$E") (verrou $MIEN, pid $$)"
# ⛔ 08/09 : un job REFUSE ne creait aucun run, donc aucun FIN.json, donc le pont ne rendait
# jamais rien : la tache restait « En cours » dans Plane pour toujours, sans que personne ne le
# sache. On garde donc la RAISON du refus a cote du job. Sortie captee par `tee` et non relue
# dans file.log : avec deux jobs en vol, on attraperait la raison du voisin.
TRACE=$(mktemp /tmp/run_sortie.XXXX)
bash $H/depot/outils/run.sh "$E" 2>&1 | tee -a "$TRACE"; RC=${PIPESTATUS[0]}
if [ $RC = 2 ]; then
  mv "$E" $H/queue/refuses/
  grep -m1 "^REFUS:" "$TRACE" > $H/queue/refuses/$(basename "$CHOISI").raison 2>/dev/null \
    || echo "REFUS: sans raison lisible" > $H/queue/refuses/$(basename "$CHOISI").raison
  rm -f "$TRACE"
  echo "$(date -Is) REFUSE $(basename "$CHOISI") : $(cat $H/queue/refuses/$(basename "$CHOISI").raison)"
else
  rm -f "$TRACE"
  mv "$E" $H/queue/faits/
  echo "$(date -Is) FINI $(basename "$CHOISI") code=$RC"
fi
