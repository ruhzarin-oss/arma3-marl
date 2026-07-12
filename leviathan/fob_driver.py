#!/usr/bin/env python3
"""fob_driver.py — Bloc C : pilote les COQUILLES de Younes (arm_shells.sqf) sur HarmattanFOB.Stratis.

Calé sur le Bloc B RÉEL (arm_shells.sqf) :
  HMT_READ logge :  HARMATTAN_RX n=<N> mode=<bool> en=[[x,y],...] | x,y,dmg,ok;x,y,dmg,ok;...
    - par coquille (ordre HMT_PILOT, figé à l'ARM) : x, y, damage(0-100), ok(vivant&conscient 0/1)
    - en = ennemis DÉTECTÉS par le pays (knowsAbout>1) = fog réaliste = mes FS injectés
  J'écris : HMT_DVX / HMT_DVY (Est/Nord) / HMT_DDIR (cap), longueur = count HMT_PILOT.
  Le tir ÉMERGE (TARGET gardé) -> aucun doFire. HMT_PILOT figé -> pas de dérive d'index.

--dry : chaîne parse -> perceive -> act -> write contre un RX au FORMAT RÉEL, sans Arma."""
import sys, math, re, ast, time, argparse, random, json, os
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import torch
from agent_swarm import AgentSwarm

LEV = "/home/younes/arma3-marl/leviathan"
D = 8

# --- couture GENERAL <-> DRIVER (par fichiers, le driver reste seul maitre du pont) ---
ORDERS_F = LEV + "/general_orders.json"
WORLD_F = LEV + "/world_state.json"
SECTORS = [("Mike26", 4279, 3856), ("AirBase", 2050, 5700), ("Maxwell", 3253, 2984), ("Kamino", 6544, 4863),
           ("Rogain", 4886, 5948), ("AgiaMarina", 2915, 6165), ("Tempest", 1942, 3557), ("OldOutpost", 4319, 4398),
           ("LZBaldy", 4604, 5284), ("MilRange", 3338, 5744), ("AgiosIoannis", 3027, 2184), ("Tsoukalia", 4206, 2715),
           ("Girna", 1935, 2723), ("KaminoFR", 6402, 5427), ("LZConnor", 2979, 1860), ("AgiosCephas", 2719, 1712),
           ("Strogos", 2024, 1790), ("Keiros", 6157, 4349), ("Limeri", 5440, 3687), ("Nisi", 1784, 4134),
           ("Kyfi", 1790, 3512), ("MarinaBay", 2648, 5990), ("Tsoukala", 4241, 2498), ("KaminoCoast", 5691, 6124), ("GirnaBay", 1845, 2656)]
SEC_XY = {n: (x, y) for n, x, y in SECTORS}


def read_general_focus():
    """Lit le focus impose par le general (secteur ou masser). None si pas d'ordre / pas frais."""
    try:
        d = json.load(open(ORDERS_F))
        if time.time() - d.get("ts", 0) > 60: return None      # ordre perime -> ignore
        return SEC_XY.get(d.get("focus"))
    except Exception:
        return None


def write_world_state(shells, enemies):
    """Expose la situation au general (active shells + ennemis connus, resumee par secteur)."""
    live = [(s[0], s[1]) for s in shells if len(s) >= 4 and s[3] == 1]
    rows = []
    for name, x, y in SECTORS:
        own = sum(1 for px, py in live if math.hypot(px - x, py - y) < 200)
        ds = [math.hypot(x - e[0], y - e[1]) for e in enemies if math.hypot(x - e[0], y - e[1]) < 450]
        rows.append([name, own, (round(min(ds)) if ds else -1)])
    try:
        json.dump({"ts": time.time(), "rows": rows}, open(WORLD_F, "w"))
    except Exception:
        pass


def parr(s):
    try: return ast.literal_eval(s)
    except Exception: return None


def parse_rx(payload):
    """`n=<N> mode=<bool> en=[[x,y],...] | x,y,dmg,ok;...` -> (shells, enemies)."""
    left, _, right = payload.partition("|")
    m = re.search(r"en=(\[.*\])", left)
    enemies = parr(m.group(1)) if m else []
    shells = []
    for tok in right.strip().rstrip(";").split(";"):
        if not tok: continue
        f = tok.split(",")
        if len(f) >= 4:
            try: shells.append([int(f[0]), int(f[1]), int(f[2]), int(f[3])])
            except ValueError: pass
    return shells, (enemies or [])


