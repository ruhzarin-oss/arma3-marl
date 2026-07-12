"""move_test v2 — teste le VRAI mecanisme : handler EachFrame 50Hz qui applique setVelocity depuis vx/vy.
2 soldats, disableAI ALL vs MOVE, pousses plein sud 8 s, deplacement reel mesure."""
import time, re, math
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
env = OpArma(squads=(("AV", 2),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=1.0, seed=1)
env.spawn({"AV": (OBJ[0] + 5, OBJ[1] - 200)}, [])
time.sleep(3)
env.b.send('(AV select 0) disableAI "ALL"; (AV select 1) disableAI "MOVE"; (AV select 1) disableAI "PATH"; (AV select 1) enableAI "TARGET";'
           '{ _x setVariable ["vx",0]; _x setVariable ["vy",0]; } forEach [AV select 0, AV select 1];', wait=True)
env.b.send('HMT_EF = addMissionEventHandler ["EachFrame", { { _x setVelocity [_x getVariable ["vx",0], _x getVariable ["vy",0], (velocity _x)#2]; } forEach [AV select 0, AV select 1]; }];', wait=True)


def pos():
    for _ in range(4):
        ls = env._query('diag_log format ["P0 %1 %2", round((getPosATL (AV select 0))#0), round((getPosATL (AV select 0))#1)];'
                        'diag_log format ["P1 %1 %2", round((getPosATL (AV select 1))#0), round((getPosATL (AV select 1))#1)];', settle=0.3)
        p0 = p1 = None
        for l in ls:
            m = re.search(r"P0 (-?\d+) (-?\d+)", l)
            if m:
                p0 = (int(m.group(1)), int(m.group(2)))
            m = re.search(r"P1 (-?\d+) (-?\d+)", l)
            if m:
                p1 = (int(m.group(1)), int(m.group(2)))
        if p0 and p1:
            return p0, p1
        time.sleep(0.3)
    return p0, p1


p0a, p1a = pos()
print("depart : u0(ALL)=%s u1(MOVE)=%s" % (p0a, p1a), flush=True)
env.b.send('{ _x setVariable ["vx",0]; _x setVariable ["vy",-4]; } forEach [AV select 0, AV select 1];', wait=True)
time.sleep(8)                                          # le EachFrame (50Hz) applique la velocite
p0b, p1b = pos()
d0 = math.hypot(p0b[0] - p0a[0], p0b[1] - p0a[1]) if p0a and p0b else -1
d1 = math.hypot(p1b[0] - p1a[0], p1b[1] - p1a[1]) if p1a and p1b else -1
print("arrivee: u0(ALL)=%s u1(MOVE)=%s" % (p0b, p1b), flush=True)
print(">>> EachFrame 50Hz : disableAI ALL = %.0f m | disableAI MOVE = %.0f m  (attendu ~32 m a 4 m/s)" % (d0, d1), flush=True)
print("MOVE_TEST FINI", flush=True)
