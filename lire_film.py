#!/usr/bin/env python3
"""LE FILM — 24 points par graine, evalues en argmax ET en echantillonnage sur SELECT.

Regles DEPOSEES AVANT ouverture (PREINSCRIPTION_ARGMAX_CENTRE.md, 8b687a7) :
  R1 intermittence : il existe k avec G1(k) >= 30 %, sur DEUX points consecutifs ou avec
     une marge superieure a l IC -> la condensation va et vient ; la recette devient la
     porte SUR POINTS, via SELECT.
  R2 bifurcation precoce : G1(k) < 10 % POUR TOUT k pendant que G0 tient >= 30 % de facon
     stable -> le sort se scelle tot ; selection sur graines.
  R3 zone grise : le film ne tranche pas seul. Et si G0 OSCILLE fortement, le 49,6 % de la
     graine passee etait lui-meme la chance de l iteration d arret.

⚠️ Garde-fou du vainqueur : un point choisi ici est un CANDIDAT. Le chiffre citable est sa
relecture sur TEST, une fois, apres le choix. Ce script ne touche PAS a GRAINES_TEST.
"""
import torch, glob, math, sys, json
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

SEL = B.GRAINES_SELECT[:3]
T = 30.0

def taux(pol, dev, argmax):
    def choisir(o, t):
        with torch.no_grad():
            lo, _ = pol(o.to(dev))
        a = lo.argmax(-1) if argmax else torch.distributions.Categorical(logits=lo).sample()
        return a.to(o.device), None, None
    v = [B.jouer(B.monde(256, g), choisir)[0]["prise"] for g in SEL]
    return sum(v) / len(v)

R = {}
for G in (0, 1):
    pts = sorted(glob.glob("/mnt/data/film_g%d/it*.pt" % G))
    R[G] = []
    print("\n  ══ GRAINE %d — %d points, graines SELECT ══\n" % (G, len(pts)))
    print("  %8s %12s %18s" % ("iter", "G argmax", "S echantillonne"))
    for p in pts:
        it = int(p.split("it")[-1].split(".")[0])
        pol = charger("cpu", p); dev = next(pol.parameters()).device
        g = taux(pol, dev, True); s = taux(pol, dev, False)
        R[G].append((it, g, s))
        ic = 1.96 * math.sqrt(max(g, 1e-9) / 100 * (1 - g / 100) / (256 * len(SEL))) * 100
        print("  %8d %10.1f %% %16.1f %%   (IC +-%.1f)" % (it, g, s, ic))
json.dump(R, open("/mnt/data/film_lecture.json", "w"))

g1 = [g for _, g, _ in R[1]]; g0 = [g for _, g, _ in R[0]]
haut1 = [(it, g) for it, g, _ in R[1] if g >= T]
consec = any(R[1][i][1] >= T and R[1][i+1][1] >= T for i in range(len(R[1]) - 1))
print("\n  ══ LES REGLES, APPLIQUEES ══\n")
print("  graine 1 : max %.1f %%   points au-dessus de %.0f %% : %d   deux consecutifs : %s"
      % (max(g1), T, len(haut1), "OUI" if consec else "non"))
print("  graine 0 : max %.1f %%   min apres decollage %.1f %%   ecart-type des 8 derniers %.1f"
      % (max(g0), min(g0[len(g0)//2:]), (sum((x - sum(g0[-8:])/8)**2 for x in g0[-8:])/8)**0.5))
print()
if consec or len(haut1) >= 2:
    print("  ➤ R1 — INTERMITTENCE. La condensation va et vient. La recette devient la porte")
    print("    SUR POINTS, choisis via SELECT et relus une fois sur TEST.")
elif max(g1) < 10 and min(g0[len(g0)//2:]) >= T:
    print("  ➤ R2 — BIFURCATION PRECOCE. Le sort se scelle tot : selection sur GRAINES.")
else:
    print("  ➤ R3 — ZONE GRISE. Le film ne tranche pas seul, on l ecrit tel quel.")
    if (sum((x - sum(g0[-8:])/8)**2 for x in g0[-8:])/8)**0.5 > 5:
        print("    ⚠️ ET G0 OSCILLE : le 49,6 % de la graine passee etait lui-meme la chance")
        print("       de l iteration d arret. La porte sur points vaut pour TOUT LE MONDE.")
