import os
os.environ['HMT_MISSION'] = '/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Altis'
os.environ['HMT_LOG'] = '/mnt/data/harmattan-sandbox/logs/server14.out'
import sys, time, re
sys.path.insert(0, '/home/younes/arma3-marl')
from arma_bridge import ArmaBridge
b = ArmaBridge()
pts = {"centre/objectif": [20885, 16779], "teleport(-55)": [20885, 16724],
       "slot": [20885, 16689], "spawn_infil": [20885, 16669]}
sqf = "worldName"
out = []
sqf = ('private _r=""; { private _p=_x; _r=_r+format["%1=water:%2,h:%3|", _forEachIndex, surfaceIsWater _p, round (getTerrainHeightASL _p)]; } '
       'forEach [[20885,16779,0],[20885,16724,0],[20885,16689,0],[20885,16669,0]]; '
       'diag_log format ["HMT_SURF wn=%1 %2", worldName, _r];')
n = b.send(sqf, wait=True, timeout=20); time.sleep(0.8)
for ln in reversed(b._log_lines()):
    m = re.search(r"HMT_SURF wn=(\S+) (.+)", ln)
    if m:
        print("world=%s" % m.group(1))
        print("points [centre, teleport, slot, spawn]:")
        print("  " + m.group(2)); break
else:
    print("pas de HMT_SURF")
