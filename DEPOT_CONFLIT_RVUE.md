# DEPOT — POINT 2 : LE CONFLIT `R_VUE_NULLE` EST REEL. TROIS HYPOTHESES MORTES.

Criteres : `CRITERES_*` de la nuit, falsificateur ecrit d avance (« ecart < 0,5 a 100 m ->
le comportement n explique rien »). Banc : `conflit_rvue.py`. Donnees : `conflit_rvue.json`.

## LE CONFLIT
`monde_fidele` porte **`R_VUE_NULLE = 100 m`** — « detection passive 4,00 a 30 m · 1,72 a
60 m · **0,00 a >= 100 m** » (30/07). Mon banc du 03/09 lit **3,99 a 250 m**.

## TROIS EXPLICATIONS TESTEES, TROIS MORTES
1. **La posture** — mort par LECTURE, cout nul : le banc du 30/07 dit « debout et arme ».
2. **La fenetre d observation** — mort par LECTURE : `controle_alerte.py` echantillonne
   **t = 0 a 60 s par pas de 10 s**, exactement comme le mien.
3. **Le comportement de l attaquant** — mort par MESURE, ce banc :

| distance | CARELESS | COMBAT/RED | ecart |
|---|---|---|---|
| 30 m | 4,00 | 4,00 | 0,00 |
| 60 m | 4,00 | 4,00 | 0,00 |
| 100 m | 4,00 | 4,00 | 0,00 |
| 150 m | 4,00 | 4,00 | 0,00 |
| 250 m | 4,00 | 4,00 | 0,00 |

Controle positif passe (30 m, les deux bras a 4,00). Et l explication candidate ne s est
**pas** montree dans la donnee : l attaquant en COMBAT n est **jamais** alle au sol (0 % du
temps dans les dix conditions), il s est **deplace** (jusqu a 69 m). Le mecanisme suppose
n existait pas.

## ⚠️ ET MON PROPRE BANC N A AUCUNE DYNAMIQUE
Il lit **4,00 partout**, y compris a 60 m ou le 30/07 lit **1,72**. Un banc sature ne peut
pas trancher : il dit seulement « au-dessus du plafond ». **Les deux instruments different
donc AVANT la question posee.**

## LE CANDIDAT SUIVANT, ET IL EST UNIQUE MAINTENANT
Le **SITE**. Mon banc est pose sur le banc plat certifie d Altis (23000,17400), choisi pour
etre degage ; celui du 30/07 pose ses hommes ailleurs. Sur terrain roulant, un homme a 100 m
est masque par le relief — et nous avons mesure ce soir meme que la fraction de corps visible
gouverne le toucher. C est la derniere variable libre entre les deux bancs.

⭐ **Cliquet : quand deux bancs se contredisent, la variable coupable se cherche par LECTURE
d abord — deux hypotheses sur trois sont mortes ce soir sans consommer une seule minute
d Arma.** La troisieme a coute onze minutes.

## CE QUI EST DECIDE
`R_VUE_NULLE = 100 m` **reste en service, non modifie**. On ne remplace pas un parametre
mesure par un autre tant que le desaccord n est pas explique. Le test du SITE est inscrit en
banc de RESERVE de la nuit : il se joue si un bloc de N1 tombe.

## CE QUI NE SE CONCLUT PAS ICI
Rien n autorise a citer 250 m comme portee de detection : ce banc est sature, donc il ne
mesure pas une portee, il constate un depassement.
