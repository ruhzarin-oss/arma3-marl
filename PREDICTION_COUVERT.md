# LES 11× DU COUVERT — la prédiction, déposée AVANT la correction

*11 août 2026. Écrit avant d'avoir touché au mécanisme.*

## LE FAIT MESURÉ

Mesuré **par observation**, comme Arma l'a mesuré sur 563 000 d'entre elles : être vu multiplie
la mortalité par **+856 %** dans la sandbox, contre **+75 %** certifiés sur Arma.

**Autrement dit : ne pas être vu y vaut neuf fois la sûreté que ça vaut dans le vrai jeu.**

## POURQUOI ÇA COMPTE, ET CE N'EST PAS LE RÉALISME

Un agent entraîné là-dedans apprend — correctement, pour son monde — que **le couvert paie
presque tout**. Il optimise une sûreté qui n'existe pas chez le juge. C'est le mécanisme
derrière deux échecs déjà mesurés : « un paramètre refuse de transférer trois fois », et 94,6 %
annoncés au gymnase pour 0 % chez le juge externe. Or la fiche `cout-exposition-par-metre` dit
que **les gagnants ENTRENT** — 0,65 contre 1,21 d'exposition par mètre. Un monde où se cacher
est neuf fois trop payant ne produit pas ça : il produit des agents qui survivent sans arriver.

## LA PRÉDICTION — elle peut échouer

> En ramenant le contraste de **+856 %** vers **+75 %**, le flanc doit **cesser de protéger**
> — les −0,42 pertes doivent tomber vers zéro, comme Arma le certifie (« zéro sur
> l'élimination ») — **sans cesser de faire arriver** : les +19,9 points de prise doivent
> tenir, Arma en certifiant +17,3.

## CE QUI LA FERAIT ÉCHOUER — écrit avant

- **Les deux tombent ensemble** → je n'ai pas corrigé la protection, j'ai cassé le monde.
- **Aucun des deux ne bouge** → ce contraste ne gouvernait pas la doctrine, et mon raisonnement
  est faux. On le dit, on ne pousse pas le bouton jusqu'à l'absurde.
- **Le bouton n'atteint jamais +75 %** → ce n'est pas ce mécanisme qui manque.

## ⚠️ ET UNE PANNE D'INSTRUMENT TROUVÉE AVANT DE LANCER

Le premier balayage de `feu_sur_connu` rendait des contrastes qui **montaient** avec le bouton
— 856 %, puis 4086 %. C'était mon instrument, pas le monde : je classais « vu / pas vu » avec
`last_exposed`, **qui dérive du même `los` que le bouton modifie**. Le traitement déplaçait donc
l'étiquette en même temps que l'effet.

> **Correction : l'étiquette « vu » se lit sur la visibilité GÉOMÉTRIQUE**, relevée **avant**
> toute application du bouton. Une mesure dont l'étiquette dépend du traitement ne mesure rien.
