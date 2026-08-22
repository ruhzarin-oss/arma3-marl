# ⛔ L'IA NATIVE D'ARMA BAT LA POLITIQUE DE 15,4 POINTS

**22/08/2026, 18 h 49.** Première comparaison **appariée** du projet.
Prédicat `DEPOT_NATIF.md`, écrit le **16/08 avant tout épisode**.
Socle **5.5.0-21082026**, canal `sv_vz_preserve_10hz`, monde à **zéro erreur de script**.
Lecteur `lire_politique.py` — il **importe** `lire()` de `lire_natif.py`, il ne le recopie pas.

## LE RÉSULTAT

**PRISE** = un attaquant **VIVANT** à moins de **25 m** (`assault_terrain.py:814`).

| | passe 1 | passe 2 | écart | **total** |
|---|---|---|---|---|
| **NATIF** | 56,1 % (n=57) | 63,2 % (n=57) | 7,0 | **59,6 %** · n=114 · IC95 [50,6 ; 68,7] |
| **POLITIQUE** | 48,2 % (n=56) | 40,4 % (n=57) | 7,9 | **44,2 %** · n=113 · IC95 [35,1 ; 53,4] |

**Les deux bras concordent** (écart entre passes < 10 points, seuil déposé).

> ## ➤ ÉCART = **−15,4 points** · erreur-type 6,6 · IC95 **[−28,2 ; −2,5]**
>
> L'intervalle **ne contient pas zéro**, et l'écart **dépasse la résolution de 12 points**
> exigée par le prédicat. **La revendication est permise, et elle est négative.**

## L'ISSUE ÉTAIT ACCEPTÉE D'AVANCE

> *« NATIF ≥ politique → la politique n'apporte rien sur ce banc, et le 44,8 % ne se cite
> plus comme un acquis. C'est l'issue la plus coûteuse, et elle est acceptée d'avance. »*
> — `DEPOT_NATIF.md`, 16/08, avant le premier épisode.

**Elle est réalisée.** Le « 44,8 % » ne se cite plus comme un acquis.

## LE DÉTAIL QUI DIT CE QUI MANQUAIT

La politique mesure **44,2 %** ici, contre **44,8 %** dans les dépôts historiques.
**Le chiffre de la politique était juste depuis le début.**

Ce qui manquait n'était pas une meilleure mesure d'elle : c'était **le plancher contre
lequel la lire**. Pendant des semaines, 44,8 % a été cité comme un acquis sans que personne
sache que **le jeu, tout seul, fait mieux**.

⚠️ **Cliquet : un chiffre sans son témoin n'est pas un résultat, c'est une décoration.**

## POURQUOI CETTE COMPARAISON TIENT, LÀ OÙ LES PRÉCÉDENTES NON

| | |
|---|---|
| même socle | 5.5.0 des deux côtés |
| même monde | **zéro erreur de script** — contre 5 306 pour la mesure retirée du 20/08 |
| même mission | 4 contre 4 à 170 m, mêmes graines de scène |
| **même instrument** | le lecteur de la politique **importe** celui du natif, il ne le copie pas |
| même taille | **128 épisodes complets** de chaque côté |
| conditions levées | prévol vert · le monde bouge (2,2-2,7 m/pas) · le natif **tire** (médiane 64-77 coups) |
| épisodes exclus | **14 et 14 « sans escouade »**, nommés, symétriques |

## CE QUE CE VERDICT NE DIT PAS

- **Rien d'un niveau absolu** : c'est un banc, une mission, un rapport de force, un terrain.
- **Rien sur la cause** de l'écart. Deux candidats sont **notés et non mesurés** : le gymnase
  entraîne contre un adversaire de gymnase, pas contre l'IA d'Arma ; et il **montre** la pente
  sans la **faire payer** (Arma sépare les régimes à 1,47×).
- ⚠️ **Angle mort déclaré** : la mission mord faiblement — 63 % des épisodes sans perte
  attaquante. Un bon attaquant ne peut s'y distinguer que par la prise.

## CE QUE ÇA OUVRE

L'écart est **mesuré**, donc il devient une cible. Les deux candidats se mesurent **sans
réentraîner** — ablation de la pente à l'évaluation, et différentiel scripté entre les deux
adversaires. C'est la première fois que « remonter le niveau » a un sens chiffré.

**Preuves** : `/mnt/data/preuves/2026-08-22_natif_propre` (264 fichiers) et
`/mnt/data/preuves/2026-08-22_politique` — journaux par épisode, relevés, consoles.
