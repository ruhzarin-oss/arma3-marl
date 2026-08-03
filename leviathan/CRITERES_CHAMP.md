# CRITÈRES — LE CHAMP DE RISQUE (figés avant le premier run)

Écrit le 27/07/2026, **avant** d'avoir lancé le moindre entraînement avec le champ.

## Ce qui motive ce test — mesuré, pas supposé
L'agent qui voit l'arc contourne **autant** que le crochet scripté (20,2 % du temps dans
l'angle mort contre 22,3 %) et **fait le même détour en distance** (2,46 de trajet par
mètre gagné contre 2,02). Mais il le fait **à 132 m quand le crochet le fait à 184 m**,
et il paie **55 % de son exposition entre 120 et 160 m** quand le crochet en paie 38 %
au-delà de 160 m.

**Même manœuvre, même quantité, mauvais moment.** Or l'exposition n'a pas le même prix
partout : être vu coûte 0,07 par pas à 200 m et 0,20 à 25 m (courbe mesurée sur Arma).
Le crochet achète son écart au tarif du long. L'agent l'achète au tarif fort.

**Pourquoi :** à 170 m, rien dans son observation ne lui dit qu'il paie déjà. Il ne
perçoit ni les tirs ni les dégâts. Il découvre le danger en mourant — et on meurt près.

## Le protocole
Deux bras, mêmes graines, tout identique sauf l'observation.
- **VOYANT** (témoin) : arc de tir seul — la meilleure configuration connue
- **VOYANT + CHAMP** : arc + le danger dans les 8 directions, **à 35 m**

⚠️ **35 m et pas un pas** : c'est une lecture à l'échelle de la MANŒUVRE, pas un réflexe.
⚠️ **Le prix, jamais la réponse** : le mouvement le moins cher est toujours de fuir ;
l'arbitrage risque/progression reste entier. C'est ce qu'un soldat lit dans le terrain.
⚠️ **Géométrie générique** (qui voit quoi d'où), pas une hypothèse sur le combat — même
principe que la coque à 12 rayons déjà dans le projet.

## Repères mesurés
| | expo/m | prise | distance du détour |
|---|---|---|---|
| frontal scripté | 0,0349 | 36 % | 118 m |
| appris aveugle | 0,0310 | 71,6 % | 123 m |
| **appris voyant** | **0,0224** | **81,4 %** | **132 m** |
| crochet scripté | 0,0136 | 89,7 % | 184 m |

## Seuils, figés
- **SUCCÈS** : exposition par mètre **≤ 0,0180** (moitié de l'écart restant entre le
  voyant et le crochet comblée) **ET** prise ≥ celle du bras témoin, aux fluctuations près.
- **TÉMOIN DE MÉCANISME — choisi à partir de ce qu'on a MESURÉ, pas de ce que j'imagine** :
  la **distance à laquelle le détour se fait** doit monter à **≥ 155 m** (mi-chemin entre
  132 et 184). C'est le mécanisme même de l'hypothèse : manœuvrer au tarif du long.
  ⚠️ Le témoin précédent (temps passé dans l'angle mort) avait ÉCHOUÉ à expliquer quoi que
  ce soit — 18,9 % contre 20,2 % pendant que l'exposition chutait de 28 %. Leçon retenue :
  un témoin se choisit dans les données, pas dans l'intuition.
- **CONTRE-ÉPREUVE** : le bras témoin doit reproduire ≈0,0224 d'exposition et ≈81 % de
  prise. Sinon autre chose a bougé et la comparaison ne vaut rien.
- **ÉCHEC** : les deux bras restent dans le bruit → le prix du terrain ne suffit pas.
  Reste alors l'audition (percevoir qu'on est déjà sous le feu) et le champ d'intention.

## Volume
3 graines par bras, 150 rondes, évaluation sur 300 épisodes avec une graine différente.

## Interdits
1. Retoucher `champ_R` (35 m) ou tout autre réglage après avoir vu les résultats.
2. Déplacer un seuil.
3. Conclure sur la seule prise : une prise qui monte sans que l'exposition descende,
   c'est encore de la force.
