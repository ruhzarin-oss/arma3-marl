# DIAGNOSTIC — `monde.py` ET SON AUC DE 0,9996

**26/08/2026.** Vérification demandée avant que ce chiffre serve d'argument. Réponse :
**il ne peut servir d'argument à rien.** Deux défauts indépendants, chacun suffisant.

Fichiers de la mesure : `sonde_auc2.py`, `sonde_identite.py`, `part_erreur.py`.
Aucun modèle n'a été chargé — tout se démontre sur les données seules.

## DÉFAUT 1 — LE BANC EST DÉCALÉ D'UNE COLONNE

`meta.json` déclare onze champs : `id x y z vivant camp tir azimut posture suppression neuf`.
`monde.py` prend `X[..., :8]` et les commente « x, y, z, vivant, camp, tir, azimut,
suppression ». **Il a oublié `id`.**

| ce que `monde.py` croit lire | ce qu'il lit vraiment |
|---|---|
| x | **id** |
| y | **x** |
| z | **y** |
| **vivant** | **z** — 16 797 valeurs distinctes, pas binaire |
| camp | **vivant** — moyenne 0,528, valeurs {0, 1} |

· **La tête de mort est entraînée sur l'ALTITUDE.** Le 0,9996 mesure la persistance de `z`.
  Un témoin sans paramètre atteint **0,9825** sur cette même cible. Le modèle n'a jamais vu
  la colonne des vivants.
· **La position prédite porte sur `(id, x)`**, pas `(x, y)`.

## DÉFAUT 2 — LES TRANCHES NE SUIVENT PAS UN HOMME

`monde.py` suit des **places** (`sel` = indices de colonnes), pas des entités. `meta.json` :
577 places pour **10 034 identifiants** sur la nuit — une place est recyclée. Le filtre
`presence.all(0)` garantit qu'elle est occupée, **pas qu'elle l'est par le même soldat**.

| | |
|---|---|
| traces où l'identifiant change au moins une fois | **50,41 %** |
| pas concernés | 5,04 % |
| identifiants distincts par trace | moyenne 1,79, maximum **12** |
| déplacement par pas, identifiant STABLE | médiane **0,00** · p99 **2,00** |
| déplacement par pas, identifiant QUI CHANGE | médiane **662,88** · p99 **13 264** |

⭐ **99,804 % de l'erreur quadratique publiée vient de ces sauts. Le vrai mouvement en pèse
0,196 %.** Rapport par pas : **9 612×**.

**C'est la cause mécanique de l'échec de `RESULTAT_PORTE0_PREDICTEUR.txt`.** Le dossier
disait « le banc ne séparait pas un crochet d'une ligne droite, le juge était en cause » :
c'est établi, et voici lequel. `err` (0,015829) et `err_pers` (0,015786) sont dominés par les
**mêmes** sauts, donc ils se touchent à la quatrième décimale **quel que soit le modèle**.

## CE QU'IL FAUT MESURER À LA PLACE — cibles et témoins, écrits avant

La cible « est mort au pas k+1 » est **triviale** : 99,98 % des morts en k+1 étaient déjà
morts en k, et le témoin « il était mort en k » obtient **AUC 0,9998** sans un paramètre.

**La seule cible qui pose une question est la TRANSITION — meurt entre k et k+1.**
Taux de base **0,0113 %**. Trois barreaux, mesurés :

| témoin, zéro paramètre | AUC sur la transition |
|---|---|
| « il était mort en k » | 0,2499 |
| **« suppression subie en k »** | **0,7196** ← LE BARREAU À BATTRE |

**Un modèle du monde qui ne dépasse pas 0,7196 sur la transition n'apporte rien**, quelle que
soit son AUC affichée par ailleurs.

## LES TROIS RÉPARATIONS, DANS L'ORDRE

1. **Aligner les colonnes** sur `meta.json`, et ajouter `posture` et `suppression` qui étaient
   jetées. Coût : une ligne.
2. **Suivre des ENTITÉS, pas des places** — sélectionner sur `id` constant sur toute la
   tranche, pas sur `presence.all(0)`. Sinon la moitié des traces mélangent deux hommes.
3. **Changer la cible** : la transition, pas l'état. Et publier l'AUC **contre le témoin de
   suppression**, jamais dans l'absolu.

## LA RÈGLE QUE ÇA DONNE

**Une AUC ne se publie jamais sans son témoin trivial sur la MÊME cible, et une cible d'état
(« est mort ») n'est pas une cible d'événement (« meurt »).** Ici l'écart entre les deux
lectures vaut 0,9998 contre 0,2499 : ce n'est pas une nuance, c'est la question entière.

---

# SUITE — 26/08 après-midi. LE DÉFAUT 3, ET IL EST TERMINAL

Trouvé en cherchant à appliquer la réparation n°2. ⟨Fable avait prévenu : « les hommes qui
MEURENT sont ceux dont la trace casse, ton filtre risque d'appauvrir la classe rare. »
La mesure est allée plus loin que l'avertissement.⟩

## LE FILTRE NE LAISSE AUCUN POSITIF — ET CE N'EST PAS LA FAUTE DU FILTRE

| | sans filtre | par FENÊTRE | par PAIRE |
|---|---|---|---|
| pas gardés | 4 415 862 | 2 222 122 | 4 196 567 |
| **transitions positives** | **514** | **0** | **0** |

Même le filtre le plus permissif — l'identifiant égal sur la seule paire `(k, k+1)` — ne
garde **aucun** positif. Ce n'est donc pas une question de sévérité.

