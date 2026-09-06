# DEPOT — L EXPOSANT DU COUVERT EST MESURE SUR ARMA 3, ET IL N EST PAS 2

Criteres : `CRITERES_LOI_VISIBILITE.md`, ecrits avant tout chiffre.
Banc : `loi_visibilite.py`. Donnees : `loi_visibilite.json`.

## LA MESURE
24 sessions, 16 duels simultanes, 100 m, tireur ET cible invulnerables, couvert partiel
FABRIQUE (obstacle a 2 m devant la cible x posture UP/MIDDLE/DOWN).
**18 181 coups tires · 7 924 impacts · 16 conditions**, fraction de corps relevee AU DEPART
DU COUP sur cinq points pied->oeil.

| case de visibilite | coups | impacts | P(toucher) |
|---|---|---|---|
| [0,2 ; 0,4[ | 1 198 | 299 | 0,250 |
| [0,4 ; 0,6[ | 9 247 | 3 752 | 0,406 |
| [0,6 ; 0,8[ | 5 928 | 2 862 | 0,483 |
| [0,8 ; 1,0] | 1 808 | 1 011 | 0,559 |

> **Pente log-log ponderee sur les 16 duels : a = 0,72 · IC95 bootstrap [0,39 ; 0,97].**
> **2 est tres largement hors de l intervalle.** A f = 0,50 : RV1 punit x0,25, la mesure x0,61.
> Le carre SUR-PUNIT le couvert d un facteur 2,4.

## ⛔ LE CONTROLE POSITIF DE NIVEAU N EST PAS PASSE — ET ON NE L A PAS ELARGI
En pleine vue a 100 m le banc lit **0,559**, hors de la bande **0,15-0,50** tiree de la courbe
du 26/07. On ne relache pas la bande : on nomme la cause. Le dépôt du projet la contient deja —
sur le meme phenomene, `HitPart` sur cible invulnerable lit **48 %** la ou la courbe tabule
**30 %**. **Les deux instruments ne comptent pas pareil**, et c est un ecart connu, pas une
surprise.

Ce que ca autorise, et rien de plus : **l exposant est une PENTE log-log, donc invariant par
un facteur multiplicatif constant de comptage.** Un biais de niveau ne le deplace pas. Le
NIVEAU, lui, n est pas lu ici et reste porte par `_p_balle`, la courbe deja mesuree.

⭐ **Cliquet : quand un controle de NIVEAU echoue, on peut encore lire une PENTE — a condition
de dire lequel des deux on prend, et pourquoi.**

## CE QU IL A FALLU REPARER, ET CE QUE CHAQUE PANNE ENSEIGNE
1. **Le tireur ne tirait pas** : `disableAI "MOVE"` au lieu de la recette prouvee
   (`disableAI "PATH"` + `AUTOTARGET` coupe + `setUnitPos "UP"`). Un compteur BRUT pose sur
   `Fired` avant tout calcul a permis de dire « le monde ne tire pas » et non « la sonde ment ».
2. **Une balle comptait pour plusieurs impacts** : `_this` de `HitPart` liste toutes les
   PARTIES touchees par UN projectile. Taux a 0,615 au lieu de ~0,32. Le depot connaissait la
   faute pour `HandleDamage` (1,9 appel par balle) — c est la meme, un cran plus loin, et
   **c est le controle positif qui l a attrapee**.
3. **Le couvert partiel ne se trouve pas, il se fabrique** : le terrain d Altis ne rend que du
   tout-ou-rien (2 cases sur 5, aucune au milieu). Obstacle pose + posture variee -> quatre
   cases peuplees. ⭐ *Un facteur qu on veut mesurer se REGLE, il ne s echantillonne pas.*

## DOMAINE DE VALIDITE, ECRIT AVEC LE RESULTAT
f entre **0,29 et 0,90** · une seule distance (**100 m**) · un seul type d unite · une carte.
Rien n autorise a extrapoler vers f -> 0. La dispersion a f ≈ 0,50 (0,289 a 0,542 selon le
duel) dit qu un autre facteur joue encore : la fraction n explique pas tout.

## CE QUI EST POSE
`VIS_EXPOSANT = 0.72` dans `canal_cwr.py` (sauvegarde `.avantexposant`), avec son IC et son
domaine. Le `visible ** 2` de RV1 rejoint la porte `MinVisibleFire` : **deuxieme equation
importee du cousin refutee par le certificateur en une soiree.**

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la prise, rien sur le transfert, rien sur le canal de designation de l equation 1.
