#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
sqf = ('if (count allPlayers > 0) then { private _p = getPosATL (allPlayers select 0); '
       'deleteMarker "moi"; createMarker ["moi", _p]; "moi" setMarkerType "hd_dot"; "moi" setMarkerColor "ColorBlue"; "moi" setMarkerText "== MOI =="; '
       'deleteMarker "depart"; createMarker ["depart", [3253,3184,0]]; "depart" setMarkerType "b_inf"; "depart" setMarkerColor "ColorBlue"; "depart" setMarkerText "FORCE BLUFOR"; '
       'deleteMarker "objectif"; createMarker ["objectif", [3253,2984,0]]; "objectif" setMarkerType "o_installation"; "objectif" setMarkerColor "ColorEAST"; "objectif" setMarkerText "FOB LAMBS"; '
       '(format ["HMT_MAP jx=%1 jy=%2", round ((_p) select 0), round ((_p) select 1)]) call HMT_EMIT; } '
       'else { (format ["HMT_MAP jx=-1 jy=-1"]) call HMT_EMIT; };')
r = b.query(sqf, r"HMT_MAP jx=(-?\d+) jy=(-?\d+)", want=1, timeout=15)
if r:
    m = r[-1]
    if m.group(1) == "-1":
        print("Aucun joueur detecte — tu es bien connecte au serveur ?")
    else:
        print("Marqueurs poses. TOI = [%s,%s] (marqueur '== MOI =='). Aussi 'FORCE BLUFOR' [3253,3184] et 'FOB LAMBS' [3253,2984]." % (m.group(1), m.group(2)))
else:
    print("pas de reponse du pont")
