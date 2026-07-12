#!/usr/bin/env python3
"""agent_swarm.py — pilote N soldats Arma comme AGENTS REFLEXES (remplace LAMBS).

Thèse : tout soldat est un agent. Un MEME corps réflexe (FightNet, reflex_r23wh) habite chaque homme,
des deux camps. La seule différence par camp = qui sont mes ennemis + où je veux aller (le but, posé par
le commandant/officier au-dessus). LAMBS est COUPÉ (disableAI FSM/ANIM/AUTOCOMBAT) ; on garde TARGET pour
le tir réflexe.

Goulot = le pont, pas le cerveau : on LIT toutes les perceptions en un appel, on infère en BATCH sur GPU,
on ÉCRIT toutes les actions en un appel. La perception (fire-sense + cover-sense), calculée par-soldat en
Python dans le live (ok pour 9), est ici VECTORISÉE en torch (tient 100+ agents sans transpirer)."""
import math
import torch

# --- géométrie des D secteurs (identique au live : ang=k*2pi/D, DXY=(cos,sin) = (est,nord)) ---
def _dxy(D):
    ang = [k * 2 * math.pi / D for k in range(D)]
    return torch.tensor([[math.cos(a), math.sin(a)] for a in ang], dtype=torch.float32)   # [D,2]


