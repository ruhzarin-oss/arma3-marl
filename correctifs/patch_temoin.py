#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-TEMOIN-PLACEUR
# Deux episodes identiques ( meme graine, meme site [6804.04,11678.3], memes refus : 7 pentes et 40 axes sur 288 )
# ont repondu l un 0,541 de couverture, l autre 0 sur les 288. Le terrain n a pas change : c est la MESURE qui
# ne repond pas toujours. Au labo, le meme balayage sur trois zones vierges donne 47, 92 et 56 positions qui
# voient, identiques a froid et 20 s plus tard : la mesure est stable QUAND elle repond.
# Regle 16, controle positif : on pose un temoin dont on connait la reponse. Depuis le centre du site, a 2 m de
# haut, on DOIT voir presque tout le plancher. Si le temoin repond 0, la mesure est muette et on RECOMMENCE
# au lieu de conclure « aucune position ne bat le site ».
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))
s = open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read()
if "appui_balayage" in s:
    print("  deja present"); sys.exit(0)
debut = s.index("    if (CHACAL_PLACEUR == 1) exitWith {")
fin = s.index("    private _best = []; private _sc = -1e9;\n    private _cible = +_ouverture;")
nouveau = '''    if (CHACAL_PLACEUR == 1) exitWith {
        // ! CONTROLE POSITIF ( regle 16 ). Deux episodes identiques ont repondu 0,541 et 0 sur les memes 288
        // candidats, avec les memes refus geometriques : ce n est pas le terrain qui change, c est la mesure qui
        // ne repond pas toujours. Le temoin est un rayon dont on connait la reponse : depuis le centre du site,
        // a 2 m de haut, on voit forcement une large part du plancher. Si le temoin repond 0, la mesure est
        // muette, et on RECOMMENCE au lieu de conclure qu aucune position ne bat le site.
        private _plancher = call CHACAL_fnc_plancher;
        private _np = count _plancher;
        private _solSite = getTerrainHeightASL _site;
        private _azAss = _site getDir _axeAssaut;
        private _best = []; private _sc = -1e9; private _couv = 0;
        private _passe = 0; private _temoin = 0; private _meilleurBrut = 0;
        private _vus = 0; private _refus = [0, 0, 0];   // eau, pente, axe d assaut
        while { _passe < 3 && { count _best == 0 } } do {
            _passe = _passe + 1;
            if (_passe > 1 && { canSuspend }) then { sleep 6 };
            private _oT = +_site; _oT set [2, _solSite + 2]; _temoin = 0;
            { if (count (lineIntersectsSurfaces [_oT, _x, objNull, objNull, true, 1]) == 0) then { _temoin = _temoin + 1 } } forEach _plancher;
            _temoin = _temoin / _np;
            _sc = -1e9; _meilleurBrut = 0; _vus = 0; _refus = [0, 0, 0];
            for "_a" from 0 to 35 do {
                for "_k" from 3 to 10 do {
                    private _dist = _k * 50;
                    private _az = _a * 10;
                    private _p = _site getPos [_dist, _az];
                    _vus = _vus + 1;
                    if (surfaceIsWater _p) then { _refus set [0, (_refus select 0) + 1]; continue };
                    // ne pas tirer dans le dos de son propre assaut : au moins 25 degres d ecart a son axe
                    private _ecart = abs (((_az - _azAss) + 540) % 360 - 180);
                    if (_ecart < 25) then { _refus set [2, (_refus select 2) + 1]; continue };
                    private _h = getTerrainHeightASL _p; private _dev = 0;
                    for "_j" from 0 to 5 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [5, _j * 60])) - _h)) };
                    if (_dev > 3) then { _refus set [1, (_refus select 1) + 1]; continue };
                    private _c = [_p, _plancher] call CHACAL_fnc_couverture;
                    if (_c > _meilleurBrut) then { _meilleurBrut = _c };
                    private _gain = _h - _solSite;
                    private _s = 3 * _c + (((_gain max -10) min 20) / 20) - ((abs (_dist - 250)) / 250) - (_dev / 12);
                    if (_c > 0 && { _s > _sc }) then { _sc = _s; _best = _p; _couv = _c };
                };
            };
            (format ["CHACAL|E|appui_balayage|%1|passe|%2|temoin|%3|balayes|%4|refus_eau|%5|refus_pente|%6|refus_axe|%7|meilleure_couverture|%8|retenue|%9",
                round (time * 100) / 100, _passe, round (_temoin * 1000) / 1000, _vus, _refus select 0, _refus select 1,
                _refus select 2, round (_meilleurBrut * 1000) / 1000, count _best]) call CHACAL_LOG;
        };
        CHACAL_COUV = round (_couv * 1000) / 1000;
        if (count _best == 0 || { _couv < 0.25 }) exitWith {
            (format ["CHACAL|AVERT|appui_feu|aucune_position_battante|meilleure_couverture|%1|temoin|%2|passes|%3",
                round (_meilleurBrut * 1000) / 1000, round (_temoin * 1000) / 1000, _passe]) call CHACAL_LOG;
            (format ["CHACAL|E|appui_feu|%1|placeur|1|couverture|%2|temoin|%3|refuse|1",
                round (time * 100) / 100, CHACAL_COUV, round (_temoin * 1000) / 1000]) call CHACAL_LOG;
            _repli
        };
        _best set [2, 0];
        (format ["CHACAL|E|appui_feu|%1|placeur|1|position|%2|couverture|%3|temoin|%4|passes|%5|points|%6|dist_site|%7|gain_sol_site|%8|score|%9|azimut|%10",
            round (time * 100) / 100, _best, CHACAL_COUV, round (_temoin * 1000) / 1000, _passe, _np,
            round (_best distance2D _site), round ((getTerrainHeightASL _best) - _solSite),
            round (_sc * 100) / 100, round (_site getDir _best)]) call CHACAL_LOG;
        _best
    };
'''
s2 = s[:debut] + nouveau + s[fin:]
if bilan(s) != bilan(s2):
    print("  !! equilibre %s -> %s" % (bilan(s), bilan(s2))); sys.exit(1)
open(f"{M}/00_socle.sqf", "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  PATCHE : 00_socle : temoin de mesure et reprise du balayage")
