#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-TACTIQUES
# LE SOCLE ET LES TACTIQUES ( document « 8 tactiques de raid », 11/09/2026 ).
#
# CHACAL_SOCLE = 1 : les quatre reparations d execution, sous les tactiques.
#   S1 charges redondantes  : chaque homme de l assaut porte une charge ; releve DEMO_1, DEMO_2, ADJOINT, CHEF, MEDECIN.
#   S3 appui cloue          : feu libre, PATH coupe, LAMBS coupe - il tire sans quitter sa place ( mesure du 10/09 :
#                             en RED il part au contact a 11-18 km/h ).
#   S4 porteurs non combattants : AWARE, AUTOCOMBAT coupe, LAMBS coupe ; chien de garde qui relance l ordre, puis fumigene.
#   S5 reconnaissance par le feu : un defenseur QUI TIRE est revele a l appui. Honnete : il s est trahi lui-meme.
#
# CHACAL_TACTIQUE : 0 socle seul ( reference ), 1 = T1 base de feu, 2 = T2 neutralisation prealable,
#                   5 = T5 infiltration silencieuse.
#   T1 : l appui cloue arrose la position du defenseur connu, reitere toutes les 30 s ( l IA se lasse en ~60 s ),
#        deplace son tir quand l assaut approche a moins de 50 m. L assaut ne part qu APRES le premier coup de l appui.
#   T2 : l appui neutralise les defenseurs un par un ( fusilier-mitrailleur d abord ), 60 s par cible ;
#        l assaut n entre que lorsqu il reste au plus un defenseur, ou au bout de 8 min. Demande l oracle ( job : oracle 1 ).
#   T5 : personne ne tire tant que rien ne nous tire dessus ; a la premiere balle, bascule en T1.
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


if "CHACAL_TACTIQUE" in open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read():
    print("  deja present"); sys.exit(0)

# --- 1. les deux parametres ---------------------------------------------------------------
patch(f"{M}/00_socle.sqf",
      'CHACAL_ORACLE = ["CHACAL_ORACLE", 0] call BIS_fnc_getParamValue;',
      'CHACAL_ORACLE = ["CHACAL_ORACLE", 0] call BIS_fnc_getParamValue;\n'
      '// ! LE SOCLE ET LES TACTIQUES ( 11/09 ). 0 = comportement d origine dans les deux cas.\n'
      'CHACAL_SOCLE = ["CHACAL_SOCLE", 0] call BIS_fnc_getParamValue;\n'
      'CHACAL_TACTIQUE = ["CHACAL_TACTIQUE", 0] call BIS_fnc_getParamValue;\n'
      'CHACAL_CONNUS = [];          // defenseurs qui se sont trahis en tirant\n'
      'CHACAL_T_PREMIER_TIR_APPUI = -1;\n'
      'CHACAL_RELANCES_SOCLE = 0; CHACAL_FUMIGENES = 0;',
      "00_socle : parametres SOCLE et TACTIQUE")

