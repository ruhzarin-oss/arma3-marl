# LE CRITÈRE EXISTE — mais il ne certifie pas ce que je croyais

**20/08/2026, 00 h 10.** Statistique inversée sur prescription de Fable. Mesuré sur les
données déjà archivées (`serverVUEAZ.out`, `serverVUEREPRO.out`, empreintes dans
`/mnt/data/preuves/2026-08-19_derivation_placeur`).

## LE RETOURNEMENT

Cinq tentatives ont échoué à certifier **« ce lieu est praticable »** — et pour cause :
cette grandeur **n'existe pas de façon stable** (r = 0,771 entre deux passages, plafond
r² ≈ 0,59). Aucun critère ne peut certifier une fiction.

Mais **le prévol n'a jamais eu besoin de ça.** Sa question est :

> **« LE CANAL EST-IL VIVANT DANS CETTE SESSION ? »**

Et cette question a une **signature de panne GLOBALE** : jambes coupées → 0 m dans **tous**
les azimuts. Donc la statistique n'est pas le minimum — **c'est le MAXIMUM sur les 8**.
L'ancien critère prenait le minimum parce qu'il certifiait un **lieu** ; le nouveau prend
le maximum parce qu'il certifie un **canal**.

## LA MESURE

| | n | min | médiane | max |
|---|---|---|---|---|
| **canal sain** | 60 | **18,7 m** | 22,5 | 43,7 |
| **jambes coupées**, mêmes lieux | 60 | 0,0 | 4,4 | **11,8 m** |

**Creux de 6,9 m, sans recouvrement.** Plancher = milieu du creux = **15,2 m**.

| contrôle | résultat |
|---|---|
| faux-rouge — lieux sains sous le plancher | **0/60** |
| faux-vert — lieux sabotés au-dessus | **0/60** |
| **désaccord de verdict entre deux passages** | **0/60 (0 %)** |

**Le maximum absorbe le scintillement qui rendait le minimum inutilisable** : là où un
blocage sur trois changeait d'avis entre deux passages, le verdict de canal ne bouge pas
d'un lieu sur soixante.

## LE CRITÈRE, DANS SA FORME

| | |
|---|---|
| **question** | le canal de locomotion est-il vivant dans cette session ? |
| **grandeur** | distance parcourue en 4 s, canal `sv_vz_preserve_10hz` |
| **échantillon** | les 8 azimuts de la couture |
| **statistique** | le **MAXIMUM** sur les 8 |
| **seuil** | **15,2 m** — milieu du creux mesuré (11,8 ; 18,7) |
| **n de la dérivation** | 60 sains + 60 sabotés + 60 répétés |
| **passages** | **1 suffit** — verdict stable à 0 % de désaccord |

⚠️ **Dit explicitement** : « max ≥ plancher » prouve que **les impulsions arrivent**, pas
que l'homme **marche au sol**. Un azimut parcouru en vol compte comme preuve de vie du
canal — c'est correct pour cette question, et il ne faut pas le lire autrement.

⚠️ **Le seuil est dérivé sur des données déjà vues.** Il doit être **rejoué une fois sur
un tirage frais** (60 lieux neufs + sabotage, ~2 min) **avant adoption**. Pré-inscription
à écrire avant ce rejeu — pas cette nuit.

## CE QUI CHANGE DANS L'ARCHITECTURE

- **Le SÉLECTEUR meurt.** C'est lui qui a fabriqué le « 104 % ». Le placeur ne trie plus.
- **Le placeur et T5 fusionnent** : la mesure du placeur **est** celle de T5.
- **Le champ des 8 distances s'ENREGISTRE** comme télémétrie d'épisode — la pente survit
  en **donnée**, pas en **juge**.
- **T4 et T7 ne bougent pas** : ce sont des actes binaires, la porte y reste le bon objet.
- **Le concept de « faux-reçu » meurt avec le sélecteur** — `quatre.py` est à réécrire.

## LES STATISTIQUES, UNE PAR QUESTION

| question | statistique | passages |
|---|---|---|
| santé du canal | **max** sur les 8 azimuts | **1** |
| champ enregistré du lieu | **médiane de k** passages | **k = 3** |
| étude du blocage (dormante) | fraction de passages bloqués | — |

k dérivé par Spearman-Brown : fiabilité de k passages = k·r / (1 + (k−1)·r), avec r = 0,771.
**k=2 → 0,87 ; k=3 → 0,91 ; k=4 → 0,93.** Pour une exigence de 0,90 : **k = 3.**
Rien de rond, tout dérivé.

## LE DOSSIER DORMANT — LES BLOCAGES

**Réel** (69 % de retour, 12× le hasard), **inexpliqué** : ni pente, ni objets — 23 des 27
bloqués ont un couloir **vide** sur 25 m. Famille d'hypothèses **non mesurée** : état
interne du moteur (cache de collision, micro-géométrie, graine locale du corps).

**Conditions de réouverture, écrites :** le dossier s'ouvre si la télémétrie de campagne
(`HMT|CORPS|SOL`, réparée ce soir, les compte gratuitement) montre qu'ils mordent les
épisodes à un taux qui compte, **ou** s'ils contaminent un verdict que quelqu'un attend.
Sinon il dort. Le dessin fusionné est **robuste au blocage par construction**.
