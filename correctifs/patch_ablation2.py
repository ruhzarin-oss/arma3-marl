#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-ABLATION2
#
# ABLATION DU SOCLE, PAR RETRAIT ( revue du 12/09 : quatre relecteurs ont refuse la version « par ajout » ).
# Le socle complet marche ( 29 reussites sur 37 contre 1 sur 10 ). On ne demande donc pas « qu est-ce qui suffit ? »
# mais « qu est-ce qui MANQUE quand on l enleve ? » : chaque bras retire UNE piece, tout le reste en place.
# Le bras « S1 seul » de la premiere version etait vide de sens : quatre hommes sur cinq portent deja une charge
# dans la dotation d origine, la redondance n ajoutait presque rien.
#
# CHACAL_ABLATION est un masque de ce qu on RETIRE :
#   0 = rien ( socle complet )        1 = sans le chien de garde ( ni relance ni fumigene )
#   2 = sans porteurs non combattants ( ils se battent comme avant )
#   4 = sans l appui cloue ( il reste en RED libre de ses jambes, comme au 10/09 )
#   8 = sans la revelation par le tir ( l appui n apprend rien des defenseurs qui tirent )
# Les valeurs se combinent ; les jobs de la nuit ( ablation 0 ) restent comparables.
import sys

M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
D = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis"
L = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"


def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))


def patch(path, avant, apres, quoi):
    s = open(path, encoding="utf-8", errors="surrogateescape").read()
    if s.count(avant) != 1:
        print("  !! motif x%d : %s" % (s.count(avant), quoi)); sys.exit(1)
    s2 = s.replace(avant, apres, 1)
    if path.endswith(".sqf") and bilan(s) != bilan(s2):
        print("  !! equilibre %s -> %s : %s" % (bilan(s), bilan(s2), quoi)); sys.exit(1)
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE :", quoi)


if "CHACAL_ABLATION" in open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read():
    print("  deja present"); sys.exit(0)

patch(f"{M}/00_socle.sqf",
      'CHACAL_TACTIQUE = ["CHACAL_TACTIQUE", 0] call BIS_fnc_getParamValue;',
      'CHACAL_TACTIQUE = ["CHACAL_TACTIQUE", 0] call BIS_fnc_getParamValue;\n'
      '// ! ABLATION PAR RETRAIT ( revue du 12/09 ) : masque de ce qu on ENLEVE au socle.\n'
      '//   1 sans chien de garde . 2 sans porteurs non combattants . 4 sans appui cloue . 8 sans revelation par le tir.\n'
      'CHACAL_ABLATION = ["CHACAL_ABLATION", 0] call BIS_fnc_getParamValue;\n'
      'CHACAL_fnc_sans = { (floor (CHACAL_ABLATION / _this)) % 2 == 1 };   // _this = le bit teste',
      "00_socle : parametre ABLATION par retrait")

# --- S4 porteurs ( bit 2 ) ET S3 appui cloue ( bit 4 ) : UNE SEULE substitution, pour que les accolades
# restent equilibrees a chaque etape ( la garde a refuse la version en deux morceaux ) ---
patch(f"{M}/00_socle.sqf",
      '''    // S4 : les porteurs ne combattent pas. Ce sont eux qui posent ; un porteur qui riposte est un porteur qui s arrete.
    {
        private _r = _x getVariable ["chacal_role", ""];
        if (_r in ["DEMO_1", "DEMO_2", "MEDECIN"]) then {
            _x disableAI "AUTOCOMBAT"; _x setBehaviour "AWARE";
            _x setVariable ["lambs_danger_disableAI", true, true];
        };
    } forEach _ass;
    // S3 : l appui est cloue. Feu libre, mais il ne quitte pas sa place.
    if (!isNull CHACAL_gAppui) then {''',
      '''    // S4 : les porteurs ne combattent pas. Ce sont eux qui posent ; un porteur qui riposte est un porteur qui s arrete.
    if !(2 call CHACAL_fnc_sans) then {
        {
            private _r = _x getVariable ["chacal_role", ""];
            if (_r in ["DEMO_1", "DEMO_2", "MEDECIN"]) then {
                _x disableAI "AUTOCOMBAT"; _x setBehaviour "AWARE";
                _x setVariable ["lambs_danger_disableAI", true, true];
            };
        } forEach _ass;
    };
    // S3 : l appui est cloue. Feu libre, mais il ne quitte pas sa place.
    if (!isNull CHACAL_gAppui && { !(4 call CHACAL_fnc_sans) }) then {''',
      "00_socle : porteurs sous le bit 2 et appui cloue sous le bit 4")

