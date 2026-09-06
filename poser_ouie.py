#!/usr/bin/env python3
"""Pose la loi auditive MESUREE sur Arma 3 (03/09/2026). Mesure bat source."""
import sys, shutil
P = "/home/younes/arma3-marl/canal_cwr.py"
s = open(P, encoding="utf-8").read()
if "OUIE_MESUREE" in s:
    print("  DEJA POSE — rien fait."); sys.exit(0)
OLD = "SIDE_OUIE_MAX = 1.4      # l.884  ⭐ LE PLAFOND QUI INTERDIT A L OUIE DE DESIGNER"
NEW = '''# ⭐ VALIDEE SUR ARMA 3 LE 03/09/2026 — la PREMIERE equation lue chez le cousin que le
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
SIDE_OUIE_MAX = 1.35     # MESURE (la source disait 1,4). Mesure bat source.'''
if s.count(OLD) != 1:
    sys.exit("ancre introuvable (%d)" % s.count(OLD))
shutil.copy2(P, P + ".avantouie")
open(P, "w", encoding="utf-8").write(s.replace(OLD, NEW))
print("  plafond auditif pose a 1,35 (mesure). Sauvegarde : canal_cwr.py.avantouie")
