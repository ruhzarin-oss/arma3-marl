"""geo_gpu — SANDBOX GÉOPOLITIQUE abstrait sur GPU (tenseurs PyTorch, 100% device).
v4 « CIVILS » : N pays = arcs d'un ANNEAU de régions ; 1 COLLINE/pays (≠ capitale) ; VICTOIRE = tenir
2 collines simultanément hold_T pas ; capitale = MORT. DOCTRINES d'allocation du trésor par pays :
  A=AMPLIFICATEUR (tout sur sa pointe la + forte), E=ÉGALISEUR (uniforme sur le front),
  Z=ZÉRO-SOMME/DÉNI (tout face à la + grosse force ennemie — réactif).
NOUVEAU v4 — POPULATION CIVILE par région (l'économie devient ENDOGÈNE) :
  · PRODUIRE : revenu = income_pp × pop des régions tenues (remplace la rente territoriale) ;
    la population occupée produit pour l'occupant (extraction — hypothèse assumée, pas de « loyauté »).
  · FUIR : fraction ∝ menace locale (force ennemie adjacente vs force amie) vers la région voisine du
    MÊME camp la moins menacée ; pas d'issue (encerclé) = piégé. Les civils voient les pointes se masser.
  · MOURIR : civ_loss de la pop d'une région à chaque changement de mains.
But : dynamiques émergentes de population (réfugiés, concentration intérieure, capture du tissu fiscal,
victoires à la Pyrrhus) et leur interaction avec doctrines + règle des 2 collines. Tout SCRIPTÉ."""
import torch


