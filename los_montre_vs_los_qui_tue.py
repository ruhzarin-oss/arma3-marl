#!/usr/bin/env python3
"""LE `los` MONTRE EST-IL CELUI QUI TUE ?

Observation (_obs)   : _losc(hm, ATTAQUANT -> DEFENSEUR, eye_a = oeil attaquant, eye_b = 1,7)
Degats (boucle par di): _losc(hm, DEFENSEUR -> ATTAQUANT, eye_a = 1,7, eye_b = oeil attaquant)

Ce sont deux rayons de sens oppose, avec des hauteurs d oeil echangees. La ligne de vue
devrait etre symetrique — mais ce projet a deja mesure que la VERTICALITE ne l est pas
(overwatch-symmetric-los-limit). Si les deux nombres different, l agent voit une exposition
qui n est pas celle qui le tue, et le signe inverse s explique enfin.

On les calcule sur les MEMES etats et on les compare.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger
pol = charger("cpu", "/home/younes/arma3-marl/boucle_pol.pt"); dev = next(pol.parameters()).device
e = B.monde(256, B.GRAINES_SELECT[0]); o = e.reset()
S = e.scale
MO=[]; TU=[]; ND=[]
for t in range(40):
    # celui qu on MONTRE (contre le plus proche, tel quel)
    MO.append(o[:, :, 7].clone()); ND.append(o[:, :, 8].clone()*200.0)
    # celui qui TUE : defenseur -> attaquant, hauteurs d oeil echangees, max sur les vivants
    _lv = []
    for di in range(e.D):
        _bx = e.dpx[:, di:di+1].expand_as(e.apx); _by = e.dpy[:, di:di+1].expand_as(e.apy)
        _v = e._losc(e.hm, _bx, _by, e.apx, e.apy, S, eye_a=1.7, eye_b=e._eye())
        _lv.append(_v * e._dalive()[:, di:di+1].float())
    TU.append(torch.stack(_lv, -1).max(-1).values)
    with torch.no_grad():
        lo, _ = pol(o.to(dev))
    o, _, d, _ = e.step(torch.distributions.Categorical(logits=lo).sample().to(o.device), auto_reset=False)
    if bool(d.all()): break
f = lambda L: torch.cat([x.reshape(-1) for x in L])
mo, tu, nd = f(MO), f(TU), f(ND)
ok = nd < 1e4; mo, tu, nd = mo[ok], tu[ok], nd[ok]

print("\n  ══ LE MONTRE CONTRE CELUI QUI TUE ══\n")
print("  moyenne montree %.3f   moyenne qui tue %.3f" % (float(mo.mean()), float(tu.mean())))
print("  correlation : %.3f" % float(torch.corrcoef(torch.stack([mo, tu]))[0, 1]))
print("\n  %-14s %14s %16s %14s" % ("distance", "montre = 0", "mais qui tue > 0", "desaccord"))
for a_, b_ in [(0,40),(40,60),(60,80),(80,100),(100,130),(130,400)]:
    m = (nd >= a_) & (nd < b_)
    if int(m.sum()) < 200: continue
    cache = m & (mo < 0.25)
    trahi = cache & (tu > 0.75)
    print("  %-14s %13d %15d %13.1f %%"
          % ("%d - %d m" % (a_, b_), int(cache.sum()), int(trahi.sum()),
             100.0*int(trahi.sum())/max(int(cache.sum()), 1)))
print("\n  ⚠️ « desaccord » = l agent se croit cache et se fait pourtant voir en plein.")
