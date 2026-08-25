# PRÉ-INSCRIPTION — LE RASTER CONTRE LES DOUZE NOMBRES

**Déposée le 25/08/2026, AVANT le premier entraînement.** Aucun chiffre de résultat n'existe
au moment où ce fichier est écrit. Le hachage de ce fichier est imprimé par le banc lui-même.

## LA QUESTION

L'observation de l'agent est aujourd'hui **12 nombres résumés** (position, direction du but,
vivant, pente, distance au bâti, ligne de vue, distance au plus proche). Mesuré sur 1,35 M de
situations de football : **les nombres résumés SATURENT** (0,619 → 0,623 de 5 k à 16 k paires,
sous le bruit) là où **la géométrie brute ne sature pas** (0,644 → 0,677), pour un écart de
+4,5 pts au-dessus du comptage seul.

Cette mesure n'a **jamais été rejouée dans ce monde-ci**. Elle dit « ne résume pas la
géométrie ». On la met à l'épreuve ici.

## L'INSTRUMENT

**Le raster** : une image égocentrique **6 × 24 × 24**, l'objectif toujours EN HAUT,
300 m de côté, 12,5 m par cellule. Canaux : `couvert`, `pente`, `bâti`, `danger`,
`ennemis`, `alliés`. Le canal `danger` est la transcription fidèle de `_champ_danger` du
dépôt, où les K directions sur un cercle deviennent les K×K cellules.

**La fenêtre a été DIMENSIONNÉE, pas choisie** (sonde 2, doctrine frontale du dépôt,
256 environnements, graine 11) : part des défenseurs vivants dans la fenêtre au pas 0 —
span 120 : 0,000 · 180 : 0,000 · 240 : 0,014 · **300 : 0,978**. Seule 300 montre le
défenseur AU DÉPART, c'est-à-dire au moment exact où le défaut connu se produit
(« à 170 m, rien dans son observation ne lui dit qu'il paie déjà »).

**Les six canaux sont vérifiés VIVANTS** au pas 7 (78 % de l'escouade encore debout) :
intra-image 0,343 · 0,197 · 0,031 · 0,095 · 0,102 · 0,075. Aucun canal constant.

## LES QUATRE BRAS — mêmes graines, même monde, même budget

| bras | observation | lecteur | ce qu'il teste |
|---|---|---|---|
| **A** | les 12 nombres | MLP 128×2 | la référence du dépôt |
| **B** | 12 nombres + raster | CNN + MLP | **la revendication** |
| **C** | 12 nombres + raster **BROUILLÉ** | CNN + MLP | contrôle GÉOMÉTRIE |
| **D** | 12 nombres + raster **APLATI** | MLP seul | contrôle CAPACITÉ |

**Le brouilleur** applique une permutation spatiale FIXE, indépendante par canal. Il préserve
**exactement** l'histogramme de chaque canal et détruit l'arrangement. Vérifié : la corrélation
à la cellule voisine — la vraie mesure de la géométrie locale — tombe de 0,747 à 0,009 sur
`danger`, de 0,592 à 0,004 sur `bâti`. Mêmes valeurs, autres places.

## LES PORTES — écrites avant les données

**G1 — LA PORTE.** Sur `GRAINES_TEST` (101-106, jamais vues), la **médiane de B sur 3 graines
d'entraînement** doit dépasser celle de A, **et les deux étendues ne doivent pas se recouvrir**.
Si elles se recouvrent : **VERDICT ILLISIBLE**, jamais « verdict favorable masqué par le bruit ».

**G2 — CONTRÔLE GÉOMÉTRIE.** Si la médiane de **C** tombe dans l'étendue de **B**, alors le
réseau ne lit pas la géométrie mais des statistiques, et **G1 ne veut rien dire quel que soit
son résultat**. G2 se lit AVANT G1.

**G3 — CONTRÔLE CAPACITÉ.** Si **D ≈ B**, le gain vient des nombres supplémentaires, pas de la
convolution. Les deux lectures sont déclarées d'avance :
  · D ≈ A  et  B > A → **c'est la CONVOLUTION qui paie** (revendication forte) ;
  · D ≈ B  et  B > A → **c'est le CONTENU qui paie**, la lecture spatiale est accessoire
    (revendication faible, mais recevable — et alors le raster n'a pas besoin d'un CNN).

**G4 — NE PAS SE TERRER.** `metres_tenus` de B ≥ `metres_tenus` de A. Un gain obtenu en
restant en arrière n'est pas un gain. On lit `metres_tenus` (position TENUE) et jamais
`metres` (point le plus profond jamais atteint), conformément à la revue du 17/08.

**G5 — LA LOTERIE EST ATTENDUE.** Il est ACQUIS que ce gymnase donne 49,6 % ou 3,3 % selon
la graine. Trois graines par bras est un MINIMUM, l'étendue complète est publiée, et
**aucune moyenne n'est citée sans son étendue**. Une graine unique ne sera jamais citée.

## CE QUE CE BANC NE PROUVERA PAS

C'est un résultat de **GYMNASE**. Il ne dit rien d'Arma tant qu'il n'y est pas certifié.
Si B passe, la ligne rejoint le registre des sursitaires jusqu'à cette certification.

## DÉCODEUR

Échantillonnage, à l'entraînement comme au jugement — décision du 24/08 : figer à l'argmax
une politique optimisée en stochastique était une hypothèse héritée, et elle donnait
3,3 à 51,1 % selon la graine contre 31,5 à 42,3 % en laissant hésiter.
