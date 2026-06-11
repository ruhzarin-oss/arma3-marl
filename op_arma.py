"""op_arma — COUCHE OPÉRATIONNELLE (nuit du 05-06/06) : des agents qui mènent une OPÉRATION COMPLEXE,
pas un carrefour. Une opération = une PARTITION : phases -> ordres par ESCOUADE (objectif + posture)
-> transitions conditionnelles -> contingences. La micro reste le cerveau GELÉ `koth_finetuned.pt`
(obs 10 relatives à l'objectif de l'escouade, 4 macros) ; la posture = biais de logits (zéro réentraînement).
L'ennemi = IA Arma scriptée (garnison + patrouille + QRF déclenchable) — réaliste et gratuit.
JOURNAL DE DÉCISIONS intégré : chaque transition loggée avec sa raison (leçon du 05/06 : un étage
non instrumenté est un étage menteur). Tourne sur serveur DÉDIÉ headless (HarmattanBridge0)."""
import time, re, json
import numpy as np
import torch
import os as _os
from arma_bridge import ArmaBridge
from train_koth_gpu import Net

SB = "/mnt/data/harmattan-sandbox"
DEV = "cuda:0"

# ---------------------------------------------------------------- postures = biais de logits [HOLD, AVANCER, SUPPRESSER, COUVERT]
STANCES = {
    "move":     np.array([0.0, 2.5, -6.0, 0.0], dtype=np.float32),   # approche : avancer, pas de feu de suppression
    "assault":  np.array([-1.0, 2.0, 0.5, -1.0], dtype=np.float32),  # prendre : pousser, suppresser au contact
    "suppress": np.array([-1.0, -2.0, 3.0, 1.0], dtype=np.float32),  # fixer : cloue l'ennemi depuis la position
    "hold":     np.array([1.5, -2.0, 0.5, 1.5], dtype=np.float32),   # tenir : statique, couvert, feu défensif
}


