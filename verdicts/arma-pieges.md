porte: Reproductibilite du banc CHACAL, six pieges Arma
date: 2026-09-03
graines: 1
chiffre: meme graine et meme build rendent deux routes opposees ; 4163 s reels pour une phase budgetee a 1800 s
verdict: ECHEC
depend_de: 
remplace_par: 
source: arma-pieges-mesures-03-09

Six pieges Arma payes en une session, aucun trouve par relecture, tous par le banc.
Le plus grave : la requete qui cherche les routes proches NE REND PAS UN ORDRE STABLE. Meme graine, meme site, deux zones de pose differentes, donc deux missions. Toute la reproductibilite tombait la-dessus sans un message.
Remede : trier soi-meme sur les coordonnees avant tout choix, y compris avant un tirage d'indice.
Deux commandes n'existent pas dans ce build, dont celle qui fixe la graine ; il faut porter son propre generateur, ce qui vaut mieux de toute facon car il ne perturbe pas le hasard interne du moteur.
Une signature de fonction mal lue faisait que la reserve ne chassait jamais de tout l'episode, sans que le verdict le dise.
L'insertion helicoptee tuait de quatre facons differentes, toutes ramenees a une cause : laisser la physique placer dix hommes sous huit tonnes.
Deux instruments mentaient aussi : le tueur rendu est le vehicule et non son servant, et une unite creee en cours d'episode passe deux secondes sans identite, sa premiere victime etant le canari lui-meme.
