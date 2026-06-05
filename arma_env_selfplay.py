"""③.3.1 — ArmaEnvSelfPlay : DEUX camps d'AGENTS dans Arma (BLUFOR vs OPFOR), tous deux pilotes par
macro-actions via le pont (combat = vraie balistique Arma). 4 macros : 0=HOLD, 1=AVANCER (doMove vers obj),
2=SUPPRESSER (doTarget+doFire ennemi proche + suppressFor), 3=COUVERT (DOWN + doMove lent).
obs/camp = 10 calee sur toy_selfplay. step(a0, a1) controle les deux camps. reward symetrique par controle cumule."""
import time, re
import numpy as np
from arma_bridge import ArmaBridge


class ArmaEnvSelfPlay:
    def __init__(self, num_envs=12, n=3, move=20.0, step_wait=2.4, settle=0.6, cols=4, spacing=520,
                 base=(15000, 16000), obj_dist=140, secure_r=32, secure_n=2, sup_range=120.0, sight=95.0,
                 max_steps=30, acc=4.0, dmg_dead=0.7, opf_skill=0.5, beta=0.25, spawn_settle=6.0,
                 mission=None, log=None, seed=0):
        self.b = ArmaBridge(mission=mission, log=log)
        self.N = int(num_envs); self.A = int(n)
        self.move = move; self.step_wait = step_wait; self.settle = settle
        self.cols = cols; self.spacing = spacing; self.base = base; self.obj_dist = obj_dist
        self.secure_r = secure_r; self.secure_n = secure_n; self.sup_range = sup_range; self.sight = sight
        self.max_steps = max_steps; self.acc = acc; self.dmg_dead = dmg_dead; self.opf_skill = opf_skill
        self.beta = beta; self.spawn_settle = spawn_settle
        self.n_actions = 4; self.obs_dim = 10; self.scale = float(obj_dist)
        self.rng = np.random.default_rng(seed)
        self.cells = [(int(base[0] + (z % cols) * spacing), int(base[1] + (z // cols) * spacing)) for z in range(self.N)]
        self.objx = np.zeros(self.N); self.objy = np.zeros(self.N)
        self.px = np.zeros((2, self.N, self.A)); self.py = np.zeros((2, self.N, self.A)); self.dmg = np.full((2, self.N, self.A), 100.0)
        self.startx = np.zeros((2, self.N, self.A)); self.starty = np.zeros((2, self.N, self.A))
        self.supp = np.zeros((2, self.N, self.A))
        self.t = np.zeros(self.N, dtype=int); self.ctrl_time = np.zeros((2, self.N)); self.prev_d = np.zeros((2, self.N))
        self.GRP = ["HMT_BLU", "HMT_OPF"]

    def _query(self, sqf, settle=None):
        settle = self.settle if settle is None else settle
        nb = self.b.send(sqf, wait=True); time.sleep(settle)
        lines = self.b._log_lines()
        idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % nb) in ln)
        return [ln for ln in lines[idx:] if ("HARMATTAN_RECV cmd %d" % (nb + 1)) not in ln]

    def _spawn_sqf(self):
        cells = "[" + ",".join("[%d,%d]" % (x, y) for (x, y) in self.cells) + "]"
        head = ("{deleteVehicle _x} forEach allUnits; HMT_BLU=[]; HMT_OPF=[]; HMT_OBJ=[];\n"
                "private _A=%d; private _od=%d; private _sk=%.2f;\n"
                "private _cells=%s;\n" % (self.A, self.obj_dist, self.opf_skill, cells))
        body = r'''{
  private _z=_forEachIndex; private _c=_x;
  private _o=[_c,0,60,8,0,0.5,0] call BIS_fnc_findSafePos; if (count _o < 2) then {_o=_c};
  HMT_OBJ set [_z,[round (_o#0), round (_o#1)]];
  private _gb=createGroup west; private _ge=createGroup east;
  for "_a" from 0 to (_A-1) do {
    private _sb=[(_o#0)-_od+(_a*7)-7,(_o#1)+(_a-1)*8,0];
    _gb createUnit ["B_Soldier_F",_sb,[],0,"FORM"];
    private _ub=(units _gb) select ((count (units _gb))-1);
    _ub setBehaviour "COMBAT"; _ub setUnitPos "AUTO"; _ub setSkill _sk; _ub allowFleeing 0;
    _ub addEventHandler ["HandleDamage",{ (_this select 2) min 0.85 }];
    HMT_BLU pushBack _ub;
    private _se=[(_o#0)+_od-(_a*7)+7,(_o#1)+(_a-1)*8,0];
    _ge createUnit ["O_Soldier_F",_se,[],0,"FORM"];
    private _ue=(units _ge) select ((count (units _ge))-1);
    _ue setBehaviour "COMBAT"; _ue setUnitPos "AUTO"; _ue setSkill _sk; _ue allowFleeing 0;
    _ue addEventHandler ["HandleDamage",{ (_this select 2) min 0.85 }];
    HMT_OPF pushBack _ue;
  };
} forEach _cells;
'''
        tail = ('setAccTime %.1f;\ndiag_log "HARMATTAN_VRESET";\n' % self.acc)
        return head + body + tail

    def _dump_sqf(self):
        out = '{ private _o=HMT_OBJ select _forEachIndex; diag_log format ["HARMATTAN_OBJ %1 %2 %3", _forEachIndex, _o#0, _o#1]; } forEach HMT_OBJ;\n'
        for tag, grp in (("BLU", "HMT_BLU"), ("OPF", "HMT_OPF")):
            out += ('{ private _u=%s select _forEachIndex; private _p = if (isNull _u) then {[0,0]} else {getPosATL _u}; '
                    'private _dm = if (isNull _u) then {100} else {round ((getDammage _u)*100)}; '
                    'diag_log format ["HARMATTAN_%s %%1 %%2 %%3 %%4", _forEachIndex, round (_p#0), round (_p#1), _dm]; } forEach %s;\n' % (grp, tag, grp))
        return out

    def _read(self):
        lines = self._query(self._dump_sqf())
        for z in range(self.N):
            m = None
        # objectifs
        for ln in lines:
            m = re.search(r"HARMATTAN_OBJ (\d+) (-?\d+) (-?\d+)", ln)
            if m:
                z = int(m.group(1))
                if 0 <= z < self.N: self.objx[z] = int(m.group(2)); self.objy[z] = int(m.group(3))
        for s, tag in ((0, "BLU"), (1, "OPF")):
            G = self.N * self.A
            px = self.px[s].reshape(-1).copy(); py = self.py[s].reshape(-1).copy(); dm = self.dmg[s].reshape(-1).copy()
            for ln in lines:
                mm = re.search(r"HARMATTAN_%s (\d+) (-?\d+) (-?\d+) (\d+)" % tag, ln)
                if mm:
                    g = int(mm.group(1))
                    if 0 <= g < G: px[g] = int(mm.group(2)); py[g] = int(mm.group(3)); dm[g] = int(mm.group(4))
            self.px[s] = px.reshape(self.N, self.A); self.py[s] = py.reshape(self.N, self.A); self.dmg[s] = dm.reshape(self.N, self.A)

    def _alive(self, s): return self.dmg[s] < self.dmg_dead * 100

    def _mean_dist(self, s):
        d = np.sqrt((self.px[s] - self.objx[:, None]) ** 2 + (self.py[s] - self.objy[:, None]) ** 2) / self.scale
        al = self._alive(s).astype(float); den = al.sum(1)
        return np.where(den > 0, (d * al).sum(1) / np.maximum(den, 1), 0.0)

    def reset(self):
        self.b.send(self._spawn_sqf(), wait=True); time.sleep(self.spawn_settle)
        self._read()
        self.startx = self.px.copy(); self.starty = self.py.copy()
        self.t = self.rng.integers(0, self.max_steps, self.N)
        self.supp[:] = 0.0; self.ctrl_time[:] = 0.0
        for s in range(2): self.prev_d[s] = self._mean_dist(s)
        return self._obs(0), self._obs(1)

    def _obs(self, s):
        o = 1 - s; S = self.scale; al = self._alive(s)
        basex = self.startx[s].mean(1, keepdims=True); basey = self.starty[s].mean(1, keepdims=True)
        ox = (self.px[s] - basex) / S; oy = (self.py[s] - basey) / S
        dgx = (self.objx[:, None] - self.px[s]) / S; dgy = (self.objy[:, None] - self.py[s]) / S
        dx = self.px[s][:, None, :] - self.px[s][:, :, None]; dy = self.py[s][:, None, :] - self.py[s][:, :, None]
        d2 = np.where(np.eye(self.A, dtype=bool)[None] | np.broadcast_to((~al)[:, None, :], (self.N, self.A, self.A)), 1e18, dx * dx + dy * dy)
        jm = d2.argmin(2)
        adx = np.take_along_axis(dx, jm[:, :, None], 2)[:, :, 0] / S; ady = np.take_along_axis(dy, jm[:, :, None], 2)[:, :, 0] / S
        nm = d2.min(2) >= 1e18; adx[nm] = 0.0; ady[nm] = 0.0
        oal = self._alive(o)
        ex = self.px[o][:, None, :] - self.px[s][:, :, None]; ey = self.py[o][:, None, :] - self.py[s][:, :, None]
        ed2 = np.where(oal[:, None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(2)
        edx = np.take_along_axis(ex, km[:, :, None], 2)[:, :, 0]; edy = np.take_along_axis(ey, km[:, :, None], 2)[:, :, 0]
        nd = np.sqrt(ed2.min(2)); seen = (nd <= self.sight) & (ed2.min(2) < 1e18)
        edx = (edx / S) * seen; edy = (edy / S) * seen
        esupp = np.take_along_axis(self.supp[o], km, 1)
        return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), adx, ady, edx, edy, esupp], axis=2).astype(np.float32)

    def _macro_cmds(self, s, a):
        grp = self.GRP[s]; al = self._alive(s); o = 1 - s
        sa = (a == 2) & al
        sx = self.px[o][:, :, None] - self.px[s][:, None, :]; sy = self.py[o][:, :, None] - self.py[s][:, None, :]
        within = ((sx * sx + sy * sy) <= self.sup_range ** 2) & sa[:, None, :] & self._alive(o)[:, :, None]
        self.supp[o] = within.any(2).astype(float)
        tox = self.objx[:, None] - self.px[s]; toy = self.objy[:, None] - self.py[s]; tn = np.sqrt(tox * tox + toy * toy) + 1e-6
        spd = np.zeros((self.N, self.A)); spd[a == 1] = self.move; spd[a == 3] = self.move * 0.5
        tgx = self.px[s] + (tox / tn) * spd; tgy = self.py[s] + (toy / tn) * spd
        ex = self.px[o][:, None, :] - self.px[s][:, :, None]; ey = self.py[o][:, None, :] - self.py[s][:, :, None]
        km = np.where(self._alive(o)[:, None, :], ex * ex + ey * ey, 1e18).argmin(2)
        cmds = []
        for z in range(self.N):
            for i in range(self.A):
                g = z * self.A + i; m = int(a[z, i])
                if m == 0:
                    cmds.append('private _u=%s select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "MIDDLE";};' % (grp, g))
                elif m == 2:
                    gk = z * self.A + int(km[z, i])
                    cmds.append('private _u=%s select %d; private _e=%s select %d; if (!isNull _u && {alive _u} && {!isNull _e}) then {doStop _u; _u setUnitPos "UP"; _u doTarget _e; _u doFire _e;};' % (grp, g, self.GRP[o], gk))
                else:
                    pos = "DOWN" if m == 3 else "MIDDLE"
                    cmds.append('private _u=%s select %d; if (!isNull _u && {alive _u}) then {_u setUnitPos "%s"; _u doMove [%d,%d,0];};' % (grp, g, pos, int(tgx[z, i]), int(tgy[z, i])))
        return cmds

    def step(self, a0, a1):
        self.supp[:] = 0.0
        a0 = np.asarray(a0).reshape(self.N, self.A).astype(int); a1 = np.asarray(a1).reshape(self.N, self.A).astype(int)
        cmds = self._macro_cmds(0, a0) + self._macro_cmds(1, a1)
        for s in range(2):
            for z in range(self.N):
                for k in range(self.A):
                    if self.supp[s][z, k] > 0.5:
                        cmds.append('private _e=%s select %d; if (!isNull _e) then {_e suppressFor 2.5;};' % (self.GRP[s], z * self.A + k))
        self.b.send("\n".join(cmds), wait=True); time.sleep(self.step_wait)
        self._read()
        inobj = []
        for s in range(2):
            al = self._alive(s); d2 = (self.px[s] - self.objx[:, None]) ** 2 + (self.py[s] - self.objy[:, None]) ** 2
            inobj.append(((d2 <= self.secure_r ** 2) & al).sum(1))
        self.ctrl_time[0] += inobj[0]; self.ctrl_time[1] += inobj[1]
        sec0 = inobj[0] >= self.secure_n; sec1 = inobj[1] >= self.secure_n
        elim0 = ~self._alive(0).any(1); elim1 = ~self._alive(1).any(1); self.t = self.t + 1; timeout = self.t >= self.max_steps
        win0 = (sec0 & ~sec1) | elim1 | (timeout & (self.ctrl_time[0] > self.ctrl_time[1]))
        win1 = (sec1 & ~sec0) | elim0 | (timeout & (self.ctrl_time[1] > self.ctrl_time[0]))
        both = win0 & win1; win0 = win0 & ~both; win1 = win1 & ~both
        done = win0 | win1 | timeout | elim0 | elim1
        rew = [np.zeros(self.N, np.float32), np.zeros(self.N, np.float32)]
        for s in range(2):
            cur = self._mean_dist(s); sh = self.beta * (self.prev_d[s] - cur); self.prev_d[s] = cur
            rew[s] = sh - 0.005 + 0.04 * (inobj[s] - inobj[1 - s]).astype(np.float32)
        rew[0] = rew[0] + win0.astype(np.float32) - win1.astype(np.float32)
        rew[1] = rew[1] + win1.astype(np.float32) - win0.astype(np.float32)
        info = {"win0": win0.copy(), "win1": win1.copy(), "decided": (win0 | win1).copy()}
        dz = np.where(done)[0]
        if len(dz) > 0:
            self._reset_zones(dz)
        return self._obs(0), self._obs(1), rew[0], rew[1], done.astype(np.float32), info

    def _reset_zones(self, dz):
        cmds = []
        for z in dz:
            z = int(z)
            for s in range(2):
                for i in range(self.A):
                    g = z * self.A + i
                    cmds.append('private _u=%s select %d; if (!isNull _u) then {_u setDamage 0; _u setPosATL [%d,%d,0]; doStop _u;};'
                                % (self.GRP[s], g, int(self.startx[s, z, i]), int(self.starty[s, z, i])))
        self.b.send("\n".join(cmds), wait=True)
        for s in range(2):
            self.px[s, dz] = self.startx[s, dz]; self.py[s, dz] = self.starty[s, dz]; self.dmg[s, dz] = 0.0
            self.prev_d[s][dz] = np.sqrt((self.startx[s, dz] - self.objx[dz, None]) ** 2 + (self.starty[s, dz] - self.objy[dz, None]) ** 2).mean(1) / self.scale
        self.supp[:, dz] = 0.0; self.ctrl_time[:, dz] = 0.0; self.t[dz] = 0
