#!/usr/bin/env python3
"""canal_cwr — EQUATION 1, INSTANCIEE DEPUIS LA SOURCE.

D OU CA VIENT. Depot `BohemiaInteractive/CWR` (moteur Poseidon, GPL-3.0-or-later, publie
par Bohemia), fichier `engine/Poseidon/World/Detection/Target.cpp`. C est RV1, l ANCETRE
du moteur d Arma 3 : chaque equation d ici est une HYPOTHESE sur RV3, jamais une mesure.
Arma 3 reste le certificateur. Il n existe aucune source d Arma 2 — RV3 n a jamais ete
publie, et le seul moteur RV public est celui-ci.

CE QUE L EQUATION DIT, ET QUE LE GYMNASE NIAIT
  · le couvert MULTIPLIE la vue : `Visibility(brain, ai)` est un FACTEUR, pas une porte ;
  · l ouie TRAVERSE le couvert a 90 % : `landAud = 1 - (1 - landVis) * 0.90` ;
  · mais l ouie SEULE n identifie JAMAIS le camp : `min(audAcc * 0.5, 1.4)` contre un
    seuil de reconnaissance a 1.5. Elle dit « quelque chose est la », jamais « ennemi ».
Le gymnase avait un INTERRUPTEUR — la designation exigeait `los > 0.5`, donc la mortalite
des jamais-vus etait EXACTEMENT NULLE. Arma 3 mesure +75 % pour les vus (563 000 obs),
pas +infini.

CE QUI N EST PAS INSTANCIE ICI, ET POURQUOI (voir CRITERES_EQ1_CANAL.md)
  · la graduation de cone 15/17/45 deg — le gymnase tire son arc au hasard (`def_rand`)
    et possede deja sa porte de tir ; deux portes composees compteraient deux fois ;
  · le passage « position connue avec erreur -> probabilite de toucher » — absent de
    Target.cpp, il vit dans le code de tir. On ne l invente pas ;
  · `TacticalFog8` (table indisponible) -> fog = 1, et `night` = 0 : PLEIN JOUR, le regime
    ou la courbe de toucher a ete mesuree le 26/07. Dit, pas cache.
"""
import torch

# ─── CONSTANTES LUES DANS LA SOURCE. Chacune porte sa ligne. Aucune n est choisie. ───
#     engine/Poseidon/World/Detection/Target.cpp
RADIUS_COEF   = 5000.0   # l.645 `radiusCoef` (vue) et l.669 `audRadiusCoef` (ouie)
VIS_SAT       = 40.0     # l.651 saturateMin(sizeVis, 40)
AUD_SAT       = 240.0    # l.671 saturateMin(sizeAud, 240)
AUD_TRAVERSE  = 0.90     # l.664 « units can hear even behind obstructions to some extent »
VIT_DIV       = 200.0    # l.831 speedCoef = mySpeed * (1/200)
VIT_MAX       = 0.8      # l.832 saturateMin(speedCoef, 0.8)
VIS_CLAMP     = 10.0     # l.841 saturate(visibility, 0, 10)
AUD_CLAMP     = 120.0    # l.842 saturate(audibility, 0, 120)
ACC_GAIN      = 3.0      # l.844/847 accuracy = visibility * 3 / audibility * 3
VIS_ACC_SAT   = 30.0     # l.845 saturateMin(visibleAccuracy, 30)
AUD_GAIN      = 0.25     # l.881 audibleAccuracy *= sensitivityEar * aiAudible * 0.25
SIDE_VUE      = 0.15     # l.885 visibleSideAccuracy = min(visibleAccuracy * 0.15, 4)
SIDE_VUE_MAX  = 4.0      # l.885
SIDE_OUIE     = 0.5      # l.884 audibleSideAccuracy = min(audibleAccuracy * 0.5, 1.4)
# ⭐ VALIDEE SUR ARMA 3 LE 03/09/2026 — la PREMIERE equation lue chez le cousin que le
# certificateur confirme au lieu de la refuter. Banc `canal_designation.py`, deux bras,
# 12 episodes valides sur 12, six geometries (15 a 100 m), `knowsAbout` lu — c est
# `FadingSideAccuracy()` elle-meme, pas un proxy.
#   bras A (visible)  : 4,00 sur 12/12   -> le controle positif franchit 1,5
#   bras B (masque, fraction visible NULLE a chaque releve, 20 coups tires) :
#       15 m 1,35 · 25 m 1,35 · 40 m 1,35 · 60 m 0,61 · 80 m 0,34 · 100 m 0,00
# **JAMAIS 1,5.** L ouie porte l information et ne nomme pas le camp.
#
# ⭐ ET LA FORME EST CELLE DE LA SOURCE. `aud = min(rayon*5000/d^2, ...)` predit du 1/d^2 :
#   (80/60)^2 = 1,78 contre 0,61/0,34 = 1,79 mesure. La constante a*d^2 vaut 2160, 2196 et
#   2176 a 40, 60 et 80 m — 0,9 % d ecart. Le plafond mesure est 1,35 (la source disait 1,4)
#   et il mord sous ~40 m. Coupure nette entre 80 et 100 m, coherente avec `R_VUE_NULLE`=100
#   du modele d alerte mesure le 30/07 par un banc INDEPENDANT.
OUIE_MESUREE = dict(K=2177.0, plafond=1.35, portee_nulle_m=100.0, date="2026-09-03")
SIDE_OUIE_MAX = 1.35     # MESURE (la source disait 1,4). Mesure bat source.
ACC_MAX       = 4.0      # l.899/900 saturateMin(visibleAccuracy, 4)
SIDE_RECONNU  = 1.5      # l.936 « real side can only be recognized at accuracy >= 1.5 »
FOG           = 1.0      # TacticalFog8 indisponible -> plein jour (regime de la courbe)
NIGHT         = 0.0      # idem

