#!/usr/bin/env python3
"""clear_gentle.py — vide le serveur de tout NON-WEST, mais PAR PAQUETS de 40 avec pauses
(evite le crash pipes.cpp : le delete massif d'un coup tue le pont natif). Garde WEST + joueurs."""
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
sqf = ('[] spawn { '
       'private _k = allUnits select { side _x != west && !(isPlayer _x) }; private _n = count _k; private _i = 0; '
       'while { _i < _n } do { { if (!isNull _x) then { deleteVehicle _x } } forEach (_k select [_i, 40]); _i = _i + 40; sleep 0.2; }; '
       '{ if (!isNull _x) then { deleteVehicle _x } } forEach (allDead select { !isNull _x }); sleep 1; '
       '(format ["HARMATTAN_GC supp=%1 reste=%2", _n, count (allUnits select { side _x != west })]) call HMT_EMIT; };')
r = b.query(sqf, r"HARMATTAN_GC supp=(\d+) reste=(\d+)", want=1, timeout=60)
print("Nettoyage doux : supprimes=%s | reste non-WEST=%s" % (r[-1].group(1), r[-1].group(2)) if r else "pas de reponse du pont")
