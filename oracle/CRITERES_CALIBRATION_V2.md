# Calibrer l'adversaire en phase 2, deuxième essai — critères écrits avant le premier épisode

*21/09/2026, campagne `CALIBRATION-P2-V2-21-09`. Reprend `CRITERES_CALIBRATION.md` (commit 3c7302b), dont la
lecture de δ n'a pas conclu pour une faute de conception : l'option était **confondue avec la situation**, le
mélange chargé en cases où le monde punit déjà seul (témoin à 0,258 contre 0,082 sur ORACLE-P2), et le bras de
référence n'a pas reproduit ses propres +0,197 (il a donné +0,009). Le contrôle négatif, lui, est soldé : il n'est
pas rejoué.*

## Les trois corrections

1. **Option fixée : *traverser tout de suite*** (`traversee = 1`). Plus de confusion avec la situation. C'est
   aussi l'option où le témoin punit le moins (0,065 sur ORACLE-P2) : celle qui laisse le plus de place pour voir
   l'Oracle. Conséquence assumée : la calibration vaut **pour cette option**.
2. **Trois bras** : **T** témoin (`oracle_cmd = 0`), **R** référence (B 6, δ 60 s), **F** fréquent (B 6, δ 30 s).
3. **Seize mondes au lieu de huit** : les 8 connus (4, 5, 6, 7, 8, 9, 11, 12) et **8 neufs**. Avec 64 épisodes par
   bras l'IC d'une différence descend vers ±0,16, contre ±0,23 la dernière fois.

3 bras × 16 mondes × 4 situations = **192 épisodes**, 96 jobs de deux graines, bras entrelacés. L'issue est lue sur
la ligne de fin de phase 2, qui existe que le détachement ait atteint la décision ou non : **l'intention de
traiter est donc incluse dès le départ**, un épisode compromis avant la décision compte comme compromis.

## Le choix des mondes neufs — règle fixée avant de les voir

Les graines 13 à 31 n'ont jamais été jouées sur aucun banc CHACAL. On prend **les 8 premières, dans l'ordre
croissant à partir de 13, qui passent un test de validité** : un épisode du bras R, situation 1, qui doit être
**accepté par le banc**, **non VOID**, **atteindre la fin de phase 2**, et porter la **ligne de carte**.

Ce test ne regarde **aucune issue** : ni compromission, ni réussite. Ses épisodes forment la campagne
`VALIDITE-GRAINES-21-09`, qui ne sera jamais lue pour un effet.

## Portes de qualité, avant toute lecture

- **K1** zéro erreur SQF.
- **K2** aucune case (bras, monde, situation) sans résultat — 192 cases. Une case vide se répare par rejeu.
- **K3** au moins **48 épisodes valides par bras** sur 64.
- **K4** la ligne `CHACAL|O|carte` présente dans tous les épisodes à Oracle monté.
- **K5** l'option jouée est bien *traverser* : `traversee = 1` dans tous les jobs, et `choix_joue = 1` dans tous
  les épisodes qui ont atteint la décision.
- **K6** la période relue dans le journal est celle du job (±8 s).
- **K7 — sensibilité, la porte qui m'a manqué la dernière fois :** le bras de référence doit se reproduire.
  **R doit compromettre au moins 10 points de plus que T, et l'IC 95 % de cet écart doit exclure zéro.** Sinon la
  campagne n'a pas la sensibilité voulue, **δ n'est pas lu**, et on le dit.

Lecture : premier épisode **accepté** de chaque (bras, monde, situation). IC par 10 000 rééchantillonnages
appariés par monde, graine 20260921.

## Les deux lectures

### L2 — la période de décision (lue seulement si K7 passe)

Réussite et compromission des trois bras. **Règle de décision :** on retient le δ dont la réussite est la plus
proche de 0,50, borne haute de l'IC de son écart au témoin inférieure à 0. **Falsificateur :** si F ne gagne pas au
moins **5 points** de compromission sur R, la période n'est pas le levier.

### L3 — la route prédit-elle la prise ? Validation sur les 8 mondes neufs

Sur les 8 mondes connus, 7 cases atteignables donnaient 0,42 de compromission, 4 ou 5 cases 0,15. Ce seuil a été
**vu** sur ces mondes-là ; il ne prouve rien tant qu'il n'a pas trié des mondes neufs.

- Classe **haute prise** : `cases_routieres ≥ 6` ; **basse prise** : `≤ 5`. La classe d'un monde est lue sur la
  ligne de carte, posée à la mise en place, **avant que rien ne bouge**.
- Mesure : l'**apport de l'Oracle** par monde, compromission moyenne de R et F moins celle de T.
- **Prédiction :** sur les mondes neufs, l'apport moyen des mondes à haute prise dépasse celui des mondes à basse
  prise d'au moins **10 points**.
- Si l'une des deux classes compte **moins de 2 mondes neufs**, la validation est déclarée **non évaluable** — pas
  réussie.
- Les prédictions **monde par monde** seront écrites dans ce fichier après le test de validité (qui révèle la carte)
  et **avant** le premier épisode de la campagne.

*Avec 8 mondes, aucune prétention statistique n'est faite sur L3 : c'est une prédiction directionnelle, écrite
d'avance, qui peut échouer.*

## Mondes neufs retenus et prédictions — écrit le 21/09 après le test de validité, **avant le premier épisode**

