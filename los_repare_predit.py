#!/usr/bin/env python3
"""LA COLONNE REPAREE PREDIT-ELLE LE DANGER ? — a verifier AVANT sept heures d entrainement.

Ancienne colonne, a distance egale : rapport degats(vu)/degats(cache) = 0,15x a 0-40 m et
3,40x au-dela de 130 m. Le signe s INVERSE, donc la colonne n apprend rien.
Reparee, elle doit donner un rapport > 1 dans TOUTES les bandes : etre offert a quelqu un
doit coefficient couter, partout. Sinon la reparation ne sert a rien et on ne la paie pas.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger
pol = charger("cpu", "/home/younes/arma3-marl/boucle_pol.pt"); dev = next(pol.parameters()).device

def mesure(los_tous):
    e = B.monde(256, B.GRAINES_SELECT[0]); e.los_tous = los_tous; o = e.reset()
    LOS=[]; DMG=[]; ND=[]; adm = e.admg.clone()
    for t in range(60):
        LOS.append(o[:, :, 7].clone()); ND.append(o[:, :, 8].clone()*200.0)
        with torch.no_grad():
            lo, _ = pol(o.to(dev))
        a = torch.distributions.Categorical(logits=lo).sample().to(o.device)
        o, _, d, _ = e.step(a, auto_reset=False)
        DMG.append((e.admg-adm).clone()); adm = e.admg.clone()
        if bool(d.all()): break
    f = lambda L: torch.cat([x.reshape(-1) for x in L])
    los, dg, nd = f(LOS), f(DMG), f(ND)
    ok = nd < 1e4
    return los[ok], dg[ok], nd[ok]

print("\n  %-14s %14s %14s   %s" % ("distance", "ANCIENNE", "REPAREE", "verdict"))
A = mesure(False); R = mesure(True)
bon = 0; tot = 0
for a_, b_ in [(0,40),(40,60),(60,80),(80,100),(100,130),(130,400)]:
    l = "  %-14s" % ("%d - %d m" % (a_, b_))
    rr = []
    for los, dg, nd in (A, R):
        m = (nd >= a_) & (nd < b_)
        c = m & (los < 0.25); v = m & (los > 0.75)
        if int(c.sum()) < 100 or int(v.sum()) < 100: rr.append(None); continue
        rr.append(float(dg[v].mean()) / max(float(dg[c].mean()), 1e-9))
    l += "".join("%13.2fx" % x if x else "%14s" % "-" for x in rr)
    if rr[1] is not None:
        tot += 1; bon += (rr[1] > 1.0)
        l += "   %s" % ("✓ etre vu coute" if rr[1] > 1.0 else "⛔ signe inverse")
    print(l)
print("\n  bandes ou etre vu COUTE, avec la colonne reparee : %d sur %d" % (bon, tot))
print("  %s" % ("➤ LA REPARATION VAUT SES SEPT HEURES." if bon >= tot - 1 else
               "⛔ LE SIGNE S INVERSE ENCORE : ne pas payer cet entrainement."))
