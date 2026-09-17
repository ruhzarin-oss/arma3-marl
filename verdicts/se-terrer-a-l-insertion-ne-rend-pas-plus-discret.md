# À l'insertion, se terrer 3 minutes plutôt que partir ne rend pas la phase plus discrète

*17/09/2026 — statut ETABLI — domaine : banc CHACAL*
*Critères pré-enregistrés : `curriculum/CRITERES_CHOIX_17_09.md` (d7f1196, amendements 714f08e, 0b9c15e, bf97862, tous
avant lecture). Mission 307f68a. Lecture : `lire_choix.py CHOIX-P1-17-09`, appliquée une fois. Sortie complète :
`curriculum/lecture_CHOIX-P1-17-09.txt`.*

## Énoncé

Sur 135 épisodes acceptés (2 options × témoin / menace × 8 mondes, au moins 3 par case), **se terrer 3 minutes près de la
zone de poser plutôt que partir aussitôt vers la route ne change pas la discrétion de la phase 1 de façon établie** :
100 % sans menace quelle que soit l'option ; 33 % (partir) contre 43 % (se terrer) avec menace. Modulation +0,092,
IC [−0,033 ; +0,213] : **choix indifférent** à la précision du dispositif. Le sens est celui de l'hypothèse, mais un
effet de plus de 21 points est exclu.

## Qualité

| porte | résultat |
|---|---|
| Q1 | 135 acceptés (143 joués, dont les remplacements du monde 9 ; 8 refus de l'enregistreur) |
| Q2 | 0 erreur SQF |
| Q3 | tests dbt bloquants à zéro sur la campagne |
| Q4 | 32 cases d'au moins 3 épisodes |
| Q5 | menaces de phase 1 dans les 71 épisodes MENACE, aucune dans les 69 TÉMOIN |

## Résultats

| issue | témoin partir / se terrer | menace partir / se terrer | modulation |
|---|---|---|---|
| **phase discrète** (primaire) | 1,000 / 1,000 | 0,333 / 0,425 | **+0,092 [−0,033 ; +0,213]** |
| vivants en fin de phase | 10,00 / 10,00 | 9,40 / 9,30 | −0,10 [−0,50 ; +0,25] |
| durée de la phase (s) | 291 / 291 | 291 / 291 | +0,4 [−0,0 ; +0,9] |

Écart moyen des deux situations sur l'issue primaire : +0,046 [−0,017 ; +0,106] (ni dépendant, ni dominé).
Modulation par monde : 4 : +0,25 ; 5 : −0,25 ; 6 : 0 ; 7 : +0,25 ; 8 : +0,25 ; 9 : +0,23 ; 11 : 0 ; 12 : 0.

## Ce que cela apprend

1. **La menace d'insertion est la plus lourde mesurée cette nuit** : elle fait perdre 58 à 67 points de discrétion, contre
   22 à la route (verdict `attendre-la-patrouille-ne-sert-a-rien`). Le choix d'attente n'en rattrape que 9, sans que ce
   soit établi.
2. **Témoin au plafond, deuxième fois** : sans menace, rien ne se passe en phase 1 (100 %). La modulation se réduit à
   l'écart sous menace ; c'est pourquoi l'IC est plus étroit que prévu : un effet d'environ 12 points aurait suffi à être établi, contre ~35 écrits d'avance. L'écart observé (9 points) reste en dessous.
3. **La durée de la phase ne dépend pas du choix** : les deux options tiennent la même fenêtre de 180 s ; seul change ce
   que font les hommes pendant ce temps (se déplacer de 300 m ou rester couchés). Le choix ne coûte donc pas de temps.
4. **Limite** : le niveau 3 mêle la patrouille et le guetteur. L'inversion prévue par le plan (se terrer face à une
   patrouille, partir face à un guetteur fixe) n'est pas testée ; ce serait la comparaison à faire, entre types de menace.

## Falsificateur pré-enregistré

« Si la modulation n'est pas établie, la menace de la phase n'a pas changé la meilleure option à la précision de ce
dispositif, et ce choix ne sert pas encore à apprendre à décider selon la situation. » — **franchi.**
