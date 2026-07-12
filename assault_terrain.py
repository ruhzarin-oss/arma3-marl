"""assault_terrain — banc d'essai PERCEPTION (G-perc-0). Un groupe ATTAQUANT manœuvre vers un objectif
DÉFENDU à travers le terrain. Le défilé (approche couverte) réduit l'exposition au feu -> lire le terrain
et choisir l'approche est un LEVIER récompensé. Remplace le KOTH (terrain non exploitable là-bas).
100% GPU vectorisé, réutilise terrain_gpu. obs inclut les variables de perception (G-perc-0)."""
import math
import torch
import terrain_gpu as TG
import numpy as np


class AssaultTerrain:
    def __init__(self, num_envs=2048, A=4, D=4, R_spawn=170.0, terr_R=200.0, terr_G=64, relief=35.0,
                 move=14.0, fire_range=110.0, hit=0.06, secure_r=25.0, max_steps=60, dmg_dead=0.7,
                 grid_obs=False, gridK=8, gridspan=80.0, team_obs=False, role_obs=False,
                 shell_obs=False, shellK=12, shell_R=60.0, suffer=False, D_min=2,
                 replica=False, replica_path="replica.npz", device="cuda:0", seed=0):
        self.N = num_envs; self.A = A; self.D = D; self.R_spawn = R_spawn
        self.terr_R = terr_R; self.terr_G = terr_G; self.relief = relief
        self.move = move; self.fire_range = fire_range; self.hit = hit; self.secure_r = secure_r
        self.max_steps = max_steps; self.dmg_dead = dmg_dead; self.dev = device; self.scale = terr_R
        self.replica = replica
        if replica:
            _R = np.load(replica_path)
            self._solid = torch.tensor(_R["solid"].astype("float32"), device=device)
            self._elevR = torch.tensor(_R["elev"].astype("float32"), device=device)
            self.terr_G = int(_R["GS"]); self.terr_R = float(_R["W"]); self.scale = self.terr_R
            self.R_spawn = min(R_spawn, self.terr_R - 25.0)

        self.g = torch.Generator(device=device).manual_seed(seed)
        self.n_actions = 10                       # 0-7 = caps (45 deg, STEERING), 8 = HOLD, 9 = SUPPRESS
        self.grid_obs = grid_obs; self.gridK = gridK; self.gridspan = gridspan; self.team_obs = team_obs; self.role_obs = role_obs
        self.shell_obs = shell_obs; self.shellK = shellK; self.shell_R = shell_R
        self.suffer = suffer; self.D_min = D_min
        self.obs_dim = 9 + (2 * gridK * gridK if grid_obs else 0) + (4 if team_obs else 0) + (2 if role_obs else 0) + ((shellK + 1) if shell_obs else 0) + (2 if suffer else 0)   # +grille +coequipiers +ROLE +COQUE +SUFFER
        self._reset(torch.arange(num_envs, device=device))

    def _reset(self, idx):
        n = idx.numel(); d = self.dev
        if not hasattr(self, "apx"):
            N, A, D = self.N, self.A, self.D
            self.apx = torch.zeros(N, A, device=d); self.apy = torch.zeros(N, A, device=d); self.admg = torch.zeros(N, A, device=d)
            self.dpx = torch.zeros(N, D, device=d); self.dpy = torch.zeros(N, D, device=d); self.ddmg = torch.zeros(N, D, device=d)
            self.dsupp = torch.zeros(N, D, device=d); self.t = torch.zeros(N, dtype=torch.long, device=d)
            self.last_dmg_in = torch.zeros(N, self.A, device=d)
            self.prev_d = torch.zeros(N, device=d)
            for nm in ("hm", "slope", "cover", "dcover"):
                setattr(self, nm, torch.zeros(N, self.terr_G, self.terr_G, device=d))
        if self.replica:
            self.hm[idx] = self._elevR; self.cover[idx] = self._solid
            self.slope[idx] = 0.0; self.dcover[idx] = 0.0
        else:
            T = TG.gen_terrain(n, self.terr_G, d, self.g, relief=self.relief)
            for nm in ("hm", "slope", "cover", "dcover"):
                getattr(self, nm)[idx] = T[nm]
        dang = torch.arange(self.D, device=d).float() / self.D * 2 * math.pi   # defenseurs en anneau autour de (0,0)
        self.dpx[idx] = 12.0 * torch.cos(dang)[None]; self.dpy[idx] = 12.0 * torch.sin(dang)[None]
        if self.replica:
            for _ in range(20):
                _dw = self._sample_solid(self.dpx[idx], self.dpy[idx]) > 0.5
                if not bool(_dw.any()): break
                _jx = (torch.rand_like(self.dpx[idx]) * 2 - 1) * 10.0
                _jy = (torch.rand_like(self.dpy[idx]) * 2 - 1) * 10.0
                self.dpx[idx] = torch.where(_dw, (self.dpx[idx] + _jx).clamp(-self.terr_R * 0.95, self.terr_R * 0.95), self.dpx[idx])
                self.dpy[idx] = torch.where(_dw, (self.dpy[idx] + _jy).clamp(-self.terr_R * 0.95, self.terr_R * 0.95), self.dpy[idx])
        self.ddmg[idx] = 0.0; self.dsupp[idx] = 0.0
        if self.suffer:
            nact = torch.randint(self.D_min, self.D + 1, (n,), device=d)         # nb defenseurs ACTIFS par env
            deact = (torch.arange(self.D, device=d)[None] >= nact[:, None])       # True = desactive
            self.ddmg[idx] = deact.float()                                        # desactives = deja neutralises
        th = torch.rand(n, generator=self.g, device=d) * 2 * math.pi           # attaquants au bord, cap aleatoire
        sx = self.R_spawn * torch.sin(th); sy = self.R_spawn * torch.cos(th); ar = torch.arange(self.A, device=d).float()
        self.apx[idx] = sx[:, None] + (ar % 2) * 6 - 3; self.apy[idx] = sy[:, None] + (ar - 1) * 6; self.admg[idx] = 0.0
        if self.replica:
            for _ in range(10):
                _w = self._sample_solid(self.apx[idx], self.apy[idx]) > 0.5
                if not bool(_w.any()): break
                self.apx[idx] = torch.where(_w, self.apx[idx] * 0.92, self.apx[idx])
                self.apy[idx] = torch.where(_w, self.apy[idx] * 0.92, self.apy[idx])
        self.t[idx] = 0
        self.prev_d[idx] = torch.sqrt(self.apx[idx] ** 2 + self.apy[idx] ** 2).mean(1) / self.scale
        if not hasattr(self, "_prev_dk"):
            self._prev_dk = torch.zeros(self.N, device=d); self.last_supp = torch.zeros(self.N, self.A, device=d)
            ar = torch.arange(self.A, device=d)
            self.role = (ar >= self.A // 2).long()[None].expand(self.N, self.A).contiguous()   # OFFICIER : 1ere moitie=APPUI(0), 2e=ASSAUT(1)
        self._prev_dk[idx] = (self.ddmg[idx] >= self.dmg_dead).float().sum(1) / self.D; self.last_supp[idx] = 0.0

    def reset(self): return self._obs()
    def _aalive(self): return self.admg < self.dmg_dead
    def _dalive(self): return self.ddmg < self.dmg_dead

    def _sample_solid(self, px, py):
        G = self.terr_G
        gx = ((px / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        gy = ((py / self.scale * 0.5 + 0.5) * (G - 1)).clamp(0, G - 1).long()
        return self._solid[gy, gx]

    def _losc(self, hm, ax, ay, bx, by, R):
        base = TG.los_clear(hm, ax, ay, bx, by, R)
        if not getattr(self, "replica", False):
            return base
        K = 24
        t = torch.linspace(0.0, 1.0, K, device=self.dev)
        pxr = ax.unsqueeze(-1) * (1 - t) + bx.unsqueeze(-1) * t
        pyr = ay.unsqueeze(-1) * (1 - t) + by.unsqueeze(-1) * t
        blocked = (self._sample_solid(pxr, pyr) > 0.5).any(-1)
        return base * (~blocked).float()

    def _obs(self):
        S = self.scale; al = self._aalive()
        dgx = -self.apx / S; dgy = -self.apy / S
        sl = TG.sample(self.slope, self.apx, self.apy, S) / 5.0
        dc = TG.sample(self.dcover, self.apx, self.apy, S) / self.terr_G
        ex = self.dpx.unsqueeze(1) - self.apx.unsqueeze(2); ey = self.dpy.unsqueeze(1) - self.apy.unsqueeze(2)  # (N,A,D)
        BIG = torch.tensor(1e18, device=self.dev)
        ed2 = torch.where(self._dalive().unsqueeze(1), ex * ex + ey * ey, BIG); km = ed2.argmin(2)
        bx = torch.gather(self.dpx, 1, km); by = torch.gather(self.dpy, 1, km)
        los = self._losc(self.hm, self.apx, self.apy, bx, by, S)
        nd = ed2.min(2).values.clamp(max=1e17).sqrt() / S
        base = torch.stack([self.apx / S, self.apy / S, dgx, dgy, al.float(), sl, dc, los, nd], dim=2)
        parts = [base]
        if self.shell_obs: parts.append(self._cover_shell())
        if self.suffer: parts.append(self._suffer_feats())
        if self.grid_obs: parts.append(self._local_grid())
        if self.team_obs: parts.append(self._team_feats())
        if self.role_obs:                                   # ROLE assigne par l'officier (one-hot appui/assaut)
            parts.append(torch.stack([(self.role == 0).float(), (self.role == 1).float()], dim=2))
        return torch.cat(parts, dim=2) if len(parts) > 1 else base

    def _team_feats(self):
        """Conscience des coequipiers (coordination) : binome le plus proche (dx,dy) + suppresse-t-il ?
        + niveau de feu de l'equipe. Permet le feu+mouvement EXPLICITE (j'avance car mon binome cloue)."""
        S = self.scale; px, py = self.apx, self.apy; al = self._aalive()
        dx = px.unsqueeze(1) - px.unsqueeze(2); dy = py.unsqueeze(1) - py.unsqueeze(2)   # (N,A,A) : ally j vu de i
        BIG = torch.tensor(1e18, device=self.dev)
        eye = torch.eye(self.A, dtype=torch.bool, device=self.dev)[None]
        d2 = torch.where(eye | ~al.unsqueeze(1), BIG, dx * dx + dy * dy); jm = d2.argmin(2)
        adx = torch.gather(dx, 2, jm.unsqueeze(2)).squeeze(2) / S; ady = torch.gather(dy, 2, jm.unsqueeze(2)).squeeze(2) / S
        nm = d2.min(2).values >= 1e18; adx = adx.masked_fill(nm, 0.0); ady = ady.masked_fill(nm, 0.0)
        ally_supp = torch.gather(self.last_supp, 1, jm)                                  # le binome cloue-t-il ?
        frac = ((self.last_supp * al.float()).sum(1, keepdim=True) / al.float().sum(1, keepdim=True).clamp(min=1)).expand(self.N, self.A)
        return torch.stack([adx, ady, ally_supp, frac], dim=2)

    def _suffer_feats(self):
        """Signal de DEBORDEMENT : degats recus au dernier pas + fraction de defenseurs qui PEUVENT me toucher
        (vivant + portee + LOS). C'est ce qui permet de JUGER tenir(gagnable) vs decrocher(submerge)."""
        N, A, D, d, S = self.N, self.A, self.D, self.dev, self.scale
        nt = torch.zeros(N, A, device=d)
        for di in range(D):
            bx = self.dpx[:, di:di + 1].expand(N, A); by = self.dpy[:, di:di + 1].expand(N, A)
            los = self._losc(self.hm, self.apx, self.apy, bx, by, S)
            dist = torch.sqrt((self.apx - self.dpx[:, di:di + 1]) ** 2 + (self.apy - self.dpy[:, di:di + 1]) ** 2)
            nt += self._dalive()[:, di:di + 1].float() * los * (dist < self.fire_range).float()
        return torch.stack([(self.last_dmg_in * 5.0).clamp(max=1.0), nt / self.D], dim=2)   # (N,A,2)

    def _cover_shell(self):
        """COQUE DE COUVERT : K rayons ray-marches dans le champ de couvert, centres sur la MENACE
        (rayon 0 = vers l'ennemi le + proche, sens horaire). Distance au 1er couvert / portee. = l'obs de l'avatar Arma."""
        N, A, K, d, S = self.N, self.A, self.shellK, self.dev, self.scale
        R, steps = self.shell_R, 20
        ex = self.dpx.unsqueeze(1) - self.apx.unsqueeze(2); ey = self.dpy.unsqueeze(1) - self.apy.unsqueeze(2)
        BIG = torch.tensor(1e18, device=d)
        ed2 = torch.where(self._dalive().unsqueeze(1), ex * ex + ey * ey, BIG); km = ed2.argmin(2)
        bx = torch.gather(self.dpx, 1, km); by = torch.gather(self.dpy, 1, km)
        th0 = torch.atan2(by - self.apy, bx - self.apx)                       # cap vers la menace (N,A)
        offs = torch.arange(K, device=d).float() * (2 * math.pi / K)
        ang = th0.unsqueeze(-1) + offs                                        # (N,A,K)
        cs = ang.cos(); sn = ang.sin()
        stp = (torch.arange(1, steps + 1, device=d).float() / steps) * R      # (steps,)
        sx = (self.apx[..., None, None] + cs[..., None] * stp).reshape(N, A * K * steps)
        sy = (self.apy[..., None, None] + sn[..., None] * stp).reshape(N, A * K * steps)
        cov = TG.sample(self.cover, sx, sy, S).reshape(N, A, K, steps)
        hit = cov > 0.5; anyh = hit.any(-1)
        first = hit.float().argmax(-1).float()                               # 1er pas touche (0 si aucun)
        dist = torch.where(anyh, (first + 1) / steps * R, torch.full_like(first, R)) / R
        return torch.cat([dist, self.admg.unsqueeze(-1)], dim=2)             # (N,A,K+1) : coque + degats

    def _local_grid(self):
        """Grille locale (G-perc-1) : fenetre KxK de [couvert, pente] autour de l'agent = CONTEXTE spatial
        (vs les valeurs au point). Aplatie -> 2*K*K features. World-aligned (rotation egocentrique = etape +)."""
        K, span, d, N, A = self.gridK, self.gridspan, self.dev, self.N, self.A
        off = (torch.arange(K, device=d).float() / (K - 1) - 0.5) * span
        gx = (self.apx[..., None, None] + off[None, None, :, None]).expand(N, A, K, K).reshape(N, A * K * K)
        gy = (self.apy[..., None, None] + off[None, None, None, :]).expand(N, A, K, K).reshape(N, A * K * K)
        cov = TG.sample(self.cover, gx, gy, self.scale).reshape(N, A, K * K)
        slp = (TG.sample(self.slope, gx, gy, self.scale) / 5.0).reshape(N, A, K * K)
        return torch.cat([cov, slp], dim=2)

    def step(self, acts, auto_reset=True):
        d = self.dev; N, A, D = self.N, self.A, self.D; al = self._aalive().float()
        th = acts.float() * (math.pi / 4.0)                    # STEERING : actions 0-7 = caps (45 deg)
        spd = self.move * (acts < 8).float()                   # 8 = HOLD, 9 = SUPPRESS -> pas de mouvement
        _oax = self.apx.clone(); _oay = self.apy.clone()
        self.apx = (self.apx + torch.sin(th) * spd * al).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)
        self.apy = (self.apy + torch.cos(th) * spd * al).clamp(-self.terr_R * 0.99, self.terr_R * 0.99)
        if self.replica:
            _wall = self._sample_solid(self.apx, self.apy) > 0.5
            self.apx = torch.where(_wall, _oax, self.apx); self.apy = torch.where(_wall, _oay, self.apy)
        incover = TG.sample(self.cover, self.apx, self.apy, self.scale).clamp(max=1.0)   # couvert = terrain (atteint par steering)
        # --- feu des DEFENSEURS sur les attaquants (LOS du relief + portee + couvert) ---
        dmg_a = torch.zeros(N, A, device=d)
        for di in range(D):
            bx = self.dpx[:, di:di + 1].expand(N, A); by = self.dpy[:, di:di + 1].expand(N, A)
            los = self._losc(self.hm, self.apx, self.apy, bx, by, self.scale)
            dist = torch.sqrt((self.apx - self.dpx[:, di:di + 1]) ** 2 + (self.apy - self.dpy[:, di:di + 1]) ** 2)
            active = self._dalive()[:, di:di + 1].float() * (self.dsupp[:, di:di + 1] < 0.5).float()
            dmg_a += self.hit * los * (dist < self.fire_range).float() * active * (1.0 - 0.7 * incover)
        self.last_dmg_in = (dmg_a * al).detach()
        self.admg = (self.admg + dmg_a * al).clamp(max=0.95)
        # --- attaquants SUPPRESS (3) les defenseurs en LOS+portee ---
        self.dsupp.zero_(); dmg_d = torch.zeros(N, D, device=d); supp_act = (acts == 9) & self._aalive()
        self.last_supp = supp_act.float()                          # memo pour la conscience d'equipe (coordination)
        for ai in range(A):
            bx = self.apx[:, ai:ai + 1].expand(N, D); by = self.apy[:, ai:ai + 1].expand(N, D)
            los = self._losc(self.hm, self.dpx, self.dpy, bx, by, self.scale)
            dist = torch.sqrt((self.dpx - self.apx[:, ai:ai + 1]) ** 2 + (self.dpy - self.apy[:, ai:ai + 1]) ** 2)
            eff = los * (dist < self.fire_range).float() * supp_act[:, ai:ai + 1].float()
            self.dsupp = torch.maximum(self.dsupp, eff); dmg_d += 0.10 * eff   # tuer un defenseur en ~7 pas de feu
        self.ddmg = (self.ddmg + dmg_d).clamp(max=0.95)
        self.t = self.t + 1
        al2 = self._aalive()
        ndist = torch.sqrt(self.apx ** 2 + self.apy ** 2)
        neutralized = ~self._dalive().any(1)                       # VICTOIRE = defenseurs neutralises PAR LE FEU
        wiped = ~al2.any(1)
        timeout = self.t >= self.max_steps
        done = neutralized | wiped | timeout
        cur = (ndist * al2.float()).sum(1) / al2.float().sum(1).clamp(min=1) / self.scale   # dist a l'objectif (pour entrer en portee)
        losses = 1.0 - al2.float().sum(1) / self.A
        dk = (self.D - self._dalive().float().sum(1)) / self.D     # fraction defenseurs neutralises
        rew = (0.2 * (self.prev_d - cur)                           # leger shaping : se rapprocher (entrer en portee de feu)
               + 1.5 * (dk - self._prev_dk)                        # RECOMPENSE = neutraliser les defenseurs au feu
               - 0.005 + neutralized.float() * 1.0                 # bonus victoire
               - 0.4 * (wiped & ~neutralized).float())             # penalite aneantissement (CMDP : pertes)
        if self.suffer:
            rew = rew - 1.1 * (wiped & ~neutralized).float()        # la mort COUTE (total -1.5) -> decrocher le perdu devient rationnel
        self.prev_d = cur; self._prev_dk = dk
        if self.role_obs:                                          # OFFICIER : recompense la STRUCTURE feu+mouvement
            appui = ((self.role == 0) & al2).float(); assaut = ((self.role == 1) & al2).float()
            sup = (acts == 9).float(); mov = (acts < 8).float()
            a_sup = (sup * appui).sum(1) / appui.sum(1).clamp(min=1)     # appui qui CLOUE
            a_mov = (mov * assaut).sum(1) / assaut.sum(1).clamp(min=1)   # PENDANT que l'assaut AVANCE
            rew = rew + 0.05 * a_sup * a_mov
        info = {"neutralized": neutralized, "wiped": wiped, "losses": losses, "dkilled": dk}
        if auto_reset:
            self._reset(done.nonzero(as_tuple=True)[0])
        return self._obs(), rew, done.float(), info

    def scripted_advance(self):
        return [torch.ones(self.N, self.A, dtype=torch.long, device=self.dev)]  # placeholder API


if __name__ == "__main__":
    dev = "cuda:0"
    def run(relief, steps=60):
        e = AssaultTerrain(num_envs=2048, relief=relief, device=dev, seed=7)
        e.reset(); neut = wiped = 0.0; losssum = 0.0; nep = 0
        for _ in range(steps):
            th = torch.atan2(-e.apx, -e.apy)
            a = (torch.round(th / (math.pi / 4.0)) % 8).long()
            _, r, done, info = e.step(a)
            di = done.bool()
            if di.any():
                neut += info["neutralized"][di].float().sum().item()
                wiped += info["wiped"][di].float().sum().item()
                losssum += info["losses"][di].sum().item(); nep += int(di.sum())
        return neut / max(nep, 1), wiped / max(nep, 1), losssum / max(nep, 1), nep
    print("ASSAUT direct (foncer) — terrain PLAT vs RELIEF (foncer sans supprimer doit ECHOUER) :")
    for label, rel in [("plat (relief 1m)", 1.0), ("relief 35m", 35.0), ("relief 60m", 60.0)]:
        pr, pw, pl, npe = run(rel)
        print("  %-18s : defenseurs neutralises %3.0f%% | aneanti %3.0f%% | pertes moy %3.0f%% (%d episodes)"
              % (label, 100 * pr, 100 * pw, 100 * pl, npe))
