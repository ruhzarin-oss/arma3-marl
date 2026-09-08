porte: Le PLAN contre son TEMOIN au palier 0 : le plan combat, aucun des deux ne pose de charge
date: 2026-09-08
graines: plan 7 et 8 ; temoin 5 et 6
chiffre: ennemis neutralises 6 et 14 (plan) contre 0 et 0 (temoin) ; charges posees 0 sur 3 dans les quatre episodes ; survivants BLUFOR 5 et 7 (plan) contre 10 et 4 (temoin) ; 4 episodes ACCEPTES, 15 portes vertes sur 15
verdict: PASSE
depend_de: chacal-portes, chacal-bras-temoin-palier0, lanceur-hmt-temoin
remplace_par: 
source: runs 2026-09-08_1415_chacal (plan) et 2026-09-08_0956_chacal (temoin)

Premiere comparaison a bras oppose, meme palier, meme facon de tirer le monde. Elle separe nettement les deux bras : le plan arrive au contact et detruit, le temoin ne tire jamais une balle.
Mais aucun des deux ne pose de charge, et les journaux donnent DEUX causes differentes, pas une.

Graine 7 — LA MITRAILLEUSE LOURDE. Le detachement est vu pendant la mise en place (`compromis|ENNEMI_VU_EN_COMBAT|phase|4`), rompt le contact, se rearticule aussitot avec son element d'assaut a 206 m, puis reprend l'assaut sur le meme axe. `O_HMG_01_high_F` tire 200 coups dans la fenetre d'assaut et signe 6 des 9 morts BLUFOR, dont le CHEF, l'ADJOINT, le MEDECIN et DEMO_2. Cinq hommes tombent en 224 s. Cinq tirs avant l'assaut, 460 pendant : tout se joue dans cette fenetre.
C'est la MEME arme qui avait tue 8 hommes en 86 s le 07/09 lors du run hors corpus. Deux episodes independants, une seule cause.

Graine 8 — LE TEMPS. L'approche s'enlise, l'observation est coupee par une compromission a sept minutes, et l'assaut demarre avec son element a plus de deux kilometres. Les trois charges sont manquees sur plafond, cause journalisee `ELEMENT_N_ARRIVE_PAS`, a 2216, 1988 et 1882 m des objets.

Fait de conception a verser au dossier : le plafond de la phase d'assaut vaut 900 s dans les deux episodes, alors que les plafonds d'approche (7696 et 5799 s), d'observation (1863 et 1767 s) et d'exfiltration (1284 et 1395 s) sont derives de la geometrie tiree. L'assaut recoit donc un plafond CONSTANT, le plus court de tous, pour la phase qui doit franchir la derniere distance sous le feu ET poser trois charges.

Ce que ca N'ETABLIT PAS : que rallonger ce plafond suffise. La graine 7 avait son element a 206 m et n'a pas manque de temps, elle a manque de vivants. Deux defauts distincts, deux remedes distincts.
Prochaines mesures, ecrites avant de les lancer, UNE SEULE a la fois :
(a) deriver le plafond d'assaut de la distance a couvrir, comme les autres phases, et rejouer les memes graines 7 et 8 ;
(b) traiter la mitrailleuse lourde avant de reprendre l'assaut — la neutraliser ou changer d'axe — plutot que reprendre sur le meme axe apres une rupture de contact.
