#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
q = ('private _w = HMT_WPILOT; private _al = _w select {alive _x}; private _cx=0; private _cy=0; private _mx=0; '
     'if (count _al > 0) then { { _cx=_cx+(getPosATL _x)#0; _cy=_cy+(getPosATL _x)#1; _mx=_mx max (speed _x) } forEach _al; _cx=_cx/(count _al); _cy=_cy/(count _al) }; '
     '(format ["HMT_F tot=%1 vivants=%2 mode=%3 cx=%4 cy=%5 vmax=%6 east=%7 joueurs=%8", '
     'count _w, count _al, HMT_WAGENT_MODE, round _cx, round _cy, round _mx, {alive _x && side _x==east} count allUnits, count allPlayers]) call HMT_EMIT;')
r = b.query(q, r"HMT_F tot=(\d+) vivants=(\d+) mode=(\w+) cx=(-?\d+) cy=(-?\d+) vmax=(-?\d+) east=(\d+) joueurs=(\d+)", want=1, timeout=15)
if r:
    m = r[-1]
    print("COQUILLES : total=%s vivantes=%s arme=%s | centre=[%s,%s] (depart=[3253,3184]) vitesse_max=%s km/h" % (m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)))
    print("LAMBS EAST vivants=%s | joueurs=%s" % (m.group(7), m.group(8)))
else:
    print("pas de reponse du pont")
