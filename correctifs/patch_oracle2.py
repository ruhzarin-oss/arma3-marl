#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-ORACLE-COMPLET
# CHACAL_ORACLE = 2 : l oracle COMPLET ( revue de Fable, 11/09 ). Le 1 etait pose APRES le choix de la porte,
# qui restait aveugle ( gardes|[0,0] ). Le 2 revele les defenseurs AVANT ce choix : la porte, la position
# d assaut et la position d appui sont calculees en les connaissant. 1 = oracle a l assaut seulement ; 0 = origine.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"; D = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis"
def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))
def patch(path, avant, apres, quoi):
    s = open(path, encoding="utf-8", errors="surrogateescape").read()
    if s.count(avant) != 1: print("  !! motif x%d : %s" % (s.count(avant), quoi)); sys.exit(1)
    s2 = s.replace(avant, apres, 1)
    if path.endswith(".sqf") and bilan(s) != bilan(s2): print("  !! equilibre : %s" % quoi); sys.exit(1)
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(s2); print("  PATCHE :", quoi)
if "CHACAL_ORACLE == 2" in open(f"{M}/60_phases.sqf", encoding="utf-8", errors="surrogateescape").read():
    print("  deja present"); sys.exit(0)
patch(f"{M}/60_phases.sqf",
  '''    private _dep = ((units CHACAL_gAssaut) select { alive _x }) call CHACAL_fnc_centre;
    if (count _dep == 0) then { _dep = CHACAL_RALLY };''',
  '''    // ! L ORACLE COMPLET ( CHACAL_ORACLE = 2, revue de Fable 11/09 ) : les defenseurs sont reveles et
    // inscrits comme vus AVANT le choix de la porte, qui se fait alors en les connaissant.
    if (CHACAL_ORACLE == 2) then {
        private _defO = CHACAL_EST_SITE select { alive _x };
        { private _u = _x; { _u reveal [_x, 4] } forEach _defO } forEach (CHACAL_FS select { alive _x });
        CHACAL_VUES = _defO apply { [_x, 4] };
        (format ["CHACAL|E|oracle|%1|reveles|%2|hommes|%3|phase|4|avant_choix_porte|1", round (time * 100) / 100,
            count _defO, count (CHACAL_FS select { alive _x })]) call CHACAL_LOG;
    };
    private _dep = ((units CHACAL_gAssaut) select { alive _x }) call CHACAL_fnc_centre;
    if (count _dep == 0) then { _dep = CHACAL_RALLY };''', "60_phases : oracle complet avant le choix de la porte")
patch(f"{M}/60_phases.sqf", "    if (CHACAL_ORACLE == 1) then {\n        private _def = CHACAL_EST_SITE select { alive _x };",
      "    if (CHACAL_ORACLE >= 1) then {\n        private _def = CHACAL_EST_SITE select { alive _x };", "60_phases : oracle avant mise en place pour 1 et 2")
patch(f"{M}/60_phases.sqf", "if (CHACAL_ORACLE == 1) then {\n    private _def = CHACAL_EST_SITE select { alive _x };",
      "if (CHACAL_ORACLE >= 1) then {\n    private _def = CHACAL_EST_SITE select { alive _x };", "60_phases : rafraichi a l assaut pour 1 et 2")
patch(f"{D}/description.ext", '''        title = "Oracle : defenseurs reveles a tous (0 = non)";
        values[] = {0,1};
        texts[]  = {"NON","OUI"};''', '''        title = "Oracle : 0 non, 1 a l assaut, 2 complet (avant le choix de la porte)";
        values[] = {0,1,2};
        texts[]  = {"NON","ASSAUT","COMPLET"};''', "description.ext : valeur 2")
