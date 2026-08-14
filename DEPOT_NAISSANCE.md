# Dépôt — étaler la naissance des attaquants, critères écrits AVANT

Déposé le 14/08/2026, avant toute mesure.

## L'écart, mesuré

Les huit hommes du banc sont **2,3 fois plus serrés** que ceux du gymnase (étalement 0,069
contre 0,160 — écart-type moyen entre camarades, au même pas). Le code dit pourquoi :

```python
# GYMNASE — assault_terrain.py:316, deux axes
apx = sx + (ar % 2) * 6 - 3          # deux files, ±3 m
apy = sy + (ar - 1) * 6              # 6 m d'intervalle, sur 42 m
```
```sqf
// BANC — un seul axe
_p = [OBJ.x + DIST*sin _az + (_i * 6), OBJ.y + DIST*cos _az, 0];
```

**`apy` est identique pour les huit hommes du banc : variance rigoureusement nulle sur une
coordonnée entière.**

## Ce qu'on fait

**On recopie la formule du gymnase, à l'identique**, avec `ar = _i - 1` pour aligner
l'indice SQF (1..8) sur l'indice torch (0..7) :

```sqf
_p = [OBJ.x + DIST*sin _az + (((_i - 1) mod 2) * 6 - 3),
      OBJ.y + DIST*cos _az + ((_i - 2) * 6), 0];
```

Ce n'est pas un réglage, c'est **le même monde** — même principe que le passage à 170 m,
qui reprenait `R_spawn` du gymnase au lieu d'inventer une distance.

## CONTRÔLE POSITIF ⟨règle 16 clause 1⟩

**Les huit hommes ne doivent plus partager un `apy` identique.** Si la variance de `apy`
entre camarades reste nulle au premier pas, la greffe n'a pas mordu et **rien ne se lit**.

## La porte, sur le MÉCANISME

**L'étalement doit dépasser 0,12** (il est à 0,069 ; le gymnase est à 0,160). C'est la
grandeur que la réparation contrôle directement.

## Ce qui est RAPPORTÉ mais ne juge PAS

Le nombre d'actions distinctes émises sur Arma. C'est ce que l'étalement est censé
acheter — donc c'est un **résultat**, pas un contrôle. L'écrire comme une porte reviendrait
à déclarer la réparation bonne parce qu'elle donne ce que j'espère.

## Ce qui restera non traité

Les hommes meurent au pas 14. **L'étalement ne corrige pas ça**, et aucune campagne de
répétitions ne vaut tant que c'est vrai — quatorze pas ne laissent aucune décision se
déployer. C'est le chantier suivant, pas celui-ci.
