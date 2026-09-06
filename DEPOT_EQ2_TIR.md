# DEPOT — L AUTRE MOITIE (loi de tir) INSTANCIEE, ET LE BANC EST BLOQUE SUR UNE LECTURE

Source : `BohemiaInteractive/CWR` — `WhatShootResult` (Target.cpp:1527-1620),
`WhatFireResult` (TargetFire.cpp:1162-1260), `HitProbability` (TargetFire.cpp:69),
`AIGroup::AssignTargets` (AIGroupImpl.cpp:892-1195). RV1, donc HYPOTHESE sur RV3.
Code : `canal_cwr.py` (loi de tir ajoutee), `assault_terrain.py` (6+1 ancres, sauvegardes
`.avanttir` et `.avantetrestriction`), `fumee_tir_cwr.py` (le controle).
ETEINT PAR DEFAUT sous le meme drapeau `canal_cwr`. `MONDE_ARMA` n a pas bouge.

## LES CONTROLES

| | ce qui est verifie | resultat |
|---|---|---|
| P5 | la porte `MinVisibleFire = 0.63` mord de part et d autre du seuil | ✔ 0 a 0,629 · 0,199 a 0,631 |
| P6 | le couvert entre AU CARRE | ✔ rapport 0,490 = 0,70², pas 0,70 |
| P7 | le plancher `hitProbab < 0.05` coupe | ✔ 0,05 x 0,49 = 0,0245 -> zero |
| P8 | le DOUBLON est refuse (`feu_sur_connu`, `feu_de_zone`) | ✔ les deux levent |
| P9 | les durees converties en pas, jamais recopiees | ✔ 10 s -> 3 pas · 15 s -> 5 pas |
| P10 | le verrou de cible tient | **INDECIS** — voir plus bas |
| P11 | la loi change les degats | ✔ rapport **0,019** |

## ⛔ LA CORRECTION QUI COMPTE PLUS QUE LES PASSES
J avais lu la fenetre de 10 s comme une PERMISSION — « le defenseur bat la derniere
position connue ». **C est une RESTRICTION.** `WhatFireResult` recalcule la visibilite
COURANTE et refuse sous 0,63 (l.1203), et la fenetre de 10 s S AJOUTE a ce refus (l.1241) :
les trois conditions sont ET, pas OU. Corollaire dur :

> **Il n existe AUCUN tir VISE sur un homme actuellement cache.** La porte
> `posError > 2*indirectHitRange` le disait deja pour un fusil ; la visibilite courante le
> redit. Donc **le +75 % d Arma 3 ne peut pas venir de la.**

⭐ Cliquet : *une fenetre temporelle dans un moteur est presque toujours une peremption,
pas un droit.* J ai lu un `if (... < t - 10) continue` comme une autorisation.

## LE FALSIFICATEUR, ECRIT
Si la loi est juste, alors dans les 563 000 observations d Arma 3 les morts etiquetes
« jamais vus » sont soit (a) visibles a >= 0,63 au moment du coup et l etiquetage les a
manques, soit (b) tues par une arme A RAYON D EFFET. Une nuit Arma 3 tranche :
rejouer en journalisant `HitPart` avec la visibilite courante du tireur ET le type de
munition. Si des morts subsistent, invisibles ET tues au fusil, **RV3 a change l equation
et on retire la loi.**

## POURQUOI P10 EST INDECIS, ET POURQUOI ON NE DESSERRE PAS
Le verrou ne se mesure que si des cibles sont designees. Sur 32 768 occasions,
**67 couples** (defenseur, pas) ont une cible : la designation est AFFAMEE en amont par les
quatre valeurs de `configFile` non lues (avec les provisoires, `sideAcc >= 1.5` ne tient
qu a moins de 30 m). L instrument ne discrimine pas, donc il ne rend pas de verdict — il
le DIT. Desserrer la porte pour voir le verrou serait regler jusqu a ce que ca passe.

Le rapport de degats **0,019** dit la meme chose : avec les provisoires, le monde est 52 fois
moins letal que la reference. **Ce chiffre ne juge pas la loi, il juge les provisoires.**

## CE QUI DEBLOQUE TOUT, ET CE QUE CA COUTE
Quatre lectures `configFile` dans Arma 3, legales, sans aucune source, quelques minutes :
`radius`/`sizeOf` · `sensitivity` · `sensitivityEar` · `audibleFire`.
Et pour la courbe : `CfgAmmo >> minRange/midRange/maxRange` + leurs `*Probab` — c est la
MEME grandeur que la courbe mesuree le 26/07, donc une contre-verification independante.

## CE QU ON N A PAS INSTANCIE, ET LE REFUS EST LA DECISION
L allocation de RV1 est une economie (`enemyTTL = 60*armor/dammagePerMinute` contre
`groupTTL = 0.6*min(TTL)`). `armor` et `dammagePerMinute` ne sont pas des grandeurs du
gymnase. Seule la consequence observable est instanciee : le VERROU de 15 s. Le
1,8 attaquant par defenseur mesure sur Arma doit EMERGER, il ne se recopie pas.

## CE QUI NE SE CONCLUT PAS ICI
Aucun verdict de fidelite, aucun chiffre de prise. La paire tenue a l ecart reste a jouer.