class FobDriver:
    """Pilote les coquilles-défenseurs. But : masser sur le FS détecté proche, sinon tenir le FOB."""
    def __init__(self, swarm, nodes, speed=5.0, planner=None):
        self.sw = swarm; self.nodes = nodes; self.speed = speed
        self.prone = {}                                              # état stance par id (logique, ANIM off)
        self.focus = None                                           # point de massage imposé par le GÉNÉRAL (ou None)
        self.planner = planner                                      # PatrolBrain.planner(tick) : rondes en paix (None = tenir)
        self.patrol_wp = {}                                         # waypoint de ronde courant par id d'agent (HMT_PILOT)
        self.flank_goals = {}                                      # ETAPE 4 : but de flanc par id (pose par l'orchestration)

    def goals(self, live_shells, fs_pos, idx=None):
        out = []
        for k, s in enumerate(live_shells):
            x, y = s[0], s[1]
            aid = idx[k] if idx is not None else None
            if aid is not None and self.flank_goals.get(aid):       # FLANC (orchestration) : l'agent manœuvre vers le point de flanc
                out.append(self.flank_goals[aid]); continue
            if fs_pos:
                nf = min(fs_pos, key=lambda f: math.hypot(x - f[0], y - f[1]))
                if math.hypot(x - nf[0], y - nf[1]) < 250: out.append([nf[0], nf[1]]); continue
            if self.focus:                                          # le GÉNÉRAL ordonne de masser -> les réserves convergent
                out.append([self.focus[0], self.focus[1]]); continue
            fob = min(self.nodes, key=lambda n: math.hypot(x - n[0], y - n[1]))
            if self.planner is not None and idx is not None:        # PAIX : ronde autour du FOB (sinon tenir)
                wp = self.patrol_wp.get(aid)
                if wp is None or math.hypot(x - wp[0], y - wp[1]) < 12.0:
                    wp = self.planner(aid, fob, [x, y]); self.patrol_wp[aid] = wp
                out.append(wp); continue
            out.append([fob[0], fob[1]])
        return out

    def tick(self, shells, enemies):
        """shells (HMT_READ) + enemies (FS détectés) -> (HMT_DVX, HMT_DVY, HMT_DDIR), longueur = len(shells)."""
        N = len(shells)
        dvx = [0.0] * N; dvy = [0.0] * N; ddir = [0.0] * N
        live = [(i, s) for i, s in enumerate(shells) if len(s) >= 4 and s[3] == 1]   # ok = vivant&conscient
        if not live: return dvx, dvy, ddir
        idx = [i for i, _ in live]
        pos = [[s[0], s[1]] for _, s in live]
        prone = [self.prone.get(i, 0.0) for i in idx]
        fs_pos = [[e[0], e[1]] for e in enemies]
        obs, thr, cdir = self.sw.perceive(pos, fs_pos, prone)
        mv, stc, frt = self.sw.act(obs)
        goals = self.goals([s for _, s in live], fs_pos, idx)
        vx, vy = self.sw.decide_velocity(pos, mv, thr, cdir, goals, assault=False, speed=self.speed)
        # BASCULE deux-corps : agents SANS menace -> corps de VOYAGE (marche/contourne) ; avec menace -> combat (déjà fait)
        if getattr(self, "travel", None) is not None:
            travel_k = [k for k in range(len(live)) if float(thr[k]) == 0]
            if travel_k:
                tvx, tvy = self.travel.velocity([pos[k] for k in travel_k],
                                                [goals[k] for k in travel_k],
                                                [idx[k] for k in travel_k])
                for j, k in enumerate(travel_k):
                    vx[k] = tvx[j]; vy[k] = tvy[j]
        for k, i in enumerate(idx):
            self.prone[i] = float(stc[k])
            dvx[i] = round(float(vx[k]), 2); dvy[i] = round(float(vy[k]), 2)
            if float(thr[k]) > 0 and fs_pos:                        # cap : face menace si contact, sinon sens de marche
                nf = min(fs_pos, key=lambda f: (pos[k][0] - f[0]) ** 2 + (pos[k][1] - f[1]) ** 2)
                ddir[i] = round(math.degrees(math.atan2(nf[0] - pos[k][0], nf[1] - pos[k][1])) % 360, 1)
            else:
                ddir[i] = round(math.degrees(math.atan2(dvx[i], dvy[i])) % 360, 1) if (dvx[i] or dvy[i]) else 0.0
        return dvx, dvy, ddir

    @staticmethod
    def write_sqf(dvx, dvy, ddir):
        return "HMT_DVX = %s; HMT_DVY = %s; HMT_DDIR = %s;" % (dvx, dvy, ddir)

    @staticmethod
    def stop_sqf():                                                 # shutdown propre / fail-safe : tout à 0
        return "{ HMT_DVX set [_forEachIndex,0]; HMT_DVY set [_forEachIndex,0]; } forEach HMT_PILOT;"


