#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-FEU-AVANT
# CHACAL_FEU_AVANT ( plan de Fable, 10/09/2026 ) : LE FEU AVANT LE MOUVEMENT.
#
# Mesure : sur les echecs du palier 4, UN fusilier fait 8 des 9 morts ; nos dix hommes ne tirent
# presque pas ; l appui zero. L appui recevait `doTarget` sur une cible qu il ne CONNAISSAIT pas
# ( la restitution ne donne que ce que la reco a vu ) : un doTarget sur un inconnu ne tire pas.
# Et l assaut, en COMBAT, se fige plus de 120 s a 65 m de la tour, ordre donne une seule fois.
#
# A 1 :
#   . les defenseurs du site sont REVELES a l appui, la cible designee est le defenseur vivant le
#     plus proche de l endroit ou va l assaut, feu libre ; la designation est relancee toutes les 5 s ;
#   . l assaut ne fait son premier pas qu APRES le premier coup de l appui ( 120 s au plus ) ;
#   . l assaut marche en AWARE et non en COMBAT, et son ordre est relance toutes les 10 s.
# A 0 : rien ne change. Le compteur de coups de l appui tourne dans les deux bras, il ne fait
# que compter : le chiffre de Fable « coups de l appui avant le premier pas » existe partout.
import sys, shutil, os

M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
D = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis"
L = "/mnt/data/hmt/depot/bancs/chacal/lancer.sh"

def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))

def patch(path, avant, apres, quoi):
    s = open(path, encoding="utf-8", errors="surrogateescape").read()
    n = s.count(avant)
    if n != 1:
        print("  !! motif x%d : %s" % (n, quoi)); sys.exit(1)
    b0 = bilan(s); s2 = s.replace(avant, apres, 1); b1 = bilan(s2)
    if b0 != b1 and path.endswith(".sqf"):
        print("  !! equilibre change %s -> %s : %s" % (b0, b1, quoi)); sys.exit(1)
    if not os.path.exists(path + ".avant-feuavant"): shutil.copy2(path, path + ".avant-feuavant")
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(s2)
    print("  PATCHE :", quoi)

s = open(f"{M}/60_phases.sqf", encoding="utf-8", errors="surrogateescape").read()
if "CHACAL_FEU_AVANT" in s:
    print("  deja present"); sys.exit(0)

# 1. le parametre
patch(f"{M}/00_socle.sqf",
  'CHACAL_APPUI_FEU = ["CHACAL_APPUI_FEU", 0] call BIS_fnc_getParamValue;',
  'CHACAL_APPUI_FEU = ["CHACAL_APPUI_FEU", 0] call BIS_fnc_getParamValue;\n'
  '// ! CHACAL_FEU_AVANT ( Fable, 10/09 ) : l appui connait et vise les defenseurs, l assaut attend son\n'
  '// premier coup, puis marche en AWARE avec un ordre relance toutes les 10 s. 0 = comportement d origine.\n'
  'CHACAL_FEU_AVANT = ["CHACAL_FEU_AVANT", 0] call BIS_fnc_getParamValue;',
  "00_socle : lecture de CHACAL_FEU_AVANT")

