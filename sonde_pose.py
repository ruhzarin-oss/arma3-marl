#!/usr/bin/env python3
"""sonde_pose — C EST LA POSE. Laquelle ?

Les deux cadences de `setVelocity` rendent 4 m sur 8 s la ou une poussee continue en donnerait
48. Ce n est donc ni la politique ni la cadence : c est la maniere dont les hommes sont poses.
Le suspect est `disableAI "PATH"` — repris du banc d appui, ou les hommes NE DOIVENT PAS
bouger. Sur des assaillants qu on pilote a la vitesse, c est peut-etre l inverse de ce qu il
faut. `move_combat.py` a ete ecrit pour cette question exacte.

QUATRE POSES, meme poussee a chaque image :
  P  disableAI PATH + AUTOCOMBAT + FSM   (ce que fait le banc live aujourd hui)
  A  disableAI ALL
  R  aucun disableAI
  M  disableAI MOVE
"""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

EXT, CAP, DUREE = 5830, 6.0, 8

POSES = {
    "P  PATH+AUTOCOMBAT+FSM": '_u disableAI "PATH"; _u disableAI "AUTOCOMBAT"; _u disableAI "FSM";',
    "A  ALL                ": '_u disableAI "ALL";',
    "R  aucun              ": '',
    "M  MOVE               ": '_u disableAI "MOVE";',
}
POSE_TPL = '''
HMT_OBJ = [1734, 5391, 0];
private _g = createGroup west; HMT_T = [];
for "_i" from 1 to 4 do {
    private _p = [(HMT_OBJ select 0) + (_i * 8), (HMT_OBJ select 1) + 200, 0];
    private _u = _g createUnit ["B_Soldier_F", _p, [], 0, "NONE"];
    _u setPosATL _p; _u allowDamage false;
    __POSE__
    _u setBehaviour "AWARE"; _u setCombatMode "BLUE";
    HMT_T pushBack _u;
};
HMT_P0 = []; { HMT_P0 pushBack (getPosATL _x) } forEach HMT_T;
diag_log format ["SONDE_POSE n=%1", count HMT_T];
'''
MESURE = '''
private _d = 0;
{ private _a = HMT_P0 select _forEachIndex; private _b = getPosATL _x;
  _d = _d + sqrt (((_b select 0)-(_a select 0))^2 + ((_b select 1)-(_a select 1))^2);
} forEach HMT_T;
diag_log format ["SONDE_DEPL %1", round (_d / (count HMT_T))];
'''
PUSH = ('HMT_V=[0,%f,0]; HMT_EH = addMissionEventHandler ["EachFrame", '
        '{ { _x setVelocity HMT_V } forEach HMT_T }];' % CAP)
STOP = 'removeMissionEventHandler ["EachFrame", HMT_EH];'


def lire(b, motif, delai=4.0):
    t0 = time.time()
    while time.time() - t0 < delai:
        for L in reversed(b._log_lines(400)):
            m = re.search(motif, L)
            if m: return m.group(1)
        time.sleep(0.2)
    return None


b = SocketBridge(EXT)
print(f"\n  poussee continue de {CAP} m/s pendant {DUREE} s -> ~{CAP*DUREE:.0f} m attendus\n", flush=True)
for nom, pose in POSES.items():
    b.send('{ deleteVehicle _x } forEach (if (isNil "HMT_T") then {[]} else {HMT_T}); HMT_T=[];', wait=False)
    time.sleep(1)
    b.send(POSE_TPL.replace("__POSE__", pose)); time.sleep(2)
    if lire(b, r"SONDE_POSE n=(\d+)") is None:
        print(f"  {nom} : pose echouee", flush=True); continue
    b.send(PUSH, wait=False); time.sleep(DUREE)
    b.send(STOP, wait=False); time.sleep(0.5)
    b.send(MESURE, wait=False)
    d = lire(b, r"SONDE_DEPL (\d+)")
    print(f"  {nom} : {d} m", flush=True)
b.sock.close()
