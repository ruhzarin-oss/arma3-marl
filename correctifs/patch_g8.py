#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-CAMPAGNE-G8
# Campagne graine 8 ( plan de Fable, 11/09/2026 ) : trois leviers nouveaux, tous a 0 = origine.
#   CHACAL_MG_ASSAUT     (V5) : l ADJOINT de l assaut echange son fusil contre une mitrailleuse Mk200.
#                               Question : le defenseur seul de la tour tombe-t-il avant nos porteurs ?
#   CHACAL_DELAI_PORTEUR (V6) : le delai du porteur vers le point de pose, 45 s a l origine.
#                               Question : lui manque-t-il du temps ou un chemin ? Le temps reel est journalise.
#   CHACAL_APPUI_FIXE    (V9) : une fois en place, l appui passe en YELLOW (tir a volonte, garde ta place),
#                               ne se deplace plus (PATH coupe), LAMBS coupe sur ses deux hommes ; rendu a
#                               l exfiltration. Question : est-ce son deplacement qui le fait voir ?
import sys, shutil, os
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
D = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis"
L = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"

def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))
def patch(path, avant, apres, quoi):
    s = open(path, encoding="utf-8", errors="surrogateescape").read()
    n = s.count(avant)
    if n != 1: print("  !! motif x%d : %s" % (n, quoi)); sys.exit(1)
    s2 = s.replace(avant, apres, 1)
    if path.endswith(".sqf") and bilan(s) != bilan(s2):
        print("  !! equilibre change %s -> %s : %s" % (bilan(s), bilan(s2), quoi)); sys.exit(1)
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE :", quoi)

if "CHACAL_MG_ASSAUT" in open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read():
    print("  deja present"); sys.exit(0)

patch(f"{M}/00_socle.sqf",
  'CHACAL_FEU_AVANT = ["CHACAL_FEU_AVANT", 0] call BIS_fnc_getParamValue;',
  'CHACAL_FEU_AVANT = ["CHACAL_FEU_AVANT", 0] call BIS_fnc_getParamValue;\n'
  '// ! CAMPAGNE GRAINE 8 ( Fable, 11/09 ) - trois leviers, 0 / 45 = comportement d origine.\n'
  'CHACAL_MG_ASSAUT = ["CHACAL_MG_ASSAUT", 0] call BIS_fnc_getParamValue;\n'
  'CHACAL_DELAI_PORTEUR = ["CHACAL_DELAI_PORTEUR", 45] call BIS_fnc_getParamValue;\n'
  'CHACAL_APPUI_FIXE = ["CHACAL_APPUI_FIXE", 0] call BIS_fnc_getParamValue;',
  "00_socle : trois parametres")

# V6 : le delai du porteur, et son temps reel journalise dans tous les bras
patch(f"{M}/60_phases.sqf",
  "(time - _t > 45 * CHACAL_ECHELLE)",
  "(time - _t > CHACAL_DELAI_PORTEUR * CHACAL_ECHELLE)",
  "60_phases : delai du porteur en parametre")
patch(f"{M}/60_phases.sqf",
  "    private _dH = round (_h distance2D _pt);\n",
  "    private _dH = round (_h distance2D _pt);\n"
  "    (format [\"CHACAL|E|porteur|%1|%2|%3|temps|%4|distance|%5|delai|%6\", round (time * 100) / 100, typeOf _o,\n"
  "        (_h getVariable [\"chacal_role\", \"\"]), round (time - _t), _dH, CHACAL_DELAI_PORTEUR]) call CHACAL_LOG;\n",
  "60_phases : temps reel du porteur journalise")

# V5 : la mitrailleuse, juste avant le premier pas de l assaut
patch(f"{M}/60_phases.sqf",
  "// LE chiffre de Fable : les coups de l appui AVANT le premier pas de l assaut.\n",
  '''// ! V5 ( Fable, 11/09 ) : une mitrailleuse dans l assaut. L ADJOINT echange son fusil contre une Mk200.
if (CHACAL_MG_ASSAUT == 1) then {
    private _mg = (units CHACAL_gAssaut) select { alive _x && { (_x getVariable ["chacal_role", ""]) == "ADJOINT" } };
    if (count _mg == 0) then { _mg = (units CHACAL_gAssaut) select { alive _x && { !((_x getVariable ["chacal_role", ""]) in ["DEMO_1", "DEMO_2"]) } } };
    if (count _mg > 0) then {
        private _u = _mg select 0;
        { _u removeMagazines _x } forEach (getArray (configFile >> "CfgWeapons" >> (primaryWeapon _u) >> "magazines"));
        _u removeWeapon (primaryWeapon _u);
        for "_i" from 1 to 3 do { _u addMagazine "200Rnd_65x39_cased_Box" };
        _u addWeapon "LMG_Mk200_F";
        (format ["CHACAL|E|mg_assaut|%1|role|%2|arme|%3|munitions_chargees|%4|chargeurs_sac|%5", round (time * 100) / 100,
            (_u getVariable ["chacal_role", ""]), primaryWeapon _u, _u ammo "LMG_Mk200_F",
            { _x == "200Rnd_65x39_cased_Box" } count (magazines _u)]) call CHACAL_LOG;
    } else { "CHACAL|AVERT|mg_assaut|aucun_tireur_disponible" call CHACAL_LOG };
};
// LE chiffre de Fable : les coups de l appui AVANT le premier pas de l assaut.
''',
  "60_phases : mitrailleuse a l assaut")

