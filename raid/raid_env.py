#!/usr/bin/env python3
"""raid_env.py — ENVIRONNEMENT Arma-dans-la-boucle pour le RAID FORCES SPECIALES (HARMATTAN).
20 SF BLUFOR prennent un objectif decompose en 10 sous-objectifs, defendu par REDFOR (garnison + QRF reactive).
Interface type Gym : reset() -> obs ; step(targets) -> obs, reward, done, info.
Pilotage Python via ArmaBridge, avec les lecons de plomberie occupation :
  - handshake de disponibilite avant le 1er spawn
  - spawns batches + verification/retry (compte par side)
  - indexation stable des SF via HMT_SF_arr (snapshot, survit aux morts)
  - 1 seul aller-retour pont par pas (etat compacte sur une ligne)."""
import os, sys, time, subprocess, re, ast, math
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"
N_SF = 20
N_SUBOBJ = 10
R_HOLD = 35.0          # rayon de prise d'un sous-objectif (m)
DT = 8                 # secondes simulees par pas
MAX_STEPS = 40         # ~5 min d'episode

class RaidEnv:
    def __init__(self, slot=2, obj_center=(14038, 16143), n_def=30, n_qrf=14, verbose=True):
        self.slot = slot; self.port = 2402 + slot * 100
        self.mis = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % slot
        self.log = SB + "/logs/server%d.out" % slot
        self.obj = obj_center; self.n_def = n_def; self.n_qrf = n_qrf; self.verbose = verbose
        self.sf_class = "B_Soldier_F"        # FS ; swap "B_recon_F" une fois la boucle validee
        self.b = None; self.booted = False
        # 10 sous-objectifs en anneau (~180 m) autour du centre
        self.subobj = [(obj_center[0] + 180 * math.cos(2 * math.pi * i / N_SUBOBJ),
                        obj_center[1] + 180 * math.sin(2 * math.pi * i / N_SUBOBJ)) for i in range(N_SUBOBJ)]
        self.insertion = (obj_center[0] - 650, obj_center[1] - 650)   # ~920 m au SO
        self.qrf_pos = (obj_center[0] + 900, obj_center[1] + 900)

    # ---------- infra serveur / pont ----------
    def _sh(self, c): return subprocess.run(c, shell=True, capture_output=True, text=True)
    def _launch(self):
        self._sh("pkill -9 -f 'profiles%d'" % self.slot); time.sleep(3)
        self._sh("rm -rf '%s'; cp -r '%s/arma3server/mpmissions/HarmattanBridge.Altis' '%s'" % (self.mis, SB, self.mis))
        self._sh("rm -f '%s/hmt_bridge/'cmd_*.sqf" % self.mis)
        self._sh("sed 's/HarmattanBridge\\.Altis/HarmattanBridge%d.Altis/g' '%s/staging/server.cfg' > '%s/staging/server%d.cfg'" % (self.slot, SB, SB, self.slot))
        self._sh("mkdir -p '%s/profiles%d'; : > '%s'" % (SB, self.slot, self.log))
        self._sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 -config='%s/staging/server%d.cfg' -profiles='%s/profiles%d' -port=%d -world=Altis -autoInit >> '%s' 2>&1 < /dev/null & disown" % (SB, 5801 + self.slot, SB, self.slot, SB, self.slot, self.port, self.log))
    def _wait_boot(self, t=200):
        t0 = time.time()
        while time.time() - t0 < t:
            try:
                if "Starting mission" in open(self.log, encoding="utf-8", errors="ignore").read(): time.sleep(10); return True
            except FileNotFoundError: pass
            time.sleep(4)
        return False
    def _q(self, sqf, tag):
        try: self.b.send(sqf, timeout=12)
        except Exception: return None
        time.sleep(0.4)
        for ln in reversed(self.b._log_lines(300)):
            m = re.search(r"HARMATTAN_%s (.+)$" % tag, ln)
            if m: return m.group(1).strip().rstrip('"')
        return None
    def _qnum(self, sqf, tag):
        v = self._q(sqf, tag)
        try: return float(v)
        except (TypeError, ValueError): return None
    def _wait_ready(self, tries=18):
        for _ in range(tries):
            if self._qnum('diag_log format ["HARMATTAN_PING %1", 1];', "PING") == 1.0: return True
            time.sleep(2)
        return False
    def fps(self): return self._qnum('diag_log format ["HARMATTAN_FPS %1", round diag_fps];', "FPS")
    def _ecount(self): return self._qnum('diag_log format ["HARMATTAN_EC %1", count (allUnits select {side _x==east && alive _x})];', "EC")
    def _wcount(self): return self._qnum('diag_log format ["HARMATTAN_WC %1", count (allUnits select {side _x==west && alive _x})];', "WC")
    def _parse_arr(self, s):
        try: return ast.literal_eval(s)
        except Exception: return []
    def _spawn_verify(self, cmd, counter, need, label):
        """envoie un spawn court, verifie qu'il a pris (compte par side), retry 3x."""
        c = 0
        for _ in range(3):
            self.b.send(cmd, timeout=20); time.sleep(5)        # spawn async ([] spawn) : laisser la boucle createUnit finir
            c = counter() or 0
            if c >= need: break
        if self.verbose: print("[reset] spawn %s -> compte=%d (requis>=%d)" % (label, c, need), flush=True)
        return c

    # ---------- API Gym ----------
    def _alive(self):
        if self.b is None: return False
        return self._qnum('diag_log format ["HARMATTAN_PING %1", 1];', "PING") == 1.0
    def _boot(self):
        self._launch()
        if self.verbose: print("[slot %d] boot..." % self.slot, flush=True)
        if not self._wait_boot(): raise RuntimeError("boot echec slot %d" % self.slot)
        self.b = ArmaBridge(mission=self.mis, log=self.log)
        if not self._wait_ready(): raise RuntimeError("handshake echec slot %d" % self.slot)
        self.booted = True
    def reset(self):
        # serveur chaud : on vide la scene au lieu de relancer (~3 min de boot economises/episode)
        if not self.booted or not self._alive():
            self._boot()
        else:
            self.b.send('[] spawn { { deleteVehicle _x } forEach allUnits; };', timeout=15); time.sleep(2)
        ox, oy = self.obj; qx, qy = self.qrf_pos; ix, iy = self.insertion
        # chaque spawn lourd enveloppe dans [] spawn {} : pile FRAICHE, pas d'accumulation sur le thread actuateur
        garr = '[] spawn { HMT_DEF = createGroup east; for "_a" from 1 to %d do { HMT_DEF createUnit ["O_Soldier_F", [%d+(random 160)-80, %d+(random 160)-80, 0], [], 0, "FORM"]; }; {_x setSkill 0.65; _x setBehaviour "AWARE"} forEach units HMT_DEF; [HMT_DEF,[%d,%d],160] call BIS_fnc_taskPatrol; };' % (self.n_def, ox, oy, ox, oy)
        qrf = '[] spawn { HMT_QRF = createGroup east; for "_a" from 1 to %d do { HMT_QRF createUnit ["O_Soldier_F", [%d+(random 30)-15, %d+(random 30)-15, 0], [], 0, "FORM"]; }; {_x setSkill 0.7; _x setBehaviour "AWARE"} forEach units HMT_QRF; HMT_ALERT = 0; };' % (self.n_qrf, qx, qy)
        sf = '[] spawn { HMT_SF = createGroup west; for "_a" from 1 to %d do { HMT_SF createUnit ["%s", [%d+(random 40)-20, %d+(random 40)-20, 0], [], 0, "FORM"]; }; {_x setSkill 0.75; _x setBehaviour "AWARE"; _x setCombatMode "YELLOW"} forEach units HMT_SF; HMT_SF_arr = units HMT_SF; };' % (N_SF, self.sf_class, ix, iy)
        self._spawn_verify(garr, self._ecount, self.n_def - 2, "DEF")
        ec = self._spawn_verify(qrf, self._ecount, self.n_def + self.n_qrf - 4, "QRF")
        wc = self._spawn_verify(sf, self._wcount, N_SF - 2, "SF")
        self.step_i = 0; self.held = [False] * N_SUBOBJ; self.prev_alive = N_SF; self.qrf_sent = False
        if self.verbose: print("[reset] east=%d west=%d | objectif=(%d,%d) %d sous-objectifs | insertion=(%d,%d)" % (ec, wc, ox, oy, N_SUBOBJ, ix, iy), flush=True)
        st = self._state()
        return self._pack(st)

    def _state(self):
        sqf = ('private _sf = HMT_SF_arr apply {[round((getposatl _x) select 0), round((getposatl _x) select 1), [0,1] select (alive _x)]}; '
               'private _ea = allUnits select {side _x==east && alive _x}; '
               'private _df = _ea apply {[round((getposatl _x) select 0), round((getposatl _x) select 1)]}; '
               'private _k = 0; { private _e = _x; { _k = _k max (_e knowsAbout _x) } forEach HMT_SF_arr } forEach _ea; '
               'diag_log format ["HARMATTAN_STATE %1|%2|%3", _sf, _df, round(_k*10)/10];')
        raw = self._q(sqf, "STATE")
        if raw is None: return None
        p = raw.split("|")
        sf = self._parse_arr(p[0]) if len(p) > 0 else []
        df = self._parse_arr(p[1]) if len(p) > 1 else []
        try: al = float(p[2])
        except Exception: al = 0.0
        return sf, df, al

    def _update_held(self, sf, df):
        for i, (sx, sy) in enumerate(self.subobj):
            sf_near = any(a[2] == 1 and math.hypot(a[0] - sx, a[1] - sy) < R_HOLD for a in sf)
            df_near = any(math.hypot(d[0] - sx, d[1] - sy) < R_HOLD for d in df)
            if sf_near and not df_near: self.held[i] = True      # raid : une fois pris, tenu

    def _pack(self, st):
        """obs structuree (brique 0 : dict ; brique 2 = tenseur par agent)."""
        if st is None: return None
        sf, df, al = st
        return {"sf": sf, "def": df, "alert": al, "held": list(self.held),
                "n_alive": sum(a[2] for a in sf), "subobj": self.subobj}

    POSTURE = {0: ("UP", "FULL"), 1: ("MIDDLE", "NORMAL"), 2: ("DOWN", "LIMITED")}   # debout/rapide, accroupi, couche/couvert
    def step(self, actions):
        # actions : liste de N_SF (=(x,y), posture_idx) -> destination + posture (exposition/feu)
        cmds = []
        for i, (t, p) in enumerate(actions):
            pos, spd = self.POSTURE.get(int(p), ("MIDDLE", "NORMAL"))
            cmds.append('private _u = HMT_SF_arr select %d; _u setUnitPos "%s"; _u setSpeedMode "%s"; _u setCombatMode "RED"; _u doMove [%d,%d]'
                        % (i, pos, spd, int(t[0]), int(t[1])))
        self.b.send("[] spawn { " + "; ".join(cmds) + "; };", timeout=20)
        time.sleep(DT)
        st = self._state()
        self.step_i += 1
        if st is None: return None, 0.0, True, {"error": "state none", "result": "ERREUR"}
        sf, df, al = st
        # defense reactive : la QRF part au 1er contact serieux
        n_alive = sum(a[2] for a in sf)
        if al > 1.0 and not self.qrf_sent and n_alive > 0:
            cx = sum(a[0] for a in sf if a[2]) / n_alive; cy = sum(a[1] for a in sf if a[2]) / n_alive
            self.b.send('[] spawn { { _x doMove [%d,%d] } forEach (units HMT_QRF); HMT_QRF setBehaviour "COMBAT"; HMT_QRF setCombatMode "RED"; };' % (cx, cy))
            self.qrf_sent = True
        prev = sum(self.held); self._update_held(sf, df); now = sum(self.held)
        lost = max(0, self.prev_alive - n_alive); self.prev_alive = n_alive
        r = 10.0 * (now - prev) - 0.1 - 5.0 * lost           # +prise, -temps(audace), -pertes
        done = False; info = {"held": now, "alive": n_alive, "alert": al, "def": len(df), "qrf": self.qrf_sent}
        if now >= N_SUBOBJ: r += 100.0; done = True; info["result"] = "VICTOIRE"
        elif n_alive <= 0: r -= 50.0; done = True; info["result"] = "ANEANTI"
        elif self.step_i >= MAX_STEPS: done = True; info["result"] = "TEMPS"
        return self._pack(st), r, done, info

    def close(self):
        self._sh("pkill -9 -f 'profiles%d'" % self.slot)
