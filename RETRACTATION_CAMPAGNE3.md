# Rétractation — campagne 3 de l'étage 1 est NULLE

Déposé le 14/08/2026. **Cause : une régression que j'ai introduite, qu'un contrôle
existant n'a pas pu voir.**

## Ce qui s'est passé

Le 13/08 au soir, pour garantir que le bras témoin ne tire pas, j'ai ajouté
`removeAllWeapons _x` au banc d'appui. Le retrait n'était pas défait pour les essais
**natifs** suivants : `setUnitLoadout` rend l'arme au SAC, pas à la MAIN.
`commandSuppressiveFire` sur un homme sans arme en main ne fait rien.

Coups tirés par terrain, bras natif :

| campagne | t0 | t1 | t2 | t3 | t4 | t5 |
|---|---|---|---|---|---|---|
| 1 (avant) | 273 | 393 | 461 | 442 | 114 | 447 |
| 2 (avant) | 324 | 423 | 480 | 449 | 241 | 463 |
| **3 (après)** | **292** | **3** | **1** | **2** | **0** | **3** |

## Le contrôle qui aurait dû l'attraper est passé 9 sur 9

`HMT_PEUT_TIRER` vérifiait `canFire` et `ammo (primaryWeapon)` — **l'arme existe et
elle est chargée**. Jamais `currentWeapon` — **l'arme est en main**.

C'est la faute de la règle 6 : *le contrôle vérifiait l'abstraction commode au lieu de
la propriété que le mécanisme emploie.* Sixième occurrence de cette famille dans la
journée du 14/08 (avec `slope`, `los`, `dcover`, `terrainIntersectASL`, `disableAI PATH`).

## Ce que ça annule

- La campagne 3 (48 essais) est **écartée** — déplacée dans
  `logs/pause_12-08_soir/campagne3_regressee/`. Elle n'a mesuré qu'un terrain sur six.
- **Le « 37,5 % qui tirent sans toucher » que j'ai rapporté à Fable est FAUX.** La
  moyenne de 46 coups cachait 292 coups sur un terrain et zéro à trois sur cinq autres.
  Les balles ne ratent pas les murets : **elles ne partent pas**. Il n'y a donc pas deux
  pannes de nature différente à séparer — il y a une régression.
- Le capteur d'impact reste **prouvé** (sonde à distance connue : 71/62/35/43 % de
  30 à 120 m). Ce résultat-là tient, il a été mesuré indépendamment.

## Ce qui est réparé

1. `_x selectWeapon (primaryWeapon _x)` après chaque restauration de tenue.
2. `HMT_PEUT_TIRER` exige désormais `currentWeapon _u != ""`.

Le second point est un **resserrement** du contrôle ⟨règle 13⟩ : il ajoute une condition,
il n'en retire aucune, et il s'applique aux deux bras. Il n'est pas calibré sur un
résultat — il est dérivé du mécanisme (`commandSuppressiveFire` emploie l'arme en main).

## La leçon, en une phrase

**Un contrôle qui ne peut pas échouer pour la bonne raison ne contrôle rien.** Celui-ci
n'avait pas de contrôle positif : personne n'avait jamais vérifié qu'il refusait un homme
désarmé de la manière dont le banc désarme réellement.
