# VERDICT — la politique NE TRANSFÈRE PAS. 0/20 sur Arma contre 59,4 % au gymnase.

Mesuré le 15/08/2026. Critères déposés dans `DEPOT_20_EPISODES.md` (`53bcc51`), repris à
l'identique après la relance justifiée dans `NOTE_RELANCE_20.md` (`4c7a12a`).
Seconde série : 20 épisodes, 4 contre 4, site apparié, `dcover` étalonné.

## LA PORTE TIENT, CETTE FOIS

```
colonnes dont la mediane sort de la plage du gymnase : 0 / 12
dcover : mediane 0,100 dans [0,000 ; 0,131]   (serie 1 : 0,133, HORS)
```

C'est la différence avec la première série, et c'est la seule chose qui a changé entre les
deux. **La mesure rend donc un verdict.**

## LE RÉSULTAT

| | Arma | gymnase |
|---|---|---|
| **prise** | **0 / 20 = 0,0 %** | **59,4 %** |
| tous morts | 9 / 20 | — |
| 60 pas sans prendre | 11 / 20 | — |

L'étalonnage de `dcover` a nettement amélioré la **survie** — 11 épisodes complets contre 4
dans la série 1. **Il n'a rien changé à la prise : elle reste à zéro.**

**Le gymnase entraîne une politique qui prend l'objectif six fois sur dix. Sur Arma, dans
le même monde nominal, elle ne le prend jamais.**

## Ce que ce verdict a coûté pour être propre

Réparées avant de pouvoir le rendre : les trois coutures du pont (`checkVisibility`,
gradient, dcover en cellules), le **site** (l'ancien était une plaine, 58 % de pentes
nulles), le **rapport de force** (le banc jouait 8 contre 13 quand le gymnase entraîne
4 contre 4), et **`dcover`** (seuil global au lieu de la moyenne locale, quatrième fois
que cette colonne était fausse).

Sans ces quatre réparations, un 0 % aurait été inlisible — on n'aurait pas su s'il jugeait
la politique ou le banc.

## Le gel — INDÉCIS, et on n'y revient pas

**8 épisodes figés sur 20.** La bande déposée était 4-17. **On ne conclut pas, et on ne
rejoue pas** — la bande a été écrite pour être respectée. Médiane de 2 actions distinctes
par épisode contre 5 au gymnase : l'écart existe, il n'est pas jugé.

## Un aveu — mon contrôle d'azimut est mal codé, pour la troisième fois de la journée

Le script exige **≥ 18 azimuts distincts à 5° près** ; il en trouve 16 et déclare TOMBE.
**Cette porte est mal posée, et démontrable sans regarder les données** : 20 tirages
uniformes dans 72 casiers de 5° donnent ~2,6 collisions attendues (problème des
anniversaires). Exiger ≥ 18 distincts échoue sur la majorité des séries valides.

Le critère **déposé** disait : *« si les 20 épisodes partagent un azimut, je n'ai pas
20 épisodes, j'ai 20 copies du même »*. Écart-type 103°, aucune répétition systématique :
**le critère déposé est satisfait.** C'est mon implémentation qui est fausse, pas la série.

Troisième fois aujourd'hui que mon code est plus strict — ou plus laxe — que mon dépôt,
après l'arrondi du choix de site et le critère insatisfiable de `dcover`.

## Ce que ce verdict NE dit PAS

- Il ne dit pas que le gymnase ne vaut rien. Il dit que **le transfert n'est pas établi**.
- Il ne dit pas où est la faute restante. Les colonnes sont dans leur plage, la plomberie
  est fidèle, le monde correspond. **Ce qui reste est le corps** : dix actions qui ne
  mordent pas sur Arma comme elles mordent au gymnase — hypothèse non testée.
- À n=20, l'intervalle sur une proportion nulle est [0 ; 0,17]. On sait que ce n'est pas
  59 %. On ne sait pas si c'est 0 ou 10 %.

## Conséquence directe

**Le 51,1 % / 57,7 % / 59,4 % ne peut être cité comme transféré. C'est désormais mesuré,
plus seulement interdit par prudence.**
