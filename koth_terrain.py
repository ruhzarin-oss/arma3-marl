"""koth_terrain — KothGPU + TERRAIN (G-perc-0). Sous-classe : `koth_gpu` reste INTACT (utilisé par la ligue).
Ajoute : terrain par env (terrain_gpu), variables de perception dans l'obs (pente, dist couvert, dist+cap route,
LOS ennemi), et le RELIEF AFFECTE LE COMBAT (la LOS bloquée par une colline annule les dégâts via le hook)."""
import torch
from koth_gpu import KothGPU
import terrain_gpu as TG


class KothTerrain(KothGPU):
    def __init__(self, *a, terr_R=256.0, terr_G=48, terr_relief=22.0, los_K=20, **kw):
        self.terr_R = terr_R; self.terr_G = terr_G; self.terr_relief = terr_relief; self.los_K = los_K
        self._terr_ready = False                       # bloque _gen pendant le _reset_rows de super().__init__
        super().__init__(*a, **kw)
        self.obs_dim += 6                              # pente, dist_couvert, dist_route, route_dx, route_dy, los_ennemi
        N, G, d = self.N, self.terr_G, self.dev
        for nm in ("hm", "slope", "cover", "road", "dcover", "droad", "rdx", "rdy"):
            setattr(self, nm, torch.zeros(N, G, G, device=d))
        self._terr_ready = True
        self._gen_terrain(torch.arange(N, device=d))   # genere pour tous les envs

    def _gen_terrain(self, idx):
        if idx.numel() == 0: return
        T = TG.gen_terrain(idx.numel(), self.terr_G, self.dev, self.g, relief=self.terr_relief)
        for nm in ("hm", "slope", "cover", "road", "dcover", "droad"):
            getattr(self, nm)[idx] = T[nm]
        gy, gx = torch.gradient(T["droad"], dim=(1, 2))           # -grad(dist_route) pointe VERS la route
        nrm = (gx * gx + gy * gy).sqrt().clamp(min=1e-6)
        self.rdx[idx] = -gx / nrm; self.rdy[idx] = -gy / nrm

    def _reset_rows(self, idx):
        super()._reset_rows(idx)
        if getattr(self, "_terr_ready", False):
            self._gen_terrain(idx)

    def _nearest_enemy_xy(self, s):
        others = self._others(s); px, py = self.px[s], self.py[s]
        epx = torch.cat([self.px[o] for o in others], 1); epy = torch.cat([self.py[o] for o in others], 1)
        eal = torch.cat([self._alive(o) for o in others], 1)
        ex = epx.unsqueeze(1) - px.unsqueeze(2); ey = epy.unsqueeze(1) - py.unsqueeze(2)
        BIG = torch.tensor(1e18, device=self.dev)
        km = torch.where(eal.unsqueeze(1), ex * ex + ey * ey, BIG).argmin(2)
        return torch.gather(epx, 1, km), torch.gather(epy, 1, km)

    def _perc_vars(self, s):
        px, py = self.px[s], self.py[s]
        sl = TG.sample(self.slope, px, py, self.terr_R) / 5.0                 # pente (normalisee)
        dc = TG.sample(self.dcover, px, py, self.terr_R) / self.terr_G        # dist couvert (frac grille)
        dr = TG.sample(self.droad, px, py, self.terr_R) / self.terr_G         # dist route
        rdx = TG.sample(self.rdx, px, py, self.terr_R); rdy = TG.sample(self.rdy, px, py, self.terr_R)  # cap route
        bx, by = self._nearest_enemy_xy(s)
        los = TG.los_clear(self.hm, px, py, bx, by, self.terr_R, K=self.los_K)   # LOS ennemi (1/0)
        return torch.stack([sl, dc, dr, rdx, rdy, los], dim=2)                # (N,A,6)

    def _obs(self, s):
        return torch.cat([super()._obs(s), self._perc_vars(s)], dim=2)

    def _dmg_terrain_mult(self, s, km):
        """Hook : la LOS du relief module les degats. km = index ennemi vise (N,A) dans l'union des autres."""
        others = self._others(s)
        epx = torch.cat([self.px[o] for o in others], 1); epy = torch.cat([self.py[o] for o in others], 1)
        bx = torch.gather(epx, 1, km); by = torch.gather(epy, 1, km)
        return TG.los_clear(self.hm, self.px[s], self.py[s], bx, by, self.terr_R, K=self.los_K)


if __name__ == "__main__":
    import time
    dev = "cuda:0"
    NE = 512
    flat = KothGPU(num_envs=NE, device=dev, seed=1)
    terr = KothTerrain(num_envs=NE, device=dev, seed=1)
    of = flat.reset(); ot = terr.reset()
    print("obs_dim plat=%d | terrain=%d (attendu +6) | obs terrain shape=%s" % (flat.obs_dim, terr.obs_dim, tuple(ot[0].shape)))
    assert ot[0].shape[-1] == of[0].shape[-1] + 6, "obs non etendue de 6 !"
    # joue 40 pas scriptes des deux cotes, compare les degats cumules (la LOS du relief doit en bloquer)
    df = dt = 0.0
    for _ in range(40):
        of, rf, donef, inf = flat.step(flat.scripted_acts())
        ot, rt, donet, intt = terr.step(terr.scripted_acts())
        df += flat.dmg.sum().item(); dt += terr.dmg.sum().item()
    los_mean = terr._perc_vars(0)[..., 5].mean().item()
    print("degats cumules : plat=%.0f | terrain=%.0f (terrain < plat = LOS bloque des tirs)" % (df, dt))
    print("LOS degagee moyenne (au contact) = %.0f%% | pente moy obs=%.2f" % (100 * los_mean, terr._perc_vars(0)[..., 0].mean().item()))
    print("VRAM %.2f Go | OK : terrain cable, perception dans l'obs, LOS au combat" % (torch.cuda.max_memory_allocated() / 1e9))
