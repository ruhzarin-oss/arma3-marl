#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-PLACEUR-BALAYAGE
# Mesure au labo MCP, 12/09, site de la graine 7 reconstruit avec son mur, son QG, sa tour et son antenne :
# 102 positions sur 288 voient le plancher, et plusieurs en voient les 37 points - a 150 m au nord (+11 m), mais
# aussi a 150 m au nord-est avec 3 m EN DESSOUS du site. Mon placeur les ratait pour deux raisons :
#   . il TIRAIT 320 positions au hasard, et le secteur qui voit est etroit : aucune de ses 37 retenues n y tombait ;
#   . il exigeait une hauteur de D/20 + 2, ce qui jette les positions basses qui voient par une porte ou un creux.
# Remede : BALAYAGE SYSTEMATIQUE. 36 azimuts x 8 distances = 288 candidats, la couverture est MESUREE pour chacun
# ( ~10 000 rayons, mesure au labo : quelques dixiemes de seconde ), et la meilleure gagne. Plus de filtre de hauteur :
# la hauteur n etait qu un indice, la couverture est la mesure. Le refus reste possible, et il reste ecrit.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))
s = open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read()
if "balayage" in s:
    print("  deja present"); sys.exit(0)
debut = s.index("    if (CHACAL_PLACEUR == 1) exitWith {")
fin = s.index("    private _best = []; private _sc = -1e9;\n    private _cible = +_ouverture;")
ancien = s[debut:fin]
nouveau = '''    if (CHACAL_PLACEUR == 1) exitWith {
        // ! BALAYAGE SYSTEMATIQUE ( mesure au labo MCP, 12/09 ). Le tirage au hasard ratait le secteur etroit qui
        // voit le site, et le filtre de hauteur jetait les positions basses qui voient par une porte ou un creux.
        // On balaye 36 azimuts sur 8 distances, on MESURE la couverture de chacun, et la meilleure gagne.
        private _plancher = call CHACAL_fnc_plancher;
        private _solSite = getTerrainHeightASL _site;
        private _best = []; private _sc = -1e9; private _couv = 0; private _meilleurBrut = 0;
        private _vus = 0; private _refus = [0, 0, 0];   // eau, pente, axe d assaut
        private _azAss = _site getDir _axeAssaut;
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
                if (_s > _sc) then { _sc = _s; _best = _p; _couv = _c };
            };
        };
        CHACAL_COUV = round (_couv * 1000) / 1000;
        (format ["CHACAL|E|appui_candidats|%1|balayes|%2|refus_eau|%3|refus_pente|%4|refus_axe|%5|meilleure_couverture|%6",
            round (time * 100) / 100, _vus, _refus select 0, _refus select 1, _refus select 2,
            round (_meilleurBrut * 1000) / 1000]) call CHACAL_LOG;
        if (count _best == 0 || { _couv < 0.25 }) exitWith {
            (format ["CHACAL|AVERT|appui_feu|aucune_position_battante|meilleure_couverture|%1|balayes|%2",
                CHACAL_COUV, _vus]) call CHACAL_LOG;
            (format ["CHACAL|E|appui_feu|%1|placeur|1|couverture|%2|refuse|1", round (time * 100) / 100, CHACAL_COUV]) call CHACAL_LOG;
            _repli
        };
        _best set [2, 0];
        (format ["CHACAL|E|appui_feu|%1|placeur|1|position|%2|couverture|%3|points|%4|dist_site|%5|gain_sol_site|%6|score|%7|azimut|%8",
            round (time * 100) / 100, _best, CHACAL_COUV, count _plancher, round (_best distance2D _site),
            round ((getTerrainHeightASL _best) - _solSite), round (_sc * 100) / 100, round (_site getDir _best)]) call CHACAL_LOG;
        _best
    };
'''
s2 = s[:debut] + nouveau + s[fin:]
if bilan(s) != bilan(s2):
    print("  !! equilibre %s -> %s" % (bilan(s), bilan(s2))); sys.exit(1)
open(f"{M}/00_socle.sqf", "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  PATCHE : 00_socle : balayage systematique, la couverture est la mesure")
