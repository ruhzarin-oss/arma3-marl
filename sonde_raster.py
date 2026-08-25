#!/usr/bin/env python3
"""sonde_raster — AVANT TOUT ENTRAINEMENT. Trois questions, dans cet ordre.

  1. LE REPERE EST-IL LE BON ?  (l objectif est-il vraiment EN HAUT, l ennemi au bon pixel)
  2. LES CANAUX SONT-ILS VIVANTS ?  (un canal constant est une entree morte par construction)
  3. COMBIEN CA COUTE ?  (mesurer avant de lancer un run cher)

Aucune de ces trois n exige d entrainer quoi que ce soit.
"""
import sys, time, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from raster import raster, brouilleur, CANAUX_DEFAUT, _grille_ego

DEV = "cuda:0"
K, SPAN = 16, 120.0

print("=" * 78)
print(" SONDE RASTER — trois questions avant tout entrainement")
print("=" * 78)

e = B.monde(256, 11); e.reset()
print("\n  monde : N=%d A=%d D=%d  scale=%.0f m  obs vectorielle = %d entrees"
      % (e.N, e.A, e.D, e.scale, e._obs().shape[-1]))

r = raster(e, K=K, span=SPAN)
print("  raster : %s   (N, A, canaux, K, K)" % (tuple(r.shape),))
assert r.shape == (e.N, e.A, len(CANAUX_DEFAUT), K, K)

# ---------------------------------------------------------------- 1. LE REPERE
print("\n─── 1. LE REPERE ────────────────────────────────────────────────────")
gx, gy = _grille_ego(e, K, SPAN)
dobj = torch.sqrt(gx ** 2 + gy ** 2)           # distance de chaque cellule a l objectif (origine)
# l objectif est EN HAUT  =>  la derniere ligne (i=K-1, "avant") doit etre PLUS PRES que la premiere
avant = dobj[:, :, -1, :].mean()
arriere = dobj[:, :, 0, :].mean()
print("  distance moyenne a l objectif — ligne AVANT %.1f m | ligne ARRIERE %.1f m" % (avant, arriere))
print("  ecart attendu ~= span = %.0f m ... mesure %.1f m   %s"
      % (SPAN, arriere - avant, "OK" if (arriere - avant) > SPAN * 0.8 else "ECHEC"))

# le lateral doit etre SYMETRIQUE (aucune preference gauche/droite)
g = dobj[:, :, :, 0].mean(); dr = dobj[:, :, :, -1].mean()
print("  lateral gauche %.1f m | droite %.1f m  -> ecart %.2f m   %s"
      % (g, dr, abs(g - dr), "OK (symetrique)" if abs(g - dr) < 1.0 else "ECHEC"))

# CONTROLE POSITIF DU SPLAT : le canal ennemis doit sommer au nombre de defenseurs DANS le champ
ce = r[:, :, CANAUX_DEFAUT.index("ennemis")]
dx = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
th0 = torch.atan2(-e.apx, -e.apy).unsqueeze(2)
f = dx * torch.sin(th0) + dy * torch.cos(th0); l = dx * torch.cos(th0) - dy * torch.sin(th0)
dedans = ((f.abs() <= SPAN / 2) & (l.abs() <= SPAN / 2) & e._dalive().unsqueeze(1)).float().sum(2)
print("  splat ennemis : somme du canal %.3f | defenseurs vivants dans le champ %.3f   %s"
      % (ce.sum(), dedans.sum(), "OK" if abs(float(ce.sum()) - float(dedans.sum())) < 1e-2 else "ECHEC"))

# ---------------------------------------------------------------- 2. LES CANAUX
print("\n─── 2. LES CANAUX SONT-ILS VIVANTS ? ────────────────────────────────")
print("  %-10s %8s %8s %8s %8s   %s" % ("canal", "moy", "ecart-t", "min", "max", "verdict"))
morts = []
for i, nom in enumerate(CANAUX_DEFAUT):
    c = r[:, :, i]
    m, s_, lo, hi = float(c.mean()), float(c.std()), float(c.min()), float(c.max())
    # un canal est VIVANT s il varie DANS une image (pas seulement entre images)
    intra = float(c.reshape(e.N * e.A, -1).std(dim=1).mean())
    v = "vivant" if intra > 1e-4 else "MORT (constant dans l image)"
    if intra <= 1e-4: morts.append(nom)
    print("  %-10s %8.4f %8.4f %8.4f %8.4f   intra-image %.5f  %s" % (nom, m, s_, lo, hi, intra, v))
print("  -> %s" % ("tous vivants" if not morts else "CANAUX MORTS : " + ", ".join(morts)))

# ---------------------------------------------------------------- 3. LE COUT
print("\n─── 3. LE COUT ──────────────────────────────────────────────────────")
def chrono(f, n=20):
    for _ in range(3): f()
    torch.cuda.synchronize(); t0 = time.time()
    for _ in range(n): f()
    torch.cuda.synchronize(); return (time.time() - t0) / n * 1000.0

t_vec = chrono(lambda: e._obs())
print("  obs vectorielle          %7.2f ms" % t_vec)
for kk in (8, 12, 16, 24):
    t = chrono(lambda: raster(e, K=kk, span=SPAN))
    print("  raster K=%-3d (%d canaux)   %7.2f ms   x%.1f" % (kk, len(CANAUX_DEFAUT), t, t / t_vec))
t_sans = chrono(lambda: raster(e, K=K, span=SPAN, canaux=tuple(c for c in CANAUX_DEFAUT if c != "danger")))
print("  raster K=16 SANS danger  %7.2f ms   -> le danger coute %.2f ms a lui seul"
      % (t_sans, chrono(lambda: raster(e, K=K, span=SPAN)) - t_sans))

pas_par_iter = B.PAS
print("\n  un entrainement = 140 iters x %d pas = %d appels" % (pas_par_iter, 140 * pas_par_iter))
t16 = chrono(lambda: raster(e, K=16, span=SPAN))
print("  surcout raster K=16 sur un entrainement complet : %.1f min (n=256)"
      % (140 * pas_par_iter * t16 / 1000.0 / 60.0))

# ---------------------------------------------------------------- 4. LE BROUILLEUR
print("\n─── 4. LE CONTROLE (brouilleur) ─────────────────────────────────────")
br = brouilleur(K, len(CANAUX_DEFAUT), DEV)
rb = br(r)
print("  histogrammes preserves ? somme %.4f vs %.4f | moyenne %.6f vs %.6f"
      % (r.sum(), rb.sum(), r.mean(), rb.mean()))
same = torch.allclose(r.reshape(e.N, e.A, len(CANAUX_DEFAUT), -1).sort(-1).values,
                      rb.reshape(e.N, e.A, len(CANAUX_DEFAUT), -1).sort(-1).values)
print("  memes valeurs, autres places ? %s" % ("OUI" if same else "NON — le controle est casse"))
print("  geometrie detruite ? correlation spatiale r/rb = %.4f (doit etre ~0)"
      % float(torch.corrcoef(torch.stack([r.reshape(-1), rb.reshape(-1)]))[0, 1]))
print()
