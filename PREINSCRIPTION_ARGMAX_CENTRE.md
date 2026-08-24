# CORRECTION AU REGISTRE + TROIS PRÉ-INSCRIPTIONS, écrites avant toute mesure

**24/08/2026, 13 h.** Tout ce qui suit est écrit **avant** les mesures correspondantes.

## ⛔ CORRECTION — « la normalisation est éliminée » était TROP LARGE

`VERDICT_REJEU_INSTRUMENTE.md` (`e6403ae`) porte la normalisation pas par pas en cause
« éliminée ». **Fable a déclaré un vice de l'instrument qu'il avait lui-même prescrit**, et
il a raison :

> **« Les pas où une prise a lieu » ne sont pas là où vit le signal de la prise.** Le
> retour-à-venir porte le +1 **en arrière, actualisé, dans TOUS les pas des épisodes
> gagnants**. Les pas décisifs sont ceux de **l'approche**, pas l'instant terminal.
> Le 1,4 % mesurait la **tranche terminale**, qui devait être petite de toute façon.

**Ce qui est vrai, et remplace la phrase déposée** : la tranche terminale n'est pas écrasée
par la normalisation — elle est même amplifiée (1,45 → 2,61 %). **La question du gradient
aux états décisifs reste OUVERTE**, et elle est **déprioritisée**, pas tranchée.

⭐ **Cliquet : un acquittement trop large ressort un jour comme un fait établi.**

## L'hypothèse qui prend la tête : COLINÉARITÉ BIAIS–COMPAS

Si les attaquants naissent toujours dans **le même secteur**, alors `dgx, dgy` est
**quasi constant sur tout le jeu de données**, donc **colinéaire au terme de biais** du
réseau. « Marcher au NO » devient exprimable de deux façons que **les données ne
distinguent pas** : dans le **biais** (mode figé, aveugle) ou dans les **poids du compas**
(mode navigant). **L'objectif échantillonné ne les sépare pas — les deux donnent le même
rendement.** Où la solution atterrit est **sous-déterminé, et la graine tranche.**

Ça expliquerait d'un coup : le cap figé à **arcsin(103/170) ≈ 37°** de l'axe, la loterie des
graines, et pourquoi l'échantillonnage marche quand même.

> **Le mode est un paramètre LIBRE de l'objectif.** Ce qui n'est pas une fatalité, c'est la
> **taille** de cet espace libre — fixée par la géométrie des entrées. Un compas quasi
> constant la rend énorme. **C'est un choix de conception, pas une loi du gradient.**

## PRÉ-INSCRIPTION 1 — L'ARGMAX CENTRÉ (minutes, artefacts existants)

Calculer le **vecteur de logits moyen** de la graine 1 sur sa propre distribution d'états,
le **soustraire** à chaque état, prendre l'argmax du reste. Si le mode était capturé par un
biais constant, ce décodage libère la partie **dépendante de l'état**.

| n° | prédiction |
|---|---|
| **P1** | l'argmax **centré** de la graine 1 passe de 3,3 % à **plus de 25 %** sur les graines **SELECT** |
| **Falsificateur** | s'il reste **sous 10 %**, l'hypothèse de colinéarité **meurt**, et il ne reste que « mode libre + recette de sélection » |

## PRÉ-INSCRIPTION 2 — LES RÈGLES DU FILM, avant de l'ouvrir

Métrique : **G(k)** = prise en argmax sur **SELECT** au point k ; **S(k)** = en
échantillonnage. Seuil **T = 30 %**.

| règle | condition | conclusion |
|---|---|---|
| **R1 intermittence** | il existe k avec G₁(k) ≥ T, sur **deux points consécutifs** ou avec marge > IC | la condensation **va et vient** → la recette devient la porte **sur points**, via SELECT |
| **R2 bifurcation précoce** | G₁(k) < 10 % **pour tout k**, pendant que G₀ tient ≥ T de façon stable | le sort se scelle **tôt** → sélection sur graines, et la colinéarité passe en tête ; le film **date** le verrouillage |
| **R3 zone grise** | oscillation des deux | le film **ne tranche pas seul** ; l'instrument redevient l'argmax centré. ⚠️ **Et si G₀ oscille fortement, le 49,6 % de la graine « passée » était lui-même la chance de l'itération d'arrêt** — la porte sur points devient la recette pour **tout le monde** |

⚠️ **Garde-fou du vainqueur** : le max sur 24 points bruités est **gonflé par
construction**. Tout point choisi sur SELECT est un **candidat** ; le résultat citable est sa
relecture sur **TEST**, **une fois**, **après** le choix. Jamais l'inverse.

## PRÉ-INSCRIPTION 3 — le rejeu à 13 minutes de l'artefact « 5,7 % »

| n° | prédiction |
|---|---|
| **P3** | sa lecture **échantillonnée** sort **au-dessus de 20 %** |

Si P3 passe, le verdict du premier dossier — *« le protocole ne retrouve plus le 13/08 »* —
se **ré-étiquette** : artefact de **budget** plus artefact de **lecture**, et l'énigme se
dissout.

## Ce qui est interdit

1. **Ne pas randomiser l'azimut d'apparition** comme correctif rapide si la colinéarité se
   confirme : c'est un changement de **MONDE**, qui déplace les doctrines scriptées, la porte
   et tous les chiffres comparables. Ce serait un environnement neuf avec ses propres
   témoins, **pas un patch**.
2. **Ne pas choisir le décodeur après avoir vu les résultats.** Argmax, argmax centré,
   τ = 0,25 : **le décodeur fait partie de la recette**, il se pré-inscrit, il se juge sur
   TEST. Sinon on crée un degré de liberté de sur-apprentissage **au niveau du banc**.
3. **Toujours pas d'entropie annelée** : le tableau d'entropie l'a doublement tuée — le
   13/08 est **mou ET bon**. Le problème n'est pas la mollesse, c'est la **direction** du mode.
4. **Aucun entraînement neuf** tant que ces trois lectures n'ont pas parlé.
