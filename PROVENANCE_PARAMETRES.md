# Table de provenance des paramètres — ORDRE 9

*6 août 2026, 11h30. Inventaire, pas chantier. Aucun paramètre n'est recalibré ici.*

## Pourquoi cette table existe

Le champ de risque a été refusé au smoke-test parce que sa portée valait 35 m. Ce 35 m avait
été choisi le 27/07 **sur l'`expo`** — la fonction qu'on a mesurée depuis à AUC 0,5005, le
hasard pur.

> **Classe d'erreur nommée : le paramètre hérité d'un instrument mort.**
> Il ne se voit pas, parce qu'il a l'air d'un choix réfléchi. Il l'était — sur un instrument
> qui n'existe plus.

Le 35 m en était un. Cette table cherche les autres.

## La table

| paramètre | valeur | origine | calibré sur | verdict |
|---|---|---|---|---|
| `CHAMP` (demi-cône de tir) | 35° | banc Arma 03/08, 26 essais | **mesure Arma** | sain |
| `ALLURES` | 0 · 5,8 · 16 m/pas | banc Arma 03/08, 14 essais | **mesure Arma** | sain |
| `POSTURES_V` | 1,0 · 0,53 · 0,23 | banc Arma 03/08 | **mesure Arma** | sain |
| `SEUIL_COUCHE` | 120 m | banc Arma 03/08, 52 essais | **mesure Arma** | sain |
| `PENTE_COUCHE` | 12,0 | — | **choix de conception** | assumé, non porteur |
| `NPAS` | 80 | raisonnement de portée, documenté | choix de conception | assumé |
| `DEPART` | 250 m | choix de conception | choix de conception | assumé |
| `ARRIVE` | 40 m | choix de conception | choix de conception | assumé |
| `TARIFS` | 4,7 | **1,75 × 2,67**, remise à l'échelle | **`expo` morte** | ⚠️ **HÉRITIER** |
| `PORTEE_CHAMP` | 35 → 100 m | 27/07 puis table du 06/08 | `expo` morte → **risque appris** | corrigé par l'ORDRE 8 |
| paliers du curriculum | 60…250 m | empirique, runs précédents | mixte | assumé |
| bonus d'arrivée | `0,05 × gagne` | choix de conception | choix de conception | assumé |

## Le second héritier trouvé : `TARIFS = 4,7`

Le commentaire du code le dit lui-même : la valeur vient de **1,75 multiplié par 2,67**, où
1,75 était le tarif calibré du temps de l'`expo`, et 2,67 le rapport des dispersions.

**La remise à l'échelle est bien faite** — elle évite de comparer « agent à coût fort » et
« agent à coût faible », et elle a été appliquée avant de voir le résultat. Mais elle transporte
un choix dont l'ancêtre a été calibré sur une fonction qui n'ordonnait rien.

**Est-il porteur ?** Le tarif fixe l'arbitrage entre risque et arrivée : c'est le cœur du
comportement. Donc **oui, il est porteur**.

**Est-il mort ?** Non — la remise à l'échelle est un changement d'unité, pas de structure, et
le comportement obtenu avec 4,7 est celui d'un curriculum qui monte jusqu'à 125 m. Il produit
un agent qui arrive.

> **Verdict : signalé, non bloquant.** L'ordre 9 dit qu'un paramètre douteux mais non critique
> se note et n'arrête pas le lancement ; seul un « second 35 m » — mort **et** porteur —
> l'arrête. Le tarif est porteur mais pas mort : il a été requalifié par une mesure de
> dispersion, pas hérité en aveugle.

**Réserve pré-enregistrée** : si l'étage 1 sort « pas de franchissement », le tarif figure dans
la liste des suspects **au même titre** que le concept et que la qualité du champ. Écrit ici,
avant le lancement, pour n'avoir pas à le décider après.

## Ce que la table ne couvre pas

Les paramètres du prédicteur de risque lui-même (architecture, corpus d'entraînement) :
hors périmètre de l'étage 1, et hors du temps alloué à cet inventaire.

## Le gisement, noté et non poursuivi

L'étude du 05/08 obtenait **0,7138** là où le modèle en service donne **0,6549**. Il existe donc
un meilleur champ que celui qu'on utilise. **Ce n'est pas une tâche aujourd'hui** — c'est un
gisement, écrit pour ne pas être oublié.
