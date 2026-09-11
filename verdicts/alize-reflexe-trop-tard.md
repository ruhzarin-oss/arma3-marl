porte: ALIZE, controle positif HMT-39 : le reflexe se declenche chez 76 % des hommes touches, mais aucun signal ne le previent assez tot - le premier coup de la rafale ennemie tue en 2,7 s
date: 2026-09-11
graines: 7, 8, dix vignettes d'assaut chacune (banc alize1, palier 4, de nuit)
chiffre: 41 hommes touches sur 200 ; 27 tues du premier impact ; reflexe au moment du coup chez 31 sur 41 (75,6 %, entre l echec 50 % et la reussite 90 %) ; avance mediane 2,3 s ; canal BRUIT reconstruit hors d Arma (590 coups ennemis joints a 100 %, ecart median 0,4 m) : 75,6 % et 2,5 s au mieux, quelle que soit la portee (100, 200, 300 m, infinie) ; delai entre le debut de la rafale ennemie et le coup recu : mediane 2,7 s, moins de 2 s dans 20 cas sur 41
verdict: ECHEC
depend_de: sirocco-immunite-tactique, alize-algo-propre, tout-ce-qui-fige-coute
remplace_par: 
source: runs 2026-09-11_142934_alize1_i6 et 2026-09-11_143019_alize1_i7 ; scripts alize_rejeu.py et alize_bruit.py (archive/alize_bruit_resultat.json)

Le banc a enregistre, homme par homme, les deux entrees de l alarme locale de SIROCCO (Hit et FiredNear), et la cascade a parametres fixes a ete rejouee hors d Arma.
Le critere de Fable (reflexe chez au moins 90 % des touches) n est pas atteint : 75,6 %. Le signal existe - personne n est touche sans qu un coup ennemi soit parti avant - mais il arrive trop tard.
Le canal BRUIT ne change rien : le temoin haut (portee infinie) met tout le detachement en reflexe et fige les 20 episodes, sans gagner une seconde d avance. La raison est dans le delai : le coup qui touche arrive en mediane 2,7 s apres le PREMIER coup de la rafale, moins de 2 s dans la moitie des cas. Aucune oreille ne previent plus tot que le premier coup.
Ce que ca etablit : un reflexe REACTIF, qu il lise l impact, la balle proche ou le son, ne peut pas proteger ici ; 27 hommes sur 41 meurent de la premiere balle qui les touche.
Ce que ca N ETABLIT PAS : que la cascade soit inutile - l etage LOCAL (le binome appuie) et le recrutement n ont pas ete mesures ; ni que le reflexe ne serve pas a survivre APRES le premier coup (14 touches ont survecu au premier impact).
Consequence pour ALIZE : le gain doit venir AVANT le premier coup - savoir ou sont les defenseurs et ne pas entrer dans leur champ de tir. C est l observation (qui ne repere presque rien aujourd hui) et l anticipation de l intention ennemie (brique recommandee par Fable, jamais mesuree), pas le reflexe.
Mesure a 2 s de resolution (pas d etat.csv) : une avance inferieure a 2 s est a la limite de l instrument.
