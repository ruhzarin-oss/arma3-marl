# DEPOT — LA PORTE `MinVisibleFire` EST FALSIFIEE PAR ARMA 3, ET RETIREE

Criteres : `CRITERES_FALSIFICATEUR_VUE.md`, ecrits AVANT tout chiffre, seuil **10 %**.
Banc : `falsificateur_vue.py`. Donnees : `falsificateur_vue.json`.

## LA REVENDICATION TESTEE
Lue dans CWR (`Target.cpp:1604`, `TargetFire.cpp:1203`) et apparemment confirmee par la
config d Arma 3 (`indirectHitRange` = 0,0) :
> Il n existe aucun tir VISE sur un homme dont la visibilite courante est < 0,63.

## LA MESURE
3 episodes 8 contre 8 sur Altis, munition qualifiee a la source (`indirectHitRange` = 0,0 ·
`hit` = 10,0), **249 impacts dont 237 sur victime VIVANTE**.

| instrument | sous 0,63 | mediane |
|---|---|---|
| rayon oeil-a-oeil | 70 / 237 = **29,5 %** | 0,865 |
| **fraction de corps** (5 points pied→oeil) | 88 / 237 = **37,1 %** | 1,000 |

**Seuil pre-inscrit 10 %. Mesure 37,1 % — 3,7 fois le seuil.** Les deux instruments
concordent en signe et en ordre de grandeur.

## LES TROIS CONTROLES POSITIFS, JOUES AVANT
1. `checkVisibility` a nu a 50 m = **1,000** · avec mur interpose = **0,000**. La sonde separe.
2. Ecouteur `HitPart` sur cible INVULNERABLE a 40 m : impacts captes > 0. Il n est pas aveugle.
3. Munition lue A LA SOURCE (chargeur en main), pas supposee.

## CE QU IL A FALLU REPARER, ET CE QUE CHAQUE PANNE ENSEIGNE
- `AGLToASL (aimingPosition _x)` fait echouer le bloc **en silence** — echelle de ping :
  `eyePos/eyePos` rend 1, la variante ne rend RIEN. On lit oeil a oeil.
- `true + true` : SQF n additionne pas deux booleens. Le controle ne repondait pas.
- `_this select 10` supposait 11 champs : **8 morts, 0 impact capte**. On emet `count` et on
  LIT la forme au lieu de la deviner.
- Le lieu du controle etait tire au hasard : deux hommes a 50 m masques par le relief, temoin +
  a 0,000. **Un controle positif se pose sur un cas dont la reponse est connue** — banc plat
  certifie d Altis (23000,17400), celui de la courbe du 26/07.
- ⚠️ Le premier instrument etait un RAYON oeil-a-oeil alors que le moteur emploie une
  FRACTION DE CORPS. Le seuil 0,63 appartient a la seconde grandeur. Corrige avant de conclure ;
  les deux sont rendus cote a cote, et leur accord est ce qui rend le verdict lisible.

## ⭐ CE QUE LE VERDICT REND AU PROJET
Le « corollaire dur » deduit de la source — *le +75 % ne peut pas venir de tirs sur des hommes
caches* — est **REFUTE par le certificateur**. On EST touche au fusil en etant cache dans
Arma 3. Donc `feu_sur_connu` et le feu sur position connue redeviennent des mecanismes
legitimes A MESURER, au lieu d etre interdits par une lecture de RV1.

⭐ **Cliquet : une equation lue chez le cousin reste une HYPOTHESE meme quand une constante de
config du certificateur semble la confirmer.** `indirectHitRange` = 0 etait VRAI, et
n impliquait pas ce qu on lui faisait dire.

## CE QUI EST RETIRE, ET CE QUI RESTE
RETIRE : `PORTE_VISIBLE = False` dans `canal_cwr.py` (sauvegarde `.avantretrait`). La remettre
a `True` exige une mesure NEUVE. Le test P5 a ete RETOURNE : il verifie desormais le retrait.

**NON teste par ce banc, donc toujours en service** : `visible ** 2`, le plancher a 0,05, les
horloges de 10 s et 15 s, le verrou de cible, et tout le canal de designation de l equation 1.
Ce banc n a teste QU UNE porte — ne pas etendre le verdict a ce qu il n a pas mesure.

## RESERVES
n = 237 sur 3 episodes, un seul type d unite et une seule carte. La visibilite est relevee
A L IMPACT (temps de vol 0,06 s a 50 m, 0,24 s a 200 m) : c est pourquoi le seuil etait a
10 % et non a 0 %. A 37,1 %, aucune de ces reserves ne renverse le signe.
