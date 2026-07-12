"""leviathan_econ.py — SUBSTRAT v3 : ECONOMIE differenciee (A+B) + RECRUTEMENT.

Ressources DISSEMINEES a defendre, chacune son ROLE :
  - GAZ  (energie)  -> permet de RECRUTER (sans gaz tenu, l'armee stagne).
  - EAU             -> SOUTIENT l'armee : plafond de force = base + par_eau*#eau ; au-dessus -> attrition.
  - PETROLE         -> MOBILITE : convois rapides ; sans petrole, la reserve arrive en retard (eta x2).
Nouvelle DECISION : RECRUTER (niveau 0 / demi / plein) = monter l'armee, borne par le gaz (cadence) et l'eau (plafond).

Action = K tetes de posture {0 TENIR,1 RENFORCER,2 DEGARNIR} + 1 tete RECRUTEMENT {0,1,2}  -> n_heads = K+1.
Ennemi CONCENTRE (Schwerpunkt) herite de l'esprit etage 2. Reuse des mecaniques validees (convois, cascade,
menace anticipee). La 'supply/muns' est fondue dans l'economie (degat = menace).
Vectorise (N mondes GPU), interface compatible avec le trainer PPO (via n_heads + baseline_action).
"""
import math, torch

# STRATIS — toute l'ile : 13 secteurs sur de vraies positions, ressources DISSEMINEES PARTOUT
# (4 petrole + 4 eau + 4 gaz + 1 QG). Plus tu en tiens, plus ton armee grandit (eau->plafond, gaz->financement).
SECTORS = [
    ("AirStationM26", 4900, 6350, "hq"),     # nord : base aerienne = QG
    ("AgiaMarina",    3350, 5600, "oil"),     # cote ouest
    ("Kamino",        1750, 5750, "gas"),     # extreme ouest
    ("Girna",         2950, 6300, "water"),   # nord-ouest
    ("Syrta",         2450, 5100, "oil"),     # ouest
    ("CampMaxwell",   4050, 5450, "water"),   # centre
    ("CampRogain",    5500, 3150, "gas"),     # sud-est
    ("CampTempest",   4600, 3700, "gas"),     # sud
    ("SaltLake",      5050, 4250, "oil"),     # centre-est
    ("RadarNE",       5750, 5900, "water"),   # nord-est
    ("DevilsCastle",  4350, 6500, "gas"),     # cote nord
    ("Theseus",       5950, 4800, "water"),   # est
    ("HarborSud",     5200, 2950, "oil"),     # sud (port)
]


