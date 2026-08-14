# VERDICT — le gel n'est PAS un défaut de perception. Le banc ne présente qu'UNE situation.

Mesuré le 14/08/2026, après le changement de site. **Ce dépôt corrige une lecture que
j'avais donnée deux heures plus tôt** — « c'est la perception, et c'est tranché ». C'était
vrai des marges ; ça ne l'est plus une fois les marges réparées.

## 1. Le site a réparé les marges — complètement

| | avant (1734,5391) | après (4644,5652) |
|---|---|---|
| colonnes dont la médiane sort de [1 % ; 99 %] du gymnase | **5 / 12** | **0 / 12** |
| décisions hors plage sur au moins une colonne | **100 %** | **0,0 %** |
| `slope` médiane | 0,000 | 0,589 (gymnase 0,368) |
| `dcover` médiane | 0,533 (garde-fou) | 0,033 (gymnase 0,035) |

`dcover` était **déclaré d'avance comme non résolu** ; il l'est. La sonde de site l'avait
mesuré à 0,167 en échantillonnant uniformément le disque de 200 m ; les hommes, eux,
suivent un couloir vers l'objectif et y rencontrent d'autres reliefs. **La prédiction était
fausse dans le bon sens — ça reste une prédiction fausse**, et la méthode qui l'a produite
(échantillonnage uniforme du disque) ne représente pas ce que le banc traverse.

## 2. Et la politique s'est figée DAVANTAGE

```
GYMNASE   {0:2750, 1:1441, 2:1144, 3:1459, 5:2115, 6:873, 7:342, 9:116}   dominante 26,9 %  ·  8/10
ARMA      {2:120}                                                          dominante 100 %   ·  1/10
```

Avant le changement de site : 93,5 % sur deux actions. Après : **100 % sur une seule**.

## 3. Arma est POURTANT dans la distribution conjointe

Distance de Mahalanobis au gymnase (contrôle positif : le gymnase lui-même doit y être
proche — il l'est, médiane 2,45) :

- médiane d'Arma : 4,31 → **98,25ᵉ centile du gymnase**. Queue extrême, mais dans le support.
- points d'Arma au-delà du 99ᵉ centile : **19,2 %** — le critère déposé exigeait > 50 % pour
  conclure au hors-distribution conjoint. **Non franchi.**
- distance au plus proche voisin du gymnase : médiane **3,85**, quand deux points du gymnase
  sont typiquement à **5,01** l'un de l'autre. **Arma est plus proche du gymnase que le
  gymnase ne l'est de lui-même.**

⚠️ Le critère « > 50 % » était peut-être trop laxe. Il n'est **pas** réinterprété après coup ;
la position en queue (98ᵉ centile) est reportée telle quelle à côté de son verdict.

## 4. Ce que la politique fait LÀ OÙ Arma se trouve

Sur les 200 points du gymnase les plus proches d'Arma :

```
{1:19, 2:129, 3:52}   dominante 64,5 %  ·  3 actions
```

**L'action 2 est la bonne réponse dans cette région** — le gymnase la choisit lui aussi,
presque deux fois sur trois. La politique ne délire pas : elle donne la réponse apprise.

## Le verdict

**Le gel n'est pas une panne de perception ni une saturation.** C'est que le banc ne
présente qu'**une seule situation** : les huit hommes y sont **2,3 fois plus serrés** que
dans le gymnase (étalement 0,069 contre 0,160), au même azimut, à la même distance — donc
ils reçoivent tous la même réponse, qui est la bonne. Et ils meurent au pas 14, avant que
quoi que ce soit puisse évoluer.

**Le banc reproduit les MARGES du gymnase, jamais ses SITUATIONS.**

## Ce que ça change pour la suite

La réparation n'est plus dans la couture. Elle est dans **la naissance des hommes** (les
étaler comme le gymnase les étale) et dans **la survie** (14 pas ne laissent aucune
décision se déployer). Aucune campagne de répétitions avant ces deux-là.

## Ce que ça ne dit pas

Un épisode, 120 décisions, un site. Le contrôle positif tient (le gymnase varie, 8 actions
sur 10) et la plomberie est fidèle (100 % d'accord vif/rejeu), mais la taille est mince.
