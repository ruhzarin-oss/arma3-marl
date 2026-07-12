"""COMMANDER ENV — commandement hierarchique pour l'incrément 2 (commandant APPRIS, contrôle fin par element).
- ACTION (commandant, haut-niveau) : positions cibles continues de chaque element  -> (N, K, 2) dans [-1,1]
- BAS-NIVEAU (scripte) : chaque agent va a la position de SON element ; une fois en place, SUPPRIME le defenseur le + proche
- CORPS : AssaultTerrain (couvert, feu, suppression, LOS) — N envs sur GPU
Recompense = securiser le colis (un agent atteint l'objectif) + neutraliser + survivre - pertes - temps.
Le commandant apprend OU placer la base de feu et l'element de manoeuvre. Deploiement via le seam (cibles -> waypoints LAMBS)."""
import torch, math
from assault_terrain import AssaultTerrain
import terrain_gpu as TG


class CommanderEnv:
    def __init__(self, num_envs, A=8, K=2, D=8, device="cuda:0", seed=0, t_low=8, R_place=95.0,
                 max_steps=96, fire_range=110.0, secure_r=22.0, relief=35.0,
                 use_carte=False, carte_G=28, carte_T=6.0, carte_diffuse=0.15,
                 carte_see=130.0, carte_thr=0.08):
        self.body = AssaultTerrain(num_envs=num_envs, A=A, D=D, device=device, seed=seed, shell_obs=False,
                                   team_obs=False, suffer=False, relief=relief, fire_range=fire_range,
                                   secure_r=secure_r, max_steps=max_steps)
        self.N = num_envs; self.A = A; self.K = K; self.D = D; self.dev = device
        self.t_low = t_low; self.R_place = R_place; self.S = self.body.scale; self.fire_range = fire_range
        self.secure_r = secure_r; self.maxT = max(1, max_steps // t_low)
        # element par agent : moitie/moitie (A//K chacun)
        per = A // K
        self.elem = torch.arange(A, device=device) // per          # (A,) id d'element
        self.elem = self.elem.clamp(max=K - 1)
        self.obs_dim = 7 * K + 3
        self.act_dim = K * 2
        # --- CARTE brouillard-memoire (etage 1) : fogge la SOURCE de menace de l'obs (loi du +97) ---
        self.use_carte = use_carte
        if use_carte:
            from carte import FogCarte
            self.carte = FogCarte(num_envs, R=self.S, device=device, G=carte_G, T_forget=carte_T,
                                  diffuse=carte_diffuse, see_range=carte_see, thr=carte_thr)
        self.t_hi = torch.zeros(num_envs, dtype=torch.long, device=device)
        self._prevmin = torch.zeros(num_envs, device=device)
        self._bestmin = torch.zeros(num_envs, device=device)      # high-water mark : plus proche JAMAIS atteint
        self._prevdk = torch.zeros(num_envs, device=device)
        self._prevalive = torch.zeros(num_envs, device=device)

    def _emask(self, k):                                            # (N,A) bool : agents de l'element k, vivants
        return (self.elem == k).unsqueeze(0) & self.body._aalive()

    def _elem_centroid(self, k):                                   # (N,2) centroide de l'element k (agents vivants)
        m = self._emask(k).float()                                 # (N,A)
        w = m / m.sum(1, keepdim=True).clamp(min=1)
        cx = (self.body.apx * w).sum(1); cy = (self.body.apy * w).sum(1)
        return torch.stack([cx, cy], dim=1)                         # (N,2)

    def _nearest_def(self, px, py):                                 # px,py (N,?) -> dir(N,?,2)+dist(N,?) du defenseur vivant le + proche
        ex = self.body.dpx.unsqueeze(1) - px.unsqueeze(2)           # (N,?,D)
        ey = self.body.dpy.unsqueeze(1) - py.unsqueeze(2)
        BIG = torch.tensor(1e18, device=self.dev)
        d2 = torch.where(self.body._dalive().unsqueeze(1), ex * ex + ey * ey, BIG)
        j = d2.argmin(2)                                            # (N,?)
        bx = torch.gather(self.body.dpx, 1, j); by = torch.gather(self.body.dpy, 1, j)
        dx = bx - px; dy = by - py; dist = torch.sqrt(dx * dx + dy * dy) + 1e-6
        return dx, dy, dist

    def _min_obj_dist(self):                                        # (N,) distance du plus proche agent VIVANT a l'objectif (0,0)
        d = torch.sqrt(self.body.apx ** 2 + self.body.apy ** 2)
        d = torch.where(self.body._aalive(), d, torch.tensor(1e9, device=self.dev))
        return d.min(1).values

    def _obs(self):
        S = self.S; parts = []
        cents = torch.stack([self._elem_centroid(k) for k in range(self.K)], dim=1)   # (N,K,2)
        if self.use_carte:                                         # menace CRUE (brouillard) au lieu du clair
            bdx, bdy, bdist, _ = self.carte.belief(cents)         # (N,K) chacun
        for k in range(self.K):
            c = cents[:, k, :]                                     # (N,2)
            al = self._emask(k).float().sum(1) / max(1, (self.elem == k).sum().item())  # frac vivante
            covv = self._cover_at(c[:, 0:1], c[:, 1:2]).squeeze(1)
            if self.use_carte:                                     # source = la carte (le su), pas la verite
                tx = bdx[:, k]; ty = bdy[:, k]; tdist = (bdist[:, k] / S).clamp(max=2)
            else:                                                 # source = verite-terrain (comportement d'origine)
                dx, dy, dist = self._nearest_def(c[:, 0:1], c[:, 1:2])  # (N,1)
                ddn = dist.squeeze(1) + 1e-6
                tx = dx.squeeze(1) / ddn; ty = dy.squeeze(1) / ddn; tdist = (ddn / S).clamp(max=2)
            parts.append(torch.stack([c[:, 0] / S, c[:, 1] / S, al, covv, tx, ty, tdist], dim=1))
        g = torch.stack([self.body._dalive().float().sum(1) / self.D,
                         self.body._aalive().float().sum(1) / self.A,
                         self.t_hi.float() / self.maxT], dim=1)
        return torch.cat(parts + [g], dim=1)                        # (N, 7K+3)

    def _cover_at(self, px, py):
        return TG.sample(self.body.cover, px, py, self.S).clamp(max=1.0)

    def reset(self):
        self.body._reset(torch.arange(self.N, device=self.dev))
        self.t_hi[:] = 0
        self._prevmin = self._min_obj_dist() / self.S
        self._bestmin = self._prevmin.clone()
        self._prevdk = (self.body.ddmg >= self.body.dmg_dead).float().sum(1)
        self._prevalive = self.body._aalive().float().sum(1)
        if self.use_carte:
            self.carte.reset(); self.carte.update(self.body)
        return self._obs()

    def _lowlevel(self, targets):                                  # targets (N,A,2) monde -> actions discretes (N,A)
        px, py = self.body.apx, self.body.apy
        dx = targets[..., 0] - px; dy = targets[..., 1] - py
        dist = torch.sqrt(dx * dx + dy * dy) + 1e-6
        th = torch.atan2(dx, dy)                                    # corps : apx+=sin(th), apy+=cos(th)
        a_move = (torch.round(th / (math.pi / 4.0)) % 8).long()
        # en place (proche de la cible) -> supprimer si menace en portee+LOS, sinon tenir
        ndx, ndy, ndist = self._nearest_def(px, py)                # (N,A)
        los = self.body._losc(self.body.hm, px, py, px + ndx, py + ndy, self.S)
        can_supp = (ndist < self.fire_range) & (los > 0.5)
        in_place = dist < 16.0
        a = torch.where(in_place, torch.where(can_supp, torch.full_like(a_move, 9), torch.full_like(a_move, 8)), a_move)
        return a

    def step(self, action):                                        # action (N,K,2) dans [-1,1]
        tgt_e = action.clamp(-1, 1) * self.R_place                 # (N,K,2) offset / objectif(0,0)
        targets = tgt_e[:, self.elem, :]                           # (N,A,2) cible par agent
        for _ in range(self.t_low):
            a = self._lowlevel(targets)
            self.body.step(a, auto_reset=False)
        self.t_hi = self.t_hi + 1
        if self.use_carte:                                         # percevoir->vieillir->diffuser->rafraichir
            self.carte.update(self.body)
        # recompense
        mind = self._min_obj_dist() / self.S
        dk = (self.body.ddmg >= self.body.dmg_dead).float().sum(1)
        alive = self.body._aalive().float().sum(1)
        secured = (self._min_obj_dist() < self.secure_r)
        wiped = alive < 0.5
        prog = (self._bestmin - mind).clamp(min=0)                  # progres = NOUVEAU plus-proche (high-water mark) -> les morts ne penalisent plus
        self._bestmin = torch.minimum(self._bestmin, mind)
        timeout_nosec = (self.t_hi >= self.maxT) & (~secured) & (~wiped)
        rew = (1.2 * prog                                          # tirer vers l'objectif (fort)
               + 0.4 * (dk - self._prevdk)                         # neutraliser
               - 0.3 * (self._prevalive - alive)                  # pertes (DOUX)
               - 0.02                                             # cout/temps
               + 12.0 * secured.float()                           # SECURISER = mission (DOMINANT)
               - 2.0 * timeout_nosec.float())                     # malus PASSIVITE
        done = secured | wiped | (self.t_hi >= self.maxT)
        info = {"secured": secured, "wiped": wiped, "neut": ~self.body._dalive().any(1),
                "alive": alive, "dk": dk}
        self._prevmin = mind; self._prevdk = dk; self._prevalive = alive
        return self._obs(), rew, done, info

    def reset_done(self, done):
        idx = done.nonzero(as_tuple=True)[0]
        if len(idx) == 0: return
        self.body._reset(idx); self.t_hi[idx] = 0
        if self.use_carte: self.carte.reset(idx)                   # nouvel episode = on ne sait rien (trou total)
        nm = (self._min_obj_dist() / self.S)[idx]
        self._prevmin[idx] = nm; self._bestmin[idx] = nm
        self._prevdk[idx] = (self.body.ddmg >= self.body.dmg_dead).float().sum(1)[idx]
        self._prevalive[idx] = self.body._aalive().float().sum(1)[idx]


if __name__ == "__main__":
    DEV = "cuda:0"
    def run(policy_fn, label, N=1024, steps=14, seed=1):
        e = CommanderEnv(N, A=8, K=2, D=8, device=DEV, seed=seed)
        obs = e.reset(); sec = wip = neu = surv = nep = 0
        for _ in range(steps):
            act = policy_fn(e, obs)
            obs, rew, done, info = e.step(act)
            dm = done
            if dm.any():
                sec += info["secured"][dm].float().sum().item(); wip += info["wiped"][dm].float().sum().item()
                neu += info["neut"][dm].float().sum().item(); surv += (info["alive"] / 8)[dm].sum().item(); nep += int(dm.sum())
                e.reset_done(dm)
        print("  %-22s | securise %3.0f%% | neutralise %3.0f%% | survie %3.0f%% (%d ep)"
              % (label, 100 * sec / max(nep, 1), 100 * neu / max(nep, 1), 100 * surv / max(nep, 1), nep))
    print("=== CommanderEnv : validation (avant entrainement) ===")
    run(lambda e, o: torch.rand(e.N, e.K, 2, device=DEV) * 2 - 1, "commandant ALEATOIRE")
    # commandant code-main : element 0 = base de feu (sud, standoff), element 1 = assaut sur l'objectif
    def handcoded(e, o):
        a = torch.zeros(e.N, e.K, 2, device=DEV)
        a[:, 0, 0] = 0.0; a[:, 0, 1] = -0.45            # base de feu au sud (~43m)
        a[:, 1, 0] = 0.15; a[:, 1, 1] = 0.0             # assaut sur l'objectif (leger offset)
        return a
    run(handcoded, "commandant CODE-MAIN")
