# VERDICT — le site du banc live passe de (1734, 5391) à (4644, 5652)

Mesuré le 14/08/2026. Critères déposés **avant** dans `DEPOT_CHOIX_SITE.md` (commit
`4247246`). 80 objectifs candidats, 30 points chacun dans le disque de 200 m que le banc
emploie réellement.

## Les portes dures — elles séparent

| porte | franchie par |
|---|---|
| médiane `slope` dans [0,20 ; 0,60] | 79 / 80 |
| pentes exactement nulles < 10 % | 80 / 80 |
| `dcover` jamais trouvé < 25 % | 69 / 80 |
| **les trois ensemble** | **68 / 80** |

Ni zéro ni tous : les deux conditions d'échec déposées sont écartées.

## Le site retenu

```
                        ancien (1734,5391)   NOUVEAU (4644,5652)   gymnase
médiane slope                  0,000               0,362            0,368
pentes exactement nulles      58,3 %               0,0 %              —
dcover médiane                 0,533               0,167            0,035
dcover jamais trouvé          78,3 %               3,3 %              —
```

L'écart de pente au gymnase passe de **0,368 à 0,006**. Le garde-fou de `dcover`, qui
produisait la constante 0,533 en rendant `16/30` faute d'avoir trouvé du couvert, ne se
déclenche plus que dans 3,3 % des cas contre 78,3 %.

## Ce que ça NE corrige pas — déclaré d'avance

`dcover` reste **décalé** : 0,167 au nouveau site contre 0,035 au gymnase. Changer le site
ne le corrige pas, et le seuil n'a **pas** été retouché après avoir vu les candidats — ce
serait étalonner le capteur sur le résultat.

Restent aussi hors plage `apy/S`, `dgy` et `nd` : ce sont la **naissance des hommes** (le
banc les fait naître dans une bande étroite d'un seul côté quand le gymnase les étale) et
la distance à l'ennemi. Le site ne les traite pas.

## Deux aveux de méthode

1. **Je m'apprêtais à réparer deux capteurs qui fonctionnent.** La sonde de terrain les a
   innocentés : sur 400 points de Stratis au hasard, `slope` rend 0,429 de médiane contre
   0,368 au gymnase. Le site était une plaine, pas le capteur un menteur. Même famille que
   le décor déplacé de 200 m à 170 m — corriger la scène au lieu de lire ce qu'elle dit.
2. **Mon dépouillement ne respectait pas ma propre règle déposée.** J'avais codé
   `round(écart, 2)`, qui met 0,004 et 0,006 dans deux paniers, alors que le dépôt dit
   « égalité à 0,01 près ». Il désignait (3690, 4538) — meilleur sur la pente, **cinq fois
   pire** sur `dcover` (16,7 % contre 3,3 %). Corrigé sans toucher au dépôt ; c'est le
   départage écrit d'avance qui a rattrapé la faute.
