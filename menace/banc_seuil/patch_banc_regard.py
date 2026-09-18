"""
Banc de perception : « REGARDEE » DOIT ETRE VRAI DES LA PREMIERE SECONDE ( 18/09, 22 h ).
Fumee du patch de journalisation, monde 5, 148 m : les hommes partent a 24 deg de la cible, doWatch les fait pivoter en 90 s, et la
connaissance tombe a la seconde ou l angle arrive a 3 deg. Le banc mesurait donc le PIVOT autant que la perception - et les delais
longs lus dans la journee ( 70, 112, 259 s, angles de depart de 22 a 30 deg ) sont a relire avec cette cause.
Correction, mode banc seulement : chaque homme est TOURNE vers la cible ( setDir ) avant le doWatch. L angle reste journalise.
S applique apres patch_banc_vue_fine.py. Usage : python3 patch_banc_regard.py [depot]   ( vise bancs/chacalvue ; --fichier pour une copie )
"""
import sys
if "--fichier" in sys.argv: P = sys.argv[sys.argv.index("--fichier") + 1]
else: P = f"{sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/hmt/depot'}/bancs/chacalvue/mission.Altis/chacal/60_phases.sqf"
s = open(P, encoding="utf-8").read()
assert "RECHERCHE FINE" in s, "patch_banc_vue_fine.py doit etre applique avant"
assert "TOURNE vers la cible" not in s, "patch deja applique"
a = "            { _x doWatch _cibleU } forEach _hommes;   // banc : ils fixent la cible, aucune ambiguite de direction\n"
b = ("            // ! « REGARDEE » DES LA PREMIERE SECONDE : doWatch seul met jusqu a 90 s a pivoter de 24 deg ( fumee du 18/09, monde 5 ),\n"
     "            // et le banc mesurait ce pivot. Chaque homme est TOURNE vers la cible, puis la fixe.\n"
     "            { _x setDir (_x getDir _cibleU); _x doWatch _cibleU } forEach _hommes;\n")
assert s.count(a) == 1, f"ancre trouvee {s.count(a)} fois"
open(P, "w", encoding="utf-8").write(s.replace(a, b))
print("patch banc_regard applique :", P)
