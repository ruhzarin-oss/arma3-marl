#!/usr/bin/env python3
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
b.send('call compile preprocessFileLineNumbers "supp_probe.sqf";'); time.sleep(0.6)
r = b.query('(format ["HARMATTAN_FN set=%1 sense=%2 fire=%3 hold=%4",'
            ' (if (isNil "HMT_SUPP_SETUP") then {0} else {1}),'
            ' (if (isNil "HMT_SUPP_SENSE") then {0} else {1}),'
            ' (if (isNil "HMT_SUPP_FIRE") then {0} else {1}),'
            ' (if (isNil "HMT_SUPP_HOLD") then {0} else {1})]) call HMT_EMIT;',
            r"HARMATTAN_FN (.+)", want=1, timeout=12)
print("FN:", r[-1].group(1) if r else "PAS DE REPONSE")
