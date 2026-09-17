# Au repli, l'allure rapide tend à mieux exfiltrer, avec ou sans menace, sans que ce soit établi

*17/09/2026 — statut ETABLI — domaine : banc CHACAL*
*Critères pré-enregistrés : `curriculum/CRITERES_CHOIX_17_09.md` (d7f1196, amendements 714f08e, 0b9c15e, bf97862, tous
avant lecture). Mission 307f68a. Lecture : `lire_choix.py CHOIX-P6-17-09`, puis relue après correctif du lecteur
(dbt 1d77a43, voir « Faute »). Sorties : `curriculum/lecture_CHOIX-P6-17-09.txt` (corrigée) et
`curriculum/lecture_CHOIX-P6-17-09_avant_correctif.txt`.*

## Énoncé

Sur 96 épisodes acceptés sur 96 (vignette `d4a6`, délai du porteur 45 s, 2 allures × témoin / menace × 8 mondes × 3),
**l'allure rapide exfiltre plus souvent que l'allure prudente, dans les deux situations** : au moins 6 exfiltrés dans
83 % des épisodes contre 58 % sans menace, 71 % contre 50 % avec. Mais l'écart moyen des deux situations,
+0,229, a un IC [0 ; +0,479] dont la borne basse vaut **exactement 0** : il n'exclut pas 0. La modulation vaut −0,042,
IC [−0,375 ; +0,292]. Classement pré-enregistré : **INDIFFÉRENT, à la limite de DOMINÉ**. L'hypothèse écrite
avant (prudent meilleur sous menace, modulation négative) n'est pas soutenue : le sens va vers « rapide partout ».

## Qualité

| porte | résultat |
|---|---|
| Q1 | 96 acceptés sur 96, aucun refus |
| Q2 | 0 erreur SQF |
| Q3 | tests dbt bloquants à zéro sur la campagne |
| Q4 | 32 cases d'au moins 2 épisodes (toutes à 3) |
| Q5 | menaces de phase 6 dans les 48 épisodes MENACE, aucune dans les 48 TÉMOIN |

## Résultats

| issue | témoin prudent / rapide | menace prudent / rapide | écart moyen | modulation |
|---|---|---|---|---|
| **exfiltration réussie** (primaire) | 0,583 / 0,833 | 0,500 / 0,708 | **+0,229 [0 ; +0,479]** | **−0,042 [−0,375 ; +0,292]** |
| exfiltrés | 4,08 / 5,08 | 4,46 / 4,92 | +0,73 [−0,21 ; +1,60] | −0,54 [−2,54 ; +1,42] |
| vivants en fin de phase | 7,46 / 7,79 | 7,42 / 7,92 | +0,42 [−0,21 ; +1,00] | +0,17 [−1,25 ; +1,54] |
| durée de la phase (s) | 714 / 371 | 1015 / 565 | **−396 [−517 ; −280]** | −107 [−439 ; +206] |

## Ce que cela apprend

1. **Aller vite ne coûte rien de visible au repli** : plus d'exfiltrés, autant ou plus de vivants, et 6 à 7 minutes de
   moins. La prudence allonge l'exposition sans protéger.
2. **La menace de sortie ne renverse pas le choix** : elle coûte environ 8 à 12 points aux deux allures.
3. **Puissance** : avec R = 3, une modulation de moins de ~40 points ne pouvait pas être établie (écrit d'avance).
   L'écart moyen de 23 points est au bord : un doublement de la campagne dirait probablement « dominé ».

## Faute consignée : le lecteur prenait un résidu flottant pour une borne positive

La première lecture a affiché « DOMINÉ ». La borne basse de l'écart moyen valait 1,3877787807814457e-17 : c'est le résidu
d'une somme de moyennes par monde qui vaut exactement 0. Le critère écrit demande un IC qui exclut 0. Correctif : une
borne à moins de 1e-9 de 0 est traitée comme 0 (dbt 1d77a43). P1, P2 et P4 ont des bornes loin de 0 : leurs classements
ne changent pas. Le pilote P5 (lecteur distinct) a des bornes à +0,125 et +0,021 : non touché.

## Falsificateur pré-enregistré

« Si la modulation n'est pas établie, la menace de la phase n'a pas changé la meilleure option à la précision de ce
dispositif, et ce choix ne sert pas encore à apprendre à décider selon la situation. » — **franchi.**
