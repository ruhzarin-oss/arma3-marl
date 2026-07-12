"""move_test4 — baseline propre (methode rate_test2) : 1 soldat a plat (7000,7000), handler EachFrame avec
COMPTEUR DE FRAMES. Confirme : le handler tourne-t-il (frames>0) ? et setVelocity deplace-t-il (m) ?"""
import time, re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=1.0, seed=1)
b = env.b
b.send('HMT_U=(createGroup west) createUnit ["B_Soldier_F",[7000,7000,0],[],0,"FORM"]; HMT_U disableAI "ALL"; HMT_U allowDamage false; HMT_UNITS=[HMT_U]; HMT_VEL=[0,0,0]; HMT_FR=0;', wait=True)
b.send('HMT_EF4 = addMissionEventHandler ["EachFrame", { HMT_FR=HMT_FR+1; { _x setVelocity HMT_VEL } forEach HMT_UNITS; }];', wait=True)
time.sleep(2)


def rd(tag):
    for _ in range(5):
        ls = env._query('diag_log format ["MVPOS_%s %%1", getPosATL HMT_U]; diag_log format ["MVFR_%s %%1", HMT_FR];' % (tag, tag), settle=0.3)
        p = None; fr = None
        for l in ls:
            m = re.search(r"MVPOS_%s \[([-\d.]+),([-\d.]+)" % tag, l)
            if m:
                p = (float(m.group(1)), float(m.group(2)))
            m = re.search(r"MVFR_%s (\d+)" % tag, l)
            if m:
                fr = int(m.group(1))
        if p is not None and fr is not None:
            return p, fr
        time.sleep(0.3)
    return p, fr


p0, _ = rd("A")
b.send('HMT_VEL=[6,0,0]; HMT_FR=0;', wait=True)
time.sleep(5)
b.send('HMT_VEL=[0,0,0];', wait=True)
p1, fr = rd("B")
import math
d = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) if p0 and p1 else -1
hz = (fr / 5.0) if fr else 0
print("depart=%s arrivee=%s" % (p0, p1), flush=True)
print(">>> handler : %s frames en 5s = %.0f Hz | deplacement = %.0f m (attendu ~30)" % (fr, hz, d), flush=True)
print("MOVE4 FINI", flush=True)
