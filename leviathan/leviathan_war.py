"""leviathan_war.py — ETAGE 3 : DEUX nations LEVIATHAN se font la guerre sur Stratis.

NORD (capitale Air Station Mike-26) vs SUD (capitale Harbor Sud). Carte = SECTORS de leviathan_econ
(ressources disseminees). Chaque nation a SON economie (gaz->recrutement, eau->plafond, petrole->combat),
sa reserve, ses garnisons. Combat aux FRONTIERES (adjacence) : on projette sa garnison sur les secteurs
voisins ; un secteur submerge BASCULE a l'ennemi. Capturer un secteur = capturer sa ressource (snowball).
DEFAITE = ta capitale tombe.

owner (N,K) in {0 neutre, 1 nord, 2 sud}. Action/nation = K postures {0 TENIR,1 RENFORCER,2 DEGARNIR}
+ 1 tete RECRUTEMENT -> n_heads = K+1. step(a_nord, a_sud) -> obs_n, obs_s, rew_n, rew_s, done, info.
Vectorise (N mondes GPU). Pour l'apprentissage : co-evolution alternee + league (a venir).
"""
import math, torch
from leviathan_econ import SECTORS   # meme carte Stratis (13 secteurs, ressources partout)


class LeviathanWar:
    def __init__(self, num_envs, device="cuda:0", base_cap=80.0, per_water=18.0,
                 gas_income=1.2, gas_cap=40.0, recruit_cap=8.0, gas_per_troop=1.0,
                 combat=0.13, oil_bonus=0.14, neutral_garr=5.0, max_steps=120,
                 score_target=700.0, upkeep=0.25, seed=0):
        self.N = num_envs; self.K = len(SECTORS); self.dev = device
        self.n_heads = self.K + 1; self.n_actions = 3
        self.score_target = score_target; self.upkeep = upkeep
        self.base_cap = base_cap; self.per_water = per_water
        self.gas_income = gas_income; self.gas_cap = gas_cap
        self.recruit_cap = recruit_cap; self.gas_per_troop = gas_per_troop
        self.combat = combat; self.oil_bonus = oil_bonus; self.neutral_garr = neutral_garr
        self.max_steps = max_steps; self.SC = 30.0
        torch.manual_seed(seed)
        role = [s[3] for s in SECTORS]; dv = device
        self.oil = torch.tensor([r == "oil" for r in role], device=dv, dtype=torch.float32)
        self.water = torch.tensor([r == "water" for r in role], device=dv, dtype=torch.float32)
        self.gas = torch.tensor([r == "gas" for r in role], device=dv, dtype=torch.float32)
        self.cap_n = next(i for i, s in enumerate(SECTORS) if s[0] == "AirStationM26")
        self.cap_s = next(i for i, s in enumerate(SECTORS) if s[0] == "HarborSud")
        for m in (self.oil, self.water, self.gas):   # les capitales ne comptent PAS comme ressource (equite)
            m[self.cap_n] = 0.0; m[self.cap_s] = 0.0
        xy = torch.tensor([[s[1], s[2]] for s in SECTORS], device=dv, dtype=torch.float32)
        d = torch.cdist(xy, xy)                                   # (K,K) distances
        self.adj = ((d > 0) & (d < 2300.0)).float()              # voisins Stratis
        self.adjn = self.adj / self.adj.sum(1, keepdim=True).clamp(min=1.0)   # projection REPARTIE (anti-runaway)
        self.lat = xy[:, 1]                                       # latitude (Y) : nord = haut
        order = torch.argsort(self.lat, descending=True)          # du plus nord au plus sud
        oi = torch.zeros(self.K, device=dv)
        oi[order[:5]] = 1.0                                       # 5 plus au nord = NORD
        oi[order[-5:]] = 2.0                                      # 5 plus au sud = SUD ; milieu (3) neutre
        self.own_init = oi                                        # depart SYMETRIQUE (5/5/3)
        # etat
        self.owner = torch.zeros(self.N, self.K, device=dv)
        self.garr = torch.zeros(self.N, self.K, device=dv)
        self.reserve = torch.zeros(self.N, 2, device=dv)
        self.gas_stock = torch.zeros(self.N, 2, device=dv)
        self.t = torch.zeros(self.N, dtype=torch.long, device=dv)
        self.prevf = torch.zeros(self.N, 2, device=dv)
        self.score = torch.zeros(self.N, 2, device=dv)
        self.obs_dim = self.K * 8 + 9
        self.reset()

    def _mask(self, f):  # f=0 nord(1), f=1 sud(2)
        return (self.owner == (f + 1)).float()

    def _count(self, mask, f):
        return (mask * self._mask(f)).sum(1)

    def _force(self, f):
        return (self.garr * self._mask(f)).sum(1) + self.reserve[:, f]

    def reset(self, idx=None):
        if idx is None:
            idx = torch.arange(self.N, device=self.dev)
        # DEPART SYMETRIQUE A EGALITE : chaque camp ne tient QUE sa capitale (meme grosse armee),
        # tout le reste NEUTRE. Les deux partent en meme temps et RACE pour prendre le controle -> pas d'avantage.
        own = torch.zeros(self.K, device=self.dev); own[self.cap_n] = 1.0; own[self.cap_s] = 2.0
        self.owner[idx] = own.unsqueeze(0)
        g = torch.full((self.K,), self.neutral_garr, device=self.dev)
        g[self.cap_n] = 50.0; g[self.cap_s] = 50.0    # l'armee de depart, egale, a la capitale
        self.garr[idx] = g.unsqueeze(0)
        self.reserve[idx] = 30.0; self.gas_stock[idx] = 8.0; self.t[idx] = 0; self.score[idx] = 0.0
        for f in range(2):
            self.prevf[idx, f] = self._force(f)[idx]
        return self._obs(0), self._obs(1)

    def _obs(self, f):
        SC = self.SC; e = 1 - f
        mine = self._mask(f); enemy = self._mask(e); neu = (self.owner == 0).float()
        epress = (self.garr * enemy) @ self.adjn                 # pression ennemie sur chaque secteur
        per = torch.stack([mine, enemy, neu, self.garr / SC, self.oil.expand(self.N, self.K),
                           self.water.expand(self.N, self.K), self.gas.expand(self.N, self.K),
                           epress / SC], dim=2).reshape(self.N, self.K * 8)
        capme = self.cap_n if f == 0 else self.cap_s; capen = self.cap_s if f == 0 else self.cap_n
        glob = torch.stack([self.reserve[:, f] / SC, self.gas_stock[:, f] / self.gas_cap,
                            self._count(self.water, f) / 4.0, self._count(self.gas, f) / 4.0,
                            (self.owner[:, capme] == (f + 1)).float(),
                            (self.owner[:, capen] == (e + 1)).float(),
                            self.score[:, f] / self.score_target, self.score[:, e] / self.score_target,
                            self.t.float() / self.max_steps], dim=1)
        return torch.cat([per, glob], dim=1)

    def _econ_posture(self, f, a):
        mine = self._mask(f); ap = a[:, :self.K]
        # recrutement (gaz consomme)
        gas_h = self._count(self.gas, f)
        self.gas_stock[:, f] = torch.minimum(self.gas_stock[:, f] + self.gas_income * gas_h,
                                             torch.full_like(self.gas_stock[:, f], self.gas_cap))
        desired = (a[:, self.K].float() * 0.5) * self.recruit_cap
        afford = torch.minimum(desired, self.gas_stock[:, f] / self.gas_per_troop)
        self.gas_stock[:, f] = self.gas_stock[:, f] - afford; self.reserve[:, f] = self.reserve[:, f] + afford
        # DEGARNIR -> reserve ; RENFORCER -> distribue la reserve sur les secteurs tenus marques
        thin = ((ap == 2) & (mine > 0)).float(); pulled = self.garr * 0.5 * thin
        self.garr = self.garr - pulled; self.reserve[:, f] = self.reserve[:, f] + pulled.sum(1)
        want = ((ap == 1) & (mine > 0)).float(); wsum = want.sum(1, keepdim=True)
        send_tot = torch.minimum(self.reserve[:, f], torch.full_like(self.reserve[:, f], 16.0))
        send = send_tot.unsqueeze(1) * want / wsum.clamp(min=1.0); send = send * (wsum > 0).float()
        self.reserve[:, f] = self.reserve[:, f] - send.sum(1); self.garr = self.garr + send
        # EAU : plafond de force
        cap = self.base_cap + self.per_water * self._count(self.water, f)
        over = torch.clamp(self._force(f) - cap, min=0.0)
        fr = torch.minimum(self.reserve[:, f], over); self.reserve[:, f] = self.reserve[:, f] - fr
        rem = (over - fr); gs = (self.garr * mine).sum(1).clamp(min=1e-6)
        self.garr = self.garr - self.garr * mine * (rem / gs).unsqueeze(1)

    def step(self, a_n, a_s, auto_reset=True):
        self._econ_posture(0, a_n.long()); self._econ_posture(1, a_s.long())
        # COMBAT aux frontieres : chaque camp projette sa garnison sur les voisins (bonus petrole)
        gn = self.garr * self._mask(0); gs = self.garr * self._mask(1)
        mult_n = 1.0 + self.oil_bonus * self._count(self.oil, 0); mult_s = 1.0 + self.oil_bonus * self._count(self.oil, 1)
        press_n = (gn @ self.adjn) * mult_n.unsqueeze(1)
        press_s = (gs @ self.adjn) * mult_s.unsqueeze(1)
        own1 = self.owner == 1; own2 = self.owner == 2; neu = self.owner == 0
        dmg = own1.float() * press_s * self.combat + own2.float() * press_n * self.combat
        self.garr = self.garr - dmg
        # BASCULES : secteur tenu submerge -> a l'ennemi ; neutre domine -> au plus fort
        fell1 = own1 & (self.garr <= 0); fell2 = own2 & (self.garr <= 0)
        ndom = press_n > press_s
        claim_n = neu & (press_n > self.garr) & ndom
        claim_s = neu & (press_s > self.garr) & (~ndom)
        new = self.owner.clone()
        new = torch.where(fell1, torch.full_like(new, 2), new)
        new = torch.where(fell2, torch.ones_like(new), new)
        new = torch.where(claim_n, torch.ones_like(new), new)
        new = torch.where(claim_s, torch.full_like(new, 2), new)
        capg = (fell1.float() + claim_s.float()) * 0.25 * press_s + (fell2.float() + claim_n.float()) * 0.25 * press_n
        captured = fell1 | fell2 | claim_n | claim_s
        self.owner = new
        self.garr = torch.where(captured, capg, self.garr.clamp(min=0.0))
        # DRAIN : entretien des troupes (chaque secteur tenu paie) -> il faut sans cesse recruter = tenir l'eco
        self.garr = (self.garr - self.upkeep * (self.owner > 0).float()).clamp(min=0.0)
        # SCORE : la COURSE -> on accumule selon les RESSOURCES tenues (camper sur sa dot = stagner = perdre)
        res_n = self._count(self.oil, 0) + self._count(self.water, 0) + self._count(self.gas, 0)
        res_s = self._count(self.oil, 1) + self._count(self.water, 1) + self._count(self.gas, 1)
        self.score[:, 0] = self.score[:, 0] + res_n; self.score[:, 1] = self.score[:, 1] + res_s
        self.t = self.t + 1
        # ISSUE : course economique (capitale prise = mort subite ; sinon, plus gros score gagne)
        n_caplost = self.owner[:, self.cap_n] != 1; s_caplost = self.owner[:, self.cap_s] != 2
        n_reach = self.score[:, 0] >= self.score_target; s_reach = self.score[:, 1] >= self.score_target
        timeout = self.t >= self.max_steps
        done = n_caplost | s_caplost | n_reach | s_reach | timeout
        n_hi = self.score[:, 0] >= self.score[:, 1]
        n_win = (s_caplost & ~n_caplost) | (~s_caplost & ~n_caplost & done & n_hi)
        s_win = (n_caplost & ~s_caplost) | (~s_caplost & ~n_caplost & done & ~n_hi)
        rew = []
        for f, res_f, win_f, lose_f in ((0, res_n, n_win, s_win), (1, res_s, s_win, n_win)):
            force = self._force(f); losses = torch.clamp(self.prevf[:, f] - force, min=0.0); self.prevf[:, f] = force
            r = 0.10 * res_f - 0.03 * losses + 3.0 * win_f.float() - 3.0 * lose_f.float()
            rew.append(r)
        info = {"n_sec": self._mask(0).sum(1).detach(), "s_sec": self._mask(1).sum(1).detach(),
                "n_score": self.score[:, 0].detach(), "s_score": self.score[:, 1].detach(),
                "n_win": n_win.detach(), "s_win": s_win.detach(), "decided": (n_win | s_win).detach()}
        di = torch.where(done)[0]
        if auto_reset and di.numel() > 0:
            self.reset(di)
        return self._obs(0), self._obs(1), rew[0], rew[1], done.float(), info

    def heuristic_action(self, f):
        # renforce le secteur FRONTALIER le plus faible (tenu et voisin de non-tenu), recrute a fond
        a = torch.zeros(self.N, self.n_heads, dtype=torch.long, device=self.dev)
        mine = self._mask(f); notmine = 1.0 - mine
        border = mine * ((notmine @ self.adj) > 0).float()
        g = self.garr.clone(); g[border <= 0] = 1e9
        weak = g.argmin(1)
        a[torch.arange(self.N, device=self.dev), weak] = 1
        a[:, self.K] = 2
        return a


