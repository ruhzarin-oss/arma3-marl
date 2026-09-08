porte: Quatre valeurs de configuration lues directement sur Arma 3
date: 2026-09-03
graines: n/a
chiffre: rayon 1,688 m ; sensitivity 6,0 ; sensitivityEar 0,125 ; audible 0,05 ; indirectHitRange 0,0
verdict: PASSE
depend_de: loi-auditive-forme
remplace_par: 
source: Plane HMT-16

Les constantes qui entrent dans les lois de detection sont LUES dans la configuration du moteur, pas supposees.
Le rayon vient de la boite englobante reelle d'un homme POSE : le champ radius est ABSENT du modele et la mesure de taille rend zero en mode sans affichage. Il faut donc poser l'homme pour le mesurer.
Piege evite, et il change les conclusions d'un facteur 800 : le champ audible de l'entite vaut 0,05, ce n'est pas l'audibleFire de la munition qui vaut 40,0.
Ce que ca n'etablit pas : que ces valeurs suffisent a predire une detection ; ce sont des entrees, pas un modele.
