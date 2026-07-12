#!/usr/bin/env python3
"""traque_live.py — BOUCLE NINJA LIVE sur Arma Stratis.
La politique apprise (traque_ninja_fs.pt) pilote 9 FS REELS sur le vrai terrain, contre une defense reelle.
TraqueEnv (N=1, vrai relief bake) = CONSTRUCTEUR D'OBS nourri par l'etat Arma ; Arma = le monde (combat reel = juge).
Boucle : query etat Arma -> construit l'obs -> politique -> doMove + posture + sabotage. Spectateur regarde."""
import sys, time, re, math, ast
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import torch
from arma_bridge import ArmaBridge
from traque_env import TraqueEnv
from traque_train import FSNet, act as act_fs
from island_stratis import NODES

SB = "/mnt/data/harmattan-sandbox"; MIS = SB + "/arma3server/mpmissions/HarmattanBridge14.Stratis"; LOG = SB + "/logs/server14.out"
N_FS = 9; STEPS = 150; INS = (5250, 3050)            # insertion a la PORTE du cluster sud (radar 5250,3300 a ~250m)
NODECLASS = {"hq": "Land_Cargo_HQ_V1_F", "radar": "Land_Radar_01_HQ_F", "comms": "Land_TTowerBig_1_F"}
DEFAULT_NODE = "Land_Cargo20_military_green_F"


def q(b, sqf, tag, settle=0.5, look=400):
    b.send(sqf); time.sleep(settle)
    for ln in reversed(b._log_lines(look)):
        m = re.search(r"HARMATTAN_%s (.+)$" % tag, ln)
        if m: return m.group(1).strip().rstrip('"')
    return None


def parr(s):
    try: return ast.literal_eval(s)
    except Exception: return []