class OpArma:
    """Espace de bataille PARTAGÉ : N escouades amies (WEST, cerveau) + ennemis scriptés (EAST, trackés pour les obs)."""

    def __init__(self, squads=(("SQ_APPUI", 7), ("SQ_ASSAUT", 7)), base=(15000, 16000),
                 mission=None, log=None, move=22.0, step_wait=1.0, settle=0.5, acc=4.0, step_game=None,
                 sup_range=120.0, sight=110.0, dmg_dead=0.7, skill=0.45, seed=0):
        if _os.environ.get("HMT_SOCKET") == "1":
            from arma_socket_bridge import SocketBridge
            import re as _re
            _m = _re.search(r"HarmattanBridge(\d+)", mission or "")
            self.b = SocketBridge(port=5801 + (int(_m.group(1)) if _m else 0))
        else:
            self.b = ArmaBridge(mission=mission or SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
                                log=log or SB + "/logs/server0.out")
        self.squads = [s[0] for s in squads]; self.sizes = [int(s[1]) for s in squads]
        self.S = len(self.squads); self.base = base
        self.move = move; self.step_wait = step_wait; self.settle = settle; self.acc = acc
        self.step_game = float(_os.environ.get("HMT_STEP_GAME", 0) or 0) or step_game   # cadence en temps de JEU (anti-confond de charge)
        if _os.environ.get("HMT_SOCKET") == "1": self.settle = min(self.settle, 0.15)   # les obs arrivent par TCP, plus d attente RPT
        self.sup_range = sup_range; self.sight = sight; self.dmg_dead = dmg_dead; self.skill = skill
        self.rng = np.random.default_rng(seed)
        self.scale = 140.0                                            # même échelle d'obs que l'entraînement KOTH
        # état ami : par escouade
        self.px = [np.zeros(n) for n in self.sizes]; self.py = [np.zeros(n) for n in self.sizes]
        self.dmg = [np.full(n, 0.0) for n in self.sizes]
        self.goals = [np.array(base, dtype=float) for _ in self.squads]
        self.stances = ["hold" for _ in self.squads]
        # état ennemi (taille dynamique : garnison + QRF ajoutées)
        self.en_n = 0; self.epx = np.zeros(0); self.epy = np.zeros(0); self.edmg = np.zeros(0)
        self.esupp = np.zeros(0); self.supp_mark = [np.zeros(n) for n in self.sizes]
        self._wp = [None for _ in self.squads]
        self.has_veh = False; self.vehdmg = 0.0; self.vehx = 0.0; self.vehy = 0.0   # QRF mécanisée (palier 1)            # waypoint de MARCHE posé (mode transit) par escouade

    # ------------------------------------------------------------- pont
    def _query(self, sqf, settle=None):
        nb = self.b.send(sqf, wait=True)
        time.sleep(self.settle if settle is None else settle)
        lines = self.b._log_lines()
        idx = max(i for i, ln in enumerate(lines) if ("HARMATTAN_RECV cmd %d" % nb) in ln)
        return lines[idx:]

    # ------------------------------------------------------------- mise en place
    def spawn(self, friendly_spawns, garrison):
        """friendly_spawns : {squad: (x,y)} ; garrison : list de (x, y, n, radius_patrouille)."""
        decl = "; ".join("%s=[]" % s for s in self.squads) + "; HMT_EN=[]"
        sqf = ("{ deleteVehicle _x } forEach vehicles; { deleteVehicle _x } forEach allUnits; HMT_VEH = nil; %s;\n"
               "west setFriend [east,0]; east setFriend [west,0];\n" % decl)
        for si, sq in enumerate(self.squads):
            x, y = friendly_spawns[sq]
            sqf += ('private _g%d = createGroup west;\n'
                    'for "_a" from 0 to %d do {\n'
                    '  private _ty = if (_a in [1,2]) then {"B_soldier_LAT_F"} else {"B_Soldier_F"};\n'
                    '  _g%d createUnit [_ty, [%d + 9*(cos (360*_a/%d)), %d + 9*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
                    '  private _u = (units _g%d) select ((count (units _g%d))-1);\n'
                    '  _u setBehaviour "COMBAT"; _u setUnitPos "AUTO"; _u setSkill %.2f; _u allowFleeing 0;\n'
                    '  %s pushBack _u;\n};\n'
                    % (si, self.sizes[si] - 1, si, x, self.sizes[si], y, self.sizes[si], si, si, self.skill, sq))
        for gi, (x, y, n, rad) in enumerate(garrison):
            sqf += ('private _e%d = createGroup east;\n'
                    'for "_a" from 0 to %d do {\n'
                    '  _e%d createUnit ["O_Soldier_F", [%d + 7*(cos (360*_a/%d)), %d + 7*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
                    '  private _u = (units _e%d) select ((count (units _e%d))-1);\n'
                    '  _u setBehaviour "AWARE"; _u setSkill %.2f; _u allowFleeing 0;\n'
                    '  HMT_EN pushBack _u;\n};\n'
                    '[_e%d, [%d,%d], %d] call BIS_fnc_taskPatrol;\n'
                    % (gi, n - 1, gi, x, n, y, n, gi, gi, self.skill, gi, x, y, rad))
        sqf += 'setAccTime %.1f; diag_log "HARMATTAN_OPSPAWN";\n' % self.acc
        self.b.send(sqf, wait=True); time.sleep(4.0)
        self.has_veh = False; self.vehdmg = 0.0
        self.en_n = sum(g[2] for g in garrison)
        self.epx = np.zeros(self.en_n); self.epy = np.zeros(self.en_n); self.edmg = np.zeros(self.en_n)
        self.read()

    def spawn_qrf(self, x, y, n, target):
        """Contre-attaque ennemie : n soldats spawned en (x,y), SAD vers target. Ajoutés au tracking."""
        sqf = ('private _q = createGroup east;\n'
               'for "_a" from 0 to %d do {\n'
               '  _q createUnit ["O_Soldier_F", [%d + 8*(cos (360*_a/%d)), %d + 8*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
               '  private _u = (units _q) select ((count (units _q))-1);\n'
               '  _u setBehaviour "COMBAT"; _u setSkill %.2f; _u allowFleeing 0; HMT_EN pushBack _u;\n};\n'
               'private _wp = _q addWaypoint [[%d,%d], 0]; _wp setWaypointType "SAD"; _wp setWaypointSpeed "FULL";\n'
               'diag_log "HARMATTAN_QRF";\n'
               % (n - 1, x, n, y, n, self.skill, target[0], target[1]))
        self.b.send(sqf, wait=True)
        self.en_n += n
        self.epx = np.concatenate([self.epx, np.zeros(n)]); self.epy = np.concatenate([self.epy, np.zeros(n)])
        self.edmg = np.concatenate([self.edmg, np.zeros(n)])

    def spawn_qrf_mech(self, x, y, n_dism, target):
        """Contre-attaque MÉCANISÉE : 1 Ifrit HMG (équipage scripté) + n_dism débarqués, SAD vers target.
        Débarqués + équipage trackés dans HMT_EN ; le VÉHICULE tracké à part (HMT_VEH) pour le verdict."""
        sqf = ('private _vr = [[%d, %d, 0], 180, "O_MRAP_02_hmg_F", east] call BIS_fnc_spawnVehicle;\n'
               'HMT_VEH = [_vr select 0];\n'
               '{ _x allowFleeing 0; _x setSkill %.2f; HMT_EN pushBack _x } forEach (_vr select 1);\n'
               'private _wv = (_vr select 2) addWaypoint [[%d,%d], 0]; _wv setWaypointType "SAD"; _wv setWaypointSpeed "FULL"; '
               '(_vr select 2) setBehaviour "COMBAT"; (driver (_vr select 0)) doMove [%d,%d];\n'
               'private _q = createGroup east;\n'
               'for "_a" from 0 to %d do {\n'
               '  _q createUnit ["O_Soldier_F", [%d + 8*(cos (360*_a/%d)), %d + 8*(sin (360*_a/%d)), 0], [], 0, "FORM"];\n'
               '  private _u = (units _q) select ((count (units _q))-1);\n'
               '  _u setBehaviour "COMBAT"; _u setSkill %.2f; _u allowFleeing 0; HMT_EN pushBack _u;\n};\n'
               'private _wp = _q addWaypoint [[%d,%d], 0]; _wp setWaypointType "SAD"; _wp setWaypointSpeed "FULL";\n'
               'diag_log "HARMATTAN_QRFMECH";\n'
               % (x, y, self.skill, target[0], target[1], target[0], target[1],
                  n_dism - 1, x + 15, n_dism, y, n_dism, self.skill, target[0], target[1]))
        self.b.send(sqf, wait=True)
        ncrew = 2                                                  # Ifrit HMG : pilote + tireur
        add = ncrew + n_dism
        self.en_n += add
        self.epx = np.concatenate([self.epx, np.zeros(add)]); self.epy = np.concatenate([self.epy, np.zeros(add)])
        self.edmg = np.concatenate([self.edmg, np.zeros(add)])
        self.has_veh = True; self.vehdmg = 0.0; self.vehx = float(x); self.vehy = float(y)

    # ------------------------------------------------------------- lecture d'état
    def _dump_sqf(self):
        out = ""
        for sq in self.squads:
            tag = sq
            out += ('{ private _u=%s select _forEachIndex; private _p = if (isNull _u) then {[0,0]} else {getPosATL _u}; '
                    'private _dm = if (isNull _u) then {100} else {round ((getDammage _u)*100)}; '
                    'diag_log format ["HARMATTAN_%s %%1 %%2 %%3 %%4", _forEachIndex, round (_p#0), round (_p#1), _dm]; } forEach %s;\n'
                    % (tag, tag, sq))
        out += ('if (!isNil "HMT_VEH") then { private _v = HMT_VEH select 0; private _p = if (isNull _v) then {[0,0]} else {getPosATL _v}; '
                'private _dm = if (isNull _v) then {100} else {round ((getDammage _v)*100)}; '
                'diag_log format ["HARMATTAN_VEH 0 %1 %2 %3", round (_p#0), round (_p#1), _dm]; };\n')
        out += ('{ private _u=HMT_EN select _forEachIndex; private _p = if (isNull _u) then {[0,0]} else {getPosATL _u}; '
                'private _dm = if (isNull _u) then {100} else {round ((getDammage _u)*100)}; '
                'diag_log format ["HARMATTAN_EN %1 %2 %3 %4", _forEachIndex, round (_p#0), round (_p#1), _dm]; } forEach HMT_EN;\n')
        return out

    def read(self):
        lines = self._query(self._dump_sqf())
        for si, sq in enumerate(self.squads):
            for ln in lines:
                m = re.search(r"HARMATTAN_%s (\d+) (-?\d+) (-?\d+) (\d+)" % sq, ln)
                if m:
                    g = int(m.group(1))
                    if g < self.sizes[si]:
                        self.px[si][g] = int(m.group(2)); self.py[si][g] = int(m.group(3)); self.dmg[si][g] = int(m.group(4))
        for ln in lines:
            mv = re.search(r"HARMATTAN_VEH 0 (-?\d+) (-?\d+) (\d+)", ln)
            if mv:
                self.vehx = int(mv.group(1)); self.vehy = int(mv.group(2)); self.vehdmg = int(mv.group(3))
        for ln in lines:
            m = re.search(r"HARMATTAN_EN (\d+) (-?\d+) (-?\d+) (\d+)", ln)
            if m:
                g = int(m.group(1))
                if g < self.en_n:
                    self.epx[g] = int(m.group(2)); self.epy[g] = int(m.group(3)); self.edmg[g] = int(m.group(4))

    def alive(self, si): return self.dmg[si] < self.dmg_dead * 100
    def en_alive(self): return self.edmg < self.dmg_dead * 100

    # ------------------------------------------------------------- obs (calées sur l'entraînement KOTH : 10 features)
    def obs(self, si):
        S = self.scale; n = self.sizes[si]
        gx, gy = self.goals[si]; al = self.alive(si)
        ox = (self.px[si] - gx) / S; oy = (self.py[si] - gy) / S
        dgx = (gx - self.px[si]) / S; dgy = (gy - self.py[si]) / S
        dx = self.px[si][None, :] - self.px[si][:, None]; dy = self.py[si][None, :] - self.py[si][:, None]
        d2 = np.where(np.eye(n, dtype=bool) | (~al)[None, :], 1e18, dx * dx + dy * dy)
        jm = d2.argmin(1)
        adx = dx[np.arange(n), jm] / S; ady = dy[np.arange(n), jm] / S
        nm = d2.min(1) >= 1e18; adx[nm] = 0.0; ady[nm] = 0.0
        eal = self.en_alive()
        if self.en_n and eal.any():
            ex = self.epx[None, :] - self.px[si][:, None]; ey = self.epy[None, :] - self.py[si][:, None]
            ed2 = np.where(eal[None, :], ex * ex + ey * ey, 1e18); km = ed2.argmin(1)
            edx = ex[np.arange(n), km]; edy = ey[np.arange(n), km]
            nd = np.sqrt(ed2.min(1)); seen = (nd <= self.sight) & (ed2.min(1) < 1e18)
            edx = (edx / S) * seen; edy = (edy / S) * seen
            es = np.zeros(n)
        else:
            edx = np.zeros(n); edy = np.zeros(n); es = np.zeros(n)
        return np.stack([ox, oy, dgx, dgy, al.astype(np.float32), adx, ady, edx, edy, es], 1).astype(np.float32)

    # ------------------------------------------------------------- ordres
    def _contact(self, si):
        """Vrai si un ennemi vivant est à portée de vue d'un soldat vivant de l'escouade."""
        eal = self.en_alive(); al = self.alive(si)
        if not (self.en_n and eal.any() and al.any()): return False
        dx = self.epx[None, :] - self.px[si][:, None]; dy = self.epy[None, :] - self.py[si][:, None]
        d2 = dx * dx + dy * dy
        return bool(((d2[al][:, eal]) <= self.sight ** 2).any())

    def _nearest_enemy_dist(self, si):
        """Distance du plus proche ennemi VIVANT à un membre vivant de l'escouade (1e9 si aucun)."""
        eal = self.en_alive(); al = self.alive(si)
        if not (self.en_n and eal.any() and al.any()): return 1e9
        dx = self.epx[None, :] - self.px[si][:, None]; dy = self.epy[None, :] - self.py[si][:, None]
        d2 = dx * dx + dy * dy
        return float(np.sqrt(d2[al][:, eal].min()))

    def _goal_dist(self, si):
        al = self.alive(si)
        if not al.any(): return 0.0
        gx, gy = self.goals[si]
        return float(np.median(np.sqrt((self.px[si][al] - gx) ** 2 + (self.py[si][al] - gy) ** 2)))

    def _game_time(self):
        """Temps de simulation Arma (variable SQF time) — seule horloge comparable a charge variable."""
        self.b.send("diag_log format [\"HARMATTAN_TIME %1\", time];", wait=True)
        for ln in reversed(self.b._log_lines(400)):
            m = re.search(r"HARMATTAN_TIME ([0-9.]+)", ln)
            if m: return float(m.group(1))
        return -1.0

    def step(self, acts_per_squad):
        cmds = []
        eal = self.en_alive()
        for si, sq in enumerate(self.squads):
            a = acts_per_squad[si]; al = self.alive(si)
            gx, gy = self.goals[si]
            # ---- MODE TRANSIT : posture move, hors contact, loin de l'objectif -> waypoint de groupe (l'IA marche) ----
            in_transit = ((self.stances[si] == "move" and not self._contact(si) and self._goal_dist(si) > 120.0)
                          or (self.stances[si] == "assault" and self._nearest_enemy_dist(si) > 250.0
                              and self._goal_dist(si) > 40.0))                  # v2 : derniers mètres en zone NETTOYÉE seulement
            if in_transit:
                if self._wp[si] != (int(gx), int(gy)):
                    lead = int(np.argmax(al)) if al.any() else 0
                    cmds.append(('private _u=%s select %d; if (!isNull _u && {alive _u}) then { private _g = group _u; '
                                 'while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]}; '
                                 '_g setBehaviour "AWARE"; _g setSpeedMode "FULL"; _g setFormation "WEDGE"; '
                                 '{ _x setUnitPos "AUTO"; _x doFollow (leader _g) } forEach units _g; '
                                 'private _wp = _g addWaypoint [[%d,%d], 0]; _wp setWaypointType "MOVE"; _wp setWaypointSpeed "FULL"; };')
                                % (sq, lead, int(gx), int(gy)))
                    self._wp[si] = (int(gx), int(gy))
                continue                                          # pas de micro pendant la marche
            # ---- MODE TACTIQUE : le cerveau reprend la main (contact ou proche objectif) ----
            if self._wp[si] is not None:                          # sortir du mode transit : redonner la main à la micro
                lead = int(np.argmax(al)) if al.any() else 0
                cmds.append(('private _u=%s select %d; if (!isNull _u && {alive _u}) then { private _g = group _u; '
                             'while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]}; _g setBehaviour "COMBAT"; };')
                            % (sq, lead))
                self._wp[si] = None
            tox = gx - self.px[si]; toy = gy - self.py[si]; tn = np.sqrt(tox ** 2 + toy ** 2) + 1e-6
            spd = np.zeros(self.sizes[si]); spd[a == 1] = self.move; spd[a == 3] = self.move * 0.5
            tgx = self.px[si] + (tox / tn) * spd; tgy = self.py[si] + (toy / tn) * spd
            if self.en_n and eal.any():
                ex = self.epx[None, :] - self.px[si][:, None]; ey = self.epy[None, :] - self.py[si][:, None]
                km = np.where(eal[None, :], ex * ex + ey * ey, 1e18).argmin(1)
            else:
                km = np.zeros(self.sizes[si], dtype=int)
            for i in range(self.sizes[si]):
                if not al[i]: continue
                m = int(a[i])
                if m == 0:
                    cmds.append('private _u=%s select %d; if (!isNull _u && {alive _u}) then {doStop _u; _u setUnitPos "MIDDLE";};' % (sq, i))
                elif m == 2 and self.en_n and eal.any():
                    cmds.append('private _u=%s select %d; private _e=HMT_EN select %d; if (!isNull _u && {alive _u} && {!isNull _e} && {alive _e}) then {doStop _u; _u setUnitPos "UP"; _u doTarget _e; _u doFire _e; _e suppressFor 2.5;};' % (sq, i, int(km[i])))
                else:
                    pos = "DOWN" if m == 3 else "MIDDLE"
                    cmds.append('private _u=%s select %d; if (!isNull _u && {alive _u}) then {_u setUnitPos "%s"; _u doMove [%d,%d,0];};' % (sq, i, pos, int(tgx[i]), int(tgy[i])))
        if self.has_veh and self.vehdmg < 70:                       # palier 1 : les NLAW traitent le véhicule
            for si, sq in enumerate(self.squads):
                al = self.alive(si)
                vd = np.sqrt((self.px[si] - self.vehx) ** 2 + (self.py[si] - self.vehy) ** 2)
                for i in (1, 2):                                        # les 2 porteurs AT de l'escouade
                    if i < self.sizes[si] and al[i] and vd[i] < 400:
                        cmds.append('private _u=%s select %d; if (!isNull _u && {alive _u} && {!isNil "HMT_VEH"}) then '
                                    '{ private _v = HMT_VEH select 0; if (!isNull _v && {alive _v}) then '
                                    '{ _u reveal [_v, 4]; _u doTarget _v; _u doFire _v; }; };' % (sq, i))
        self.b.send("\n".join(cmds), wait=True)
        if self.step_game:
            # [11/06 anti-confond] cadence en temps de JEU : on attend que la SIM ait avance de step_game s,
            # quelle que soit la charge machine (mur de securite : 6x le budget attendu)
            t0 = self._game_time(); t0w = time.time()
            while True:
                time.sleep(0.12)
                if self._game_time() - t0 >= self.step_game: break
                if time.time() - t0w > 6.0 * self.step_game: break
        else:
            time.sleep(self.step_wait)
        self.read()


