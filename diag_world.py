import os
os.environ['HMT_MISSION'] = '/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Altis'
os.environ['HMT_LOG'] = '/mnt/data/harmattan-sandbox/logs/server14.out'
import sys, time, re
sys.path.insert(0, '/home/younes/arma3-marl')
from arma_bridge import ArmaBridge
b = ArmaBridge()
sqf = ('private _u = playableUnits select 0; private _p = getPosATL _u; '
       'diag_log format ["HMT_WORLD wn=%1 slotpos=%2 water=%3 h=%4", '
       'worldName, _p, surfaceIsWater _p, getTerrainHeightASL _p];')
n = b.send(sqf, wait=True, timeout=15); time.sleep(0.8)
for ln in reversed(b._log_lines()):
    m = re.search(r"HMT_WORLD wn=(\S+) slotpos=(\[[^\]]*\]) water=(\w+) h=(\S+)", ln)
    if m:
        print("worldName=%s | slot=%s | water=%s | hauteurASL=%s" % m.groups()); break
else:
    print("pas de HMT_WORLD")
