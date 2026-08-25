# PRÉ-INSCRIPTION — MONTRER LE PRIX DE LÀ OÙ ON VA

**25/08/2026, 23 h. Écrite avant tout entraînement.**

## Le fait mesuré aujourd'hui, qui la motive

Les dégâts sont calculés sur la géométrie de **FIN de pas**. L'agent décide sur l'exposition
de la position qu'il **quitte** et se fait tirer dessus selon celle qu'il **atteint**.

| distance au défenseur | `los` **avant** le pas | `los` **après** le pas |
|---|---|---|
| 0-40 m | **0,11×** ⛔ | dénominateur **nul** ✓ |
| 40-60 m | 0,25× ⛔ | dénominateur **nul** ✓ |
| 100-130 m | 3,71× ✓ | dénominateur **nul** ✓ |

> **Un homme caché À L'ARRIVÉE du pas n'a RIEN pris.** La règle est nette ; c'est la
> **variable montrée** qui ne l'est pas.

**Donc `los` n'est pas une variable de décision : c'est un compte rendu.** On ne peut pas
apprendre à éviter une exposition qu'on ne voit jamais **avant** d'y aller — et ça explique
enfin, sans hypothèse, pourquoi la brouiller ne coûte que 0,9 point.

⚠️ **Deux hypothèses à moi sont mortes en chemin** : ce n'était **ni** le nombre de
défenseurs (`los` contre le plus proche seulement), **ni** le sens du rayon. Les deux
réparations ont été codées, mesurées, et n'ont pas changé le signe. **C'était le temps.**

## Le geste

Le monde possède **déjà** `_champ_danger` : pour chacune des **8 directions**, la somme, sur
les défenseurs vivants, de la probabilité de toucher à cette distance, filtrée par la ligne
de vue et l'arc de tir. **C'est le prix du terrain, et il est éteint.**

| | |
|---|---|
| **`champ_risque = True`** | l'observation passe de 12 à **20 colonnes** |
| **`champ_R = 14,0`** | ⚠️ il vaut **35 m** par défaut, alors qu'un pas fait **14 m** : le champ décrirait le danger d'un endroit **où l'action ne mène pas**. Le régler sur la longueur du pas n'est pas un second changement, c'est **le seul choix cohérent** du premier |
| budget · graines · décodeur | 1 200 itérations · **k = 4** · échantillonnage, τ = 1 |
| témoin | le bras **sans champ** des mêmes k = 4 graines, en cours |
| lecture | **SELECT**. TEST n'est pas touché |

## Les prédictions

| n° | prédiction |
|---|---|
| **C1** | avec le champ, la politique bat le bras sans champ d'au moins **5 points** |
| **C2** | ⭐ **les colonnes du champ sont LUES** : les brouiller coûte **plus de 10 points** |
| **C3** | `los` reste ignoré — le brouiller coûte toujours moins de 5 points |

⚠️ **Résolution déclarée** : à k = 4, un effet **sous 5-6 points est NON RÉSOLU**.

## Les falsificateurs

> **C1 sans C2** : le gain ne vient pas du champ. On ne le présente **pas** comme « l'agent
> lit le terrain » — c'est un effet de taille de réseau ou de hasard, et on le dit.

> **C2 échoue** — le champ est ignoré comme `los` l'était : alors ce n'est pas l'information
> qui manquait. Il resterait deux suspects, et **aucun ne serait de l'observation** : la
> récompense ne paie pas assez la survie, ou 8 directions × 14 m est encore trop grossier
> pour une géométrie qui se décide à 40 m.

> **C3 échoue** — `los` devient lu **en même temps** que le champ : signe que les deux se
> renforcent, et que le compte rendu devenait utile une fois la décision éclairée.

## Interdits

- **Un seul levier** : ni postures, ni récompense, ni létalité dans ce bras.
- **Ne pas lire TEST.**
- **Ne pas tuer l'expérience des postures en cours** pour passer devant : elle est
  pré-inscrite et à mi-course. Arrêter une expérience déposée parce qu'une idée neuve
  arrive est exactement la faute que ce dossier passe ses journées à éviter.
