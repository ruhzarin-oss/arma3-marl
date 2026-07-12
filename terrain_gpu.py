"""terrain_gpu — moteur de TERRAIN sur GPU (G-perc-0), brique réutilisable et TESTÉE EN ISOLATION.
Génère relief/pente/couvert/route par env, échantillonne au point de l'agent, calcule la LOS (ray-march
contre le relief). Sera câblé ensuite dans koth_gpu (perception soldats) + miroir Arma (contrat d'obs).
Discipline : on teste la brique seule avant de toucher au sim validé."""
import math
import torch


def gen_terrain(N, G, device, gen, relief=22.0, cover_thr=1.4, road_w=2.2):
    """N terrains G×G. Renvoie hm (relief, m), slope, cover/road (0/1), dcover/droad (dist en cellules)."""
    hm = torch.randn(N, G, G, generator=gen, device=device)
    for _ in range(4):                                   # lissage -> relief continu (collines)
        hm = (hm + torch.roll(hm, 1, 1) + torch.roll(hm, -1, 1) + torch.roll(hm, 1, 2) + torch.roll(hm, -1, 2)) / 5
    hm = hm - hm.amin((1, 2), keepdim=True)
    hm = hm / hm.amax((1, 2), keepdim=True).clamp(min=1e-6) * relief
    gy, gx = torch.gradient(hm, dim=(1, 2)); slope = (gx * gx + gy * gy).sqrt()
    cover = (slope > cover_thr * slope.mean((1, 2), keepdim=True)).float()   # crêtes/pentes = abris
    ang = torch.rand(N, generator=gen, device=device) * math.pi              # route : bande, direction/env
    ii = torch.arange(G, device=device).float() / (G - 1) * 2 - 1
    Y, X = torch.meshgrid(ii, ii, indexing="ij")
    proj = (X[None] * torch.cos(ang)[:, None, None] + Y[None] * torch.sin(ang)[:, None, None]).abs()
    road = (proj < road_w / G).float()
    return dict(hm=hm, slope=slope, cover=cover, road=road,
                dcover=_dist_field(cover, G), droad=_dist_field(road, G))


def _dist_field(mask, G, iters=16):
    """Distance approx (en cellules) au plus proche 1, par max-pool itéré (cheap, vectorisé)."""
    dist = torch.where(mask > 0.5, torch.zeros_like(mask), torch.full_like(mask, float(iters)))
    cur = mask
    for k in range(1, iters):
        cur = torch.nn.functional.max_pool2d(cur.unsqueeze(1), 3, 1, 1).squeeze(1)
        dist = torch.minimum(dist, torch.where(cur > 0.5, torch.full_like(dist, float(k)), torch.full_like(dist, float(iters))))
    return dist


def _w2g(px, py, R, G):
    return ((px + R) / (2 * R) * (G - 1)).clamp(0, G - 1), ((py + R) / (2 * R) * (G - 1)).clamp(0, G - 1)


def sample(field, px, py, R):
    """Bilinéaire : field (N,G,G) aux positions agents (N,A) -> (N,A)."""
    N, G, _ = field.shape
    gx, gy = _w2g(px, py, R, G)
    x0 = gx.floor().long(); y0 = gy.floor().long(); x1 = (x0 + 1).clamp(max=G - 1); y1 = (y0 + 1).clamp(max=G - 1)
    wx = gx - x0.float(); wy = gy - y0.float(); f = field.view(N, -1)
    def gat(yy, xx): return f.gather(1, yy * G + xx)
    return (gat(y0, x0) * (1 - wx) * (1 - wy) + gat(y0, x1) * wx * (1 - wy)
            + gat(y1, x0) * (1 - wx) * wy + gat(y1, x1) * wx * wy)


def los_clear(hm, ax, ay, bx, by, R, K=24, eye=1.7):
    """LOS A(N,A) -> B(N,A) contre le relief hm(N,G,G). 1=dégagée, 0=bloquée. (N,A)."""
    ts = torch.linspace(0, 1, K, device=hm.device)
    lx = ax[..., None] * (1 - ts) + bx[..., None] * ts
    ly = ay[..., None] * (1 - ts) + by[..., None] * ts
    N, A, _ = lx.shape
    terr = sample(hm, lx.reshape(N, -1), ly.reshape(N, -1), R).reshape(N, A, K)
    ha = sample(hm, ax, ay, R)[..., None]; hb = sample(hm, bx, by, R)[..., None]
    sight = ha * (1 - ts) + hb * ts + eye
    return (~(terr > sight).any(-1)).float()


if __name__ == "__main__":
    import time
    dev = "cuda:0"; g = torch.Generator(device=dev).manual_seed(0)
    N, G, R, A = 4096, 48, 256.0, 3
    t0 = time.time(); T = gen_terrain(N, G, dev, g); torch.cuda.synchronize(); t_gen = time.time() - t0
    print("gen %d terrains %dx%d : %.0f ms | relief %.1f m | couvert %.0f%% cellules | route %.1f%% cellules"
          % (N, G, G, t_gen * 1e3, T["hm"].amax().item(), 100 * T["cover"].mean().item(), 100 * T["road"].mean().item()))
    # agents/ennemis aléatoires dans [-R,R]
    ax = (torch.rand(N, A, generator=g, device=dev) * 2 - 1) * R; ay = (torch.rand(N, A, generator=g, device=dev) * 2 - 1) * R
    bx = (torch.rand(N, A, generator=g, device=dev) * 2 - 1) * R; by = (torch.rand(N, A, generator=g, device=dev) * 2 - 1) * R
    t0 = time.time()
    sl = sample(T["slope"], ax, ay, R)                       # pente sous les pieds
    dc = sample(T["dcover"], ax, ay, R)                      # dist au couvert (cellules)
    los = los_clear(T["hm"], ax, ay, bx, by, R)              # LOS agent->ennemi
    torch.cuda.synchronize(); t_perc = time.time() - t0
    print("perception (pente+dist_couvert+LOS) %d agents : %.0f ms" % (N * A, t_perc * 1e3))
    print("pente moy %.2f | dist_couvert moy %.1f cellules | LOS dégagée %.0f%% (ni 0 ni 100 = relief joue)"
          % (sl.mean().item(), dc.mean().item(), 100 * los.mean().item()))
    print("VRAM %.2f Go | shapes: hm%s slope_sample%s los%s" % (torch.cuda.max_memory_allocated() / 1e9, tuple(T["hm"].shape), tuple(sl.shape), tuple(los.shape)))
