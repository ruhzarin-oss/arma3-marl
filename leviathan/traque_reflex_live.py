#!/usr/bin/env python3
"""traque_reflex_live.py — LE VRAI TEST : les REFLEXES APPRIS (R1) pilotent de vrais FS sur Arma Stratis.
Remplace le hack pantin du step 84 : au lieu de glisser tout droit dans les balles, sous le feu la politique R1
choisit la DIRECTION vers le couvert (du relief reel). Fire-sense = ennemis Arma (knowsAbout) ; cover-sense = relief bake.
Hors contact : le commandant route (glisse vers le noeud cible). En contact : le reflexe R1 prend la main."""
import sys, time, re, math, ast
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import torch
from arma_bridge import ArmaBridge
from traque_env import TraqueEnv
from reflex_fight_train import FightNet, act as act_fight
from traque_train import FSNet, act as act_cmd
from traque_coevo import CountryNet, act_country
from island_stratis import NODES

SB = "/mnt/data/harmattan-sandbox"; MIS = SB + "/arma3server/mpmissions/HarmattanBridge14.Stratis"; LOG = SB + "/logs/server14.out"
N_FS = 9; STEPS = 120; INS = (5250, 3050); MAXR = 170.0; D = 8
ang = [k * 2 * math.pi / D for k in range(D)]; DXY = [(math.cos(a), math.sin(a)) for a in ang]
NODECLASS = {"hq": "Land_Cargo_HQ_V1_F", "radar": "Land_Radar_01_HQ_F", "comms": "Land_TTowerBig_1_F"}
DEFAULT_NODE = "Land_Cargo20_military_green_F"


def q(b, sqf, tag, settle=0.6, look=600):
    b.send(sqf); time.sleep(settle)
    for ln in reversed(b._log_lines(look)):
        m = re.search(r"HARMATTAN_%s (.+)$" % tag, ln)
        if m: return m.group(1).strip().rstrip('"')
    return None


def parr(s):
    try: return ast.literal_eval(s)
    except Exception: return None


