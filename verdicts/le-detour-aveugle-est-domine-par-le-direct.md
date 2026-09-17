# À la mise en place, le détour aveugle de 350 m est dominé par l'itinéraire direct

*17/09/2026 — statut ETABLI — domaine : banc CHACAL*
*Critères pré-enregistrés : `curriculum/CRITERES_CHOIX_17_09.md` (d7f1196, amendements 714f08e, 0b9c15e, bf97862, tous
avant lecture). Mission 307f68a. Lecture : `lire_choix.py CHOIX-P4-17-09`, appliquée une fois. Sortie complète :
`curriculum/lecture_CHOIX-P4-17-09.txt`.*

## Énoncé

Sur 133 épisodes acceptés (vignette `d3 obs0 a4`, 2 options × témoin / menace × 8 mondes), **l'itinéraire direct vaut
mieux que le détour de 350 m dans les deux situations** : mise en place propre 62,5 % contre 25,0 % sans menace, 9,4 %
contre 0 % avec. Écart moyen des deux situations −0,234, IC [−0,406 ; −0,078] ; modulation +0,281, IC [−0,062 ;
+0,625], non établie. Classement pré-enregistré : **DOMINÉ**. Ce n'est pas une décision qui dépend de la situation.

## Qualité

| porte | résultat |
|---|---|
| Q1 | 133 acceptés (138 joués, dont les remplacements du monde 9 ; 5 refus de l'enregistreur) |
| Q2 | 0 erreur SQF |
| Q3 | tests dbt bloquants à zéro sur la campagne ; 3 lignes `choix_joue` par épisode (une par élément) |
| Q4 | 32 cases d'au moins 3 épisodes |
| Q5 | menaces de phase 4 dans les 74 épisodes MENACE, aucune dans les 64 TÉMOIN |

## Résultats

| issue | témoin direct / détour | menace direct / détour | modulation |
|---|---|---|---|
| **mise en place propre** (primaire) | 0,625 / 0,250 | 0,094 / 0,000 | **+0,281 [−0,062 ; +0,625]** |
| écart détour − direct | −0,375 [−0,688 ; −0,062] | −0,094 [−0,219 ; 0,000] | |
| vivants en fin de phase | 10,00 / 9,91 | 9,59 / 9,73 | +0,23 [−0,17 ; +0,66] |
| durée de la phase (s) | 354 / 342 | 249 / 267 | +31 [−33 ; +95] |

## Pourquoi : lecture des causes écrites par le script (descriptive, après la lecture pré-enregistrée)

Issue de la phase 4 par case (épisodes acceptés) :

| case | ATTEINT sans compromission | compromis | durée moyenne jusqu'à ATTEINT propre |
|---|---|---|---|
| témoin, direct | 21 / 32 | 11 / 32 | 390 s |
| témoin, détour | 9 / 32 | 23 / 32 | 499 s |
| menace, direct | 5 / 33 | 28 / 33 | — |
| menace, détour | 1 / 36 | 35 / 36 | — |

1. **Sans menace ajoutée, le détour est compromis deux fois plus souvent** (72 % contre 34 %) : les défenseurs du site
   suffisent. Le détour allonge la marche d'environ 110 s et la fait passer ailleurs que l'axe, sans savoir où sont
   les défenseurs.
2. **Avec la menace de niveau 3, la phase 4 est presque impossible** : 85 à 97 % de compromission quelle que soit
   l'option. Le bras menace est au **plancher** ; la modulation positive vient surtout de ce que le direct n'a plus
   rien à perdre. C'est l'inverse des phases 1 et 2 (témoin au plafond), avec la même conséquence : une des deux
   situations ne départage rien.
3. **Limite** : le détour est **aveugle** (350 m à droite de l'axe à mi-chemin, à gauche si l'eau l'impose), pas choisi
   loin de la menace. Un détour qui s'écarte du danger connu n'est pas testé ici.

## Falsificateur pré-enregistré

« Si la modulation n'est pas établie, la menace de la phase n'a pas changé la meilleure option à la précision de ce
dispositif, et ce choix ne sert pas encore à apprendre à décider selon la situation. » — **franchi.** Le choix est
dominé : le direct vaut mieux partout.
