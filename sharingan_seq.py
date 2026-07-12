"""sharingan_seq (etape 1 / memoire) — enregistre les demos LAMBS en SEQUENCES TEMPORELLES (la trajectoire de
chaque soldat dans le temps), pas en paires melangees. Necessaire pour entrainer un cerveau a MEMOIRE (recurrent).
Sortie : staff/sharingan_seq14.npz = X[N,T,14] (padded), y[N,T], lengths[N]. args: episodes."""
import time, re, sys, math
import numpy as np
from op_arma import OpArma
import paros as M
SB = "/mnt/data/harmattan-sandbox"
OBJ = M.COMPLEXE
N_ATQ, N_DEF = 8, 8
EPISODES = int(sys.argv[1]) if len(sys.argv) > 1 else 14
STEPS = 35
SIGHT, SCALE = 110.0, 140.0
STANCE = {"STAND": 0.0, "CROUCH": 0.5, "PRONE": 1.0}
MIN_LEN = 6


def base_obs(px, py, al, gx, gy, epx, epy, eal):
    n = len(px)
    ox = (px - gx) / SCALE; oy = (py - gy) / SCALE; dgx = (gx - px) / SCALE; dgy = (gy - py) / SCALE
    dx = px[None, :] - px[:, None]; dy = py[None, :] - py[:, None]
    d2 = np.where(np.eye(n, dtype=bool) | (~al)[None, :], 1e18, dx * dx + dy * dy)
    jm = d2.argmin(1); adx = dx[np.arange(n), jm] / SCALE; ady = dy[np.arange(n), jm] / SCALE
    nm = d2.min(1) >= 1e18; adx[nm] = 0; ady[nm] = 0
    if len(epx) and eal.any():
        ex = epx[None, :] - px[:, None]; ey = epy[None, :] - py[:, None]
        ed2 = np.where(eal[None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(1)
        edx = ex[np.arange(n), km]; edy = ey[np.arange(n), km]
        nd = np.sqrt(ed2.min(1)); seen = (nd <= SIGHT) & (ed2.min(1) < 1e18)
        edx = (edx / SCALE) * seen; edy = (edy / SCALE) * seen
    else:
        edx = np.zeros(n); edy = np.zeros(n)
    return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), adx, ady, edx, edy, np.zeros(n)], 1).astype(np.float32)


