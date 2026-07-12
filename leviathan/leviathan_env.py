"""leviathan_env.py — ETAGE 1 de LEVIATHAN : env VECTORISE (N mondes en parallele) ou UN pays
apprend a s'organiser SEUL pour PROSPERER. Sert l'entrainement PPO rapide (puis le live continu).

Les 4 choix de Younes, replies proprement :
  - RAISON D'ETRE = prosperer : recompense = tenir le terrain - saigner peu, gros malus si effondrement
    (survie + minimisation des pertes en un scalaire ; l'expansion mordra a l'etage 2-3, quand il y aura un ennemi a conquerir).
  - CE QU'ELLE PILOTE = UNE action par secteur dans {0 TENIR, 1 RENFORCER, 2 DEGARNIR} :
      RENFORCER route la reserve (allocation) ; DEGARNIR replie des troupes vers la reserve (concentrer/abandonner) ;
      TENIR = garnison. -> allocation + roles + posture en une seule tete.
  - PERCEPTION = anticipation : un indicateur de MENACE monte et est VISIBLE le tick AVANT le choc -> pre-positionnement.
  - APPRENTISSAGE = parallele rapide (cet env) puis live continu (mode cadence, plus tard).

Logistique heritee du substrat : caserne (renforts, STOPPE si capturee), depot (muns), trajet des convois
(pipeline par eta), cascade de captures.
"""
import math
import torch

SECTORS = [("Kavala", 3600, 13200, ""), ("Pyrgos", 16800, 12600, ""), ("Sofia", 25700, 21300, "depot"),
           ("Agios", 9200, 21600, ""), ("AirHQ", 14600, 16900, "hq")]