if __name__ == "__main__":   # smoke : deux nations heuristiques se font la guerre
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    e = LeviathanWar(num_envs=4096, device=dev, seed=1)
    print("K", e.K, "| cap nord", e.cap_n, "cap sud", e.cap_s, "| voisins moy", round(e.adj.sum(1).mean().item(), 1))
    print("split initial : nord", int((e.owner[0] == 1).sum()), "sud", int((e.owner[0] == 2).sum()), "neutre", int((e.owner[0] == 0).sum()))
    nw = sw = dec = 0; nsec = []; ssec = []
    for _ in range(e.max_steps * 4):
        an = e.heuristic_action(0); as_ = e.heuristic_action(1)
        o0, o1, rn, rs, d, info = e.step(an, as_)
        nsec.append(info["n_sec"].mean().item()); ssec.append(info["s_sec"].mean().item())
        di = torch.where(d > 0)[0]
        if di.numel() > 0:
            nw += int(info["n_win"][di].sum().item()); sw += int(info["s_win"][di].sum().item()); dec += int(info["decided"][di].sum().item())
    import statistics
    print("secteurs tenus moy : NORD %.1f | SUD %.1f (sur 13)" % (statistics.mean(nsec), statistics.mean(ssec)))
    print("parties decidees %d | nord gagne %d | sud gagne %d" % (dec, nw, sw))
    print("obs fini ?", bool(torch.isfinite(o0).all()), "| obs_dim", e.obs_dim, "n_heads", e.n_heads)