class GeoGPU:
    def __init__(self, num_envs=8192, n_countries=3, arc=4, income_pp=0.05, atk_thresh=1.1, push=0.5,
                 hills_needed=2, hold_T=5, doctrines=None, pop_base=10.0, pop_capital=20.0,
                 civ_flee=0.5, civ_loss=0.2, max_steps=80, device="cuda:0", seed=0):
        self.dev = device; self.N = num_envs; self.C = n_countries; self.arc = arc
        self.R = n_countries * arc
        self.income_pp = income_pp; self.atk = atk_thresh; self.push = push
        self.hills_needed = hills_needed; self.hold_T = hold_T; self.max_steps = max_steps
        self.pop_base = pop_base; self.pop_capital = pop_capital
        self.civ_flee = civ_flee; self.civ_loss = civ_loss
        self.doctrines = (doctrines or "A" * n_countries).upper()
        assert len(self.doctrines) == n_countries and set(self.doctrines) <= set("AEZD"), "doctrines = chaîne en A/E/Z, une par pays"
        self.g = torch.Generator(device=device).manual_seed(seed)
        self.base_owner = (torch.arange(self.R, device=device) // arc).long()
        self.capital = torch.tensor([c * arc + arc // 2 for c in range(self.C)], device=device)
        off = 1 if arc // 2 != 1 else 0                       # colline ≠ capitale (asymétrie assumée)
        self.hill = torch.tensor([c * arc + off for c in range(self.C)], device=device)
        self.cidx = torch.arange(self.C, device=device); self.ar = torch.arange(num_envs, device=device)
        self.owner = torch.zeros(num_envs, self.R, dtype=torch.long, device=device)
        self.force = torch.zeros(num_envs, self.R, device=device)
        self.treasury = torch.zeros(num_envs, self.C, device=device)
        self.hold = torch.zeros(num_envs, self.C, device=device)
        self.pop = torch.zeros(num_envs, self.R, device=device)            # population civile par région
        self.civ_dead = torch.zeros(num_envs, device=device)               # morts civils cumulés
        self.civ_moved = torch.zeros(num_envs, device=device)              # déplacements cumulés (réfugiés)
        self.pop0_total = pop_base * (self.R - self.C) + pop_capital * self.C   # pop mondiale initiale
        self.t = torch.zeros(num_envs, dtype=torch.long, device=device)
        R = self.R
        self.even = [(i, (i + 1) % R) for i in range(0, R, 2)]
        self.odd = [(i, (i + 1) % R) for i in range(1, R, 2)]
        self._reset(torch.arange(num_envs, device=device))

    def _reset(self, idx):
        if idx.numel() == 0: return
        self.owner[idx] = self.base_owner[None, :]
        f = torch.full((idx.numel(), self.R), 3.0, device=self.dev); f[:, self.capital] = 8.0
        f = f * (0.85 + 0.3 * torch.rand(idx.numel(), self.R, generator=self.g, device=self.dev))
        self.force[idx] = f; self.treasury[idx] = 0.0; self.hold[idx] = 0.0; self.t[idx] = 0
        p = torch.full((idx.numel(), self.R), self.pop_base, device=self.dev)
        p[:, self.capital] = self.pop_capital
        self.pop[idx] = p; self.civ_dead[idx] = 0.0; self.civ_moved[idx] = 0.0

    def alive(self):  # pays vivant s'il tient sa capitale
        return self.owner[:, self.capital] == self.cidx[None, :]   # (N, C)

    def _edges(self, edges):
        for i, j in edges:
            oi = self.owner[:, i].clone(); oj = self.owner[:, j].clone()
            fi = self.force[:, i].clone(); fj = self.force[:, j].clone()
            diff = oi != oj
            ip = diff & (fi > fj * self.atk); jp = diff & (fj > fi * self.atk) & (~ip)
            self.owner[:, j] = torch.where(ip, oi, self.owner[:, j])
            self.force[:, j] = torch.where(ip, (fi - fj) * self.push, self.force[:, j])
            self.force[:, i] = torch.where(ip, fi * self.push, self.force[:, i])
            self.owner[:, i] = torch.where(jp, oj, self.owner[:, i])
            self.force[:, i] = torch.where(jp, (fj - fi) * self.push, self.force[:, i])
            self.force[:, j] = torch.where(jp, fj * self.push, self.force[:, j])
            lost_j = self.pop[:, j] * self.civ_loss * ip.float()           # pertes civiles à la prise
            lost_i = self.pop[:, i] * self.civ_loss * jp.float()
            self.pop[:, j] = self.pop[:, j] - lost_j; self.pop[:, i] = self.pop[:, i] - lost_i
            self.civ_dead = self.civ_dead + lost_j + lost_i

    def civ_obs(self):
        """Observations CIVILES par région (N, R, 9) + masques d'issue même-camp. Locales, normalisées."""
        left = torch.roll(self.owner, 1, 1); right = torch.roll(self.owner, -1, 1)
        fl = torch.roll(self.force, 1, 1); fr = torch.roll(self.force, -1, 1)
        tl = torch.where(left != self.owner, fl, torch.zeros_like(fl))
        tr = torch.where(right != self.owner, fr, torch.zeros_like(fr))
        lok = (left == self.owner).float(); rok = (right == self.owner).float()
        iscap = torch.zeros_like(self.force); iscap[:, self.capital] = 1.0
        ishill = torch.zeros_like(self.force); ishill[:, self.hill] = 1.0
        obs = torch.stack([self.pop / 10.0, self.force / 10.0, tl / 10.0, tr / 10.0, lok, rok,
                           iscap, ishill, self.t.float()[:, None].expand(-1, self.R) / self.max_steps], 2)
        return obs, lok, rok

    def step(self, auto_reset=True, civ_policy=None):
        owner = self.owner
        terr = torch.stack([(owner == c).sum(1) for c in range(self.C)], 1).float()   # (N, C)
        popc = torch.stack([(self.pop * (owner == c).float()).sum(1) for c in range(self.C)], 1)  # pop contrôlée
        self.treasury = self.treasury + self.income_pp * popc                          # revenu = la population produit
        left = torch.roll(owner, 1, 1); right = torch.roll(owner, -1, 1)
        fl = torch.roll(self.force, 1, 1); fr = torch.roll(self.force, -1, 1)
        neg = torch.full_like(self.force, -1e9)
        for c in range(self.C):                                                        # allouer le trésor selon la DOCTRINE
            ownc = owner == c
            frontier = ownc & ((left != c) | (right != c))
            has = frontier.any(1); d = self.doctrines[c]
            if d == "E":
                nf = frontier.float().sum(1).clamp(min=1.0)
                self.force = self.force + frontier.float() * (self.treasury[:, c] / nf)[:, None]
            else:
                if d == "A":
                    score = torch.where(frontier, self.force, neg)
                elif d == "D":   # DÉNI DE REVENU : vers la région ennemie la + PEUPLÉE (étrangler la base fiscale)
                    pl = torch.roll(self.pop, 1, 1); pr = torch.roll(self.pop, -1, 1)
                    tl = torch.where(left != c, pl, torch.zeros_like(pl))
                    tr = torch.where(right != c, pr, torch.zeros_like(pr))
                    score = torch.where(frontier, torch.maximum(tl, tr), neg)
                else:            # ZÉRO-SOMME/CONTRE-FORCE : face à la + grosse force ennemie
                    tl = torch.where(left != c, fl, torch.zeros_like(fl))
                    tr = torch.where(right != c, fr, torch.zeros_like(fr))
                    score = torch.where(frontier, torch.maximum(tl, tr), neg)
                spear = score.argmax(1)
                add = torch.where(has, self.treasury[:, c], torch.zeros_like(self.treasury[:, c]))
                self.force[self.ar, spear] = self.force[self.ar, spear] + add
            self.treasury[:, c] = torch.where(has, torch.zeros_like(self.treasury[:, c]), self.treasury[:, c])
        # ---- MIGRATION CIVILE (les civils voient les pointes massées : menace = force ennemie adjacente) ----
        if civ_policy is not None:                                                     # politique APPRISE : {0=rester,1=G,2=D}
            obs, lokf, rokf = self.civ_obs()
            acts = civ_policy(obs, lokf, rokf)                                         # (N, R) long
            moving = self.pop * self.civ_flee                                          # quantum fixe : le RL choisit QUAND/OÙ
            goL = (acts == 1) & (lokf > 0); goR = (acts == 2) & (rokf > 0)
            fL = moving * goL.float(); fR = moving * goR.float()
        else:                                                                          # règle SCRIPTÉE
            fl = torch.roll(self.force, 1, 1); fr = torch.roll(self.force, -1, 1)      # recalc après allocation
            tl = torch.where(left != owner, fl, torch.zeros_like(fl))
            tr = torch.where(right != owner, fr, torch.zeros_like(fr))
            threat = torch.maximum(tl, tr)
            frac = self.civ_flee * threat / (threat + self.force + 1.0)                # fuite ∝ déséquilibre local
            moving = self.pop * frac
            lok = left == owner; rok = right == owner                                  # issues du même camp
            thL = torch.roll(threat, 1, 1); thR = torch.roll(threat, -1, 1)            # menace chez les voisins
            goL = lok & ((~rok) | (thL <= thR)); goR = rok & (~goL)
            fL = moving * goL.float(); fR = moving * goR.float()
        self.pop = self.pop - fL - fR + torch.roll(fL, -1, 1) + torch.roll(fR, 1, 1)
        self.civ_moved = self.civ_moved + (fL + fR).sum(1)
        # ---- COMBAT ----
        self._edges(self.even); self._edges(self.odd)
        self.t = self.t + 1
        al = self.alive(); nal = al.sum(1)
        hills_of = self.owner[:, self.hill]
        nh = torch.stack([(hills_of == c).sum(1) for c in range(self.C)], 1).float()
        cond = (nh >= self.hills_needed) & al
        self.hold = (self.hold + 1.0) * cond.float()
        hill_win = self.hold >= self.hold_T
        win_any = hill_win.any(1)
        timeout = self.t >= self.max_steps
        done = (nal <= 1) | win_any | timeout
        terr_alive = torch.where(al, terr, torch.full_like(terr, -1.0))
        winner = torch.where(win_any, hill_win.float().argmax(1), terr_alive.argmax(1))
        win_by = torch.where(win_any, torch.zeros_like(self.t),
                 torch.where(nal <= 1, torch.ones_like(self.t), torch.full_like(self.t, 2)))
        popc_now = torch.stack([(self.pop * (self.owner == c).float()).sum(1) for c in range(self.C)], 1)
        info = {"terr": terr, "alive": al, "nalive": nal, "winner": winner, "win_by": win_by,
                "hills": hills_of, "nhills": nh, "pop_c": popc_now,
                "civ_dead": self.civ_dead.clone(), "civ_moved": self.civ_moved.clone()}
        if auto_reset:
            self._reset(done.nonzero(as_tuple=True)[0])
        return done, info