# --- 2. les fonctions ---------------------------------------------------------------------
patch(f"{M}/00_socle.sqf", "CHACAL_fnc_plat = {", '''// ! LE SOCLE : quatre reparations d execution, sous toutes les tactiques ( document du 11/09 ).
// La moitie des echecs mesures sont des pannes d execution, pas des erreurs de tactique.
CHACAL_fnc_socleAssaut = {
    private _ass = (units CHACAL_gAssaut) select { alive _x };
    // S1 : chaque homme de l assaut porte une charge. Le porteur mort a un suivant.
    { if (!("DemoCharge_Remote_Mag" in (magazines _x))) then { _x addMagazine "DemoCharge_Remote_Mag" } } forEach _ass;
    // S4 : les porteurs ne combattent pas. Ce sont eux qui posent ; un porteur qui riposte est un porteur qui s arrete.
    {
        private _r = _x getVariable ["chacal_role", ""];
        if (_r in ["DEMO_1", "DEMO_2", "MEDECIN"]) then {
            _x disableAI "AUTOCOMBAT"; _x setBehaviour "AWARE";
            _x setVariable ["lambs_danger_disableAI", true, true];
        };
    } forEach _ass;
    // S3 : l appui est cloue. Feu libre, mais il ne quitte pas sa place.
    if (!isNull CHACAL_gAppui) then {
        CHACAL_gAppui setBehaviour "COMBAT"; CHACAL_gAppui setCombatMode "RED";
        CHACAL_gAppui setVariable ["lambs_danger_disableGroupAI", true, true];
        {
            if (alive _x) then {
                _x disableAI "PATH"; _x setUnitPos "MIDDLE";
                _x setVariable ["lambs_danger_disableAI", true, true];
                _x addEventHandler ["Fired", {
                    if (CHACAL_T_PREMIER_TIR_APPUI < 0) then { CHACAL_T_PREMIER_TIR_APPUI = time };
                }];
            };
        } forEach (units CHACAL_gAppui);
    };
    // S5 : reconnaissance par le feu. Un defenseur qui TIRE se trahit : on le revele a l appui. Ce n est pas un oracle.
    {
        if (alive _x) then {
            _x addEventHandler ["Fired", {
                params ["_t"];
                if (!(_t in CHACAL_CONNUS)) then {
                    CHACAL_CONNUS pushBack _t;
                    { _x reveal [_t, 4] } forEach ((units CHACAL_gAppui) + (units CHACAL_gAssaut));
                    (format ["CHACAL|E|trahi_par_son_tir|%1|%2|connus|%3", round (time * 100) / 100,
                        (_t getVariable ["chacal_id", -1]), count CHACAL_CONNUS]) call CHACAL_LOG;
                };
            }];
        };
    } forEach CHACAL_EST_SITE;
    (format ["CHACAL|E|socle|%1|porteurs|%2|appui_cloue|%3", round (time * 100) / 100,
        count (_ass select { "DemoCharge_Remote_Mag" in (magazines _x) }),
        (if (isNull CHACAL_gAppui) then {0} else {count (units CHACAL_gAppui)})]) call CHACAL_LOG;
};

// La cible que l appui doit prendre : le fusilier-mitrailleur d abord, puis le chef, puis le reste.
CHACAL_fnc_ciblePrio = {
    private _viv = (CHACAL_EST_SITE select { alive _x });
    if (count _viv == 0) exitWith { objNull };
    private _rang = {
        private _t = typeOf _x;
        if (_t find "_AR_" > -1) then { 0 } else { if (_t find "_TL_" > -1) then { 1 } else { 2 } };
    };
    private _tri = [_viv, [], _rang, "ASCEND"] call BIS_fnc_sortBy;
    _tri select 0
};

// ! LA TACTIQUE, cote APPUI. Elle ne bouge personne : elle designe, elle arrose, elle reitere.
// L IA cesse d engager une cible qui ne tombe pas au bout de ~60 s : tout ordre de feu se reitere.
CHACAL_fnc_tactiqueAppui = {
    private _t0 = time; private _derniere = objNull; private _tCible = 0; private _tSupp = -99;
    while { !CHACAL_FIN && { CHACAL_PHASE == 5 } && { !isNull CHACAL_gAppui } } do {
        private _app = (units CHACAL_gAppui) select { alive _x };
        if (count _app == 0) exitWith {};
        private _viv = CHACAL_EST_SITE select { alive _x };
        if (CHACAL_TACTIQUE == 2) then {
            // T2 : une cible a la fois, 60 s au plus, le fusilier-mitrailleur d abord.
            if (isNull _derniere || { !alive _derniere } || { time - _tCible > 60 }) then {
                _derniere = call CHACAL_fnc_ciblePrio; _tCible = time;
                if (!isNull _derniere) then {
                    (format ["CHACAL|E|cible_designee|%1|%2|restants|%3", round (time * 100) / 100,
                        (_derniere getVariable ["chacal_id", -1]), count _viv]) call CHACAL_LOG;
                };
            };
            if (!isNull _derniere) then {
                { _x reveal [_derniere, 4]; _x doTarget _derniere; _x doFire _derniere } forEach _app;
            };
        } else {
            // T1 et T5 apres bascule : arroser la position du defenseur connu le plus proche de l assaut,
            // sauf si l assaut est a moins de 50 m de cette position ( on deplace alors le tir ).
            private _cn = CHACAL_CONNUS select { alive _x };
            if (count _cn > 0) then {
                private _ca = ((units CHACAL_gAssaut) select { alive _x }) call CHACAL_fnc_centre;
                private _cible = objNull; private _dmax = -1;
                {
                    private _d = if (count _ca > 0) then { _x distance2D _ca } else { 999 };
                    if (_d > 50 && { _d > _dmax }) then { _dmax = _d; _cible = _x };
                } forEach _cn;
                if (!isNull _cible && { time - _tSupp > 30 }) then {
                    _tSupp = time;
                    { _x reveal [_cible, 4]; _x doTarget _cible; _x doFire _cible;
                      _x doSuppressiveFire (getPosATL _cible) } forEach _app;
                    (format ["CHACAL|E|suppression|%1|%2|distance_assaut|%3", round (time * 100) / 100,
                        (_cible getVariable ["chacal_id", -1]), round _dmax]) call CHACAL_LOG;
                };
            };
        };
        sleep 5;
    };
};

// ! LE CHIEN DE GARDE ( S4 ). Un assaut qui n avance plus recoit son ordre une seconde fois ; au deuxieme
// echec, un fumigene tombe entre lui et le defenseur connu le plus proche. « Tout ce qui fige un homme coute ».
CHACAL_fnc_chienDeGarde = {
    private _dRef = 1e9; private _tRef = time; private _rates = 0;
    while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {
        sleep 10;
        if (count CHACAL_CIBLE_ASSAUT > 0 && { !isNull CHACAL_gAssaut }) then {
            private _v = (units CHACAL_gAssaut) select { alive _x };
            if (count _v > 0) then {
                private _c = _v call CHACAL_fnc_centre;
                private _d = _c distance2D CHACAL_CIBLE_ASSAUT;
                if (_d < _dRef - 5) then { _dRef = _d; _tRef = time; _rates = 0 }
                else {
                    if (time - _tRef > 30) then {
                        _tRef = time; _rates = _rates + 1; CHACAL_RELANCES_SOCLE = CHACAL_RELANCES_SOCLE + 1;
                        CHACAL_gAssaut setBehaviour "AWARE";
                        { if (alive _x) then { _x doMove CHACAL_CIBLE_ASSAUT } } forEach _v;
                        (format ["CHACAL|E|chien_de_garde|%1|relance|%2|reste|%3", round (time * 100) / 100,
                            _rates, round _d]) call CHACAL_LOG;
                        if (_rates >= 2) then {
                            private _cn = CHACAL_CONNUS select { alive _x };
                            private _vers = if (count _cn > 0) then { getPosATL (_cn select 0) } else { CHACAL_CIBLE_ASSAUT };
                            private _p = _c getPos [25, _c getDir _vers];
                            createVehicle ["SmokeShell", _p, [], 0, "CAN_COLLIDE"];
                            CHACAL_FUMIGENES = CHACAL_FUMIGENES + 1; _rates = 0;
                            (format ["CHACAL|E|fumigene|%1|entre|%2|et|%3", round (time * 100) / 100, str _p, str _vers]) call CHACAL_LOG;
                        };
                    };
                };
            };
        };
    };
};

CHACAL_fnc_plat = {''', "00_socle : socle, cible prioritaire, tactique de l appui, chien de garde")

