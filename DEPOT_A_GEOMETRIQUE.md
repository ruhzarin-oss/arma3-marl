# Dépôt — l'hypothèse A mesurée sur LA CARTE SEULE. Critères AVANT.

Déposé le 15/08/2026, sur reprise de Fable : *« l'hypothèse A est retenue sur une mesure
confondue. Temps passé près du couvert mélange la carte et la politique : un agent qui
cherche le couvert gonfle ce temps là où il en trouve. »*

Il a raison. Les 44,8 % contre 11,6 % que j'avais lus **ne mesurent pas la disponibilité**,
ils mesurent ce que l'agent a occupé. **A n'est pas établie.**

## La grandeur — sans agent, sans politique, sans épisode

**Distance au couvert le plus proche, échantillonnée sur le COULOIR D'APPROCHE**, dans les
deux mondes : des rayons de 170 m vers l'objectif, exactement le trajet que le banc impose.

- **Arma** : mesure **déjà faite** par `sonde_dcover.sqf` au site (4644, 5652), seuil local
  réparé, 24 rayons × 8 distances. Réemployée telle quelle — c'est une mesure de **carte**,
  aucune politique n'y intervient, et elle est antérieure à cette question.
- **Gymnase** : mêmes rayons, même géométrie, sur les terrains générés par `MONDE_ARMA`.
  Pur torch, aucun serveur — **zéro concurrence avec le run des 67 en cours.**

## CONTRÔLE POSITIF ⟨règle 16⟩ — l'échantillonnage représente-t-il le couloir ?

**L'échantillonnage carte-seule doit retrouver, à un facteur 2 près, le `dcover` que les
agents ont réellement traversé dans chaque monde** (Arma 0,123 de moyenne ; gymnase 0,041).
S'il en est loin, le couloir échantillonné n'est pas celui qui est parcouru et **rien ne se lit**.

## LES PORTES SONT EXÉCUTÉES AVANT DE JUGER ⟨règle 18⟩

Chaque bande passe deux cas fabriqués — un qui doit la franchir, un qui doit la faire
tomber — imprimés **avant** toute donnée réelle.

## Les lectures

| médiane Arma ÷ médiane gymnase | lecture |
|---|---|
| **> 2** | le couvert est réellement **plus rare** sur Arma. **A RETENUE**, et cette fois sur la carte. |
| **0,5 à 2** | la carte offre autant de couvert des deux côtés. **A RÉFUTÉE** — l'écart est comportemental, pas géographique. |
| **< 0,5** | Arma offre **plus** de couvert. A réfutée dans l'autre sens. |

## Ce que ça ne dira pas

Si A est réfutée, l'agent dispose d'autant de couvert et ne s'en sert pas — ce qui rejoint
le verdict « exposition CHOISIE » sans le prouver, puisque celui-ci reste confondu.

Si A est retenue, ça ne dit toujours pas **pourquoi** l'agent s'expose 73 % du temps quand
un abri est à une cellule.
