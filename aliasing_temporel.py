#!/usr/bin/env python3
"""ET SI LE DEFAUT ETAIT LE TEMPS, PAS LA GEOMETRIE ?

Je lis `los` AVANT le pas et les degats APRES. Un pas vaut 14 m. A 30 m d un defenseur, ce
pas change la geometrie du tout au tout : un homme cache au depart peut etre a decouvert
pendant l essentiel du pas. La correlation serait alors detruite PRECISEMENT a courte
portee — ce qui est le motif observe.

Test : les memes degats, mis en face du `los` du pas SUIVANT (donc apres deplacement).
Si le signe devient coherent, ce n est pas l observation qui est mauvaise, c est le PAS
qui est trop gros pour la geometrie de pres.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger
pol = charger("cpu", "/home/younes/arma3-marl/boucle_pol.pt"); dev = next(pol.parameters()).device
e = B.monde(256, B.GRAINES_SELECT[0]); e.los_tous = True; o = e.reset()
LOS=[]; DMG=[]; ND=[]; adm = e.admg.clone()
for t in range(40):
    LOS.append(o[:, :, 7].clone()); ND.append(o[:, :, 8].clone()*200.0)
    with torch.no_grad():
        lo, _ = pol(o.to(dev))
    o, _, d, _ = e.step(torch.distributions.Categorical(logits=lo).sample().to(o.device), auto_reset=False)
    DMG.append((e.admg-adm).clone()); adm = e.admg.clone()
    if bool(d.all()): break
n = len(DMG) - 1
f = lambda L, a, b: torch.cat([x.reshape(-1) for x in L[a:b]])
print("\n  %-14s %18s %18s" % ("distance", "los AVANT le pas", "los APRES le pas"))
for a_, b_ in [(0,40),(40,60),(60,80),(80,100),(100,130),(130,400)]:
    l = "  %-14s" % ("%d - %d m" % (a_, b_))
    for dec in (0, 1):
        los = f(LOS, dec, n+dec); dg = f(DMG, 0, n); nd = f(ND, 0, n)
        ok = nd < 1e4; los, dg, nd = los[ok], dg[ok], nd[ok]
        m = (nd >= a_) & (nd < b_)
        c = m & (los < 0.25); v = m & (los > 0.75)
        if int(c.sum()) < 100 or int(v.sum()) < 100: l += "%18s" % "-"; continue
        r = float(dg[v].mean()) / max(float(dg[c].mean()), 1e-9)
        l += "%16.2fx%s" % (r, " ✓" if r > 1 else " ⛔")
    print(l)
print("\n  ⚠️ Si la colonne APRES est coherente et la colonne AVANT non, le defaut n est pas")
print("     l observation : c est le PAS, trop gros pour la geometrie de courte portee.")
