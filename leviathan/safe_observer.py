#!/usr/bin/env python3
"""safe_observer.py — protege le joueur du tir fratricide : setCaptive (invisible aux 2 camps),
et re-applique automatiquement au respawn via un EH. Il peut observer/juger le placement sans mourir."""
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
sqf = ('private _ps = allUnits select {isPlayer _x}; '
       '{ _x setCaptive true; _x allowDamage false; '
       '  _x addEventHandler ["Respawn", { (_this select 0) setCaptive true; (_this select 0) allowDamage false }]; '
       '} forEach _ps; '
       '(format ["OBS joueurs=%1 captive+invuln applique", count _ps]) call HMT_EMIT;')
r = b.query(sqf, r"OBS (.+)", want=1, timeout=15)
print("RESULT:", r[-1].group(1) if r else "pas de reponse (joueur en respawn ? reconnecte-toi et relance)")
