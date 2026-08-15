# Rétractation — « couvert à portée » n'a jamais voulu dire à portée

Déposé le 15/08/2026. Faute trouvée par Fable en relisant mes propres tableaux : deux
conditionnelles censées être différentes rendaient **le même nombre à trois décimales**
(0,727 et 0,727 sur Arma ; 0,232 et 0,229 au gymnase).

## La faute

```
1/30 exactement    = 0,0333333333
mon seuil          = 0,0330000000
1/30 <= 0,033 ?      FAUX
```

`dcover` est quantifié en cellules : ses valeurs sont 0, 1/30, 2/30… **Mon seuil de 0,033
était inférieur à 1/30.** Il excluait donc les **116 pas à exactement une cellule** et se
réduisait à « SUR le couvert » — 150 pas dans les deux cas, effectifs identiques.

**« À portée » mesurait « dessus ».** Le verdict `VERDICT_SUBIE.md` ne mesurait pas ce
qu'il annonçait : il est **rétracté**.

## La mesure refaite, seuil corrigé (≤ 1/30 + ε, donc 266 pas)

| | P(exposé \| couvert à portée) | part forcée |
|---|---|---|
| GYMNASE | 0,231 | 45,8 % |
| ARMA | 0,703 | 74,2 % |

**Rapport 3,05** (contre 3,13 avant) — **même lecture : CHOISIE.** La faute n'a pas changé
la conclusion. **C'est de la chance, pas de la méthode**, et ça ne rachète pas le bug.

## Sixième critère troué du jour

Après l'arrondi du choix de site, le critère `dcover` insatisfiable, la porte d'azimut trop
stricte, la bande de gel absurde et les bandes de masquage non partitionnantes. Celui-ci
est d'une autre espèce : **un seuil écrit en décimal contre une grandeur quantifiée en
fractions.** Il aurait suffi d'imprimer les valeurs distinctes de `dcover` avant de seuiller.

**Clause à ajouter à la règle 18** : quand une grandeur est **quantifiée**, le banc imprime
ses valeurs distinctes et vérifie que chaque seuil tombe **entre** deux niveaux, jamais sur
l'un d'eux.

## Et l'interprétation reste démolie, indépendamment du bug

Fable : *« Être près d'une cellule pentue qui expose par géométrie, et y être exposé 73 %
du temps, ce n'est pas un choix — c'est le terrain. »*

Le verdict CHOISIE, même avec le masque réparé, **ne prouve pas un choix**. Le vrai test
serait : *quand une position de rupture de vue existe à une cellule, l'agent s'y déplace-t-il ?*
Non mesuré.