# ==================================================================== le CHEF D'OPÉRATION (machine à phases)
class OperationRunner:
    def __init__(self, env, net, mission_plan, log_path="op_journal.jsonl", verbose=True):
        self.env = env; self.net = net; self.plan = mission_plan
        self.logf = open(log_path, "a"); self.verbose = verbose
        self.t0 = time.time(); self.step_i = 0; self.qrf_done = set()

    def jlog(self, kind, **kw):
        rec = {"t": round(time.time() - self.t0, 1), "step": self.step_i, "kind": kind, **kw}
        self.logf.write(json.dumps(rec) + "\n"); self.logf.flush()
        if self.verbose:
            print("[%6.1fs] %-10s %s" % (rec["t"], kind, {k: v for k, v in kw.items() if k != "detail"}), flush=True)

    def squad_at(self, si, pt, r):
        al = self.env.alive(si)
        if not al.any(): return False
        d = np.sqrt((self.env.px[si] - pt[0]) ** 2 + (self.env.py[si] - pt[1]) ** 2)
        return np.median(d[al]) < r

    def zone_clear(self, pt, r):
        eal = self.env.en_alive()
        if not eal.any(): return True
        d = np.sqrt((self.env.epx - pt[0]) ** 2 + (self.env.epy - pt[1]) ** 2)
        return not (eal & (d < r)).any()

    def losses(self):
        tot = sum(self.env.sizes); alive = sum(int(self.env.alive(si).sum()) for si in range(self.env.S))
        return 1.0 - alive / tot

    def cond(self, c):
        k = c[0]
        if k == "squad_at": return self.squad_at(c[1], c[2], c[3])
        if k == "zone_clear": return self.zone_clear(c[1], c[2])
        if k == "enemy_dead_frac": return (1.0 - self.env.en_alive().mean()) >= c[1] if self.env.en_n else True
        if k == "steps": return self.phase_steps >= c[1]
        if k == "losses": return self.losses() >= c[1]          # contingences (seuil de pertes franchi)
        if k == "losses_max": return self.losses() <= c[1]      # critère de succès (pertes contenues)
        if k == "all": return all(self.cond(x) for x in c[1])
        if k == "any": return any(self.cond(x) for x in c[1])
        raise ValueError(k)

    def act(self, si):
        o = self.env.obs(si)
        with torch.no_grad():
            lg = self.net.a_logits(torch.as_tensor(o, dtype=torch.float32, device=DEV))
        lg = lg + torch.as_tensor(STANCES[self.env.stances[si]], device=DEV)
        return torch.distributions.Categorical(logits=lg).sample().cpu().numpy()

    def run(self, max_steps=400, max_wall=1200.0, stall_wall=500.0):
        pidx = 0
        # [10/06] bornes de cout : un standoff ne doit plus couter 7 h (mur temps-reel + detecteur d enlisement)
        t_mur = time.time(); sig_prec = None; t_fige = time.time(); abort = None
        self.jlog("OP_START", op=self.plan["name"], squads=self.env.squads, sizes=self.env.sizes)
        while pidx < len(self.plan["phases"]) and self.step_i < max_steps and abort is None:
            ph = self.plan["phases"][pidx]
            for sq, (goal, stance) in ph["orders"].items():
                si = self.env.squads.index(sq)
                self.env.goals[si] = np.array(goal, dtype=float); self.env.stances[si] = stance
            self.jlog("PHASE", name=ph["name"], orders={k: (list(map(int, v[0])), v[1]) for k, v in ph["orders"].items()},
                      losses=round(self.losses(), 2))
            if "on_enter" in ph: ph["on_enter"](self)
            self.phase_steps = 0
            while self.step_i < max_steps:
                if max_wall and time.time() - t_mur > max_wall:
                    abort = "TIMEOUT_MUR"
                sig = (int(self.env.en_alive().sum()),
                       sum(int(self.env.alive(si).sum()) for si in range(self.env.S)), pidx)
                if sig != sig_prec:
                    sig_prec = sig; t_fige = time.time()
                elif stall_wall and time.time() - t_fige > stall_wall:
                    abort = "ENLISEMENT"
                if abort:
                    self.jlog("OP_ABORT", raison=abort, phase=ph["name"], steps=self.step_i,
                              losses=round(self.losses(), 2), ennemis=int(self.env.en_alive().sum()))
                    break
                acts = [self.act(si) for si in range(self.env.S)]
                self.env.step(acts); self.step_i += 1; self.phase_steps += 1
                # [v3 07/06] QRF déclenchée par la CHUTE DE LA GARNISON, quel que soit le chemin de phases
                # (l'accrochage à l'entrée en CONSOLIDATION laissait les contingences l'esquiver — artefact AZALAI-01)
                qg = self.plan.get("qrf_on_garrison")
                if qg is not None and "qrf" not in self.qrf_done:
                    if not self.env.en_alive()[0:self.plan.get("garr_n", 12)].any():
                        self.jlog("QRF_TRIGGER", detail="garnison tombee -> contre-attaque")
                        qg(self)
                if self.step_i % 5 == 0:
                    self.jlog("SITREP", phase=ph["name"],
                              vivants=[int(self.env.alive(si).sum()) for si in range(self.env.S)],
                              ennemis=int(self.env.en_alive().sum()), losses=round(self.losses(), 2))
                jumped = False
                for cont in ph.get("contingencies", []):
                    if self.cond(cont["if"]):
                        self.jlog("CONTINGENCE", phase=ph["name"], raison=cont["reason"], goto=cont["goto"])
                        pidx = next(i for i, p in enumerate(self.plan["phases"]) if p["name"] == cont["goto"])
                        jumped = True; break
                if jumped: break
                if self.cond(ph["done_when"]):
                    self.jlog("PHASE_OK", phase=ph["name"], steps=self.phase_steps, losses=round(self.losses(), 2))
                    pidx += 1; break
        self.abort_reason = abort
        success = self.cond(self.plan["success"])
        self.jlog("OP_END", succes=bool(success), steps=self.step_i, losses=round(self.losses(), 2),
                  ennemis_restants=int(self.env.en_alive().sum()))
        return success
