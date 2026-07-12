"""diag_scale — setVelocity passe-t-il a l'echelle 20 ? Global HMT_VEL pour TOUS, + mesure FPS serveur.
Si global bouge les 20 -> le bug etait getVariable par-soldat. Si 3/20 -> setVelocity ne scale pas a 20 (ou FPS effondre)."""
import time, re, sys
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 0
N = 20
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180); GX, GY = OBJ
env = OpArma(squads=(("AV", N),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SRV)
env.spawn({"AV": (GX + 10, GY - 115)}, [(GX, GY, 10, 14)])
env.b.send('{ _x disableAI "MOVE"; _x disableAI "PATH"; _x disableAI "FSM"; _x disableAI "ANIM"; _x disableAI "AUTOCOMBAT"; } forEach AV; HMT_VEL=[0,0,0];', wait=True)
env.b.send('HMT_EF_S = addMissionEventHandler ["EachFrame", { { _x setVelocity HMT_VEL } forEach AV; }];', wait=True)
time.sleep(1.5)
env.b.send('HMT_VEL=[0,4,0];', wait=True)
time.sleep(4.0)
env.b.send('HMT_VEL=[0,0,0];', wait=True)
ls = env._query('diag_log format ["FPS %1", round diag_fps]; { diag_log format ["U %1 spd=%2", _forEachIndex, round((vectorMagnitude velocity _x)*10)]; } forEach AV;', settle=0.4)
spds = []; fps = None
for l in ls:
    m = re.search(r"U (\d+) spd=(\d+)", l)
    if m:
        spds.append(int(m.group(2)) / 10.0)
    mf = re.search(r"FPS (\d+)", l)
    if mf:
        fps = int(mf.group(1))
if spds:
    nm = sum(1 for s in spds if s > 1.0)
    print(">>> GLOBAL HMT_VEL sur 20 : %d/%d bougent | moy=%.1f max=%.1f m/s | FPS serveur=%s" % (nm, len(spds), sum(spds) / len(spds), max(spds), fps), flush=True)
else:
    print(">>> pas de lecture | FPS=%s" % fps, flush=True)
print("DIAG_SCALE FINI", flush=True)
