# PRÉDICAT — LA NUIT DE L'HÉSITATION, écrit avant le premier épisode

**25/08/2026, 11 h 20.** Protocole revu par Fable et **corrigé sur un point factuel** :
il croyait le témoin périmé par la réparation du banc. **Faux** — `a98dc5d` (banc réparé)
date du 22/08 à 22 h 00 et la nuit a été lancée **la même minute** ; le 30,7 % et le 33,6 %
sortent tous deux du banc réparé, et le seul changement depuis est le décodeur.

**Mais son design est adopté quand même**, pour une raison qui survit : comparer d'une nuit
à l'autre expose au **destin de session**, que ce projet a mesuré. Deux bras dans la **même**
nuit y sont immunisés.

## Le dispositif

| | |
|---|---|
| **artefact** | **un seul** : `boucle_pol.pt`, celui déployé le 23/08. Un second artefact serait un troisième changement silencieux |
| **bras 1** | `HMT_DECODEUR=echantillon`, **τ = 1** |
| **bras 2** | `HMT_DECODEUR=argmax`, même artefact |
| **entrelacement** | épisode par épisode (ABAB), **même graine d'action** dans les deux bras au même rang |
| **n** | 67 par bras · **~9 h** |

**La nuit est FACTORISÉE** : *figé de cette nuit contre 33,6 %* = dérive éventuelle du
banc ; ***hésitant contre figé, même nuit* = effet du décodeur**, immunisé contre tout le
reste. Mon plan initial à un bras empilait deux changements sur un chiffre — la structure
exacte que ce dossier a passé deux jours à démonter.

## Les quatre issues, acceptées d'avance

Critère principal : **hésitant − figé, même nuit**. Repère du gymnase pour cet artefact :
**−19,6 points** (51,1 → 31,5).

| n° | condition | conclusion, écrite maintenant |
|---|---|---|
| **1** | figé ≈ 33,6 (±12) **et** hésitant ≈ figé − 20 | le banc est stable **et le gymnase prédit l'effet du décodeur dans Arma** — une revendication de fidélité sur un axe neuf. La décision garde son coût, connu et accepté |
| **2** | figé ≈ 33,6 **et** hésitant ≈ figé (écart > −10) | l'effet du gymnase **ne transfère pas** ; la décision est **gratuite** dans Arma ; anomalie de fidélité à noter |
| **3** | figé ≈ 33,6 **et** hésitant < figé − 25 | **pénalité d'hésitation propre à Arma**. ⚠️ **Déclencheur pré-inscrit : la décision repasse en délibéré POUR ARMA.** Un décodeur par monde est une issue légitime — c'est pour ça que `HMT_DECODEUR` est un paramètre |
| **4** | figé **hors** de 33,6 ± 12 | la réparation ou le temps a déplacé le banc : **tous les chiffres d'avant expirent, natif inclus**. La nuit reste lisible en interne, et la relecture du natif se programme |

⚠️ **Honnêteté de puissance, écrite d'avance** : à 67 épisodes par bras, cette nuit détecte
un effet de **~20 points**. **Un effet plus petit sort en « NON RÉSOLU À CE BUDGET »**, et
c'est une **issue acceptée**, pas un échec.

## ⚠️ La concordance, recalculée pour le n réel

Le seuil déposé — *« deux passes à moins de 10 points »* — était dimensionné pour **n = 67
par passe**. Ici chaque bras se coupe en deux moitiés de **~31**. À taux de fausse alarme
constant (10 pts vaut 1,19 écart-type à n = 62), le seuil devient **14 points**.
**Le garder à 10 sonnerait faux par construction.**

## Les observables secondaires, DIAGNOSTIQUES et non renversants

Calculés **hors ligne** depuis le relevé `.npz` — **aucun changement au banc** :

1. mètres **réalisés** / mètres **commandés**, par pas ;
2. ventilés par **l'angle entre commandes consécutives** (0°, 45°, 90°, 135°, 180°) ;
3. **taux de renversements** (> 90°) par épisode.

**Le comparateur est le bras figé de CETTE nuit**, jamais la nuit d'avant. Si le rapport
s'effondre aux grands angles **et** que l'hésitation en émet plus, le risque déclaré est
mesuré **et décomposé** : l'inertie mange les demi-tours.

⚠️ **Ils expliquent le critère principal, ils ne peuvent pas le renverser.**

## Les interdits de cette nuit

1. **Aucune comparaison à un chiffre d'avant cette nuit pour en tirer un verdict.**
   33,6 · 30,7 · 0/20 : **contexte, jamais témoin.** Seul le bras figé re-ancre.
2. **Aucune réparation de la marche en cours de nuit** — pas de lissage, pas de maintien
   d'action, pas d'hystérésis. Si la marche est coupable, le correctif est un **objet neuf
   pour une nuit neuve**.
3. **Aucune lecture au milieu.** La nuit court jusqu'au bout et se lit **une fois**, contre
   les quatre issues ci-dessus.
4. **Un seul artefact**, un seul τ, une graine d'action journalisée par épisode.

## Test de fumée — passé

Un épisode par décodeur. `att=4 def=4` des deux côtés, prévol vert, chaîne complète.
**L'échantillonnage se produit réellement côté pont** (`[5,4,4,5]` puis `[5,5,5,3]`), et le
**figé émet `[0,0,0,0]` à tous les pas** — le champ spatialement constant, visible dans Arma.
