import os
os.environ['HMT_MISSION'] = '/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Altis'
os.environ['HMT_LOG'] = '/mnt/data/harmattan-sandbox/logs/server14.out'
import sys, time, re
sys.path.insert(0, '/home/younes/arma3-marl')
from arma_bridge import ArmaBridge
b = ArmaBridge()
sqf = 'diag_log format ["HMT_DIAG playable=%1 players=%2 west=%3", count playableUnits, count allPlayers, {side _x==west} count allUnits];'
n = b.send(sqf, wait=True, timeout=15); time.sleep(0.8)
for ln in reversed(b._log_lines()):
    m = re.search(r"HMT_DIAG playable=(\d+) players=(\d+) west=(\d+)", ln)
    if m:
        print("playableUnits=%s | players=%s | westUnits=%s" % m.groups()); break
else:
    print("pas de HMT_DIAG (actuateur ?)")
