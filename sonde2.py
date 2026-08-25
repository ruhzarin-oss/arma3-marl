#!/usr/bin/env python3
"""sonde2 — la fenetre se DIMENSIONNE sur une trajectoire, elle ne se choisit pas.

La sonde 1 jugeait au reset : les defenseurs sont a 170 m, la fenetre en voit 60, donc
le canal ennemis etait vide. Un canal vide au reset n est pas forcement un canal mort —
il faut regarder QUAND l agent avance. On joue donc la doctrine frontale scriptee (celle
du depot, pas une invention) et on mesure a chaque pas.
"""
import sys, torch, math
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from raster import raster, brouilleur, CANAUX_DEFAUT

DEV = "cuda:0"
print("=" * 78); print(" SONDE 2 — dimensionner la fenetre sur une trajectoire"); print("=" * 78)

SPANS = [120.0, 180.0, 240.0, 300.0]
print("\n─── part des defenseurs VIVANTS visibles dans la fenetre, par pas ───")
print("  %-6s" % "pas", end="")
for sp in SPANS: print(" span=%-6.0f" % sp, end="")
print("   dist. moyenne a l objectif")

e = B.monde(256, 11); o = e.reset()
lignes = []
for t in range(B.PAS):
    d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean()
    if t % 6 == 0:
        row = []
        for sp in SPANS:
            dx = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
            th0 = torch.atan2(-e.apx, -e.apy).unsqueeze(2)
            f = dx * torch.sin(th0) + dy * torch.cos(th0); l = dx * torch.cos(th0) - dy * torch.sin(th0)
            dedans = ((f.abs() <= sp / 2) & (l.abs() <= sp / 2) & e._dalive().unsqueeze(1)).float().sum(2)
            viv = e._dalive().float().sum(1, keepdim=True).clamp(min=1)
            row.append(float((dedans / viv).mean()))
        print("  %-6d" % t, end="")
        for v in row: print("   %8.3f" % v, end="")
        print("        %6.1f m" % d)
    a = B.frontal(e, t)
    o, _, done, info = e.step(a, auto_reset=False)
    if bool(done.all()): break

# ---------------------------------------------------------------------------
print("\n─── canaux vivants A MI-PARCOURS (pas 18), span=240, K=20 ───")
e = B.monde(256, 11); e.reset()
for t in range(18):
    e.step(B.frontal(e, t), auto_reset=False)
K, SPAN = 20, 240.0
r = raster(e, K=K, span=SPAN)
print("  %-10s %8s %8s %10s  %s" % ("canal", "moy", "max", "intra-img", "verdict"))
for i, nom in enumerate(CANAUX_DEFAUT):
    c = r[:, :, i]
    intra = float(c.reshape(-1, K * K).std(dim=1).mean())
    nonnul = float((c.reshape(-1, K * K).abs().sum(1) > 0).float().mean())
    print("  %-10s %8.4f %8.4f %10.5f  %s (non nul dans %.0f %% des images)"
          % (nom, float(c.mean()), float(c.max()), intra,
             "vivant" if intra > 1e-4 else "MORT", 100 * nonnul))

# ---------------------------------------------------------------------------
print("\n─── le brouilleur, CANAL PAR CANAL (mon instrument etait faux) ───")
br = brouilleur(K, len(CANAUX_DEFAUT), DEV)
rb = br(r)
print("  %-10s %12s  %s" % ("canal", "corr r/rb", "lecture"))
for i, nom in enumerate(CANAUX_DEFAUT):
    a = r[:, :, i].reshape(-1); b = rb[:, :, i].reshape(-1)
    if float(a.std()) < 1e-8 or float(b.std()) < 1e-8:
        print("  %-10s %12s  canal degenere, la correlation ne veut rien dire" % (nom, "n/a")); continue
    cc = float(torch.corrcoef(torch.stack([a, b]))[0, 1])
    part_nulle = float((a == 0).float().mean())
    print("  %-10s %12.4f  %.0f %% de cellules nulles -> le residu vient de la, pas de la geometrie"
          % (nom, cc, 100 * part_nulle))
# la vraie question : le brouillage detruit-il le VOISINAGE ?
def autocorr(x):
    """correlation entre une cellule et sa voisine de droite — la geometrie locale."""
    a = x[..., :, :-1].reshape(-1); b = x[..., :, 1:].reshape(-1)
    if float(a.std()) < 1e-8: return float("nan")
    return float(torch.corrcoef(torch.stack([a, b]))[0, 1])
print("\n  LA BONNE MESURE — correlation avec la cellule VOISINE (= la geometrie locale) :")
print("  %-10s %10s %10s" % ("canal", "droit", "brouille"))
for i, nom in enumerate(CANAUX_DEFAUT):
    print("  %-10s %10.4f %10.4f" % (nom, autocorr(r[:, :, i]), autocorr(rb[:, :, i])))
print()
