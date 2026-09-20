# Calibration de l'adversaire — ce que l'Oracle punit tout seul

*20/09/2026. **Calibration, pas un verdict.** Lecture de `ORACLE-P2-19-09` sur des issues d'**adversaire**
(compromission, pertes, abandon), et non sur l'effet du choix de traversée : cette campagne est close, et sa
question ne sera pas lue (amendement 3 de `CRITERES_ORACLE_P2.md`). 122 épisodes, 61 par bras, règle de
déduplication inchangée (premier épisode accepté de chaque case). IC 95 % par 10 000 rééchantillonnages appariés
par monde, graine 20260920.*

| issue | Oracle | témoin | écart | IC 95 % |
|---|---|---|---|---|
| compromis en phase 2 | **0,279** | 0,082 | **+0,197** | [+0,056 ; +0,327] |
| au moins un homme perdu | **0,180** | 0,066 | **+0,115** | [+0,026 ; +0,198] |
| pris avant la décision | 0,082 | 0,016 | +0,066 | [+0,000 ; +0,156] |
| alarme donnée | 0,066 | 0,033 | +0,033 | [−0,031 ; +0,109] |
| **phase discrète** (issue primaire) | **0,721** | 0,918 | **−0,197** | [−0,327 ; −0,056] |

**À son budget normal, sans qu'on lui amène personne, l'Oracle multiplie la compromission par 3,4** et fait tomber
le taux de réussite de 92 % à 72 %. Trois écarts sur cinq excluent zéro.

## Ce que ça dit pour la suite

1. **Le plafond est cassé.** À 91,8 %, aucun choix ne pouvait se voir : il n'y avait plus de place au-dessus. À
   72 %, la variance de l'issue est **2,7 fois plus grande** (0,202 contre 0,074). Un effet de 10-15 points
   redevient mesurable avec le corpus qu'on sait jouer.
2. **Le budget n'est pas le levier.** L'Oracle ne dépense que **3,1 ordres sur 6** : il lui en reste presque la
   moitié à la fin. Monter B ne changera donc pas grand-chose. Ce qui le bride, c'est le **nombre d'occasions de
   décider** — période δ = 60 s — et non sa provision.
3. **Le monde reste très inégal.** Compromission Oracle contre témoin, par monde : 7 → 0,62 / 0,17 ; 8 → 0,50 /
   0,12 ; 6 → 0,38 / 0,00 ; mais 5 → 0,00 / 0,00 et 12 → 0,00 / 0,12. Deux mondes sur huit ne donnent aucune prise
   à l'adversaire. À vérifier avant d'y dimensionner une campagne.

## Ce que ça ne dit pas

Rien sur l'utilité de l'Oracle pour l'agent, rien sur le choix de traversée, et rien qui puisse servir de résultat :
c'est une mesure d'instrument, faite pour régler la manette avant de payer une campagne.
