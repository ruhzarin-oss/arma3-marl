# DEPOT — LES QUATRE LECTURES `configFile` SONT FAITES (03/09/2026)

Serveur Altis, instance 0, pont natif 5801 (tache planifiee `HMT_Arma` — un `setsid`
lance depuis ssh meurt). Sondes : `lire_config_arma.py`, `lire_config_arma2.py`.
Sorties : `config_arma3_canal.json`, `config_arma3_canal2.json`.
Constantes installees : `canal_cwr.ARMA3`, via `constantes_arma3()`.

## LA SONDE D ABORD (regle 16)
Chaque lecture emet `isNumber` PUIS la valeur : `getNumber` rend 0 pour « absent » comme
pour « vaut zero ». Deux temoins encadrent la serie — temoin + `CfgAmmo >> hit` = 10,000
(existe, non nul) et temoin - chemin bidon (isNumber = 0). **La sonde discrimine.**

## LES QUATRE VALEURS

| | valeur | ou | provisoire |
|---|---|---|---|
| `rayon_m` | **1,688 m** | `boundingBoxReal` 1,600 x 2,200 x 2,000 sur un homme POSE | 0,6 (x2,8) |
| `sensibilite` | **6,0** | `CfgVehicles >> B_Soldier_F >> sensitivity` | 1,0 (x6) |
| `sensibilite_oreille` | **0,125** | `... >> sensitivityEar` | 1,0 (/8) |
| `audible_cible` | **0,05** | `... >> audible` | 1,0 (/20) |

⚠️ **`radius` est ABSENT de CfgVehicles, et `sizeOf` rend 0,000 sur un serveur headless.**
Il a fallu POSER un homme et lire sa boite englobante — juger l ACTE, pas la table. Un
`sizeOf` lu sans unite aurait donne un rayon nul et un canal muet, sans une seule erreur.

⚠️ **PIEGE EVITE.** `aiAudible = ai->Audible()` (Target.cpp:822) est l audibilite de
l ENTITE — `audible` = **0,05** — et non `audibleFire` de la munition = **40,0**, qui
alimente l autre terme (le tir qui trahit). Un facteur 800 separe les deux.

## ⭐ CE QUE LA CONFIG CONFIRME TOUTE SEULE
`CfgAmmo >> B_65x39_Caseless >> indirectHitRange` = **0,0000**.
Donc `posError > 2 x 0` : **toute erreur de position ecarte le fusil.** La consequence
tiree de RV1 — aucun tir VISE sur un homme dont la position n est connue qu approximativement
— est confirmee par la config d ARMA 3 elle-meme, pas par le cousin.

## ⛔ LE CONTRE-TEST DE LA COURBE ECHOUE, ET C EST UN RESULTAT
La courbe n est pas dans `CfgAmmo` : elle est dans les **MODES** de l arme. `arifle_MX_F`
en a **six** — `Single`, `FullAuto`, `fullauto_medium`, `single_medium_optics1`,
`single_far_optics2`, `ACE_Burst_far` — et `Single` (120-400 m) plus `FullAuto` (0-30 m)
laissaient un trou de 30 a 120 m qui se remplit avec les autres.

Formule verifiee dans la source (`Weapons.cpp:130-134`, « premultiply with probabilities ») :
interpolation lineaire par morceaux entre les trois points, zero hors [minRange, maxRange].

| distance | config (meilleur mode) | mesure du 26/07 | ecart |
|---|---|---|---|
| 25 m | 0,518 (`fullauto_medium`) | 0,75 | −0,23 |
| 50 m | 0,609 | 0,57 | +0,04 |
| 75 m | 0,700 | 0,41 | **+0,29** |
| 100 m | 0,483 | 0,30 | +0,18 |
| 150 m | 0,667 (`Single`) | 0,24 | **+0,43** |
| 200 m | 0,611 | 0,26 | **+0,35** |

> **Ce ne sont PAS la meme grandeur.** Le `*Probab` de la config est le SCORE que l IA
> utilise pour choisir un mode et decider si elle tire ; la courbe du 26/07 est le
> RESULTAT balistique mesure impact par impact. La contre-verification gratuite annoncee
> n existe pas. **La courbe mesuree reste la loi de degats du gymnase** ; la config ne
> vaudrait que si l on modelisait le choix de mode, ce que le gymnase ne fait pas.

⭐ Cliquet : *deux tables qui portent le meme nom ne mesurent pas forcement la meme chose.*

## CE QUE LES VRAIES VALEURS CHANGENT AU BANC

| | provisoire | mesure |
|---|---|---|
| portee de designation (efrac 0,10 / 0,50 / 1,00) | 9 / 21 / 30 m | **38 / 87 / 123 m** |
| P10 verrou de cible | INDECIS (67 couples) | **PASSE** — 8 251 couples, 22,7 % de changements avec verrou contre **29,5 %** sans |
| P11 degats contre la reference | 0,019 (monde mort) | **0,733** |
| P1 designe sans etre vu | 0 | 9 |

Les onze controles positifs passent. **Aucun verdict de fidelite n en sort** : la paire
tenue a l ecart et le contraste contre les +75 % restent une nuit Arma a jouer.
