"""FormationEnv — apprendre le DEPLACEMENT EN FORMATION. Une ancre avance vers l'objectif ; chaque agent
a un SLOT (place dans la forme, tournee selon le cap). L'agent apprend a SUIVRE son slot (la forme avance)
sans s'amasser. Gabarit tire au hasard chaque episode -> une seule politique tient les 8 formations.
Recompense = suivi de slot (telescope) - anti-amas - pas. Mesure = erreur de slot moyenne (serrage)."""
import math, torch

TEMPLATES = {   # (le_long_avant+, lateral_droite+) en unites d'espacement, A=8
    "file":    [(0, 0), (-1, 0), (-2, 0), (-3, 0), (-4, 0), (-5, 0), (-6, 0), (-7, 0)],
    "colonne": [(0, .5), (-1, -.5), (-2, .5), (-3, -.5), (-4, .5), (-5, -.5), (-6, .5), (-7, -.5)],
    "coin":    [(0, 0), (-1, -1), (-1, 1), (-2, -2), (-2, 2), (-3, -3), (-3, 3), (-4, 0)],
    "ligne":   [(0, -3.5), (0, -2.5), (0, -1.5), (0, -.5), (0, .5), (0, 1.5), (0, 2.5), (0, 3.5)],
    "echelon": [(0, 0), (-1, 1), (-2, 2), (-3, 3), (-4, 4), (-5, 5), (-6, 6), (-7, 7)],
    "vee":     [(0, -3), (0, 3), (-1, -2), (-1, 2), (-2, -1), (-2, 1), (-3, 0), (-4, 0)],
    "losange": [(2, 0), (1, -1.5), (1, 1.5), (0, -2.5), (0, 2.5), (-1, -1.5), (-1, 1.5), (-2, 0)],
    "box":     [(0, -1.5), (0, -.5), (0, .5), (0, 1.5), (-1.5, -1.5), (-1.5, -.5), (-1.5, .5), (-1.5, 1.5)],
}
NAMES = list(TEMPLATES)


