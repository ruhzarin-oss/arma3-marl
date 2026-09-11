#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-ORACLE
# CHACAL_ORACLE ( Fable, 11/09/2026 ) : que vaut le renseignement PARFAIT ? Les defenseurs du site sont
# reveles a tous nos hommes et inscrits comme vus, avant la mise en place, puis revus au debut de l assaut.
# Question : quand on sait ou ils sont, gagne-t-on ? 0 = comportement d origine.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
D = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis"
L = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"
def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))
def patch(path, avant, apres, quoi):
    s = open(path, encoding="utf-8", errors="surrogateescape").read()
    if s.count(avant) != 1: print("  !! motif x%d : %s" % (s.count(avant), quoi)); sys.exit(1)
    s2 = s.replace(avant, apres, 1)
    if path.endswith(".sqf") and bilan(s) != bilan(s2): print("  !! equilibre : %s" % quoi); sys.exit(1)
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(s2); print("  PATCHE :", quoi)
if "CHACAL_ORACLE" in open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read():
    print("  deja present"); sys.exit(0)
patch(f"{M}/00_socle.sqf",
  'CHACAL_APPUI_FIXE = ["CHACAL_APPUI_FIXE", 0] call BIS_fnc_getParamValue;',
  'CHACAL_APPUI_FIXE = ["CHACAL_APPUI_FIXE", 0] call BIS_fnc_getParamValue;\n'
  '// ! CHACAL_ORACLE ( Fable, 11/09 ) : les defenseurs reveles a tous et inscrits comme vus. 0 = origine.\n'
  'CHACAL_ORACLE = ["CHACAL_ORACLE", 0] call BIS_fnc_getParamValue;', "00_socle : parametre")
patch(f"{M}/60_phases.sqf",
  '''    if (CHACAL_DEPART >= 4) then {
        "CHACAL|AVERT|hors_corpus|depart|4|articulation_non_jouee" call CHACAL_LOG;''',
  '''    // ! L ORACLE ( Fable, 11/09 ) : que vaut le renseignement PARFAIT ? Les defenseurs du site sont
    // reveles a TOUS nos hommes et inscrits comme vus, avant la mise en place. 0 = origine.
    if (CHACAL_ORACLE == 1) then {
        private _def = CHACAL_EST_SITE select { alive _x };
        { private _u = _x; { _u reveal [_x, 4] } forEach _def } forEach (CHACAL_FS select { alive _x });
        CHACAL_VUES = _def apply { [_x, 4] };
        (format ["CHACAL|E|oracle|%1|reveles|%2|hommes|%3|phase|4", round (time * 100) / 100, count _def,
            count (CHACAL_FS select { alive _x })]) call CHACAL_LOG;
    };
    if (CHACAL_DEPART >= 4) then {
        "CHACAL|AVERT|hors_corpus|depart|4|articulation_non_jouee" call CHACAL_LOG;''', "60_phases : oracle avant la mise en place")
patch(f"{M}/60_phases.sqf",
  "private _recoHommes = CHACAL_RECO call CHACAL_fnc_role;",
  '''// ! L ORACLE : la connaissance se rafraichit au debut de l assaut, pour tous nos hommes.
if (CHACAL_ORACLE == 1) then {
    private _def = CHACAL_EST_SITE select { alive _x };
    { private _u = _x; { _u reveal [_x, 4] } forEach _def } forEach (CHACAL_FS select { alive _x });
    (format ["CHACAL|E|oracle|%1|reveles|%2|phase|5", round (time * 100) / 100, count _def]) call CHACAL_LOG;
};
private _recoHommes = CHACAL_RECO call CHACAL_fnc_role;''', "60_phases : oracle rafraichi a l assaut")
patch(f"{M}/70_verdict.sqf", '|appui_fixe|%34",', '|appui_fixe|%34|oracle|%35",', "70_verdict : format FINI")
patch(f"{M}/70_verdict.sqf", 'CHACAL_APPUI_FIXE]) call CHACAL_LOG;', 'CHACAL_APPUI_FIXE, CHACAL_ORACLE]) call CHACAL_LOG;', "70_verdict : valeur FINI")
patch(f"{D}/description.ext", '    class CHACAL_MG_ASSAUT\n', '''    // ! L ORACLE ( Fable, 11/09 ) : defenseurs reveles a tous nos hommes avant la mise en place.
    class CHACAL_ORACLE
    {
        title = "Oracle : defenseurs reveles a tous (0 = non)";
        values[] = {0,1};
        texts[]  = {"NON","OUI"};
        default = 0;
    };
    class CHACAL_MG_ASSAUT
''', "description.ext")
patch(L, 'MG_ASSAUT=$(lit mg_assaut 0);', 'ORACLE=$(lit oracle 0); MG_ASSAUT=$(lit mg_assaut 0);', "lancer.sh : lecture")
patch(L, 'ecrire_param MG_ASSAUT "$MG_ASSAUT";', 'ecrire_param ORACLE "$ORACLE"; ecrire_param MG_ASSAUT "$MG_ASSAUT";', "lancer.sh : ecriture")
