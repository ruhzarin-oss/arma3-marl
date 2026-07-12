#!/usr/bin/env python3
"""clear_civ.py — serveur 100% vide sauf BLUFOR : supprime tout ce qui n'est PAS west et PAS joueur
(civils, tout reste EAST/independant, cadavres). Ne touche pas aux coquilles WEST ni aux joueurs."""
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
sqf = ('[] spawn { '
       'private _k = allUnits select { side _x != west && !(isPlayer _x) }; private _n = count _k; '
       '{ deleteVehicle _x } forEach _k; '
       '{ deleteVehicle _x } forEach (allDead select { !isNull _x }); '
       'sleep 2.5; '
       'private _ce = {alive _x && side _x == east} count allUnits; '
       'private _cc = {side _x == civilian} count allUnits; '
       'private _cg = {side _x == resistance} count allUnits; '
       'private _cw = {side _x == west} count allUnits; '
       '(format ["HARMATTAN_CLEARALL supp=%1 east=%2 civ=%3 indep=%4 west=%5 joueurs=%6", _n, _ce, _cc, _cg, _cw, count allPlayers]) call HMT_EMIT; };')
r = b.query(sqf, r"HARMATTAN_CLEARALL supp=(\d+) east=(\d+) civ=(\d+) indep=(\d+) west=(\d+) joueurs=(\d+)", want=1, timeout=40)
if r:
    m = r[-1]
    print("=== SERVEUR 100% VIDE (sauf BLUFOR) ===")
    print("  supprimes (non-west) : %s" % m.group(1))
    print("  restants -> EAST:%s  civils:%s  independant:%s" % (m.group(2), m.group(3), m.group(4)))
    print("  WEST (tes coquilles) : %s | joueurs : %s" % (m.group(5), m.group(6)))
else:
    print("pas de reponse du pont")