def main():
    b = ArmaBridge(mission=MIS, log=LOG); time.sleep(2)
    for _ in range(15):
        b.send('diag_log format ["HARMATTAN_PING %1",1];'); time.sleep(0.4)
        if any("HARMATTAN_PING 1" in l for l in b._log_lines(120)): print("[pont] OK", flush=True); break
        time.sleep(1.2)

    # --- SPAWN : nettoie, pose les noeuds (objets destructibles), les FS, la defense LAMBS ---
    nodes_sqf = ""
    for i, (nm, x, y, t) in enumerate(NODES):
        cls = NODECLASS.get(t, DEFAULT_NODE)
        nodes_sqf += 'HMT_NODES set [%d, (createVehicle ["%s",[%d,%d,0],[],0,"CAN_COLLIDE"])];\n' % (i, cls, x, y)
    spawn = ('[] spawn {\n'
             '{deleteVehicle _x} forEach allUnits;\n'
             'if (!isNil "HMT_NODES") then {{deleteVehicle _x} forEach HMT_NODES};\n'
             'HMT_NODES = []; HMT_NODES resize %d;\n%s'
             # FS (ouest) au sud
             'HMT_G = createGroup west; HMT_FS = []; HMT_VX = []; HMT_VY = []; HMT_CB = [];\n'
             # insertion DISPERSEE (grille 3x3 ~140m x ~90m) pour ne pas mourir en blob
             'for "_i" from 0 to %d do { private _u = HMT_G createUnit ["B_recon_F",[%d + (_i %% 3)*70 - 70, %d + (floor(_i/3))*45, 0],[],0,"FORM"]; '
             '_u setSkill 0.85; _u disableAI "FSM"; _u disableAI "ANIM"; _u disableAI "AUTOCOMBAT"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setUnitPos "MIDDLE"; '
             'HMT_FS pushBack _u; HMT_VX pushBack 0; HMT_VY pushBack 0; HMT_CB pushBack 0; };\n'
             # pilotage setVelocity : EachFrame applique la velocite SAUF aux FS passes en combat (HMT_CB=1 -> l IA d Arma reprend)
             'HMT_EH = addMissionEventHandler ["EachFrame", { { if (alive _x) then { _x setVelocity [HMT_VX select _forEachIndex, HMT_VY select _forEachIndex, (velocity _x)#2] } } forEach HMT_FS; }];\n'
             # defense (est) : 2 par noeud + une QRF
             'HMT_DEF = createGroup east;\n'
             '{ private _n=_x; for "_k" from 0 to 1 do { private _d=HMT_DEF createUnit ["O_Soldier_F",[(getPos _n)#0+(random 60)-30,(getPos _n)#1+(random 60)-30,0],[],0,"FORM"]; _d setSkill 0.55; _d setBehaviour "AWARE"; }; } forEach HMT_NODES;\n'
             'diag_log format ["HARMATTAN_SPAWN fs=%%1 def=%%2 nodes=%%3", count HMT_FS, count (allUnits select {side _x==east}), count (HMT_NODES select {!isNull _x})];\n'
             '};') % (len(NODES), nodes_sqf, N_FS - 1, INS[0], INS[1])
    b.send(spawn, timeout=30); time.sleep(8)
    sp = q(b, 'diag_log format ["HARMATTAN_SP2 %1 %2 %3", count HMT_FS, count (allUnits select {side _x==east && alive _x}), count (HMT_NODES select {!isNull _x})];', "SP2", 1.0)
    print("[spawn] FS/DEF/NODES =", sp, flush=True)

    # --- env = constructeur d'obs (vrai relief) ---
    e = TraqueEnv(num_envs=1, device="cpu", n_fs=N_FS, fs_evade=0.35, relief=True)
    net = FSNet(e.obs_dim, e.M, 160); net.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/traque_ninjacost_fs.pt", map_location="cpu")); net.eval()
    e.reset(); e.coercion[0] = 0.0
    npos = [(x, y) for _, x, y, _ in NODES]
    combat = [0] * N_FS                                   # latch : un FS au contact passe en mode assaut-tir (ANIM rallumee)
    dead = set()                                          # noeuds deja sabotes (comptes UNE seule fois)

    print("=== BOUCLE NINJA LIVE (regarde au spectateur) ===", flush=True)
    for step in range(STEPS):
        st = q(b, 'private _sf=HMT_FS apply {[round((getposatl _x)#0),round((getposatl _x)#1),[0,1] select (alive _x)]}; '
                  'private _ec=(allUnits select {side _x==east && alive _x}) apply {[round((getposatl _x)#0),round((getposatl _x)#1)]}; '
                  'private _nd=HMT_NODES apply {[0,1] select (!isNull _x)}; '
                  'diag_log format ["HARMATTAN_TQ %1|%2|%3", _sf, _ec, _nd];', "TQ", 0.6, 600)
        if not st: print("  [%02d] etat vide" % step, flush=True); time.sleep(1); continue
        p = st.split("|"); sf = parr(p[0]); ec = parr(p[1]) if len(p) > 1 else []; nd = parr(p[2]) if len(p) > 2 else []
        if len(sf) < N_FS or len(nd) < e.M: time.sleep(1); continue
        for ti in dead:                                    # noeud deja sabote -> traite MORT (sinon la policy se fige dessus si deleteVehicle a rate)
            if ti < len(nd): nd[ti] = 0
        # nourrir l'env
        e.fs_x[0] = torch.tensor([a[0] for a in sf], dtype=torch.float32)
        e.fs_y[0] = torch.tensor([a[1] for a in sf], dtype=torch.float32)
        e.fs_alive[0] = torch.tensor([float(a[2]) for a in sf])
        e.node_alive[0] = torch.tensor([float(x) for x in nd])
        # team_pos = 6 ennemis les plus proches du centre FS
        cx = sum(a[0] for a in sf) / N_FS; cy = sum(a[1] for a in sf) / N_FS
        ec_sorted = sorted(ec, key=lambda u: (u[0] - cx) ** 2 + (u[1] - cy) ** 2)[:e.n_teams] or [[cx, cy]]
        while len(ec_sorted) < e.n_teams: ec_sorted.append(ec_sorted[-1])
        e.team_pos[0] = torch.tensor(ec_sorted[:e.n_teams], dtype=torch.float32)
        e.surge[0] = torch.tensor([ec_sorted[0][0], ec_sorted[0][1]], dtype=torch.float32)
        with torch.no_grad():
            tg, po, _, _ = act_fs(net, e._obs(), e.node_alive, greedy=True)
        tg = tg[0].tolist(); po = po[0].tolist()
        # PILOTAGE : transit en glisse RAPIDE (ANIM off) ; au CONTACT -> ANIM rallumee (ils TIRENT) + assaut LENT vers le noeud (avance-tire)
        SPEED = {0: 7.0, 1: 5.0, 2: 3.0, 3: 5.0, 4: 3.0}; CONTACT_R = 130.0; ASSAULT_SPD = 2.8
        vx = []; vy = []; newcombat = []
        for i in range(N_FS):
            de = min([math.hypot(sf[i][0] - u[0], sf[i][1] - u[1]) for u in ec] or [9e9])   # ennemi le plus proche
            if combat[i] == 0 and sf[i][2] == 1 and de < CONTACT_R:
                combat[i] = 1; newcombat.append(i)                                          # bascule -> firefight (ANIM rallumee)
            tx, ty = npos[int(tg[i])]; dx = tx - sf[i][0]; dy = ty - sf[i][1]; d = math.hypot(dx, dy) + 1e-6
            spd = 0.0 if sf[i][2] == 0 else (ASSAULT_SPD if combat[i] == 1 else SPEED[int(po[i])])
            vx.append(round(dx / d * spd, 2)); vy.append(round(dy / d * spd, 2))           # glisse TOUJOURS vers la cible
        cmds = ['HMT_VX = %s; HMT_VY = %s;' % (vx, vy)]
        for i in newcombat:                                                                # rallume l IA de TIR (mais pas la FSM qui fige) -> avance-tire
            cmds.append('private _u = HMT_FS select %d; { _u enableAI _x } forEach ["ANIM","AUTOCOMBAT","TARGET","WEAPONAIM","AIMINGERROR"]; _u setCombatMode "RED";' % i)
        # SABOTAGE : tout noeud vivant a portee d'un FS vivant -> detruit UNE SEULE FOIS (set persistant)
        sab = 0
        for i in range(N_FS):
            if sf[i][2] == 0: continue
            for ti in range(e.M):
                if ti not in dead and nd[ti] == 1 and math.hypot(sf[i][0] - npos[ti][0], sf[i][1] - npos[ti][1]) < 60:
                    cmds.append('private _n = HMT_NODES select %d; _n setDamage 1; deleteVehicle _n;' % ti); e.coercion[0] += e.nw[ti]; dead.add(ti); nd[ti] = 0; sab += 1
        b.send("[] spawn {" + "; ".join(cmds) + ";};", timeout=20)
        nalive = sum(a[2] for a in sf); nleft = sum(nd)
        cx2 = sum(a[0] for a in sf) / N_FS; cy2 = sum(a[1] for a in sf) / N_FS
        mind = min([math.hypot(cx2 - npos[ti][0], cy2 - npos[ti][1]) for ti in range(e.M) if nd[ti] == 1] or [0])
        print("  [%02d] FS %d/9 | en combat %d | centre~(%d,%d) | noeud+proche %dm | noeuds %d/22 | sab %d | coercion %.0f" % (step, nalive, sum(combat), cx2, cy2, mind, nleft, sab, e.coercion[0].item()), flush=True)
        if nalive == 0 or nleft == 0: break
        time.sleep(1.0)
    print("=== FIN boucle | coercion finale %.0f/88 ===" % e.coercion[0].item(), flush=True)


if __name__ == "__main__":
    main()
