#!/bin/bash
# Toutes les portes du moteur, dans l ordre, avec un bilan d une ligne chacune ( 26/09 ). A passer apres toute
# modification et apres le passage a Ubuntu. Code de sortie : le nombre de portes refusees.
#   bash portes.sh [ --vite ]      ( --vite : sans les portes du pays, ~20 min de moins )
DEPOT=$(cd "$(dirname "$0")" && pwd); cd $DEPOT; export PYTHONPATH=$DEPOT
PY=${PY:-python3}; REF=${HMT_REF:-/mnt/data/hmt}; export HMT_REF=$REF
refus=0
porte() {   # nom, motif de reussite, commande...
  local nom=$1 motif=$2; shift 2
  local t0=$(date +%s) sortie; sortie=$("$@" 2>&1 | tail -30)
  if echo "$sortie" | grep -qE "$motif"; then echo "PASSE   $nom ( $(( $(date +%s) - t0 )) s )"
  else echo "ECHOUE  $nom ( $(( $(date +%s) - t0 )) s )"; echo "$sortie" | tail -8 | sed 's/^/        /'; refus=$((refus + 1)); fi
}
porte "socle"          "14 / 14 portes du socle"            $PY -m monde.socle.tests_socle
porte "monde"          "15 / 15 portes du monde"             $PY -m monde.tests
porte "colonnes"       "PORTE DES COLONNES : FRANCHIE"       $PY -m monde.porte_colonnes
porte "domaines"       "PORTE DES DOMAINES : FRANCHIE"       $PY -m monde.porte_domaines --comparer $REF/ref_domaines.json
porte "domaines (27)"  "PORTE DES DOMAINES : FRANCHIE"       $PY -m monde.porte_domaines --comparer $REF/ref_domaines_tous.json
porte "identite"       "PORTE DE L IDENTITE : FRANCHIE"      $PY -m monde.porte_identite
porte "iles (G1)"      "PORTE G1 .* FRANCHIE"                $PY -m monde.porte_iles
porte "archipel (G2G3)" "PORTES G2 ET G3 : FRANCHIES"        $PY -m monde.porte_archipel
porte "traversee"      "PORTES DE LA TRAVERSEE : FRANCHIES"  $PY -m monde.porte_traversee
porte "enregistreur"   "PORTE DE L ENREGISTREUR : FRANCHIE"  $PY -m monde.porte_enregistreur
porte "agent codeur"   "PORTE DE L AGENT CODEUR : FRANCHIE"  $PY -m monde.porte_agent_codeur
porte "devises"        "PORTE DES DEVISES : FRANCHIE"        $PY -m monde.porte_devises
porte "guerre"         "PORTES DE LA GUERRE : FRANCHIES"     $PY -m guerre.porte_guerre
if [ "$1" != "--vite" ]; then
  # les portes du pays : les echecs de COMPORTEMENT doivent etre ceux de la liste connue ( les portes de cout
  # dependent de la charge de la machine et ne comptent pas ). Fichiers PRIVES a ce lancement : /tmp est partage par
  # toutes les sessions de la WS ( 27/09 : deux portes.sh en meme temps ecrivaient le meme /tmp/echecs_pays.txt ).
  # references/tests_fragiles_pays.txt : tests dont l issue suit le bruit ( puissance trop faible ), ignores dans les
  # deux sens et rapportes a part ; chacun porte sa raison et sa tache Plane, le remede est un test plus grand.
  E=$(mktemp /tmp/echecs_pays_XXXXXX); S=$(mktemp /tmp/sortie_pays_XXXXXX); FR=references/tests_fragiles_pays.txt
  filtre() { awk -v F="$FR" 'BEGIN { while ((getline l < F) > 0) if (l !~ /^#/ && split(l, a, " ") >= 3) fr[a[2] " " a[3]] = 1 }
                              !(($2 " " $3) in fr)'; }
  $PY -m monde.pays.tests > $S 2>&1
  grep "^ECHOUE" $S | grep -v test_cout | sed 's/ *(.*//' | sort | filtre > $E
  if diff -q <(sort references/echecs_attendus_pays.txt | filtre) $E >/dev/null; then echo "PASSE   pays ( memes echecs de comportement que references/echecs_attendus_pays.txt )"
  else echo "ECHOUE  pays : echecs differents"; diff <(sort references/echecs_attendus_pays.txt | filtre) $E | sed 's/^/        /'; refus=$((refus + 1)); fi
  [ -f $FR ] && grep -v "^#" $FR | awk 'NF >= 3 { print $2, $3 }' | while read d t; do
    echo "        fragile, ne compte pas : $d $t $(grep -E "^(PASSE|ECHOUE) +$d +$t " $S | awk '{ print $1 }')"; done
  rm -f $E $S
fi
echo "PORTES REFUSEES : $refus"
exit $refus
