# ALIZÉ 6 : le signal anticipatoire existe, mais il est dans la tête de l'ennemi

*Verdict du 13/09/2026. Dépend de [alize-reflexe-trop-tard.md]. Tâche Plane HMT-47.*

## La question posée avant de mesurer

Le verdict du 11/09 établit qu'ALIZÉ ne peut pas marcher sur une entrée RÉACTIVE :
63,4 % des hommes touchés le sont sans aucun avertissement préalable, et la moitié
tombent au premier coup. La question posée dans HMT-47, **avant toute mesure**, était :

> L'exposition à l'instant t prédit-elle un coup reçu entre t et t+2 s ?

avec une porte écrite d'avance : l'écart au témoin doit valoir **au moins +0,10** d'AUC.
Le témoin est un prédicteur sans aucune information spatiale — le temps écoulé seul.

## Ce qui est mesuré

20 épisodes du 11/09, 47 791 couples (homme, instant), aucune seconde d'Arma en plus.
Trois prédicteurs spatiaux contre le témoin. Horizon de 2 s, celui de la porte.

| Étiquette | Prédicteur | AUC | Témoin | Écart | Positifs |
|---|---|---|---|---|---|
| **coup reçu** (pré-enregistré) | `knowsAbout` de camp | **0,7773** | 0,5649 | **+0,2124** | 45 |
| coup reçu | défenseurs qui le voient | 0,6376 | 0,5649 | +0,0727 | 45 |
| coup ou frôlement | `knowsAbout` de camp | 0,6050 | 0,5118 | +0,0932 | 429 |
| coup ou frôlement | défenseurs qui le voient | 0,5377 | 0,5118 | +0,0259 | 429 |

Sur le **premier** coup reçu par un homme — le cas que le verdict du 11/09 déclarait
indéfendable — `knowsAbout` de camp donne 0,7702 contre 0,5786 au témoin, soit +0,1916.

## Le verdict, en deux temps

**Sur l'étiquette pré-enregistrée, la porte PASSE.** Être connu du camp ennemi annonce
un coup deux secondes à l'avance, nettement mieux que le hasard et que le témoin.
Le signal anticipatoire existe. Il existe même avant le PREMIER coup.

**Mais il n'est pas observable par l'agent.** `east knowsAbout _homme` est la connaissance
de l'ennemi. Un agent ne peut pas la lire. Le seul prédicteur qu'il pourrait réellement
calculer — le nombre de défenseurs qui le voient géométriquement — n'atteint que 0,6376,
soit **+0,073** au-dessus du témoin : **sous la porte**.

## Ce que cela change pour ALIZÉ

Le problème d'ALIZÉ n'est ni la vitesse de réaction, ni l'absence de signal. C'est que
le signal utile vit chez l'adversaire. La tâche devient donc :

> **estimer la connaissance ennemie à partir de ce que l'agent peut observer.**

Ce n'est plus un réflexe, c'est un modèle d'adversaire. Et c'est une question bien posée,
avec une cible chiffrée : l'estimation doit s'approcher de 0,78, pas de 0,64.

## Ce que cette mesure ne dit pas

- **Peu de positifs.** 45 couples seulement portent un coup reçu à 2 s. L'AUC de 0,78
  a un intervalle large, de l'ordre de ±0,12. Elle demande confirmation sur plus d'épisodes.
- **Circularité partielle.** Le camp connaît l'homme en partie PARCE QU'UN défenseur le
  vise. Ce n'est pas une fuite du futur, mais la connaissance et le tir partagent une cause.
- **Instrument tronqué.** Le canal VH côté est n'enregistre que la MEILLEURE cible de
  chaque défenseur. Le prédicteur géométrique est donc sous-compté par construction :
  son 0,6376 est un plancher, pas sa vraie valeur.

## La mesure suivante, la moins chère

Rejouer le canal de perception en enregistrant, pour chaque défenseur, TOUTES ses cibles
visibles et non la seule meilleure, puis remesurer le prédicteur géométrique. S'il monte
vers 0,78, l'estimation est inutile : la géométrie suffit. S'il reste à 0,64, il faut
un modèle d'adversaire.

## Fichiers

- `bancs/alize1/analyse/alize6_exposition.json` — la porte, sur l'étiquette élargie.
- `bancs/alize1/analyse/alize6_horizons.json` — les trois étiquettes × cinq horizons.