class FormationEnv:
    def __init__(self, num_envs, A=8, device="cuda:0", seed=0, S=200.0, spacing=9.0,
                 move=10.0, anchor_speed=7.0, max_steps=140, dmin=5.0, reach_r=18.0,
                 transition=False, switch_frac=0.45, p_transition=0.6):
        self.N, self.A, self.dev, self.S = num_envs, A, device, S
        self.spacing = spacing; self.move = move; self.anchor_speed = anchor_speed
        self.max_steps = max_steps; self.dmin = dmin; self.reach_r = reach_r
        self.transition = transition; self.switch_frac = switch_frac; self.p_transition = p_transition
        self.APP = torch.tensor([0, 1, 2], device=device)   # approche : file, colonne, coin
        self.ASS = torch.tensor([3, 2, 5], device=device)   # assaut   : ligne, coin, vee
        self.n_actions = 9                                  # 0-7 deplacement, 8 = halte
        self.g = torch.Generator(device=device).manual_seed(seed)
        self.tmpl = torch.tensor([TEMPLATES[n] for n in NAMES], dtype=torch.float32, device=device) * spacing  # (F,A,2)
        self.F = self.tmpl.shape[0]
        z = lambda *s: torch.zeros(*s, device=device)
        self.apx = z(num_envs, A); self.apy = z(num_envs, A)
        self.ancx = z(num_envs); self.ancy = z(num_envs)
        self.objx = z(num_envs); self.objy = z(num_envs)
        self.fidx = torch.zeros(num_envs, dtype=torch.long, device=device)
        self.fi2 = torch.zeros(num_envs, dtype=torch.long, device=device)   # forme d'assaut (apres bascule)
        self.switchd = torch.zeros(num_envs, device=device)                 # distance objectif a laquelle on bascule
        self.t = torch.zeros(num_envs, device=device)
        self.prevsd = z(num_envs, A)
        self._reset(torch.arange(num_envs, device=device))
        self.obs_dim = self._obs().shape[-1]

    def _reset(self, ids):
        n = ids.numel()
        if n == 0: return
        r = lambda: torch.rand(n, device=self.dev, generator=self.g)
        ri = lambda hi: torch.randint(0, hi, (n,), device=self.dev, generator=self.g)
        if self.transition:                                                # V2 : episodes a bascule colonne->assaut
            istr = r() < self.p_transition
            fall = ri(self.F)
            self.fidx[ids] = torch.where(istr, self.APP[ri(len(self.APP))], fall)
            self.fi2[ids] = torch.where(istr, self.ASS[ri(len(self.ASS))], self.fidx[ids])
        else:
            self.fidx[ids] = ri(self.F); self.fi2[ids] = self.fidx[ids]
        ang = r() * 2 * math.pi                                            # cap de marche aleatoire
        self.ancx[ids] = (r() - 0.5) * 0.4 * self.S; self.ancy[ids] = (r() - 0.5) * 0.4 * self.S
        d = (0.55 + 0.35 * r()) * self.S
        self.objx[ids] = self.ancx[ids] + d * torch.cos(ang); self.objy[ids] = self.ancy[ids] + d * torch.sin(ang)
        self.switchd[ids] = self.switch_frac * d                           # bascule a switch_frac du chemin
        # agents demarrent en grappe autour de l'ancre (pas en formation -> ils doivent s'y mettre)
        self.apx[ids] = self.ancx[ids][:, None] + (r()[:, None] * 0 + torch.randn(n, self.A, device=self.dev, generator=self.g) * 6)
        self.apy[ids] = self.ancy[ids][:, None] + torch.randn(n, self.A, device=self.dev, generator=self.g) * 6
        self.t[ids] = 0.0
        self.prevsd[ids] = torch.sqrt(((self._slots()[ids] - torch.stack([self.apx[ids], self.apy[ids]], -1)) ** 2).sum(-1) + 1e-6)

    def reset(self):
        self._reset(torch.arange(self.N, device=self.dev)); return self._obs()

    def _heading(self):
        hx = self.objx - self.ancx; hy = self.objy - self.ancy
        d = torch.sqrt(hx * hx + hy * hy) + 1e-6
        return hx / d, hy / d

    def _curfi(self):                                                      # forme active : approche, puis assaut une fois proche
        d = torch.sqrt((self.objx - self.ancx) ** 2 + (self.objy - self.ancy) ** 2)
        return torch.where(d <= self.switchd, self.fi2, self.fidx)

    def _slots(self):                                                      # (N,A,2) positions monde des slots
        hx, hy = self._heading()
        cf = self._curfi()
        along = self.tmpl[cf][..., 0]; lat = self.tmpl[cf][..., 1]   # (N,A)
        sx = self.ancx[:, None] + along * hx[:, None] + lat * (-hy[:, None])
        sy = self.ancy[:, None] + along * hy[:, None] + lat * (hx[:, None])
        return torch.stack([sx, sy], -1)

    def _nearest_tm(self):
        dx = self.apx[:, :, None] - self.apx[:, None, :]; dy = self.apy[:, :, None] - self.apy[:, None, :]
        d2 = dx * dx + dy * dy + torch.eye(self.A, device=self.dev)[None] * 1e9
        j = d2.argmin(-1)
        tx = torch.gather(self.apx, 1, j); ty = torch.gather(self.apy, 1, j)
        td = torch.sqrt((tx - self.apx) ** 2 + (ty - self.apy) ** 2) + 1e-6
        return (tx - self.apx) / td, (ty - self.apy) / td, td

    def _obs(self):
        S = self.S; slots = self._slots()
        sdx = slots[..., 0] - self.apx; sdy = slots[..., 1] - self.apy; sd = torch.sqrt(sdx * sdx + sdy * sdy) + 1e-6
        hx, hy = self._heading()
        odx = self.objx[:, None] - self.apx; ody = self.objy[:, None] - self.apy; od = torch.sqrt(odx * odx + ody * ody) + 1e-6
        tnx, tny, td = self._nearest_tm()
        o = torch.stack([sdx / sd, sdy / sd, (sd / S).clamp(max=2),
                         hx[:, None].expand(-1, self.A), hy[:, None].expand(-1, self.A),
                         odx / od, ody / od, (od / S).clamp(max=2),
                         tnx, tny, (td / S).clamp(max=2)], -1)
        return o

    def step(self, acts):
        ang = acts.float() * (2 * math.pi / 8)
        mv = (acts < 8).float()
        self.apx = self.apx + self.move * torch.cos(ang) * mv
        self.apy = self.apy + self.move * torch.sin(ang) * mv
        hx, hy = self._heading()
        dobj = torch.sqrt((self.objx - self.ancx) ** 2 + (self.objy - self.ancy) ** 2)
        adv = (dobj > self.reach_r).float()                                # l'ancre avance tant que pas arrivee
        self.ancx = self.ancx + self.anchor_speed * hx * adv; self.ancy = self.ancy + self.anchor_speed * hy * adv
        slots = self._slots()
        sd = torch.sqrt((slots[..., 0] - self.apx) ** 2 + (slots[..., 1] - self.apy) ** 2) + 1e-6
        follow = (self.prevsd - sd) / self.spacing; self.prevsd = sd
        _, _, td = self._nearest_tm()
        clump = (td < self.dmin).float()
        slot_err = sd.mean(1)                                              # serrage moyen (m)
        self.t = self.t + 1
        reached = dobj <= self.reach_r
        done = reached | (self.t >= self.max_steps)
        good = (slot_err < self.spacing)                                   # formation tenue
        rew = 2.0 * follow - 0.5 * clump - 0.01 + (reached & good).float()[:, None] * 8.0 / self.A
        info = {"slot_err": slot_err, "reached": reached, "held": (reached & good)}
        self._reset(done.nonzero(as_tuple=True)[0])
        return self._obs(), rew, done.float(), info
