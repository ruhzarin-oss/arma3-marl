#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-PLACEUR-PLANCHER
#
# LE PLACEUR D APPUI BATTAIT L OUVERTURE, PAS LE SITE.
# Banc de certification du 12/09, 40 episodes : 79 postes sur 80 ne voient AUCUN defenseur sur 4, et le seul tireur
# cloue qui en voyait un est exactement le seul qui a tire ( 1/1 contre 0/39, p = 0,025 ). Le contraste brut
# « cloue 1/20 contre libre 18/20 » n opposait donc pas deux reglages de tir : il opposait un homme immobilise sur un
# poste aveugle a une patrouille qui marche 459 m et finit a 108 m du site, c est-a-dire qui cesse d etre un appui.
#
# CHACAL_PLACEUR = 1 : la position d appui est choisie sur ce qu elle BAT A L INTERIEUR du site.
#   37 points fixes ( centre + anneaux a 0,30 R, 0,60 R, 0,85 R, a 8, 12 et 16 points ), poses a 1,1 m du sol.
#   COUV = part de ces points que l oeil atteint depuis le candidat ( oeil a 1,5 m ), par lineIntersectsSurfaces.
#   Deux etages, pour ne pas payer 37 rayons par candidat : filtres geometriques d abord ( eau, relief, portee
#   150-350 m, ecart 40-120 degres de l axe d assaut ), puis les 24 meilleurs par le GAIN D ALTITUDE SUR LE SOL DU
#   SITE - et non sur l ouverture, ce qui mentait de 1,5 a 3,4 m.
#   Score : 3*COUV + gain/20 - |D-250|/250 - relief/12.
#   ET IL SAIT DIRE NON : si le meilleur COUV reste sous 0,25, on l ecrit et on ne pretend pas avoir un appui.
# A 0 : l ancien placeur, inchange, pour que le contraste A/B soit propre.
#
# Le banc de certification gagne trois instruments reclames par la revue : la serie des defenseurs vus toutes les
# 10 s ( et non un seul instantane ), le mode de tir reellement applique, et l objet qui coupe le rayon.
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


if "CHACAL_PLACEUR" in open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read():
    print("  deja present"); sys.exit(0)

patch(f"{M}/00_socle.sqf",
      'CHACAL_BANC_APPUI = ["CHACAL_BANC_APPUI", 0] call BIS_fnc_getParamValue;',
      '// ! LE PLACEUR ( banc du 12/09 ) : 0 = ancien ( vue sur l ouverture ), 1 = nouveau ( bat le plancher du site ).\n'
      'CHACAL_PLACEUR = ["CHACAL_PLACEUR", 0] call BIS_fnc_getParamValue;\n'
      'CHACAL_COUV = -1;   // part des points interieurs battus depuis la position retenue\n'
      'CHACAL_BANC_APPUI = ["CHACAL_BANC_APPUI", 0] call BIS_fnc_getParamValue;',
      "00_socle : parametre PLACEUR")

# --- le plancher : 37 points interieurs, et la couverture d un candidat ---------------------
patch(f"{M}/00_socle.sqf", "CHACAL_fnc_positionAppui = {",
      '''// ! LE PLANCHER DU SITE : 37 points fixes a l interieur, a 1,1 m du sol, la ou des hommes se tiennent.
// Aucune connaissance des defenseurs : c est de la geometrie, disponible au moment du choix.
CHACAL_fnc_plancher = {
    private _R = 45;
    if (count CHACAL_OBJETS > 0) then {
        { _R = _R max ((_x distance2D CHACAL_SITE) + 15) } forEach CHACAL_OBJETS;
    };
    _R = (_R max 30) min 80;
    private _pts = [];
    private _c = +CHACAL_SITE; _c set [2, (getTerrainHeightASL CHACAL_SITE) + 1.1];
    _pts pushBack _c;
    {
        _x params ["_r", "_n", "_dec"];
        for "_i" from 0 to (_n - 1) do {
            private _p = CHACAL_SITE getPos [_R * _r, _dec + (_i * 360 / _n)];
            _p set [2, (getTerrainHeightASL _p) + 1.1];
            _pts pushBack _p;
        };
    } forEach [[0.30, 8, 0], [0.60, 12, 15], [0.85, 16, 7]];
    _pts
};

// La couverture d un candidat : la part du plancher que son oeil atteint. 0 = il ne bat rien, 1 = il bat tout.
CHACAL_fnc_couverture = {
    params ["_p", "_plancher"];
    private _oeil = +_p; _oeil set [2, (getTerrainHeightASL _p) + 1.5];
    private _n = 0;
    { if (count (lineIntersectsSurfaces [_oeil, _x, objNull, objNull, true, 1]) == 0) then { _n = _n + 1 } } forEach _plancher;
    _n / (count _plancher)
};

CHACAL_fnc_positionAppui = {''', "00_socle : le plancher et la couverture")

