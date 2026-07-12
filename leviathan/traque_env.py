"""traque_env.py — POURSUITE-EVASION : le PAYS (traque, capteurs) vs 40 FS (se cacher + actions coercitives).

Sur l'architecture island_stratis (22 noeuds types). Vectorise (N mondes GPU).
- 40 FS : se deplacent vers un noeud cible, posture (vite/prudent/CACHE = basse exposition), et DETRUISENT
  le noeud a portee = action coercitive (le type du noeud). Score de COERCITION accumule.
- LE PAYS : DETECTION = couverture des CAPTEURS vivants (radars/comms) + patrouille de base + SURGE
  (concentration la ou il a vu). Un FS detecte est neutralise (proba ~ detection x exposition).
- COEUR REFLEXIF : les FS qui detruisent les capteurs FONT CHUTER la couverture -> la traque devient aveugle
  -> ils operent libres. -> emergence : aveugler d'abord, frapper ensuite ; le pays apprend a proteger ses yeux.

v0 : pays SCRIPTE (surge reactif), FS pilotes (smoke scripte ici). Apprentissage FS + co-evolution = couche suivante.
Terrain LOS (se cacher dans le relief) = raffinement a brancher apres (heightmap Stratis).
"""
import math, torch
from island_stratis import NODES, TYPE_META, SENSOR_TYPES


