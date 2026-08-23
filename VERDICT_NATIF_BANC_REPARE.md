# NATIF SUR LE BANC RÉPARÉ = **30,7 %** — sa moitié était empruntée au banc

**23/08/2026.** Prédicat `DEPOT_NATIF.md`, écrit le **16/08 avant tout épisode**, inchangé.
Lecteur **déposé** (`lire_natif.lire`), inchangé. Banc réparé en `a98dc5d`.
Nuit `HMT_NuitDeux`, 22 h 00 → 06 h 57, dossier `/mnt/data/natif2`.

| | passe 1 | passe 2 | écart | **total** |
|---|---|---|---|---|
| **NATIF, banc réparé** | 27,7 % (n=65) | 33,9 % (n=62) | **6,2** ✓ | **30,7 %** · n=127 · IC95 **[22,7 ; 38,7]** |
| natif, banc cassé (retiré) | 56,1 % | 63,2 % | 7,0 | 59,6 % · n=114 · IC95 [50,6 ; 68,7] |

> ## Les deux intervalles ne se recouvrent pas.
> **L'IA native perd la moitié de sa performance dès qu'on lui retire ce que le banc lui
> donnait** : un quart de mondes sans adversaire, et 29 mètres d'avance pris pendant le prévol.

## La nuit la plus propre du projet

| | banc cassé | **banc réparé** |
|---|---|---|
| défenseurs vivants au départ | 2,30 en moyenne | **4,00 sur 134 épisodes** |
| mondes sans aucun adversaire | 26 sur 114 | **0** |
| escouades mortes avant le départ | 14 | **0** |
| épisodes écartés après coup | 14 | **0** |
| prévols refusés | 11 | **7** (la porte, pas une panne) |
| coups attaquants, médiane | 77 et 72 | **150 et 144** |

**127 épisodes joués, 127 lus, aucun jeté.** Deux fois plus de balles tirées : le banc mesure
enfin un combat.

## La condition qui a failli tout bloquer

Le contrôle du monde — *« le natif BOUGE, > 1 m/pas »* — rend **1,12** puis **1,31**, contre
2,27 et 2,33 sur le banc cassé. **Il passe, de peu.** C'est cohérent et non alarmant : le
natif rampe parce qu'il est sous le feu de quatre défenseurs vivants au lieu de marcher dans
un monde à demi vide. Mais la marge est mince et doit être surveillée, **sans jamais toucher
au seuil** : il est déposé.

## Ce qu'il fait vraiment

| pas | vivants | distance |
|---|---|---|
| 0 | 4,00 | 158 m |
| 5 | **3,46** | 154 m |
| 30 | 2,82 | 112 m |
| 59 | 2,48 | 103 m |

**Il perd un demi-homme dans les cinq premiers pas, à plus de 150 m**, puis progresse par
petits pas. Seules 2 escouades sur 65 sont détruites avant le pas 30 : il ne meurt pas,
**il rampe**.

## ⚠️ Ce que ça ne dit pas

**Rien sur la politique** tant que sa nuit n'est pas finie (en cours, 52 épisodes sur 134).
La comparaison ne se fait qu'une fois les deux bras complets, et elle a son prédicat.

⚠️ **Une vérification reste indirecte** : le marqueur de l'ordre du pas 0 passe par la
socket et n'apparaît dans aucun fichier. Deux indices convergent — le même canal d'envoi
fonctionne démontrablement avant le prévol, et rien d'autre ne peut faire avancer le natif
de 55 m puisque aucun ordre de vitesse ne lui est envoyé. **À rendre direct après la nuit.**
