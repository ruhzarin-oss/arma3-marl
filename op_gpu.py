"""op_gpu — SIMULATEUR OPÉRATIONNEL sur GPU (tenseurs PyTorch) pour entraîner le MANAGER APPRIS [pile 1/5].
Abstraction de l'opération HARMATTAN-2 (4 escouades vs garnison+patrouilles+QRF), assez fidèle pour que
la DÉCISION du manager (objectif + posture par escouade) compte, assez rapide pour le RL (~milliers d'op/s).
NON un clone d'Arma : capture la PHYSIQUE DÉCISIONNELLE calibrée sur 200+ opérations Arma journalisées —
attrition par contact/posture, destruction de la garnison à l'assaut massé, QRF létale en consolidation,
horloge d'exfil. Critère de VALIDITÉ (empirique, pas un réglage libre) : la partition SCRIPTÉE rejouée
ici doit reproduire la baseline P-v3b (38 % strict / 72 % militaire). Tout 100 % device."""
import torch

# ---- géographie abstraite (mêmes points nommés que run_op palier 2, en coordonnées normalisées) ----
POINTS = {  # (x, y) en mètres, repris de run_op.py
    "SPAWN_APPUI": (14920, 15620), "SPAWN_AO": (15080, 15600), "SPAWN_AE": (15290, 15740), "SPAWN_RES": (15000, 15560),
    "CRETE": (14880, 15860), "ATTENTE": (15120, 15820), "ATTENTE_E": (15260, 15980), "POSTE_RES": (15060, 15740),
    "LIGNE_O": (15090, 15930), "LIGNE_E": (15200, 16010), "COMPLEXE": (15000, 16000), "LZ": (15180, 15620),
    "QRF_PT": (15000, 16350),
}
# index des objectifs adressables par le manager (action discrète)
GOALS = ["CRETE", "ATTENTE", "ATTENTE_E", "POSTE_RES", "LIGNE_O", "LIGNE_E", "COMPLEXE", "LZ"]
STANCE_NAMES = ["move", "assault", "suppress", "hold"]


