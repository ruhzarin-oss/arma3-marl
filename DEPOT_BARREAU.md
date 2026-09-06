# LE BARREAU ET LES TROIS PORTES — déposé le 26/08/2026, avant tout entraînement

Amende `DEPOT_TEMOINS.md` (`85c8f481a72026ea`), qui déclarait la famille **avant** tout calcul.
Voici ce que la famille a rendu. **Aucun modèle n'a été entraîné à cette heure.**

## LE BANC EST RÉPARÉ
Indexé par **IDENTIFIANT**, plus par colonne. 20 blocs de temps, **6 tenus à l'écart**, jamais
mélangés. Sur ces 6 blocs : 1 535 566 pas, **432 transitions** vivant→mort, taux de base
**0,0281 %**.

## LE BARREAU — maximum de la famille, sur n = 432 positifs
| témoin, zéro paramètre | AUC |
|---|---|
| **T1 — suppression subie** | **0,7379** ← LE BARREAU |
| T2b — `knowsAbout` dirigé vers lui | 0,5862 |
| T2a — être vu (arête `vue`=1) | 0,5666 |
| T5 — immobile | 0,5666 |
| T3 — proximité de l'ennemi | **0,3572** |
| plancher hasard | 0,5008 |
| T4 — tir dirigé sur lui | ⛔ **NON CALCULABLE** — les arêtes portent (tick, source, cible, knowsAbout, vue, mesurée), jamais qui tire sur qui. Déclaré, pas remplacé. |

**Tout modèle se publie contre 0,7379, avec son n de positifs.**

⭐ **T3 est ANTI-prédictif** : être PRÈS de l'ennemi ne prédit pas la mort, être LOIN la prédit
(0,643 dans l'autre sens). **On meurt à distance, du feu et de la suppression, pas au contact.**
⚠️ Réserve : seuls 65 % des pas ont un ennemi identifiable — à instruire avant usage.

## ⭐⭐ LA PORTE MOYENNE — ses trois cibles, mesurées indépendamment
⟨Fable : « le modèle doit RETROUVER, sans qu'on les lui montre, les tarifs qu'Arma a déjà
avoués indépendamment »⟩

| condition au pas k | taux de mort | sinon | **rapport** | n |
|---|---|---|---|---|
| **supprimé** | 0,4765 % | 0,0160 % | **×29,81** | 40 500 |
| `knowsAbout` > 1 | 0,0739 % | 0,0267 % | **×2,77** | 46 018 |
| **être vu** | 0,0685 % | 0,0279 % | **×2,45** | 8 765 |

**LE MODÈLE DOIT RETROUVER CET ORDRE : suppression ≫ knowsAbout > vu.** Un modèle qui prédit
la transition mais ordonne mal ces trois-là n'a rien compris d'actionnable.

## ⭐ UNE RÉCONCILIATION, ET UNE LEÇON D'UNITÉS
J'ai d'abord annoncé une **anomalie** : « être vu ne rend que 0,5666 ici alors que la fiche
annonce ×2 sur 563 000 observations ». **Il n'y avait pas d'anomalie — je comparais deux
grandeurs différentes.** Une AUC et un rapport de taux ne disent pas la même chose : sur une
classe à 0,03 %, un facteur 2 laisse une AUC proche de 0,5, sans qu'aucune des deux ne soit
fausse.
**Mesuré ici : ×2,45.** La fiche disait ×2, sur un autre corpus, un autre découpage, sans que
je l'aie cherché. **Les deux mesures se confirment.**
Et la suppression sort à **×29,81** là où le cahier des charges lui donnait **×10** : elle est
trois fois plus lourde encore que ce qui était déposé.

> **Règle : une AUC n'est pas un rapport de taux. Avant de crier à l'anomalie entre deux
> mesures, vérifier qu'elles portent sur la même grandeur.**

## LES TROIS PORTES, ÉTAGÉES
· **BASSE** — battre **0,7379** sur la transition, blocs tenus à l'écart, avec le n.
· **MOYENNE** — retrouver l'ordre **×29,81 ≫ ×2,77 > ×2,45** sans qu'on le lui montre.
· **D'ADOPTION** — le classement de comportements en déroulé interne. Exige un banc
  **interventionnel** ; un corpus passif ne permet pas de dérouler des doctrines. Elle attend
  son monde.

## CE QUI EST INTERDIT À PARTIR DE MAINTENANT
1. Entraîner avant que ce fichier soit haché — **fait**.
2. Publier une AUC sans son n de positifs.
3. Ajouter un témoin après avoir vu les chiffres. La famille est close ; T4 reste déclaré
   non calculable, et le barreau d'origine restera publié à côté de tout amendement.
