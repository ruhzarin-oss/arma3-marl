porte: Plancher de bruit de la mission complete : a monde ET configuration fixes, l'issue va de 0 a 5 survivants
date: 2026-09-09
graines: 7, huit repetitions
chiffre: 8 episodes acceptes, meme configuration et meme graine — survivants 5, 4, 5, 5, 0, 5, 3, 2 (de 0 a 5 sur 10, moyenne 3,6) ; QUATRE causes de fin differentes : ARTICULATION_ROMPUE, CHARGES_INCOMPLETES, COMPROMIS_LOIN, DETACHEMENT_DETRUIT ; durees de 4590 a 8899 s, soit un facteur 1,9
verdict: PASSE
depend_de: monde-fixe-episode-libre, chacal-portes
remplace_par: 
source: runs 2026-09-09_0146_chacal et 2026-09-09_0155_chacal, arretes a la main apres 4 episodes chacun

C'est le chiffre qui manquait depuis le debut, et il condamne une methode.
Huit episodes rigoureusement identiques — meme graine, meme palier, meme bras, meme empreinte de mission — rendent des survivants allant de zero a cinq et quatre causes de fin differentes. La duree double du plus court au plus long.
La cause est connue et voulue : la mission ne seme pas le hasard interne du moteur, pour laisser LAMBS libre de decider. La graine fixe le MONDE, jamais l'EPISODE.
Consequence operatoire, deja cablee dans le controle d'avant-run : un job compare soit sur au moins deux graines distinctes, soit sur au moins cinq repetitions. Un episode par bras ne conclut rien, et les trois comparaisons du 08/09 ont perdu leur valeur de preuve.
Ordre de grandeur a retenir pour dimensionner : pour distinguer un ecart d'un homme sur dix avec une dispersion pareille, il faut des dizaines de repetitions par cellule. Sur une mission de 55 minutes c'est hors de portee ; sur une vignette de 8 minutes c'est une nuit.
Contraste avec la vignette, mesure le meme jour : au meme niveau et sur la meme graine, la vignette d'assaut rend huit fois exactement cinq survivants et zero charge. Zero dispersion.
Ce que ca N'ETABLIT PAS : que cette dispersion soit du bruit sans structure. Les quatre causes de fin different, mais elles restent lisibles, et la detection en cascade est une explication candidate. Ce n'est pas mesure ici.
Les runs ont ete arretes a la main a huit episodes sur dix prevus, l'etendue etant deja acquise et les instances valant mieux ailleurs.
