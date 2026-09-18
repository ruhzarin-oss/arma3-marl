"""
Leviers d observation, correctif de la fumee ( 19/09, 0 h ) : au depart direct a la route ( depart = 2 ), le detachement etait pose a 330 m de la
route QUEL QUE SOIT CHACAL_AVANT. A avant = 120 il devait donc marcher 210 m au lieu de 70 : dans le monde 5 il s est ENLISE ( reflexe de gel,
324 s de marche ) et a observe depuis 208 m au lieu de 120. Le levier deplace desormais AUSSI le point de pose : toujours 70 m derriere le point
d observation, comme a l origine ( 260 + 70 = 330 : l origine est inchangee ).
Usage : python3 patch_mission_observation_v2.py --racine <dossier du banc>
"""
import sys
B = sys.argv[sys.argv.index("--racine") + 1]; P = f"{B}/mission.Altis/chacal/60_phases.sqf"
s = open(P, encoding="utf-8").read()
assert "CHACAL_AVANT" in s and "CHACAL_AVANT + 70" not in s
a = "    private _pt = CHACAL_ROUTE getPos [330, CHACAL_ROUTE getDir CHACAL_LZ];"
assert s.count(a) == 1, s.count(a)
s = s.replace(a, "    private _pt = CHACAL_ROUTE getPos [CHACAL_AVANT + 70, CHACAL_ROUTE getDir CHACAL_LZ];   // 70 m derriere le point d observation, comme a l origine ( 260 + 70 = 330 )")
open(P, "w", encoding="utf-8").write(s); print("patch mission_observation v2 applique :", B)