# ─── LES QUATRE VALEURS PAR TYPE QUI NE SONT PAS DANS LA SOURCE ───
# A LIRE dans Arma 3 par `configFile` — legal, aucune source requise (⟨Fable⟩ : les
# constantes par configFile, les mecanismes par la source comme hypothese).
A_MESURER = {
    "rayon_m":             'GetRadius() du modele — `sizeOf _t` / `boundingBoxReal`, a verifier',
    "sensibilite":         'getNumber (configFile >> "CfgVehicles" >> _t >> "sensitivity")',
    "sensibilite_oreille": 'getNumber (configFile >> "CfgVehicles" >> _t >> "sensitivityEar")',
    "audible_cible":       'getNumber (configFile >> "CfgWeapons" >> _w >> "audibleFire")',
}


def constantes(**kw):
    """Valide les quatre valeurs de config et rend le dict du canal. REFUSE si une manque.

    Precedent : `tir_par_pas`. Un parametre invente ne se signale jamais, donc le code
    doit refuser de tourner sans lui — plutot que de tourner avec un chiffre raisonnable
    choisi un jour par quelqu un de sense.
    """
    manque = [k for k in A_MESURER if kw.get(k) is None]
    if manque:
        lignes = "\n".join("      %-20s %s" % (k, A_MESURER[k]) for k in manque)
        raise ValueError(
            "canal_cwr REFUSE de tourner : %d valeur(s) de config d Arma 3 manquante(s).\n"
            "    Elles ne sont PAS dans la source (elles sont par type) et ne s inventent pas :\n%s\n"
            "    Pour une FUMEE seulement : canal_cwr.provisoire() — il crie, et interdit le banc."
            % (len(manque), lignes))
    for k in A_MESURER:
        v = float(kw[k])
        if v < 0:
            raise ValueError("canal_cwr : %s negatif (%r)" % (k, v))
    c = {k: float(kw[k]) for k in A_MESURER}
    c["mesure"] = True
    return c


def provisoire():
    """Jeu PROVISOIRE, NON MESURE — fumee uniquement. Il crie et se marque.

    Aucun banc ne doit lire un resultat produit avec ca. Les quatre valeurs sont posees
    a 1.0 (neutre multiplicatif) et le rayon a 0.6 m (demi-largeur d un homme), pour que
    le controle positif puisse verifier la FORME des equations, pas leur calibration.
    """
    print("  ⚠⚠ canal_cwr : VALEURS PROVISOIRES NON MESUREES (rayon 0,6 m, sensibilites 1,0).")
    print("     Elles servent a verifier la FORME des equations. AUCUN BANC ne peut les lire.")
    return dict(rayon_m=0.6, sensibilite=1.0, sensibilite_oreille=1.0,
                audible_cible=1.0, mesure=False)


