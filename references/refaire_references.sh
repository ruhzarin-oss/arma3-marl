#!/bin/bash
# Reconstruit les trois references des portes, hors du depot ( 26/09, 27/09 ) :
#   1. la reference des domaines : le code fusionne de la reference d origine ( 5917fa8 ) + les memes corrections que le
#      moteur, puis porte_domaines --ecrire ; comparee a l ancienne si elle existe ( reproduction au bit ) ;
#   2. l ancien moteur temoin de la porte des colonnes : references/monde_ancien, copie dans $REF/monde_ancien ;
#   3. la reference des 27 domaines : les domaines 14 a 27 sont nes en colonnes, sans code d origine ; leur reference
#      est le moteur fusionne du 27/09 ( commit TOUS ), rejoue depuis une extraction propre du depot.
# Usage : bash references/refaire_references.sh [ dossier des references, par defaut /mnt/data/hmt ]
set -e
DEPOT=$(cd "$(dirname "$0")/.." && pwd); REF=${1:-/mnt/data/hmt}; PY=${PY:-python3}
C=$DEPOT/references/correctifs; ARBRE=$REF/ref_socle_fix
rm -rf $ARBRE && mkdir -p $ARBRE && git -C $DEPOT archive 5917fa8 monde | tar -x -C $ARBRE
$PY $C/patch_demande.py $ARBRE/monde/monde.py
$PY $C/patch_echelle.py $ARBRE/monde/monde.py --colonnes
$PY $C/patch_travail.py $ARBRE/monde/pays/d04_travail.py
$PY $C/patch_prio.py $ARBRE/monde/pays/d07_exterieur.py
$PY $C/patch_alpha.py $ARBRE/monde/pays/d03_economie.py
$PY $C/patch_parite.py $ARBRE/monde/pays/d07_exterieur.py
$PY $C/patch_dettes.py $ARBRE
( cd $ARBRE && PYTHONPATH=$ARBRE $PY -m monde.porte_domaines --ecrire $REF/ref_domaines_refaite.json | tail -1 )
if [ -f $REF/ref_domaines.json ]; then
  cmp -s $REF/ref_domaines_refaite.json $REF/ref_domaines.json && echo "REFERENCE DES DOMAINES REPRODUITE AU BIT" || echo "REFERENCE DES DOMAINES DIFFERENTE"
else cp $REF/ref_domaines_refaite.json $REF/ref_domaines.json; echo "reference des domaines ecrite"; fi
mkdir -p $REF/ref && rm -rf $REF/ref/monde_ancien.nouveau && cp -r $DEPOT/references/monde_ancien $REF/ref/monde_ancien.nouveau
if [ -d $REF/ref/monde_ancien ]; then
  diff -rq -x __pycache__ -x "*.avant*" -x resultats $REF/ref/monde_ancien $REF/ref/monde_ancien.nouveau >/dev/null && echo "ANCIEN MOTEUR TEMOIN IDENTIQUE" || echo "ANCIEN MOTEUR TEMOIN DIFFERENT"
  rm -rf $REF/ref/monde_ancien.nouveau
else mv $REF/ref/monde_ancien.nouveau $REF/ref/monde_ancien; echo "ancien moteur temoin pose"; fi
TOUS=9932d0c
ARBRE2=$REF/ref_tous; rm -rf $ARBRE2 && mkdir -p $ARBRE2 && git -C $DEPOT archive $TOUS monde | tar -x -C $ARBRE2
( cd $ARBRE2 && PYTHONPATH=$ARBRE2 $PY -m monde.porte_domaines --ecrire $REF/ref_domaines_tous_refaite.json | tail -1 )
if [ -f $REF/ref_domaines_tous.json ]; then
  cmp -s $REF/ref_domaines_tous_refaite.json $REF/ref_domaines_tous.json && echo "REFERENCE DES 27 DOMAINES REPRODUITE AU BIT" || echo "REFERENCE DES 27 DOMAINES DIFFERENTE"
else cp $REF/ref_domaines_tous_refaite.json $REF/ref_domaines_tous.json; echo "reference des 27 domaines ecrite"; fi