# --- le choix : deux etages, et le droit de dire non ----------------------------------------
patch(f"{M}/00_socle.sqf",
      '''    params ["_site", "_ouverture", "_axeAssaut", "_repli"];
    private _azOuv = _site getDir _ouverture;''',
      '''    params ["_site", "_ouverture", "_axeAssaut", "_repli"];
    private _azOuv = _site getDir _ouverture;
    // ! PLACEUR QUI BAT LE PLANCHER ( 12/09 ). L ancien certifiait la vue vers l OUVERTURE : 79 postes sur 80
    // ne voyaient aucun defenseur, et l appui s est tu dans quatre mesures d affilee.
    if (CHACAL_PLACEUR == 1) exitWith {
        private _plancher = call CHACAL_fnc_plancher;
        private _solSite = getTerrainHeightASL _site;
        private _cands = [];
        for "_i" from 1 to 220 do {
            private _cote = if ((call CHACAL_fnc_rnd) < 0.5) then {1} else {-1};
            private _dec = _cote * (40 + (80 call CHACAL_fnc_al));
            private _dist = 150 + (200 call CHACAL_fnc_al);
            private _p = _site getPos [_dist, _azOuv + _dec];
            if (surfaceIsWater _p) then { continue };
            private _h = getTerrainHeightASL _p; private _dev = 0;
            for "_k" from 0 to 5 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [12, _k * 60])) - _h)) };
            if (_dev > 6) then { continue };
            _cands pushBack [_h - _solSite, _p, _dev, _dist];
        };
        if (count _cands == 0) exitWith {
            "CHACAL|AVERT|appui_feu|aucun_candidat|repli_observatoire" call CHACAL_LOG;
            CHACAL_COUV = -1; _repli
        };
        // etage 2 : seuls les 24 plus hauts au-dessus du SOL DU SITE paient les 37 rayons
        _cands = [_cands, [], { - (_x select 0) }, "ASCEND"] call BIS_fnc_sortBy;
        private _garde = (count _cands) min 24;
        private _best = []; private _sc = -1e9; private _couv = 0;
        for "_i" from 0 to (_garde - 1) do {
            (_cands select _i) params ["_gain", "_p", "_dev", "_dist"];
            private _c = [_p, _plancher] call CHACAL_fnc_couverture;
            private _s = 3 * _c + (((_gain max -10) min 20) / 20) - ((abs (_dist - 250)) / 250) - (_dev / 12);
            if (_s > _sc) then { _sc = _s; _best = _p; _couv = _c };
        };
        CHACAL_COUV = round (_couv * 1000) / 1000;
        if (_couv < 0.25) exitWith {
            (format ["CHACAL|AVERT|appui_feu|aucune_position_battante|meilleure_couverture|%1|candidats|%2",
                CHACAL_COUV, count _cands]) call CHACAL_LOG;
            (format ["CHACAL|E|appui_feu|%1|placeur|1|couverture|%2|refuse|1", round (time * 100) / 100, CHACAL_COUV]) call CHACAL_LOG;
            _repli
        };
        _best set [2, 0];
        (format ["CHACAL|E|appui_feu|%1|placeur|1|position|%2|couverture|%3|points|%4|dist_site|%5|gain_sol_site|%6|score|%7",
            round (time * 100) / 100, _best, CHACAL_COUV, count _plancher, round (_best distance2D _site),
            round ((getTerrainHeightASL _best) - _solSite), round (_sc * 100) / 100]) call CHACAL_LOG;
        _best
    };''', "00_socle : le choix en deux etages, avec droit de refus")

# --- le banc gagne ses trois instruments ------------------------------------------------------
patch(f"{M}/00_socle.sqf",
      '''        private _oeil = eyePos _u;
        private _vu = { count (lineIntersectsSurfaces [_oeil, aimPos _x, _u, _x, true, 1]) == 0 } count _def;''',
      '''        private _oeil = eyePos _u;
        private _vu = 0; private _occulteur = "";
        {
            private _r = lineIntersectsSurfaces [_oeil, aimPos _x, _u, _x, true, 1];
            if (count _r == 0) then { _vu = _vu + 1 } else {
                if (_occulteur == "") then { _occulteur = typeOf ((_r select 0) select 2) };
            };
        } forEach _def;''', "00_socle : le banc nomme ce qui coupe le rayon")

