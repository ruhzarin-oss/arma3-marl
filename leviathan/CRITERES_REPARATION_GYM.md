# CRITÈRES — RÉPARATION DU GYMNASE (figés avant la première ligne)

Écrits le 2026-07-30. Diagnostic de Fable, lu dans le code. Arbitrage : Younes.

## L'INVERSION QUI GOUVERNE TOUT
**Le but n'est pas de faire réussir le gymnase, c'est de le faire échouer au même endroit.**
Un gymnase qui reproduit la halte du juge est un gymnase valide.

## LE CONSTAT
| A | juge | gymnase | écart |
|---|---|---|---|
| 4 | **0,0 %** (n=40, Wilson [0 ; 8,8]) | 94,6 % | 94,6 |
| 8 | **5,6 %** (n=36) | 99,9 % | 94,3 |

Tripler les attaquants déplace le juge de quatre points. **L'écart est invariant à l'effectif** :
ce n'est donc pas un mauvais calibrage de la létalité, c'est une erreur de structure.

**Où meurent les hommes, chez le juge** : partout entre 60 et 130 m, pic à 60-70 m,
écart-type de la distance d'arrêt 15 m. Ni barrière géométrique nette (< 10 m), ni attrition
pure (≥ 30 m) : ils se font tuer **en chemin**, progressivement.

## LES TROIS DÉFAUTS DE STRUCTURE, lus dans `assault_terrain.py`
1. **La vitesse ne dépend jamais du feu reçu.** `spd = self.move * (acts < 8).float()` — elle ne
   dépend que de l'action. Il n'existe **aucun état de suppression côté attaquant** : `dsupp` ne
   s'applique qu'aux défenseurs. Le gymnase est structurellement incapable de représenter une
   halte sous le feu.
2. **La suppression est un bouclier parfait.** `active = ... * (self.dsupp < 0.5)` : binaire,
   totale, remise à zéro chaque pas. À huit attaquants on éteint les huit défenseurs chaque pas
   et on ne prend aucun dégât. **C'est là la saturation à 100 %** — une mécanique, pas un réglage.
3. **La récompense est dominée par tuer.** Le terme `kill_w = 1.5 * (dk - prev_dk)` pèse plus que
   la prise, alors que la mission est de **saisir**. Même réparé sur la mobilité, ce gymnase
   entraîne à la mauvaise tâche.

## LES TROIS RÉPARATIONS
1. **Coût de mobilité sous le feu reçu** : la vitesse de l'attaquant décroît avec l'exposition
   subie au pas précédent. Un homme sous le feu avance moins vite.
2. **Suppression graduée pour les défenseurs** : réduction de cadence avec décroissance, au lieu
   d'une annulation binaire remise à zéro. La courbe n°2 mesurée sur Arma le 28/07 donne déjà les
   valeurs — 8 % de capacité résiduelle, retour à 89 % en deux secondes.
3. **Rééquilibrage de la récompense** : la prise doit dominer la neutralisation.

**Une réparation à la fois, chacune mesurée seule.** Le motif de la journée : deux changements
simultanés et on ne sait plus lequel a payé.

## LE CRITÈRE D'ACCEPTATION — le gymnase doit PRÉDIRE L'ÉCHEC
Après chaque réparation, la même manœuvre de débordement, A=4 contre D=8, 1024 épisodes :
- **taux de prise dans [0 ; 8,8 %]**, l'intervalle de Wilson du juge → réparation acceptée ;
- au-dessus → insuffisante, on passe à la suivante sans défaire la précédente ;
- **exactement 0 % → suspect** : le gymnase ne doit pas devenir impossible, il doit devenir
  difficile. On vérifie alors qu'à A=24 il rend encore quelque chose.

**Contrôle de non-régression obligatoire** : l'étalon des six doctrines est **recalculé** après
chaque réparation. Il changera — c'est le but. Ce qui doit être préservé, c'est l'**ordre** :
le débordement devant, les bonds alternés derniers. Une inversion d'ordre signifie qu'on a
cassé autre chose.

## INTERDITS
- Ne pas toucher aux courbes mesurées sur Arma en juillet : elles sont justes, c'est leur
  assemblage qui ment.
- Ne pas viser 0 %. Viser l'intervalle du juge.
- Aucune revendication tirée du gymnase ne reprend vie avant que le critère d'acceptation soit
  franchi et l'étalon recalculé — les 72 % de l'agent restent gelés.
