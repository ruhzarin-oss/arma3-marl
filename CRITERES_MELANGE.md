# CRITERES — LA COURBE EST-ELLE UN MELANGE ? (test du RANG, cible INVULNERABLE)

Ecrits AVANT tout chiffre.

## POURQUOI CE BANC EXISTE
Le banc `degat_par_impact` a rendu `p_touche` decroissant avec le rang du coup :
0,286 (coups 1-10) · 0,209 (11-30) · 0,083 (31-80), IC disjoints. Si c est vrai de la
courbe, **la courbe est un melange et ne se transporte pas**.

**MAIS ce banc a un biais de composition connu** : sa cible est VULNERABLE. Un duel ou le
tireur est bon tue vite et ne fournit que des coups de rang 1-10 ; les duels qui trainent —
donc les MAUVAIS duels — dominent seuls les rangs eleves. La decroissance peut donc etre un
effet de SURVIE et non une decroissance reelle.

**On ne leve pas la suspension par un argument. On la tranche par une mesure.**

## LE DISPOSITIF — celui dont la courbe est ISSUE
Cible **INVULNERABLE**, comme pour la courbe : chaque duel va jusqu au bout du bloc, la
composition des rangs ne bouge pas. 100 m, debout, meme capteur repare (un impact par
PROJECTILE, source appariee). **On enregistre l identifiant de duel** — faute payee au banc
precedent, ou je l avais jete et ou je n ai donc PAS PU trancher.

## LES DEUX LECTURES, ET LA SECONDE EST LA VRAIE
1. **Entre duels** : `p_touche` par case de rang, tous duels confondus. C est la lecture qui
   a declenche la suspension.
2. **DANS le duel** : pour les seuls duels qui atteignent le rang 31, comparer leur propre
   `p_touche` en rangs 1-10 contre 31-80. **Composition identique par construction.**

## CE QUI TRANCHE, ECRIT D AVANCE
- **La decroissance persiste DANS le duel** (IC disjoints) -> elle est REELLE. La courbe est
  un melange, elle ne se transporte pas, et l allumage d ÉQ. 1 reste SUSPENDU. Il faudra
  alors mesurer la courbe a rang borne, ou la parametrer par le rang.
- **La decroissance disparait DANS le duel** (IC recouvrants) -> c etait un biais de
  composition du banc a cible vulnerable. La courbe n est pas un melange, la suspension est
  LEVEE, et le banc precedent est marque comme portant ce biais.
- **Moins de 10 duels atteignent le rang 31, ou moins de 100 balles dans une case** -> le
  banc ne discrimine pas, la suspension RESTE par defaut. Un doute ne se resout pas en
  faveur de ce qu on veut.

## CONTROLE POSITIF
`p_touche` global a 100 m debout doit retomber dans l IC deja etabli sur ce meme capteur :
0,402 [0,371 ; 0,435] et 0,383 [0,335 ; 0,434]. Hors de la, l instrument a bouge et rien
n est lu.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la valeur de la courbe, rien sur ÉQ. 1. Ce banc dit seulement si la courbe est un
melange.
