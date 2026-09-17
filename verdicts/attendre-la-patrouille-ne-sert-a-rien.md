# À la route, attendre la patrouille ne rend pas la traversée plus discrète

*17/09/2026 — statut ETABLI — domaine : banc CHACAL*
*Critères pré-enregistrés : `curriculum/CRITERES_CHOIX_17_09.md` (d7f1196, amendements 714f08e, 0b9c15e, bf97862, tous
avant lecture). Mission 307f68a. Lecture : `lire_choix.py CHOIX-P2-17-09`, appliquée une fois. Sortie complète :
`curriculum/lecture_CHOIX-P2-17-09.txt`.*

## Énoncé

Sur 128 épisodes acceptés (2 options × témoin / menace × 8 mondes × 4), **attendre d'avoir vu passer la patrouille
avant de traverser ne change pas la discrétion de la traversée** : 100 % de phases discrètes sans menace quelle que soit
l'option, 77 % (tout de suite) contre 78 % (attendre) avec menace. Modulation +0,010, IC [−0,250 ; +0,281] : **choix
indifférent** à la précision du dispositif. Attendre coûte du temps : +265 s sans menace, IC [+168 ; +371], +141 s avec,
IC [+3 ; +292].

## Qualité

| porte | résultat |
|---|---|
| Q1 | 128 acceptés pour 128 prévus (148 joués, dont 20 remplacements et refus de l'enregistreur) |
| Q2 | 0 erreur SQF |
| Q3 | tests dbt bloquants à zéro |
| Q4 | 32 cases d'au moins 3 épisodes (monde 9 complété par remplacement, amendement 2) |
| Q5 | menaces de phase 2 dans les 74 épisodes MENACE, aucune dans les 74 TÉMOIN |

## Résultats

| issue | témoin tout de suite / attendre | menace tout de suite / attendre | modulation |
|---|---|---|---|
| **phase discrète** (primaire) | 1,000 / 1,000 | 0,771 / 0,781 | **+0,010 [−0,250 ; +0,281]** |
| vivants en fin de phase | 10,00 / 10,00 | 9,83 / 9,91 | +0,07 [−0,03 ; +0,17] |
| durée de la phase (s) | 443 / 709 | 647 / 788 | −124 [−254 ; +15] |

Écart moyen des deux situations sur l'issue primaire : +0,005 [−0,125 ; +0,141] (ni dépendant, ni dominé).

## Ce que cela apprend

1. **Sans menace, rien ne se passe à la route** (100 % discret) : le témoin est au plafond. Une modulation ne pouvait
   venir que du bras menace, et l'attente n'y change rien.
2. **La menace coûte 22 points de discrétion quelle que soit l'option** : le blindé de patrouille et le poste de contrôle
   repèrent le détachement autant quand il attend que quand il traverse aussitôt.
3. **Attendre est un coût sans bénéfice mesuré** : 2 à 4 minutes de plus. Sur l'issue primaire, le choix est indifférent ;
   sur le temps, « tout de suite » vaut mieux. Tant que le temps ne coûte rien avant l'alarme, un agent ne peut pas
   l'apprendre de l'issue primaire.
4. **Limite** : le niveau 3 mêle deux menaces (patrouille qui roule et poste fixe). L'inversion prévue par le plan
   (attendre face à une patrouille, pas face à un poste) n'est pas testée ici.

## Fautes consignées pendant la campagne

- **Extracteur dbt (corrigé, dbt ac37b87)** : l'expression exigeait une heure à deux chiffres ; tout épisode lancé avant
  10 h était extrait sans aucune ligne, sans erreur. Attrapé par `situation_conforme_au_job` sur la fumée ; aucun
  résultat passé touché (toutes les campagnes lues avant ont tourné après 10 h).
- **Canari du monde 9 (ouverte)** : le témoin du canari l'abat parfois après ses premiers tirs ; le contrôle de
  l'enregistreur refuse l'épisode. 20 refus sur 148 épisodes dans cette campagne, tous dans le monde 9, aucun lié au choix.

## Falsificateur pré-enregistré

« Si la modulation n'est pas établie, la menace de la phase n'a pas changé la meilleure option à la précision de ce
dispositif, et ce choix ne sert pas encore à apprendre à décider selon la situation. » — **franchi.**
