#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
r = b.query('{ _x allowDamage false; _x setCaptive true; _x setPosATL [3253,3258,0]; _x setDir 180 } forEach allPlayers; '
            '(format ["HARMATTAN_TP joueurs=%1", count allPlayers]) call HMT_EMIT;',
            r"HARMATTAN_TP joueurs=(\d+)", want=1, timeout=15)
print("joueurs teleportes au surplomb :", r[-1].group(1) if r else "?")
