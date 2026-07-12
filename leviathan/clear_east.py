#!/usr/bin/env python3
"""clear_east.py — vide le serveur de TOUT ennemi : supprime toutes les unites EAST (garnison / monde persistant).
Ne touche pas aux coquilles WEST ni aux joueurs. Reporte ce qui reste par camp."""
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
sqf = ('[] spawn { '
       'private _e = allUnits select { side _x == east }; private _n = count _e; '
       '{ deleteVehicle _x } forEach _e; '
       '{ deleteVehicle _x } forEach (allDead select { !isNull _x && side _x == east }); '
       'sleep 2.5; '
       'private _ce = {alive _x && side _x == east} count allUnits; '
       'private _cg = {side _x == resistance} count allUnits; '
       'private _cc = {side _x == civilian} count allUnits; '
       'private _cw = {side _x == west} count allUnits; '
       '(format ["HARMATTAN_CLEAR supp=%1 east=%2 indep=%3 civ=%4 west=%5 joueurs=%6", _n, _ce, _cg, _cc, _cw, count allPlayers]) call HMT_EMIT; };')
r = b.query(sqf, r"HARMATTAN_CLEAR supp=(\d+) east=(\d+) indep=(\d+) civ=(\d+) west=(\d+) joueurs=(\d+)", want=1, timeout=40)
if r:
    m = r[-1]
    print("=== SERVEUR NETTOYE ===")
    print("  EAST supprimes : %s" % m.group(1))
    print("  Restants -> EAST(vivants): %s | independant: %s | civils: %s" % (m.group(2), m.group(3), m.group(4)))
    print("  WEST (tes coquilles) : %s | joueurs : %s" % (m.group(5), m.group(6)))
else:
    print("pas de reponse du pont")
