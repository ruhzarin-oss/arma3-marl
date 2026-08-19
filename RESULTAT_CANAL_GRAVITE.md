# RÉSULTAT — LE CANAL AVEC GRAVITÉ. 2 prédictions sur 4.

**19/08/2026, 20 h 30.** Mesure **appariée** : 12 lieux × 2 canaux dans le **même passage**,
plus 4 bras sud. n = 28. Journal `serverVUEGRAV.out`.
Prédictions écrites et committées **avant** (`PREDICTIONS_CANAL_GRAVITE.md`, `c88259a`).

## LE TABLEAU

| | ancien canal (`Z=0`) | **nouveau canal (gravité)** |
|---|---|---|
| **montée** — distance | 14,3 m | **15,0 m** |
| **montée** — part au sol | 100 % | **100 %** |
| **descente** — distance | 24,1 m | **22,1 m** |
| **descente** — part au sol | 0 % | **38 %** |
| **descente** — hauteur max | **6,8 m** | **0,4 m** |

## LES PRÉDICTIONS

| n° | prédiction | obtenu | |
|---|---|---|---|
| P1 | part au sol en descente **> 50 %** | 38 % | **ÉCHOUE** |
| P2 | distance en descente **< 20 m** | 22,1 m | **ÉCHOUE** |
| P3 | distance en montée **dans [11 ; 16] m** | 15,0 m | **PASSE** |
| P4 | hauteur max en descente **< 2,0 m** | **0,4 m** | **PASSE** |

**Falsificateur de la branche : NON déclenché** (il exigeait ≥ 23 m avec < 10 % au sol).

## CE QUI EST ÉTABLI

1. **Le vol est aboli.** 6,8 m → **0,4 m**. L'homme ne s'élève plus : il **effleure**.
   C'était l'absurdité physique ; elle est corrigée.
2. **P3 confirme le mécanisme.** En montée, rendre la gravité ne change **rien** —
   14,3 → 15,0 m, 100 % au sol des deux côtés. Cohérent avec la vitesse verticale relue
   qui y valait déjà 0,0 m/s : le contrôleur d'animation la mangeait déjà.
3. **La thèse de la direction tient sur le nouveau canal** : bras sud, lieu montant
   20,8 et 21,1 m à 58-60 % au sol ; lieu descendant 16,0 et 16,4 m à **100 %** au sol.

## POURQUOI MES DEUX SEUILS ONT ÉCHOUÉ — ET CE N'EST PAS LA BRANCHE

J'ai prédit une **retombée franche**. Le régime réel est l'**effleurement** : l'homme touche
par intermittence (38 % des ticks) à quelques dizaines de centimètres, et **garde donc
l'essentiel de sa vitesse**. Fable l'avait annoncé qualitativement — « des sautillements
courts » — et j'ai traduit en chiffres sans modèle de ce régime. **Les seuils étaient faux,
pas la branche.**

⚠️ Cliquet : *une prédiction chiffrée doit sortir d'un modèle du régime attendu, pas d'une
extrapolation linéaire depuis le régime observé.* Deux seuils sur quatre l'ignoraient.

## CE QUI RESTE OUVERT — ET C'EST IMPORTANT

**Rendre la gravité ne suffit pas à rendre honnête le tempo du gymnase.**
L'écart montée/descente passe de **1,7×** à **1,47×** (15,0 contre 22,1 m). Il persiste.
Le recalage du gymnase — deuxième moitié de la branche 1 — reste **entièrement à faire**.

**Et l'ancien seuil devient universellement infranchissable** : sur le nouveau canal, la
plus longue distance des 12 lieux est **22,5 m** — sous les 23 m. Le critère doit être
redérivé de la capacité du canal retenu, comme prévu.

## ORDRE DE LA SUITE

1. Adopter le canal en production (`arma_couture.py`, socle) — la mesure l'autorise.
2. Redériver le critère du placeur sur ce canal, avec sa grandeur, sa statistique, son
   seuil et son n, plus ses sabotages.
3. Recaler le tempo du gymnase — et **mesurer d'abord** la capacité par régime.
4. Puis seulement : tampons, porte pleine, et la file (anneau, bloc C, NATIF ×2).