## LA CAUSE : `vivant` EST UNE ÉTIQUETTE, PAS UN ÉTAT

Sur le tenseur **BRUT**, sans le moindre fenêtrage, 13 607 357 paires :

| | |
|---|---|
| passages vivant→mort, toutes paires | 1 484 |
| **passages vivant→mort à IDENTIFIANT CONSTANT** | **0** |
| disparitions (vivant en k, absent en k+1) | **0** |

Et sur 19 309 entités suivies, **`vivant` ne change que pour 3** (0,02 %).

**Une entité ne meurt jamais dans `noeuds.npy`.** Elle y est étiquetée vivante ou morte, une
fois pour toutes. Les 1 484 « transitions » sont des places qui changent d'occupant.

## OÙ SONT LES 10 196 MORTS : DANS `morts.npy`

Tableau séparé, (10 196, 4) :

| col | contenu | plage | remarque |
|---|---|---|---|
| 0 | **instant** | 87,97 → 37 979,80 | 9 626 valeurs |
| 1 | **victime** | −1 → 10 025 | −1 dans 6,1 % |
| 2 | **tueur** | −1 → 10 003 | **−1 dans 29,2 %** = exactement les 2 973 `morts_sans_cause` |
| 3 | code | {0, 1, 2} | moyenne 0,59 |

## CE QUE ÇA CHANGE POUR LA RÉPARATION

La réparation n'est plus « aligner les colonnes ». **Il faut JOINDRE l'événement de mort sur
la ligne de temps des nœuds** : pour chaque entité et chaque pas, la cible devient
« cette entité figure-t-elle dans `morts.npy` dans la fenêtre à venir ». Sans cette jointure,
la tête de mort n'a **aucune cible** — et n'en a jamais eu.

⛔ **Toute AUC de mort produite avant cette jointure est vide de contenu**, y compris le 0,9996
et y compris mon propre barreau de 0,7196, qui portait sur les fausses transitions. **Je le
retire.** Le vrai barreau se recalculera après jointure, et se publiera avec son n de positifs.

---

# ⚠️ CORRECTION — 26/08, 30 minutes plus tard. LE §« DÉFAUT 3 TERMINAL » EST RÉFUTÉ

J'ai écrit ci-dessus : « une entité ne meurt jamais dans `noeuds.npy` », « la cible est
structurellement vide », « la mort est dans `morts.npy` ». **Ma propre mesure le réfute.**

## CE QUI M'A TROMPÉ
Je suivais des PLACES. Or **93,5 % des entités occupent plusieurs places** au cours de leur
vie : une entité change de colonne. Une transition vivant→mort qui se produit en même temps
qu'un changement de place est donc invisible à toute analyse indexée par colonne — y compris
la mienne, qui reproduisait fidèlement le défaut qu'elle diagnostiquait.

## CE QUI EST VRAI, MESURÉ EN SUIVANT L'IDENTIFIANT
| | |
|---|---|
| entités suivies par identifiant | 2 043 |
| qui occupent **plusieurs places** | **1 911 — 93,5 %** |
| dont `vivant` change | 771 — 37,7 % |
| **passages VIVANT → MORT** | **771** |
| passages MORT → VIVANT | **0** — l'étiquette est monotone |
| pas vivants par entité (médiane) | 517 |
| pas morts par entité (médiane) | 793 |

**La cible existe et elle est abondante.** L'étiquette est monotone, donc elle est lisible
comme un état de vie. Aucune jointure avec `morts.npy` n'est nécessaire pour la cible de
base — `morts.npy` reste utile pour le TUEUR (colonne 2, −1 dans 29,2 % = les 2 973
`morts_sans_cause`), c'est-à-dire pour l'attribution, pas pour la détection.

## LA JOINTURE, ÉTABLIE AU PASSAGE
· unité de `morts.npy` col 0 : **secondes, tick = 0,2 s** — 189 459 ticks couverts pour
  173 338 réels, à 9 % près ; les autres hypothèses sont hors d'un facteur 4 ;
· recouvrement des identifiants : **1 563 des 1 726 identifiants échantillonnés dans les
  nœuds sont des victimes, soit 90,6 %**. ⚠️ Ma sonde avait imprimé « les identifiants ne se
  recouvrent pas » en normalisant par le mauvais ensemble — **verdict automatique faux, à ne
  pas reprendre**.

## LA RÉPARATION, DÉFINITIVE ET PLUS SIMPLE QUE CRAINT
1. **Indexer par IDENTIFIANT, pas par colonne.** C'est la réparation ; tout le reste en découle.
2. Aligner les colonnes sur `meta.json` (`id` était oublié) et récupérer `posture` et `suppression`.
3. Cible = la **transition** vivant→mort, jamais l'état.
4. Toute AUC publiée **avec son n de positifs** et **contre son témoin trivial**.

## LA LEÇON, ET ELLE VAUT PLUS QUE LE DIAGNOSTIC
**J'ai diagnostiqué un défaut d'indexation avec un instrument qui portait le même défaut.**
Mes trois premières sondes suivaient des places, exactement comme le banc qu'elles jugeaient,
et elles ont donc « confirmé » l'absence de morts avec une assurance croissante — jusqu'à
conclure à un défaut terminal qui n'existait pas.
**Ce qui a sauvé : un chiffre qui ne collait pas.** Une victime était étiquetée vivante 19,5 %
du temps, ce qui est incompatible avec « aucune transition ». Une contradiction interne vaut
mieux qu'une confirmation répétée — et c'est elle qu'il faut chercher, pas elle qu'il faut
expliquer.
