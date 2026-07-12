"""op_deploy_brain — DEPLOIEMENT REEL : le cerveau distille de LAMBS (obs14) commande de VRAIS soldats Arma.
Boucle : pont -> obs14 par unite -> cerveau -> ordre Arma (avancer/suppresser/couvert/tenir). Vrai ennemi. Serveur vanilla."""
import time, re, sys, math, collections
import numpy as np, torch
from op_arma import OpArma
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
OBJ = M.COMPLEXE; N_ATQ, N_DEF = 8, 8; STEPS = 30
SIGHT, SCALE = 110.0, 140.0
STANCE = {"STAND": 0.0, "CROUCH": 0.5, "PRONE": 1.0}
ACT = ["TENIR", "AVANCER", "SUPPRESSER", "COUVERT"]
brain = Net(14, 4, 512, 3).to(DEV)
brain.load_state_dict(torch.load("/home/younes/arma3-marl/koth_lambs_cloned14.pt", map_location=DEV)); brain.eval()


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


env = OpArma(squads=(("ATQ", N_ATQ),), mission=SB + "/arma3server/mpmissions/HarmattanBridge2.Altis",
             log=SB + "/logs/server2.out", acc=2.0, seed=7)
start = (OBJ[0] + 120, OBJ[1] - 110)
print("=== DEPLOIEMENT cerveau distille sur VRAIS soldats (server2 vanilla) ===", flush=True)
env.spawn({"ATQ": start}, [(OBJ[0], OBJ[1], N_DEF, 30)])
env.b.send('private _g = group (ATQ select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; } forEach units _g;'
           '_g setBehaviour "AWARE"; _g setCombatMode "YELLOW"; _g setSpeedMode "NORMAL";', wait=True)