# --- S5 : la revelation par le tir ( bit 8 ) ---
patch(f"{M}/00_socle.sqf",
      '''    {
        if (alive _x) then {
            _x addEventHandler ["Fired", {
                params ["_t"];
                if (!(_t in CHACAL_CONNUS)) then {''',
      '''    {
        if (alive _x && { !(8 call CHACAL_fnc_sans) }) then {
            _x addEventHandler ["Fired", {
                params ["_t"];
                if (!(_t in CHACAL_CONNUS)) then {''',
      "00_socle : revelation par le tir sous le bit 8")

# --- la ligne socle dit ce qui a ete pose ---
patch(f"{M}/00_socle.sqf",
      '''    (format ["CHACAL|E|socle|%1|porteurs|%2|appui_cloue|%3", round (time * 100) / 100,
        count (_ass select { "DemoCharge_Remote_Mag" in (magazines _x) }),
        (if (isNull CHACAL_gAppui) then {0} else {count (units CHACAL_gAppui)})]) call CHACAL_LOG;''',
      '''    (format ["CHACAL|E|socle|%1|porteurs|%2|appui_cloue|%3|ablation|%4|sans_chien|%5|sans_porteurs|%6|sans_appui|%7|sans_revelation|%8",
        round (time * 100) / 100,
        count (_ass select { "DemoCharge_Remote_Mag" in (magazines _x) }),
        (if (isNull CHACAL_gAppui || { 4 call CHACAL_fnc_sans }) then {0} else {count (units CHACAL_gAppui)}),
        CHACAL_ABLATION,
        (if (1 call CHACAL_fnc_sans) then {1} else {0}), (if (2 call CHACAL_fnc_sans) then {1} else {0}),
        (if (4 call CHACAL_fnc_sans) then {1} else {0}), (if (8 call CHACAL_fnc_sans) then {1} else {0})]) call CHACAL_LOG;''',
      "00_socle : la ligne socle porte ce qui a ete pose")

# --- le chien de garde ( bit 1 ) ---
patch(f"{M}/60_phases.sqf",
      "if (CHACAL_SOCLE == 1) then { [] spawn CHACAL_fnc_chienDeGarde };",
      "if (CHACAL_SOCLE == 1 && { !(1 call CHACAL_fnc_sans) }) then { [] spawn CHACAL_fnc_chienDeGarde };",
      "60_phases : chien de garde sous le bit 1")

# --- la ligne FINI porte l ablation ---
patch(f"{M}/70_verdict.sqf", '|zones|%40",', '|zones|%40|ablation|%41",', "70_verdict : format FINI")
patch(f"{M}/70_verdict.sqf", "CHACAL_RELANCES_SOCLE, CHACAL_FUMIGENES, CHACAL_ZONES]) call CHACAL_LOG;",
      "CHACAL_RELANCES_SOCLE, CHACAL_FUMIGENES, CHACAL_ZONES, CHACAL_ABLATION]) call CHACAL_LOG;",
      "70_verdict : valeurs FINI")

patch(f"{D}/description.ext", '    class CHACAL_SOCLE\n', '''    // ! ABLATION PAR RETRAIT ( revue du 12/09 ) : masque de ce qu on enleve au socle.
    class CHACAL_ABLATION
    {
        title = "Ablation : 0 socle complet, 1 sans chien de garde, 2 sans porteurs non combattants, 4 sans appui cloue, 8 sans revelation";
        values[] = {0,1,2,4,8};
        texts[]  = {"COMPLET","SANS CHIEN","SANS PORTEURS","SANS APPUI CLOUE","SANS REVELATION"};
        default = 0;
    };
    class CHACAL_SOCLE
''', "description.ext")
patch(L, 'SOCLE=$(lit socle 0);', 'ABLATION=$(lit ablation 0); SOCLE=$(lit socle 0);', "lancer.sh : lecture")
patch(L, 'ecrire_param SOCLE "$SOCLE";', 'ecrire_param ABLATION "$ABLATION"; ecrire_param SOCLE "$SOCLE";', "lancer.sh : ecriture")

# --- le catalogue connait les nouveaux leviers ( defaut « a_corriger » de la revue ) ---
CAT = "/mnt/data/hmt/depot/outils/catalogue.py"
c = open(CAT).read()
if '"socle"' not in c:
    a = '"accessible", "effectif", "oracle"]'
    assert c.count(a) == 1
    c = c.replace(a, '"accessible", "effectif", "oracle", "socle", "tactique", "ablation"]')
    open(CAT, "w").write(c)
    print("  PATCHE : catalogue : leviers socle, tactique, ablation")