patch(f"{M}/00_socle.sqf",
      '''        (format ["CHACAL|E|banc_appui_poste|%1|%2|role|%3|distance_cible|%4|defenseurs_vus|%5|sur|%6|connait|%7",
            round (time * 100) / 100, (_u getVariable ["chacal_id", -1]), (_u getVariable ["chacal_role", ""]),
            round (_u distance _cible), _vu, count _def, round ((_u knowsAbout _cible) * 100) / 100]) call CHACAL_LOG;''',
      '''        (format ["CHACAL|E|banc_appui_poste|%1|%2|role|%3|distance_cible|%4|defenseurs_vus|%5|sur|%6|connait|%7|occulteur|%8|mode|%9|couverture|%10",
            round (time * 100) / 100, (_u getVariable ["chacal_id", -1]), (_u getVariable ["chacal_role", ""]),
            round (_u distance _cible), _vu, count _def, round ((_u knowsAbout _cible) * 100) / 100,
            (if (_occulteur == "") then {"aucun"} else {_occulteur}), (combatMode (group _u)), CHACAL_COUV]) call CHACAL_LOG;''',
      "00_socle : le poste journalise l occulteur, le mode et la couverture")

patch(f"{M}/00_socle.sqf",
      '''        private _c = _viv select 0;
        { _x reveal [_c, 4]; _x doWatch _c; _x doTarget _c; _x doFire _c } forEach _a;
    };''',
      '''        private _c = _viv select 0;
        { _x reveal [_c, 4]; _x doWatch _c; _x doTarget _c; _x doFire _c } forEach _a;
        // ! la vue est une SERIE, pas un instantane : les defenseurs bougent, et un poste aveugle a la pose peut
        // s ouvrir ensuite. On ecrit toutes les 10 s ce que chaque tireur atteint reellement.
        {
            private _u = _x; private _oe = eyePos _u;
            private _v = { count (lineIntersectsSurfaces [_oe, aimPos _x, _u, _x, true, 1]) == 0 } count _viv;
            (format ["CHACAL|E|banc_appui_vue|%1|%2|vus|%3|sur|%4|coups|%5|mode|%6", round (time * 100) / 100,
                (_u getVariable ["chacal_id", -1]), _v, count _viv, (_u getVariable ["banc_tirs", 0]),
                (combatMode (group _u))]) call CHACAL_LOG;
        } forEach _a;
    };''', "00_socle : la vue du banc devient une serie")

# --- la ligne FINI porte le placeur et la couverture --------------------------------------------
patch(f"{M}/70_verdict.sqf", '|tirs_banc|%43",', '|tirs_banc|%43|placeur|%44|couverture|%45",', "70_verdict : format FINI")
patch(f"{M}/70_verdict.sqf", "CHACAL_BANC_APPUI, CHACAL_TIRS_BANC]) call CHACAL_LOG;",
      "CHACAL_BANC_APPUI, CHACAL_TIRS_BANC, CHACAL_PLACEUR, CHACAL_COUV]) call CHACAL_LOG;", "70_verdict : valeurs FINI")

patch(f"{D}/description.ext", '    class CHACAL_BANC_APPUI\n', '''    // ! LE PLACEUR ( banc du 12/09 ) : 0 = vue sur l ouverture ( ancien ), 1 = bat le plancher du site.
    class CHACAL_PLACEUR
    {
        title = "Placeur d appui : 0 vue sur l ouverture, 1 bat le plancher du site";
        values[] = {0,1};
        texts[]  = {"OUVERTURE","PLANCHER"};
        default = 0;
    };
    class CHACAL_BANC_APPUI
''', "description.ext")
patch(L, 'BANC_APPUI=$(lit banc_appui 0);', 'PLACEUR=$(lit placeur 0); BANC_APPUI=$(lit banc_appui 0);', "lancer.sh : lecture")
patch(L, 'ecrire_param BANC_APPUI "$BANC_APPUI";', 'ecrire_param PLACEUR "$PLACEUR"; ecrire_param BANC_APPUI "$BANC_APPUI";', "lancer.sh : ecriture")