def main():
    b = ArmaBridge(mission=MIS, log=LOG); time.sleep(2)
    for _ in range(15):
        b.send('diag_log format ["HARMATTAN_PING %1",1];'); time.sleep(0.4)
        if any("HARMATTAN_PING 1" in l for l in b._log_lines(120)): print("[pont] OK", flush=True); break
        time.sleep(1.2)
    # SPAWN (memes pieces que traque_live + pilotage setVelocity ; on GARDE TARGET pour le tir reflexe)
    nodes_sqf = ""
    for i, (nm, x, y, t) in enumerate(NODES):
        nodes_sqf += 'HMT_NODES set [%d, (createVehicle ["%s",[%d,%d,0],[],0,"CAN_COLLIDE"])];\n' % (i, NODECLASS.get(t, DEFAULT_NODE), x, y)
    defstarts_sqf = "[" + ",".join("[%d,%d,0]" % (NODES[i][1], NODES[i][2]) for i in (1, 5, 9, 13, 17, 21)) + "]"   # 6 points de depart disperses
    spawn = ('[] spawn {\n{deleteVehicle _x} forEach allUnits;\n'
             'setDate [2035, 7, 6, 1, 0]; setTimeMultiplier 60;\n'         # CYCLE JOUR/NUIT : demarre en pleine nuit (01h), temps x60

             'if (!isNil "HMT_NODES") then {{deleteVehicle _x} forEach HMT_NODES};\nHMT_NODES = []; HMT_NODES resize %d;\n%s'
             'HMT_G = createGroup west; HMT_FS = []; HMT_VX = []; HMT_VY = [];\n'
             'for "_i" from 0 to %d do { private _u = HMT_G createUnit ["B_recon_F",[%d + (_i %% 3)*70 - 70, %d + (floor(_i/3))*45, 0],[],0,"FORM"]; '
             '_u setSkill 0.85; '
             # GEAR amelioré : fusil RHS + optique + NVG RHS + kit ACE (combattants ameliores)
             'removeAllWeapons _u; _u addWeapon "rhs_weap_m4a1"; _u addPrimaryWeaponItem "rhsusf_acc_eotech"; _u linkItem "rhsusf_ANPVS_15"; '
             '_u addMagazines ["rhs_mag_30Rnd_556x45_M855A1_Stanag", 8]; _u addItemToUniform "ACE_fieldDressing"; _u addItemToUniform "ACE_morphine"; '
             '_u disableAI "FSM"; _u disableAI "ANIM"; _u disableAI "AUTOCOMBAT"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; '
             'HMT_FS pushBack _u; HMT_VX pushBack 0; HMT_VY pushBack 0; };\n'
             'HMT_EH = addMissionEventHandler ["EachFrame", { { if (alive _x) then { _x setVelocity [HMT_VX select _forEachIndex, HMT_VY select _forEachIndex, (velocity _x)#2] } } forEach HMT_FS; }];\n'
             # PAYS 500 en DYN-SIM : garnison dense (8/noeud) + reserve spread, TOUS geles ; un loop Arma active ceux proches des FS (le nb engage EMERGE de la menace)
             'HMT_ALL = [];\n'
             '{ private _gg = createGroup east; for "_k" from 0 to 7 do { private _d=_gg createUnit ["O_Soldier_F",[(getPos _x)#0+(random 80)-40,(getPos _x)#1+(random 80)-40,0],[],0,"FORM"]; _d setSkill 0.5; _d setBehaviour "COMBAT"; _d setCombatMode "RED"; _d enableSimulation false; _d hideObject true; HMT_ALL pushBack _d; }; } forEach HMT_NODES;\n'
             'for "_t" from 0 to 39 do { private _g=createGroup east; private _rp=[1000+random 5000, 2700+random 3800,0]; for "_k" from 0 to 7 do { private _d=_g createUnit ["O_Soldier_F",_rp,[],40,"FORM"]; _d setSkill 0.5; _d setBehaviour "COMBAT"; _d setCombatMode "RED"; _d enableSimulation false; _d hideObject true; HMT_ALL pushBack _d; }; };\n'
             'HMT_DYN = [] spawn { while {true} do { { private _u=_x; if (alive _u) then { if ((({(_u distance _y) < 500} count HMT_FS) > 0)) then { _u enableSimulation true; _u hideObject false } else { _u enableSimulation false; _u hideObject true } } } forEach HMT_ALL; sleep 3; }; };\n'
             '};') % (len(NODES), nodes_sqf, N_FS - 1, INS[0], INS[1])
    b.send(spawn, timeout=30); time.sleep(8)
    print("[spawn]", q(b, 'diag_log format ["HARMATTAN_SP %1 %2 %3", count HMT_FS, count (allUnits select {side _x==east && alive _x}), count (HMT_NODES select {!isNull _x})];', "SP", 1.0), flush=True)

    # politique R1 (reflexe) + heightmap reel (pour le cover-sense terrain)
    rfx = FightNet(21, D, 160); rfx.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/reflex_r23wh_voyant.pt", map_location="cpu")); rfx.eval()   # R1+R2+R3 avec MANIEMENT D'ARME
    hm = TraqueEnv(num_envs=1, device="cpu", n_fs=N_FS, relief=True)
    HM = hm.HM; hx0 = hm.hx0; hy0 = hm.hy0; hres = hm.hres_x; HN = hm.HN
    # COMMANDANT APPRIS (traque_ninjacost) : vise les cibles molles + decroche ; hm sert d'obs-builder
    cmd_net = FSNet(hm.obs_dim, hm.M, 160); cmd_net.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/coevo_nuit2_fs.pt", map_location="cpu")); cmd_net.eval()   # commandant CO-EVOLUE (conscient nuit)
    # (pays-organisateur = dyn-sim cote Arma : pas de politique-pays a charger ici)

    def height(x, y):
        j = min(max(int((x - hx0) / hres), 0), HN - 1); i = min(max(int((y - hy0) / hres), 0), HN - 1)
        return float(HM[i, j])

    def los_clear(ax, ay, bx, by):                                         # FOG : le relief bloque la vue (perception shell)
        ha = height(ax, ay) + 2.0; hb = height(bx, by) + 1.2
        for t in (0.25, 0.45, 0.65, 0.85):
            if height(ax + t * (bx - ax), ay + t * (by - ay)) > ha + t * (hb - ha) + 0.7: return False
        return True

    npos = [(x, y) for _, x, y, _ in NODES]; prone = [0.0] * N_FS; dead = set(); breaking = [0] * N_FS
    coercion = 0.0; nw = hm.nw.tolist(); py_zheat = [0.0] * hm.Z   # connaissance du pays : chaleur de detection par zone
    print("=== BOUCLE REFLEXE LIVE (regarde au spectateur) ===", flush=True)
    for step in range(STEPS):
        st = q(b, 'private _sf=HMT_FS apply {[round((getposatl _x)#0),round((getposatl _x)#1),[0,1] select (alive _x && !(_x getVariable ["ACE_isUnconscious", false]))]}; '
                  'private _en=(allUnits select {private _u=_x; side _u==east && alive _u && simulationEnabled _u && ({(_u distance _x) < 400} count HMT_FS) > 0}) apply {[round((getposatl _x)#0),round((getposatl _x)#1)]}; '   # def. ACTIFS (dyn-sim) proches des FS
                  'private _nd=HMT_NODES apply {[0,1] select (!isNull _x)}; '
                  'diag_log format ["HARMATTAN_RX %1#%2#%3#%4", _sf, _en, _nd, dayTime];', "RX", 0.6, 800)
        if not st: time.sleep(1); continue
        p = st.split("#"); sf = parr(p[0]); ec = parr(p[1]) if len(p) > 1 else []; nd = parr(p[2]) if len(p) > 2 else []
        if ec is None: ec = []
        try: daytime = float(p[3])
        except Exception: daytime = 12.0
        is_night = daytime < 5.0 or daytime > 20.0
        if not sf or not nd or len(sf) < N_FS: time.sleep(1); continue
        for ti in dead:
            if ti < len(nd): nd[ti] = 0
        vx = [0.0] * N_FS; vy = [0.0] * N_FS; ncontact = 0; fire_cmds = []
        # COMMANDANT : disperse l'assaut -> chaque FS sur un noeud DIFFERENT (assignation gloutonne par proximite)
        phase = (step // 14) % 2                                          # BOUNDING : alterne base de feu / manoeuvre toutes les 14 etapes
        # COMMANDANT APPRIS : reconstruit l'obs traque depuis l'etat live -> choisit la cible de chaque FS (cibles molles)
        hm.fs_x[0] = torch.tensor([a[0] for a in sf], dtype=torch.float32); hm.fs_y[0] = torch.tensor([a[1] for a in sf], dtype=torch.float32)
        hm.fs_alive[0] = torch.tensor([float(a[2]) for a in sf])
        hm.node_alive[0] = torch.tensor([float(nd[j]) if j < len(nd) else 0.0 for j in range(hm.M)])
        ccx = sum(a[0] for a in sf) / N_FS; ccy = sum(a[1] for a in sf) / N_FS
        ecs = sorted(ec, key=lambda u: (u[0] - ccx) ** 2 + (u[1] - ccy) ** 2)[:hm.n_teams] or [[ccx, ccy]]
        while len(ecs) < hm.n_teams: ecs.append(ecs[-1])
        hm.team_pos[0] = torch.tensor(ecs[:hm.n_teams], dtype=torch.float32); hm.surge[0] = torch.tensor([ecs[0][0], ecs[0][1]], dtype=torch.float32)
        hm.coercion[0] = coercion; hm.t[0] = min(step, hm.max_steps - 1); hm.night[0] = 1.0 if is_night else 0.0
        with torch.no_grad():
            ctg, _, _, _ = act_cmd(cmd_net, hm._obs(), hm.node_alive, greedy=True)
        ctg = ctg[0].tolist(); fs_target = {i: int(ctg[i]) for i in range(N_FS) if sf[i][2] == 1}
        for i in range(N_FS):
            fx, fy, al = sf[i]
            if al == 0: continue
            threats = [e for e in ec if math.hypot(e[0] - fx, e[1] - fy) < 165.0]   # menaces = ennemis proches (proxy du feu)
            if breaking[i] > 0:                                             # HIT-AND-RUN : rompre le contact (fuir la menace)
                breaking[i] -= 1
                if threats:
                    cxk = sum(e[0] for e in threats) / len(threats); cyk = sum(e[1] for e in threats) / len(threats)
                    rdx = fx - cxk; rdy = fy - cyk
                else:
                    rdx = INS[0] - fx; rdy = INS[1] - fy
                rn = math.hypot(rdx, rdy) + 1e-6; vx[i] = rdx / rn * 7.5; vy[i] = rdy / rn * 7.5
                continue
            # FIRE-SENSE : secteur de chaque ennemi (relatif au FS), pondere par distance
            fire = [0.0] * D
            for ex, ey in threats:
                dx = ex - fx; dy = ey - fy; dd = math.hypot(dx, dy) + 1e-6
                sect = max(range(D), key=lambda k: (dx * DXY[k][0] + dy * DXY[k][1]))
                fire[sect] = max(fire[sect], max(0.05, 1 - dd / MAXR))
            # COVER-SENSE : par secteur, gain d'altitude du terrain (relief = couvert)
            h0 = height(fx, fy); cover = [0.0] * D
            for k in range(D):
                mh = max(height(fx + DXY[k][0] * s, fy + DXY[k][1] * s) for s in (12, 24, 36))
                cover[k] = min(max((mh - h0) / 14.0, 0), 1)
            cb = max(range(D), key=lambda k: cover[k]); cvx, cvy = DXY[cb]
            exposed = min(len(threats) / 3.0, 1.0)
            leftf = min(len(threats) / 3.0, 1.0)
            obs = torch.tensor([fire + [exposed] + cover + [cvx, cvy] + [prone[i], leftf]], dtype=torch.float32)
            mv, stc, frt, _, _ = act_fight(rfx, obs, greedy=True)
            mv = int(mv[0]); prone[i] = float(int(stc[0])); frsec = int(frt[0])
            if frsec > 0 and threats and step % 2 == 0:                     # R2 maniement : tir vise quand la politique juge que s'arreter est sur
                bdeg = round(math.degrees(math.atan2(DXY[frsec - 1][0], DXY[frsec - 1][1]))) % 360
                fire_cmds.append((i, bdeg))
            ti = fs_target.get(i, 0)                                       # noeud assigne par le commandant (dispersion)
            tx, ty = npos[ti]; ndx = tx - fx; ndy = ty - fy; nn = math.hypot(ndx, ndy) + 1e-6; ndx /= nn; ndy /= nn
            nthreat = len(threats); is_base = (i % 2 == phase) and not is_night   # la NUIT : tout le monde manoeuvre (assaut), pas de base de feu statique
            if nthreat >= (99 if is_night else 4):                          # NUIT (pays aveugle, pas de QRF) : on n'evade plus, on ASSAILLE
                ncontact += 1; breaking[i] = 6
                cxk = sum(e[0] for e in threats) / nthreat; cyk = sum(e[1] for e in threats) / nthreat
                rdx = fx - cxk; rdy = fy - cyk; rn = math.hypot(rdx, rdy) + 1e-6
                vx[i] = rdx / rn * 7.5; vy[i] = rdy / rn * 7.5
            elif is_base:                                                   # BASE DE FEU : tient sur place + prone + tire (TARGET) = suppression
                if threats: ncontact += 1
                prone[i] = 1.0
                if threats and mv > 0:                                      # micro-ajustement au couvert, sinon il tient (vx,vy~0)
                    vx[i] = DXY[mv - 1][0] * 1.5; vy[i] = DXY[mv - 1][1] * 1.5
            elif nthreat >= 1:                                              # MANOEUVRE sous feu modere -> bondit au noeud (feu-et-mouvement)
                ncontact += 1
                cdx, cdy = (DXY[mv - 1] if mv > 0 else (ndx, ndy))
                bdx = 0.6 * ndx + 0.4 * cdx; bdy = 0.6 * ndy + 0.4 * cdy; bn = math.hypot(bdx, bdy) + 1e-6
                vx[i] = bdx / bn * 5.5; vy[i] = bdy / bn * 5.5
            else:                                                          # libre -> fonce au noeud
                vx[i] = ndx * 8.0; vy[i] = ndy * 8.0
        cmds = ['HMT_VX = %s; HMT_VY = %s;' % ([round(v, 2) for v in vx], [round(v, 2) for v in vy])]
        for (fi, bdeg) in fire_cmds:                                       # R2 tir vise (maniement appris) : engage l'ennemi du secteur choisi
            cmds.append('private _u=HMT_FS select %d; if (alive _u) then {private _es=(allUnits select {side _x==east && alive _x && (_u distance _x)<200 && abs((((_u getDir _x)-%d+540) mod 360)-180)<28}); if (count _es>0) then {_es=_es apply {[_u distance _x,_x]}; _es sort true; private _e=(_es#0)#1; _u reveal _e; _u doTarget _e; _u doFire _e;};};' % (fi, bdeg))
        # sabotage
        sab = 0
        for i in range(N_FS):
            if sf[i][2] == 0: continue
            for ti in range(len(npos)):
                if nd[ti] == 1 and ti not in dead and math.hypot(sf[i][0] - npos[ti][0], sf[i][1] - npos[ti][1]) < 60:
                    cmds.append('deleteVehicle (HMT_NODES select %d);' % ti)   # delete simple (setDamage figeait l'actuateur)
                    coercion += nw[ti]; dead.add(ti); nd[ti] = 0; sab += 1; breaking[i] = 0 if is_night else 4   # nuit : on enchaine sans decrocher
        # ===== PAYS-ORGANISATEUR + FOG-OF-WAR : la nuit il voit court (pas de NVG), le relief bloque ; les FS (NVG) restent furtifs
        drange = 95.0 if is_night else 400.0
        detected = [(sf[i][0], sf[i][1]) for i in range(N_FS)
                    if sf[i][2] == 1 and any(math.hypot(sf[i][0] - dx, sf[i][1] - dy) < drange and los_clear(dx, dy, sf[i][0], sf[i][1]) for (dx, dy) in ec)]
        nseen = len(detected)
        # L'ORGANISATION est cote Arma (dyn-sim) : le pays s'ACTIVE au contact, le nombre engage emerge de la proximite des FS
        b.send("[] spawn {" + "; ".join(cmds) + ";};", timeout=20)
        nalive = sum(a[2] for a in sf)
        print("  [%02d] %04.1fh%s | FS %d/9 | contact %d | pays voit %d | noeuds %d/22 | coercion %.0f" % (step, daytime, "NUIT" if is_night else "jour", nalive, ncontact, nseen, sum(nd), coercion), flush=True)
        if nalive == 0: break
        time.sleep(1.0)
    print("=== FIN | survie %d/9 | coercion %.0f/88 ===" % (sum(a[2] for a in sf), coercion), flush=True)


if __name__ == "__main__":
    main()
