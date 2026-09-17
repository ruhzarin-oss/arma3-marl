# Observer 8 minutes plutôt que 2 domine, et paie davantage sous menace, à la limite de l'établi

*17/09/2026 — statut ETABLI — domaine : banc CHACAL*
*Critères pré-enregistrés : `curriculum/CRITERES_CHOIX_17_09.md` (d7f1196, amendements 714f08e, 0b9c15e, bf97862, tous
avant lecture). Mission 307f68a. Lecture : `lire_choix.py CHOIX-P3-17-09` (avec la tolérance de 1e-9 sur les bornes,
dbt 1d77a43, corrigée avant cette lecture). Sortie : `curriculum/lecture_CHOIX-P3-17-09.txt`.*

## Énoncé

**La campagne.** 109 épisodes acceptés sur 116 joués, remplacements du monde 9 compris. Vignette `d3 obs1 a3`, 2 durées
× témoin / menace × 8 mondes.
- **Observer 8 minutes localise plus souvent un défenseur sans être repéré, dans les deux situations.**
  - Sans menace : 29,2 % contre 20,8 %.
  - Avec la patrouille de crête : 50,0 % contre 12,5 %.
  - Écart moyen : +0,229, IC [+0,042 ; +0,438]. Classement pré-enregistré : **DOMINÉ**, 8 minutes valent mieux partout.
- **Le gain est bien plus grand sous menace** : +0,375, IC [+0,042 ; +0,708], contre +0,083, IC [0 ; +0,208].
  - Modulation : +0,292, IC [0 ; +0,583]. La borne basse vaut exactement 0 : **non établie, à la limite**.
- **L'hypothèse écrite avant est réfutée dans son sens.** On attendait qu'une patrouille de crête rende la longue
  observation dangereuse (modulation négative). C'est l'inverse : sous menace, observer 2 minutes ne localise presque
  rien.

## Qualité

| porte | résultat |
|---|---|
| Q1 | 109 acceptés sur 116 joués (prévus 96 ; 7 refus de l'enregistreur, remplacés) |
| Q2 | 0 erreur SQF |
| Q3 | tests dbt bloquants à zéro sur la campagne |
| Q4 | 32 cases d'au moins 2 épisodes |
| Q5 | menaces de phase 3 dans les 63 épisodes MENACE, aucune dans les 53 TÉMOIN |

## Résultats

| issue | témoin 2 min / 8 min | menace 2 min / 8 min | écart moyen | modulation |
|---|---|---|---|---|
| **observation utile** (primaire) | 0,208 / 0,292 | 0,125 / 0,500 | **+0,229 [+0,042 ; +0,438]** | **+0,292 [0 ; +0,583]** |
| défenseurs localisés (renseignement) | 0,29 / 0,33 | 0,58 / 1,11 | +0,29 [−0,07 ; +0,63] | +0,49 [−0,12 ; +1,04] |
| phase discrète | 1,000 / 1,000 | 0,750 / 0,792 | +0,02 [−0,06 ; +0,13] | +0,04 [−0,13 ; +0,25] |
| vivants en fin de phase | 10,00 / 10,00 | 9,96 / 9,90 | −0,03 [−0,13 ; +0,05] | −0,06 [−0,27 ; +0,11] |
| durée de la phase (s) | 307 / 661 | 363 / 699 | +345 [+320 ; +367] | −18 [−74 ; +34] |

## Ce que cela apprend

1. **C'est le premier choix où la situation semble peser sur l'avantage**, pas seulement sur le niveau. La modulation
   (+29 points) est la plus grande des six choix, mais le dispositif (R = 3) ne pouvait établir que ~40 points
   (écrit d'avance).
2. **Observer plus longtemps ne coûte pas d'hommes** et ne compromet pas davantage : phase discrète et vivants restent
   stables. Le coût est le temps : 6 minutes de plus.
3. **Sous menace, 2 minutes ne suffisent presque jamais** (12,5 %) : la patrouille de crête gêne l'observation courte
   plus que la longue.
4. **Pour la suite** : P3 est le meilleur candidat pour une campagne plus puissante (doubler R) et pour la perception
   de la menace (`plans/plan-menace-visible.md`).

## Falsificateur pré-enregistré

« Si la modulation n'est pas établie, la menace de la phase n'a pas changé la meilleure option à la précision de ce
dispositif, et ce choix ne sert pas encore à apprendre à décider selon la situation. » — **franchi**, de justesse : la
borne basse est à 0.
