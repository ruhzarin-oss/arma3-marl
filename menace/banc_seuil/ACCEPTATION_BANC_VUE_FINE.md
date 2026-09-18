# patch_banc_vue_fine.py - test d acceptation ( ecrit AVANT de l appliquer, 18/09/2026 )

Propose par la session du balayage BANC-TROU-18-09. Hors depot : a appliquer par la session qui tient la mission,
FILE VIDE ( lancer.sh resynchronise la mission a chaque episode : l appliquer pendant PRIX DU TEMPS changerait
l empreinte de la campagne en cours de route ). Remplace patch_banc_refuse.py ( s applique qu il ait ete joue ou non ).

## Deja prouve a blanc ( sur une copie de 60_phases.sqf du commit 3b31348 )
- ancres uniques ; ordre « seul » et ordre « apres patch_banc_refuse » -> fichiers IDENTIQUES ;
- rejoue deux fois -> refus bruyant ; patch_banc_refuse joue apres -> refus bruyant ( ancre absente ) ;
- accolades, crochets, parentheses equilibres avant et apres ; le lecteur menace/lire_banc.sh lit les lignes telles quelles.

## Ce que SEUL Arma peut prouver - fumee de 3 jobs x 2 mondes ( ~35 min sur 3 instances libres )
| job | reglage | attendu |
|---|---|---|
| POSITIF | nuit, 100 m | ligne_de_vue=1, hommes_avec_vue >= 5, vue_reelle >= 1, connue en <= 10 s ( comme le matin ) |
| LE CAS QUI ECHOUAIT | nuit, 225 m, mondes 4 et 5 | ligne_de_vue=1 dans au moins 1 monde sur 2 ( 0 sur 2 avant le patch ) |
| NEGATIF | nuit, 225 m, recherche rendue impossible ( controle_dist=20000 : tout candidat tombe hors carte ou en mer ) | ligne banc_refuse, issue VOID cause BANC_SANS_LIGNE_DE_VUE, episode fini en < 3 min, 0 erreur SQF |
- GLOBAL : 0 erreur SQF ; duree de la recherche < 2 s ( ecart entre la ligne precedente du RPT et banc_perception ) ;
  |distance_posee - distance| <= 6 % ; vue_reelle et hommes_avec_vue d accord a 2 hommes pres ( sinon le dire, pas le cacher ).
- Si le NEGATIF ne finit pas vite ou laisse une erreur : retirer la ligne VOID ( une seule ligne ), garder le reste.

## Ce que le patch NE fait PAS
- il ne change ni la cible, ni le regard, ni la sonde : les episodes valides restent comparables a ceux du matin ;
- la distance posee peut s ecarter de +-6 % : LIRE `verite_distance_menace` ( deja dans la sonde ), pas la consigne.