# V9 : l appui fixe, des qu il est en place
patch(f"{M}/60_phases.sqf",
  '''        CHACAL_POS_APPUI = [CHACAL_SITE, CHACAL_OUV_CHOISIE, CHACAL_POS_ASSAUT, CHACAL_OP] call CHACAL_fnc_positionAppui;
    };
''',
  '''        CHACAL_POS_APPUI = [CHACAL_SITE, CHACAL_OUV_CHOISIE, CHACAL_POS_ASSAUT, CHACAL_OP] call CHACAL_fnc_positionAppui;
    };
    // ! V9 ( Fable, 11/09 ) : une fois en place, l appui tient sa place. YELLOW = tir a volonte,
    // garde ta place ; RED = engage a volonte, et on l a mesure partir au contact a 11-18 km/h.
    if (CHACAL_APPUI_FIXE == 1) then {
        [] spawn {
            waitUntil { sleep 2; CHACAL_FIN || { !isNull CHACAL_gAppui && { [CHACAL_gAppui, CHACAL_POS_APPUI, 70] call CHACAL_fnc_enPlace } } };
            if (CHACAL_FIN || { isNull CHACAL_gAppui }) exitWith {};
            CHACAL_gAppui setCombatMode "YELLOW";
            CHACAL_gAppui setVariable ["lambs_danger_disableGroupAI", true, true];
            { if (alive _x) then { _x disableAI "PATH"; _x setVariable ["lambs_danger_disableAI", true, true] } } forEach (units CHACAL_gAppui);
            (format ["CHACAL|E|appui_fixe|%1|position|%2|compromis|%3", round (time * 100) / 100, CHACAL_POS_APPUI,
                (if (CHACAL_COMPROMIS) then {1} else {0})]) call CHACAL_LOG;
        };
    };
''',
  "60_phases : appui fixe une fois en place")
patch(f"{M}/60_phases.sqf",
  'CHACAL_gAppui setBehaviour "COMBAT"; CHACAL_gAppui setCombatMode "RED"; CHACAL_gAppui setSpeedMode "LIMITED";',
  'CHACAL_gAppui setBehaviour "COMBAT"; CHACAL_gAppui setCombatMode (if (CHACAL_APPUI_FIXE == 1) then {"YELLOW"} else {"RED"}); CHACAL_gAppui setSpeedMode "LIMITED";',
  "60_phases : l appui fixe reste en YELLOW a l assaut")
patch(f"{M}/60_phases.sqf",
  'private _compExf = if (CHACAL_COMPROMIS) then {"COMBAT"} else {"AWARE"};',
  '// l appui fixe est rendu a ses jambes pour rentrer\n'
  'if (CHACAL_APPUI_FIXE == 1 && { !isNull CHACAL_gAppui }) then { { _x enableAI "PATH" } forEach (units CHACAL_gAppui) };\n'
  'private _compExf = if (CHACAL_COMPROMIS) then {"COMBAT"} else {"AWARE"};',
  "60_phases : appui rendu a l exfiltration")

# FINI porte les trois leviers
patch(f"{M}/70_verdict.sqf", '|feu_avant|%31",', '|feu_avant|%31|mg_assaut|%32|delai_porteur|%33|appui_fixe|%34",', "70_verdict : format FINI")
patch(f"{M}/70_verdict.sqf", 'CHACAL_FEU_AVANT]) call CHACAL_LOG;', 'CHACAL_FEU_AVANT, CHACAL_MG_ASSAUT, CHACAL_DELAI_PORTEUR, CHACAL_APPUI_FIXE]) call CHACAL_LOG;', "70_verdict : valeurs FINI")

patch(f"{D}/description.ext", '    class CHACAL_FEU_AVANT\n', '''    // ! CAMPAGNE GRAINE 8 ( Fable, 11/09 ) : trois leviers, a 0 / 45 le comportement d origine.
    class CHACAL_MG_ASSAUT
    {
        title = "Mitrailleuse Mk200 a l adjoint de l assaut (0 = non)";
        values[] = {0,1};
        texts[]  = {"NON","OUI"};
        default = 0;
    };
    class CHACAL_DELAI_PORTEUR
    {
        title = "Delai du porteur vers le point de pose, en secondes (45 = origine)";
        values[] = {45,60,90,120,180};
        texts[]  = {"45","60","90","120","180"};
        default = 45;
    };
    class CHACAL_APPUI_FIXE
    {
        title = "Appui fixe en YELLOW une fois en place, LAMBS coupe (0 = non)";
        values[] = {0,1};
        texts[]  = {"NON","OUI"};
        default = 0;
    };
    class CHACAL_FEU_AVANT
''', "description.ext")

patch(L, 'FEU_AVANT=$(lit feu_avant 0);', 'MG_ASSAUT=$(lit mg_assaut 0); DELAI_PORTEUR=$(lit delai_porteur 45); APPUI_FIXE=$(lit appui_fixe 0); FEU_AVANT=$(lit feu_avant 0);', "lancer.sh : lecture")
patch(L, 'ecrire_param FEU_AVANT "$FEU_AVANT";', 'ecrire_param MG_ASSAUT "$MG_ASSAUT"; ecrire_param DELAI_PORTEUR "$DELAI_PORTEUR"; ecrire_param APPUI_FIXE "$APPUI_FIXE"; ecrire_param FEU_AVANT "$FEU_AVANT";', "lancer.sh : ecriture")
