#!/usr/bin/env python3
"""trouver_zone.py — cherche sur la carte le meilleur TERRAIN D'ESSAI pour calibrer le tir.

Ce qu'il faut : une bande plate, sèche et dégagée, assez longue pour aligner des duels
espacés (sinon les tireurs se mélangent). On ne devine pas — on balaie et on classe.
"""
import sys, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
ap = argparse.ArgumentParser()
ap.add_argument("--pas", type=int, default=300, help="écart entre duels le long de la bande")
ap.add_argument("--n", type=int, default=6, help="nombre de duels par bande")
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
b = NativeBridge(port=TH.PORT)

candidats = [(3000 + (k % 9) * 2900, 3000 + (k // 9) * 2900) for k in range(72)]
print("=== balayage de %d emplacements (bande de %d duels espacés de %d m) ===" % (len(candidats), a.n, a.pas), flush=True)

resultats = []
for i in range(0, len(candidats), 12):
    lot = candidats[i:i + 12]
    liste = "[" + ",".join("[%d,%d]" % c for c in lot) + "]"
    sqf = ('private _o = ""; '
           '{ private _p = _x; private _bad = 0; private _hmin = 9999; private _hmax = -9999; '
           '  for "_i" from 0 to %d do { '
           '    private _cx = (_p select 0) + _i * %d; private _cy = _p select 1; '
           '    if (surfaceIsWater [_cx,_cy]) then { _bad = _bad + 3 }; '
           '    if (count (nearestTerrainObjects [[_cx,_cy,0], [%sHOUSE%s,%sBUILDING%s,%sROCK%s], 150]) > 1) then { _bad = _bad + 1 }; '
           '    private _h = getTerrainHeightASL [_cx,_cy]; '
           '    if (_h < _hmin) then { _hmin = _h }; if (_h > _hmax) then { _hmax = _h }; '
           '  }; '
           '  _o = _o + format ["%%1,%%2,%%3,%%4|", _p select 0, _p select 1, _bad, round (_hmax - _hmin)]; '
           '} forEach %s; (format ["S %%1", _o]) call HMT_EMIT;'
           % (a.n - 1, a.pas, Q, Q, Q, Q, Q, Q, liste))
    r = b.query(sqf, r"S (.+)", want=1, timeout=60)
    if not r:
        print("  (lot %d sans réponse)" % i, flush=True); continue
    for t in r[-1].group(1).strip().rstrip("|").split("|"):
        f = t.split(",")
        if len(f) >= 4 and f[0].lstrip("-").isdigit():
            resultats.append((int(f[2]), int(f[3]), int(f[0]), int(f[1])))

resultats.sort()
print("\n=== les 8 meilleurs emplacements ===", flush=True)
print("%8s %10s   %s" % ("obstacles", "relief", "zone"), flush=True)
for bad, rel, x, y in resultats[:8]:
    print("%8d %8d m   --zone %d,%d" % (bad, rel, x, y), flush=True)
if resultats:
    bad, rel, x, y = resultats[0]
    print("\n>>> meilleur : --zone %d,%d  (obstacles %d, relief %d m)" % (x, y, bad, rel), flush=True)
    print(">>> %s" % ("utilisable" if bad <= 2 and rel <= 20 else
                      "ATTENTION : aucun emplacement vraiment plat — il faudra vérifier la vue duel par duel"), flush=True)
print("ZONE_DONE", flush=True)
