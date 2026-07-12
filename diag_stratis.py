import os
os.environ['HMT_MISSION'] = '/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis'
os.environ['HMT_LOG'] = '/mnt/data/harmattan-sandbox/logs/server14.out'
import sys, time, re
sys.path.insert(0, '/home/younes/arma3-marl')
from arma_bridge import ArmaBridge
b = ArmaBridge()
sqf = ('private _sp = [[4096,4096],0,1600,14,0,0.22,0] call BIS_fnc_findSafePos; '
       'diag_log format ["HMT_ST wn=%1 slotwater=%2 safe=%3 safewater=%4 h=%5", '
       'worldName, surfaceIsWater [3500,5500,0], _sp, surfaceIsWater _sp, round (getTerrainHeightASL _sp)];')
n = b.send(sqf, wait=True, timeout=25); time.sleep(1.0)
for ln in reversed(b._log_lines()):
    m = re.search(r"HMT_ST wn=(\S+) slotwater=(\w+) safe=(\[[^\]]*\]) safewater=(\w+) h=(\S+)", ln)
    if m:
        print("world=%s | slot[3500,5500] water=%s | findSafePos=%s water=%s h=%s" % m.groups()); break
else:
    print("pas de reponse (boot pas fini ?)")