time.sleep(2)
# etat PERSISTANT par soldat : une ligne de log manquante n'efface pas l'unite (sinon faux morts)
ax = np.full(N_ATQ, start[0], float); ay = np.full(N_ATQ, start[1], float); apos = ["STAND"] * N_ATQ
adm = np.zeros(N_ATQ); asup = np.zeros(N_ATQ); afat = np.zeros(N_ATQ)
akx = np.zeros(N_ATQ); aky = np.zeros(N_ATQ); ahk = np.zeros(N_ATQ)
last_act = [-1] * N_ATQ          # ordre de marche emis UNE fois par transition (pas de doMove en boucle)
for st in range(STEPS):
    ls = env._query('{ private _u = ATQ select _forEachIndex; private _p = getPosATL _u; private _ne = _u findNearestEnemy _u; private _kx = 0; private _ky = 0; private _hk = 0;'
                    ' if (!isNull _ne && {(_u knowsAbout _ne) >= 1}) then { private _np = getPosATL _ne; _kx = _np#0; _ky = _np#1; _hk = 1; };'
                    ' diag_log format ["HA %1 %2 %3 %4 %5 %6 %7 %8 %9 %10 %11 %12", _forEachIndex, round(_p#0), round(_p#1), round((vectorMagnitude velocity _u)*10), stance _u, round((getDammage _u)*100), (_u ammo currentWeapon _u), round((getSuppression _u)*100), round((getFatigue _u)*100), round _kx, round _ky, _hk]; } forEach ATQ;'
                    '{ private _u = HMT_EN select _forEachIndex; private _p = getPosATL _u; diag_log format ["HE %1 %2 %3 %4", _forEachIndex, round(_p#0), round(_p#1), round((getDammage _u)*100)]; } forEach HMT_EN; diag_log "HMT_REC";', settle=1.5)
    ex, ey, edm = [], [], []
    for l in ls:
        m = re.search(r"HA (\d+) (-?\d+) (-?\d+) (\d+) (\w+) (\d+) (\d+) (\d+) (\d+) (-?\d+) (-?\d+) (\d+)", l)
        if m:
            i = int(m.group(1))
            if i < N_ATQ:
                ax[i] = int(m.group(2)); ay[i] = int(m.group(3)); apos[i] = m.group(5); adm[i] = int(m.group(6))
                asup[i] = int(m.group(8)) / 100.0; afat[i] = int(m.group(9)) / 100.0
                akx[i] = int(m.group(10)); aky[i] = int(m.group(11)); ahk[i] = int(m.group(12))
        m2 = re.search(r"HE (\d+) (-?\d+) (-?\d+) (\d+)", l)
        if m2:
            ex.append(int(m2.group(2))); ey.append(int(m2.group(3))); edm.append(int(m2.group(4)))
    al = adm < 70
    if not al.any():
        print("  pas %d : tous les attaquants HS" % st, flush=True); break
    epx = np.array(ex, float); epy = np.array(ey, float); eal = (np.array(edm, float) < 70) if edm else np.zeros(0, bool)
    bo = base_obs(ax, ay, al, OBJ[0], OBJ[1], epx, epy, eal); bo[:, 9] = asup
    kdx = np.where(ahk > 0, (akx - ax) / SCALE, 0.0); kdy = np.where(ahk > 0, (aky - ay) / SCALE, 0.0)
    stc = np.array([STANCE.get(p, 0.0) for p in apos])
    obs = np.concatenate([bo, afat[:, None], stc[:, None], kdx[:, None], kdy[:, None]], 1).astype(np.float32)
    with torch.no_grad():
        acts = brain.a_logits(torch.tensor(obs, device=DEV)).argmax(1).cpu().numpy()
    # --- PYRAMIDE : intention de commandement = avancer tant qu'on n'est pas REELLEMENT engage ;
    #     le cerveau-reflexe ne garde la main que quand l'unite voit un ennemi ou est supprimee ---
    for i in range(N_ATQ):
        if not al[i]:
            continue
        engaged = (bo[i, 7] != 0.0 or bo[i, 8] != 0.0) or (asup[i] > 0.3)
        if not engaged:
            acts[i] = 1
    cmds = []
    for i in range(N_ATQ):
        if not al[i]:
            continue
        u = "(ATQ select %d)" % i; a = int(acts[i])
        if a == 1:
            if last_act[i] != 1:        # (re)lance la marche seulement sur transition -> pas de re-pathing
                cmds.append('private _u = %s; _u setUnitPos "AUTO"; _u doMove [%d, %d, 0];' % (u, OBJ[0], OBJ[1]))
        elif a == 2:
            if ahk[i] > 0:
                cmds.append('private _u = %s; doStop _u; _u setUnitPos "MIDDLE"; _u doWatch [%d, %d, 0]; _u doSuppressiveFire [%d, %d, 1];' % (u, akx[i], aky[i], akx[i], aky[i]))
            else:
                cmds.append('private _u = %s; doStop _u; _u setUnitPos "MIDDLE";' % u)
        elif a == 3:
            cmds.append('private _u = %s; doStop _u; _u setUnitPos "DOWN";' % u)
        else:
            cmds.append('private _u = %s; doStop _u; _u setUnitPos "UP";' % u)
        last_act[i] = a
    if cmds:
        env.b.send("\n".join(cmds), wait=True)
    nliv = int(al.sum()); ndef = int(eal.sum()) if edm else N_DEF
    md = float(np.mean([math.hypot(ax[i] - OBJ[0], ay[i] - OBJ[1]) for i in range(N_ATQ) if al[i]]))
    dist = collections.Counter([ACT[int(acts[i])] for i in range(N_ATQ) if al[i]])
    print("  pas %2d | ATQ vivants %d/%d  DEF vivants %d/%d  dist_moy_obj %5.0fm | actions %s" % (st, nliv, N_ATQ, ndef, N_DEF, md, dict(dist)), flush=True)
    time.sleep(0.3)
print("DEPLOY FINI", flush=True)