# 2. le feu avant le mouvement : juste apres l ordre d origine a l appui, avant l attente de 8 s
patch(f"{M}/60_phases.sqf",
  '''    { if (alive _x && { count _cibles > 0 }) then { _x doTarget (_cibles select 0); _x doFire (_cibles select 0) } } forEach (units CHACAL_gAppui);
};
sleep (8 * CHACAL_ECHELLE);''',
  '''    { if (alive _x && { count _cibles > 0 }) then { _x doTarget (_cibles select 0); _x doFire (_cibles select 0) } } forEach (units CHACAL_gAppui);
};

// ! LE FEU AVANT LE MOUVEMENT ( Fable, 10/09 ). Sur les echecs du palier 4, un seul fusilier
// fait 8 des 9 morts et l appui ne tire pas : il visait une cible qu il ne connaissait pas.
// Le compteur tourne dans les deux bras ; la designation et l attente seulement a FEU_AVANT = 1.
CHACAL_TIRS_APPUI = 0; CHACAL_T_PREMIER_TIR = -1; CHACAL_CIBLE_ASSAUT = []; CHACAL_RELANCES = 0;
if (!isNull CHACAL_gAppui) then {
    {
        _x addEventHandler ["Fired", {
            CHACAL_TIRS_APPUI = CHACAL_TIRS_APPUI + 1;
            if (CHACAL_T_PREMIER_TIR < 0) then { CHACAL_T_PREMIER_TIR = time };
        }];
    } forEach ((units CHACAL_gAppui) select { alive _x });
};
if (CHACAL_FEU_AVANT == 1 && { !isNull CHACAL_gAppui }) then {
    [] spawn {
        while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {
            private _def = CHACAL_EST_SITE select { alive _x };
            private _ref = if (count CHACAL_CIBLE_ASSAUT > 0) then { CHACAL_CIBLE_ASSAUT } else { CHACAL_OUV_CHOISIE };
            if (count _def > 0) then {
                _def = [_def, [_ref], { _x distance2D _input0 }, "ASCEND"] call BIS_fnc_sortBy;
                private _c = _def select 0;
                {
                    private _u = _x;
                    if (alive _u) then {
                        { _u reveal [_x, 4] } forEach _def;
                        _u doTarget _c; _u doFire _c;
                    };
                } forEach (units CHACAL_gAppui);
            };
            sleep 5;
        };
    };
    private _tG = time;
    waitUntil { sleep 1; (CHACAL_TIRS_APPUI > 0) || { (time - _tG) > (120 * CHACAL_ECHELLE) } || { CHACAL_FIN } };
    (format ["CHACAL|E|feu_avant|%1|premier_tir|%2|attente|%3|defenseurs_vivants|%4", round (time * 100) / 100,
        (if (CHACAL_T_PREMIER_TIR < 0) then {-1} else {round (CHACAL_T_PREMIER_TIR * 100) / 100}),
        round (time - _tG), count (CHACAL_EST_SITE select { alive _x })]) call CHACAL_LOG;
};
sleep (8 * CHACAL_ECHELLE);''',
  "60_phases : l appui connait sa cible, l assaut attend le premier coup")

# 3. le premier pas de l assaut, en AWARE a FEU_AVANT = 1, et la relance toutes les 10 s
patch(f"{M}/60_phases.sqf",
  '''CHACAL_gAssaut setBehaviour "COMBAT"; CHACAL_gAssaut setCombatMode "RED"; CHACAL_gAssaut setSpeedMode "FULL";
[CHACAL_gAssaut, CHACAL_OUV_CHOISIE, "FULL", "COMBAT", "WEDGE", "OUVERTURE_CHOISIE"] call CHACAL_fnc_ordreAller;''',
  '''// LE chiffre de Fable : les coups de l appui AVANT le premier pas de l assaut.
(format ["CHACAL|E|premier_pas_assaut|%1|tirs_appui_avant|%2|feu_avant|%3", round (time * 100) / 100,
    CHACAL_TIRS_APPUI, CHACAL_FEU_AVANT]) call CHACAL_LOG;
// ! Le mode COMBAT fige l assaut ( plus de 120 s immobile a 65 m de la tour ). A FEU_AVANT = 1 il
// marche en AWARE, et un ordre donne une seule fois est relance toutes les 10 s.
CHACAL_COMP_ASSAUT = if (CHACAL_FEU_AVANT == 1) then {"AWARE"} else {"COMBAT"};
CHACAL_gAssaut setBehaviour CHACAL_COMP_ASSAUT; CHACAL_gAssaut setCombatMode "RED"; CHACAL_gAssaut setSpeedMode "FULL";
CHACAL_CIBLE_ASSAUT = +CHACAL_OUV_CHOISIE;
[CHACAL_gAssaut, CHACAL_OUV_CHOISIE, "FULL", CHACAL_COMP_ASSAUT, "WEDGE", "OUVERTURE_CHOISIE"] call CHACAL_fnc_ordreAller;
if (CHACAL_FEU_AVANT == 1) then {
    [] spawn {
        while { !CHACAL_FIN && { CHACAL_PHASE == 5 } } do {
            sleep 10;
            if (count CHACAL_CIBLE_ASSAUT > 0 && { !isNull CHACAL_gAssaut }) then {
                CHACAL_gAssaut setBehaviour "AWARE";
                { if (alive _x) then { _x doMove CHACAL_CIBLE_ASSAUT } } forEach (units CHACAL_gAssaut);
                CHACAL_RELANCES = CHACAL_RELANCES + 1;
            };
        };
    };
};''',
  "60_phases : premier pas journalise, assaut en AWARE, ordre relance")

