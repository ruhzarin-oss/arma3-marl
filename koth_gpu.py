"""koth_gpu — champ de bataille KotH 3 camps ENTIEREMENT sur GPU (tenseurs PyTorch, aucun aller-retour CPU).
But : faire de la 3090 le MOTEUR. Des dizaines de milliers de batailles en parallele, sim + cerveaux sur le meme device.
Memes regles que toy_koth3 (4 macros, colline centrale, ennemi=union des 2 autres, controle, capture). obs 10."""
import math
import torch


class KothGPU:
    def __init__(self, num_envs=32768, n=3, camps=3, obj_dist=140.0, move=20.0, sup_range=120.0,
                 threat_range=90.0, secure_r=20.0, secure_n=2, max_steps=120, dmg_dead=0.7, cap_need=6, rot_period=14,
                 hit=0.15, beta=0.25, kappa=0.12, tie_pen=0.15, spawn_jit=0.0, sight=1e9, occ=False,
                 econ=True, xp_step=4.0, max_level=5, tier_cost=8.0, max_tier=4, lvl_dmg=0.20, tier_dmg=0.35,
                 tier_armor=0.13, tier_range=0.25, k_xp=10.0, k_money=15.0, zone_money=3.0, base_money=0.0, base_xp=0.0, income_r=80.0, zone_xp=1.5, device="cuda:0", seed=0):
        self.dev = device; self.N = num_envs; self.A = n; self.C = camps
        self.obj_dist = obj_dist; self.move = move; self.sup_range = sup_range; self.threat_range = threat_range
        self.secure_r = secure_r; self.secure_n = secure_n; self.max_steps = max_steps; self.dmg_dead = dmg_dead
        self.cap_need = cap_need; self.rot_period = rot_period
        self.hit = hit; self.beta = beta; self.kappa = kappa; self.tie_pen = tie_pen; self.spawn_jit = spawn_jit
        self.scale = float(obj_dist); self.n_actions = 4; self.sight = sight; self.occ = occ; self.obs_dim = 11 if occ else 10
        self.econ = econ; self.xp_step = xp_step; self.max_level = float(max_level); self.tier_cost = tier_cost; self.max_tier = float(max_tier)
        self.lvl_dmg = lvl_dmg; self.tier_dmg = tier_dmg; self.tier_armor = tier_armor; self.tier_range = tier_range
        self.k_xp = k_xp; self.k_money = k_money; self.zone_money = zone_money; self.base_money = base_money; self.base_xp = base_xp; self.income_r = income_r; self.zone_xp = zone_xp
        self.g = torch.Generator(device=device).manual_seed(seed)
        N, A, C = num_envs, n, camps; d = device
        self.ox = torch.zeros(N, device=d); self.oy = torch.zeros(N, device=d)
        self.px = torch.zeros(C, N, A, device=d); self.py = torch.zeros(C, N, A, device=d)
        self.dmg = torch.zeros(C, N, A, device=d); self.supp = torch.zeros(C, N, A, device=d)
        self.t = torch.zeros(N, dtype=torch.long, device=d)
        self.prev_d = torch.zeros(C, N, device=d); self.ctrl_time = torch.zeros(C, N, device=d)
        self.cap_prog = torch.zeros(N, device=d); self.cap_owner = torch.full((N,), -1, dtype=torch.long, device=d)
        # économie par agent : niveau (via XP), argent, tier d'équipement (acheté)
        self.level = torch.ones(C, N, A, device=d); self.xp = torch.zeros(C, N, A, device=d)
        self.money = torch.zeros(C, N, A, device=d); self.tier = torch.zeros(C, N, A, device=d)
        # index fixes pour l'union des camps adverses
        self.camp_of = {s: torch.cat([torch.full((A,), o, dtype=torch.long, device=d) for o in self._others(s)]) for s in range(C)}
        self.loc_of = {s: torch.cat([torch.arange(A, device=d) for _ in self._others(s)]) for s in range(C)}
        self._reset_rows(torch.arange(N, device=d))

    def _others(self, s): return [c for c in range(self.C) if c != s]
    def _alive(self, c): return self.dmg[c] < self.dmg_dead

    def _dist(self, c):
        al = self._alive(c).float()
        dd = torch.sqrt((self.px[c] - self.ox[:, None]) ** 2 + (self.py[c] - self.oy[:, None]) ** 2) / self.scale
        den = al.sum(1); return torch.where(den > 0, (dd * al).sum(1) / den.clamp(min=1), torch.zeros_like(den))

    def _reset_rows(self, idx):
        n = idx.numel()
        if n == 0: return
        A, C, d = self.A, self.C, self.dev
        cx = torch.rand(n, generator=self.g, device=d) * 60 - 30; cy = torch.rand(n, generator=self.g, device=d) * 60 - 30
        self.ox[idx] = cx; self.oy[idx] = cy; ar = torch.arange(A, device=d).float()
        for c in range(C):
            ang = 2.0 * math.pi * c / C + math.pi / 2.0
            rad = self.obj_dist * (1.0 + self.spawn_jit * (torch.rand(n, generator=self.g, device=d) * 2 - 1))
            bx = cx + rad * math.cos(ang); by = cy + rad * math.sin(ang)
            self.px[c, idx] = bx[:, None] + (ar % 2) * 6.0 - 3.0
            self.py[c, idx] = by[:, None] + (ar - 1) * 8.0
            self.dmg[c, idx] = 0.0; self.supp[c, idx] = 0.0; self.ctrl_time[c, idx] = 0.0
        self.t[idx] = 0; self.cap_prog[idx] = 0.0; self.cap_owner[idx] = -1
        self.level[:, idx] = 1.0; self.xp[:, idx] = 0.0; self.money[:, idx] = 0.0; self.tier[:, idx] = 0.0
        for c in range(C):
            px = self.px[c, idx]; py = self.py[c, idx]; al = (self.dmg[c, idx] < self.dmg_dead).float()
            dd = torch.sqrt((px - self.ox[idx, None]) ** 2 + (py - self.oy[idx, None]) ** 2) / self.scale
            den = al.sum(1); self.prev_d[c, idx] = torch.where(den > 0, (dd * al).sum(1) / den.clamp(min=1), torch.zeros_like(den))

    def reset(self): return tuple(self._obs(c) for c in range(self.C))

    def _obs(self, s):
        S, A, N, d = self.scale, self.A, self.N, self.dev; al = self._alive(s)
        ox = (self.px[s] - self.ox[:, None]) / S; oy = (self.py[s] - self.oy[:, None]) / S
        dgx = (self.ox[:, None] - self.px[s]) / S; dgy = (self.oy[:, None] - self.py[s]) / S
        dx = self.px[s].unsqueeze(1) - self.px[s].unsqueeze(2); dy = self.py[s].unsqueeze(1) - self.py[s].unsqueeze(2)
        eye = torch.eye(A, dtype=torch.bool, device=d).unsqueeze(0); deadj = (~al).unsqueeze(1).expand(N, A, A)
        BIG = torch.tensor(1e18, device=d)
        d2 = torch.where(eye | deadj, BIG, dx * dx + dy * dy); jm = d2.argmin(2)
        adx = torch.gather(dx, 2, jm.unsqueeze(2)).squeeze(2) / S; ady = torch.gather(dy, 2, jm.unsqueeze(2)).squeeze(2) / S
        nm = d2.min(2).values >= 1e18; adx = adx.masked_fill(nm, 0.0); ady = ady.masked_fill(nm, 0.0)
        others = self._others(s)
        epx = torch.cat([self.px[o] for o in others], 1); epy = torch.cat([self.py[o] for o in others], 1)
        eal = torch.cat([self._alive(o) for o in others], 1); esp = torch.cat([self.supp[o] for o in others], 1)
        ex = epx.unsqueeze(1) - self.px[s].unsqueeze(2); ey = epy.unsqueeze(1) - self.py[s].unsqueeze(2)
        ed2 = torch.where(eal.unsqueeze(1), ex * ex + ey * ey, BIG); km = ed2.argmin(2)
        edx = torch.gather(ex, 2, km.unsqueeze(2)).squeeze(2) / S; edy = torch.gather(ey, 2, km.unsqueeze(2)).squeeze(2) / S
        nd = ed2.min(2).values >= 1e18; edx = edx.masked_fill(nd, 0.0); edy = edy.masked_fill(nd, 0.0)
        esupp = torch.gather(esp, 1, km)
        if self.occ:
            seen = (torch.sqrt(ed2.min(2).values) <= self.sight).float()
            edx = edx * seen; edy = edy * seen; esupp = esupp * seen
            return torch.stack([ox, oy, dgx, dgy, al.float(), adx, ady, edx, edy, esupp, seen], dim=2)
        return torch.stack([ox, oy, dgx, dgy, al.float(), adx, ady, edx, edy, esupp], dim=2)

    def _apply(self, s, a):
        al = self._alive(s); supp_act = (a == 2) & al
        for o in self._others(s):
            ex = self.px[o].unsqueeze(2) - self.px[s].unsqueeze(1); ey = self.py[o].unsqueeze(2) - self.py[s].unsqueeze(1)
            within = ((ex * ex + ey * ey) <= self.sup_range ** 2) & supp_act.unsqueeze(1)
            self.supp[o] = torch.maximum(self.supp[o], within.any(2).float())
        tox = self.ox[:, None] - self.px[s]; toy = self.oy[:, None] - self.py[s]
        tn = torch.sqrt(tox * tox + toy * toy) + 1e-6
        spd = torch.zeros(self.N, self.A, device=self.dev); spd = torch.where(a == 1, torch.full_like(spd, self.move), spd)
        spd = torch.where(a == 3, torch.full_like(spd, self.move * 0.5), spd)
        alf = al.float(); self.px[s] = self.px[s] + (tox / tn) * spd * alf; self.py[s] = self.py[s] + (toy / tn) * spd * alf
        return (a == 3).float()

    def scripted_acts(self):
        # politique SCRIPTEE vectorisee : couvert si blesse, supprimer si ennemi proche, sinon avancer vers la zone
        BIG = torch.tensor(1e18, device=self.dev); acts = []
        for c in range(self.C):
            others = self._others(c)
            epx = torch.cat([self.px[o] for o in others], 1); epy = torch.cat([self.py[o] for o in others], 1)
            eal = torch.cat([self._alive(o) for o in others], 1)
            ex = epx.unsqueeze(1) - self.px[c].unsqueeze(2); ey = epy.unsqueeze(1) - self.py[c].unsqueeze(2)
            ed2 = torch.where(eal.unsqueeze(1), ex * ex + ey * ey, BIG)
            nd = torch.sqrt(ed2.min(2).values)
            hurt = self.dmg[c] > 0.5 * self.dmg_dead; near = nd < self.sup_range
            a = torch.ones(self.N, self.A, dtype=torch.long, device=self.dev)  # 1 = AVANCER
            a = torch.where(near, torch.full_like(a, 2), a)                    # 2 = SUPPRESSER
            a = torch.where(hurt, torch.full_like(a, 3), a)                    # 3 = COUVERT
            acts.append(a)
        return acts

    def step(self, acts, auto_reset=True):
        N, A, C, d = self.N, self.A, self.C, self.dev
        self.supp.zero_()
        cov = [self._apply(s, acts[s]) for s in range(C)]
        BIG = torch.tensor(1e18, device=d)
        dmgbuf = [torch.zeros(N, A, device=d) for _ in range(C)]
        for s in range(C):
            others = self._others(s)
            epx = torch.cat([self.px[o] for o in others], 1); epy = torch.cat([self.py[o] for o in others], 1)
            eal = torch.cat([self._alive(o) for o in others], 1); ecov = torch.cat([cov[o] for o in others], 1)
            ex = epx.unsqueeze(1) - self.px[s].unsqueeze(2); ey = epy.unsqueeze(1) - self.py[s].unsqueeze(2)
            ed2 = torch.where(eal.unsqueeze(1), ex * ex + ey * ey, BIG)
            shoot = (self.supp[s] < 0.5).float() * self._alive(s).float()
            km = ed2.argmin(2); nd = torch.sqrt(ed2.min(2).values)
            rng = self.threat_range * (1.0 + self.tier_range * self.tier[s]) if self.econ else self.threat_range
            exp = (1.0 - nd / rng).clamp(0.0, 1.0) * shoot
            covt = torch.gather(ecov, 1, km); dmgval = exp * self.hit * (1.0 - 0.6 * covt)
            if self.econ:
                atk = 1.0 + self.lvl_dmg * (self.level[s] - 1.0) + self.tier_dmg * self.tier[s]   # plus fort = niveau + tier
                etier = torch.cat([self.tier[o] for o in others], 1); dtier = torch.gather(etier, 1, km)
                dmgval = dmgval * atk * (1.0 - self.tier_armor * dtier).clamp(min=0.1)            # armure du defenseur
                self.xp[s] = self.xp[s] + self.k_xp * dmgval; self.money[s] = self.money[s] + self.k_money * dmgval
            tcamp = self.camp_of[s][km]; tloc = self.loc_of[s][km]
            for o in others:
                dmgbuf[o].scatter_add_(1, tloc, dmgval * (tcamp == o).float())
        for c in range(C):
            self.dmg[c] = torch.minimum(torch.full_like(self.dmg[c], 0.85), self.dmg[c] + dmgbuf[c])
        self.t = self.t + 1
        # rotation de la zone tous les rot_period pas -> force le deplacement / re-contest
        if self.rot_period > 0:
            rot = ((self.t % self.rot_period) == 0) & (self.t > 0)
            ridx = rot.nonzero(as_tuple=True)[0]
            if ridx.numel() > 0:
                self.ox[ridx] = torch.rand(ridx.numel(), generator=self.g, device=d) * 120 - 60
                self.oy[ridx] = torch.rand(ridx.numel(), generator=self.g, device=d) * 120 - 60
                self.cap_prog[ridx] = 0.0; self.cap_owner[ridx] = -1
                for c in range(C):  # recale la distance de shaping sur la nouvelle zone
                    px = self.px[c, ridx]; py = self.py[c, ridx]; al = self._alive(c)[ridx].float()
                    dd = torch.sqrt((px - self.ox[ridx, None]) ** 2 + (py - self.oy[ridx, None]) ** 2) / self.scale
                    den = al.sum(1); self.prev_d[c, ridx] = torch.where(den > 0, (dd * al).sum(1) / den.clamp(min=1), torch.zeros_like(den))
        inobj = []
        for c in range(C):
            d2 = (self.px[c] - self.ox[:, None]) ** 2 + (self.py[c] - self.oy[:, None]) ** 2
            inm = (d2 <= self.secure_r ** 2) & self._alive(c)
            ino = inm.sum(1).float(); inobj.append(ino); self.ctrl_time[c] = self.ctrl_time[c] + ino
            if self.econ:  # revenu = présence dans l'AO (rayon income_r) + combat (plus haut). PAS de salaire de base.
                inc_m = (d2 <= self.income_r ** 2) & self._alive(c)
                self.money[c] = self.money[c] + self.zone_money * inc_m.float()
                self.xp[c] = self.xp[c] + self.zone_xp * inc_m.float()
        inobj_t = torch.stack(inobj)
        if self.econ:  # progression : XP -> niveau ; argent -> achat auto d'equipement (tier)
            for c in range(C):
                al = self._alive(c).float()
                self.xp[c] = self.xp[c] + self.base_xp * al; self.money[c] = self.money[c] + self.base_money * al  # salaire de base par agent vivant
                self.level[c] = (1.0 + torch.floor(self.xp[c] / self.xp_step)).clamp(max=self.max_level)
                buy = torch.floor(self.money[c] / self.tier_cost).clamp(min=0.0)
                buy = torch.minimum(buy, self.max_tier - self.tier[c]).clamp(min=0.0)
                self.tier[c] = self.tier[c] + buy; self.money[c] = self.money[c] - buy * self.tier_cost
        alive_camp = torch.stack([self._alive(c).any(1) for c in range(C)]); n_alive = alive_camp.sum(0)
        timeout = self.t >= self.max_steps
        sec = torch.zeros(C, N, dtype=torch.bool, device=d)
        for c in range(C):
            others_lt = torch.stack([inobj[o] < self.secure_n for o in self._others(c)]).all(0)
            sec[c] = (inobj[c] >= self.secure_n) & others_lt
        sec_any = sec.any(0)
        # barre de capture : il faut DOMINER (sec) pendant cap_need pas pour capturer ; zone contestee -> la barre decroit
        dom = torch.full((N,), -1, dtype=torch.long, device=d)
        for c in range(C):
            dom = torch.where(sec[c], torch.full_like(dom, c), dom)
        has_dom = dom >= 0; same = has_dom & (dom == self.cap_owner); newd = has_dom & (dom != self.cap_owner)
        inc = 1.0 / float(max(1, self.cap_need))
        self.cap_prog = torch.where(same, self.cap_prog + inc,
                          torch.where(newd, torch.full_like(self.cap_prog, inc),
                          torch.where(has_dom, self.cap_prog, (self.cap_prog - 0.5 * inc).clamp(min=0.0))))
        self.cap_owner = torch.where(newd, dom, self.cap_owner)
        captured = self.cap_prog >= 1.0
        ct = self.ctrl_time; mx = ct.max(0).values; n_max = (ct == mx).sum(0)
        m1 = torch.full((N,), -1, dtype=torch.long, device=d)
        ct_winner = torch.where(n_max == 1, ct.argmax(0), m1)
        sole_alive = torch.where(n_alive == 1, alive_camp.float().argmax(0), m1)
        winner = m1.clone()
        winner = torch.where(captured, self.cap_owner, winner)
        winner = torch.where((winner == -1) & (n_alive == 1), sole_alive, winner)
        winner = torch.where((winner == -1) & timeout & (n_max == 1), ct_winner, winner)
        decided = winner >= 0
        done = captured | timeout | (n_alive <= 1)
        rew = []
        mean_in = inobj_t.sum(0)
        for c in range(C):
            cur = self._dist(c); sh = self.beta * (self.prev_d[c] - cur); self.prev_d[c] = cur
            others_in = (mean_in - inobj[c]) / max(1, C - 1); ctrl = self.kappa * (inobj[c] - others_in)
            wterm = torch.where(winner == c, torch.ones_like(cur), torch.where(decided, torch.full_like(cur, -0.5), torch.zeros_like(cur)))
            tie = (done & (~decided)).float()
            rew.append(sh - 0.005 + ctrl + wterm - self.tie_pen * tie)
        info = {"winner": winner, "decided": decided, "secured": captured, "occ": inobj_t.sum(0), "cap": self.cap_prog.mean(),
                "lvl": self.level.mean(), "tier": self.tier.mean(), "money": self.money.mean()}
        done_f = done.float()
        if auto_reset:
            self._reset_rows(done.nonzero(as_tuple=True)[0])
        return tuple(self._obs(c) for c in range(C)), tuple(rew), done_f, info
