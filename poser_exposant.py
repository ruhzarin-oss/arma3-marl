#!/usr/bin/env python3
"""Remplace l exposant du couvert par la valeur MESUREE sur Arma 3 (03/09/2026)."""
import sys, shutil
P = "/home/younes/arma3-marl/canal_cwr.py"
s = open(P, encoding="utf-8").read()
if "VIS_EXPOSANT_MESURE" in s:
    print("  DEJA POSE — rien fait."); sys.exit(0)
OLD = "VIS_EXPOSANT     = 2      # Target.cpp:1611 `hitProbab *= Square(visible)`"
NEW = '''# ⛔ L EXPOSANT DE RV1 EST REFUTE — MESURE SUR ARMA 3 LE 03/09/2026.
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
VIS_EXPOSANT     = VIS_EXPOSANT_MESURE   # etait 2 (Target.cpp:1611), REFUTE le 03/09'''
if s.count(OLD) != 1:
    sys.exit("ancre introuvable (%d)" % s.count(OLD))
shutil.copy2(P, P + ".avantexposant")
open(P, "w", encoding="utf-8").write(s.replace(OLD, NEW))
print("  exposant pose a 0,72. Sauvegarde : canal_cwr.py.avantexposant")