class OpGPU:
    def __init__(self, num_envs=4096, device="cuda:0", seed=0,
                 # --- constantes calibrées sur les ops Arma (ajustables au calibrage) ---
                 move_speed=14.0,        # m / pas (marche de groupe ~ vitesse réelle mesurée)
                 patrol_bite=0.020,      # attrition/pas par escouade en mouvement à portée d'une patrouille
                 garr_dps=0.024,         # CALIBRÉ (avec qrf_dps + bruit log-normal sd0.5)
                 assault_dmg=0.16,       # dégâts/pas infligés À la garnison par escouade en posture assault au contact
                 suppress_shield=0.45,   # réduction de garr_dps subie quand une escouade amie suppresse
                 hold_shield=0.55,       # réduction des dégâts en posture hold (défense)
                 qrf_dps=0.060,          # CALIBRÉ : partition scriptée -> 73.5% militaire = baseline Arma P-v3b 72%
                 qrf_hp=8.0, garr_hp=12.0, patrol_hp=4.0, squad_n=7,
                 contact_r=120.0, secure_r=60.0, exfil_budget=195, qrf_step=None,
                 max_steps=260):
        self.dev = device; self.N = num_envs; self.S = 4   # 4 escouades
        self.g = torch.Generator(device=device).manual_seed(seed)
        self.P = torch.tensor([POINTS[k] for k in POINTS], dtype=torch.float32, device=device)
        self.pname = list(POINTS.keys())
        self.goalP = torch.tensor([POINTS[k] for k in GOALS], dtype=torch.float32, device=device)  # (G,2)
        self.G = len(GOALS)
        self.move_speed = move_speed; self.patrol_bite = patrol_bite; self.garr_dps = garr_dps
        self.assault_dmg = assault_dmg; self.suppress_shield = suppress_shield; self.hold_shield = hold_shield
        self.qrf_dps = qrf_dps; self.contact_r = contact_r; self.secure_r = secure_r
        self.exfil_budget = exfil_budget; self.max_steps = max_steps
        self.qrf_hp0 = qrf_hp; self.garr_hp0 = garr_hp; self.patrol_hp0 = patrol_hp; self.squad_n = squad_n
        self.COMPLEXE = torch.tensor(POINTS["COMPLEXE"], dtype=torch.float32, device=device)
        self.LZ = torch.tensor(POINTS["LZ"], dtype=torch.float32, device=device)
        self.QRF_PT = torch.tensor(POINTS["QRF_PT"], dtype=torch.float32, device=device)
        self._reset(torch.arange(num_envs, device=device))

    def _reset(self, idx):
        if idx.numel() == 0: return
        n = idx.numel()
        for arr, init in [("spos", None), ("sgoal", None), ("sstance", None), ("sstr", None)]:
            pass
        sp = torch.stack([torch.tensor(POINTS[k], dtype=torch.float32, device=self.dev)
                          for k in ("SPAWN_APPUI", "SPAWN_AO", "SPAWN_AE", "SPAWN_RES")])  # (4,2)
        if not hasattr(self, "spos"):
            self.spos = torch.zeros(self.N, self.S, 2, device=self.dev)
            self.sstr = torch.zeros(self.N, self.S, device=self.dev)            # effectif (0..squad_n)
            self.sgoal = torch.zeros(self.N, self.S, dtype=torch.long, device=self.dev)
            self.sstance = torch.zeros(self.N, self.S, dtype=torch.long, device=self.dev)
            self.garr = torch.zeros(self.N, device=self.dev)                    # PV garnison
            self.patrol = torch.zeros(self.N, device=self.dev)                  # PV patrouilles
            self.qrf = torch.zeros(self.N, device=self.dev)                     # PV QRF (0 tant que pas spawn)
            self.qrf_live = torch.zeros(self.N, dtype=torch.bool, device=self.dev)
            self.t = torch.zeros(self.N, dtype=torch.long, device=self.dev)
            self.consol_t = torch.zeros(self.N, device=self.dev)               # pas passés en consolidation tenue
        self.spos[idx] = sp[None].expand(n, -1, -1)
        self.sstr[idx] = float(self.squad_n)
        self.sgoal[idx] = 0; self.sstance[idx] = 0
        self.garr[idx] = self.garr_hp0; self.patrol[idx] = self.patrol_hp0 * 2  # 2 patrouilles
        self.qrf[idx] = 0.0; self.qrf_live[idx] = False
        self.t[idx] = 0; self.consol_t[idx] = 0.0

    def alive_squads(self):  # (N,S) bool
        return self.sstr > 0.5

    def force_frac(self):    # part de la force amie encore vivante (0..1)
        return self.sstr.sum(1) / (self.S * self.squad_n)

    def obs(self):
        """Observation du manager (N, F) : par escouade [dx,dy vers complexe, effectif, dist LZ] + ennemis + phase."""
        S = self.S
        rel_cx = (self.spos - self.COMPLEXE[None, None]) / 500.0                 # (N,S,2)
        dist_lz = ((self.spos - self.LZ[None, None]).pow(2).sum(-1).sqrt() / 500.0)[..., None]
        strn = (self.sstr / self.squad_n)[..., None]
        per_sq = torch.cat([rel_cx, strn, dist_lz], -1).reshape(self.N, S * 4)    # (N, 16)
        en = torch.stack([self.garr / self.garr_hp0, self.patrol / (2 * self.patrol_hp0),
                          self.qrf / self.qrf_hp0, self.qrf_live.float(),
                          self.consol_t / 20.0, self.t.float() / self.max_steps], 1)  # (N,6)
        return torch.cat([per_sq, en], 1)                                        # (N, 22)

    def obs_dim(self): return self.S * 4 + 6

    def _noise(self, shape, sd=0.5):
        """bruit multiplicatif log-normal centré sur 1 (variance de combat — calibré sur la dispersion Arma)."""
        return (torch.randn(shape, generator=self.g, device=self.dev) * sd).exp()

    def step(self, goals, stances):
        """goals (N,S) long in [0,G), stances (N,S) long in [0,4). Retourne (done, info)."""
        self.sgoal = goals; self.sstance = stances
        al = self.alive_squads()
        tgt = self.goalP[goals]                                                  # (N,S,2)
        # --- mouvement vers l'objectif (vitesse pleine en move/assault, lent en suppress/hold) ---
        d = tgt - self.spos; dist = d.norm(dim=-1, keepdim=True).clamp(min=1e-3)
        spd = torch.where((stances == 0) | (stances == 1), self.move_speed, self.move_speed * 0.3)[..., None]
        stepv = torch.minimum(d / dist * spd, d)                                 # ne dépasse pas la cible
        self.spos = torch.where(al[..., None], self.spos + stepv, self.spos)
        # --- contact patrouilles : escouades en mouvement loin du complexe, patrouilles vivantes ---
        d_cx = (self.spos - self.COMPLEXE[None, None]).norm(dim=-1)               # (N,S)
        moving = (stances == 0) & al & (d_cx > self.secure_r)
        pat_live = (self.patrol > 0)[:, None]
        bite = self.patrol_bite * self.squad_n * (moving & pat_live).float()
        self.sstr = (self.sstr - bite).clamp(min=0)
        # les patrouilles encaissent dès qu'une escouade avance dans la zone (infiltration/assaut)
        eng_pat = ((stances == 0) | (stances == 1)) & al & (d_cx > self.secure_r) & (d_cx < 220.0)
        self.patrol = (self.patrol - self.assault_dmg * 1.4 * eng_pat.float().sum(1)).clamp(min=0)
        # --- combat au complexe : qui est au contact (dans contact_r du complexe) ---
        at_cx = (d_cx < self.contact_r) & al
        assaulting = (stances == 1) & at_cx
        suppressing = (stances == 2) & at_cx
        holding = (stances == 3) & at_cx
        garr_live = (self.garr > 0)
        # la garnison tape les assaillants ; suppression amie réduit ses dégâts
        supp_any = suppressing.any(1).float()
        shield = 1.0 - self.suppress_shield * supp_any
        dmg_to_squads = self.garr_dps * garr_live.float() * shield * self._noise((self.N,))  # bruit combat
        exposed = (assaulting | suppressing).float()                             # (N,S)
        self.sstr = (self.sstr - dmg_to_squads[:, None] * exposed * 0.5).clamp(min=0)
        # les assaillants détruisent la garnison
        self.garr = (self.garr - self.assault_dmg * assaulting.float().sum(1) * self._noise((self.N,))).clamp(min=0)
        # --- QRF : spawn quand la garnison tombe et qu'au moins une escouade tient le complexe ---
        garr_down = self.garr <= 0
        near_cx = ((d_cx < self.secure_r) & al).any(1)                           # une escouade tient le complexe
        spawn_qrf = garr_down & near_cx & (~self.qrf_live)
        self.qrf = torch.where(spawn_qrf, torch.full_like(self.qrf, self.qrf_hp0), self.qrf)
        self.qrf_live = self.qrf_live | spawn_qrf
        # combat QRF : tape les défenseurs au complexe (hold réduit), les défenseurs tapent la QRF
        qrf_on = self.qrf > 0
        n_def = (holding | assaulting).float().sum(1).clamp(min=1)
        hold_any = holding.any(1).float()
        qshield = 1.0 - self.hold_shield * hold_any
        dmg_qrf_to = self.qrf_dps * qrf_on.float() * qshield * self._noise((self.N,))
        self.sstr = (self.sstr - (dmg_qrf_to[:, None] * (holding | assaulting).float()) / n_def[:, None]).clamp(min=0)
        self.qrf = (self.qrf - self.assault_dmg * (holding | assaulting).float().sum(1) * qrf_on.float()).clamp(min=0)
        # --- consolidation tenue : garnison morte, QRF traitée ou en cours, ≥2 escouades au complexe ---
        secured = garr_down & ((holding | assaulting) & (d_cx < self.secure_r)).sum(1).float().ge(2)
        self.consol_t = torch.where(secured, self.consol_t + 1, self.consol_t)
        self.t = self.t + 1
        # --- conditions de fin ---
        al = self.alive_squads()
        ff = self.force_frac()
        ennemi_total = self.garr_hp0 + 2 * self.patrol_hp0 + self.qrf_hp0
        ennemi_reste = self.garr + self.patrol + self.qrf
        ennemi_brise = (1 - ennemi_reste / ennemi_total) >= 0.7
        pertes = 1 - ff
        # à la LZ : médiane des escouades vivantes proche de la LZ
        d_lz = (self.spos - self.LZ[None, None]).norm(dim=-1)
        at_lz = ((d_lz < 90) & al).float().sum(1) >= 2
        timeout = self.t >= self.max_steps
        wiped = ~al.any(1)
        # succès STRICT = ennemi brisé + pertes ≤50 % + à la LZ
        succ_strict = ennemi_brise & (pertes <= 0.5) & at_lz
        # accompli MILITAIREMENT = ennemi brisé + pertes ≤50 % (peu importe la LZ)
        mil = ennemi_brise & (pertes <= 0.5)
        done = succ_strict | wiped | timeout | (pertes > 0.7)
        info = {"succ_strict": succ_strict, "mil": mil, "pertes": pertes, "ennemi_brise": ennemi_brise,
                "at_lz": at_lz, "consol": self.consol_t > 0, "qrf_faced": self.qrf_live,
                "ennemi_reste": ennemi_reste, "t": self.t.clone()}
        return done, info
