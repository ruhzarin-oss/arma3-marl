#!/usr/bin/env python3
"""`los` PROTEGE-T-IL DEJA ? — la question qui change le diagnostic.

`self.cover` (qui protege, via 1 - 0,7*incover) et `self.dcover` (qui est MONTRE) sont deux
champs differents. Et si `couvert_directionnel` est vrai, le terme de couvert est IGNORE :
toute la protection passe par `los`. Or `los` EST dans l observation (colonne 7) — et
l agent l ignore (le brouiller coute 0,9 point).

Si les degats sont proportionnels a `los`, alors s exposer COUTE DEJA, et le diagnostic
« il faut faire payer l exposition » est FAUX : il faudrait comprendre pourquoi il n apprend
pas a se servir d une variable qui paie deja.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

e = B.monde(256, B.GRAINES_SELECT[0]); o = e.reset()
print("\n  couvert_directionnel : %s" % getattr(e, "couvert_directionnel", "absent"))
print("  -> %s" % ("le terme de couvert est IGNORE, tout passe par los"
                   if getattr(e, "couvert_directionnel", False) else "le couvert agit AUSSI"))
pol = charger("cpu", "/home/younes/arma3-marl/boucle_pol.pt"); dev = next(pol.parameters()).device

LOS = []; DMG = []; adm = e.admg.clone()
for t in range(60):
    LOS.append(o[:, :, 7].clone())
    with torch.no_grad():
        lo, _ = pol(o.to(dev))
    a = torch.distributions.Categorical(logits=lo).sample().to(o.device)
    o, _, d, _ = e.step(a, auto_reset=False)
    DMG.append((e.admg - adm).clone()); adm = e.admg.clone()
    if bool(d.all()): break
los = torch.cat([x.reshape(-1) for x in LOS]); dg = torch.cat([x.reshape(-1) for x in DMG])

print("\n  ══ DEGATS PAR PAS, SELON CE QU ON OFFRE AU TIREUR ══\n")
print("  %-22s %10s %16s" % ("fraction du corps vue", "n", "degats/pas"))
bornes = [(0.0, 0.01), (0.01, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 0.99), (0.99, 1.01)]
ref = None
for a_, b_ in bornes:
    m = (los >= a_) & (los < b_)
    if int(m.sum()) < 200: continue
    v = float(dg[m].mean())
    if ref is None and v > 0: ref = v
    print("  %-22s %10d %14.5f   %s" % ("%.2f - %.2f" % (a_, b_), int(m.sum()), v,
          ("x%.1f" % (v/ref)) if ref else ""))
cache = los < 0.25; vu = los > 0.75
print("\n  cache (los < 0,25) : %.5f de degats/pas" % float(dg[cache].mean()))
print("  vu    (los > 0,75) : %.5f de degats/pas" % float(dg[vu].mean()))
r = float(dg[vu].mean()) / max(float(dg[cache].mean()), 1e-9)
print("\n  ➤ ETRE VU COUTE %.1f FOIS PLUS QUE SE CACHER." % r)
if r > 3:
    print("     Donc s exposer COUTE DEJA, et beaucoup. Le diagnostic « il faut faire payer")
    print("     l exposition » est FAUX : la variable paie deja, et l agent ne l apprend pas.")
else:
    print("     L exposition coute peu : la faire payer est un levier reel.")
