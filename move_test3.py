"""move_test3 — methode EXACTE de rate_test (global HMT_VEL + EachFrame). Compare PLAT(7000,7000) vs COMPLEXE.
Isole : setVelocity bouge-t-il sur du plat mais pas sur le terrain du complexe ?"""
import time, re, math
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=1.0, seed=1)
b = env.b
b.send('HMT_A = (createGroup west) createUnit ["B_Soldier_F",[7000,7000,0],[],0,"FORM"]; HMT_A disableAI "ALL"; HMT_A allowDamage false;', wait=True)
b.send('HMT_B = (createGroup west) createUnit ["B_Soldier_F",[%d,%d,0],[],0,"FORM"]; HMT_B disableAI "ALL"; HMT_B allowDamage false;' % (OBJ[0], OBJ[1] - 100), wait=True)
b.send('HMT_UNITS=[HMT_A,HMT_B]; if (isNil "HMT_VEL") then {HMT_VEL=[0,0,0]};', wait=True)
b.send('HMT_EF2 = addMissionEventHandler ["EachFrame", { { if (!isNull _x) then {_x setVelocity HMT_VEL} } forEach HMT_UNITS; }];', wait=True)
time.sleep(2)


def pos():
    for _ in range(4):
        ls = env._query('diag_log format ["A %1 %2", round((getPosATL HMT_A)#0), round((getPosATL HMT_A)#1)];'
                        'diag_log format ["B %1 %2", round((getPosATL HMT_B)#0), round((getPosATL HMT_B)#1)];', settle=0.3)
        a = bb = None
        for l in ls:
            m = re.search(r"\bA (-?\d+) (-?\d+)", l)
            if m:
                a = (int(m.group(1)), int(m.group(2)))
            m = re.search(r"\bB (-?\d+) (-?\d+)", l)
            if m:
                bb = (int(m.group(1)), int(m.group(2)))
        if a and bb:
            return a, bb
        time.sleep(0.3)
    return a, bb


a0, b0 = pos()
print("depart : PLAT=%s COMPLEXE=%s" % (a0, b0), flush=True)
b.send('HMT_VEL=[6,0,0];', wait=True)                 # plein est, 6 m/s
time.sleep(5)
b.send('HMT_VEL=[0,0,0];', wait=True)
a1, b1 = pos()
da = math.hypot(a1[0] - a0[0], a1[1] - a0[1]) if a0 and a1 else -1
db = math.hypot(b1[0] - b0[0], b1[1] - b0[1]) if b0 and b1 else -1
print("arrivee: PLAT=%s COMPLEXE=%s" % (a1, b1), flush=True)
print(">>> deplacement (5s @ 6 m/s, attendu ~30 m) : PLAT = %.0f m | COMPLEXE = %.0f m" % (da, db), flush=True)
print("MOVE3 FINI", flush=True)