def canal(landVis, dist_m, cst, porte_cone=None, v_capteur=0.0):
    """Le canal de detection de Target.cpp, terme par terme, dans l ORDRE de la source.

    landVis  (N,A) fraction de corps visible depuis le capteur — l analogue exact de
             `Visibility(brain, ai)`. Au gymnase c est `_body_exposure` (5 segments du
             corps par rayons), donc `replica`+`emergent_expo` sont EXIGES : sans eux le
             gymnase ne sait produire qu un `los` BINAIRE, et l equation n a plus d objet.
    dist_m   (N,A) distance capteur->cible en metres.
    porte_cone (N,A) ou None — 1 la ou le capteur peut engager, 0 ailleurs. On reprend la
             porte DEJA en service dans le gymnase ; on n importe pas les cosinus de RV1.
    v_capteur vitesse propre du capteur, m/s (l.830 : bouger degrade sa propre perception).

    Rend un dict de tenseurs (N,A). `designe` est le seul a remplacer quelque chose.
    """
    d2 = dist_m * dist_m
    un = torch.ones_like(dist_m)

    # l.643-651 — TAILLE APPARENTE : le rayon sur la distance au carre, sature a 40.
    sizeVis = torch.where(d2 > 0, cst["rayon_m"] * RADIUS_COEF / d2.clamp(min=1e-6), un * 100.0)
    sizeVis = sizeVis.clamp(max=VIS_SAT)
    # l.653-655 — ⭐ LE COUVERT MULTIPLIE. Ce n est pas une porte.
    vis = FOG * sizeVis * landVis

    # l.664-673 — ⭐ L OUIE TRAVERSE LE COUVERT A 90 %.
    landAud = 1.0 - (1.0 - landVis) * AUD_TRAVERSE
    sizeAud = torch.where(d2 > 0, cst["rayon_m"] * RADIUS_COEF / d2.clamp(min=1e-6), un * 1000.0)
    sizeAud = sizeAud.clamp(max=AUD_SAT)
    aud = sizeAud * landAud

    # l.830-833 — le capteur qui BOUGE percoit moins bien, vue et ouie.
    if v_capteur:
        pen = min(abs(float(v_capteur)) / VIT_DIV, VIT_MAX)
        vis = vis - pen
        aud = aud - pen
    vis = vis.clamp(0.0, VIS_CLAMP)          # l.841
    aud = aud.clamp(0.0, AUD_CLAMP)          # l.842

    # l.844-880 — PRECISION. Le plafond a 30 s applique AVANT la porte et la sensibilite.
    acc_vue = (vis * ACC_GAIN).clamp(max=VIS_ACC_SAT)
    acc_vue = acc_vue * cst["sensibilite"] * (1.0 - NIGHT)
    if porte_cone is not None:
        acc_vue = acc_vue * porte_cone
    # l.881 — l ouie ne connait ni cone ni nuit.
    acc_ouie = aud * ACC_GAIN * cst["sensibilite_oreille"] * cst["audible_cible"] * AUD_GAIN

    # l.884-885 — ⭐ LE CAMP. Calcule AVANT le plafond a 4 (l ordre de la source compte :
    # `visibleAccuracy` peut valoir 30 ici, donc `side_vue` sature a 4).
    side_ouie = (acc_ouie * SIDE_OUIE).clamp(max=SIDE_OUIE_MAX)   # <= 1.4, TOUJOURS
    side_vue = (acc_vue * SIDE_VUE).clamp(max=SIDE_VUE_MAX)

    acc_vue = acc_vue.clamp(max=ACC_MAX)     # l.899
    acc_ouie = acc_ouie.clamp(max=ACC_MAX)   # l.900

    side = torch.maximum(side_vue, side_ouie)
    acc = torch.maximum(acc_vue, acc_ouie)
    # l.936 — LE SEUIL. 1.4 < 1.5 : l ouie seule ne franchit jamais cette ligne.
    designe = side >= SIDE_RECONNU

    return dict(vis=vis, aud=aud, acc_vue=acc_vue, acc_ouie=acc_ouie,
                side_vue=side_vue, side_ouie=side_ouie, side=side, acc=acc, designe=designe)


