porte: ALIZE, controle positif HMT-39 : le reflexe se declenche chez 63 % des hommes touches, et la moitie d entre eux sont touches par le PREMIER coup d un engagement - aucun signal reactif ne peut les prevenir
date: 2026-09-11
graines: 7, 8, dix vignettes d'assaut chacune (banc alize1, palier 4, de nuit)
chiffre: 41 hommes touches sur 200 ; 27 tues du premier impact ; reflexe AVANT le vol de la balle qui touche (dernier pas < tc - 1 s) chez 26 sur 41 (63,4 %, critere 90 %, echec sous 50 %) ; avance mediane 3,1 s ; 21 touches sur 41 sans aucun coup ennemi dans les 10 s avant (hors la balle qui touche) ; pour les 20 autres, delai entre le debut de la rafale et le coup : mediane 3,7 s (quartiles 2,1 et 6,4) ; canal BRUIT reconstruit hors d Arma (590 coups ennemis joints a 100 %, ecart median 0,4 m) : 63,4 % a toutes les portees, avance 3,8 s au mieux
verdict: ECHEC
depend_de: sirocco-immunite-tactique, alize-algo-propre, tout-ce-qui-fige-coute
remplace_par: 
source: runs 2026-09-11_142934_alize1_i6 et 2026-09-11_143019_alize1_i7 ; scripts alize_rejeu.py et alize_bruit.py (archive/alize_bruit_resultat.json)

Le banc a enregistre, homme par homme, les deux entrees de l alarme locale de SIROCCO (Hit et FiredNear), et la cascade a parametres fixes a ete rejouee hors d Arma.
Le critere de Fable (reflexe chez au moins 90 % des touches) n est pas atteint : 63,4 %. Pour la moitie des touches, aucun coup ennemi n est parti dans les 10 s avant : c est le premier coup de l engagement qui touche.
Le canal BRUIT ne change rien : le temoin haut (portee infinie) met tout le detachement en reflexe et fige les 20 episodes, sans gagner une seconde d avance. La raison est dans le delai : la moitie des hommes touches le sont par le premier coup d un engagement ; pour les autres, la rafale ne donne que 3,7 s d avance en mediane. Aucune oreille ne previent plus tot que le premier coup.
Ce que ca etablit : un reflexe REACTIF, qu il lise l impact, la balle proche ou le son, ne peut pas proteger ici ; 27 hommes sur 41 meurent de la premiere balle qui les touche.
Ce que ca N ETABLIT PAS : que la cascade soit inutile - l etage LOCAL (le binome appuie) et le recrutement n ont pas ete mesures ; ni que le reflexe ne serve pas a survivre APRES le premier coup (14 touches ont survecu au premier impact).
Consequence pour ALIZE : le gain doit venir AVANT le premier coup - savoir ou sont les defenseurs et ne pas entrer dans leur champ de tir. C est l observation (qui ne repere presque rien aujourd hui) et l anticipation de l intention ennemie (brique recommandee par Fable, jamais mesuree), pas le reflexe.
Mesure a 2 s de resolution (pas d etat.csv) : une avance inferieure a 2 s est a la limite de l instrument.

CORRECTION DU 11/09 (revue de Fable) : la premiere version comptait un pas coincidant avec le coup, qui contient deja l impact, et prenait la ligne tir de la balle qui touche pour un avertissement. Chiffres refaits : 75,6 % -> 63,4 % ; 2,7 s -> la moitie sans aucun avertissement, 3,7 s pour les autres. La conclusion ne change pas.
