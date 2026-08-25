#!/usr/bin/env python3
"""ETRE VU COUTE-T-IL, A DISTANCE EGALE ?

En agregat, les caches prennent PLUS que les vus (0,01675 contre 0,01123). C est inverse, et
c est le motif d un confondant : un homme cache est probablement PLUS PRES — le couvert est
au bord de l objectif, la ou les defenseurs sont denses. Et le code porte un terme de FEU DE
ZONE proportionnel a `inr` (a portee) qui ignore `los`.

On refait la mesure A DISTANCE EGALE. Si l ecart s inverse dans chaque bande, l agregat
mentait. S il reste, alors etre vu ne coute VRAIMENT rien, et ignorer `los` est RATIONNEL.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

e = B.monde(256, B.GRAINES_SELECT[0]); o = e.reset()
print("\n  feu_de_zone : %s" % getattr(e, "feu_de_zone", "absent"))
pol = charger("cpu", "/home/younes/arma3-marl/boucle_pol.pt"); dev = next(pol.parameters()).device
LOS=[]; DMG=[]; ND=[]; adm = e.admg.clone()
for t in range(60):
    LOS.append(o[:, :, 7].clone()); ND.append(o[:, :, 8].clone() * 200.0)
    with torch.no_grad():
        lo, _ = pol(o.to(dev))
    a = torch.distributions.Categorical(logits=lo).sample().to(o.device)
    o, _, d, _ = e.step(a, auto_reset=False)
    DMG.append((e.admg - adm).clone()); adm = e.admg.clone()
    if bool(d.all()): break
f = lambda L: torch.cat([x.reshape(-1) for x in L])
los, dg, nd = f(LOS), f(DMG), f(ND)
ok = nd < 1e4                      # on jette la sentinelle "plus aucun defenseur"
los, dg, nd = los[ok], dg[ok], nd[ok]

print("\n  ══ DEGATS PAR PAS, A DISTANCE EGALE DU DEFENSEUR LE PLUS PROCHE ══\n")
print("  %-18s %10s %14s %10s %14s %10s" % ("distance", "n cache", "degats", "n vu", "degats", "rapport"))
for a_, b_ in [(0,40),(40,60),(60,80),(80,100),(100,130),(130,400)]:
    m = (nd >= a_) & (nd < b_)
    c = m & (los < 0.25); v = m & (los > 0.75)
    if int(c.sum()) < 100 or int(v.sum()) < 100: continue
    dc_, dv = float(dg[c].mean()), float(dg[v].mean())
    print("  %-18s %10d %13.5f %10d %13.5f %9.2fx"
          % ("%d - %d m" % (a_, b_), int(c.sum()), dc_, int(v.sum()), dv, dv / max(dc_, 1e-9)))
print("\n  ⚠️ rapport = degats en etant VU / degats en etant CACHE, a distance egale.")
print("     > 1 : etre vu coute. ~1 : etre vu ne coute rien, et ignorer `los` est RATIONNEL.")