patch(f"{M}/60_phases.sqf",
  '''    [CHACAL_gAssaut, _pt, "FULL", "COMBAT", "WEDGE", "OBJECTIF_" + (typeOf _o)] call CHACAL_fnc_ordreAller;''',
  '''    CHACAL_CIBLE_ASSAUT = +_pt;
    [CHACAL_gAssaut, _pt, "FULL", CHACAL_COMP_ASSAUT, "WEDGE", "OBJECTIF_" + (typeOf _o)] call CHACAL_fnc_ordreAller;''',
  "60_phases : chaque objectif suit le mode de l assaut")

patch(f"{M}/60_phases.sqf",
  '''[CHACAL_gAssaut, _abri, "FULL", "COMBAT", "WEDGE", "DEGAGEMENT_AVANT_MISE_A_FEU"] call CHACAL_fnc_ordreAller;''',
  '''CHACAL_CIBLE_ASSAUT = +_abri;
[CHACAL_gAssaut, _abri, "FULL", CHACAL_COMP_ASSAUT, "WEDGE", "DEGAGEMENT_AVANT_MISE_A_FEU"] call CHACAL_fnc_ordreAller;''',
  "60_phases : le degagement aussi")

patch(f"{M}/60_phases.sqf",
  '''[5, "ASSAUT", _iss5] call CHACAL_fnc_finPhase;''',
  '''(format ["CHACAL|E|feu_appui_total|%1|tirs_appui|%2|relances_assaut|%3|feu_avant|%4", round (time * 100) / 100,
    CHACAL_TIRS_APPUI, CHACAL_RELANCES, CHACAL_FEU_AVANT]) call CHACAL_LOG;
[5, "ASSAUT", _iss5] call CHACAL_fnc_finPhase;''',
  "60_phases : total des coups de l appui en fin d assaut")

# 4. declaration
patch(f"{D}/description.ext",
  '    class CHACAL_APPUI_FEU\n',
  '''    // ! LE FEU AVANT LE MOUVEMENT ( Fable, 10/09 ) : l appui connait et vise les defenseurs,
    // l assaut attend son premier coup, marche en AWARE, ordre relance toutes les 10 s.
    class CHACAL_FEU_AVANT
    {
        title = "Feu de l appui avant le mouvement de l assaut (0 = origine)";
        values[] = {0,1};
        texts[]  = {"NON","OUI"};
        default = 0;
    };
    class CHACAL_APPUI_FEU
''',
  "description.ext")

# 5. lanceur
patch(L, 'APPUI_FEU=$(lit appui_feu 0);', 'FEU_AVANT=$(lit feu_avant 0); APPUI_FEU=$(lit appui_feu 0);', "lancer.sh : lecture")
patch(L, 'ecrire_param APPUI_FEU "$APPUI_FEU";', 'ecrire_param FEU_AVANT "$FEU_AVANT"; ecrire_param APPUI_FEU "$APPUI_FEU";', "lancer.sh : ecriture")
