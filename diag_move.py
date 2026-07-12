"""diag_move — pourquoi 20 soldats forces plein nord n'avancent pas ? On regarde :
- count AV vs count (units group) [limite 12/groupe d'Arma]
- vitesse reelle (m/s) de chaque soldat pendant le pilotage, et batiments a <8m."""
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
# ESPACE les soldats sur une grille 5 col x 16m (sinon ils se collent et se bloquent)
spread = "".join('(AV select %d) setPosATL [%d, %d, 0];' % (i, GX - 32 + (i % 5) * 16, GY - 150 + (i // 5) * 16) for i in range(N))
env.b.send('[] spawn { %s };' % spread, wait=True)
time.sleep(1.0)
env.b.send('{ _x disableAI "MOVE"; _x disableAI "PATH"; _x disableAI "FSM"; _x disableAI "ANIM"; _x disableAI "AUTOCOMBAT"; _x setVariable ["vx",0]; _x setVariable ["vy",0]; } forEach AV;', wait=True)
# handler sur AV DIRECTEMENT (pas group, pour contourner la limite 12/groupe) ; nom unique, pas de garde
env.b.send('HMT_EF_D = addMissionEventHandler ["EachFrame", { { _x setVelocity [_x getVariable ["vx",0], _x getVariable ["vy",0], (velocity _x)#2]; } forEach AV; }];', wait=True)
time.sleep(1.5)
ls = env._query('diag_log format ["CNT av=%1 grp=%2 grps=%3", count AV, count (units (group (AV select 0))), count (allGroups select {side _x == side (AV select 0)})];', settle=0.3)
for l in ls:
    m = re.search(r"CNT av=(\d+) grp=(\d+) grps=(\d+)", l)
    if m:
        print(">>> count AV=%s | units(group AV0)=%s | nb groupes alli, =%s" % (m.group(1), m.group(2), m.group(3)), flush=True)
# pilote plein nord ~4s puis mesure vitesse reelle
cmds = "".join('(AV select %d) setVariable ["vx",0]; (AV select %d) setVariable ["vy",4];' % (i, i) for i in range(N))
env.b.send('[] spawn { %s };' % cmds, wait=True)
t_end = time.time() + 4
while time.time() < t_end:
    env.b.send('[] spawn { %s };' % cmds, wait=False); time.sleep(0.25)
ls = env._query('{ diag_log format ["U %1 spd=%2 bld=%3 z=%4", _forEachIndex, round((vectorMagnitude velocity _x)*10), count (nearestObjects [getPosATL _x, ["House","Building","Wall","Fortification"], 6]), round((getPosATL _x)#2 *10)]; } forEach AV;', settle=0.4)
spds = []; blds = []
for l in ls:
    m = re.search(r"U (\d+) spd=(\d+) bld=(\d+) z=(-?\d+)", l)
    if m:
        spds.append(int(m.group(2)) / 10.0); blds.append(int(m.group(3)))
if spds:
    n_moving = sum(1 for s in spds if s > 1.0)
    n_near_bld = sum(1 for b in blds if b > 0)
    print(">>> pendant pilotage nord 4 m/s : %d/%d soldats bougent (>1 m/s) | vitesse moy=%.1f m/s max=%.1f" % (n_moving, len(spds), sum(spds) / len(spds), max(spds)), flush=True)
    print(">>> %d/%d soldats ont un batiment/mur a <6m" % (n_near_bld, len(blds)), flush=True)
print("DIAG_MOVE FINI", flush=True)
