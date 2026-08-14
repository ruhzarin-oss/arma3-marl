# Règle 16 — les instruments passent la même porte que les mesures

Amendement de Fable, 14/08/2026, après **six occurrences en une seule journée** du même
défaut. Énoncé sans référence à un résultat ⟨règle 13⟩ : il ne fait que resserrer, et il
s'applique symétriquement à tous les bras et à tous les bancs.

## Le constat

La règle « une mesure doit savoir échouer » existait. Elle ne s'appliquait qu'aux
**mesures**, jamais aux **instruments**. Le 14/08, six sondes ont menti :

| sonde | ce qu'elle vérifiait | ce que le mécanisme emploie |
|---|---|---|
| `slope` | `surfaceNormal`, borné à 0,40 | le gradient réel, médiane 0,589 |
| `los` | `terrainIntersectASL` — relief SEUL | la géométrie complète, objets compris |
| `dcover` | distance aux bâtiments, en mètres | couvert de terrain, en cellules |
| `disableAI "PATH"` | (recopié d'un autre banc) | retirait les jambes : 9 m au lieu de 48 |
| `HMT_PEUT_TIRER` | `canFire` + munitions en inventaire | l'arme **en main** — passait 9/9 à vide |
| sonde `vue` | (posée sans contrôle positif) | lisait **0 sous 347 coups** |

## Clause 1 — contrôle positif obligatoire pour toute sonde

**Aucune lecture d'instrument n'est admissible avant que l'instrument ait été posé sur un
cas où le phénomène est connu massif, et qu'il l'y ait lu.**

La sonde `vue` affichant 0 là où 347 coups partaient aurait été rejetée en cinq minutes
par cette porte, au lieu de contaminer une soirée.

## Clause 2 — juger l'ACTE, pas l'ÉTAT

`HMT_PEUT_TIRER` interrogeait des **drapeaux** (`canFire`, inventaire). Le phénomène est
un **événement** : `Fired`, `HitPart`. Les six échecs interrogeaient un état commode ;
le moteur, lui, produit des actes.

**L'instrument ultime est toujours l'événement que le mécanisme émet.** Quand un
événement existe, une sonde qui interroge un état à sa place doit se justifier par écrit.

## Portée

S'applique à tout capteur de tout banc, sandbox et Arma, à compter du 14/08/2026.
Rétroactivement : toute sonde déjà en service qui n'a pas de contrôle positif déposé est
**suspecte** — ses lectures tiennent, mais un résultat qui en dépend seul ne peut pas
être certifié tant que le contrôle positif n'est pas fait.
