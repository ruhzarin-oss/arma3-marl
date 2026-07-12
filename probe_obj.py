#!/usr/bin/env python3
"""probe_obj — le point objectif (GX,GY) est-il atteignable, ou dans un batiment ?"""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
b = SocketBridge(5801); time.sleep(1)
GX, GY = 20885, 16779
b.send('private _p=[%d,%d,0]; _p set [2, getTerrainHeightASL _p];'
       ' private _inb = count (nearestObjects [_p, ["House","Building"], 3]);'
       ' private _nb = nearestObjects [_p, ["House","Building"], 25];'
       ' private _nd = if (count _nb > 0) then { round (_p distance (_nb select 0)) } else { -1 };'
       ' private _fe = _p isFlatEmpty [2, 0, 0.6, 3, 0, false];'
       ' diag_log format ["OBJPT inbld3=%%1 nbld25=%%2 nearestbld=%%3m flatempty=%%4", _inb, count _nb, _nd, _fe];' % (GX, GY))
time.sleep(1.2)
for ln in reversed(b._log_lines(3000)):
    m = re.search(r"OBJPT (.+)", ln)
    if m:
        print(">>>", m.group(1)); break
print("PROBE_OBJ DONE", flush=True)
