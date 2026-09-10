porte: La correction terrain (positions accessibles depuis le depart) ne change pas l'issue au palier 4
date: 2026-09-10
graines: 7, 8, deux repetitions chacune par bras
chiffre: accessible 0 : 2 succes sur 4 (graine 7 : 1/2, graine 8 : 1/2) ; accessible 1 : 2 succes sur 4 (graine 7 : 0/2, graine 8 : 2/2) ; la prediction — debloquer la graine 7 — donne 0 sur 2 AVEC la correction et 1 sur 2 SANS
verdict: ECHEC
depend_de: palier4-gagne-une-fois-sur-deux, plancher-de-bruit-mission-complete
remplace_par: 
source: runs 2026-09-09_1625_chacal et 2026-09-09_1635_chacal

La correction etait nee d'un seul episode : graine 7 du 09/09 matin, le moteur declarait l'arrivee a 800 m, pentes de 29 et 37 degres, ABANDON par ARTICULATION_ROMPUE.
Rejoue quatre fois, ce blocage ne revient pas, meme SANS la correction : aucun abandon sur 8 episodes. Le blocage de la graine 7 etait un tirage, pas une propriete du terrain.
A n = 4 par bras, aucun effet n'est visible. Un effet de plus de 3 episodes sur 4 est exclu ; un effet plus petit reste possible et n'est pas mesure.
Le parametre CHACAL_ACCESSIBLE reste dans le code, a 0 par defaut. Il ne coute rien et garde le comportement d'origine.
Lecon de methode : un echec observe une fois est un candidat, pas une cause. Il se rejoue AVANT d'etre corrige.
