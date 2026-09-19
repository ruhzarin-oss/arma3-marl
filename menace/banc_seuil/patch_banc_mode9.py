"""
Banc, mode 9 : REGARD CENTRE SUR UNE POSITION, pas sur l unite ( 19/09, 2 h 45 ). Vise bancs/chacalvue, apres patch_banc_modes.py.
Le banc BANC3 donne 1 cible connue sur 14 en balayage ( doWatch sur une POSITION ), meme dans l axe, alors que le mode 5 ( doWatch sur L UNITE ennemie )
donne ~100 % en 5 s a la meme distance. Soupcon : designer l unite au moteur suffit a la faire entrer dans la liste de cibles. Le mode 9 est le mode 5
a une difference pres : les hommes sont tournes vers la cible ( setDir ) et regardent SA POSITION ( doWatch <position> ), jamais l objet.
Si le mode 9 connait la cible comme le mode 5, le soupcon tombe. S il ne la connait pas, toutes les portees « regard centre » mesurent une cible DESIGNEE.
Usage : python3 patch_banc_mode9.py [depot]   ( --racine <dossier du banc> pour une copie )
"""
import sys
if "--racine" in sys.argv: B = sys.argv[sys.argv.index("--racine") + 1]
else: B = f"{sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/hmt/depot'}/bancs/chacalvue"
P = f"{B}/mission.Altis/chacal/60_phases.sqf"; s = open(P, encoding="utf-8").read()
assert "BANC, VERSION 3" in s and "mode 9" not in s
def r(s, a, b, n=1):
    assert s.count(a) == n, f"« {a[:60]} » trouve {s.count(a)} fois"; return s.replace(a, b)
s = r(s, "if ((CHACAL_CONTROLE_PERCEPTION in [1, 5, 7, 8]) && { count _hommes > 0 }) then {", "if ((CHACAL_CONTROLE_PERCEPTION in [1, 5, 7, 8, 9]) && { count _hommes > 0 }) then {")
s = r(s, "        private _banc = CHACAL_CONTROLE_PERCEPTION in [5, 7, 8];", "        private _banc = CHACAL_CONTROLE_PERCEPTION in [5, 7, 8, 9];")
s = r(s, "            _regards = [];                            // le banc a regard centre ne balaie pas\n        };\n",
      "            _regards = [];                            // le banc a regard centre ne balaie pas\n        };\n"
      "        if (CHACAL_CONTROLE_PERCEPTION == 9) then {\n"
      "            // ! mode 9 : meme regard centre que le mode 5, mais sur la POSITION de la cible, jamais sur l objet. Si designer l unite au moteur\n"
      "            // suffit a la faire connaitre, le mode 5 le cache et le mode 9 le montre.\n"
      "            private _posCible = getPosATL (leader _g);\n"
      "            { _x setDir (_x getDir _posCible); _x doWatch _posCible } forEach _hommes;\n"
      "            _regards = [];\n"
      "        };\n")
s = r(s, "(CHACAL_CONTROLE_PERCEPTION in [5, 7, 8]) && { !isNull _gBanc }", "(CHACAL_CONTROLE_PERCEPTION in [5, 7, 8, 9]) && { !isNull _gBanc }")
s = r(s, "    if ((CHACAL_CONTROLE_PERCEPTION in [5, 7, 8]) && { !CHACAL_FIN }) then {", "    if ((CHACAL_CONTROLE_PERCEPTION in [5, 7, 8, 9]) && { !CHACAL_FIN }) then {")
open(P, "w", encoding="utf-8").write(s); print("patch banc mode 9 applique :", B)
