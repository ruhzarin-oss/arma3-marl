# DEPOT — EQUATION 1 INSTANCIEE, ET CE QU ELLE NE FAIT PAS

Criteres : `CRITERES_EQ1_CANAL.md`, ecrits avant tout chiffre.
Source : `BohemiaInteractive/CWR`, `engine/Poseidon/World/Detection/Target.cpp` (RV1, GPL).
Code : `canal_cwr.py` (les equations seules), `assault_terrain.py` (branchement, 6 ancres,
sauvegarde `.avantcanal`), `fumee_canal_cwr.py` (le controle positif).
ETEINT PAR DEFAUT. `MONDE_ARMA` n a pas bouge : la batterie gelee n est pas touchee.

## LES QUATRE CONTROLES PASSENT

| | ce qui est verifie | resultat |
|---|---|---|
| P4 | refuse de tourner sans les valeurs de config d Arma 3 | ✔ il leve |
| P3a | l ouie ne peut PAS designer, par le calcul : `min(acc*0.5, 1.4) < 1.5` | ✔ |
| P3b | efrac = 0, de 5 a 200 m : `acc_ouie` de 4,00 a 0,006, `designe` = False partout | ✔ |
| P2 | le couvert ATTENUE : portee de designation 9 · 15 · 21 · 25 · 30 m pour efrac 0,10 · 0,25 · 0,50 · 0,75 · 1,00 ; a 10 m `side` 1,13 (cache) contre 4,00 (decouvert) | ✔ continu |
| P1 | le canal change des decisions : 16 942 sur 24 576 | ✔ non inerte |

## ⛔ CE QUE LE CONTROLE REVELE, ET QUI COMPTE PLUS QUE LES QUATRE PASSES

**« designe SANS etre vu geometriquement : 0 ».** Dans les deux sens, un seul est peuple :
le canal est PLUS EXIGEANT que l ancienne porte (16 942 designations perdues), et il n en
ajoute AUCUNE. **L equation 1 ne leve donc pas l interrupteur.** Elle remplace une porte
binaire par une porte continue A L INTERIEUR de la bande deja vue — rien de plus.

La raison est dans la source elle-meme : `vis = fog · sizeVis · landVis`, donc
`landVis = 0 -> vis = 0`. Chez RV1 non plus la VUE n atteint pas un homme jamais vu.
Ce qui rend les jamais-vus mortels dans Arma 3 (+75 %, 563 000 obs) est l autre moitie :
l ouie eleve `accuracy` et pose une position connue avec erreur `spotError = 0.8·d`, et le
defenseur bat ensuite CETTE position. **Le passage « position connue avec erreur ->
probabilite de toucher » n est PAS dans `Target.cpp`** — il vit dans le code de tir
(`TargetFire.cpp`, 2076 lignes, telecharge, non lu). Il n a pas ete invente.

> **Verdict : l equation 1 est instanciee et active, mais elle est la MOITIE d un
> mecanisme. Seule, elle rend le gymnase MOINS letal, pas plus fidele.**

## LA CALIBRATION EST PORTEE PAR CE QUI N EST PAS MESURE
Avec les valeurs provisoires (rayon 0,6 m, sensibilites 1,0), un homme entierement
decouvert n est designe que **jusqu a 30 m** — alors que la courbe de toucher mesuree
porte jusqu a 200 m. C est pour ca que le module REFUSE de tourner sans les quatre valeurs
de config, et qu aucun banc ne peut lire un chiffre produit avec les provisoires.

A lire dans Arma 3, `configFile`, legal, sans aucune source :
`radius`/`sizeOf` (GetRadius du modele) · `sensitivity` · `sensitivityEar` · `audibleFire`.

## CE QUI NE SE CONCLUT PAS ICI
Aucun verdict de fidelite. Le contraste vu / pas-vu contre les +75 %, et la paire tenue a
l ecart, restent une nuit Arma a part. Rien de cette livraison n autorise a citer un chiffre
de prise.
