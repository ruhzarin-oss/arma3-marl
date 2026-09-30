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
$PY $C/patch_faim.py $ARBRE
$PY $C/patch_prix.py $ARBRE
$PY $C/patch_autoconsommation.py $ARBRE/monde/pays/d09_agriculture.py
$PY $C/patch_devises.py $ARBRE
$PY $C/patch_priorite_devises.py $ARBRE
$PY $C/patch_rupture.py $ARBRE
$PY $C/patch_plafond.py $ARBRE
$PY $C/patch_lissage.py $ARBRE
$PY $C/patch_ancre.py $ARBRE
$PY $C/patch_menages_a.py $ARBRE
$PY $C/patch_marchands.py $ARBRE
$PY $C/patch_licencier.py $ARBRE
$PY $C/patch_passe_fiscal.py $ARBRE
$PY $C/patch_migrations.py $ARBRE/monde/pays/d07_exterieur.py
$PY $C/patch_patrons.py $ARBRE
$PY $C/patch_menages_e.py $ARBRE          # HMT-126 ( e ) : factures et cotisations apres la nourriture, coupure
$PY $C/patch_menages_d.py $ARBRE          # HMT-126 ( d ) : la consommation des menages
$PY $C/patch_menages_e2.py $ARBRE         # HMT-126 ( e, suite ) : plancher sans revenu, insaisissable du fisc
$PY $C/patch_insaisissable.py $ARBRE       # HMT-126 ( e, 28/09 ) : l insaisissable du fisc copie la loi ( KEDE art. 33 par. 2 )
$PY $C/patch_kea.py $ARBRE/monde/pays/d06_etat.py      # 28/09 : le KEA branche dans tous les mondes ( chef de projet ; la Grece depuis 2017 )
$PY $C/patch_allocation_enfant.py $ARBRE/monde/pays/d06_etat.py   # 28/09 : l allocation A21, apres le KEA
$PY $C/patch_gerance_cessation.py $ARBRE          # HMT-139 a : gerance et reglement des dettes par rang ( moteur )
$PY $C/patch_greve_arrieres.py $ARBRE        # HMT-143 ( 29/09 ) : tout employeur debiteur regle ses arrieres a la paie, meme sans bulletin
$PY $C/patch_cuve_ouverture.py $ARBRE  # HMT-143 ( 29/09 ) : la cuve de brut nait pleine et a elle, au bilan d ouverture
$PY $C/patch_controle_entreprises.py $ARBRE  # ( 29/09 ) le controle d une entreprise extrapole sur au moins un trimestre
$PY $C/patch_garde_import.py $ARBRE  # ( 29/09, run long ) le negoce : demande bornee par habitant, reserve de nourriture du marche
$PY $C/patch_blocus.py $ARBRE                       # 29/09 : le port pris, c est le blocus ( G25 )
$PY $C/patch_fisc_drachmes.py $ARBRE                # 29/09 ( HMT-140 ) : bareme de l IR en drachmes, dividendes et IS hors du domaine 3
$PY $C/patch_enfia_drachmes.py $ARBRE               # 29/09 ( regle 8 ) : l ENFIA en drachmes
$PY $C/patch_passe_exercice.py $ARBRE  # ( 29/09 ) le controle d une entreprise redresse le passe exercice par exercice
$PY $C/patch_orphelins.py $ARBRE/monde/pays/d01_population.py   # ( 30/09, session Classes ) aucun mineur seul : parente ( AK 1510, 1589, 1592, 1463 ) sinon accueil, garde le temps d une absence ; d21 appelle d01 a l arrestation
$PY $C/patch_fecondite.py $ARBRE/monde/pays/d01_population.py   # ( 30/09, session Classes ) fecondite copiee sur Eurostat demo_frate 2024 : ages simples a l age de la naissance, jumeaux, duree des pertes, couples age par age
( cd $ARBRE && PYTHONPATH=$ARBRE $PY -m monde.porte_domaines --ecrire $REF/ref_domaines_refaite.json | tail -1 )
if [ -f $REF/ref_domaines.json ]; then
  cmp -s $REF/ref_domaines_refaite.json $REF/ref_domaines.json && echo "REFERENCE DES DOMAINES REPRODUITE AU BIT" || echo "REFERENCE DES DOMAINES DIFFERENTE"
else cp $REF/ref_domaines_refaite.json $REF/ref_domaines.json; echo "reference des domaines ecrite"; fi
mkdir -p $REF/ref && rm -rf $REF/ref/monde_ancien.nouveau && cp -r $DEPOT/references/monde_ancien $REF/ref/monde_ancien.nouveau
if [ -d $REF/ref/monde_ancien ]; then
  diff -rq -x __pycache__ -x "*.avant*" -x resultats $REF/ref/monde_ancien $REF/ref/monde_ancien.nouveau >/dev/null && echo "ANCIEN MOTEUR TEMOIN IDENTIQUE" || echo "ANCIEN MOTEUR TEMOIN DIFFERENT"
  rm -rf $REF/ref/monde_ancien.nouveau
else mv $REF/ref/monde_ancien.nouveau $REF/ref/monde_ancien; echo "ancien moteur temoin pose"; fi
TOUS=2af8f04     # 29/09 : integration 13 ( fisc de la guerre b3f340c, passe fiscal du moteur 3ba4dc8 )
ARBRE2=$REF/ref_tous; rm -rf $ARBRE2 && mkdir -p $ARBRE2 && git -C $DEPOT archive $TOUS monde | tar -x -C $ARBRE2
( cd $ARBRE2 && PYTHONPATH=$ARBRE2 $PY -m monde.porte_domaines --ecrire $REF/ref_domaines_tous_refaite.json | tail -1 )
if [ -f $REF/ref_domaines_tous.json ]; then
  cmp -s $REF/ref_domaines_tous_refaite.json $REF/ref_domaines_tous.json && echo "REFERENCE DES 27 DOMAINES REPRODUITE AU BIT" || echo "REFERENCE DES 27 DOMAINES DIFFERENTE"
else cp $REF/ref_domaines_tous_refaite.json $REF/ref_domaines_tous.json; echo "reference des 27 domaines ecrite"; fi
