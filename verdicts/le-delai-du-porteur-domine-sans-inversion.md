# Le délai de 180 s domine avec ou sans menace : la situation ne l'inverse pas

*16/09/2026 — statut ETABLI — domaine : banc CHACAL*
*Critères pré-enregistrés : `curriculum/CRITERES_PILOTE_P5.md` (4bcbdd6). Lecture : `C:\hmt\dbt\outils\lire_pilote_p5.py`
(dbt fb69b5a), appliquée une seule fois après la fin de la campagne. Plan : `plans/plan-choix-par-vignette.md`.*

## Énoncé

Sur 192 épisodes appariés (8 mondes × 2 bras × 2 délais × 6), laisser **180 s au porteur au lieu de 45** rend l'assaut
utile (3 charges et au moins 6 vivants) **nettement plus souvent sans menace (+33,3 points, IC [+12,5 ; +54,2])** et
**encore avec menace (+14,6 points, IC [+2,1 ; +27,1])**. L'avantage diminue sous menace (modulation −18,8 points), mais
son IC [−37,5 ; +2,1] touche zéro : **la modulation n'est pas établie**, et il n'y a **pas d'inversion**. Selon la règle
écrite d'avance, le choix n'entre pas au curriculum comme décision dépendant de la situation.

## Qualité (avant toute lecture d'effet)

| porte | résultat |
|---|---|
| Q1 épisodes acceptés | **192 sur 192** |
| Q2 erreurs SQF | **0** |
| Q3 tests dbt bloquants (décision présente et unique, choix conforme, choix exécuté, alarme lue après la pose, conséquence avant l'arrêt, zéro erreur) | **tous à zéro** |
| Q4 cases (monde, bras, délai) d'au moins 4 épisodes | **32 cases pleines (6 chacune)** |
| Q5 alarme au moment du choix | **MENACE 96/96, TÉMOIN 0/96** |

## Issue primaire : assaut utile

| bras | 45 s | 180 s | écart 180 − 45 (IC 95 %, mondes rééchantillonnés) |
|---|---|---|---|
| TÉMOIN | 0,479 (23/48) | 0,812 (39/48) | **+0,333 [+0,125 ; +0,542]** |
| MENACE | 0,438 (21/48) | 0,583 (28/48) | **+0,146 [+0,021 ; +0,271]** |
| **modulation** (menace − témoin) | | | **−0,188 [−0,375 ; +0,021]** |

Modulation par monde : 4 : −0,50 · 5 : 0 · 6 : −0,50 · 7 : −0,17 · 8 : +0,33 · 9 : 0 · 11 : −0,33 · 12 : −0,33
(5 négatives, 2 nulles, 1 positive).

| critère écrit avant | résultat |
|---|---|
| C1 effet dans le témoin (informatif) | +0,333, établi |
| **C2 modulation établie** | **NON** (borne haute +0,021) |
| C3 inversion | NON : 180 s gagne dans les deux situations |
| sens conforme à l'hypothèse | OUI : l'avantage de 180 s diminue sous menace |

## Issues secondaires (descriptives)

| issue | TÉMOIN 45 / 180 | MENACE 45 / 180 | modulation |
|---|---|---|---|
| 3 charges | 0,479 / 0,833 | 0,458 / 0,583 | −0,229 [−0,438 ; +0,000] |
| charges (0-3) | 2,25 / 2,71 | 2,13 / 2,31 | −0,27 [−0,73 ; +0,21] |
| tués en phase 5 | 2,21 / 2,08 | 3,13 / 2,83 | −0,17 [−0,88 ; +0,46] |
| vivants | 7,79 / 7,92 | 6,88 / 7,17 | +0,17 [−0,46 ; +0,88] |

La menace coûte environ un homme de plus par assaut ; **180 s ne coûte pas d'hommes**, ni avec ni sans menace.
L'hypothèse « rester 3 minutes sous l'alarme coûte des hommes » n'est pas observée.

## Ce que cela apprend

1. **Le délai du porteur est maintenant établi sur l'assaut**, dans une campagne entrelacée et appariée par monde :
   +33 points d'assaut utile sans menace. Le verdict `delai-porteur-le-mecanisme-tient-pas-le-resultat` (AMENDE)
   laissait l'effet sur l'issue non démontré ; il l'est ici pour l'assaut (la mission entière reste à mesurer).
2. **Un choix peut ne rien apprendre de deux façons.** La porte est *indifférente* ; le délai est *dominé* : 180 s
   gagne partout. Dans les deux cas, l'agent n'apprend pas à décider selon la situation. Le plan ne connaissait que
   le premier cas ; la catégorie « option dominante » est ajoutée.
3. **Pour le script actuel, la conclusion pratique est simple** : 180 s vaut mieux que 45 s dans toutes les situations
   testées.
4. **La modulation de −19 points est plausible mais non établie** ; les critères prévoyaient qu'en dessous de ~30 points
   ce dispositif ne pourrait pas conclure. Doubler la campagne (384 épisodes) resserrerait l'IC d'environ un tiers :
   c'est une décision à prendre, pas une suite automatique.

## Falsificateur pré-enregistré

« Si C2 n'est pas établie, la menace de phase 5 n'a pas changé le meilleur délai du porteur à la précision de ce
dispositif, et le choix ne sert pas encore à apprendre à décider selon la situation. » — **franchi.**

## Données

PILOTE-P5-DELAI-SITUATION-16-09 : 32 jobs, 192 épisodes, 20:32 → vers 23:05. Fumée préalable FUMEE-DECISION-P5-16-09 :
4 épisodes, 10 attentes tenues. Sortie complète : `curriculum/lecture_pilote_p5.txt`.