class AgentSwarm:
    """Driver réflexe vectorisé pour N agents d'un même camp.

    body   : FightNet chargé (corps réflexe partagé reflex_r23wh)
    hm     : heightmap [HN,HN] (relief, pour le cover-sense) ; hx0,hy0,hres,HN = géo de la grille
    enemy_side / group_var / vx_var / vy_var : côté Arma (qui je combats, et les variables globales SQF)
    """

    def __init__(self, body, hm, hx0, hy0, hres, HN, *, D=8, obs_dim=21,
                 group_var="HMT_FS", enemy_side="east", vx_var="HMT_VX", vy_var="HMT_VY",
                 maxr=170.0, threat_r=165.0, device="cpu"):
        self.net = body.to(device).eval()
        self.dev = device
        self.D = D; self.obs_dim = obs_dim
        self.DXY = _dxy(D).to(device)                                  # [D,2]
        self.maxr = maxr; self.threat_r = threat_r
        self.group_var = group_var; self.enemy_side = enemy_side
        self.vx_var = vx_var; self.vy_var = vy_var
        self.HM = torch.as_tensor(hm, dtype=torch.float32, device=device)
        self.hx0 = float(hx0); self.hy0 = float(hy0); self.hres = float(hres); self.HN = int(HN)

    # ---------- relief vectorisé : altitude du terrain à des points [..,2] ----------
    def _height(self, pts):
        x = pts[..., 0]; y = pts[..., 1]
        j = ((x - self.hx0) / self.hres).long().clamp(0, self.HN - 1)
        i = ((y - self.hy0) / self.hres).long().clamp(0, self.HN - 1)
        return self.HM[i, j]

    # ---------- PERCEPTION vectorisée : N agents, M ennemis -> obs [N, obs_dim] ----------
    @torch.no_grad()
    def perceive(self, pos, enemies, prone):
        """pos [N,2] (mes agents vivants), enemies [M,2], prone [N] -> (obs [N,obs_dim], threats [N], coverdir [N,2])."""
        pos = torch.as_tensor(pos, dtype=torch.float32, device=self.dev)
        prone = torch.as_tensor(prone, dtype=torch.float32, device=self.dev)
        N = pos.shape[0]; D = self.D
        M = 0 if enemies is None else len(enemies)
        if M == 0:                                                     # aucun ennemi : fire=0, threats=0
            fire = torch.zeros(N, D, device=self.dev); threats = torch.zeros(N, device=self.dev)
        else:
            en = torch.as_tensor(enemies, dtype=torch.float32, device=self.dev)   # [M,2]
            dx = en[:, 0][None, :] - pos[:, 0][:, None]               # [N,M] est
            dy = en[:, 1][None, :] - pos[:, 1][:, None]               # [N,M] nord
            dist = torch.sqrt(dx * dx + dy * dy) + 1e-6               # [N,M]
            # secteur de chaque ennemi = argmax_k (dx*cos_k + dy*sin_k)
            proj = dx[:, :, None] * self.DXY[:, 0][None, None, :] + dy[:, :, None] * self.DXY[:, 1][None, None, :]  # [N,M,D]
            sect = proj.argmax(-1)                                    # [N,M]
            within = (dist < self.maxr).float()
            w = torch.clamp(1.0 - dist / self.maxr, min=0.05) * within  # [N,M] poids = proche -> fort
            fire = torch.zeros(N, D, device=self.dev)
            fire.scatter_reduce_(1, sect, w, reduce="amax", include_self=True)  # max par secteur
            threats = (dist < self.threat_r).sum(1).float()          # [N] nb menaces proches
        # COVER-SENSE : par secteur, gain d'altitude du relief (échantillons 12/24/36 m)
        h0 = self._height(pos)                                        # [N]
        steps = torch.tensor([12.0, 24.0, 36.0], device=self.dev)
        samp = pos[:, None, None, :] + self.DXY[None, :, None, :] * steps[None, None, :, None]  # [N,D,3,2]
        mh = self._height(samp).amax(-1)                             # [N,D] max sur les 3 distances
        cover = torch.clamp((mh - h0[:, None]) / 14.0, 0.0, 1.0)     # [N,D]
        cb = cover.argmax(1)                                          # [N] meilleur secteur de couvert
        coverdir = self.DXY[cb]                                       # [N,2]
        exposed = torch.clamp(threats / 3.0, max=1.0)
        leftf = exposed                                              # proxy (identique au live)
        obs = torch.cat([fire, exposed[:, None], cover, coverdir, prone[:, None], leftf[:, None]], dim=1)  # [N,21]
        return obs, threats, coverdir

    @torch.no_grad()
    def act(self, obs):
        """obs [N,obs_dim] -> mv [N], stance [N], fire_sector [N] (corps réflexe partagé, batch)."""
        ml, sl, fl, _ = self.net(obs)
        return ml.argmax(-1), sl.argmax(-1), fl.argmax(-1)

    # ---------- mapping réflexe -> vitesse (vectorisé) : but + couvert + posture au feu ----------
    @torch.no_grad()
    def decide_velocity(self, pos, mv, threats, coverdir, goals, *, assault=True, speed=8.0):
        """Renvoie vx,vy [N]. Hors feu -> fonce au but. Sous feu modéré -> bond vers but biaisé couvert.
        Feu lourd -> assaut (pousse au but) ou tient (base de feu) selon `assault`."""
        pos = torch.as_tensor(pos, dtype=torch.float32, device=self.dev)
        goals = torch.as_tensor(goals, dtype=torch.float32, device=self.dev)
        N = pos.shape[0]
        gd = goals - pos; gn = gd.norm(dim=1, keepdim=True) + 1e-6; gdir = gd / gn          # dir vers le but
        mvi = mv.clamp(0, self.D)                                                            # 0 = rester
        movedir = self.DXY[(mvi - 1).clamp(0, self.D - 1)]                                   # dir réflexe (couvert)
        has_mv = (mvi > 0).float()[:, None]
        # bond feu-et-mouvement : 60% but + 40% réflexe-couvert
        bound = 0.6 * gdir + 0.4 * (movedir * has_mv + coverdir * (1 - has_mv))
        bn = bound.norm(dim=1, keepdim=True) + 1e-6; bound = bound / bn
        light = (threats >= 1) & (threats < 4)
        heavy = threats >= 4
        v = gdir * speed                                                                    # défaut : libre -> but
        v = torch.where(light[:, None], bound * (speed * 0.7), v)                            # contact modéré -> bond
        if assault:
            v = torch.where(heavy[:, None], bound * (speed * 0.7), v)                        # feu lourd -> pousse quand même
        else:
            v = torch.where(heavy[:, None], torch.zeros_like(v), v)                          # base de feu -> tient (suppression)
        return v[:, 0], v[:, 1]

    # ---------- SQF : ARMER les agents (= COUPER LAMBS) sur un paquet de soldats ----------
    @staticmethod
    def arm_agents_sqf(group_var, vx_var, vy_var):
        """SQF qui transforme chaque unité de `group_var` en agent pilotable : coupe FSM/ANIM/AUTOCOMBAT
        (remplace LAMBS), garde TARGET (tir réflexe), enregistre une vitesse 0 et pose l'EachFrame 50 Hz."""
        return (
            "%s = []; %s = [];\n" % (vx_var, vy_var) +
            "{ _x disableAI \"FSM\"; _x disableAI \"ANIM\"; _x disableAI \"AUTOCOMBAT\"; "
            "_x setBehaviour \"COMBAT\"; _x setCombatMode \"RED\"; "
            "%s pushBack 0; %s pushBack 0; } forEach %s;\n" % (vx_var, vy_var, group_var) +
            "addMissionEventHandler [\"EachFrame\", { { if (alive _x) then "
            "{ _x setVelocity [%s select _forEachIndex, %s select _forEachIndex, (velocity _x)#2] } } "
            "forEach %s; }];" % (vx_var, vy_var, group_var)
        )

    def write_velocity_sqf(self, vx, vy):
        """SQF batché : pousse toutes les vitesses d'un coup (un seul write pour N agents)."""
        vxl = [round(float(v), 2) for v in vx.tolist()]; vyl = [round(float(v), 2) for v in vy.tolist()]
        return "%s = %s; %s = %s;" % (self.vx_var, vxl, self.vy_var, vyl)

    def fire_sqf(self, idxs, bearings):
        """SQF batché : chaque agent i engage (doFire) l'ennemi le plus proche dans le secteur visé."""
        out = []
        for i, bdeg in zip(idxs, bearings):
            out.append(
                "private _u=%s select %d; if (alive _u) then {private _es=(allUnits select "
                "{side _x==%s && alive _x && (_u distance _x)<200 && abs((((_u getDir _x)-%d+540) mod 360)-180)<28}); "
                "if (count _es>0) then {_es=_es apply {[_u distance _x,_x]}; _es sort true; private _e=(_es#0)#1; "
                "_u reveal _e; _u doTarget _e; _u doFire _e;};};" % (self.group_var, int(i), self.enemy_side, int(bdeg))
            )
        return out

    def bearings(self, fire_sectors, threats):
        """Secteurs de tir -> (indices agents, caps boussole) pour les agents qui tirent et ont une menace."""
        idxs = []; deg = []
        for i in range(len(fire_sectors)):
            fs = int(fire_sectors[i])
            if fs > 0 and float(threats[i]) > 0:
                cx, cy = self.DXY[fs - 1].tolist()
                deg.append(round(math.degrees(math.atan2(cx, cy))) % 360); idxs.append(i)   # cap = atan2(est,nord)
        return idxs, deg


