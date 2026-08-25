#!/usr/bin/env python3
"""Y A-T-IL SEULEMENT DU COUVERT DANS CE MONDE ?

`dcover` a une dispersion de 0,029 quand les colonnes de geometrie en ont 0,30 : dix fois
moins. Si le gymnase ne MONTRE presque pas de couvert, alors faire payer l exposition ne
servira a rien — il n y aura rien a lire, et le levier ne sera pas la recompense mais le
MONDE. On regarde avant de construire.

Trois questions, dans l ordre :
  A. quelle est la vraie distribution de dcover, et sur quelle plage ?
  B. le couvert PROTEGE-t-il ? (correlation entre etre couvert et ne pas etre touche)
  C. y a-t-il des positions qui protegent vraiment, ou tout se vaut-il ?
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger

e = B.monde(256, B.GRAINES_SELECT[0]); o = e.reset()
pol = charger("cpu", "/home/younes/arma3-marl/boucle_pol.pt"); dev = next(pol.parameters()).device

DC = []; LOS = []; DMG = []
adm = e.admg.clone()
for t in range(60):
    DC.append(o[:, :, 6].clone()); LOS.append(o[:, :, 7].clone())
    with torch.no_grad():
        lo, _ = pol(o.to(dev))
    a = torch.distributions.Categorical(logits=lo).sample().to(o.device)
    o, _, d, _ = e.step(a, auto_reset=False)
    DMG.append((e.admg - adm).clone()); adm = e.admg.clone()
    if bool(d.all()): break
dc = torch.cat([x.reshape(-1) for x in DC])
los = torch.cat([x.reshape(-1) for x in LOS])
dg = torch.cat([x.reshape(-1) for x in DMG])

print("\n  ══ A. LA DISTRIBUTION DE dcover ══")
q = [0, 10, 25, 50, 75, 90, 99, 100]
v = torch.quantile(dc, torch.tensor([x/100 for x in q], device=dc.device))
print("     centiles : %s" % "  ".join("%d%%=%.3f" % (a, b) for a, b in zip(q, v.tolist())))
print("     ecart-type %.4f   part exactement a zero : %.1f %%"
      % (float(dc.std()), 100.0*float((dc == 0).float().mean())))
print("     unite : dcover = distance au bati / 30 m, plafonnee a 1")
print("     -> en metres : mediane %.1f m, 99e centile %.1f m" % (float(v[3])*30, float(v[6])*30))

print("\n  ══ B. LE COUVERT PROTEGE-T-IL ? ══")
for lo_, hi in [(0.0, 0.02), (0.02, 0.05), (0.05, 0.10), (0.10, 1.01)]:
    m = (dc >= lo_) & (dc < hi)
    if int(m.sum()) < 100: continue
    print("     dcover %.2f-%.2f (%5.1f-%5.1f m) : n=%6d   los moyen %.3f   degats/pas %.5f"
          % (lo_, hi, lo_*30, hi*30, int(m.sum()), float(los[m].mean()), float(dg[m].mean())))

print("\n  ══ C. TOUT SE VAUT-IL ? ══")
bas = dc < torch.quantile(dc, torch.tensor(0.25, device=dc.device))
haut = dc > torch.quantile(dc, torch.tensor(0.75, device=dc.device))
print("     quart le PLUS PRES du bati  : los %.3f   degats/pas %.5f" % (float(los[bas].mean()), float(dg[bas].mean())))
print("     quart le PLUS LOIN du bati  : los %.3f   degats/pas %.5f" % (float(los[haut].mean()), float(dg[haut].mean())))
r = float(dg[haut].mean()) / max(float(dg[bas].mean()), 1e-9)
print("\n     rapport des degats loin/pres : %.2fx" % r)
print("     ⚠️ Si ce rapport est proche de 1, le bati ne protege pas : il n y a rien a lire,")
print("        et faire payer l exposition ne creerait aucune information nouvelle.")
