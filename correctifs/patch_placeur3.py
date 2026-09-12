#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-PLACEUR-HAUTEUR
# MESURE AU LABO MCP, 12/09 : avec l enceinte reconstruite ( 31 HBarrier sur 46 m de rayon ), 199 positions sur 504
# voient encore le plancher du site, et les meilleures en voient les 37 points - dont une a 150 m avec 11 m de
# denivele. Mon placeur ne pouvait pas les trouver : il rejetait tout candidat dont le relief local depasse 6 m,
# c est-a-dire exactement les buttes qui permettent de voir par-dessus un mur.
# La regle geometrique, verifiee au labo : pour voir le sol au-dela d un mur de 2,5 m pose a 46 m du centre, il faut
# etre haut d environ D/20 au-dessus du sol du site ( 8 m a 150 m, 12 m a 250 m ).
# On filtre donc sur la HAUTEUR ( gain >= D/20 + 2 ), on ne juge la platitude que sur 5 m ( de quoi se coucher ),
# et on garde la couverture mesuree par rayons comme juge final.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))
def patch(path, avant, apres, quoi):
    s = open(path, encoding="utf-8", errors="surrogateescape").read()
    if s.count(avant) != 1: print("  !! motif x%d : %s" % (s.count(avant), quoi)); sys.exit(1)
    s2 = s.replace(avant, apres, 1)
    if path.endswith(".sqf") and bilan(s) != bilan(s2): print("  !! equilibre : %s" % quoi); sys.exit(1)
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(s2); print("  PATCHE :", quoi)
s = open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read()
if "hauteur_utile" in s: print("  deja present"); sys.exit(0)
patch(f"{M}/00_socle.sqf",
  '''        for "_i" from 1 to 220 do {
            private _cote = if ((call CHACAL_fnc_rnd) < 0.5) then {1} else {-1};
            private _dec = _cote * (40 + (80 call CHACAL_fnc_al));
            private _dist = 150 + (200 call CHACAL_fnc_al);
            private _p = _site getPos [_dist, _azOuv + _dec];
            if (surfaceIsWater _p) then { continue };
            private _h = getTerrainHeightASL _p; private _dev = 0;
            for "_k" from 0 to 5 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [12, _k * 60])) - _h)) };
            if (_dev > 6) then { continue };
            _cands pushBack [_h - _solSite, _p, _dev, _dist];
        };''',
  '''        // ! LA HAUTEUR EST LA CONDITION, PAS LA PLATITUDE ( mesure au labo, 12/09 ). Pour voir le sol derriere un
        // mur de 2,5 m pose a 46 m du centre, il faut environ D/20 au-dessus du sol du site. L ancien filtre rejetait
        // tout relief local de plus de 6 m : il jetait justement les buttes qui donnent la vue.
        private _refus = [0, 0, 0];   // eau, trop bas, trop accidente pour se coucher
        for "_i" from 1 to 320 do {
            private _cote = if ((call CHACAL_fnc_rnd) < 0.5) then {1} else {-1};
            private _dec = _cote * (30 + (100 call CHACAL_fnc_al));
            private _dist = 120 + (330 call CHACAL_fnc_al);
            private _p = _site getPos [_dist, _azOuv + _dec];
            if (surfaceIsWater _p) then { _refus set [0, (_refus select 0) + 1]; continue };
            private _h = getTerrainHeightASL _p;
            private _hauteur_utile = (_dist / 20) + 2;
            if ((_h - _solSite) < _hauteur_utile) then { _refus set [1, (_refus select 1) + 1]; continue };
            private _dev = 0;
            for "_k" from 0 to 5 do { _dev = _dev max (abs ((getTerrainHeightASL (_p getPos [5, _k * 60])) - _h)) };
            if (_dev > 3) then { _refus set [2, (_refus select 2) + 1]; continue };
            _cands pushBack [_h - _solSite, _p, _dev, _dist];
        };
        (format ["CHACAL|E|appui_candidats|%1|retenus|%2|refus_eau|%3|refus_trop_bas|%4|refus_pente|%5",
            round (time * 100) / 100, count _cands, _refus select 0, _refus select 1, _refus select 2]) call CHACAL_LOG;''',
  "00_socle : le placeur cherche la HAUTEUR utile, pas la platitude")