# --- 3. les branchements en phase 5 --------------------------------------------------------
patch(f"{M}/60_phases.sqf",
      '''// ! LE FEU AVANT LE MOUVEMENT ( Fable, 10/09 ).''',
      '''// ! LE SOCLE ET LA TACTIQUE ( document du 11/09 ). Le socle repare l execution, la tactique conduit l appui.
if (CHACAL_SOCLE == 1) then { call CHACAL_fnc_socleAssaut };
if (CHACAL_TACTIQUE == 5) then {
    // T5 : personne ne tire tant que rien ne nous tire dessus. A la premiere balle, on bascule en T1.
    { if (!isNull _x) then { _x setCombatMode "GREEN" } } forEach [CHACAL_gAppui, CHACAL_gAssaut, CHACAL_gBouchon];
    CHACAL_gAssaut setBehaviour "STEALTH";
    [] spawn {
        waitUntil { sleep 2; CHACAL_FIN || { CHACAL_PHASE != 5 } || { count CHACAL_CONNUS > 0 } || CHACAL_COMPROMIS };
        if (CHACAL_FIN || { CHACAL_PHASE != 5 }) exitWith {};
        CHACAL_TACTIQUE = 1;
        { if (!isNull _x) then { _x setCombatMode "RED" } } forEach [CHACAL_gAppui, CHACAL_gBouchon];
        CHACAL_gAssaut setBehaviour "AWARE"; CHACAL_gAssaut setCombatMode "YELLOW";
        (format ["CHACAL|E|bascule_t5_vers_t1|%1|connus|%2|compromis|%3", round (time * 100) / 100,
            count CHACAL_CONNUS, (if (CHACAL_COMPROMIS) then {1} else {0})]) call CHACAL_LOG;
    };
};
if (CHACAL_TACTIQUE > 0) then { [] spawn CHACAL_fnc_tactiqueAppui };
if (CHACAL_SOCLE == 1) then { [] spawn CHACAL_fnc_chienDeGarde };
// L assaut attend : T1 le premier coup de l appui ( 120 s au plus ), T2 qu il ne reste au plus qu un defenseur ( 8 min ).
if (CHACAL_TACTIQUE == 1) then {
    private _tA = time;
    waitUntil { sleep 1; (CHACAL_T_PREMIER_TIR_APPUI > 0) || { time - _tA > 120 } || CHACAL_FIN };
    sleep 5;
    (format ["CHACAL|E|t1_depart|%1|premier_tir_appui|%2|attente|%3", round (time * 100) / 100,
        round CHACAL_T_PREMIER_TIR_APPUI, round (time - _tA)]) call CHACAL_LOG;
};
if (CHACAL_TACTIQUE == 2) then {
    private _tA = time;
    waitUntil { sleep 2; (count (CHACAL_EST_SITE select { alive _x }) <= 1) || { time - _tA > 480 } || CHACAL_FIN };
    (format ["CHACAL|E|t2_depart|%1|defenseurs_restants|%2|attente|%3", round (time * 100) / 100,
        count (CHACAL_EST_SITE select { alive _x }), round (time - _tA)]) call CHACAL_LOG;
};

// ! LE FEU AVANT LE MOUVEMENT ( Fable, 10/09 ).''', "60_phases : branchement du socle et des tactiques")

