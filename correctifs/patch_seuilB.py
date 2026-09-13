#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-SEUIL-B
# Le bras B attendait que le CENTRE de tous les survivants depasse 300 m du site, avec un repli a 900 s.
# Le plafond mesure de la phase 6 vaut 1300 s, donc le repli aurait joue - mais le parametre n etait pas
# lu, donc rien n a tourne. Avec le parametre repare, on durcit quand meme le bras pour qu il soit
# certainement actif et mesurable : 200 m au lieu de 300, repli a 180 s au lieu de 900.
# L intention tactique est inchangee : rompre le contact, puis rendre les jambes. La ligne exfil_degage
# ecrit la distance REELLE au moment de la bascule, donc on saura ce qui s est passe.
import sys
p = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf"
s = open(p, encoding="utf-8", errors="surrogateescape").read()
a = "((time - _t0) > 900) ||\n            ((_v call CHACAL_fnc_centre) distance2D CHACAL_SITE > 300) };"
if a not in s:
    print("  !! ancre du seuil absente"); sys.exit(1)
b = "((time - _t0) > 180) ||\n            ((_v call CHACAL_fnc_centre) distance2D CHACAL_SITE > 200) };"
s2 = s.replace(a, b, 1)
bil = lambda t: (t.count("{")-t.count("}"), t.count("[")-t.count("]"), t.count("(")-t.count(")"))
if bil(s) != bil(s2):
    print("  !! equilibre"); sys.exit(1)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  PATCHE : 60_phases : bras B a 200 m, repli a 180 s")