class PatrolBrain:
    """Cerveau de PATROUILLE (paix) : chaque agent fait une ronde autour de son FOB.
    note_threat() mémorise les contacts récents ; planner(tick) rend un plan(aid, home, pos)->[wx,wy]
    qui fait tourner la ronde et la PENCHE vers l'axe de menace appris (écran défensif)."""
    def __init__(self, nodes, ring_r=70.0, k=6, decay=150):
        self.nodes = nodes; self.ring_r = ring_r; self.k = k; self.decay = decay
        self.threats = []                                           # [(x, y, tick)] contacts mémorisés
        self.ring = [(math.cos(2 * math.pi * i / k), math.sin(2 * math.pi * i / k)) for i in range(k)]

    def note_threat(self, enemy, tick):
        self.threats.append((float(enemy[0]), float(enemy[1]), int(tick)))

    def _axis_for(self, home, tick):
        """Vecteur unitaire moyen home->menaces récentes (None si calme)."""
        ax = ay = 0.0; n = 0
        for (x, y, t) in self.threats:
            if tick - t > self.decay: continue
            dx = x - home[0]; dy = y - home[1]; d = math.hypot(dx, dy)
            if d < 1.0 or d > 1000.0: continue
            ax += dx / d; ay += dy / d; n += 1
        if n == 0: return None
        m = math.hypot(ax, ay)
        return (ax / m, ay / m) if m > 1e-3 else None

    def planner(self, tick):
        """Rend la fonction de ronde du moment (purge la mémoire ancienne au passage)."""
        self.threats = [(x, y, t) for (x, y, t) in self.threats if tick - t <= self.decay]
        ring = self.ring; R = self.ring_r; kf = self.k
        def plan(aid, home, pos):
            j = (aid + tick // 4) % kf                              # l'index tourne lentement -> mouvement de ronde
            ox, oy = ring[j]
            wx = home[0] + ox * R; wy = home[1] + oy * R
            axis = self._axis_for(home, tick)
            if axis is not None:                                    # penche la ronde vers la menace
                wx += axis[0] * R * 0.8; wy += axis[1] * R * 0.8
            return [round(wx, 1), round(wy, 1)]
        return plan


def load_body(device="cpu"):
    from reflex_fight_train import FightNet
    net = FightNet(21, D, 160)
    net.load_state_dict(torch.load(LEV + "/reflex_r23wh_voyant.pt", map_location=device)); net.eval()
    return net


def synth_hm(HN=400, hres=7.5):
    yy, xx = torch.meshgrid(torch.arange(HN), torch.arange(HN), indexing="ij")
    return (8 * torch.sin(xx.float() / 11) * torch.cos(yy.float() / 9)).float(), 0.0, 0.0, hres, HN


def run_dry():
    random.seed(2)
    HM, hx0, hy0, hres, HN = synth_hm()
    body = load_body("cpu")
    sw = AgentSwarm(body, HM, hx0, hy0, hres, HN, group_var="HMT_PILOT", enemy_side="west", device="cpu")
    nodes = [(random.uniform(1500, 6000), random.uniform(2500, 6000)) for _ in range(25)]
    drv = FobDriver(sw, nodes)
    # --- construit un HARMATTAN_RX au FORMAT REEL de arm_shells.sqf ---
    Npil = 60
    shells_str = ""
    truth = []
    for j in range(Npil):
        x = round(random.uniform(1500, 6000)); y = round(random.uniform(2500, 6000))
        ok = 1; dmg = 0
        if j == 3: ok = 0; dmg = 100                               # un mort
        if j == 7: ok = 0                                          # un inconscient
        shells_str += "%d,%d,%d,%d;" % (x, y, dmg, ok); truth.append(ok)
    en = [[round(random.uniform(1500, 6000)), round(random.uniform(2500, 6000))] for _ in range(9)]
    payload = "n=%d mode=true en=%s | %s" % (Npil, str(en).replace(" ", ""), shells_str)
    shells, enemies = parse_rx(payload)
    assert len(shells) == Npil, "parse coquilles KO (%d)" % len(shells)
    assert len(enemies) == 9, "parse ennemis KO (%d)" % len(enemies)
    dvx, dvy, ddir = drv.tick(shells, enemies)
    assert len(dvx) == Npil and len(ddir) == Npil
    assert dvx[3] == 0.0 and dvy[3] == 0.0 and dvx[7] == 0.0, "mort/inconscient pilote a tort"
    nlive = sum(truth)
    nmoving = sum(1 for i in range(Npil) if abs(dvx[i]) > 1e-6 or abs(dvy[i]) > 1e-6)
    w = drv.write_sqf(dvx, dvy, ddir)
    assert w.startswith("HMT_DVX =") and "HMT_DDIR" in w
    assert drv.stop_sqf().startswith("{ HMT_DVX set")
    print("[dry] parse format REEL : %d coquilles, %d FS detectes" % (len(shells), len(enemies)))
    print("[dry] %d vivantes+conscientes pilotees, %d en mouvement ; mort(#3)/inconscient(#7) -> 0 OK" % (nlive, nmoving))
    print("[dry] write (%d car.) : %s ..." % (len(w), w[:80]))
    print("[dry] fail-safe stop_sqf pret")
    print("=== DRY OK : driver C cale sur arm_shells.sqf REEL — parse->perceive->act->write ===")


MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"


def run_live(steps=30, wake=40):
    """RUN 1 : prouve la couture B<->C + le pilotage. Reveille ~wake defenseurs -> HMT_ARM ->
    les pilote comme AGENTS vers le HVT (cible 0). Pas de FS (run 2). Retour LAMBS a la fin."""
    from arma_bridge import ArmaBridge
    b = ArmaBridge(mission=MIS, log=LOG)
    try:
        b.send('diag_log "HARMATTAN_PING ok";', timeout=20)
    except Exception as e:
        print("[pont] PAS DE PING:", e, "-> server_fob ne tourne pas le pont (reboot launch_fob.sh)"); return
    print("[pont] OK", flush=True)
    r = b.query('diag_log format ["HARMATTAN_HASARM %1", !(isNil "HMT_ARM")];', r'HARMATTAN_HASARM (\w+)', want=1)
    has = r[-1].group(1) if r else "?"
    print("[B] HMT_ARM defini :", has, flush=True)
    if has != "true":
        print(">>> arm_shells PAS charge sur l'instance courante -> reboot server_fob requis (bash launch_fob.sh)"); return
    # reveiller ~wake defenseurs (sinon dyn-sim les gele -> rien a armer)
    b.send('{ if (!isNull _x) then {_x enableSimulation true; _x hideObject false} } forEach ((HMT_FOB_MEN apply {_x select 0}) select [0,%d]);' % wake, timeout=20)
    time.sleep(2)
    r = b.query('diag_log format ["HARMATTAN_TGT %1", HMT_TARGET apply {[round ((getPosATL _x)#0), round ((getPosATL _x)#1)]}];', r'HARMATTAN_TGT (\[.*\])', want=1)
    tg = parr(r[-1].group(1)) if r else None
    rally = tuple(tg[0]) if tg else (3253, 2984)
    print("[cibles] %d | rally(HVT) = %s" % (len(tg or []), rally), flush=True)
    b.send('call HMT_ARM;', timeout=20); time.sleep(2)
    HM, hx0, hy0, hres, HN = synth_hm()                              # run 1 : pas de menace -> cover-sense neutre, HM synthetique ok
    sw = AgentSwarm(load_body("cpu"), HM, hx0, hy0, hres, HN, group_var="HMT_PILOT", enemy_side="west", device="cpu")
    drv = FobDriver(sw, [rally], speed=5.0)

    def read():
        r = b.query('call HMT_READ;', r'HARMATTAN_RX (.+)', want=1, timeout=12)
        return parse_rx(r[-1].group(1)) if r else ([], [])

    print("=== RUN 1 LIVE : coquilles-AGENTS vers le HVT (regarde au spectateur) ===", flush=True)
    prev = None
    for step in range(steps):
        shells, enemies = read()
        if not shells:
            print("  [%02d] 0 coquille active (rien arme ?)" % step, flush=True); time.sleep(0.6); continue
        drv.focus = read_general_focus()                            # le GÉNÉRAL (Qwen) impose où masser
        write_world_state(shells, enemies)                          # j'expose la situation au GÉNÉRAL
        live = [(s[0], s[1]) for s in shells if s[3] == 1]
        dvx, dvy, ddir = drv.tick(shells, enemies)
        b.send("HMT_DVX = %s; HMT_DVY = %s; HMT_DDIR = %s;" % (dvx, dvy, ddir))
        disp = 0.0
        if prev and live:
            n = min(len(live), len(prev))
            if n: disp = sum(math.hypot(live[i][0] - prev[i][0], live[i][1] - prev[i][1]) for i in range(n)) / n
        prev = live
        print("  [%02d] coquilles-agents %d | -> HVT | depl.moy %.1f m | ennemis %d" % (step, len(live), disp, len(enemies)), flush=True)
        time.sleep(1.0)
    b.send('{HMT_DVX set [_forEachIndex,0]; HMT_DVY set [_forEachIndex,0];} forEach HMT_PILOT;', timeout=15); time.sleep(0.5)
    b.send('call HMT_DISARM;', timeout=15)
    print("=== FIN run 1 : coquilles pilotees comme AGENTS, retour LAMBS ===", flush=True)


def run_fight(steps=40, n_fs=9, fob=(3253, 2984)):
    """RUN 2 : le COMBAT. Reveille la garnison du FOB cible, spawn les FS (agents) a ~450 m, les fait
    converger ; tes defenseurs-agents detectent les FS (en= dans HMT_READ) et MASSENT dessus. Deux camps appris."""
    from arma_bridge import ArmaBridge
    b = ArmaBridge(mission=MIS, log=LOG)
    try: b.send('diag_log "HARMATTAN_PING ok";', timeout=20)
    except Exception as e: print("[pont] PAS DE PING:", e); return
    print("[pont] OK | FOB cible =", fob, flush=True)
    fx, fy = fob; ins = (fx - 250, fy)                               # FS plus proches (250 m) -> contact rapide
    # 1) reveiller la garnison proche du FOB (active -> armable + combat)
    b.send('{ private _u=_x select 0; if (!isNull _u && {(_u distance %s) < 450}) then {_u enableSimulation true; _u hideObject false} } forEach HMT_FOB_MEN;' % ("[%d,%d,0]" % (fx, fy)), timeout=20)
    time.sleep(2)
    # 2) spawn FS attaquants (west, gear RHS+NVG, pilotes par vitesse, TARGET garde -> tir emerge)
    spawn = ('[] spawn {\n'
             'if (!isNil "HMT_FS_EH") then { removeMissionEventHandler ["EachFrame", HMT_FS_EH]; };\n'
             'if (!isNil "HMT_FS") then { { deleteVehicle _x } forEach HMT_FS; };\n'
             'HMT_FS_G = createGroup west; HMT_FS = []; HMT_FVX = []; HMT_FVY = [];\n'
             'for "_i" from 0 to %d do { private _u = HMT_FS_G createUnit ["B_recon_F", [%d + (_i %% 3)*15, %d + (floor(_i/3))*15, 0], [], 0, "FORM"];\n'
             '_u setSkill 0.85; removeAllWeapons _u; _u addWeapon "rhs_weap_m4a1"; _u addPrimaryWeaponItem "rhsusf_acc_eotech"; _u linkItem "rhsusf_ANPVS_15";\n'
             '_u addMagazines ["rhs_mag_30Rnd_556x45_M855A1_Stanag", 8];\n'
             '_u disableAI "FSM"; _u disableAI "ANIM"; _u disableAI "AUTOCOMBAT"; _u setBehaviour "COMBAT"; _u setCombatMode "RED";\n'
             'HMT_FS pushBack _u; HMT_FVX pushBack 0; HMT_FVY pushBack 0; };\n'
             'HMT_FS_EH = addMissionEventHandler ["EachFrame", { { if (alive _x) then { _x setVelocity [HMT_FVX select _forEachIndex, HMT_FVY select _forEachIndex, (velocity _x)#2] } } forEach HMT_FS; }];\n'
             '};') % (n_fs - 1, ins[0], ins[1])
    b.send(spawn, timeout=30); time.sleep(4)
    # 3) armer les defenseurs
    b.send('call HMT_ARM;', timeout=20); time.sleep(2)
    HM, hx0, hy0, hres, HN = synth_hm()
    sw = AgentSwarm(load_body("cpu"), HM, hx0, hy0, hres, HN, group_var="HMT_PILOT", enemy_side="west", device="cpu")
    drv = FobDriver(sw, [fob], speed=5.0)

    def read_def():
        r = b.query('call HMT_READ;', r'HARMATTAN_RX (.+)', want=1, timeout=12)
        return parse_rx(r[-1].group(1)) if r else ([], [])

    def read_fs():
        r = b.query('diag_log format ["HARMATTAN_FS %1", HMT_FS apply {[round ((getPosATL _x)#0), round ((getPosATL _x)#1), [0,1] select (alive _x)]}];', r'HARMATTAN_FS (\[.*\])', want=1, timeout=12)
        return parr(r[-1].group(1)) if r else []

    print("=== RUN 2 LIVE : COMBAT FS-agents vs defenseurs-agents (regarde au spectateur) ===", flush=True)
    for step in range(steps):
        fs = read_fs()
        if not fs: print("  [%02d] FS introuvables" % step, flush=True); time.sleep(0.6); continue
        b.send('{ if (alive _x) then { east reveal [_x, 4] } } forEach HMT_FS;')   # le pays DETECTE (reseau d'alerte/recon = defense_eval)
        shells, enemies = read_def()
        drv.focus = read_general_focus()                            # le GÉNÉRAL (Qwen) impose où masser
        write_world_state(shells, enemies)                          # j'expose la situation au GÉNÉRAL
        # FS : foncent sur le FOB (mouvement simple ; le tir emerge via TARGET)
        fvx = []; fvy = []
        for a in fs:
            if a[2] == 0: fvx.append(0.0); fvy.append(0.0); continue
            dx = fx - a[0]; dy = fy - a[1]; dn = math.hypot(dx, dy) + 1e-6
            sp = 6.0 if dn > 50 else 0.0
            fvx.append(round(dx / dn * sp, 2)); fvy.append(round(dy / dn * sp, 2))
        b.send("HMT_FVX = %s; HMT_FVY = %s;" % (fvx, fvy))
        # defenseurs-agents : massent sur les FS detectes (enemies), sinon tiennent le FOB
        if shells:
            dvx, dvy, ddir = drv.tick(shells, enemies)
            b.send("HMT_DVX = %s; HMT_DVY = %s; HMT_DDIR = %s;" % (dvx, dvy, ddir))
        nfs = sum(a[2] for a in fs); ndef = sum(1 for s in shells if len(s) >= 4 and s[3] == 1)
        dmin = min((math.hypot(a[0] - fx, a[1] - fy) for a in fs if a[2] == 1), default=999)
        print("  [%02d] FS %d/%d | defenseurs-agents %d | contacts %d | FS-FOB min %.0fm" % (step, nfs, n_fs, ndef, len(enemies), dmin), flush=True)
        if nfs == 0: print("  -> tous les FS tombes"); break
        time.sleep(1.0)
    # cleanup
    b.send('{HMT_DVX set [_forEachIndex,0]; HMT_DVY set [_forEachIndex,0];} forEach HMT_PILOT; call HMT_DISARM;', timeout=15); time.sleep(0.5)
    b.send('if (!isNil "HMT_FS_EH") then { removeMissionEventHandler ["EachFrame", HMT_FS_EH]; }; { deleteVehicle _x } forEach HMT_FS; HMT_FS = [];', timeout=15)
    print("=== FIN run 2 : combat deux-camps-agents joue, nettoyage OK ===", flush=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry", action="store_true"); ap.add_argument("--steps", type=int, default=30); ap.add_argument("--fight", action="store_true")
    a = ap.parse_args()
    if a.dry: run_dry(); return
    if a.fight: run_fight(steps=a.steps); return
    run_live(steps=a.steps)


if __name__ == "__main__":
    main()
