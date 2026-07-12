#!/usr/bin/env python3
"""probe_buildings — les batiments du complexe sont-ils ENTERABLES dans Arma ? (buildingPos = positions interieures IA).
Decide si la direction CQB (nettoyage interieur) a un sens ici. Lecture fiable SocketBridge+grab."""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
CX, CY = 20885, 16779
b = SocketBridge(PORT)
time.sleep(1)
b.send('private _objs = nearestObjects [[%d,%d,0], ["House","Building","Ruins"], 130];'
       ' private _t=0; private _ne=0; private _det="";'
       ' { private _n = count (_x buildingPos -1); _t=_t+_n; if (_n>0) then {_ne=_ne+1; _det=_det+format["%%1(%%2) ", typeOf _x, _n]}; } forEach _objs;'
       ' diag_log format ["BPOS objs=%%1 enterable=%%2 totalpos=%%3", count _objs, _ne, _t];'
       ' diag_log format ["BDET %%1", _det];' % (CX, CY))
time.sleep(1.0)


def grab(tag):
    for ln in reversed(b._log_lines(4000)):
        m = re.search(r"%s (.+)" % tag, ln)
        if m:
            return m.group(1).strip()
    return None


print(">>>", grab("BPOS"), flush=True)
det = grab("BDET")
print("   batiments enterables (type(nb_pos)) :", (det[:400] if det else "aucun"), flush=True)
print("PROBE_BLD DONE", flush=True)