class LeviathanEnv:
    def __init__(self, num_envs, device="cuda:0", threat_rate=0.45, reinforce_rate=3.0,
                 speed=9000.0, max_steps=80, secure_min=2, seed=0):
        self.N = num_envs; self.K = len(SECTORS); self.dev = device
        self.hq = next(i for i, s in enumerate(SECTORS) if s[3] == "hq")
        self.depot = next(i for i, s in enumerate(SECTORS) if s[3] == "depot")
        self.threat_rate = threat_rate; self.reinforce_rate = reinforce_rate
        self.max_steps = max_steps; self.secure_min = secure_min; self.SC = 30.0
        torch.manual_seed(seed)
        hx, hy = SECTORS[self.hq][1], SECTORS[self.hq][2]
        d = [math.hypot(SECTORS[i][1] - hx, SECTORS[i][2] - hy) for i in range(self.K)]
        self.eta = [max(1, min(3, int(math.ceil(di / speed)))) for di in d]   # ticks de trajet par secteur
        self.L = 3
        self.is_hq = torch.zeros(self.K, device=device); self.is_hq[self.hq] = 1
        self.is_depot = torch.zeros(self.K, device=device); self.is_depot[self.depot] = 1
        self.disthq = torch.tensor(d, device=device, dtype=torch.float32) / (speed * self.L)
        self.garr0 = torch.tensor([20, 16, 14, 16, 24], dtype=torch.float32, device=device)
        self.obs_dim = self.K * 7 + 5; self.n_actions = 3; self.n_heads = self.K
        N, K, L, dv = self.N, self.K, self.L, self.dev
        self.garr = torch.zeros(N, K, device=dv); self.supply = torch.zeros(N, K, device=dv)
        self.owner = torch.zeros(N, K, device=dv); self.threat = torch.zeros(N, K, device=dv)
        self.reserve = torch.zeros(N, device=dv); self.transit = torch.zeros(N, K, L, device=dv)
        self.t = torch.zeros(N, dtype=torch.long, device=dv); self.prev_force = torch.zeros(N, device=dv)
        self.reset()

    def _force(self):
        return self.garr.sum(1) + self.reserve + self.transit.sum((1, 2))

    def _roll_threat(self, idx=None):
        # la menace monte sur des secteurs tenus ; visible dans l'obs AVANT que le degat tombe (anticipation)
        if idx is None:
            held = self.owner > 0
            fire = (torch.rand(self.N, self.K, device=self.dev) < self.threat_rate) & held
            self.threat = self.threat * 0.4 + fire.float() * torch.rand(self.N, self.K, device=self.dev) * 6.0
        else:
            held = self.owner[idx] > 0
            fire = (torch.rand(idx.numel(), self.K, device=self.dev) < self.threat_rate) & held
            self.threat[idx] = self.threat[idx] * 0.4 + fire.float() * torch.rand(idx.numel(), self.K, device=self.dev) * 6.0

    def reset(self, idx=None):
        if idx is None:
            idx = torch.arange(self.N, device=self.dev)
        self.garr[idx] = self.garr0.unsqueeze(0)
        self.supply[idx] = 100.0; self.owner[idx] = 1.0; self.threat[idx] = 0.0
        self.reserve[idx] = 30.0; self.transit[idx] = 0.0; self.t[idx] = 0
        self._roll_threat(idx)
        self.prev_force[idx] = self._force()[idx]
        return self._obs()

    def _obs(self):
        SC = self.SC
        per = torch.stack([self.owner, self.garr / SC, self.supply / 100.0, self.threat / 8.0,
                           self.is_hq.expand(self.N, self.K), self.is_depot.expand(self.N, self.K),
                           self.disthq.expand(self.N, self.K)], dim=2).reshape(self.N, self.K * 7)
        glob = torch.stack([self.reserve / SC, (self.owner[:, self.hq] > 0).float(),
                            (self.owner[:, self.depot] > 0).float(), self.owner.sum(1) / self.K,
                            self.t.float() / self.max_steps], dim=1)
        return torch.cat([per, glob], dim=1)

    def step(self, action, auto_reset=True):
        a = action.long(); held = self.owner > 0
        # 1) DEGAT depuis la menace COURANTE (qui etait visible le tick precedent)
        lossf = 1.5 - self.supply / 100.0
        self.garr = self.garr - self.threat * lossf * held.float()
        self.supply = torch.clamp(self.supply - self.threat * 1.8 * held.float(), 0, 100)
        # 2) RENFORTS (caserne) + RAVITO (depot) — stoppent si la base est perdue
        hq_ok = (self.owner[:, self.hq] > 0).float(); dep_ok = (self.owner[:, self.depot] > 0).float()
        self.reserve = self.reserve + self.reinforce_rate * hq_ok
        self.supply = torch.clamp(self.supply + 5.0 * dep_ok.unsqueeze(1) * held.float(), 0, 100)
        # 3) DEGARNIR -> replie une part de la garnison vers la reserve
        thin = ((a == 2) & held).float()
        pulled = self.garr * 0.5 * thin
        self.garr = self.garr - pulled; self.reserve = self.reserve + pulled.sum(1)
        # 4) RENFORCER -> repartit la reserve (max 12) vers les secteurs marques, en transit (eta)
        want = ((a == 1) & held).float(); wsum = want.sum(1, keepdim=True)
        send_total = torch.minimum(self.reserve, torch.full_like(self.reserve, 12.0))
        send = send_total.unsqueeze(1) * want / wsum.clamp(min=1.0)
        send = send * (wsum > 0).float()
        self.reserve = self.reserve - send.sum(1)
        for k in range(self.K):
            e = self.eta[k]
            self.transit[:, k, e - 1] = self.transit[:, k, e - 1] + send[:, k]
        # 5) CONVOIS arrivent (slot 0), pipeline avance
        arrive = self.transit[:, :, 0].clone()
        self.transit[:, :, :-1] = self.transit[:, :, 1:].clone(); self.transit[:, :, -1] = 0.0
        self.garr = self.garr + arrive * held.float()
        self.reserve = self.reserve + (arrive * (~held).float()).sum(1)   # secteur perdu -> repli reserve
        # 6) SECTEURS TOMBES (cascade : si caserne/depot, la logistique s'effondre au tick suivant)
        fell = held & (self.garr <= 0)
        self.owner = torch.where(fell, torch.zeros_like(self.owner), self.owner)
        self.garr = torch.clamp(self.garr, min=0.0)
        # 7) menace du PROCHAIN tick -> visible dans l'obs (anticipation)
        self._roll_threat()
        self.t = self.t + 1
        # RECOMPENSE prosperer = tenir - saigner - temps ; gros malus si effondrement
        held_cnt = self.owner.sum(1); force = self._force()
        losses = torch.clamp(self.prev_force - force, min=0.0); self.prev_force = force
        elim = held_cnt < self.secure_min; timeout = self.t >= self.max_steps; done = elim | timeout
        rew = 0.10 * held_cnt - 0.04 * losses - 0.01 - 3.0 * elim.float()
        info = {"held": held_cnt.detach(), "survived": (~elim).detach()}
        di = torch.where(done)[0]
        if auto_reset and di.numel() > 0:
            self.reset(di)
        return self._obs(), rew, done.float(), info