def preuve_analytique():
    """P3 par le calcul, avant tout tenseur : l ouie ne peut PAS designer, quelles que
    soient la distance et la sensibilite d oreille — parce que le plafond est AVANT le max."""
    print("  P3 analytique : side_ouie = min(acc_ouie * %.1f, %.1f) <= %.1f < %.1f = seuil"
          % (SIDE_OUIE, SIDE_OUIE_MAX, SIDE_OUIE_MAX, SIDE_RECONNU))
    return SIDE_OUIE_MAX < SIDE_RECONNU


if __name__ == "__main__":
    print(__doc__.split("\n")[0])
    assert preuve_analytique()
    c = provisoire()
    d = torch.tensor([[5.0, 25.0, 60.0, 120.0, 200.0]])
    for lv in (0.0, 0.2, 0.6, 1.0):
        r = canal(torch.full_like(d, lv), d, c, porte_cone=torch.ones_like(d))
        print("  landVis %.1f | side %s | designe %s"
              % (lv, [round(x, 2) for x in r["side"][0].tolist()],
                 [bool(x) for x in r["designe"][0].tolist()]))


# ═══════════════════════════════════════════════════════════════════════════════════════
#  L AUTRE MOITIE — LA LOI DE TIR
#  `WhatShootResult` (Target.cpp:1527-1620), `WhatFireResult` (TargetFire.cpp:1162-1260),
#  `HitProbability` (TargetFire.cpp:69), `AIGroup::AssignTargets` (AIGroupImpl.cpp:892).
#
#  CE QU ELLE DIT, ET QUI RENVERSE LA LECTURE DE LA PREMIERE MOITIE :
#    · RV1 A UN INTERRUPTEUR AUSSI — `MinVisibleFire = 0.63` — mais sur une FRACTION
#      continue de corps visible, pas sur un booleen. Le gymnase avait 0,5 sur un binaire.
#      Donc les jamais-vus ne meurent PAS de tir vise, ni ici ni la : c est la loi.
#    · le couvert entre AU CARRE : `hitProbab *= Square(visible)`.
#    · une cible non vue depuis plus de 10 s n est PLUS TIRABLE (`lastSeen < t - 10`), et
#      une cible dont la position est connue avec une erreur superieure a deux fois le
#      rayon d effet de la munition n est pas tirable non plus (`posError`). Pour un FUSIL,
#      `indirectHitRange` vaut ~0 : une cible connue par l OREILLE SEULE est intirable.
#    · l homme reste COLLE a sa cible : `FireValidTime() = 15 s` avant de pouvoir changer.
#
#  DONC LE +75 % D ARMA 3 NE VIENT PAS DES JAMAIS-VUS. Il vient des VUS IL Y A MOINS DE
#  10 s, et des armes a rayon d effet. `feu_sur_connu` n est pas une fraction libre : c est
#  une FENETRE DE 10 SECONDES. C est falsifiable, et le falsificateur est ecrit plus bas.
# ═══════════════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════════════
#  ⛔ LA PORTE `MinVisibleFire` EST FALSIFIEE SUR ARMA 3 — 03/09/2026, ET ELLE EST RETIREE
#
#  Revendication testee : « aucun tir VISE sur un homme dont la visibilite courante est
#  < 0,63 ». Elle venait de RV1 (Target.cpp:1604) et paraissait confirmee par la config
#  d Arma 3 (`indirectHitRange` = 0,0). Falsificateur ecrit AVANT la mesure, seuil 10 %.
#
#  Banc `falsificateur_vue.py`, 3 episodes 8 contre 8 sur Altis, 249 impacts dont 237 sur
#  victime VIVANTE, munition qualifiee (`indirectHitRange` = 0,0 · `hit` = 10,0).
#  DEUX instruments independants, tous deux avec controle positif joue avant :
#      rayon oeil-a-oeil ... 70 / 237 =  29,5 % sous 0,63
#      fraction de corps ... 88 / 237 =  37,1 % sous 0,63   <- l instrument du moteur
#  Seuil pre-inscrit : 10 %. **Mesure : 3,7 fois le seuil.** Les deux instruments concordent.
#
#  ⭐ CE QUE CA REND AU PROJET, ET C EST UNE BONNE NOUVELLE. Le « corollaire dur » deduit de
#  la source — le +75 % ne peut pas venir de tirs sur des hommes caches — est REFUTE par le
#  certificateur. On EST touche au fusil en etant cache dans Arma 3. Donc `feu_sur_connu` et
#  le feu sur position connue redeviennent des mecanismes legitimes a mesurer, au lieu d etre
#  interdits par une lecture de RV1.
#
#  ⭐ CLIQUET : une equation lue chez le cousin reste une HYPOTHESE meme quand une constante
#  de config du certificateur semble la confirmer. `indirectHitRange` = 0 etait vrai ET
#  n impliquait pas ce qu on lui faisait dire.
#
#  CE QUI N EST PAS FALSIFIE PAR CE BANC, et reste en service : `visible ** 2`, le plancher
#  a 0,05, les horloges de 10 s et 15 s, et tout le canal de designation de l equation 1.
#  Ce banc n a teste QU UNE porte. Ne pas etendre le verdict a ce qu il n a pas mesure.
# ═══════════════════════════════════════════════════════════════════════════════════════
PORTE_VISIBLE = False   # RETIREE le 03/09/2026. La remettre a True exige une mesure NEUVE.
MIN_VISIBLE_FIRE = 0.63   # Target.cpp:45 et TargetFire.cpp:37 — la porte dure
# ⛔ L EXPOSANT DE RV1 EST REFUTE — MESURE SUR ARMA 3 LE 03/09/2026.
# Banc `loi_visibilite.py`, 24 sessions de duels, 16 duels simultanes, tireur ET cible
# invulnerables, 100 m : **18 181 coups tires, 7 924 impacts, 16 conditions**.
# Pente log-log ponderee sur les 16 duels : a = 0,72, IC95 bootstrap [0,39 ; 0,97].
# **2 est tres largement hors de l intervalle.** A f = 0,50, RV1 punissait x0,25 ; la mesure
# donne x0,61 — le carre SUR-PUNIT le couvert d un facteur 2,4.
#
# ⚠️ CE QUI EST LU ICI, ET CE QUI NE L EST PAS. L exposant est une PENTE log-log : il est
# invariant par un facteur multiplicatif constant de comptage. Le NIVEAU absolu, lui, n a pas
# passe son controle positif (0,559 en pleine vue a 100 m contre la bande 0,15-0,50 tiree de
# la courbe du 26/07) — et le depot du projet montre pourquoi : sur le meme phenomene,
# `HitPart` sur cible invulnerable lit 48 % la ou la courbe tabule 30 %. Les deux instruments
# ne comptent pas pareil. Donc on prend la PENTE et **on ne prend pas le niveau** : le niveau
# reste porte par `_p_balle`, la courbe deja mesuree.
#
# DOMAINE DE VALIDITE : f entre 0,29 et 0,90, une seule distance (100 m), un seul type
# d unite. Rien n autorise a extrapoler vers f -> 0.
VIS_EXPOSANT_MESURE = 0.72
VIS_EXPOSANT_IC = (0.39, 0.97)
VIS_EXPOSANT     = VIS_EXPOSANT_MESURE   # etait 2 (Target.cpp:1611), REFUTE le 03/09
HIT_PROBAB_MIN   = 0.05   # Target.cpp:1614 `if (hitProbab < 0.05) return false`
MEM_TIR_S        = 10.0   # TargetFire.cpp:1241 `if (target.lastSeen < Glob.time - 10)`
FIRE_VALID_S     = 15.0   # EntityAI.hpp:433 `virtual float FireValidTime() const {return 15;}`
SPOT_ERR_OUIE    = 0.8    # Target.cpp:1022 `spotError = ai->Position().Distance(Position()) * 0.8`

