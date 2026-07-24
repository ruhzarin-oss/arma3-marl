#!/usr/bin/env python3
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
q = ('(format ["HARMATTAN_DBG e=%1 w=%2 es=%3",'
     ' (if (isNil "HMT_EAST") then {-1} else {count HMT_EAST}),'
     ' (if (isNil "HMT_WPILOT") then {-1} else {count HMT_WPILOT}),'
     ' (if (isNil "HMT_ESHOTS") then {-1} else {HMT_ESHOTS})]) call HMT_EMIT;')
r = b.query(q, r"HARMATTAN_DBG (.+)", want=1, timeout=12)
print("DBG:", r[-1].group(1) if r else "PAS DE REPONSE")
# les fonctions supp existent-elles ?
r2 = b.query('(format ["HARMATTAN_FN set=%1 sense=%2 fire=%3",'
             ' (if (isNil "HMT_SUPP_SETUP") then {0} else {1}),'
             ' (if (isNil "HMT_SUPP_SENSE") then {0} else {1}),'
             ' (if (isNil "HMT_SUPP_FIRE") then {0} else {1})]) call HMT_EMIT;',
             r"HARMATTAN_FN (.+)", want=1, timeout=12)
print("FN :", r2[-1].group(1) if r2 else "PAS DE REPONSE")
