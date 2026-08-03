# RÉFÉRENCE FIGÉE — CÔNE DUR, GÉOMÉTRIE OÙ L'ARC EXISTE

## Pourquoi elle a dû être refaite

`reverdict_arc2` ne fixait pas `def_arc` : il prenait le défaut, un demi-angle de 180°.
Le cône couvrait le cercle entier — **aucun angle mort**, donc le flanc ne pouvait pas être
dehors. On mesurait un arc en testant l'absence d'arc.

`reverdict_arc3` pose un cône de 120° (`def_arc=pi/3`) et une géométrie fixe
(`def_rand=False`). En corrigeant ça, le témoin a cessé d'être comparable à l'ancienne
référence (19,3 % / 74,7 %). La contre-épreuve a échoué et les critères ont refusé de
conclure — c'était leur travail.

## La référence

Mesurée par `faire_reference_arc3.py`, **cône dur seul**, sur des graines
**volontairement différentes** de celles du re-verdict (11-16 contre 7,8,9) : reproduire
une référence sur ses propres graines ne prouverait rien.

| | prise | écart-type entre graines |
|---|---|---|
| frontal | **22,2 %** | 0,5 pt |
| crochet | **40,4 %** | 0,7 pt |

6 graines × 2048 épisodes. A=4, D=8, `def_arc=pi/3`, `def_rand=False`.

**Tolérance : ±5,0 points.** Trois écarts-types entre graines, plancher à 5 points. Elle
n'est pas choisie : elle est lue sur la dispersion que le monde produit tout seul.

## Ce qu'elle sert à faire

La contre-épreuve du re-verdict. Si le cône dur d'un run futur sort de cette bande, le
harnais a dérivé et **on ne conclut rien**, quel que soit le reste du run.

## Ce qu'elle n'autorise pas

Elle ne remplace aucun verdict Arma. La référence Arma « ×2-3 à un tiers du coût » reste
**non comparable** : sa garnison n'existe plus. On juge une NON-RÉGRESSION interne.