# ⛔ CE QU ON N INSTANCIE PAS, ET LE REFUS EST LA DECISION
# L allocation de RV1 est une ECONOMIE : on empile des tireurs sur une cible tant que
# `enemyTTL = 60*armor/dammagePerMinute` depasse `groupTTL = 0.6*min(TTL)`, puis on passe a
# la suivante (AIGroupImpl.cpp:1032-1195). `armor` et `dammagePerMinute` ne sont PAS des
# grandeurs du gymnase — les inventer ferait exactement ce que le projet s interdit. On
# n instancie donc que la consequence OBSERVABLE et deja mesuree : le VERROU de 15 s, qui
# est ce qui fait qu un flanqueur isole encaisse tout au lieu d etre relache au pas suivant.
# Le 1,8 attaquant par defenseur mesure sur Arma est le RESULTAT de la boucle, pas une
# constante : il ne se recopie pas, il doit EMERGER du verrou. Falsificateur ecrit.


def tir(p_bulle, visible):
    """`hitProbab` de WhatShootResult, terme par terme, dans l ordre de la source.

    `p_bulle` = `HitProbability(d, ammo)` : la probabilite de toucher une cible
    ENTIEREMENT visible. Au gymnase c est `_p_balle(dist)` — mesuree le 26/07 sur terrain
    NU et plat, donc bien le cas « entierement visible ». La source la calcule par une
    rampe lineaire sur trois points de `CfgAmmo` (`minRange/midRange/maxRange` et leurs
    `*Probab`) : la courbe mesuree et la courbe de config sont la MEME grandeur, ce qui
    donne une contre-verification independante de la mesure — a faire, pas faite.

    ⚠️ POURQUOI LE CARRE N EST PAS UN DOUBLE COMPTE. Un facteur `visible` dit « quelle
    part de la cible peut etre atteinte », l autre « avec quelle qualite on peut viser ce
    qu on voit ». La source les multiplie tous les deux ; le gymnase n en appliquait qu un.
    """
    z = torch.zeros_like(p_bulle)
    p = p_bulle * visible ** VIS_EXPOSANT                       # Target.cpp:1611
    if PORTE_VISIBLE:
        p = torch.where(visible >= MIN_VISIBLE_FIRE, p, z)      # RETIREE — voir ci-dessous
    p = torch.where(p >= HIT_PROBAB_MIN, p, z)                  # Target.cpp:1614 — plancher
    return p


