"""carte — CARTE TACTIQUE BROUILLARD-MEMOIRE (etage 1 du combat collaboratif).
Etat de situation PARTAGE et PERMANENT sur la grille terrain : la menace y est ce qui est SU,
PAS la verite-terrain. Elle VIEILLIT (decay), s'ELARGIT (diffusion), et se REMET A JOUR quand un
agent PERCOIT (LOS + portee). Le commandant lit la carte au lieu de l'ennemi en clair -> loi du +97
(le brouillard est la fonction forcante). 100% GPU vectorise, testee EN ISOLATION (discipline brique).

Convention monde<->grille IDENTIQUE a terrain_gpu (_w2g) : px,py dans [-R,R].
Canaux V1 : MENACE (intensite crue, vieillit) + FRAICHEUR (recence -> revele les TROUS).
"""
import math
import torch
import torch.nn.functional as F
import terrain_gpu as TG


class FogCarte:
    def __init__(self, N, R, device, G=28, T_forget=6.0, diffuse=0.15,
                 see_range=130.0, thr=0.08):
        self.N = N; self.R = float(R); self.dev = device; self.G = G
        self.aT = math.exp(-1.0 / max(T_forget, 1e-3))    # decay par PAS-HAUT (oubli)
        self.diffuse = diffuse                            # part diffusee (incertitude qui grandit)
        self.see_range = see_range; self.thr = thr
        self.threat = torch.zeros(N, G, G, device=device)  # canal MENACE (su, vieillit)
        self.fresh = torch.zeros(N, G, G, device=device)   # canal FRAICHEUR (recence -> trous)
        lin = (torch.arange(G, device=device).float() / (G - 1)) * 2 * self.R - self.R
        py, px = torch.meshgrid(lin, lin, indexing="ij")   # px[y,x]=lin[x], py[y,x]=lin[y]  (cf sample)
        self.cellpx = px.reshape(-1)                       # (G*G,) centre monde de chaque cellule
        self.cellpy = py.reshape(-1)

    def reset(self, idx=None):
        if idx is None:
            self.threat.zero_(); self.fresh.zero_()
        else:
            self.threat[idx] = 0.0; self.fresh[idx] = 0.0

    @torch.no_grad()
    def update(self, body):
        """Un pas de carte : PERCEVOIR -> VIEILLIR -> DIFFUSER -> RAFRAICHIR le su."""
        N, G, R = self.N, self.G, self.R; A = body.A; D = body.D
        al = body._aalive(); dal = body._dalive()                  # (N,A),(N,D)
        # --- PERCEVOIR : un defenseur est SU si un attaquant vivant a LOS + portee ---
        ax = body.apx.unsqueeze(2).expand(N, A, D).reshape(N, A * D)
        ay = body.apy.unsqueeze(2).expand(N, A, D).reshape(N, A * D)
        bx = body.dpx.unsqueeze(1).expand(N, A, D).reshape(N, A * D)
        by = body.dpy.unsqueeze(1).expand(N, A, D).reshape(N, A * D)
        los = TG.los_clear(body.hm, ax, ay, bx, by, R).reshape(N, A, D)
        dist = torch.sqrt((ax - bx) ** 2 + (ay - by) ** 2).reshape(N, A, D)
        seen = (los > 0.5) & (dist < self.see_range) & al.unsqueeze(2) & dal.unsqueeze(1)
        seen_d = seen.any(1) & dal                                 # (N,D) defenseurs SUS maintenant
        # splat des defenseurs vus dans une grille d'observation
        gx, gy = TG._w2g(body.dpx, body.dpy, R, G)                 # (N,D)
        cell = gy.round().long() * G + gx.round().long()          # (N,D) index cellule
        obs = torch.zeros(N, G * G, device=self.dev)
        obs.scatter_reduce_(1, cell, seen_d.float(), reduce="amax", include_self=True)
        obs = obs.view(N, G, G)
        # --- VIEILLIR (decay) + DIFFUSER (la tache s'elargit en vieillissant) ---
        t = self.threat * self.aT
        blur = F.avg_pool2d(t.unsqueeze(1), 3, 1, 1).squeeze(1)
        t = (1 - self.diffuse) * t + self.diffuse * blur
        # --- RAFRAICHIR : les cellules vues repassent au su (max) ---
        self.threat = torch.maximum(t, obs)
        self.fresh = torch.maximum(self.fresh * self.aT, obs)

    @torch.no_grad()
    def belief(self, cents):
        """Pour chaque element (centroide monde, (N,K,2)) : la menace CRUE la plus proche au-dessus
        du seuil -> (dirx,diry unitaires, dist monde, known). Rien de su : dir 0, dist=2R (loin/inconnu).
        Meme semantique que _nearest_def, mais SOURCE = la croyance brouillee, pas la verite."""
        N, K, _ = cents.shape; G = self.G
        cx = cents[..., 0].unsqueeze(2); cy = cents[..., 1].unsqueeze(2)   # (N,K,1)
        dx = self.cellpx.view(1, 1, -1) - cx                              # (N,K,G*G)
        dy = self.cellpy.view(1, 1, -1) - cy
        d2 = dx * dx + dy * dy
        believed = self.threat.view(N, 1, G * G) > self.thr               # (N,1,G*G)
        BIG = torch.tensor(1e18, device=self.dev)
        d2m = torch.where(believed, d2, BIG)
        j = d2m.argmin(2)                                                 # (N,K) cellue crue la + proche
        known = d2m.gather(2, j.unsqueeze(2)).squeeze(2) < 1e17           # (N,K)
        bdx = dx.gather(2, j.unsqueeze(2)).squeeze(2)
        bdy = dy.gather(2, j.unsqueeze(2)).squeeze(2)
        dist = torch.sqrt(bdx * bdx + bdy * bdy) + 1e-6
        dirx = torch.where(known, bdx / dist, torch.zeros_like(dist))
        diry = torch.where(known, bdy / dist, torch.zeros_like(dist))
        dist = torch.where(known, dist, torch.full_like(dist, 2 * self.R))
        return dirx, diry, dist, known.float()