class TraqueEnv:
    def __init__(self, num_envs, device="cuda:0", n_fs=40, max_steps=60,
                 R_radar=1300.0, R_attack=70.0, move=130.0,
                 base_patrol=0.012, cov_w=0.11, surge_boost=0.085, surge_scale=750.0,
                 grid_g=6, n_teams=6, fs_evade=1.0, relief=True, smoke_max=3, seed=0):
        self.N = num_envs; self.dev = device; self.n_fs = n_fs; self.M = len(NODES); self.max_steps = max_steps
        self.R_radar = R_radar; self.R_attack = R_attack; self.move = move
        self.base_patrol = base_patrol; self.cov_w = cov_w; self.surge_boost = surge_boost; self.surge_scale = surge_scale
        self.fs_evade = fs_evade   # <1 = FS d'elite ameliorees (NVG/stealth/ACE) : bien plus dures a detecter/neutraliser
        torch.manual_seed(seed)
        self.npos = torch.tensor([[x, y] for _, x, y, _ in NODES], dtype=torch.float32, device=device)
        self.ntype = [t for _, _, _, t in NODES]
        self.nw = torch.tensor([TYPE_META[t]["coercion"] for t in self.ntype], device=device)
        # GARNISON (coût de combat, calibré sur Arma : des défenseurs gardent chaque nœud et tuent les assaillants) :
        # force ∝ valeur du nœud (le QG = le plus défendu) -> assaillir un nœud précieux coûte des pertes
        self.garrison = self.nw.clone(); self.Rg = 230.0; self.gar_k = 0.03
        self.sensor = torch.tensor([t in SENSOR_TYPES for t in self.ntype], device=device)
        xs, ys = self.npos[:, 0], self.npos[:, 1]
        self.xmin, self.xmax = float(xs.min()), float(xs.max()); self.ymin, self.ymax = float(ys.min()), float(ys.max())
        # GRILLE sur TOUT Stratis : G x G zones ; le pays place n_teams equipes dessus
        self.G = grid_g; self.n_teams = n_teams; self.Z = grid_g * grid_g
        mx = (self.xmax - self.xmin) * 0.15 + 300.0; my = (self.ymax - self.ymin) * 0.15 + 300.0
        self.gx0 = self.xmin - mx; self.gy0 = self.ymin - my
        self.cellx = (self.xmax + mx - self.gx0) / self.G; self.celly = (self.ymax + my - self.gy0) / self.G
        zc = [[self.gx0 + (gx + 0.5) * self.cellx, self.gy0 + (gy + 0.5) * self.celly]
              for gy in range(self.G) for gx in range(self.G)]
        self.zcenters = torch.tensor(zc, dtype=torch.float32, device=device)              # (Z,2)
        nz = self._zone_of(self.npos[:, 0], self.npos[:, 1])                               # (M,) zone de chaque noeud
        self.node_onehot = torch.zeros(self.M, self.Z, device=device); self.node_onehot[torch.arange(self.M), nz] = 1.0
        # RELIEF : le VRAI Stratis (bake getTerrainHeightASL) si dispo, sinon un relief representatif (meme role)
        self.relief = relief; self.R_rays = 8; self.ray_d = 350.0
        import os as _os, json as _json
        _hm = "/home/younes/arma3-marl/leviathan/stratis_heightmap.json"
        if relief and _os.path.exists(_hm):
            _d = _json.load(open(_hm)); self.HM = torch.tensor(_d["H"], dtype=torch.float32, device=device)
            self.HN = int(_d["n"]); self.hx0 = float(_d["x0"]); self.hy0 = float(_d["y0"]); self.hres_x = self.hres_y = float(_d["res"])
        else:
            self.HN = 96; self.hx0 = self.gx0; self.hy0 = self.gy0
            self.hres_x = (self.cellx * self.G) / (self.HN - 1); self.hres_y = (self.celly * self.G) / (self.HN - 1)
            gg = torch.linspace(0, 1, self.HN, device=device); GY, GX = torch.meshgrid(gg, gg, indexing="ij")
            H = 210.0 * torch.exp(-((GY - 0.5) ** 2) / 0.07) * (0.6 + 0.4 * torch.sin(GX * 6.0))
            gen = torch.Generator(device=device); gen.manual_seed(7)
            for _ in range(9):
                cx = torch.rand(1, generator=gen, device=device); cy = torch.rand(1, generator=gen, device=device)
                amp = 70 + 130 * torch.rand(1, generator=gen, device=device); w = 0.02 + 0.05 * torch.rand(1, generator=gen, device=device)
                H = H + amp * torch.exp(-(((GX - cx) ** 2 + (GY - cy) ** 2) / w))
            self.HM = H
        ang = torch.arange(self.R_rays, device=device, dtype=torch.float32) * (6.2831853 / self.R_rays)
        self.ray_dx = torch.cos(ang); self.ray_dy = torch.sin(ang)                               # coque de perception (8 rayons)
        dv = device
        self.fs_x = torch.zeros(self.N, n_fs, device=dv); self.fs_y = torch.zeros(self.N, n_fs, device=dv)
        self.fs_alive = torch.ones(self.N, n_fs, device=dv); self.node_alive = torch.ones(self.N, self.M, device=dv)
        self.coercion = torch.zeros(self.N, device=dv); self.prevco = torch.zeros(self.N, device=dv)
        self.surge = torch.zeros(self.N, 2, device=dv); self.last_det = torch.zeros(self.N, 2, device=dv)
        self.zheat = torch.zeros(self.N, self.Z, device=dv); self.decoy_heat = torch.zeros(self.N, self.Z, device=dv)
        self.smoke = torch.zeros(self.N, self.Z, device=dv); self.smoke_max = smoke_max
        self.smoke_charges = torch.zeros(self.N, self.n_fs, device=dv)        # stock de fumigenes (limite)
        self.team_pos = torch.zeros(self.N, self.n_teams, 2, device=dv)       # positions des equipes de traque (pour le RECON)
        self.t = torch.zeros(self.N, dtype=torch.long, device=dv)
        self.EXPO = torch.tensor([1.0, 0.5, 0.25, 0.5, 0.5], device=dv); self.SPD = torch.tensor([1.0, 0.7, 0.4, 0.5, 0.5], device=dv)  # 3=LEURRE 4=FUMIGENE
        self.cx = (self.xmin + self.xmax) / 2; self.cy = (self.ymin + self.ymax) / 2; self.S = 4000.0
        self.n_target = self.M; self.n_post = 5   # 0 vite / 1 prudent / 2 cache / 3 LEURRE (genjutsu) / 4 FUMIGENE
        self.obs_dim = 6 + self.M * 5 + 5 + (self.R_rays + 1 + 3 if self.relief else 0)   # +3 RECON, +1 NUIT (glob)
        self.country_obs_dim = 3 * self.Z + 4   # +1 = NUIT
        self.night = torch.zeros(self.N, device=device)   # 1 = nuit : le pays voit moins (pas de NVG), les FS gardent l'avantage
        self.reset()

    def _zone_of(self, x, y):
        gx = torch.clamp(((x - self.gx0) / self.cellx).long(), 0, self.G - 1)
        gy = torch.clamp(((y - self.gy0) / self.celly).long(), 0, self.G - 1)
        return gy * self.G + gx

    def _height(self, x, y):
        j = torch.clamp(((x - self.hx0) / self.hres_x).long(), 0, self.HN - 1)
        i = torch.clamp(((y - self.hy0) / self.hres_y).long(), 0, self.HN - 1)
        return self.HM[i, j]

    def _los_clear(self, ax, ay, bx, by, eye=2.0, S=7):
        ha = self._height(ax, ay) + eye; hb = self._height(bx, by) + eye
        clear = torch.ones(torch.broadcast_shapes(ax.shape, bx.shape), dtype=torch.bool, device=self.dev)
        for k in range(1, S):
            t = k / S; px = ax + (bx - ax) * t; py = ay + (by - ay) * t
            clear = clear & (self._height(px, py) <= ha + (hb - ha) * t + 1.0)
        return clear

    def _perception(self):
        # COQUE de terrain par FS (la perception qui permet d'exploiter le relief, logique +97)
        hself = self._height(self.fs_x, self.fs_y)
        ray = torch.stack([(self._height(self.fs_x + self.ray_dx[r] * self.ray_d, self.fs_y + self.ray_dy[r] * self.ray_d) - hself) / 120.0
                           for r in range(self.R_rays)], dim=2)                              # gain d'altitude par direction = ou est le couvert
        sp = self.npos[self.sensor]; sa = self.node_alive[:, self.sensor]
        ax = self.fs_x[:, :, None]; ay = self.fs_y[:, :, None]
        d2 = (ax - sp[None, None, :, 0]) ** 2 + (ay - sp[None, None, :, 1]) ** 2
        d2 = torch.where(sa[:, None, :] > 0, d2, torch.full_like(d2, 1e18)); km = d2.argmin(2)
        hidden = (~self._los_clear(self.fs_x, self.fs_y, sp[:, 0][km], sp[:, 1][km])).float().unsqueeze(2)  # suis-je en defile ?
        # RECON (Sharingan / reseau d'espions) : distance + direction de l'equipe de traque la plus proche
        tddx = self.team_pos[:, None, :, 0] - self.fs_x[:, :, None]; tddy = self.team_pos[:, None, :, 1] - self.fs_y[:, :, None]
        td2 = tddx * tddx + tddy * tddy; tkm = td2.argmin(2)
        recon = torch.stack([torch.clamp(torch.sqrt(td2.min(2).values) / self.S, 0, 1),
                             torch.gather(tddx, 2, tkm[:, :, None])[:, :, 0] / self.S,
                             torch.gather(tddy, 2, tkm[:, :, None])[:, :, 0] / self.S], dim=2)
        return torch.cat([ray, hidden, recon], dim=2)                                       # (N,n_fs,R+1+3)

    def obs_country(self):
        # vue GRILLE : le pays ne distingue PAS le vrai (zheat) du LEURRE (decoy_heat) -> il peut se faire avoir
        tot = self.zheat + self.decoy_heat; zh = tot / (tot.amax(1, keepdim=True) + 1e-6)
        zval = (self.node_alive * (self.nw / 10.0)[None, :]) @ self.node_onehot
        zsens = (self.node_alive * self.sensor.float()[None, :]) @ self.node_onehot
        g = torch.stack([self.node_alive[:, self.sensor].sum(1) / 5.0, self.coercion / 88.0, self.t.float() / self.max_steps, self.night], dim=1)
        return torch.cat([zh, zval, zsens, g], dim=1)

    def _obs(self):
        S = self.S; cov = self.coverage()
        self_f = torch.stack([(self.fs_x - self.cx) / S, (self.fs_y - self.cy) / S, self.fs_alive, cov / 5.0,
                              (self.surge[:, 0:1] - self.fs_x) / S, (self.surge[:, 1:2] - self.fs_y) / S], dim=2)
        dx = (self.npos[None, None, :, 0] - self.fs_x[:, :, None]) / S
        dy = (self.npos[None, None, :, 1] - self.fs_y[:, :, None]) / S
        nal = self.node_alive[:, None, :].expand(self.N, self.n_fs, self.M)
        w = (self.nw / 10.0)[None, None, :].expand(self.N, self.n_fs, self.M)
        se = self.sensor.float()[None, None, :].expand(self.N, self.n_fs, self.M)
        nodes_f = torch.stack([nal, dx, dy, w, se], dim=3).reshape(self.N, self.n_fs, self.M * 5)
        g = torch.stack([self.fs_alive.mean(1), self.coercion / 88.0,
                         self.node_alive[:, self.sensor].sum(1) / 5.0, self.t.float() / self.max_steps, self.night], dim=1)
        glob = g[:, None, :].expand(self.N, self.n_fs, 5)
        out = torch.cat([self_f, nodes_f, glob], dim=2)
        if self.relief:
            out = torch.cat([out, self._perception()], dim=2)                            # la coque de perception du terrain
        return out

    def reset(self, idx=None):
        if idx is None:
            idx = torch.arange(self.N, device=self.dev)
        n = idx.numel()
        self.fs_x[idx] = torch.rand(n, self.n_fs, device=self.dev) * (self.xmax - self.xmin) + self.xmin
        self.fs_y[idx] = self.ymin - 250 + torch.rand(n, self.n_fs, device=self.dev) * 300   # infiltration par le sud
        self.fs_alive[idx] = 1.0; self.node_alive[idx] = 1.0; self.coercion[idx] = 0.0; self.prevco[idx] = 0.0
        ctr = torch.tensor([(self.xmin + self.xmax) / 2, (self.ymin + self.ymax) / 2], device=self.dev)
        self.surge[idx] = ctr; self.last_det[idx] = ctr; self.zheat[idx] = 0.0; self.decoy_heat[idx] = 0.0; self.smoke[idx] = 0.0
        self.smoke_charges[idx] = self.smoke_max; self.team_pos[idx] = 0.0
        self.t[idx] = 0; self.night[idx] = (torch.rand(n, device=self.dev) < 0.4).float()   # ~40% des episodes = nuit

    def coverage(self):
        sp = self.npos[self.sensor]; sa = self.node_alive[:, self.sensor]
        ax = self.fs_x[:, :, None]; ay = self.fs_y[:, :, None]; bx = sp[None, None, :, 0]; by = sp[None, None, :, 1]
        inr = ((ax - bx) ** 2 + (ay - by) ** 2) < self.R_radar ** 2
        if self.relief:
            inr = inr & self._los_clear(ax, ay, bx, by)                                  # le terrain masque la vue du capteur
        return (inr.float() * sa[:, None, :]).sum(-1)                                     # (N,n_fs)

    def step(self, targets, posture, country_zones=None):
        a = self.fs_alive; tgt = targets.long().clamp(0, self.M - 1); post = posture.long().clamp(0, 4)
        tx = self.npos[:, 0][tgt]; ty = self.npos[:, 1][tgt]
        # 1) deplacement vers la cible (posture = vitesse)
        ddx = tx - self.fs_x; ddy = ty - self.fs_y; dd = torch.sqrt(ddx * ddx + ddy * ddy).clamp(min=1.0)
        step_m = torch.minimum(dd, self.SPD[post] * self.move)
        self.fs_x = self.fs_x + ddx / dd * step_m * a; self.fs_y = self.fs_y + ddy / dd * step_m * a
        # 2) ATTAQUE : FS a portee d'un noeud vivant -> detruit (action coercitive) -> coercition + effet
        ndist = torch.sqrt((self.fs_x - tx) ** 2 + (self.fs_y - ty) ** 2)
        can = (ndist < self.R_attack) & (a > 0) & (self.node_alive.gather(1, tgt) > 0)
        attacked = torch.zeros(self.N, self.M, device=self.dev); attacked.scatter_add_(1, tgt, can.float())
        newdes = (attacked > 0) & (self.node_alive > 0)
        self.coercion = self.coercion + (newdes.float() * self.nw).sum(1)
        self.node_alive = self.node_alive * (~newdes).float()                            # capteur detruit -> couverture chute
        # 3) DETECTION + attrition : couverture capteurs + patrouille + surge, module par l'exposition (se cacher protege)
        # le PAYS place n_teams EQUIPES sur la grille (surge = somme de bulles) ; sinon scripte (1 bulle qui suit)
        cov = self.coverage()
        if country_zones is not None:
            ctr = self.zcenters[country_zones.long().clamp(0, self.Z - 1)]               # (N, n_teams, 2)
            self.team_pos = ctr                                                          # memorise pour le RECON des FS
            ax = self.fs_x[:, :, None]; ay = self.fs_y[:, :, None]; bx = ctr[:, None, :, 0]; by = ctr[:, None, :, 1]
            bub = self.surge_boost * torch.exp(-((ax - bx) ** 2 + (ay - by) ** 2) / (self.surge_scale ** 2))
            if self.relief:
                bub = bub * self._los_clear(ax, ay, bx, by).float()                      # une equipe ne voit le FS que si LOS degagee
            surge = bub.sum(-1)
        else:
            sdx = self.fs_x - self.surge[:, 0:1]; sdy = self.fs_y - self.surge[:, 1:2]
            surge = self.surge_boost * torch.exp(-(sdx * sdx + sdy * sdy) / (self.surge_scale ** 2))
        fz = self._zone_of(self.fs_x, self.fs_y)
        use_smoke = ((post == 4) & (a > 0) & (self.smoke_charges > 0)).float()           # FUMIGENE : stock LIMITE (3)
        self.smoke = self.smoke * 0.7; self.smoke.scatter_add_(1, fz, use_smoke * 2.0); self.smoke_charges = self.smoke_charges - use_smoke
        smoke_at = self.smoke.gather(1, fz)
        pdet = torch.clamp((self.base_patrol + self.cov_w * cov + surge) * self.EXPO[post], 0, 1) * self.fs_evade * a
        pdet = pdet * (1.0 - 0.9 * torch.clamp(smoke_at, 0, 1))                            # l'ecran de fumee casse la detection
        pdet = pdet * (1.0 - 0.7 * self.night[:, None])                                    # NUIT : le pays voit beaucoup moins (pas de NVG)
        spotted = (torch.rand(self.N, self.n_fs, device=self.dev) < pdet) & (a > 0)
        self.fs_alive = self.fs_alive * (~spotted).float()
        # FEU de GARNISON : chaque nœud défendu vivant tire sur les FS proches (assaut = risque, la fumée protège un peu)
        gar = self.garrison[None, :] * self.node_alive
        gdx = self.fs_x[:, :, None] - self.npos[None, None, :, 0]; gdy = self.fs_y[:, :, None] - self.npos[None, None, :, 1]
        gexp = (gar[:, None, :] * torch.exp(-(gdx * gdx + gdy * gdy) / (self.Rg ** 2))).sum(-1)
        pgar = torch.clamp(self.gar_k * gexp, 0, 0.6) * (1.0 - 0.7 * torch.clamp(smoke_at, 0, 1)) * self.fs_alive
        pgar = pgar * (1.0 - 0.6 * self.night[:, None])                                    # NUIT : la garnison voit mal les FS approcher -> ils se faufilent aux noeuds
        killed_gar = (torch.rand(self.N, self.n_fs, device=self.dev) < pgar) & (self.fs_alive > 0)
        self.fs_alive = self.fs_alive * (~killed_gar).float()
        sp_any = spotted.float().sum(1, keepdim=True)
        cx = (self.fs_x * spotted.float()).sum(1, keepdim=True) / sp_any.clamp(min=1)
        cy = (self.fs_y * spotted.float()).sum(1, keepdim=True) / sp_any.clamp(min=1)
        mv = (sp_any > 0).float()
        self.last_det = self.last_det * (1 - mv) + torch.cat([cx, cy], 1) * mv
        if country_zones is None:
            self.surge = self.surge * (1 - 0.5 * mv) + torch.cat([cx, cy], 1) * (0.5 * mv)
        self.zheat = self.zheat * 0.85; self.zheat.scatter_add_(1, fz, spotted.float())
        # LEURRE (genjutsu) : un FS en posture 3 pose un faux signal a sa zone -> le pays ne le distingue pas du vrai
        self.decoy_heat = self.decoy_heat * 0.8; self.decoy_heat.scatter_add_(1, fz, ((post == 3) & (a > 0)).float())
        self.n_killed = spotted.float().sum(1) + killed_gar.float().sum(1)
        self.t = self.t + 1
        co_gain = self.coercion - self.prevco; self.prevco = self.coercion.clone()
        rew_fs = co_gain[:, None] * a - 0.4 * spotted.float() - 0.4 * killed_gar.float()   # coercition partagee - mort (détection OU garnison)
        done = (self.t >= self.max_steps) | (self.fs_alive.sum(1) <= 0) | (self.node_alive.sum(1) <= 0)
        rew_country = -co_gain + 0.3 * self.n_killed                                  # le pays : empecher la coercition + neutraliser
        info = {"coercion": self.coercion.detach().clone(), "fs_alive": self.fs_alive.sum(1).detach(),
                "nodes_left": self.node_alive.sum(1).detach(), "sensors_left": self.node_alive[:, self.sensor].sum(1).detach(),
                "rew_country": rew_country.detach()}
        di = torch.where(done)[0]
        if di.numel() > 0:
            self.reset(di)
        return self._obs(), rew_fs, done.float(), info

    def scripted_fs(self, blind_first=True):
        # heuristique FS : viser le noeud vivant le plus proche (capteurs PRIORITAIRES si blind_first) ; se cacher si detecte
        nd = torch.sqrt((self.fs_x[:, :, None] - self.npos[None, None, :, 0]) ** 2 +
                        (self.fs_y[:, :, None] - self.npos[None, None, :, 1]) ** 2)       # (N,n_fs,M)
        bonus = self.sensor.float()[None, None, :] * (2500.0 if blind_first else 0.0)
        score = nd - bonus
        score = torch.where(self.node_alive[:, None, :] > 0, score, torch.full_like(score, 1e9))
        targets = score.argmin(-1)
        posture = torch.where(self.coverage() > 0, torch.full_like(targets, 2), torch.zeros_like(targets))
        return targets, posture


if __name__ == "__main__":
    import statistics as st
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    def run(blind_first):
        e = TraqueEnv(num_envs=2048, device=dev, seed=1)
        co = []; alv = []; sens = []
        for _ in range(e.max_steps * 3):
            tg, po = e.scripted_fs(blind_first=blind_first)
            _, r, d, info = e.step(tg, po)
            di = torch.where(d > 0)[0]
            for i in di.tolist():
                co.append(info["coercion"][i].item()); alv.append(info["fs_alive"][i].item()); sens.append(info["sensors_left"][i].item())
        print("  coercion moy %.1f/88 | FS survivants %.1f/40 | capteurs restants %.1f/5" % (st.mean(co), st.mean(alv), st.mean(sens)))
    print("=== SMOKE traque (FS scriptes vs pays scripte) ===")
    print("FS qui AVEUGLENT d'abord (detruisent les capteurs) :"); run(True)
    print("FS qui foncent sur la coercition (sans aveugler)   :"); run(False)
