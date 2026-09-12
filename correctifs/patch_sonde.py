#!/usr/bin/env python3
# MARQUEUR-CORRECTIF-SONDE
# Le temoin repond 1 : la mesure fonctionne. Pourtant le balayage rend 0 sur 288 a la premiere passe des deux
# cotes, puis 0,541 a la seconde sur une instance et toujours 0 sur l autre. Et la position retenue a 0,541 de
# couverture est a 500 m : l appui y voit 0 defenseur et ne tire pas. Couvrir le plancher n est donc pas voir
# les hommes. Avant de rechanger le placeur, on NOMME ce qui bloque : quatre sondes fixes a 150 m (nord, est,
# sud, ouest), et pour chacune on compte les rayons libres, ceux qui butent sur le TERRAIN, et le type des
# objets rencontres. lineIntersectsSurfaces rend [pos, normale, objet, parent] : parent nul = terrain.
import sys
M = "/mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal"
def bilan(s): return (s.count("{") - s.count("}"), s.count("[") - s.count("]"), s.count("(") - s.count(")"))
s = open(f"{M}/00_socle.sqf", encoding="utf-8", errors="surrogateescape").read()
if "appui_sonde" in s:
    print("  deja present"); sys.exit(0)
ancre = """            (format ["CHACAL|E|appui_balayage|%1|passe|%2|temoin|%3|balayes|%4|refus_eau|%5|refus_pente|%6|refus_axe|%7|meilleure_couverture|%8|retenue|%9","""
sonde = '''            // ! SONDES : quatre points fixes a 150 m, pour NOMMER ce qui arrete les rayons.
            {
                private _az = _x;
                private _ps = _site getPos [150, _az];
                private _os = +_ps; _os set [2, (getTerrainHeightASL _ps) + 1.5];
                private _libre = 0; private _terr = 0; private _types = [];
                {
                    private _r = lineIntersectsSurfaces [_os, _x, objNull, objNull, true, 1];
                    if (count _r == 0) then { _libre = _libre + 1 } else {
                        private _e = (_r select 0) select 3;
                        if (isNull _e) then { _terr = _terr + 1 } else { _types pushBackUnique (typeOf _e) };
                    };
                } forEach _plancher;
                (format ["CHACAL|E|appui_sonde|%1|passe|%2|azimut|%3|libres|%4|sur|%5|terrain|%6|objets|%7|gain|%8",
                    round (time * 100) / 100, _passe, _az, _libre, _np, _terr, _types,
                    round ((getTerrainHeightASL _ps) - _solSite)]) call CHACAL_LOG;
            } forEach [0, 90, 180, 270];
'''
s2 = s.replace(ancre, sonde + ancre, 1)
if s2 == s or bilan(s) != bilan(s2):
    print("  !! ancre absente ou equilibre casse"); sys.exit(1)
open(f"{M}/00_socle.sqf", "w", encoding="utf-8", errors="surrogateescape").write(s2)
print("  PATCHE : 00_socle : quatre sondes qui nomment l obstacle")
