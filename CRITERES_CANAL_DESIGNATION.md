# CRITERES — LE CANAL DE DESIGNATION (equation 1) SUR ARMA 3

Ecrits AVANT tout chiffre.

## LA REVENDICATION
Lue dans CWR (`Target.cpp:884-936`) :
`audibleSideAccuracy = min(audAcc * 0,5 ; 1,4)` contre un seuil de reconnaissance de camp
a **1,5**. Donc :
> **L OUIE SEULE NE PERMET JAMAIS D IDENTIFIER LE CAMP.** Un homme entendu mais JAMAIS VU
> peut etre su present, il ne peut pas etre reconnu ennemi — donc pas designe comme cible.

## LA GRANDEUR LISIBLE, ET POURQUOI C EST LA BONNE
`knowsAbout` rend `FadingSideAccuracy()` (`GameStateExtGrp.cpp:1024`, confirme le 31/08) :
c est **exactement** la grandeur que le seuil de 1,5 gouverne, et elle est portee par le
GROUPE. On ne lit donc pas un proxy commode : on lit la variable meme de l equation.

## LE DISPOSITIF — DEUX BRAS
- **BRAS A, controle positif** : attaquant VISIBLE a 40 m. `knowsAbout` doit franchir 1,5.
  C est le cas ou le phenomene est connu massif ; s il ne franchit pas, la sonde ne
  discrimine pas et **rien n est lu**.
- **BRAS B, le test** : attaquant TOTALEMENT MASQUE (fraction de corps visible = 0 sur toute
  la duree, verifiee a chaque releve) et BRUYANT — il tire, en visant le vide, jamais vers le
  defenseur. `audibleFire` de la munition vaut 40,0, contre 0,05 pour l audibilite d un homme
  qui marche : c est le seul moyen d avoir un signal auditif qui ne soit pas du bruit de fond.
  Il ne tire PAS sur le defenseur, pour ne pas ouvrir la voie de transfert de camp
  (`sensorFire > 0,8` fait heriter la precision de la cible visee — autre mecanisme, autre
  question).

## LES TROIS ISSUES, ECRITES D AVANCE
1. `knowsAbout` du bras B **atteint 1,5** alors que la fraction visible est restee nulle
   -> **LA REVENDICATION EST FALSIFIEE**, le plafond de 1,4 ne tient pas dans RV3. On retire.
2. `knowsAbout` du bras B reste **strictement entre 0 et 1,5** -> **elle TIENT** : l ouie
   porte l information et ne nomme pas le camp.
3. `knowsAbout` du bras B reste **exactement 0** -> **INDECIS**. ⟨un zero n est pas un accord⟩
   Le canal auditif n a rien transmis du tout : le banc n a pas teste le plafond, il a teste
   le silence. On ne conclut pas, on le dit.

## CONDITIONS DE VALIDITE
- fraction visible du bras B **= 0 a chaque releve** ; un seul releve non nul et l episode
  est ECARTE, pas rattrape ;
- coups tires du bras B **> 0** ; sinon il n y a pas de signal a plafonner ;
- au moins **6 episodes par bras**.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la portee de designation, rien sur la prise, rien sur le transfert.
Ce banc teste UN plafond.