env = OpArma(squads=(("ATQ", N_ATQ),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=2.0, seed=1)
SEQX, SEQY = [], []
print("=== Sharingan SEQUENCES : %d episodes, maitre LAMBS (obs14, trajectoires temporelles) ===" % EPISODES, flush=True)
for ep in range(EPISODES):
    th = 2 * math.pi * ep / EPISODES
    start = (OBJ[0] + int(230 * math.cos(th)), OBJ[1] + int(230 * math.sin(th)))
    env.spawn({"ATQ": start}, [(OBJ[0], OBJ[1], N_DEF, 30)])
    env.b.send('private _g = group (ATQ select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g,0]};'
               'private _wp = _g addWaypoint [[%d,%d],0]; _wp setWaypointType "SAD"; _g setBehaviour "COMBAT"; _g setCombatMode "RED";' % (OBJ[0], OBJ[1]), wait=True)
    time.sleep(2)
    uX = [[] for _ in range(N_ATQ)]; uY = [[] for _ in range(N_ATQ)]
    prev_amm = np.full(N_ATQ, -1.0)
    for st in range(STEPS):
        ls = env._query('{ private _u=ATQ select _forEachIndex; private _p=getPosATL _u; private _ne=_u findNearestEnemy _u; private _kx=0; private _ky=0; private _hk=0;'
                        ' if (!isNull _ne && {(_u knowsAbout _ne) >= 1}) then { private _np=getPosATL _ne; _kx=_np#0; _ky=_np#1; _hk=1; };'
                        ' diag_log format ["HA %1 %2 %3 %4 %5 %6 %7 %8 %9 %10 %11 %12", _forEachIndex, round(_p#0), round(_p#1), round((vectorMagnitude velocity _u)*10), stance _u, round((getDammage _u)*100), (_u ammo currentWeapon _u), round((getSuppression _u)*100), round((getFatigue _u)*100), round _kx, round _ky, _hk]; } forEach ATQ;'
                        '{ private _u=HMT_EN select _forEachIndex; private _p=getPosATL _u; diag_log format ["HE %1 %2 %3 %4", _forEachIndex, round(_p#0), round(_p#1), round((getDammage _u)*100)]; } forEach HMT_EN; diag_log "HMT_REC";', settle=1.0)
        ax = np.zeros(N_ATQ); ay = np.zeros(N_ATQ); asp = np.zeros(N_ATQ); apos = ["STAND"] * N_ATQ
        adm = np.full(N_ATQ, 100.0); amm = np.full(N_ATQ, -1.0); asup = np.zeros(N_ATQ); afat = np.zeros(N_ATQ)
        akx = np.zeros(N_ATQ); aky = np.zeros(N_ATQ); ahk = np.zeros(N_ATQ)
        ex, ey, edm = [], [], []
        for l in ls:
            m = re.search(r"HA (\d+) (-?\d+) (-?\d+) (\d+) (\w+) (\d+) (\d+) (\d+) (\d+) (-?\d+) (-?\d+) (\d+)", l)
            if m:
                i = int(m.group(1))
                if i < N_ATQ:
                    ax[i] = int(m.group(2)); ay[i] = int(m.group(3)); asp[i] = int(m.group(4)) / 10.0; apos[i] = m.group(5)
                    adm[i] = int(m.group(6)); amm[i] = int(m.group(7)); asup[i] = int(m.group(8)) / 100.0; afat[i] = int(m.group(9)) / 100.0
                    akx[i] = int(m.group(10)); aky[i] = int(m.group(11)); ahk[i] = int(m.group(12))
            m2 = re.search(r"HE (\d+) (-?\d+) (-?\d+) (\d+)", l)
            if m2:
                ex.append(int(m2.group(2))); ey.append(int(m2.group(3))); edm.append(int(m2.group(4)))
        al = adm < 70
        if not al.any():
            break
        epx = np.array(ex, float); epy = np.array(ey, float); eal = (np.array(edm, float) < 70) if edm else np.zeros(0, bool)
        bo = base_obs(ax, ay, al, OBJ[0], OBJ[1], epx, epy, eal); bo[:, 9] = asup
        kdx = np.where(ahk > 0, (akx - ax) / SCALE, 0.0); kdy = np.where(ahk > 0, (aky - ay) / SCALE, 0.0)
        stc = np.array([STANCE.get(p, 0.0) for p in apos])
        obs = np.concatenate([bo, afat[:, None], stc[:, None], kdx[:, None], kdy[:, None]], 1).astype(np.float32)
        fired = (prev_amm >= 0) & (amm >= 0) & (amm < prev_amm)
        for i in range(N_ATQ):
            if not al[i]:
                continue
            if fired[i]:
                a = 2
            elif asp[i] > 1.5:
                a = 1
            elif apos[i] in ("PRONE", "CROUCH"):
                a = 3
            else:
                a = 0
            uX[i].append(obs[i]); uY[i].append(a)
        prev_amm = np.where(amm >= 0, amm, prev_amm)
        time.sleep(0.4)
    for i in range(N_ATQ):
        if len(uX[i]) >= MIN_LEN:
            SEQX.append(np.array(uX[i], np.float32)); SEQY.append(np.array(uY[i], np.int64))
    print("ep %d/%d -> %d sequences cumulees" % (ep + 1, EPISODES, len(SEQX)), flush=True)
# pad
T = max(len(s) for s in SEQX); N = len(SEQX); D = 14
X = np.zeros((N, T, D), np.float32); Y = np.full((N, T), -1, np.int64); L = np.zeros(N, np.int64)
for k, (sx, sy) in enumerate(zip(SEQX, SEQY)):
    X[k, :len(sx)] = sx; Y[k, :len(sy)] = sy; L[k] = len(sx)
np.savez("/home/younes/arma3-marl/staff/sharingan_seq14.npz", X=X, y=Y, lengths=L)
print("CORPUS SEQUENCES : %d sequences | T_max %d | pas totaux %d -> staff/sharingan_seq14.npz" % (N, T, int(L.sum())), flush=True)
print("SEQ FINI", flush=True)
