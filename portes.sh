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
if [ "$1" != "--vite" ]; then
  # les portes du pays : les echecs de COMPORTEMENT doivent etre ceux de la liste connue ( les portes de cout
  # dependent de la charge de la machine et ne comptent pas )
  $PY -m monde.pays.tests 2>&1 | grep "^ECHOUE" | grep -v test_cout | sed 's/ *(.*//' | sort > /tmp/echecs_pays.txt
  if diff -q <(sort references/echecs_attendus_pays.txt) /tmp/echecs_pays.txt >/dev/null; then echo "PASSE   pays ( memes echecs de comportement que references/echecs_attendus_pays.txt )"
  else echo "ECHOUE  pays : echecs differents"; diff <(sort references/echecs_attendus_pays.txt) /tmp/echecs_pays.txt | sed 's/^/        /'; refus=$((refus + 1)); fi
fi
echo "PORTES REFUSEES : $refus"
exit $refus