Les 12 graines testées (13 à 24) sont toutes valides : acceptées, non VOID, fin de phase 2 atteinte, ligne de carte
présente. La règle retient les 8 premières : **13, 14, 15, 16, 17, 18, 19, 20**. Aucune issue n'a été lue.

Leur carte, lue à la mise en place :

| graine | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|
| cases atteignables | 8 | 7 | 8 | 8 | 6 | **5** | 8 | 7 |
| classe | haute | haute | haute | haute | haute | **basse** | haute | haute |

**Conséquence que je dois annoncer maintenant, pas après :** la classe basse ne compte qu'**un seul** monde neuf
(18). La règle écrite d'avance exige au moins 2 mondes par classe : **la validation L3 sera donc déclarée non
évaluable.** Je ne change pas la sélection pour autant — la modifier maintenant, même sur la carte seule, serait un
amendement, et la question de la période (L2) n'en dépend pas.

Ce que ce tirage apprend déjà : **les mondes sans prise sont rares.** Parmi les graines 13 à 24, une seule sur douze
tombe à 5 cases ou moins ; parmi les 8 mondes historiques, c'était quatre sur huit. Le jeu de mondes sur lequel
toutes les campagnes précédentes ont tourné était anormalement pauvre en routes — c'est une des raisons pour
lesquelles l'adversaire y pesait si peu.

**Prédiction descriptive, écrite ici pour pouvoir échouer, sans valeur de test :** parmi les 8 mondes neufs, le
monde **18** aura l'**apport de l'Oracle le plus faible**.

Pour valider vraiment le critère de la route, il faudra un **échantillon stratifié** : chercher des mondes à basse
prise au-delà de la graine 24, et en réunir au moins quatre.

## Résultat — 21/09 11 h 55 : instrument propre, **effet de l'Oracle non reproduit**, période non lue

192 épisodes joués, 186 lus (T 64, R 61, F 61). **Les six portes de qualité passent** : zéro erreur SQF, aucune
case vide, carte présente dans les 122 épisodes à Oracle monté, option *traverser* jouée partout, période conforme.
La campagne est techniquement la plus propre qu'on ait jouée.

**K7, la porte de sensibilité, échoue** : R compromet **+0,094** de plus que T, IC [−0,109 ; +0,312]. Le point est
à un cheveu des 10 points exigés, mais l'intervalle contient zéro. **Conformément à la règle écrite d'avance, la
période δ n'est pas lue.** Les chiffres de F sont affichés par le lecteur ; ils ne sont pas interprétés.

### Ce que ça dit de l'Oracle

Trois estimations de son apport naturel (compromission, bras δ 60 s contre témoin) :

| campagne | écart | IC 95 % | remarque |
|---|---|---|---|
| ORACLE-P2 (lue en calibration) | **+0,197** | [+0,056 ; +0,327] | la première, et la plus haute |
| calibration v1 | +0,009 | — | mélange option/situation confondu |
| **calibration v2** | **+0,094** | [−0,109 ; +0,312] | propre, 16 mondes |

**La première estimation était la plus forte, les suivantes plus faibles** — exactement le motif du « premier choix
dépendant » du 19/09 : un premier succès sélectionné est surestimé. Le bras Oracle, lui, est stable (réussite
0,721 dans ORACLE-P2 comme ici) ; c'est l'écart au témoin qui fond.

**Lecture honnête :** à son réglage normal, l'Oracle ajoute **de l'ordre de 10 points** de compromission — probable
mais modeste, et **trop petit pour être vu de façon fiable avec 60 épisodes par bras**. La calibration cd3a22f
(« la réussite tombe de 92 % à 72 % ») retenait l'estimation la plus favorable ; elle ne doit plus être citée seule.

Et le contrôle positif, lui, reste acquis : **amené au contact, l'adversaire prend 18 fois sur 18.** Ce qui manque à
l'Oracle n'est donc pas la capacité de punir, c'est de **trouver** le détachement — son camp le perçoit rarement.
Le levier le plus probable est ce que l'adversaire **voit**, pas la fréquence à laquelle il décide.

### L3 — non évaluable, comme annoncé ; la prédiction du monde 18 **échoue**

Un seul monde neuf à basse prise (18) : la validation est non évaluable. La prédiction descriptive — *le monde 18
aura l'apport le plus faible des huit neufs* — **échoue** : 18 est à −0,250, mais le monde 19 est à **−0,750** et le
15 à −0,250.

### ⛔ Je retire « la route prédit la prise »

Hier j'ai présenté comme un résultat qui tient : 7 cases atteignables → 0,42 de compromission, 4-5 cases → 0,15.
**Recalculé à l'identique sur les mêmes huit mondes connus, avec les données d'aujourd'hui, le sens s'inverse** :

| | compromission R+F, haute prise | basse prise |
|---|---|---|
| calibration v1 (20/09) | 0,393 | 0,156 |
| **calibration v2 (21/09)** | **0,296** | **0,375** |

Même le témoin saute de 0,312 à 0,062 dans la classe basse d'un jour à l'autre. **Avec une quinzaine d'épisodes par
classe, un taux par classe de mondes est du bruit.** Le fait géométrique reste vrai — la CRÊTE du monde 5 est à
1 865 m de toute route — mais son lien avec la punition **n'est pas établi**. La ligne `cases_routieres` reste
utile comme instrument ; elle n'est plus un critère d'admissibilité.
