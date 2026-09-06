#!/usr/bin/env python3
"""RETRAIT de la porte `MinVisibleFire` — falsifiee sur Arma 3 le 03/09/2026.
Criteres ecrits d avance (CRITERES_FALSIFICATEUR_VUE.md, seuil 10 %), mesure 37,1 %.
On RETIRE, on ne regle pas : c est ce que les criteres disaient."""
import sys, shutil
P = "/home/younes/arma3-marl/canal_cwr.py"
s = open(P, encoding="utf-8").read()
OLD = """    z = torch.zeros_like(p_bulle)
    p = p_bulle * visible ** VIS_EXPOSANT                       # Target.cpp:1611
    p = torch.where(visible >= MIN_VISIBLE_FIRE, p, z)          # Target.cpp:1604 — porte dure
    p = torch.where(p >= HIT_PROBAB_MIN, p, z)                  # Target.cpp:1614 — plancher
    return p"""
NEW = '''    z = torch.zeros_like(p_bulle)
    p = p_bulle * visible ** VIS_EXPOSANT                       # Target.cpp:1611
    if PORTE_VISIBLE:
        p = torch.where(visible >= MIN_VISIBLE_FIRE, p, z)      # RETIREE — voir ci-dessous
    p = torch.where(p >= HIT_PROBAB_MIN, p, z)                  # Target.cpp:1614 — plancher
    return p'''
if "PORTE_VISIBLE" in s:
    print("  DEJA RETIREE — rien fait."); sys.exit(0)
if s.count(OLD) != 1:
    sys.exit("ancre introuvable (%d)" % s.count(OLD))
s = s.replace(OLD, NEW)

MARQUE = '''
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
'''
s = s.replace("MIN_VISIBLE_FIRE = 0.63", MARQUE + "MIN_VISIBLE_FIRE = 0.63", 1)
shutil.copy2(P, P + ".avantretrait")
open(P, "w", encoding="utf-8").write(s)
print("  porte retiree (PORTE_VISIBLE = False). Sauvegarde : canal_cwr.py.avantretrait")
