"""
Banc, levier CHACAL_CONTROLE_PAS : duree du regard sur chaque azimut du balayage, en secondes ( origine 10 ). Vise bancs/chacalvue, apres patch_banc_mode9.py.
Motif ( DESIGNATION-19-09 ) : une cible NON designee, regard centre, demande ~12 s de regard continu ( contre 6 s designee ) ; le balayage ne tient que 10 s
par azimut. Hypothese : un pas de 30 s ( un seul passage sur les trois azimuts en 90 s ) connait ce que le pas de 10 s ne connait jamais.
Usage : python3 patch_banc_pas.py [depot]   ( --racine <dossier du banc> pour une copie )
"""
import sys
if "--racine" in sys.argv: B = sys.argv[sys.argv.index("--racine") + 1]
else: B = f"{sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/hmt/depot'}/bancs/chacalvue"
PH, EXT, SOC, LAN = f"{B}/mission.Altis/chacal/60_phases.sqf", f"{B}/mission.Altis/description.ext", f"{B}/mission.Altis/chacal/00_socle.sqf", f"{B}/lancer.sh"
def lire(p): return open(p, encoding="utf-8").read()
def ecrire(p, s): open(p, "w", encoding="utf-8").write(s)
def r(s, a, b):
    assert s.count(a) == 1, f"« {a[:70]} » trouve {s.count(a)} fois"; return s.replace(a, b)
s = lire(PH); assert "mode 9" in s and "CHACAL_CONTROLE_PAS" not in s
s = r(s, "            _tRegard = time + 10; _iRegard = (_iRegard + 1) % (count _regards);", "            _tRegard = time + CHACAL_CONTROLE_PAS; _iRegard = (_iRegard + 1) % (count _regards);   // levier : duree du regard par azimut ( origine 10 s )")
s = r(s, "|essais|%16|vis_pose|%17|candidats|%18\",", "|essais|%16|vis_pose|%17|candidats|%18|pas|%19\",")
s = r(s, "_essais, (round (_visPose * 100)) / 100, count _cands]) call CHACAL_LOG;", "_essais, (round (_visPose * 100)) / 100, count _cands, CHACAL_CONTROLE_PAS]) call CHACAL_LOG;")
ecrire(PH, s)
e = lire(EXT); assert "CHACAL_CONTROLE_PAS" not in e
a = "    class CHACAL_CONTROLE_AZ\n    {"
e = r(e, a, '    class CHACAL_CONTROLE_PAS\n    {\n        title = "Fenetre d observation : duree du regard sur chaque azimut du balayage, en secondes ( origine 10 )";\n'
      '        values[] = {10,20,30}; texts[] = {"10","20","30"}; default = 10;\n    };\n' + a)
ecrire(EXT, e)
c = lire(SOC); assert "CHACAL_CONTROLE_PAS" not in c
a = 'CHACAL_CONTROLE_AZ = ["CHACAL_CONTROLE_AZ", 0] call BIS_fnc_getParamValue;'
c = r(c, a, 'CHACAL_CONTROLE_PAS = ["CHACAL_CONTROLE_PAS", 10] call BIS_fnc_getParamValue;   // balayage : duree du regard par azimut ( origine 10 s )\n' + a); ecrire(SOC, c)
l = lire(LAN); assert "CONTROLE_PAS" not in l
a = 'ecrire_param CONTROLE_AZ "$(lit controle_az 0)";'
l = r(l, a, 'ecrire_param CONTROLE_PAS "$(lit controle_pas 10)"; ' + a); ecrire(LAN, l)
print("patch banc pas applique :", B)
