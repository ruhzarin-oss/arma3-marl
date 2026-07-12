"""move_test5 — baseline DECISIF : spawn AV (parse confirme) a PLAT (7000,7000), methode rate_test
(global HMT_VEL + EachFrame + compteur). setVelocity bouge-t-il un soldat sur du plat ?"""
import time, re, math
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=1.0, seed=1)
env.spawn({"AV": (OBJ[0] + 5, OBJ[1] - 200)}, [])      # sud du complexe (spawn valide, parse confirme en v2)
time.sleep(2)
b = env.b
b.send('(AV select 0) disableAI "ALL"; (AV select 0) allowDamage false; HMT_UNITS=[AV select 0]; HMT_VEL=[0,0,0]; HMT_FR=0;', wait=True)
b.send('HMT_EF5 = addMissionEventHandler ["EachFrame", { HMT_FR=HMT_FR+1; { _x setVelocity HMT_VEL } forEach HMT_UNITS; }];', wait=True)
time.sleep(2)


def rd():
    for _ in range(5):
        ls = env._query('private _p=getPosATL (AV select 0); diag_log format ["MVP %1 %2 %3", round(_p#0), round(_p#1), HMT_FR];', settle=0.3)
        for l in ls:
            m = re.search(r"MVP (-?\d+) (-?\d+) (\d+)", l)
            if m:
                return (int(m.group(1)), int(m.group(2))), int(m.group(3))
        time.sleep(0.3)
    return None, None


p0, _ = rd()
b.send('HMT_VEL=[6,0,0]; HMT_FR=0;', wait=True)
time.sleep(5)
b.send('HMT_VEL=[0,0,0];', wait=True)
p1, fr = rd()
d = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) if p0 and p1 else -1
print("depart=%s arrivee=%s" % (p0, p1), flush=True)
print(">>> handler %s frames/5s (%.0f Hz) | deplacement PLAT = %.0f m (attendu ~30)" % (fr, (fr or 0) / 5.0, d), flush=True)
print("MOVE5 FINI", flush=True)
