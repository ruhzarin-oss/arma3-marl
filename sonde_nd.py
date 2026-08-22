#!/usr/bin/env python3
"""La colonne `nd` a une dispersion de 37 826 la ou les autres valent 0,3.
⚠️ Premiere sonde FAUSSE : elle jouait une politique PASSIVE. Aucun defenseur ne mourait,
donc la sentinelle « plus aucun defenseur vivant » ne se declenchait jamais.
On rejoue avec la POLITIQUE, seule condition ou des defenseurs tombent.
"""
import torch, sys
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from porter_boucle import charger
pol = charger("cpu"); DEV = next(pol.parameters()).device
e = B.monde(256, B.GRAINES_TEST[0]); o = e.reset()
gros = 0; tot = 0; mx = 0.0; pas_gros = 0
for t in range(60):
    nd = o[:, :, 8]
    g = int((nd > 10).sum()); gros += g; tot += nd.numel(); mx = max(mx, float(nd.max()))
    if g: pas_gros += 1
    with torch.no_grad():
        a = pol(o.to(DEV))[0].argmax(-1).to(o.device)
    o, _, d, _ = e.step(a, auto_reset=False)
    if bool(d.all()): break
print("\n  nd : maximum vu = %.3e" % mx)
print("  valeurs aberrantes (> 10, soit > 2000 m sur 200 m de terrain) : %d sur %d (%.2f %%)"
      % (gros, tot, 100.0*gros/tot))
print("  pas ou l aberration est presente : %d sur %d" % (pas_gros, t+1))
print("  sentinelle attendue : sqrt(clamp(1e18, max=1e17)) / 200 = %.3e" % ((1e17)**0.5/200))
if mx > 1e3:
    print("\n  ⛔ CONFIRME : quand tous les defenseurs sont morts, `nd` vaut ~1,6 MILLION")
    print("     et part dans le reseau a cote de colonnes bornees a [-1, 1].")