# ======================= SELF-TEST (sans Arma) : vectorisation correcte + rapide =======================
def _ref_perceive_one(fx, fy, prone, enemies, hmf, D, maxr, threat_r):
    """Référence par-agent (copie EXACTE de la logique du live) pour valider la vectorisation."""
    DXY = [(math.cos(k * 2 * math.pi / D), math.sin(k * 2 * math.pi / D)) for k in range(D)]
    threats = [e for e in enemies if math.hypot(e[0] - fx, e[1] - fy) < threat_r]
    fire = [0.0] * D
    for ex, ey in enemies:
        dx = ex - fx; dy = ey - fy; dd = math.hypot(dx, dy) + 1e-6
        if dd >= maxr: continue
        sect = max(range(D), key=lambda k: dx * DXY[k][0] + dy * DXY[k][1])
        fire[sect] = max(fire[sect], max(0.05, 1 - dd / maxr))
    h0 = hmf(fx, fy); cover = [0.0] * D
    for k in range(D):
        mh = max(hmf(fx + DXY[k][0] * s, fy + DXY[k][1] * s) for s in (12, 24, 36))
        cover[k] = min(max((mh - h0) / 14.0, 0), 1)
    cb = max(range(D), key=lambda k: cover[k]); cvx, cvy = DXY[cb]
    exposed = min(len(threats) / 3.0, 1.0)
    return fire + [exposed] + cover + [cvx, cvy] + [prone, exposed], len(threats)


