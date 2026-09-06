#!/usr/bin/env python3
"""verif_86 — UN CHIFFRE TROP BEAU SE VERIFIE AVANT DE SERVIR.

`shamal_action` SANS bounding rend 86,5 % la ou la reference du depot fait 49,6 % et ou deux
objets independants suggeraient un plafond vers 61-62 %. Avant d en faire un resultat, quatre
questions — chacune peut le tuer.

  Q1. Tient-il GRAINE PAR GRAINE, ou est-ce une moyenne portee par une graine ?
  Q2. Gagne-t-il VRAIMENT, ou par un mode degenere ? (survivants, metres tenus, danger)
  Q3. La grille complete bounding x flank : ou est le vrai optimum ?
  Q4. Le monde est-il bien MONDE_ARMA, ou ai-je change de monde sans le voir ?
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import jouer_phi2
from shamal_teacher import shamal_action

def jouer(kw, graines, n=256):
    pr, tn, dh, sv = [], [], [], []
    for g in graines:
        e = B.monde(n, g)
        st, *_ = jouer_phi2(e, lambda o, t, _e=e: (shamal_action(_e, **kw), None, None), w_phi=0.0)
        pr.append(st["prise"]); tn.append(st["metres_tenus"])
        dh.append(st["danger_homme_pas"]); sv.append(st["survivants"])
    m = lambda v: sum(v) / len(v)
    return m(pr), pr, m(tn), m(dh), m(sv)

print("=" * 96); print(" VERIFICATION DU 86,5 %"); print("=" * 96)
e = B.monde(8, 11); e.reset()
print("\n─── Q4 · LE MONDE ───")
print("  A=%d  D=%d  R_spawn=%.0f  fire_range=%.0f  secure_r=%.0f  max_steps=%d  courbe=%s"
      % (e.A, e.D, e.R_spawn, e.fire_range, e.secure_r, e.max_steps, e.courbe is not None))
print("  n_actions=%d  postures=%s   (le repertoire de shamal utilise 9,10,11,12)" % (e.n_actions, e.postures))
print("  -> %s" % ("MONDE_ARMA, celui de tous les autres chiffres du dossier" if e.D == 4 and e.fire_range == 110.0
                   else "⚠️ CE N EST PAS LE MEME MONDE — les chiffres ne se comparent pas"))

print("\n─── Q3 · LA GRILLE COMPLETE ───")
print("  %-22s %8s %10s %10s %12s %10s" % ("configuration", "prise", "etendue", "tenus", "danger/h-pas", "survivants"))
base = dict(drop_to=1, retreat=True, mode="assault")
best = None
for bnd in (True, False):
    for flk in (True, False):
        kw = dict(base, bounding=bnd, flank=flk)
        p, par, t, d, s = jouer(kw, B.GRAINES_TEST)
        nom = "bounding=%s flank=%s" % (str(bnd)[0], str(flk)[0])
        print("  %-22s %7.1f %% [%4.1f;%4.1f] %9.1f m %11.4f %9.2f" % (nom, p, min(par), max(par), t, d, s))
        if best is None or p > best[0]: best = (p, kw, par, t, d, s)

print("\n─── Q1 · GRAINE PAR GRAINE, la meilleure configuration ───")
p, kw, par, t, d, s = best
print("  %s" % kw)
for g, v in zip(B.GRAINES_TEST, par):
    print("     graine %d : %5.1f %%" % (g, v))
print("  moyenne %.1f %%  etendue [%.1f ; %.1f]  -> %s"
      % (p, min(par), max(par), "STABLE, ce n est pas une graine chanceuse" if max(par) - min(par) < 15
         else "⚠️ DISPERSE, la moyenne cache une loterie"))

print("\n─── Q2 · GAGNE-T-IL VRAIMENT ? ───")
pa, para, ta, da, sa = jouer(dict(base, bounding=True, flank=True), B.GRAINES_TEST)
print("  %-22s prise %5.1f %%  tenus %6.1f m  danger %.4f  survivants %.2f" % ("SHAMAL complet", pa, ta, da, sa))
print("  %-22s prise %5.1f %%  tenus %6.1f m  danger %.4f  survivants %.2f" % ("la meilleure", p, t, d, s))
print("  -> %s" % ("il gagne EN COMBATTANT : plus de prises ET plus de survivants" if s >= sa
                   else "⚠️ il gagne avec MOINS de survivants — verifier que ce n est pas un mode degenere"))
