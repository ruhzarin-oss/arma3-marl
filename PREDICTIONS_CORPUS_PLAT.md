# LE CONTRÔLE POSITIF, CONSTRUIT — spécification écrite AVANT la mesure

**19/08/2026, 21 h 20.** Suite de `DERIVATION_CRITERE_ARRET.md`.

Le contrôle positif de ce soir avait échoué **parce qu'il était hérité** : les 12 lieux
« connus » l'étaient au titre d'une marche vers le nord seulement. On en construit un
qui ne dépend d'**aucun** critère de marche.

## LA SÉLECTION — SUR LE TERRAIN SEUL, JAMAIS SUR UN RÉSULTAT DE MARCHE

Un lieu entre dans le corpus si, et seulement si :

| condition | seuil |
|---|---|
| pas dans l'eau | `surfaceIsWater` faux |
| **plat** : dénivelé sur ±15 m (9 points) | **≤ 3 m** |
| **dégagé** : objets à moins de 10 m | **aucun** |

Tirage uniforme, graine 19, ±250 m autour de 4644/5652. Cible : **50 lieux**.
⚠️ Aucune de ces trois conditions ne regarde une distance parcourue. Le corpus est donc
indépendant du critère qu'il servira à juger.

## LES PRÉDICTIONS, CHIFFRÉES

| n° | prédiction |
|---|---|
| **P1** | **≥ 90 %** des lieux plats et dégagés ont un minimum sur 8 azimuts **≥ 10 m** |
| **P2** | l'écart entre le 1ᵉʳ et le 3ᵉ quartile de leurs minima est **< 4 m** |
| **P3** | le sabotage des jambes les refuse **tous** (0/50) |

## LA RÈGLE DE DÉRIVATION DU SEUIL — écrite avant les nombres

> **seuil = le 5ᵉ centile des minima du corpus plat, arrondi au mètre inférieur.**

Justification : le corpus est fait de lieux dont on sait, **par le terrain**, qu'ils sont
libres. Le seuil doit donc les recevoir presque tous — le 5ᵉ centile laisse la marge d'un
cas sur vingt pour l'imprévu, et **rien de plus**. Le seuil ne regarde ni le taux de
réception du tirage libre, ni les 12 anciens lieux.

## LE FALSIFICATEUR DE L'APPROCHE ELLE-MÊME

> **Si les minima du corpus plat s'étalent comme ceux du tirage libre (0 à 19 m), alors
> la platitude et le dégagement ne déterminent pas le blocage** : la cause serait ailleurs,
> et le « minimum sur 8 azimuts » ne serait pas la bonne grandeur. L'approche tomberait,
> et le critère resterait non écrit.

Concrètement : **P2 est le falsificateur**. Si l'écart interquartile dépasse 4 m, on arrête.

## CE QUI RESTE INTERDIT

Choisir la statistique ou le seuil en regardant lequel fait passer les lieux qu'on
aimerait voir passer. La statistique (**minimum sur 8 azimuts**) et la règle de seuil
(**5ᵉ centile du corpus plat**) sont fixées ici, avant la mesure.