def _selftest():
    import time
    torch.manual_seed(0)
    D = 8; HN = 200; hx0 = hy0 = 0.0; hres = 7.5
    # relief synthétique (collines douces) pour exercer le cover-sense
    yy, xx = torch.meshgrid(torch.arange(HN), torch.arange(HN), indexing="ij")
    HM = (8 * torch.sin(xx.float() / 11) * torch.cos(yy.float() / 9) + 4 * torch.sin(xx.float() / 5)).float()

    class _Body(torch.nn.Module):                                     # corps réflexe factice (test de forme/vitesse)
        def __init__(s):
            super().__init__()
            s.b = torch.nn.Sequential(torch.nn.Linear(21, 64), torch.nn.Tanh())
            s.mv = torch.nn.Linear(64, D + 1); s.stc = torch.nn.Linear(64, 2); s.fire = torch.nn.Linear(64, D + 1); s.v = torch.nn.Linear(64, 1)
        def forward(s, o):
            z = s.b(o); return s.mv(z), s.stc(z), s.fire(z), s.v(z).squeeze(-1)

    sw = AgentSwarm(_Body(), HM, hx0, hy0, hres, HN, D=D, device="cpu")

    def hmf(x, y):
        j = min(max(int((x - hx0) / hres), 0), HN - 1); i = min(max(int((y - hy0) / hres), 0), HN - 1)
        return float(HM[i, j])

    # --- 1) correction : vectorisé == référence par-agent ---
    N = 40; M = 15
    pos = torch.rand(N, 2) * 1200 + 100
    enemies = (torch.rand(M, 2) * 1200 + 100).tolist()
    prone = (torch.rand(N) > 0.5).float()
    obs, threats, _ = sw.perceive(pos, enemies, prone)
    maxd = 0.0; maxt = 0
    for i in range(N):
        ref, rt = _ref_perceive_one(float(pos[i, 0]), float(pos[i, 1]), float(prone[i]), enemies, hmf, D, sw.maxr, sw.threat_r)
        d = (obs[i] - torch.tensor(ref)).abs().max().item(); maxd = max(maxd, d); maxt = max(maxt, abs(int(threats[i]) - rt))
    print("[1] correction perception : ecart_max obs=%.2e | ecart_max threats=%d (attendu 0)" % (maxd, maxt))
    assert maxd < 1e-4 and maxt == 0, "VECTORISATION INCORRECTE"

    # --- 2) vitesse : latence à plusieurs échelles d'ensemble ACTIF (dyn-sim) ---
    for N in (100, 200, 500):                                          # 500 = cas extreme (tout le reseau au contact)
        pos = torch.rand(N, 2) * 1200 + 100
        enemies = (torch.rand(30, 2) * 1200 + 100).tolist()
        prone = torch.zeros(N)
        goals = torch.rand(N, 2) * 1200 + 100
        t0 = time.time()
        for _ in range(50):
            obs, threats, cdir = sw.perceive(pos, enemies, prone)
            mv, stc, frt = sw.act(obs)
            vx, vy = sw.decide_velocity(pos, mv, threats, cdir, goals, assault=True)
            idxs, deg = sw.bearings(frt, threats)
        dt = (time.time() - t0) / 50 * 1000
        print("[2] %3d agents (perceive+act+velocity+bearings) : %.2f ms/tick | tirent=%d" % (N, dt, len(idxs)))

    # --- 3) SQF d'armement (coupe LAMBS) ---
    sqf = AgentSwarm.arm_agents_sqf("HMT_DEF", "HMT_DVX", "HMT_DVY")
    assert 'disableAI "FSM"' in sqf and "EachFrame" in sqf
    print("[3] arm_agents_sqf : coupe FSM/ANIM/AUTOCOMBAT + EachFrame OK (%d car.)" % len(sqf))
    print("=== SELF-TEST OK : perception vectorisee correcte, 100 agents temps reel, LAMBS coupable ===")


if __name__ == "__main__":
    _selftest()