def en_pas(secondes, sec_par_pas):
    """Arma compte en SECONDES, le gymnase en PAS. Aucune duree ne se recopie telle quelle."""
    if not sec_par_pas:
        raise ValueError("canal_cwr : duree en secondes sans sec_par_pas — elle ne se recopie pas")
    return max(1, int(round(float(secondes) / float(sec_par_pas))))


# ═══════════════════════════════════════════════════════════════════════════════════════
#  LES QUATRE VALEURS, LUES DANS ARMA 3 LE 03/09/2026 — elles ne sont plus provisoires.
#  Serveur Altis, pont natif 5801, sonde `lire_config_arma.py` / `lire_config_arma2.py`.
#  Controle positif joue AVANT : temoin + (`CfgAmmo >> hit` = 10) et temoin - (chemin
#  bidon, isNumber = 0). Chaque sonde emet `isNumber` PUIS la valeur, parce que `getNumber`
#  rend 0 pour « absent » comme pour « vaut zero ».
# ═══════════════════════════════════════════════════════════════════════════════════════
ARMA3 = dict(
    # `GetRadius()` = sphere englobante. ⚠️ `radius` est ABSENT de CfgVehicles et `sizeOf`
    # rend 0,000 sur un serveur sans unite posee — il a fallu POSER un homme et lire
    # `boundingBoxReal` (1,600 x 2,200 x 2,000 m), donc juger l ACTE et non la table.
    rayon_m=1.688,
    sensibilite=6.0,            # CfgVehicles >> B_Soldier_F >> sensitivity
    sensibilite_oreille=0.125,  # CfgVehicles >> B_Soldier_F >> sensitivityEar
    # ⚠️ PIEGE EVITE : `aiAudible = ai->Audible()` (Target.cpp:822) est l audibilite de
    # l ENTITE — `CfgVehicles >> audible` = 0,05 — et NON `audibleFire` de la munition
    # (= 40,0), qui alimente l autre terme, celui du TIR qui trahit.
    audible_cible=0.05,
    mesure=True,
)

# Ce que la meme lecture a rendu, et qui ne sert pas au canal mais tranche une question :
ARMA3_AUTRES = dict(
    audibleFire_munition=40.0,   # CfgAmmo >> B_65x39_Caseless >> audibleFire
    visibleFire_munition=3.0,
    indirectHitRange=0.0,        # ⭐ ZERO : `posError > 2*0` -> TOUTE erreur de position
                                 #   ecarte le fusil. La consequence tiree de RV1 est
                                 #   CONFIRMEE par la config d Arma 3 elle-meme.
    camouflage=1.4, audible_entite=0.05, armor=2.0, armorStructural=4.0, accuracy=2.3,
)


def constantes_arma3():
    """Le jeu MESURE. Contrairement a `provisoire()`, il ne crie pas : un banc peut le lire."""
    return dict(ARMA3)
