# Criteres pre-enregistres - PORTEE-REGARD-CENTRE-18-09 ( ecrit AVANT de poser, 18/09/2026 ~23 h )

Cadre de Younes ( 18/09, ~22 h 55 ) : travail autonome jusqu a 9 h, points 1 a 4 du plan + P2 autorises ; interdits : bancs/chacal,
GitHub, arret de processus. Banc `chacalvue` ( 2786e65 : recherche fine, sonde 1 s, checkVisibility continu, regard tourne des t = 0 ).

## Question
Acquis : regard centre, cible DEBOUT, nuit, connue en 3-11 s de 128 a 215 m ( 29 sur 33 ; les 4 « jamais » = cibles masquees ).
Jusqu ou cela porte-t-il ? De nuit et de jour, a 250, 300, 400, 500 et 600 m.

## Jobs : 2 eclairages x 5 distances x 4 paires de mondes ( 4-5, 6-7, 8-9, 11-12 ) = 40 jobs, 80 episodes, 12 instances
Ordre MELANGE ( graine 1841, la premiere a partir de 1809 qui donne a CHAQUE instance les deux eclairages, au moins deux distances et deux paires de mondes ) puis tourniquet sur les instances : aucune instance ne porte un seul eclairage, une seule distance ou une
seule paire. Fenetre 600 s, fermee 30 s apres la connaissance.

## Validite ( ecrite avant, et DURCIE par la lecon du soir )
ligne_de_vue = 1, pas de refus, 0 erreur SQF, angle de la 1re sonde <= 5 deg, et **vis_moy > 0,01** ( une cible reelle masquee n est
pas un echec de perception : 4 cas sur 33 ce soir ). Un « jamais » ne compte que si la fenetre est allee au bout ( >= 590 s ).
La distance lue est la distance VRAIE.

## Lecture
Par eclairage et par tranche de distance vraie ( 225-275, 275-350, 350-450, 450-550, 550-650 m ) : part connue en 600 s, part connue
en 90 s ( la fenetre de la mission ), delai median des connus. Portee p50 = tranche ou la part connue en 90 s passe sous 50 %.

## Predictions ecrites avant
1. NUIT : encore connue a >= 80 % dans la tranche 225-275 m ( un point non centre a 263 m etait connu en 3 s ).
2. NUIT : la part connue en 90 s passe sous 50 % quelque part entre 275 et 650 m ( sinon la vision nocturne porte plus loin que ce banc ).
3. JOUR : a chaque tranche, part connue du jour >= part connue de la nuit.
4. DELAI : contrairement a l apres-midi ( artefact du pivot ), le delai median des connus reste <= 15 s dans toutes les tranches ou
   la part connue depasse 50 %. S il s allonge franchement ( > 30 s ) regard centre, alors l allongement existe bel et bien et je le dis.
Toute prediction fausse est rapportee telle quelle.

## Limites
Cible debout ( les vraies menaces sont ACCROUPIES : banc suivant ), un episode par ( eclairage, distance, monde ), machine partagee.
A longue distance beaucoup d episodes seront refuses faute de ligne de vue : le refus coute quelques secondes et n est pas un resultat.
