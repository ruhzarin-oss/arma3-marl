# LA PORTE PLEINE-CHEMIN — LES QUATRE LIGNES, ET UNE RÉSERVE DE HASH

17/08/2026, 23 h. Porte sur socle `2.7.0`, sabotages sur `2.8.0`.

## Les quatre lignes du critère, écrites avant

| ligne | mesure | verdict |
|---|---|---|
| **1 · faux-reçus inexpliqués** | **0** sur **56** réceptions (exigé : 0 sur ≥ 50) | ✓ **VERTE** |
| **2 · muets décomposés** | 0 planté · 0 pont · 4 lents, tous nommés | ✓ **VERTE** |
| **3 · regroupement par serveur** | **X² = 4,44** — seuil 5 % à 11,07 | ✓ **VERTE** |
| **4 · les quatre sabotages** | munitions 3/3 · jambes 3/3 · traverse ✓ · tir ✓ | ✓ **VERTE** |

**54 verts sur 60 tirages, soit 90 %** — contre **26 %** ce matin.

## ⭐ LE DESTIN DE SESSION A DISPARU

| | X² (11 ou 4 ddl) | surdispersion |
|---|---|---|
| sonde d'unité, ère 1.1 | **49,8** | ×4,15 |
| sonde du pont, ère 1.2 | **56,6** | ×4,71 |
| **porte pleine-chemin, socle 2.7.0** | **4,44** | — |

Le phénomène qui a occupé toute la session — un serveur naissant bon ou mauvais et le
restant — **n'est plus détectable**. Il n'a pas été contourné : sa cause a été trouvée (le
placeur jugeait la pente au lieu de la marche) et réparée.

## LA RÉSERVE, et elle est écrite au lieu d'être plaidée

**La porte a tourné sur `2.7.0`, les sabotages sur `2.8.0`.** Une porte certifie **un hash**,
et le hash a changé entre les deux.

L'équivalence est **démontrable par lecture** : le diff `2.7.0 → 2.8.0` n'ajoute que le levier
`_vyT5`, et hors sabotage `_vyT5 = 6`, qui est exactement le défaut de `HMT_MARCHER`
(`["_vy", 6]`). L'appel est donc identique au caractère près quand `HMT_SABOTER` n'est pas posé.

**Mais démontrable n'est pas mesuré.** La porte est relancée sur `2.8.0` pour lever la réserve.
Tant qu'elle n'a pas rendu, le banc reste **formellement** en panne — non parce qu'un doute
pèse sur le monde, mais parce qu'aucune ligne ne se déclare verte sur un hash qu'elle n'a pas
éprouvé.

## Ce que le sabotage des jambes a révélé au passage

Le levier `HMT_SABOTER = "jambes"` retirait `PATH` — **le pathfinding** — à un test qui se
déplace par `setVelocity`, **une impulsion physique qui ne passe pas par le pathfinding**.
Résultat : 1 rouge sur 3, deux tirages restant **verts jambes retirées**.

Ce levier vivait depuis le socle `1.11.0` et **n'avait jamais été exécuté**. Il aurait pu
faire croire à un contrôle positif passé — exactement ce que la règle 18 interdit.

**Deuxième fois de la journée pour cette faute précise** (la première sur l'acte 2 du placeur).
Un sabotage doit attaquer le mécanisme que le test **emploie**, et un levier jamais joué n'est
pas un garde-fou : c'est une décoration.

## Ce qui attend, une fois la réserve levée

1. **NATIF ×2**, selon `DEPOT_NATIF.md` et son amendement — n = 67, deux passes, concordance
   à moins de 10 points.
2. **La politique rejouée sous le même prévol** — sans quoi le 44,8 % et NATIF viennent de
   deux instruments différents.
3. Restent ouverts : le transitoire de rang 1, la divergence `doWatch` objet/position, le
   capteur de visée pour `cible_unique` et l'avantage du flanc.
