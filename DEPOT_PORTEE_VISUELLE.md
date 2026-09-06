# DEPOT — LA PORTEE DE DESIGNATION VISUELLE : PREDICTION REFUTEE SUR LES DEUX PLANS

Criteres : `CRITERES_PORTEE_VISUELLE.md`, prediction chiffree posee AVANT la mesure.
Banc : `portee_visuelle.py`. Donnees : `portee_visuelle.json`. 24 conditions, 60 s chacune.

## LA PREDICTION ET LA MESURE
Prediction : **d_max(f) = 123 · racine(f)** — 87 m a f = 0,50 · 123 m a f = 1,00.

| cas | fraction | 60 | 100 | 140 | 180 | 250 | 350 m |
|---|---|---|---|---|---|---|---|
| 0 pleine vue | 1,00 | 4,00 | 4,00 | 4,00 | 4,00 | **3,99** | 0,00 |
| 1 obstacle, debout | 0,60 | 4,00 | 4,00 | 4,00 | 4,00 | **3,99** | 0,00 |
| 2 obstacle, accroupi | 0,40 | 4,00 | 4,00 | 4,00 | 4,00 | 0,00 | 0,00 |
| 3 obstacle, **couche** | 0,71-0,80 | 4,00 | 4,00 | **0,00** | 0,00 | 0,00 | 0,00 |

**Les deux falsificateurs ecrits d avance tombent :**
1. **Le niveau** : la bascule est entre 250 et 350 m, pas a 123 m — **facteur 2,4**.
2. **La forme** : rapport mesure **1,00** contre **1,41** attendu. Entre f = 0,40 et f = 1,00,
   la portee **ne depend PAS de la fraction visible**. Le `vis ∝ rayon/d² · f` du canal est
   refute dans sa forme, pas seulement dans son echelle.

> **Ce qui gouverne la portee, c est la POSTURE, pas la fraction de corps visible.**
> Debout et accroupi : ~300 m. Couche : coupure nette entre 100 et 140 m.

## ⭐ ET LE COUCHE REPRODUIT UN ACQUIS, PAR UN INSTRUMENT NEUF
La coupure du bras 3 entre 100 et 140 m retrouve **`COUCHE_INVISIBLE_M = 120`**, mesuree le
03/08 par le banc de l angle mort (18/18 dans le cone contre 0/26 hors). Deux bancs
independants, deux capteurs differents, meme frontiere. **C est le seul element du canal
visuel qui sorte renforce de cette soiree.**

## ⛔ ET UN CONFLIT QUI DOIT ETRE TRANCHE AVANT D ECRIRE QUOI QUE CE SOIT
`monde_fidele` porte **`R_VUE_NULLE = 100 m`** (« detection 4,00 a 30 m, 1,72 a 60 m, nulle
a 100 m », mesure du 30/07). **Ce banc lit 3,99 a 250 m.** Facteur 2,5 sur un parametre EN
SERVICE. Les conditions different (ici : defenseur COMBAT/RED, attaquant CARELESS immobile
en terrain decouvert, 60 s, aucun `reveal`) — c est peut-etre l explication, ce n est pas une
excuse. **On ne remplace rien tant que les deux bancs n ont pas ete mis face a face.**

## RESERVE PORTEE PAR LA MESURE
La fraction n a couvert que **[0,40 ; 1,00]** : l obstacle a 2 m ne masque pas davantage un
homme debout. La forme n est donc refutee **sur cette bande**, pas en dessous. Et pour le
COUCHE, ma sonde de fraction (cinq points pied->oeil) est mal definie : un corps horizontal
n a pas d etendue verticale — c est probablement pourquoi elle lit 0,71-0,80 sur un homme
que le moteur, lui, cesse de voir. **La sonde de fraction ne vaut que debout.**

## CE QUI SE DEPOSE
Le terme de portee visuelle du canal est **refute**. On ne le remplace pas encore : il faut
d abord trancher le conflit `R_VUE_NULLE`, et une sonde de fraction qui vaille aussi couche.
Rien n est ecrit dans `canal_cwr.py` pour ce point.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur le toucher, rien sur la prise. Ce banc a teste UNE portee.
