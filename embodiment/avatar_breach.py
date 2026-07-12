"""avatar_breach — PERCEE ARTICULEE, cerveau vivant. Deux roles : APPUI (base de feu, suppresse l'objectif)
+ ASSAUT (bondit sous le feu). Terrain degage. Victoire = OPFOR neutralise PAR DES DEGATS QU'ON A INFLIGES
(corrige le faux 'neutralise'). args: server_idx seed cycles."""
import time, re, sys, math
import numpy as np, torch
from op_arma import OpArma
from train_koth_gpu import Net
import paros as M
SB = "/mnt/data/harmattan-sandbox"; DEV = "cuda:0"
SRV = int(sys.argv[1]) if len(sys.argv) > 1 else 7
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 51
CYCLES = int(sys.argv[3]) if len(sys.argv) > 3 else 320
N_SUP, N_ASLT, N_DEF = 3, 4, 4
N_ATK = N_SUP + N_ASLT
OBJ = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)          # terrain degage sud-Paros
SCALE, SIGHT = 140.0, 110.0
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


env = OpArma(squads=(("SUP", N_SUP), ("ASLT", N_ASLT)), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
start_sup = (OBJ[0] - 40, OBJ[1] - 120)
start_aslt = (OBJ[0] + 30, OBJ[1] - 120)
env.spawn({"SUP": start_sup, "ASLT": start_aslt}, [(OBJ[0], OBJ[1], N_DEF, 12)])
SUP_POS = (OBJ[0] - 45, OBJ[1] - 95)                # position d'appui (flanc, ~95 m)
env.b.send('ATK = SUP + ASLT; { _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; _x setBehaviour "AWARE"; } forEach ATK;'
           '{ _x enableAI "ALL"; _x enableAI "TARGET"; _x enableAI "AUTOTARGET"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; _x setSkill 0.55; } forEach HMT_EN;', wait=True)
time.sleep(2)
print("=== PERCEE ARTICULEE : %d APPUI + %d ASSAUT vs %d DEF (server%d) ===" % (N_SUP, N_ASLT, N_DEF, SRV), flush=True)
gx, gy = OBJ
ax = np.concatenate([np.full(N_SUP, start_sup[0]), np.full(N_ASLT, start_aslt[0])]).astype(float)
ay = np.concatenate([np.full(N_SUP, start_sup[1]), np.full(N_ASLT, start_aslt[1])]).astype(float)
adm = np.zeros(N_ATK); asup = np.zeros(N_ATK); afat = np.zeros(N_ATK); apos = ["STAND"] * N_ATK
last_cmd = [-1] * N_ATK; at_sup = [False] * N_ATK
t_start = time.time(); fired_ever = False; dmg_dealt = 0.0; def_dmg_prev = np.zeros(N_DEF); outcome = "timeout"; ever_def = False
for c in range(CYCLES):
    ls = env._query('{ private _u = ATK select _forEachIndex; private _p = getPosATL _u; diag_log format ["HA %1 %2 %3 %4 %5 %6 %7", _forEachIndex, round(_p#0), round(_p#1), stance _u, round((getDammage _u)*100), round((getSuppression _u)*100), round((getFatigue _u)*100)]; } forEach ATK;'
                    '{ private _e = HMT_EN select _forEachIndex; private _q = getPosATL _e; diag_log format ["HE %1 %2 %3 %4", _forEachIndex, round(_q#0), round(_q#1), round((getDammage _e)*100)]; } forEach HMT_EN; diag_log "BREND";', settle=0.15)
    ex, ey, edm = [None] * N_DEF, [None] * N_DEF, [None] * N_DEF
    got = False
    for l in ls:
        m = re.search(r"HA (\d+) (-?\d+) (-?\d+) (\w+) (\d+) (\d+) (\d+)", l)
        if m:
            i = int(m.group(1))
            if i < N_ATK:
                got = True; ax[i] = int(m.group(2)); ay[i] = int(m.group(3)); apos[i] = m.group(4)
                adm[i] = int(m.group(5)) / 100.0; asup[i] = int(m.group(6)) / 100.0; afat[i] = int(m.group(7)) / 100.0
        me = re.search(r"HE (\d+) (-?\d+) (-?\d+) (\d+)", l)
        if me:
            j = int(me.group(1))
            if j < N_DEF:
                ex[j] = int(me.group(2)); ey[j] = int(me.group(3)); edm[j] = int(me.group(4))
    if not got:
        time.sleep(0.05); continue
    al = adm < 0.7
    if not al.any():
        outcome = "ASSAUT DETRUIT"; print("  t=%.0fs : %s" % (time.time() - t_start, outcome), flush=True); break
    have_def = [j for j in range(N_DEF) if edm[j] is not None]
    if have_def:
        ever_def = True
        for j in have_def:
            if edm[j] > def_dmg_prev[j]:
                dmg_dealt += (edm[j] - def_dmg_prev[j]); def_dmg_prev[j] = edm[j]
        epx = np.array([ex[j] for j in have_def], float); epy = np.array([ey[j] for j in have_def], float)
        eal = np.array([edm[j] < 70 for j in have_def])
        n_def = int(eal.sum())
    else:
        epx = np.zeros(0); epy = np.zeros(0); eal = np.zeros(0, bool); n_def = int(def_dmg_prev[def_dmg_prev < 70].size)
    # VICTOIRE fiable : plus de defenseurs vivants ET on a inflige des degats reels
    if ever_def and have_def and n_def == 0 and dmg_dealt > 60:
        outcome = "OBJECTIF PRIS"; print("  t=%.0fs : PERCEE REUSSIE (degats infliges=%.0f)" % (time.time() - t_start, dmg_dealt), flush=True); break
    bo = base_obs(ax, ay, al, gx, gy, epx, epy, eal); bo[:, 9] = asup
    nd_known = None
    if have_def:
        kk = np.argmin([(ex[j] - gx) ** 2 + (ey[j] - gy) ** 2 for j in have_def])
    stc = np.array([STANCE.get(p, 0.0) for p in apos])
    # known enemy = nearest defender to each attacker
    kdx = np.zeros(N_ATK); kdy = np.zeros(N_ATK)
    kpx = np.full(N_ATK, gx, float); kpy = np.full(N_ATK, gy, float)   # cible de tir = vrai defenseur le plus proche
    if have_def:
        for i in range(N_ATK):
            dd = [(ex[j] - ax[i]) ** 2 + (ey[j] - ay[i]) ** 2 for j in have_def]
            j = have_def[int(np.argmin(dd))]
            kdx[i] = (ex[j] - ax[i]) / SCALE; kdy[i] = (ey[j] - ay[i]) / SCALE
            kpx[i] = ex[j]; kpy[i] = ey[j]
    obs = np.concatenate([bo, afat[:, None], stc[:, None], kdx[:, None], kdy[:, None]], 1).astype(np.float32)
    with torch.no_grad():
        acts = brain.a_logits(torch.tensor(obs, device=DEV)).argmax(1).cpu().numpy()
    cmds = []
    for i in range(N_ATK):
        if not al[i]:
            continue
        sup_role = i < N_SUP
        u = "(ATK select %d)" % i
        if sup_role:
            d_sp = math.hypot(ax[i] - SUP_POS[0], ay[i] - SUP_POS[1])
            if d_sp > 14 and not at_sup[i]:
                if last_cmd[i] != 1:
                    cmds.append('private _u = %s; _u setUnitPos "AUTO"; _u doMove [%d, %d, 0];' % (u, SUP_POS[0], SUP_POS[1])); last_cmd[i] = 1
            else:
                at_sup[i] = True
                cmds.append('private _u = %s; doStop _u; _u setUnitPos "MIDDLE"; _u doWatch [%d,%d,0]; _u doSuppressiveFire [%d, %d, 1];' % (u, int(kpx[i]), int(kpy[i]), int(kpx[i]), int(kpy[i])))
                fired_ever = True; last_cmd[i] = 2
        else:
            # BOND : pousse tant que la suppression est gerable ; clouee -> RIPOSTE (ajoute du feu), pas terre
            if asup[i] > 0.7 and have_def:
                cmds.append('private _u = %s; _u setUnitPos "MIDDLE"; _u doSuppressiveFire [%d, %d, 1];' % (u, int(kpx[i]), int(kpy[i]))); fired_ever = True; last_cmd[i] = 2
            else:
                if last_cmd[i] != 1 or c % 8 == 0:
                    cmds.append('private _u = %s; _u setUnitPos "AUTO"; _u doMove [%d, %d, 0];' % (u, gx, gy)); last_cmd[i] = 1
    if cmds:
        env.b.send("\n".join(cmds), wait=True)
    if c % 6 == 0:
        nsup = int(al[:N_SUP].sum()); nas = int(al[N_SUP:].sum())
        dmean = float(np.mean([math.hypot(ax[i] - gx, ay[i] - gy) for i in range(N_SUP, N_ATK) if al[i]])) if al[N_SUP:].any() else 0
        smean = float(np.mean(asup[N_SUP:][al[N_SUP:]])) if al[N_SUP:].any() else 0
        print("  t=%4.1fs|APPUI %d/%d ASSAUT %d/%d DEF %d/%d|assaut dist %3.0fm sup %.2f|degats_infliges %3.0f" % (
            time.time() - t_start, nsup, N_SUP, nas, N_ASLT, n_def, N_DEF, dmean, smean, dmg_dealt), flush=True)
    time.sleep(0.05)
nsup = int((adm[:N_SUP] < 0.7).sum()); nas = int((adm[N_SUP:] < 0.7).sum())
print(">>> BREACH | %.0fs | issue=%s | APPUI %d/%d ASSAUT %d/%d survivants | DEF restants %d/%d | degats_infliges=%.0f" % (
    time.time() - t_start, outcome, nsup, N_SUP, nas, N_ASLT, n_def, N_DEF, dmg_dealt), flush=True)
print("BREACH FINI", flush=True)
