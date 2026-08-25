#!/usr/bin/env python3
"""sonde_entites — AVANT TOUT ENTRAINEMENT. Le repere, le masque, le controle, le cout."""
import sys, time, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from entites import entites, brouilleur_entites, NF_TOK
from raster import raster, K_DEFAUT, SPAN_DEFAUT
from entites import CANAUX_TERRAIN

print("=" * 78); print(" SONDE ENTITES"); print("=" * 78)
e = B.monde(256, 11); e.reset()
for t in range(7): e.step(B.frontal(e, t), auto_reset=False)
j, m = entites(e)
print("\n  jetons %s   masque %s   U = D(%d) + A(%d) = %d"
      % (tuple(j.shape), tuple(m.shape), e.D, e.A, j.shape[2]))

# ── 1. LE REPERE : la coordonnee AVANT doit croitre vers l objectif
print("\n─── 1. LE REPERE ───")
f, l, dist = j[..., 0], j[..., 1], j[..., 2]
dd = torch.sqrt((e.dpx.unsqueeze(1) - e.apx.unsqueeze(2)) ** 2
                + (e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)) ** 2) / e.scale
err = (dist[:, :, :e.D] - dd).abs().max()
print("  distance du jeton contre la distance vraie : ecart max %.2e   %s"
      % (err, "OK" if err < 1e-4 else "ECHEC"))
print("  identite (f,l) : ecart max a la distance %.2e   %s"
      % ((torch.sqrt(f ** 2 + l ** 2) - dist).abs().max(),
         "OK" if float((torch.sqrt(f**2+l**2)-dist).abs().max()) < 1e-4 else "ECHEC"))
# les defenseurs sont pres de l objectif, donc leur AVANT doit etre POSITIF en moyenne
fd = f[:, :, :e.D][m[:, :, :e.D]]
print("  AVANT moyen des defenseurs %+.3f (doit etre > 0, ils sont vers l objectif)   %s"
      % (fd.mean(), "OK" if float(fd.mean()) > 0 else "ECHEC"))

# ── 2. LE MASQUE
print("\n─── 2. LE MASQUE ───")
soi = m[:, :, e.D:].diagonal(dim1=1, dim2=2)
print("  l homme se voit-il lui-meme ? %s   %s"
      % (bool(soi.any()), "OK (jamais)" if not bool(soi.any()) else "ECHEC"))
mort_d = (~e._dalive()).unsqueeze(1).expand(e.N, e.A, e.D)
print("  un defenseur MORT est-il jamais demasque ? %s   %s"
      % (bool((m[:, :, :e.D] & mort_d).any()),
         "OK (jamais)" if not bool((m[:, :, :e.D] & mort_d).any()) else "ECHEC"))
print("  jetons reels par homme : moyenne %.2f sur %d" % (m.float().sum(2).mean(), j.shape[2]))
print("  hommes SANS aucun jeton (attention vide) : %.2f %%"
      % (100 * float((m.sum(2) == 0).float().mean())))

# ── 3. LE CONTROLE
print("\n─── 3. LE CONTROLE (positions permutees ENTRE unites) ───")
bre = brouilleur_entites()
jb, mb = bre(j, m)
tri = lambda x: x.reshape(-1, x.shape[2], 3).sum(2).sort(1).values
print("  memes positions dans le lot ? %s"
      % ("OUI" if torch.allclose(tri(j[..., :3]), tri(jb[..., :3]), atol=1e-5) else "NON"))
print("  identite (camp, vivant, vu) intacte ? %s"
      % ("OUI" if torch.allclose(j[..., 3:], jb[..., 3:]) else "NON"))
acc = (j[..., :3] - jb[..., :3]).abs().sum(-1)
print("  appariement position<->unite detruit ? %.1f %% des jetons ont bouge"
      % (100 * float((acc > 1e-6).float().mean())))
# la vraie mesure : la correlation entre le camp et l AVANT s effondre-t-elle ?
def corr_camp_avant(jj, mm):
    a = jj[..., 0][mm]; b = jj[..., 3][mm]
    return float(torch.corrcoef(torch.stack([a, b]))[0, 1])
print("  correlation camp<->AVANT : droit %+.3f | brouille %+.3f  (doit s effondrer)"
      % (corr_camp_avant(j, m), corr_camp_avant(jb, mb)))

# ── 4. LE COUT
print("\n─── 4. LE COUT (GPU partage avec 3 runs en cours) ───")
def chrono(fn, n=10):
    for _ in range(3): fn()
    torch.cuda.synchronize(); t0 = time.time()
    for _ in range(n): fn()
    torch.cuda.synchronize(); return (time.time() - t0) / n * 1000
t_ent = chrono(lambda: entites(e))
t_r6 = chrono(lambda: raster(e, K=K_DEFAUT, span=SPAN_DEFAUT))
t_r4 = chrono(lambda: raster(e, K=K_DEFAUT, span=SPAN_DEFAUT, canaux=CANAUX_TERRAIN))
print("  raster 6 canaux (bras B)      %7.2f ms" % t_r6)
print("  raster 4 canaux + entites (E) %7.2f ms   (%.2f + %.2f)" % (t_r4 + t_ent, t_r4, t_ent))
print("  -> E coute %+.1f %% par rapport a B" % (100 * ((t_r4 + t_ent) / t_r6 - 1)))
print()
