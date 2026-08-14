# Note — pourquoi les 20 épisodes se rejouent, et pourquoi ce n'est pas un second tirage

Déposé le 14/08/2026, avant la relance.

## La raison, et elle est unique

La première série **n'a rendu aucune lecture** : sa porte est tombée. `dcover` était hors
de la plage du gymnase (médiane 0,133 contre [0,000 ; 0,131], 60,1 % des décisions au-delà
du 99ᵉ centile, deux épisodes coincés sur le garde-fou). Mon dépôt posait explicitement
cette condition d'échec : *« une colonne qui ressort de sa plage → le monde a bougé sous
la mesure »*.

**Une mesure dont la porte tombe ne rend pas de verdict. Elle ne se relit pas, elle se
refait — après réparation de ce qui l'a fait tomber.**

Ce qui a changé entre les deux séries : **rien d'autre que `dcover`**. Seuil local au lieu
d'une constante globale, rayon de recherche 15 au lieu de 8. Vérifié par une sonde qui a dû
d'abord reproduire la panne connue (95,3 % de garde-fou sur le site plat) avant qu'on la
croie.

## Ce qui NE change pas

**Les critères de `DEPOT_20_EPISODES.md` sont repris à l'identique**, sans une virgule de
différence :

- prise par le critère déjà codé, `dmin < 25` **et** `vivants > 0` ;
- référence gymnase 59,4 %, intervalle ±22 points à n=20 ;
- gel : ≥ 18 figés → réel · ≤ 3 → n'a jamais existé · **4 à 17 → indécis, on ne conclut
  pas et on ne rejoue pas** ;
- les deux contrôles positifs : scène confirmée par le jeu, azimuts distincts ;
- échec si moins de 15 épisodes valides, ou si une colonne ressort de sa plage.

## Ce qui serait malhonnête, et que je ne fais pas

Rejouer parce que le résultat déplaît. **Le 0/20 n'est pas la raison de la relance** — la
porte tombée l'est. Si la porte tient cette fois et que la prise reste à 0, **c'est le
résultat**, et il se dépose tel quel.

Et si le gel retombe dans la bande indécise, il y reste : la bande a été écrite pour être
respectée, pas pour être franchie au troisième essai.
