# DÉPÔT — LA PORTE PLEINE-CHEMIN, critères écrits AVANT

17/08/2026, socle `2.7.0` (`fab63ae`). Critère de sortie de panne, tel que Fable l'a posé.

## Ce qui a changé depuis la dernière porte

| | |
|---|---|
| **A1** | tout homme jetable est invulnérable ; le mannequin n'est plus une cible captive |
| **A2** | jeton de génération — deux prévols ne se superposent plus |
| **A3** | le muet se décompose : pont mort / prévol lent / prévol planté |
| **B1** | une seule boucle de marche, un seul tir, télémétrie dans la brique |
| **B3** | on ne tue que les serveurs qu'on a lancés |
| **C** | les positions de la scène certifiées AVANT que quiconque naisse |
| **D** | le corps rend 104 %, le « 62 % » était du terrain |
| **B2** | le `reveal` est inutile, T7 certifie le bon canal |

## LES QUATRE LIGNES, et elles doivent être vertes ENSEMBLE

1. **faux-reçus inexpliqués : ZÉRO sur ≥ 50 réceptions** — règle de trois, borne à 6 %,
   plafond dérivé de la règle 19.
2. **muets décomposés** — « planté » : zéro toléré ; « lent » : doit avoir disparu avec le
   timeout par étape ; « pont » : compté à part, plafond économique.
3. **aucun regroupement par serveur** au-delà du binomial — test de surdispersion, seuil
   χ² à (lots − 1) ddl, 5 %.
4. **les quatre sabotages rejoués** — munitions (T4), jambes (T5), traverse et tir (placeur).

**Une seule ligne rouge ⇒ le banc RESTE en panne diagnostique.**

## Forme

Lots de 12 sur serveur neuf — le pont meurt à 20-40 min et une porte d'une heure sur un
serveur unique s'est déjà terminée en « trois tirages sans réponse ». Cinq lots donnent
60 tirages pour 50 réceptions.

## Angle mort déclaré ⟨règle 20⟩

Cinq naissances de serveur au lieu d'une : un résidu propre au serveur reste possible, mais
il est réparti. Et les lots restent l'unité du test de regroupement, donc un effet **intra**-lot
plus fin que le lot ne serait pas vu.