class LeviathanEcon:
    def __init__(self, num_envs, device="cuda:0", threat_rate=0.27, focus_ticks=4,
                 recruit_cap=8.0, gas_per_troop=1.0, gas_income=1.2, gas_cap=40.0,
                 base_cap=40.0, per_water=20.0, speed=1600.0,
                 max_steps=80, secure_min=2, seed=0):
        self.N = num_envs; self.K = len(SECTORS); self.dev = device
        self.n_heads = self.K + 1            # K postures + 1 recrutement
        self.n_actions = 3; self.threat_rate = threat_rate; self.focus_ticks = focus_ticks
        self.recruit_cap = recruit_cap; self.gas_per_troop = gas_per_troop
        self.gas_income = gas_income; self.gas_cap = gas_cap
        self.base_cap = base_cap; self.per_water = per_water
        self.max_steps = max_steps; self.secure_min = secure_min; self.SC = 30.0
        torch.manual_seed(seed)
        self.hq = next(i for i, s in enumerate(SECTORS) if s[3] == "hq")
        role = [s[3] for s in SECTORS]
        self.oil = torch.tensor([r == "oil" for r in role], device=device, dtype=torch.float32)
        self.water = torch.tensor([r == "water" for r in role], device=device, dtype=torch.float32)
        self.gas = torch.tensor([r == "gas" for r in role], device=device, dtype=torch.float32)
        hx, hy = SECTORS[self.hq][1], SECTORS[self.hq][2]
        d = [math.hypot(SECTORS[i][1] - hx, SECTORS[i][2] - hy) for i in range(self.K)]
        self.eta = torch.tensor([max(1, min(3, int(math.ceil(di / speed)))) for di in d], device=device)  # (K,)
        self.L = 6   # pipeline (eta de base 1-3, x2 sans petrole -> jusqu'a 6)
        self.disthq = torch.tensor(d, device=device, dtype=torch.float32) / (speed * 3)
        self.garr0 = torch.full((self.K,), 6.0, device=device); self.garr0[self.hq] = 10.0
        self.obs_dim = self.K * 8 + 8
        dv = device
        self.garr = torch.zeros(self.N, self.K, device=dv); self.owner = torch.zeros(self.N, self.K, device=dv)
        self.threat = torch.zeros(self.N, self.K, device=dv); self.reserve = torch.zeros(self.N, device=dv)
        self.transit = torch.zeros(self.N, self.K, self.L, device=dv)
        self.gas_stock = torch.zeros(self.N, device=dv)
        self.t = torch.zeros(self.N, dtype=torch.long, device=dv); self.prev_force = torch.zeros(self.N, device=dv)
        self.e_target = torch.zeros(self.N, dtype=torch.long, device=dv); self.e_timer = torch.zeros(self.N, dtype=torch.long, device=dv)
        self.reset()

    # ---- helpers economie ----
    def _held(self, mask):
        return (self.owner * mask).sum(1)                 # (N,) nb de sites tenus de ce type

    def _force(self):
        return self.garr.sum(1) + self.reserve + self.transit.sum((1, 2))

    def _roll_threat(self, rows):
        n = rows.numel()
        garr = self.garr[rows].clone(); held = self.owner[rows] > 0
        garr = torch.where(held, garr, torch.full_like(garr, 1e9))
        tgt_held = held.gather(1, self.e_target[rows].unsqueeze(1)).squeeze(1)
        retarget = (self.e_timer[rows] <= 0) | (~tgt_held)
        self.e_target[rows] = torch.where(retarget, garr.argmin(1), self.e_target[rows])
        self.e_timer[rows] = torch.where(retarget, torch.full_like(self.e_timer[rows], self.focus_ticks), self.e_timer[rows] - 1)
        intensity = 10.0 * self.threat_rate
        thr = torch.zeros(n, self.K, device=self.dev)
        thr.scatter_(1, self.e_target[rows].unsqueeze(1), torch.full((n, 1), intensity, device=self.dev))
        probe = (torch.rand(n, self.K, device=self.dev) < 0.25 * self.threat_rate) & held
        thr = thr + probe.float() * torch.rand(n, self.K, device=self.dev) * 2.0
        self.threat[rows] = self.threat[rows] * 0.4 + thr * held.float()

    def reset(self, idx=None):
        if idx is None:
            idx = torch.arange(self.N, device=self.dev)
        self.garr[idx] = self.garr0.unsqueeze(0); self.owner[idx] = 1.0; self.threat[idx] = 0.0
        self.reserve[idx] = 12.0; self.transit[idx] = 0.0; self.gas_stock[idx] = 8.0; self.t[idx] = 0
        self.e_target[idx] = int(self.garr0.argmin().item()); self.e_timer[idx] = 0
        self._roll_threat(idx)
        self.prev_force[idx] = self._force()[idx]
        return self._obs()

    def _obs(self):
        SC = self.SC; N, K = self.N, self.K
        per = torch.stack([self.owner, self.garr / SC, self.threat / 8.0,
                           self.oil.expand(N, K), self.water.expand(N, K), self.gas.expand(N, K),
                           (self.gather_eta() / self.L), self.disthq.expand(N, K)], dim=2).reshape(N, K * 8)
        cap = self.base_cap + self.per_water * self._held(self.water)
        glob = torch.stack([self.reserve / SC, self._held(self.oil) / 4.0, self._held(self.water) / 4.0,
                            self._held(self.gas) / 4.0, cap / SC, self._force() / SC,
                            self.gas_stock / self.gas_cap, self.t.float() / self.max_steps], dim=1)
        return torch.cat([per, glob], dim=1)

    def gather_eta(self):
        # eta effectif par (monde, secteur) : x2 si pas de petrole tenu
        mult = torch.where(self._held(self.oil) > 0, torch.ones(self.N, device=self.dev), torch.full((self.N,), 2.0, device=self.dev))
        return (self.eta.unsqueeze(0).float() * mult.unsqueeze(1))

    def baseline_action(self):
        # BASELINE : RENFORCER le secteur tenu le plus faible, TENIR ailleurs, RECRUTER a fond
        a = torch.zeros(self.N, self.n_heads, dtype=torch.long, device=self.dev)
        g = self.garr.clone(); g[self.owner <= 0] = 1e9
        a[torch.arange(self.N, device=self.dev), g.argmin(1)] = 1
        a[:, self.K] = 2   # recrutement plein
        return a

    def step(self, action, auto_reset=True):
        a = action.long(); ap = a[:, :self.K]; rec = a[:, self.K]; held = self.owner > 0
        # 1) DEGAT (menace courante, visible le tick d'avant)
        self.garr = self.garr - self.threat * held.float()
        # 2) RECRUTEMENT : COUTE du gaz (stock consomme) -> vraie decision (recruter MAINTENANT vs banquer)
        gas_h = self._held(self.gas)
        self.gas_stock = torch.minimum(self.gas_stock + self.gas_income * gas_h, torch.full_like(self.gas_stock, self.gas_cap))
        desired = (rec.float() * 0.5) * self.recruit_cap          # troupes voulues : 0 / demi / plein
        afford = torch.minimum(desired, self.gas_stock / self.gas_per_troop)
        self.gas_stock = self.gas_stock - afford * self.gas_per_troop
        self.reserve = self.reserve + afford
        # 3) DEGARNIR -> repli vers reserve ; RENFORCER -> route la reserve (eta selon petrole)
        thin = ((ap == 2) & held).float(); pulled = self.garr * 0.5 * thin
        self.garr = self.garr - pulled; self.reserve = self.reserve + pulled.sum(1)
        want = ((ap == 1) & held).float(); wsum = want.sum(1, keepdim=True)
        send_total = torch.minimum(self.reserve, torch.full_like(self.reserve, 14.0))
        send = send_total.unsqueeze(1) * want / wsum.clamp(min=1.0); send = send * (wsum > 0).float()
        self.reserve = self.reserve - send.sum(1)
        slot = (self.gather_eta().long() - 1).clamp(0, self.L - 1)             # (N,K) slot d'arrivee
        self.transit.scatter_add_(2, slot.unsqueeze(2), send.unsqueeze(2))
        # 4) EAU : plafond de force ; au-dessus -> attrition (on ne nourrit pas)
        cap = self.base_cap + self.per_water * self._held(self.water)
        over = torch.clamp(self._force() - cap, min=0.0)
        from_res = torch.minimum(self.reserve, over); self.reserve = self.reserve - from_res
        rem = over - from_res                                                  # reste a prelever sur les garnisons
        gsum = self.garr.sum(1).clamp(min=1e-6)
        self.garr = self.garr - self.garr * (rem / gsum).unsqueeze(1) * held.float()
        # 5) CONVOIS arrivent
        arrive = self.transit[:, :, 0].clone()
        self.transit[:, :, :-1] = self.transit[:, :, 1:].clone(); self.transit[:, :, -1] = 0.0
        self.garr = self.garr + arrive * held.float()
        self.reserve = self.reserve + (arrive * (~held).float()).sum(1)
        # 6) SECTEURS TOMBES
        fell = held & (self.garr <= 0)
        self.owner = torch.where(fell, torch.zeros_like(self.owner), self.owner)
        self.garr = torch.clamp(self.garr, min=0.0)
        # 7) menace du prochain tick (anticipation)
        self._roll_threat(torch.arange(self.N, device=self.dev))
        self.t = self.t + 1
        # RECOMPENSE prosperer : tenir + une armee vivante - pertes - effondrement
        held_cnt = self.owner.sum(1); force = self._force()
        losses = torch.clamp(self.prev_force - force, min=0.0); self.prev_force = force
        elim = (held_cnt < self.secure_min) | (self.owner[:, self.hq] <= 0)
        timeout = self.t >= self.max_steps; done = elim | timeout
        rew = 0.08 * held_cnt + 0.02 * (force / self.SC) - 0.04 * losses - 0.01 - 3.0 * elim.float()
        info = {"held": held_cnt.detach(), "survived": (~elim).detach(), "force": force.detach(),
                "oil": self._held(self.oil).detach(), "water": self._held(self.water).detach(), "gas": self._held(self.gas).detach()}
        di = torch.where(done)[0]
        if auto_reset and di.numel() > 0:
            self.reset(di)
        return self._obs(), rew, done.float(), info


if __name__ == "__main__":   # smoke autonome : rollout aleatoire
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    e = LeviathanEcon(num_envs=2048, device=dev, seed=1)
    print("obs_dim", e.obs_dim, "n_heads", e.n_heads, "K", e.K)
    o = e.reset(); surv = []; r = None
    for _ in range(e.max_steps * 5):
        a = torch.randint(0, 3, (e.N, e.n_heads), device=e.dev)
        o, r, d, info = e.step(a); di = torch.where(d > 0)[0]
        if di.numel() > 0:
            surv.append(info["survived"][di].float())
    import statistics
    print("survie ALEATOIRE =", round(torch.cat(surv).mean().item(), 3))
    print("reward fini ?", bool(torch.isfinite(r).all()), "| obs fini ?", bool(torch.isfinite(o).all()))
    # baseline
    o = e.reset(); surv = []
    for _ in range(e.max_steps * 5):
        a = e.baseline_action(); o, r, d, info = e.step(a); di = torch.where(d > 0)[0]
        if di.numel() > 0:
            surv.append(info["survived"][di].float())
    print("survie BASELINE =", round(torch.cat(surv).mean().item(), 3))
