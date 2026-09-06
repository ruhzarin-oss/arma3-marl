#!/usr/bin/env python3
"""pourquoi_s1 — l eleve tient 76 m, son maitre 147. Ou perd-il ?

Hypothese a tester : EFFONDREMENT SUR LA CLASSE MAJORITAIRE. Le maitre emet TIRER 20,6 % du
temps et un cap 79,4 %. Un imitateur qui sur-emet la classe la plus frequente d une seule
classe se fige — et se figer coute, on vient de l etablir en dose-reponse.
"""
import sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from distillation import Eleve, cible_shamal
DEV = "cuda:0"
NOMS = ['cap0','cap1','cap2','cap3','cap4','cap5','cap6','cap7','TENIR','TIRER']

def histo(nom, f, graines=(101, 102, 103)):
    h = torch.zeros(10); n = 0
    for g in graines:
        e = B.monde(256, g); o = e.reset()
        fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
        for t in range(B.PAS):
            a = f(o, e); viv = e._aalive() & ~fini.unsqueeze(1)
            h += torch.bincount(a[viv].flatten().cpu(), minlength=10).float(); n += int(viv.sum())
            o, _, d, _ = e.step(a, auto_reset=False); fini |= d.bool()
            if bool(fini.all()): break
    return h / h.sum()

e0 = B.monde(8, 11); e0.reset(); nobs = e0._obs().shape[-1]
el = Eleve(nobs, avec_prix=False).to(DEV)
el.load_state_dict(torch.load("/mnt/data/eleve_S1_0.pt", map_location=DEV)); el.eval()
def f_el(o, e):
    with torch.no_grad(): lo, _ = el(o)
    return torch.distributions.Categorical(logits=lo).sample()

print("=" * 78); print(" OU S1 PERD-IL SON MAITRE ?"); print("=" * 78)
hm = histo("maitre", lambda o, e: cible_shamal(e))
he = histo("S1", f_el)
print("\n  %-8s %10s %10s %10s" % ("action", "MAITRE", "ELEVE S1", "ecart"))
for i, n in enumerate(NOMS):
    if hm[i] > 0.002 or he[i] > 0.002:
        print("  %-8s %9.2f %% %9.2f %% %+9.2f" % (n, 100 * hm[i], 100 * he[i], 100 * (he[i] - hm[i])))
print("\n  part des CAPS (0-7) : maitre %.1f %%  eleve %.1f %%" % (100 * hm[:8].sum(), 100 * he[:8].sum()))
print("  part de TIRER       : maitre %.1f %%  eleve %.1f %%" % (100 * hm[9], 100 * he[9]))
print("  part de TENIR       : maitre %.1f %%  eleve %.1f %%" % (100 * hm[8], 100 * he[8]))
d = float(he[9] - hm[9])
print("\n  -> %s" % ("EFFONDREMENT SUR TIRER : l eleve sur-emet la classe majoritaire de %+.1f pts,"
                     " donc il s immobilise — et se figer coute (dose-reponse)." % (100 * d)
                     if d > 0.10 else
                     "pas d effondrement sur TIRER ; la perte vient d ailleurs (la DIRECTION des caps)."))
# si ce n est pas TIRER, c est la direction : accord des caps avec le maitre
acc = tot = 0
for g in (101, 102, 103):
    e = B.monde(256, g); o = e.reset(); fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    for t in range(B.PAS):
        am = cible_shamal(e)
        with torch.no_grad(): lo, _ = el(o)
        ae = lo.argmax(-1)
        viv = e._aalive() & ~fini.unsqueeze(1) & (am < 8)
        acc += int(((ae == am) & viv).sum()); tot += int(viv.sum())
        o, _, dd, _ = e.step(f_el(o, e), auto_reset=False); fini |= dd.bool()
        if bool(fini.all()): break
print("  accord de CAP avec le maitre, quand le maitre avance : %.1f %%  (hasard = 12,5 %%)"
      % (100 * acc / max(tot, 1)))
