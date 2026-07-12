"""Le terrain est-il EXPLOITABLE pour un assaut ? Pour chaque cap d'approche d'un objectif defendu, on mesure
l'EXPOSITION (fraction du trajet vue par un defenseur via LOS contre le relief). Si min(cap) << moyenne(cap),
choisir l'approche (le defile) paie fort -> la perception est un levier -> bon banc d'essai (vs le KOTH plat)."""
import math, torch
import terrain_gpu as TG
dev = "cuda:0"; g = torch.Generator(device=dev).manual_seed(0)
N, G, R = 2048, 64, 200.0
K, P, D = 12, 14, 4                       # caps d'approche, points/trajet, defenseurs
T = gen = TG.gen_terrain(N, G, dev, g, relief=35.0)   # relief modere
hm = T["hm"]
# defenseurs en petit cercle autour de l'objectif (0,0), legerement en hauteur (sur le relief)
dang = torch.arange(D, device=dev).float() / D * 2 * math.pi
dx = (12.0 * torch.cos(dang))[None, :].expand(N, D)   # (N,D)
dy = (12.0 * torch.sin(dang))[None, :].expand(N, D)
# caps d'approche
bearings = torch.arange(K, device=dev).float() / K * 2 * math.pi
ts = torch.linspace(0, 1, P, device=dev)              # le long du trajet (bord -> objectif)
expo = torch.zeros(N, K, device=dev)
for k in range(K):
    th = bearings[k]
    sx = R * math.sin(th); sy = R * math.cos(th)       # depart au bord
    # points du trajet (N,P) : du depart vers (0,0)
    pxk = (sx * (1 - ts))[None, :].expand(N, P)
    pyk = (sy * (1 - ts))[None, :].expand(N, P)
    seen = torch.zeros(N, P, device=dev)
    for d in range(D):                                  # vu par AU MOINS un defenseur ?
        bdx = dx[:, d:d+1].expand(N, P); bdy = dy[:, d:d+1].expand(N, P)
        seen = torch.maximum(seen, TG.los_clear(hm, pxk, pyk, bdx, bdy, R, K=20))
    expo[:, k] = seen.mean(1)                            # fraction du trajet exposee pour ce cap
best = expo.min(1).values; worst = expo.max(1).values; moy = expo.mean(1)
print("EXPOSITION du trajet d'assaut (1 = tout le trajet vu par un defenseur) :")
print("  meilleur cap (defile)  : %.0f%%" % (100 * best.mean()))
print("  cap moyen              : %.0f%%" % (100 * moy.mean()))
print("  pire cap (a decouvert) : %.0f%%" % (100 * worst.mean()))
gain = (moy.mean() - best.mean()) / moy.mean().clamp(min=1e-6)
print("  -> choisir le bon cap reduit l'exposition de %.0f%% vs un cap moyen" % (100 * gain))
print("VERDICT:", "TERRAIN EXPLOITABLE -> bon banc d'essai assaut" if best.mean() < 0.7 * moy.mean() else "peu exploitable (terrain a structurer)")
