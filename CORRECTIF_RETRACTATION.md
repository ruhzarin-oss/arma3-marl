# Correctif à RETRACTATION_CAMPAGNE3.md — la cause accusée était FAUSSE

Déposé le 14/08/2026, quelques heures après la rétractation elle-même.

## Ce que j'avais écrit

Que `removeAllWeapons` posé au bras témoin le 13/08 n'était pas défait pour les essais
natifs, et que c'était la cause du tir limité au terrain 0.

## Ce que la mesure dit

J'ai posé `selectWeapon` après chaque restauration de tenue, relancé une campagne
complète, et **la forme est inchangée** :

| | t0 | t1 | t2 | t3 | t4 | t5 |
|---|---|---|---|---|---|---|
| campagne 3 (avant correctif) | 292 | 3 | 1 | 2 | 0 | 3 |
| **campagne 4 (après correctif)** | **347** | **3** | **3** | **4** | **0** | **3** |

**`removeAllWeapons` n'était pas la cause.** Deuxième diagnostic faux de la journée sur
ce banc, après « le capteur d'impact est aveugle » (réfuté par la sonde à distance
connue : 71 % à 30 m, 62 % à 60, 35 % à 90, 43 % à 120).

## Ce qui tient malgré tout

- **La campagne 3 reste écartée** — mais parce qu'elle partage le défaut de la 4, pas
  à cause de ma régression.
- Les deux réparations posées (`selectWeapon`, et `currentWeapon` exigé dans
  `HMT_PEUT_TIRER`) **restent** : elles corrigent un contrôle qui était réellement
  incapable de voir un homme désarmé. Elles n'ont simplement pas résolu la panne.
- Le capteur d'impact reste prouvé.

## Ce que ça ajoute au motif

Le motif du jour n'est pas « un contrôle était faux ». C'est que **j'ai réfuté deux
hypothèses au tarif d'une campagne pièce**. Fable : *« Le défaut n'était pas ton
jugement, c'était le tarif. »* La suite se fait à 6 essais, pas à 36.
