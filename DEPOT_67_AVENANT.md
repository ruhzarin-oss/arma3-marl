# Avenant au dépôt des 67 — trois clauses écrites pendant que 3 épisodes seulement sont joués

Déposé le 15/08/2026, sur exigence de Fable, **avant que le run ait produit la moindre
donnée lisible**. Aucune de ces clauses ne relâche quoi que ce soit ⟨règle 13⟩.

## Clause 1 — si les 67 ne suffisent pas, on PROLONGE, on n'élargit pas

La taille de 67 vient d'une extrapolation à partir de **9 morts observés**. L'intervalle de
Poisson sur 9 va de **4 à 17** : le run peut donc livrer entre **~14 et ~57 morts** dans la
case critique, et rater les 30 exigés.

**Si une case rend moins de 30 morts : on prolonge au MÊME protocole, jusqu'à l'atteindre.
On n'élargit pas la bande, on ne baisse pas le seuil, on ne « lit quand même ».**

Le geste est décidé **maintenant**, avant de voir le chiffre — c'est tout l'objet de cette
clause.

## Clause 2 — les épisodes FIGÉS sont INCLUS dans le dénominateur de B

Un épisode où la politique n'émet qu'une action de bout en bout est un **échantillon vrai**
de cette politique dans ce monde, et B conditionne déjà sur « exposé ». Les exclure
reviendrait à choisir les épisodes qui arrangent.

**Ils sont inclus, et le taux de gel est rapporté à côté du verdict de B**, jamais fondu
dedans.

## Clause 3 — B doit être stratifiée par la DISTANCE À L'ENNEMI

⚠️ Le rapport de protection est propre **par construction dans le gymnase seulement** :
`(1 − 0,7·incover)` y est un multiplicateur pur. **Sur Arma, il ne l'est pas** — les
positions sur couvert corrèlent avec la distance aux tireurs, et le projet a déjà mesuré
que l'effet d'être vu **croît avec la distance**.

Sans précaution, un verdict de B pourrait n'être qu'un artefact de *« le couvert n'existe
qu'à courte portée »*.

**On enregistre donc, à chaque exposition et à chaque mort, la distance à l'ennemi le plus
proche** (colonne `nd`, déjà dans les douze). Puis :

1. on **vérifie l'équilibre** de cette distance entre les cases sur-couvert et hors-couvert ;
2. **si les distances médianes diffèrent de plus de 20 %, la protection se lit STRATIFIÉE**
   par bandes de distance, et le verdict porte sur la lecture stratifiée ;
3. si elles s'équilibrent, la lecture brute suffit — et l'équilibre est **rapporté**.

## Ce que cet avenant ne fait pas

Il ne change ni la grandeur, ni les contrôles positifs, ni les trois bandes de lecture de
`DEPOT_COUVERT.md` et de son amendement. Il ferme trois portes de sortie qui auraient permis
de lire le résultat dans le sens qui arrange.
