#!/usr/bin/env python3
import sys
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
b = NativeBridge(port=5816)
q = ('private _c=[[1400,6200],[6200,6100],[1400,2100],[4600,6500],[2400,4300],[5900,2200],[1150,4800],[3700,6300],[900,5200],[6400,2400],[5000,6300],[1900,6400]]; '
     'private _o=_c apply { private _p=_x; [_p, ({side _x==east && (_x distance2D _p)<450} count allUnits)] }; '
     '(format ["HARMATTAN_SCAN %1", _o]) call HMT_EMIT;')
r = b.query(q, r"HARMATTAN_SCAN (\[.*\])", want=1, timeout=15)
print(r[-1].group(1) if r else "pas de reponse")
