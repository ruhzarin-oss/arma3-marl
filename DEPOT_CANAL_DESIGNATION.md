# DEPOT — LE CANAL AUDITIF EST VALIDE SUR ARMA 3, ET SA FORME AUSSI

Criteres : `CRITERES_CANAL_DESIGNATION.md`, ecrits avant tout chiffre, trois issues posees
d avance (falsifiee / tient / indecis).
Banc : `canal_designation.py`. Donnees : `canal_designation.json`.

## LA REVENDICATION
`audibleSideAccuracy = min(audAcc * 0,5 ; 1,4)` contre un seuil de camp a **1,5**
(`Target.cpp:884-936`) : **l ouie seule ne permet jamais d identifier le camp.**

La grandeur lue est `knowsAbout`, qui **EST** `FadingSideAccuracy()`
(`GameStateExtGrp.cpp:1024`) : on lit la variable de l equation, pas un proxy commode.

## LE RESULTAT

| distance | bras A (visible) | bras B (masque, bruyant) |
|---|---|---|
| 15 m | 4,00 | **1,35** |
| 25 m | 4,00 | **1,35** |
| 40 m | 4,00 | **1,35** |
| 60 m | 4,00 | **0,61** |
| 80 m | 4,00 | **0,34** |
| 100 m | 4,00 | **0,00** |

12 episodes valides sur 12 · fraction de corps visible **nulle a chaque releve** dans le
bras B · 20 coups tires par episode · six geometries distinctes.

> ✔ **ELLE TIENT.** L ouie porte l information (jusqu a 1,35) et **ne franchit JAMAIS 1,5**.
> C est la **premiere equation lue chez le cousin que le certificateur CONFIRME**, apres
> deux refutations le meme soir.

## ⭐ ET LA FORME EST CELLE DE LA SOURCE, PAS SEULEMENT LE PLAFOND
La source predit `aud = min(rayon*5000/d^2, ...)`, donc du **1/d²** :
- prediction `(80/60)^2 = 1,78` · mesure `0,61/0,34 = **1,79**` ;
- la constante `a x d^2` vaut **2160 · 2196 · 2176** a 40, 60 et 80 m — **0,9 % d ecart** ;
- plafond mesure **1,35** (la source disait 1,4), mordant sous ~40 m ;
- coupure nette entre 80 et 100 m, **coherente avec `R_VUE_NULLE` = 100 m** du modele
  d alerte mesure le 30/07 par un banc INDEPENDANT.

Loi deposee : **audSide(d) = min(2177 / d² ; 1,35)**, nulle au-dela de 100 m.

## CE QU IL A FALLU CORRIGER — ET C EST LE PLUS INSTRUCTIF
La premiere serie donnait **8 episodes sur 8 a exactement 1,35**. Zero variance : la scene
etait DETERMINISTE (site fixe, distance fixe). **n = 8 y etait n = 1 replique huit fois**, et
ca n aurait etabli qu un point. Le balayage de distance transforme un point en LOI — et c est
lui, pas la repetition, qui a rendu le 1/d².

⭐ **Cliquet : repeter une condition n augmente pas le n. Seule la VARIATION mesure.**

## LES TROIS ISSUES ETAIENT ECRITES, ET LA TROISIEME A FAILLI ARRIVER
Si `knowsAbout` etait reste a **exactement 0** dans le bras B, le banc aurait teste le
SILENCE et non le plafond, et la conclusion aurait ete INDECIS ⟨un zero n est pas un accord⟩.
C est pour ca que l attaquant TIRE : `audibleFire` de la munition vaut **40,0** contre **0,05**
pour l audibilite d un homme qui marche. Et il tire vers le vide, jamais vers le defenseur,
pour ne pas ouvrir la voie de transfert de camp (`sensorFire > 0,8`) — autre mecanisme,
autre question. A 100 m le zero apparait, et c est bien une coupure, pas une panne : les
autres distances portent le signal.

## CE QUI EST POSE
`SIDE_OUIE_MAX = 1.35` (mesure ; la source disait 1,4) et `OUIE_MESUREE` dans `canal_cwr.py`
(sauvegarde `.avantouie`).

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la portee de designation VISUELLE, rien sur la prise, rien sur le transfert.
Ce banc a teste UN plafond et a rendu, en prime, la forme de sa decroissance.
