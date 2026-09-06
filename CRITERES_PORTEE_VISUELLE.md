# CRITERES — LA PORTEE DE DESIGNATION VISUELLE

Ecrits AVANT tout chiffre.

## LA PREDICTION, CHIFFREE D AVANCE
Le canal instancie avec les valeurs LUES dans Arma 3 (rayon 1,688 m · sensitivity 6,0)
donne : `side_vue >= 1,5` <=> `vis >= 0,556` avec `vis = min(8440/d² ; 40) * f`.
Donc une portee de designation

> **d_max(f) = 123 * racine(f)**

soit **39 m a f = 0,10 · 62 m a 0,25 · 87 m a 0,50 · 123 m a 1,00**.
C est une prediction NUMERIQUE, posee avant la mesure, et elle peut echouer.

## LA GRANDEUR LUE
`knowsAbout`, qui EST `FadingSideAccuracy()` — la variable meme du seuil de 1,5.
Meme sonde que le banc du canal auditif, deja controlee.

## LE DISPOSITIF
Defenseur en COMBAT/RED, attaquant VISIBLE en partie, **aucun `reveal`** : on veut la
detection naturelle. Fraction de corps reglee par obstacle a 2 m devant l attaquant x
posture (UP / MIDDLE / DOWN), **independamment de la distance**.
Distances balayees : 60, 100, 140, 180, 250, 350 m. 60 s par episode.

## CE QUI FALSIFIE
1. **`knowsAbout >= 1,5` a 350 m en pleine vue** -> la portee n est pas de 123 m, elle est
   fixee par autre chose. Le terme de portee du canal est REFUTE.
2. **La distance de bascule ne suit pas racine(f)** — si le rapport
   d_max(f=1) / d_max(f=0,25) sort de la bande **[1,4 ; 2,8]** (2 attendu), la FORME est
   fausse meme si l ordre de grandeur tombe juste.
3. **Aucune bascule observee nulle part** (tout a 4,00 ou tout a 0) -> le banc ne discrimine
   pas, on ne conclut pas.

## CONTROLES POSITIFS
- **borne haute** : a 60 m en pleine vue, `knowsAbout` doit atteindre 4,00 (cas connu massif,
  deja mesure par le banc du canal auditif) ;
- **borne basse** : l attaquant TOTALEMENT masque doit rester sous 1,5 (deja etabli le meme
  soir, 12/12) — rejoue ici comme temoin negatif.
Si l une des deux tombe, rien n est lu.

## CONDITIONS DE VALIDITE
- la fraction de corps mesuree doit etre **stable et non nulle** dans les bras visibles ;
- au moins **3 fractions distinctes** et **4 distances** peuplees ;
- on rapporte la distance de bascule PAR fraction, pas une moyenne globale.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur le toucher, rien sur la prise, rien sur le transfert.
