porte: Un UAV d'Arma renseigne-t-il l'IA
date: 2026-08-16
graines: 1
chiffre: knowsAbout = 0 sur 4 montages, y compris cloue a 148 m au-dessus de la cible pendant 60 s
verdict: ECHEC
depend_de: knowsabout-de-camp
remplace_par: 
source: drone-arma-ne-donne-rien-a-lia

Deux drones d'Arma ne font rien connaitre a l'IA, meme colles a la cible, quel que soit le mode de combat.
Un helicoptere a equipage IA percoit, lui, mais seulement en oblique : pose a la verticale au-dessus de la cible il rend zero pendant une minute.
Consequence : le capteur d'un UAV alimente le terminal d'un operateur humain, pas la base de connaissance des unites IA.
Tout banc drone dans Arma devra ECRIRE la perception du drone par script ; le moteur ne la fournit pas.
Piege de mesure paye : l'helicoptere semblait percevoir alors qu'il heritait de la connaissance de camp d'un fantassin present dans la meme scene.
Regle qui en sort : un observateur qu'on teste ne partage jamais la scene avec un autre observateur ami.
