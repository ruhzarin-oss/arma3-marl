# Règle 18 — Aucun critère ne juge sans avoir été jugé

Amendement de Fable, 15/08/2026, après **quatre occurrences en une seule journée**.

## Le constat

Quatre fois, mon **code** a trahi mon **dépôt**. Chaque fois la faute était démontrable
**sur le papier, avant toute donnée** :

| critère | la faute, vérifiable sans données |
|---|---|
| choix du site | `round(écart, 2)` mettait 0,004 et 0,006 dans deux paniers, quand le dépôt disait « égalité à 0,01 près » — il désignait un site 5× pire sur `dcover` |
| `dcover` | « baisse d'au moins 20 points depuis une base de 19,1 » — **insatisfiable par arithmétique** |
| porte d'azimut | exigeait ≥ 18 valeurs distinctes sur 20 tirages dans 72 casiers, quand le problème des anniversaires en prédit ~2,6 collisions : **échouait sur la majorité des séries valides** |
| bande de gel | déclarait « indécis » jusqu'à 17/20 alors que 4/20 a déjà p = 2 % sous le taux de référence de 3,1 % : **a masqué un résultat établi trois séries de suite** |

**La structure est identique : un juge qui n'a jamais été jugé.** La règle 16 exige qu'une
*mesure* sache échouer ; il manquait la même exigence pour les *critères*.

## La règle

**Avant le run, chaque porte, bande ou seuil est EXÉCUTÉ sur deux cas fabriqués : un qui
doit passer, un qui doit échouer.**

**Exécuté, pas argumenté.**

- Un critère qu'**aucun cas ne peut satisfaire** est faux par construction.
- Un critère qu'**aucun cas ne peut faire échouer** ne contrôle rien.
- Et le code **re-vérifie mécaniquement la clause du dépôt sur sa propre sortie** — l'arrondi
  du choix de site serait tombé là.

## L'épreuve, en une phrase

La bande de gel n'aurait pas survécu dix minutes à ce banc : nourrie du taux de référence
du gymnase lui-même (3,1 %), elle déclarait « indécis » un cas déjà à p = 2 %.

## Portée

Tout critère de tout banc, à compter du 15/08/2026. Complète la règle 16 (contrôle positif
obligatoire pour toute sonde ; juger l'acte pas l'état) et la règle 17 (tout instrument
déclare sa juridiction dans son schéma).

**16 juge les sondes. 17 juge les instruments. 18 juge les juges.**
