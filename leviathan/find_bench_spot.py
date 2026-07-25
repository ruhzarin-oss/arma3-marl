#!/usr/bin/env python3
"""find_bench_spot.py — cherche le meilleur EMPLACEMENT DE BANC sur la carte Arma en cours.

Ce qu'on cherche (le finding de la session) : le flanc ne paie QUE si le couvert est ASYMÉTRIQUE.
  - couloir d'approche FRONTAL   -> DÉCOUVERT (l'assaut de face se fait tirer dessus)
  - couloirs de FLANC (±90°)     -> COUVERTS  (contourner protège vraiment)
Score = couvert_flanc - couvert_frontal. Plus c'est haut, mieux le banc discrimine.

Méthode : pour chaque ville, on teste 8 azimuts d'approche. Pour chaque azimut on échantillonne
le couloir frontal (40->120 m) et les deux couloirs de flanc, en comptant les bâtiments proches.

Usage : python find_bench_spot.py --port 5826 [--top 8]
"""
import sys, argparse, math, json
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=5826)
ap.add_argument("--top", type=int, default=8)
ap.add_argument("--max_towns", type=int, default=14)
a = ap.parse_args()
b = NativeBridge(port=a.port)

# --- 1) le monde + la liste des villes ---
r = b.query('(format ["W %1 %2", worldName, worldSize]) call HMT_EMIT;', r"W (\S+) (\d+)", want=1, timeout=12)
world, wsize = (r[-1].group(1), int(r[-1].group(2))) if r else ("?", 0)
print("=== monde : %s (%d m) ===" % (world, wsize), flush=True)

q = ('private _c = [%d/2, %d/2, 0]; '
     'private _ls = nearestLocations [_c, ["NameCityCapital","NameCity","NameVillage"], %d]; '
     'private _o = ""; '
     '{ private _p = locationPosition _x; '
     '  _o = _o + format ["%%1|%%2|%%3|%%4;", text _x, round (_p select 0), round (_p select 1), type _x]; '
     '} forEach _ls; '
     '(format ["TOWNS %%1", _o]) call HMT_EMIT;') % (wsize, wsize, wsize)
r = b.query(q, r"TOWNS (.*)", want=1, timeout=20)
towns = []
if r:
    for t in r[-1].group(1).strip().rstrip(";").split(";"):
        f = t.split("|")
        if len(f) >= 4 and f[1].lstrip("-").isdigit():
            towns.append((f[0], int(f[1]), int(f[2]), f[3]))
print("villes trouvées : %d" % len(towns), flush=True)
towns = towns[:a.max_towns]

# --- 2) score d'asymétrie par ville ---
# pour chaque azimut : frontal = ligne d'approche ; flancs = mêmes distances, décalées de ±70 m
SQF = ('private _res = ""; '
       '{ _x params ["_nm","_cx","_cy"]; '
       '  private _best = -999; private _bestAz = 0; private _bf = 0; private _bl = 0; '
       '  for "_k" from 0 to 7 do { '
       '    private _az = _k * 45; '
       '    private _ux = sin _az; private _uy = cos _az; '          # direction d'approche (depuis l'objectif vers le départ)
       '    private _px = -_uy; private _py = _ux; '                  # perpendiculaire
       '    private _cf = 0; private _cl = 0; '
       '    { private _d = _x; '
       '      private _fx = _cx + _ux*_d; private _fy = _cy + _uy*_d; '
       '      _cf = _cf + count (nearestTerrainObjects [[_fx,_fy,0], ["HOUSE","BUILDING","CHURCH","FORTRESS","WALL"], 18]); '
       '      { private _s = _x; '
       '        private _lx = _cx + _ux*_d + _px*70*_s; private _ly = _cy + _uy*_d + _py*70*_s; '
       '        _cl = _cl + count (nearestTerrainObjects [[_lx,_ly,0], ["HOUSE","BUILDING","CHURCH","FORTRESS","WALL"], 18]); '
       '      } forEach [-1,1]; '
       '    } forEach [40,60,80,100,120]; '
       '    _cl = _cl / 2; '                                          # moyenne des deux flancs
       '    private _sc = _cl - _cf; '
       '    if (_sc > _best) then { _best = _sc; _bestAz = _az; _bf = _cf; _bl = _cl }; '
       '  }; '
       '  _res = _res + format ["%1|%2|%3|%4|%5|%6|%7;", _nm, _cx, _cy, _bestAz, _bf, round _bl, round _best]; '
       '} forEach HMT_TOWNS; '
       '(format ["SCORE %1", _res]) call HMT_EMIT;')

payload = "[" + ",".join('["%s",%d,%d]' % (n.replace('"', ""), x, y) for n, x, y, _ in towns) + "]"
b.send("HMT_TOWNS = %s;" % payload)
r = b.query(SQF, r"SCORE (.*)", want=1, timeout=90)

rows = []
if r:
    for t in r[-1].group(1).strip().rstrip(";").split(";"):
        f = t.split("|")
        if len(f) >= 7 and f[1].lstrip("-").isdigit():
            rows.append(dict(nom=f[0], x=int(f[1]), y=int(f[2]), az=int(f[3]),
                             frontal=int(f[4]), flanc=int(f[5]), score=int(f[6])))
rows.sort(key=lambda d: -d["score"])

print("\n=== CANDIDATS (score = couvert flanc - couvert frontal ; haut = bon banc) ===", flush=True)
print("%-22s %-14s %5s %8s %6s %6s" % ("ville", "objectif", "axe", "frontal", "flanc", "SCORE"), flush=True)
for d in rows[:a.top]:
    print("%-22s %6d,%-7d %4d° %8d %6d %6d" % (d["nom"], d["x"], d["y"], d["az"], d["frontal"], d["flanc"], d["score"]), flush=True)

out = "/home/younes/arma3-marl/leviathan/bench_spots_%s.json" % world.lower()
json.dump({"world": world, "candidates": rows}, open(out, "w"), indent=1)
print("\n-> %s" % out, flush=True)
print("LECTURE : frontal BAS = l'assaut de face est à découvert (bien). flanc HAUT = contourner protège (bien).", flush=True)
