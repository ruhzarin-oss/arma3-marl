"""S4/S5 — ArmaSquadEnv : env RL au-dessus du pont. Squad BLUFOR + objectif + OPFOR.
reset(opfor=N) ; step(actions) -> doMove ; obs/agent 7d ; récompense=objectif, coût=pertes.
Enregistre self._squad / self._opfor (positions réelles) pour la capture carte."""
import time, re
from arma_bridge import ArmaBridge

class ArmaSquadEnv:
    def __init__(self, n=4, x0=1000, y0=1000, size=200, objx=1140, objy=1140,
                 move=12, step_wait=2.0, acc=6.0, max_steps=22, secure_r=22, secure_n=3, opfor=2):
        self.b = ArmaBridge(); self.n = n; self.x0, self.y0, self.size = x0, y0, size
        self.objx, self.objy = objx, objy; self.move = move; self.step_wait = step_wait; self.acc = acc
        self.max_steps = max_steps; self.secure_r = secure_r; self.secure_n = secure_n; self.opfor = opfor
        self.n_actions = 5; self.obs_dim = 7; self.t = 0; self.prev_alive = n; self.secured = False
        self._squad = []; self._opfor = []
    def _query(self, sqf, prefix, settle=0.5):
        nb = self.b.send(sqf, wait=True); time.sleep(settle)
        lines = self.b._log_lines()
        idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % nb) in ln)
        out = []
        for ln in lines[idx:]:
            if ("HARMATTAN_RECV cmd %d" % (nb + 1)) in ln: break
            if prefix in ln: out.append(ln)
        return out
    def reset(self):
        sqf = '{ deleteVehicle _x; } forEach allUnits;\nHMT_SQUAD = []; HMT_OPFOR = [];\nprivate _g = createGroup west;\n'
        for i in range(self.n):
            sx = self.x0 + (i % 2) * 6; sy = self.y0 + (i // 2) * 6
            sqf += 'HMT_SQUAD pushBack (_g createUnit ["B_Soldier_F",[%d,%d,0],[],0,"NONE"]);\n' % (sx, sy)
        sqf += '{ _x disableAI "AUTOTARGET"; _x setBehaviour "CARELESS"; _x setSpeedMode "FULL"; _x setUnitPos "UP"; _x allowFleeing 0; } forEach HMT_SQUAD;\n'
        if self.opfor > 0:
            sqf += 'private _o = createGroup east;\n'
            for j in range(self.opfor):
                ox = (self.x0 + self.objx) // 2 + j * 8 - 8; oy = (self.y0 + self.objy) // 2 + j * 4
                sqf += 'HMT_OPFOR pushBack (_o createUnit ["O_Soldier_F",[%d,%d,0],[],0,"NONE"]);\n' % (ox, oy)
            sqf += '{ _x setBehaviour "COMBAT"; _x setUnitPos "MIDDLE"; } forEach HMT_OPFOR;\n'
        sqf += 'diag_log "HARMATTAN_RESET";\n'
        self.b.send(sqf, wait=True); self.b.send('setAccTime %.1f;' % self.acc, wait=False)
        time.sleep(1.5); self.t = 0; self.prev_alive = self.n; self.secured = False
        self._read_all(); return self._obs_from(self._squad)
    def _parse(self, lines, prefix):
        d = {}
        for ln in lines:
            m = re.search(prefix + r" (\d+) (-?\d+) (-?\d+) (\d)", ln)
            if m: d[int(m.group(1))] = {"x": int(m.group(2)), "y": int(m.group(3)), "alive": m.group(4) == "1"}
        return d
    def _read_all(self):
        sqf = ('{ private _u = HMT_SQUAD select _forEachIndex; private _p = if (isNull _u) then {[0,0]} else {getPosATL _u}; '
               'diag_log format ["HARMATTAN_AG %1 %2 %3 %4", _forEachIndex, round (_p#0), round (_p#1), (if (!isNull _u && {alive _u}) then {1} else {0})]; } forEach HMT_SQUAD;\n'
               '{ private _u = HMT_OPFOR select _forEachIndex; private _p = if (isNull _u) then {[0,0]} else {getPosATL _u}; '
               'diag_log format ["HARMATTAN_OP %1 %2 %3 %4", _forEachIndex, round (_p#0), round (_p#1), (if (!isNull _u && {alive _u}) then {1} else {0})]; } forEach HMT_OPFOR;\n')
        lines = self._query(sqf, "HARMATTAN_")
        ds = self._parse(lines, "HARMATTAN_AG"); do = self._parse(lines, "HARMATTAN_OP")
        self._squad = [ds.get(i, {"x": 0, "y": 0, "alive": False}) for i in range(self.n)]
        self._opfor = [do.get(i, {"x": 0, "y": 0, "alive": False}) for i in range(self.opfor)]
        return self._squad, self._opfor
    def _obs_from(self, us):
        obs = []
        for i, u in enumerate(us):
            ox = (u["x"] - self.x0) / self.size; oy = (u["y"] - self.y0) / self.size
            dgx = (self.objx - u["x"]) / self.size; dgy = (self.objy - u["y"]) / self.size
            best = (0.0, 0.0); bd = 1e9
            for j, v in enumerate(us):
                if j == i or not v["alive"]: continue
                dx = (v["x"] - u["x"]) / self.size; dy = (v["y"] - u["y"]) / self.size; dd = dx * dx + dy * dy
                if dd < bd: bd = dd; best = (dx, dy)
            obs.append([ox, oy, dgx, dgy, 1.0 if u["alive"] else 0.0, best[0], best[1]])
        return obs
    def step(self, actions):
        acts = "[" + ",".join(str(int(a)) for a in actions) + "]"
        sqf = ('private _A = %s;\n' % acts +
               '{ private _u = HMT_SQUAD select _forEachIndex; if (!isNull _u && {alive _u}) then '
               '{ private _d = [[0,0],[0,1],[0,-1],[1,0],[-1,0]] select (_A select _forEachIndex); '
               'private _p = getPosATL _u; _u setPosATL [(_p#0)+(_d#0)*%d,(_p#1)+(_d#1)*%d,0]; }; } forEach HMT_SQUAD;\n' % (self.move, self.move))
        self.b.send(sqf, wait=True); time.sleep(self.step_wait)
        self._read_all(); us = self._squad; obs = self._obs_from(us)
        n_alive = sum(1 for u in us if u["alive"])
        in_obj = sum(1 for u in us if u["alive"] and abs(u["x"] - self.objx) <= self.secure_r and abs(u["y"] - self.objy) <= self.secure_r)
        secured = in_obj >= self.secure_n; newly = secured and not self.secured; self.secured = secured
        cost = max(0, self.prev_alive - n_alive); self.prev_alive = n_alive; self.t += 1
        done = secured or self.t >= self.max_steps or n_alive == 0
        return obs, (1.0 if newly else 0.0) - 0.01, cost, done, {"in_obj": in_obj, "alive": n_alive, "secured": secured}
