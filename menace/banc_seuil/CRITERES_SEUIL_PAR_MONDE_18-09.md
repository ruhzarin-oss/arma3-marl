# Criteres pre-enregistres - SEUIL-PAR-MONDE-18-09 ( ecrit AVANT de poser, 18/09/2026 au soir )

Ordre de Younes : « attaque ca en parallele, laisse-le finir tout seul, tu peux prendre 9 serveurs ». Je prends les instances
5, 6, 7, 8, 10, 11, 12, 13 ( la 9 est le labo ; 1 a 4 restent a l autre session ). Banc `chacalvue` ( copie ), jamais `bancs/chacal`.

## But
Une table « monde -> seuil de connaissance de nuit d* », et les points pour tester la deuxieme variable de l equation
( la visibilite du lieu ). C est le point 3 du plan 33e1c3a. La table sert ensuite a poser les menaces a d* x [ 0,8 ; 1,2 ].

## Instrument : patch_banc_journal.py ( sur chacalvue, apres patch_banc_vue_fine.py )
Sonde a 1 s pendant 120 s ; vis_max et vis_moy ( checkVisibility continu ) dans chaque sonde ; fenetre de 600 s, fermee 30 s
apres la premiere connaissance ; episode rendu a la fin de la fenetre ( VOID BANC_TERMINE ).
FUMEE AVANT LA CAMPAGNE ( 2 jobs, mondes 4 et 5 ) : A = 150 m, B = 250 m. Attendu : 0 erreur SQF ; >= 100 sondes dans les 120
premieres secondes ; vis_max et vis_moy presents, entre 0 et 1 ; A : connue en <= 10 s, fenetre fermee ~30 s apres, FINI VOID
BANC_TERMINE, episode < 4 min ; B : si jamais connue, la fenetre dure >= 590 s puis VOID BANC_TERMINE. Un seul echec = on corrige
et on rejoue la fumee, la campagne ne part pas.

## Campagne : 17 jobs x 2 mondes = 34 episodes, de nuit, cible debout regardee
- mondes 4 et 5 : 150, 157, 164, 171 m ; mondes 6 et 7 : 170, 185, 200, 215 m ; mondes 8 et 9, 11 et 12 : 150, 170, 190, 210 m ;
- 17e job : mondes 4 et 5 a 157 m REJOUE sur une autre instance ( la scene est-elle deterministe ? ) ;
- bras ENTRELACES : les jobs sont distribues en tourniquet sur les 8 instances, aucune instance ne porte un seul monde ni une seule distance.

## Lecture ( par episode valide : ligne de vue = 1, pas de refus, 0 erreur SQF ; distance VRAIE )
connue / jamais en 600 s ; delai de premiere connaissance ( resolution 1 s ) ; connue en 90 s ( la porte de e33942b ) ; vis_moy et
vis_max a la premiere sonde et en moyenne sur la fenetre. d* d un monde = milieu entre le plus loin CONNU et le plus pres JAMAIS.

## Predictions ecrites avant
1. LIEU : les d* des 8 mondes s etalent sur plus de 30 m ( si tous tiennent dans 30 m, le « seuil depend du lieu » d aujourd hui
   etait un accident des mondes 4 et 6 ).
2. DELAI : dans au moins 3 mondes sur 4 paires, le delai du point connu le plus lointain depasse celui du point le plus proche.
3. DEUXIEME VARIABLE : parmi les episodes a moins de 20 % du d* de leur monde, vis_moy des CONNUS > vis_moy des JAMAIS
   ( separation lue par l aire sous la courbe ; >= 0,75 : candidate retenue pour EvoGP ; <= 0,60 : checkVisibility n est PAS la
   deuxieme variable, chercher ailleurs - fond, azimut de la lune ). Entre les deux : indecis, le dire.
4. DETERMINISME : le job rejoue donne les memes issues ( connue / jamais ) et des delais a 2 s pres. Sinon la repetition a un sens
   et la regle « 6 episodes par distance » de e33942b redevient utile.

## Limites dites d avance
Un episode par ( monde, distance ) : descriptif. Une heure de nuit, une posture. Les autres sessions peuvent charger la machine
( charge archivee par run ). La fermeture anticipee de la fenetre coupe l observation apres la connaissance : voulu.