patch(f"{M}/60_phases.sqf",
      'CHACAL_COMP_ASSAUT = if (CHACAL_FEU_AVANT == 1) then {"AWARE"} else {"COMBAT"};',
      '// Une tactique marche en AWARE : le mode COMBAT fige l assaut ( plus de 120 s mesurees a 65 m de la tour ).\n'
      'CHACAL_COMP_ASSAUT = if (CHACAL_FEU_AVANT == 1 || { CHACAL_TACTIQUE > 0 }) then {"AWARE"} else {"COMBAT"};',
      "60_phases : l assaut marche en AWARE sous tactique")

patch(f"{M}/60_phases.sqf",
      'if (CHACAL_FEU_AVANT == 1) then {\n    [] spawn {\n        while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {\n            sleep 10;',
      'if (CHACAL_FEU_AVANT == 1 || { CHACAL_TACTIQUE > 0 }) then {\n    [] spawn {\n        while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {\n            sleep 10;',
      "60_phases : relance de l ordre sous tactique")

# S1 : la releve des porteurs suit un ordre ecrit d avance
patch(f"{M}/60_phases.sqf",
      'private _demo = _porteurs select { (_x getVariable ["chacal_role", ""]) in ["DEMO_1", "DEMO_2"] };\n'
      '    private _h = if (count _demo > 0) then { _demo select 0 } else { _porteurs select 0 };',
      '// ! S1 ( 11/09 ) : la releve est ecrite d avance - DEMO_1, DEMO_2, ADJOINT, CHEF, MEDECIN - et chaque homme\n'
      '    // de l assaut porte une charge, donc un porteur mort a toujours un suivant.\n'
      '    private _ordreP = ["DEMO_1", "DEMO_2", "ADJOINT", "CHEF", "MEDECIN"];\n'
      '    private _demo = [];\n'
      '    { private _r = _x; { if ((_x getVariable ["chacal_role", ""]) == _r) then { _demo pushBack _x } } forEach _porteurs } forEach _ordreP;\n'
      '    private _h = if (count _demo > 0) then { _demo select 0 } else { _porteurs select 0 };',
      "60_phases : releve des porteurs dans l ordre ecrit")

# --- 4. la ligne FINI porte les deux leviers et les compteurs ------------------------------
patch(f"{M}/70_verdict.sqf", '|oracle|%35",', '|oracle|%35|socle|%36|tactique|%37|relances|%38|fumigenes|%39",', "70_verdict : format FINI")
patch(f"{M}/70_verdict.sqf", 'CHACAL_ORACLE]) call CHACAL_LOG;',
      'CHACAL_ORACLE, CHACAL_SOCLE, CHACAL_TACTIQUE, CHACAL_RELANCES_SOCLE, CHACAL_FUMIGENES]) call CHACAL_LOG;',
      "70_verdict : valeurs FINI")

# --- 5. declaration et lanceur --------------------------------------------------------------
patch(f"{D}/description.ext", '    class CHACAL_ORACLE\n', '''    // ! LE SOCLE ( quatre reparations d execution ) et LA TACTIQUE ( 11/09 ).
    class CHACAL_SOCLE
    {
        title = "Socle : charges redondantes, porteurs non combattants, appui cloue, chien de garde (0 = non)";
        values[] = {0,1};
        texts[]  = {"NON","OUI"};
        default = 0;
    };
    class CHACAL_TACTIQUE
    {
        title = "Tactique : 0 socle seul, 1 base de feu, 2 neutralisation prealable, 5 infiltration";
        values[] = {0,1,2,5};
        texts[]  = {"SOCLE","T1","T2","T5"};
        default = 0;
    };
    class CHACAL_ORACLE
''', "description.ext")
patch(L, 'ORACLE=$(lit oracle 0);', 'SOCLE=$(lit socle 0); TACTIQUE=$(lit tactique 0); ORACLE=$(lit oracle 0);', "lancer.sh : lecture")
patch(L, 'ecrire_param ORACLE "$ORACLE";', 'ecrire_param SOCLE "$SOCLE"; ecrire_param TACTIQUE "$TACTIQUE"; ecrire_param ORACLE "$ORACLE";', "lancer.sh : ecriture")
