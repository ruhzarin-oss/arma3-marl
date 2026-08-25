#!/usr/bin/env python3
"""sonde_prix — LE CONTROLE POSITIF DOIT LUI-MEME ETRE CONTROLE.

Trois questions, avant tout entrainement :
  1. la direction i de `_champ_danger` est-elle bien le cap i de `boucle.cap` ?
  2. le prix DISCRIMINE-t-il entre les 8 caps, ou est-il plat ? (plat = controle mort)
  3. une doctrine qui SUIT ce prix encaisse-t-elle moins de degats qu'une qui l ignore ?
     -> si non, l information est inactionnable et le controle positif ne peut pas reussir.
"""
import sys, math, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import prix_des_actions

print("=" * 78); print(" SONDE PRIX — le controle positif"); print("=" * 78)
e = B.monde(512, 11); e.reset()
for t in range(6): e.step(B.frontal(e, t), auto_reset=False)
p = prix_des_actions(e)
print("\n  prix %s  (N, A, 8 caps)   champ_R = %.1f m = move" % (tuple(p.shape), e.champ_R))

# ── 1. ALIGNEMENT : le cap i doit mener a la cellule dont on annonce le prix
print("\n─── 1. ALIGNEMENT cap <-> direction ───")
S = e.scale
for i in (0, 2, 4, 6):
    th = i * (2 * math.pi / 8)
    cx = e.apx + math.sin(th) * e.move; cy = e.apy + math.cos(th) * e.move
    # le cap que `boucle.cap` attribuerait a ce deplacement
    c = B.cap(cx - e.apx, cy - e.apy)
    print("  direction %d -> deplacement (%+.1f, %+.1f) -> cap calcule %d   %s"
          % (i, math.sin(th) * e.move, math.cos(th) * e.move, int(c[0, 0]),
             "OK" if int(c[0, 0]) == i else "ECHEC"))

# ── 2. DISCRIMINATION : un prix plat est un controle mort
print("\n─── 2. LE PRIX DISCRIMINE-T-IL ? ───")
inter = p.std(dim=2)                     # ecart-type ENTRE les 8 caps, par homme
moy = p.mean(dim=2)
viv = e._aalive()
print("  moyenne du prix        %.5f" % float(moy[viv].mean()))
print("  ecart-type ENTRE caps  %.5f" % float(inter[viv].mean()))
print("  rapport ecart/moyenne  %.2f   %s"
      % (float(inter[viv].mean() / moy[viv].mean().clamp(min=1e-9)),
         "OK, il discrimine" if float(inter[viv].mean()) > 0.2 * float(moy[viv].mean()) else "PLAT = controle mort"))
mx, mn = p.max(2).values, p.min(2).values
print("  ecart pire cap - meilleur cap : moyenne %.5f  (soit %.0f %% du prix moyen)"
      % (float((mx - mn)[viv].mean()), 100 * float((mx - mn)[viv].mean() / moy[viv].mean().clamp(min=1e-9))))
print("  hommes dont les 8 caps sont IDENTIQUES : %.1f %%"
      % (100 * float(((mx - mn)[viv] < 1e-9).float().mean())))

# ── 3. EST-CE ACTIONNABLE ? une doctrine qui suit le prix contre une qui l ignore
print("\n─── 3. SUIVRE LE PRIX PAIE-T-IL ? (doctrines scriptees, 6 graines de jugement) ───")
def joue(nom, choix):
    pr, tn, dg = [], [], []
    for g in B.GRAINES_TEST:
        ee = B.monde(256, g)
        st, *_ = B.jouer(ee, lambda o, t, _e=ee: (choix(_e, t), None, None))
        pr.append(st["prise"]); tn.append(st["metres_tenus"]); dg.append(float(ee.admg.mean()))
    print("  %-26s prise %5.1f %%   tenus %6.1f m   degats %.3f"
          % (nom, sum(pr)/len(pr), sum(tn)/len(tn), sum(dg)/len(dg)))
    return sum(pr)/len(pr)

def vers_but(ee, t): return B.cap(-ee.apx, -ee.apy)
def moins_cher_vers_but(ee, t):
    """avance, mais parmi les 3 caps qui vont GLOBALEMENT vers l objectif, prend le moins cher."""
    pp = prix_des_actions(ee)
    c0 = B.cap(-ee.apx, -ee.apy)
    cand = torch.stack([(c0 - 1) % 8, c0, (c0 + 1) % 8], dim=2)      # (N,A,3)
    pc = torch.gather(pp, 2, cand)
    return torch.gather(cand, 2, pc.argmin(2, keepdim=True)).squeeze(2)

a = joue("frontal (ignore le prix)", vers_but)
b = joue("frontal + moins cher", moins_cher_vers_but)
print("\n  ECART : %+.1f points   %s" % (b - a,
      "le prix est ACTIONNABLE" if b - a > 2.0 else "⚠️ le prix ne paie pas, meme en le suivant"))
print()
