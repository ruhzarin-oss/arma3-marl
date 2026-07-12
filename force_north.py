"""force_north — on IGNORE la politique : on force les 20 soldats plein nord (vers l'objectif) avec le fix disableAI.
La squad avance-t-elle physiquement ? (separe collision/murs de la politique.)"""
import time, re, sys, math
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 0
N = 20
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180); GX, GY = OBJ
env = OpArma(squads=(("AV", N),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SRV)
start = (GX + 10, GY - 115)
env.spawn({"AV": start}, [(GX, GY, 10, 14)])
env.b.send('{ _x disableAI "MOVE"; _x disableAI "PATH"; _x disableAI "FSM"; _x disableAI "ANIM"; _x disableAI "AUTOCOMBAT"; _x setVariable ["vx",0]; _x setVariable ["vy",0]; } forEach (units (group (AV select 0)));', wait=True)
env.b.send('if (isNil "HMT_EF") then { HMT_EF = addMissionEventHandler ["EachFrame", { { _x setVelocity [_x getVariable ["vx",0], _x getVariable ["vy",0], (velocity _x)#2]; } forEach (units (group (AV select 0))); }]; };', wait=True)
time.sleep(2)


def dist():
    for _ in range(4):
        ls = env._query('private _s=0; { _s=_s+(getPosATL _x distance [%d,%d,0]); } forEach AV; diag_log format ["DM %%1 %%2", round(_s/((count AV) max 1)), count AV];' % (GX, GY), settle=0.25)
        for l in ls:
            m = re.search(r"DM (-?\d+) (\d+)", l)
            if m:
                return int(m.group(1)), int(m.group(2))
        time.sleep(0.3)
    return None, None


d0, n0 = dist()
print("depart : dist_moy=%sm (%s soldats) | objectif plein nord (+Y)" % (d0, n0), flush=True)
# force tout le monde plein nord (+Y) a 4 m/s pendant ~14 s, SANS requete pendant (sinon le pont sature)
cmds = "".join('(AV select %d) setVariable ["vx",0]; (AV select %d) setVariable ["vy",4];' % (i, i) for i in range(N))
env.b.send('[] spawn { %s };' % cmds, wait=True)
t_end = time.time() + 14
while time.time() < t_end:
    env.b.send('[] spawn { %s };' % cmds, wait=False)
    time.sleep(0.25)
time.sleep(0.5)
d1, _ = dist()
print(">>> FORCE NORD : %sm -> %sm  (avance de %s m si le pilotage porte la squad)" % (d0, d1, (d0 - d1) if (d0 and d1) else "?"), flush=True)
print("FORCE_NORTH FINI", flush=True)
