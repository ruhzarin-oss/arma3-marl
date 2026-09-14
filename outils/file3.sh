#!/bin/bash
# MARQUEUR-GARDE-FIGE-FILE3
#
# file3.sh — SUCCESSEUR de file2.sh (nuit du 08 au 09/09/2026).
# Contenu strictement identique a file2.sh, PLUS la garde anti-modification-en-vol.
#
# ⛔ POURQUOI CE FICHIER EXISTE. Le 08/09, file2.sh a ete edite pendant que TROIS copies
# tournaient. bash lit un script par MORCEAUX : editer le fichier decale les offsets et la
# suite est lue de travers. Consequences mesurees, dans file.log :
#   - « /mnt/data/hmt/depot/outils/file2.sh: line 84: -z: command not found »
#   - deux invocations en vol ont relance des jobs DEJA TERMINES
#     (« mv: cannot stat ... No such file or directory » puis PRISE du meme job),
#     ce qui a bloque deux instances pendant des heures.
# run.sh porte deja ce remede depuis le 08/09 ; on le copie ici, tel quel.
#
# ⭐ LE REMEDE : on ne s execute jamais depuis le fichier du depot. Au lancement on prend une
# COPIE FIGEE dans /tmp et on s y transfere par exec. Une edition du depot pendant un passage
# ne touche plus le processus en vol ; elle ne prendra effet qu au passage suivant.
#
# ⚠️ file2.sh RESTE EN PLACE, INTACT, comme repli. Pour revenir en arriere :
#   powershell -NoProfile -Command "$a = New-ScheduledTaskAction -Execute 'wsl.exe' -Argument '-u younes -- bash /mnt/data/hmt/depot/outils/file2.sh'; Set-ScheduledTask -TaskName HMT_RUN -Action $a"
#
# ⚠️ La copie figee reste dans /tmp apres coup (comme celle de run.sh) : /tmp accumule un petit
# fichier par passage, soit ~144 par jour. A purger de temps en temps.
if [ "${HMT_FIGE:-0}" != "1" ]; then
  C=$(mktemp /tmp/file_fige.XXXX.sh); cp "$0" "$C"
  HMT_FIGE=1 exec bash "$C" "$@"
fi
# ----- a partir d ici : copie conforme de file2.sh -----
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

# ⚠️ Les verrous changent de nom (`j<N>` au lieu de `i<N>`) : un processus BLOQUE par l ancienne
# version tourne encore avec l ancien code en memoire, et son `trap` effacerait le verrou d un
# job NEUF portant le meme nom. On lit les DEUX noms pour l occupation, on n en cree qu un.
MIEN=""
libere() {
  # On ne rend que le verrou qu on a soi-meme pose : le pid inscrit doit etre le notre.
  [ -n "$MIEN" ] && [ "$(cat "$VERROUS/$MIEN/pid" 2>/dev/null)" = "$$" ] && rm -rf "$VERROUS/$MIEN"
}
trap libere EXIT

pris_par_un_verrou() {   # $1 = instance
  [ -d "$VERROUS/j$1" ] || [ -d "$VERROUS/i$1" ]
}

# Un verrou dont le processus est mort ne protege plus rien, il bloque. On le retire — mais on
# le DIT, parce qu un verrou mort veut dire qu un run est parti sans rendre la main.
for V in "$VERROUS"/i* "$VERROUS"/j*; do
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
MAX=10  # 10 depuis le 14/09 : Younes autorise dix serveurs. Instances 1-8, 10, 11 ; 0 est au Gymnase, 9 est le labo.
        # 5 depuis le 11/09 : Younes, la puissance est la (Xeon 12 coeurs, 64 Go). La charge reste archivee par run.
        # 3 depuis le 08/09 : gymnase (i0) + les deux bancs CHACAL (i1, i3).
        # ! Non mesure au-dela de 2 instances : la charge concurrente est archivee
        # dans chaque run (charge_au_lancement), donc un effet de contention serait visible.
VIVANTS=$(ls -1d "$VERROUS"/i* "$VERROUS"/j* 2>/dev/null | wc -l)
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
  elif pris_par_un_verrou "$I"; then
    echo "$(date -Is) ATTEND $(basename "$J") : verrou de l instance $I deja tenu"
  elif mkdir "$VERROUS/j$I" 2>/dev/null; then
    echo $$ > "$VERROUS/j$I/pid"; MIEN="j$I"; CHOISI="$J"; break
  else
    echo "$(date -Is) ATTEND $(basename "$J") : verrou j$I pris par un appel simultane"
  fi
done
[ -z "$CHOISI" ] && exit 0

mv "$CHOISI" $H/queue/en_cours/
E=$H/queue/en_cours/$(basename "$CHOISI")
echo "$(date -Is) PRISE $(basename "$CHOISI") sur l instance $(inst_de "$E") (verrou $MIEN, pid $$)"
# ⛔ 08/09 : un job REFUSE ne creait aucun run, donc aucun FIN.json, donc le pont ne rendait
# jamais rien : la tache restait « En cours » dans Plane pour toujours. On garde donc la RAISON
# du refus a cote du job.
#
# ⛔⛔ ET LA PREMIERE VERSION DE CETTE CAPTURE A BLOQUE UNE INSTANCE TROIS HEURES.
# Elle passait par `| tee` : un TUYAU ne se ferme que quand TOUS ses ecrivains ont ferme, or
# le serveur Arma lance par le petit-fils herite du descripteur. run.sh avait fini depuis 3 h,
# `tee` attendait encore, le verrou i0 tenait, et le gymnase etait a l arret.
# ⭐ On ne met JAMAIS un tuyau en travers d un lanceur qui detache des processus.
# Redirection vers un FICHIER : rien a attendre, et le code de sortie est direct.
TRACE=$(mktemp /tmp/run_sortie.XXXX)
# ⛔ 11/09 : `HMT_FIGE=1` (pose par le gel de CE script) etait HERITE par run.sh, qui se croyait gele et
# lisait le fichier du depot en direct. run.sh edite a 09:43 pendant V1 : a 14:52 il a relu le fichier decale
# (« line 39: RUN: command not found ») et rejoue ses 5 repetitions dans le meme dossier. On retire la
# variable : chaque script se gele lui-meme.
env -u HMT_FIGE bash $H/depot/outils/run.sh "$E" > "$TRACE" 2>&1; RC=$?
cat "$TRACE"
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
# ⭐ 11/09 : la base de connaissance suit chaque run. Jamais bloquant : un catalogue en echec ne
# retient ni la file ni le job, il le dit dans file.log.
timeout 600 python3 $H/depot/outils/catalogue.py >> $H/etat/catalogue.log 2>&1 || echo "$(date -Is) catalogue en echec (voir etat/catalogue.log)"