if __name__ == "__main__":
    # ---- TEST EN ISOLATION (3090) : la brique tient-elle ses 3 promesses ? ----
    import sys
    from assault_terrain import AssaultTerrain
    DEV = sys.argv[1] if len(sys.argv) > 1 else "cuda:0"
    N, A, D = 256, 8, 8
    body = AssaultTerrain(num_envs=N, A=A, D=D, device=DEV, seed=3, relief=35.0, max_steps=200)
    body.reset()
    R = body.scale
    carte = FogCarte(N, R=R, device=DEV, G=28, T_forget=6.0, diffuse=0.15, see_range=130.0)
    print("=== CARTE brouillard-memoire : test en isolation (N=%d, G=%d, R=%.0f) ===" % (N, carte.G, R))

    # 1) PERCEVOIR : on rapproche les attaquants -> la carte doit se REMPLIR la ou on voit
    for _ in range(18):
        th = torch.atan2(-body.apx, -body.apy)
        a = (torch.round(th / (math.pi / 4.0)) % 8).long()         # foncer vers l'objectif
        body.step(a, auto_reset=False)
        carte.update(body)
    mass = carte.threat.sum(dim=(1, 2)).mean().item()
    occ = (carte.threat > carte.thr).float().mean().item() * 100
    print("  [1] PERCEVOIR  | masse menace moy %.2f | %.1f%% cellules crues (>0 attendu)" % (mass, occ))

    # 2) BELIEF : pour un element au sud, la direction crue doit pointer VERS l'anneau (objectif 0,0)
    cents = torch.zeros(N, 2, 2, device=DEV)
    cents[:, 0, 1] = -80.0                                          # element sud
    cents[:, 1, 0] = 80.0                                           # element est
    dx, dy, dist, known = carte.belief(cents)
    # element sud (y=-80) : la menace connue (anneau a r=12) est au NORD -> diry > 0
    kn = known[:, 0] > 0.5
    diry_sud = dy[kn, 0].mean().item() if kn.any() else float("nan")
    print("  [2] BELIEF     | %.0f%% elements-sud ont une menace SUE | diry moy %.2f (>0 = pointe au nord, vers l'anneau)"
          % (100 * known[:, 0].mean().item(), diry_sud))

    # 3) OUBLIER : plus aucune perception -> la masse doit DECROITRE (decay) vers 0
    m0 = carte.threat.sum(dim=(1, 2)).mean().item()
    carte.see_range = 0.0                                           # on aveugle la perception
    for _ in range(10):
        carte.update(body)
    m1 = carte.threat.sum(dim=(1, 2)).mean().item()
    print("  [3] OUBLIER    | masse %.2f -> %.2f apres 10 pas sans voir (decroit = memoire qui s'efface)" % (m0, m1))
    ok = (mass > 0) and (m1 < 0.6 * m0) and (known[:, 0].mean().item() > 0.3)
    print("  ====> %s" % ("PASS : la carte voit, croit, et oublie." if ok else "A REVOIR (voir nombres ci-dessus)."))
