#!/usr/bin/env python3
"""etat_stratis — y a-t-il une garnison EAST au FOB Maxwell, et depuis quand ?"""
import sys
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
T = theatre.use("stratis")
b = NativeBridge(port=T.PORT)
fx, fy = T.FOB
q = ("(format [" + Q + "S monde=" + P + "1 est=" + P + "2 unites=" + P + "3 groupes=" + P + "4 pres=" + P + "5" + Q + ", "
     "worldName, count (allUnits select {side _x == east}), count allUnits, count allGroups, "
     "count (allUnits select {side _x == east && (_x distance2D [" + str(fx) + "," + str(fy) + "]) < 120})]) call HMT_EMIT;")
r = b.query(q, r"S monde=(\S+) est=(\d+) unites=(\d+) groupes=(\d+) pres=(\d+)", want=1, timeout=40)
b.close()
print(r[-1].group(0) if r else "PAS DE REPONSE")
sys.exit(0 if r else 1)
