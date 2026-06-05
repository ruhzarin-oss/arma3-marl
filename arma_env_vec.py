"""ArmaVecEnv (V2 — tache MAITRISEE, multi-serveurs ready) — N escouades en parallele dans UN serveur Arma.
3 OPFOR LETAUX STATIQUES gardant l'objectif ; obs 10 dont menace (dir + proximite du plus proche OPFOR).
BLUFOR manoeuvre seule (riposte off ; deplacement pilote par la politique via setPosATL).
Accepte mission/log pour cibler un serveur precis (pont par instance) -> agrege par MultiArmaEnv.
Recompense = +1 securise, -0.01/pas, + shaping vers l'objectif (cout=pertes gere par le trainer)."""
import time, re
import numpy as np
from arma_bridge import ArmaBridge


class ArmaVecEnv:
    def __init__(self, num_envs=24, n=4, opfor=3, move=15, step_wait=0.7, settle=0.6,
                 cols=8, spacing=320, base=(15400, 16200), obj_dist=150,
                 secure_r=26, secure_n=3, max_steps=22, acc=4.0, dmg_dead=0.7,
                 spawn_settle=5.0, beta=1.0, threat_range=90.0, opf_skill=0.5,
                 mission=None, log=None, seed=0):
        self.b = ArmaBridge(mission=mission, log=log)
        self.N = int(num_envs); self.A = int(n); self.K = int(opfor)
        self.move = move; self.step_wait = step_wait; self.settle = settle
        self.cols = cols; self.spacing = spacing; self.base = base
        self.obj_dist = obj_dist; self.secure_r = secure_r; self.secure_n = secure_n
        self.max_steps = max_steps; self.acc = acc; self.dmg_dead = dmg_dead
        self.spawn_settle = spawn_settle; self.beta = beta
        self.threat_range = float(threat_range); self.opf_skill = opf_skill
        self.n_actions = 5; self.obs_dim = 10; self.scale = float(obj_dist)
        self.rng = np.random.default_rng(seed)
        self.cells = []
        for z in range(self.N):
            gx = base[0] + (z % cols) * spacing
            gy = base[1] + (z // cols) * spacing
            self.cells.append((int(gx), int(gy)))
        self.startx = np.zeros((self.N, self.A)); self.starty = np.zeros((self.N, self.A))
        self.objx = np.zeros(self.N); self.objy = np.zeros(self.N)
        self.opfx = np.zeros((self.N, self.K)); self.opfy = np.zeros((self.N, self.K))
        self.px = np.zeros((self.N, self.A)); self.py = np.zeros((self.N, self.A))
        self.alive = np.ones((self.N, self.A), dtype=bool)
        self.t = np.zeros(self.N, dtype=int)
        self.prev_alive = np.full(self.N, self.A, dtype=int)
        self.secured = np.zeros(self.N, dtype=bool)
        self.prev_d = np.zeros(self.N)

    def _query(self, sqf, settle=None):
        settle = self.settle if settle is None else settle
        nb = self.b.send(sqf, wait=True); time.sleep(settle)
        lines = self.b._log_lines()
        idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % nb) in ln)
        return [ln for ln in lines[idx:] if ("HARMATTAN_RECV cmd %d" % (nb + 1)) not in ln]

    def _spawn_sqf(self):
        cells = "[" + ",".join("[%d,%d]" % (x, y) for (x, y) in self.cells) + "]"
        head = ("{deleteVehicle _x} forEach allUnits; HMT_AG=[]; HMT_OP=[]; HMT_OBJ=[];\n"
                "private _A=%d; private _K=%d; private _od=%d; private _sk=%.2f;\n"
                "private _cells=%s;\n" % (self.A, self.K, self.obj_dist, self.opf_skill, cells))
        body = r'''{
  private _z=_forEachIndex; private _c=_x;
  private _b=[_c,0,80,6,0,0.6,0] call BIS_fnc_findSafePos; if (count _b < 2) then {_b=_c};
  private _o0=[(_b#0)+_od,(_b#1),0];
  private _o=[_o0,0,70,6,0,0.6,0] call BIS_fnc_findSafePos; if (count _o < 2) then {_o=_o0};
  HMT_OBJ set [_z,[round (_o#0), round (_o#1)]];
  private _gw=createGroup west;
  for "_a" from 0 to (_A-1) do {
    private _sp=[(_b#0)+(_a mod 2)*5-2,(_b#1)+(floor(_a/2))*5-2,0];
    _gw createUnit ["B_Soldier_F",_sp,[],0,"NONE"];
    private _u=(units _gw) select ((count (units _gw))-1);
    _u disableAI "AUTOTARGET"; _u disableAI "MOVE"; _u setBehaviour "AWARE"; _u setUnitPos "MIDDLE"; _u allowFleeing 0;
    _u addEventHandler ["HandleDamage", { (_this select 2) min 0.85 }];
    HMT_AG pushBack _u;
  };
  private _ge=createGroup east;
  for "_k" from 0 to (_K-1) do {
    _ge createUnit ["O_Soldier_F",[(_o#0)-28+(_k-1)*8,(_o#1)+(_k-1)*16,0],[],0,"NONE"];
    private _e=(units _ge) select ((count (units _ge))-1);
    _e setBehaviour "COMBAT"; _e disableAI "MOVE"; _e setUnitPos "MIDDLE";
    _e setSkill ["aimingAccuracy",_sk]; _e setSkill ["aimingSpeed",_sk]; _e setSkill ["spotDistance",0.85]; _e setSkill ["spotTime",0.85];
    _e addEventHandler ["HandleDamage", { (_this select 2) min 0.85 }];
    HMT_OP pushBack _e;
  };
} forEach _cells;
'''
        tail = ('setAccTime %.1f;\ndiag_log "HARMATTAN_VRESET";\n' % self.acc)
        return head + body + tail

    def _dump_obj_sqf(self):
        return ('{ private _o=HMT_OBJ select _forEachIndex; '
                'diag_log format ["HARMATTAN_OBJ %1 %2 %3", _forEachIndex, _o#0, _o#1]; } forEach HMT_OBJ;\n')

    def _dump_op_sqf(self):
        return ('{ private _u=HMT_OP select _forEachIndex; private _p = if (isNull _u) then {[0,0]} else {getPosATL _u}; '
                'diag_log format ["HARMATTAN_OP %1 %2 %3", _forEachIndex, round (_p#0), round (_p#1)]; } forEach HMT_OP;\n')

    def _dump_ag_sqf(self):
        return ('{ private _u=HMT_AG select _forEachIndex; '
                'private _p = if (isNull _u) then {[0,0]} else {getPosATL _u}; '
                'private _dm = if (isNull _u) then {100} else {round ((getDammage _u)*100)}; '
                'diag_log format ["HARMATTAN_AG %1 %2 %3 %4", _forEachIndex, round (_p#0), round (_p#1), _dm]; } forEach HMT_AG;\n')

    def _read(self):
        lines = self._query(self._dump_ag_sqf())
        G = self.N * self.A
        px = np.zeros(G); py = np.zeros(G); dm = np.full(G, 100.0); seen = np.zeros(G, dtype=bool)
        for ln in lines:
            m = re.search(r"HARMATTAN_AG (\d+) (-?\d+) (-?\d+) (\d+)", ln)
            if m:
                g = int(m.group(1))
                if 0 <= g < G:
                    px[g] = int(m.group(2)); py[g] = int(m.group(3)); dm[g] = int(m.group(4)); seen[g] = True
        px = px.reshape(self.N, self.A); py = py.reshape(self.N, self.A)
        dm = dm.reshape(self.N, self.A); seen = seen.reshape(self.N, self.A)
        self.px = np.where(seen, px, self.px); self.py = np.where(seen, py, self.py)
        self.alive = np.where(seen, dm < self.dmg_dead * 100, self.alive)

    def _read_op(self):
        Go = self.N * self.K
        ox = np.zeros(Go); oy = np.zeros(Go)
        for ln in self._query(self._dump_op_sqf()):
            m = re.search(r"HARMATTAN_OP (\d+) (-?\d+) (-?\d+)", ln)
            if m:
                g = int(m.group(1))
                if 0 <= g < Go:
                    ox[g] = int(m.group(2)); oy[g] = int(m.group(3))
        self.opfx = ox.reshape(self.N, self.K); self.opfy = oy.reshape(self.N, self.K)

    def _mean_dist(self):
        d = np.sqrt((self.px - self.objx[:, None]) ** 2 + (self.py - self.objy[:, None]) ** 2) / self.scale
        al = self.alive.astype(float); den = al.sum(1)
        return np.where(den > 0, (d * al).sum(1) / np.maximum(den, 1), 0.0)

    def reset(self):
        self.b.send(self._spawn_sqf(), wait=True)
        time.sleep(self.spawn_settle)
        for ln in self._query(self._dump_obj_sqf()):
            m = re.search(r"HARMATTAN_OBJ (\d+) (-?\d+) (-?\d+)", ln)
            if m:
                z = int(m.group(1))
                if 0 <= z < self.N:
                    self.objx[z] = int(m.group(2)); self.objy[z] = int(m.group(3))
        self._read_op()
        self._read()
        self.startx = self.px.copy(); self.starty = self.py.copy()
        self.t = self.rng.integers(0, self.max_steps, self.N)
        self.prev_alive = self.alive.sum(1).astype(int)
        self.secured = np.zeros(self.N, dtype=bool)
        self.prev_d = self._mean_dist()
        return self._obs()

    def _obs(self):
        S = self.scale
        basex = self.startx.mean(1, keepdims=True); basey = self.starty.mean(1, keepdims=True)
        ox = (self.px - basex) / S; oy = (self.py - basey) / S
        dgx = (self.objx[:, None] - self.px) / S; dgy = (self.objy[:, None] - self.py) / S
        al = self.alive.astype(float)
        PX = self.px; PY = self.py
        dx = PX[:, None, :] - PX[:, :, None]; dy = PY[:, None, :] - PY[:, :, None]
        d2m = np.where(np.eye(self.A, dtype=bool)[None] | np.broadcast_to((~self.alive)[:, None, :], (self.N, self.A, self.A)),
                       1e18, dx * dx + dy * dy)
        jmin = d2m.argmin(2)
        mdx = np.take_along_axis(dx, jmin[:, :, None], 2)[:, :, 0] / S
        mdy = np.take_along_axis(dy, jmin[:, :, None], 2)[:, :, 0] / S
        mdx[d2m.min(2) >= 1e18] = 0.0; mdy[d2m.min(2) >= 1e18] = 0.0
        tx = self.opfx[:, None, :] - PX[:, :, None]; ty = self.opfy[:, None, :] - PY[:, :, None]
        td2 = tx * tx + ty * ty
        kmin = td2.argmin(2)
        nox = np.take_along_axis(tx, kmin[:, :, None], 2)[:, :, 0] / S
        noy = np.take_along_axis(ty, kmin[:, :, None], 2)[:, :, 0] / S
        tprox = np.clip(1.0 - np.sqrt(td2.min(2)) / self.threat_range, 0.0, 1.0)
        return np.stack([ox, oy, dgx, dgy, al, mdx, mdy, nox, noy, tprox], axis=2).astype(np.float32)

    def step(self, actions):
        a = np.asarray(actions).reshape(self.N, self.A).astype(int)
        acts = "[" + ",".join(str(int(v)) for v in a.reshape(-1)) + "]"
        move = ('private _A=%s; { private _u=HMT_AG select _forEachIndex; '
                'if (!isNull _u && {(getDammage _u)<%.2f}) then { '
                'private _d=[[0,0],[0,1],[0,-1],[1,0],[-1,0]] select (_A select _forEachIndex); '
                'private _p=getPosATL _u; _u setPosATL [(_p#0)+(_d#0)*%d,(_p#1)+(_d#1)*%d,0]; }; } forEach HMT_AG;'
                % (acts, self.dmg_dead, self.move, self.move))
        self.b.send(move, wait=True)
        time.sleep(self.step_wait)
        self._read()
        n_alive = self.alive.sum(1)
        d2 = (self.px - self.objx[:, None]) ** 2 + (self.py - self.objy[:, None]) ** 2
        in_obj = ((d2 <= self.secure_r ** 2) & self.alive).sum(1)
        secured = in_obj >= self.secure_n
        newly = secured & (~self.secured)
        cost = np.maximum(0, self.prev_alive - n_alive).astype(np.float32)
        self.t = self.t + 1
        done = secured | (self.t >= self.max_steps) | (n_alive == 0)
        cur_d = self._mean_dist(); shaping = self.beta * (self.prev_d - cur_d); self.prev_d = cur_d
        rew = (newly.astype(np.float32) * 1.0) - 0.01 + shaping.astype(np.float32)
        self.secured = secured.copy(); self.prev_alive = n_alive.astype(int)
        info = {"success": secured.copy(), "in_obj": in_obj.copy(), "alive": n_alive.copy()}
        dz = np.where(done)[0]
        if len(dz) > 0:
            self._reset_zones(dz)
        return self._obs(), rew, cost, done.astype(np.float32), info

    def _reset_zones(self, dz):
        cmds = []
        for z in dz:
            z = int(z)
            for a in range(self.A):
                g = z * self.A + a
                cmds.append('private _u=HMT_AG select %d; if (!isNull _u) then {_u setDamage 0; _u setPosATL [%d,%d,0];};'
                            % (g, int(self.startx[z, a]), int(self.starty[z, a])))
            for k in range(self.K):
                gk = z * self.K + k
                cmds.append('private _e=HMT_OP select %d; if (!isNull _e) then {_e setDamage 0;};' % gk)
        self.b.send("\n".join(cmds), wait=True)
        self.px[dz] = self.startx[dz]; self.py[dz] = self.starty[dz]
        self.alive[dz] = True; self.t[dz] = 0; self.prev_alive[dz] = self.A; self.secured[dz] = False
        sd = np.sqrt((self.startx[dz] - self.objx[dz, None]) ** 2 + (self.starty[dz] - self.objy[dz, None]) ** 2) / self.scale
        self.prev_d[dz] = sd.mean(1)
