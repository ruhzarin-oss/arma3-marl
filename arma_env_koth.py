"""ÉTAPE C.1 — ArmaEnvKoth : TROIS factions d'agents dans le VRAI Arma (BLUFOR/OPFOR/Indépendant), à 120 deg
autour d'une zone centrale. Combat = vraie balistique Arma (macro-actions via le pont). CAPTURE PAR PRÉSENCE
(la barre n'avance que si une faction DOMINE la zone -> il faut dégager les autres) + AO qui TOURNE (anti-symétrie).
Étend arma_env_selfplay.py de 2 à 3 camps. step(a0,a1,a2). obs/camp=10 (ennemi = union des 2 autres), calée sur toy_koth3.
4 macros : 0=HOLD, 1=AVANCER, 2=SUPPRESSER (ennemi proche, toutes factions), 3=COUVERT."""
import time, re
import numpy as np
from arma_bridge import ArmaBridge

SIDES = [("HMT_BLU", "west", "B_Soldier_F"), ("HMT_OPF", "east", "O_Soldier_F"), ("HMT_IND", "resistance", "I_Soldier_F")]


class ArmaEnvKoth:
    def __init__(self, num_envs=8, n=3, move=20.0, step_wait=2.4, settle=0.6, cols=4, spacing=560,
                 base=(15000, 16000), obj_dist=140, secure_r=32, sup_range=120.0, sight=95.0,
                 max_steps=40, acc=4.0, dmg_dead=0.7, skill=0.5, beta=0.25, spawn_settle=6.0,
                 cap_need=4, rot_period=12, rot_jit=70, mission=None, log=None, seed=0):
        self.b = ArmaBridge(mission=mission, log=log)
        self.N = int(num_envs); self.A = int(n); self.C = 3
        self.move = move; self.step_wait = step_wait; self.settle = settle
        self.cols = cols; self.spacing = spacing; self.base = base; self.obj_dist = obj_dist
        self.secure_r = secure_r; self.sup_range = sup_range; self.sight = sight
        self.max_steps = max_steps; self.acc = acc; self.dmg_dead = dmg_dead; self.skill = skill
        self.beta = beta; self.spawn_settle = spawn_settle
        self.cap_need = cap_need; self.rot_period = rot_period; self.rot_jit = rot_jit
        self.n_actions = 4; self.obs_dim = 10; self.scale = float(obj_dist)
        self.rng = np.random.default_rng(seed)
        self.cells = [(int(base[0] + (z % cols) * spacing), int(base[1] + (z // cols) * spacing)) for z in range(self.N)]
        self.objx = np.zeros(self.N); self.objy = np.zeros(self.N); self.cx = np.zeros(self.N); self.cy = np.zeros(self.N)
        self.px = np.zeros((self.C, self.N, self.A)); self.py = np.zeros((self.C, self.N, self.A)); self.dmg = np.full((self.C, self.N, self.A), 100.0)
        self.startx = np.zeros((self.C, self.N, self.A)); self.starty = np.zeros((self.C, self.N, self.A))
        self.supp = np.zeros((self.C, self.N, self.A))
        self.t = np.zeros(self.N, dtype=int); self.ctrl_time = np.zeros((self.C, self.N)); self.prev_d = np.zeros((self.C, self.N))
        self.cap_prog = np.zeros(self.N); self.cap_owner = np.full(self.N, -1)
        self.GRP = [s[0] for s in SIDES]

    def _others(self, s): return [c for c in range(self.C) if c != s]

    def _query(self, sqf, settle=None):
        settle = self.settle if settle is None else settle
        nb = self.b.send(sqf, wait=True); time.sleep(settle)
        lines = self.b._log_lines()
        idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % nb) in ln)
        return [ln for ln in lines[idx:] if ("HARMATTAN_RECV cmd %d" % (nb + 1)) not in ln]

    def _spawn_sqf(self):
        cells = "[" + ",".join("[%d,%d]" % (x, y) for (x, y) in self.cells) + "]"
        decl = "; ".join("%s=[]" % g for g in self.GRP)
        head = ("{ if (!(isPlayer _x)) then {deleteVehicle _x} } forEach allUnits; %s; HMT_OBJ=[];\n"
                "west setFriend [east,0]; west setFriend [resistance,0]; east setFriend [west,0]; east setFriend [resistance,0]; resistance setFriend [west,0]; resistance setFriend [east,0];\n"
                "private _A=%d; private _od=%d; private _sk=%.2f;\n"
                "private _cells=%s;\n" % (decl, self.A, self.obj_dist, self.skill, cells))
        body = (r'''{
  private _z=_forEachIndex; private _c=_x;
  private _o=[_c,0,80,8,0,0.6,0] call BIS_fnc_findSafePos; if (count _o < 2) then {_o=_c};
  HMT_OBJ set [_z,[round (_o#0), round (_o#1)]];
  private _grps=[createGroup west, createGroup east, createGroup resistance];
  private _types=["B_Soldier_F","O_Soldier_F","I_Soldier_F"];
  private _camps=[HMT_BLU,HMT_OPF,HMT_IND];
  {
    private _ci=_forEachIndex; private _g=_x; private _ty=_types select _ci; private _ang=90+120*_ci;
    private _r = 4 + _A*0.6;
    for "_a" from 0 to (_A-1) do {
      private _bx=(_o#0)+_od*(cos _ang)+_r*(cos (360*_a/_A)); private _by=(_o#1)+_od*(sin _ang)+_r*(sin (360*_a/_A));
      _g createUnit [_ty,[_bx,_by,0],[],0,"FORM"];
      private _u=(units _g) select ((count (units _g))-1);
      _u setBehaviour "COMBAT"; _u setUnitPos "AUTO"; _u setSkill _sk; _u allowFleeing 0;
      _u addEventHandler ["HandleDamage",{ (_this select 2) min 0.85 }];
      (_camps select _ci) pushBack _u;
    };
  } forEach _grps;
} forEach _cells;
''')
        tail = ('setAccTime %.1f;\ndiag_log "HARMATTAN_VRESET";\n' % self.acc)
        return head + body + tail

    def _dump_sqf(self):
        out = '{ private _o=HMT_OBJ select _forEachIndex; diag_log format ["HARMATTAN_OBJ %1 %2 %3", _forEachIndex, _o#0, _o#1]; } forEach HMT_OBJ;\n'
        for (grp, _, _) in SIDES:
            tag = grp[4:]
            out += ('{ private _u=%s select _forEachIndex; private _p = if (isNull _u) then {[0,0]} else {getPosATL _u}; '
                    'private _dm = if (isNull _u) then {100} else {round ((getDammage _u)*100)}; '
                    'diag_log format ["HARMATTAN_%s %%1 %%2 %%3 %%4", _forEachIndex, round (_p#0), round (_p#1), _dm]; } forEach %s;\n' % (grp, tag, grp))
        return out

    def _read(self):
        lines = self._query(self._dump_sqf())
        for ln in lines:
            m = re.search(r"HARMATTAN_OBJ (\d+) (-?\d+) (-?\d+)", ln)
            if m:
                z = int(m.group(1))
                if 0 <= z < self.N: self.objx[z] = int(m.group(2)); self.objy[z] = int(m.group(3))
        for c, (grp, _, _) in enumerate(SIDES):
            tag = grp[4:]; G = self.N * self.A
            px = self.px[c].reshape(-1).copy(); py = self.py[c].reshape(-1).copy(); dm = self.dmg[c].reshape(-1).copy()
            for ln in lines:
                mm = re.search(r"HARMATTAN_%s (\d+) (-?\d+) (-?\d+) (\d+)" % tag, ln)
                if mm:
                    g = int(mm.group(1))
                    if 0 <= g < G: px[g] = int(mm.group(2)); py[g] = int(mm.group(3)); dm[g] = int(mm.group(4))
            self.px[c] = px.reshape(self.N, self.A); self.py[c] = py.reshape(self.N, self.A); self.dmg[c] = dm.reshape(self.N, self.A)

    def _alive(self, c): return self.dmg[c] < self.dmg_dead * 100

    def _mean_dist(self, c):
        d = np.sqrt((self.px[c] - self.objx[:, None]) ** 2 + (self.py[c] - self.objy[:, None]) ** 2) / self.scale
        al = self._alive(c).astype(float); den = al.sum(1)
        return np.where(den > 0, (d * al).sum(1) / np.maximum(den, 1), 0.0)

    def reset(self):
        self.b.send(self._spawn_sqf(), wait=True); time.sleep(self.spawn_settle)
        self._read()
        self.startx = self.px.copy(); self.starty = self.py.copy()
        self.cx = self.objx.copy(); self.cy = self.objy.copy()
        self.t = self.rng.integers(0, self.max_steps, self.N)
        self.supp[:] = 0.0; self.ctrl_time[:] = 0.0; self.cap_prog[:] = 0.0; self.cap_owner[:] = -1
        for c in range(self.C): self.prev_d[c] = self._mean_dist(c)
        return tuple(self._obs(c) for c in range(self.C))

    def _obs(self, s):
        S = self.scale; al = self._alive(s); others = self._others(s)
        ox = (self.px[s] - self.objx[:, None]) / S; oy = (self.py[s] - self.objy[:, None]) / S
        dgx = (self.objx[:, None] - self.px[s]) / S; dgy = (self.objy[:, None] - self.py[s]) / S
        dx = self.px[s][:, None, :] - self.px[s][:, :, None]; dy = self.py[s][:, None, :] - self.py[s][:, :, None]
        d2 = np.where(np.eye(self.A, dtype=bool)[None] | np.broadcast_to((~al)[:, None, :], (self.N, self.A, self.A)), 1e18, dx * dx + dy * dy)
        jm = d2.argmin(2)
        adx = np.take_along_axis(dx, jm[:, :, None], 2)[:, :, 0] / S; ady = np.take_along_axis(dy, jm[:, :, None], 2)[:, :, 0] / S
        nm = d2.min(2) >= 1e18; adx[nm] = 0.0; ady[nm] = 0.0
        epx = np.concatenate([self.px[o] for o in others], 1); epy = np.concatenate([self.py[o] for o in others], 1)
        eal = np.concatenate([self._alive(o) for o in others], 1); esp = np.concatenate([self.supp[o] for o in others], 1)
        ex = epx[:, None, :] - self.px[s][:, :, None]; ey = epy[:, None, :] - self.py[s][:, :, None]
        ed2 = np.where(eal[:, None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(2)
        edx = np.take_along_axis(ex, km[:, :, None], 2)[:, :, 0]; edy = np.take_along_axis(ey, km[:, :, None], 2)[:, :, 0]
        nd = np.sqrt(ed2.min(2)); seen = (nd <= self.sight) & (ed2.min(2) < 1e18)
        edx = (edx / S) * seen; edy = (edy / S) * seen
        esupp = np.take_along_axis(esp, km, 1)
        return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), adx, ady, edx, edy, esupp], axis=2).astype(np.float32)

    def _macro_cmds(self, s, a):
        grp = self.GRP[s]; al = self._alive(s); others = self._others(s)
        epx = np.concatenate([self.px[o] for o in others], 1); epy = np.concatenate([self.py[o] for o in others], 1)
        eal = np.concatenate([self._alive(o) for o in others], 1)
        oloc = np.concatenate([np.full(self.A, o) for o in others]); oidx = np.concatenate([np.arange(self.A) for _ in others])
        sa = (a == 2) & al
        sx = epx[:, :, None] - self.px[s][:, None, :]; sy = epy[:, :, None] - self.py[s][:, None, :]
        within = ((sx * sx + sy * sy) <= self.sup_range ** 2) & sa[:, None, :] & eal[:, :, None]
        # marquer la suppression sur la bonne faction adverse
        supp_un = within.any(2)  # (N, A*(C-1)) ennemis supprimes
        for j, o in enumerate(others):
            self.supp[o] = supp_un[:, j * self.A:(j + 1) * self.A].astype(float)
        tox = self.objx[:, None] - self.px[s]; toy = self.objy[:, None] - self.py[s]; tn = np.sqrt(tox * tox + toy * toy) + 1e-6
        spd = np.zeros((self.N, self.A)); spd[a == 1] = self.move; spd[a == 3] = self.move * 0.5
        tgx = self.px[s] + (tox / tn) * spd; tgy = self.py[s] + (toy / tn) * spd
        ex = epx[:, None, :] - self.px[s][:, :, None]; ey = epy[:, None, :] - self.py[s][:, :, None]
        km = np.where(eal[:, None, :], ex * ex + ey * ey, 1e18).argmin(2)
        cmds = []
        for z in range(self.N):
            for i in range(self.A):
                g = z * self.A + i; m = int(a[z, i])
                if m == 0:
                    cmds.append('private _u=%s select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "MIDDLE";};' % (grp, g))
                elif m == 2:
                    k = int(km[z, i]); eg = self.GRP[int(oloc[k])]; ei = z * self.A + int(oidx[k])
                    cmds.append('private _u=%s select %d; private _e=%s select %d; if (!isNull _u && {alive _u} && {!isNull _e}) then {doStop _u; _u setUnitPos "UP"; _u doTarget _e; _u doFire _e;};' % (grp, g, eg, ei))
                else:
                    pos = "DOWN" if m == 3 else "MIDDLE"
                    cmds.append('private _u=%s select %d; if (!isNull _u && {alive _u}) then {_u setUnitPos "%s"; _u doMove [%d,%d,0];};' % (grp, g, pos, int(tgx[z, i]), int(tgy[z, i])))
        return cmds

    def step(self, a0, a1, a2):
        self.supp[:] = 0.0
        acts = [np.asarray(x).reshape(self.N, self.A).astype(int) for x in (a0, a1, a2)]
        cmds = []
        for c in range(self.C):
            cmds += self._macro_cmds(c, acts[c])
        for c in range(self.C):
            for z in range(self.N):
                for k in range(self.A):
                    if self.supp[c][z, k] > 0.5:
                        cmds.append('private _e=%s select %d; if (!isNull _e) then {_e suppressFor 2.5;};' % (self.GRP[c], z * self.A + k))
        self.b.send("\n".join(cmds), wait=True); time.sleep(self.step_wait)
        self._read()
        self.t = self.t + 1
        # rotation de l'AO (cote Python : on deplace l'objectif vise)
        rot = (self.t % self.rot_period) == 0
        if rot.any():
            jx = self.rng.uniform(-self.rot_jit, self.rot_jit, self.N); jy = self.rng.uniform(-self.rot_jit, self.rot_jit, self.N)
            self.objx = np.where(rot, np.clip(self.cx + jx, self.cx - self.rot_jit, self.cx + self.rot_jit), self.objx)
            self.objy = np.where(rot, np.clip(self.cy + jy, self.cy - self.rot_jit, self.cy + self.rot_jit), self.objy)
            self.cap_prog = np.where(rot, 0.0, self.cap_prog); self.cap_owner = np.where(rot, -1, self.cap_owner)
        inobj = []
        for c in range(self.C):
            al = self._alive(c); d2 = (self.px[c] - self.objx[:, None]) ** 2 + (self.py[c] - self.objy[:, None]) ** 2
            inobj.append(((d2 <= self.secure_r ** 2) & al).sum(1)); self.ctrl_time[c] += inobj[c]
        io = np.stack(inobj)  # (C,N)
        mx = io.max(0); nmax = (io == mx).sum(0); dom = np.where((nmax == 1) & (mx >= 1), io.argmax(0), -1)
        same = (dom >= 0) & (dom == self.cap_owner); new = (dom >= 0) & (dom != self.cap_owner); none = (dom < 0)
        self.cap_prog = np.where(same, self.cap_prog + 1, self.cap_prog)
        self.cap_owner = np.where(new, dom, self.cap_owner); self.cap_prog = np.where(new, 1.0, self.cap_prog)
        self.cap_prog = np.where(none, np.maximum(0.0, self.cap_prog - 1), self.cap_prog)
        captured = self.cap_prog >= self.cap_need
        alive_c = np.stack([self._alive(c).any(1) for c in range(self.C)]); n_alive = alive_c.sum(0)
        timeout = self.t >= self.max_steps
        ct = self.ctrl_time; ctmx = ct.max(0); ctn = (ct == ctmx).sum(0)
        winner = np.full(self.N, -1)
        winner = np.where(captured, self.cap_owner, winner)
        winner = np.where((winner == -1) & (n_alive == 1), alive_c.astype(float).argmax(0), winner)
        winner = np.where((winner == -1) & timeout & (ctn == 1), ct.argmax(0), winner)
        decided = winner >= 0
        done = captured | timeout | (n_alive <= 1)
        rew = [np.zeros(self.N, np.float32) for _ in range(self.C)]
        mean_in = io.sum(0)
        for c in range(self.C):
            cur = self._mean_dist(c); sh = self.beta * (self.prev_d[c] - cur); self.prev_d[c] = cur
            others_in = (mean_in - inobj[c]) / max(1, self.C - 1); ctrl = 0.04 * (inobj[c] - others_in).astype(np.float32)
            wterm = np.where(winner == c, 1.0, np.where(decided, -0.5, 0.0)).astype(np.float32)
            rew[c] = sh - 0.005 + ctrl + wterm
        info = {"winner": winner.copy(), "decided": decided.copy(), "captured": captured.copy()}
        dz = np.where(done)[0]
        if len(dz) > 0: self._reset_zones(dz)
        return tuple(self._obs(c) for c in range(self.C)), tuple(rew), done.astype(np.float32), info

    def _reset_zones(self, dz):
        cmds = []
        for z in dz:
            z = int(z)
            for c in range(self.C):
                for i in range(self.A):
                    g = z * self.A + i
                    cmds.append('private _u=%s select %d; if (!isNull _u) then {_u setDamage 0; _u setPosATL [%d,%d,0]; doStop _u;};'
                                % (self.GRP[c], g, int(self.startx[c, z, i]), int(self.starty[c, z, i])))
        self.b.send("\n".join(cmds), wait=True)
        for c in range(self.C):
            self.px[c, dz] = self.startx[c, dz]; self.py[c, dz] = self.starty[c, dz]; self.dmg[c, dz] = 0.0
        self.objx[dz] = self.cx[dz]; self.objy[dz] = self.cy[dz]
        for c in range(self.C):
            self.prev_d[c][dz] = np.sqrt((self.startx[c, dz] - self.objx[dz, None]) ** 2 + (self.starty[c, dz] - self.objy[dz, None]) ** 2).mean(1) / self.scale
        self.supp[:, dz] = 0.0; self.ctrl_time[:, dz] = 0.0; self.cap_prog[dz] = 0.0; self.cap_owner[dz] = -1; self.t[dz] = 0
