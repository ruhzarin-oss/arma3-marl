#!/usr/bin/env python3
"""marge_du_choix — LA PORTE AVANT DE PIVOTER VERS L OFFICIER ⟨Fable, 26/08⟩.

« L objet apprenable n a jamais ete l EXECUTANT, c est le SELECTEUR. MAIS mesure d abord la
MARGE DU CHOIX : sur tes scenarios de jugement, l identite de la meilleure doctrine
varie-t-elle ? L ecart oracle-selecteur moins meilleure-doctrine-FIXE est le plafond de
l officier. Si le 91,0 domine partout, la marge du choix est nulle et la question de
l officier ne peut pas plus se poser ici que celle de la perception. »

On ne construit PAS d officier. On mesure son PLAFOND, par la doctrine parfaite : celle qui,
pour chaque scenario, choisirait la meilleure. Si ce plafond ne depasse pas la meilleure
doctrine fixe, il n y a rien a apprendre a choisir.
"""
import sys, torch, itertools, json
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import jouer_phi2
from shamal_teacher import shamal_action

def brider(a):
    return torch.where(a >= 10, torch.full_like(a, 9), a)

DOCTRINES = {
    "coureur_91": lambda e, t: brider(shamal_action(e, drop_to=1, retreat=True, mode="assault", bounding=False, flank=True)),
    "coureur_sans_flanc": lambda e, t: brider(shamal_action(e, drop_to=1, retreat=True, mode="assault", bounding=False, flank=False)),
    "shamal_complet": lambda e, t: brider(shamal_action(e, drop_to=1, retreat=True, mode="assault", bounding=True, flank=True)),
    "bond_sans_flanc": lambda e, t: brider(shamal_action(e, drop_to=1, retreat=True, mode="assault", bounding=True, flank=False)),
    "flanc_depot": lambda e, t: B.flanc(e, t),
    "frontal_depot": lambda e, t: B.frontal(e, t),
    "traque": lambda e, t: brider(shamal_action(e, drop_to=1, retreat=True, mode="hunt", bounding=False, flank=True)),
}

# des SCENARIOS, pas seulement des graines : si l officier a une marge, elle vient de ce que
# le monde CHANGE de regime. On fait varier ce que le depot sait faire varier sans rien inventer.
SCENARIOS = {}
for D in (2, 4, 6):
    for R in (120.0, 170.0):
        SCENARIOS["D%d_R%.0f" % (D, R)] = dict(D=D, R_spawn=R)

def monde(n, g, **kw):
    from assault_terrain import AssaultTerrain
    from monde_fidele import MONDE_ARMA
    cfg = dict(MONDE_ARMA); cfg.update(kw)
    return AssaultTerrain(num_envs=n, seed=g, device="cuda:0", max_steps=B.PAS, **cfg)

print("=" * 104)
print(" LA MARGE DU CHOIX — un officier aurait-il quelque chose a decider ici ?")
print("=" * 104, flush=True)
GJ = B.GRAINES_TEST[:4]
res = {}
noms = list(DOCTRINES)
print("\n  %-12s" % "scenario", end="")
for d in noms: print(" %10s" % d[:10], end="")
print("   MEILLEURE")
for sc, kw in SCENARIOS.items():
    ligne = {}
    for d, f in DOCTRINES.items():
        pr = []
        for g in GJ:
            e = monde(192, g, **kw)
            st, *_ = jouer_phi2(e, lambda o, t, _e=e, _f=f: (_f(_e, t), None, None), w_phi=0.0)
            pr.append(st["prise"])
        ligne[d] = sum(pr) / len(pr)
    res[sc] = ligne
    best = max(ligne, key=ligne.get)
    print("  %-12s" % sc, end="")
    for d in noms: print(" %9.1f%s" % (ligne[d], "*" if d == best else " "), end="")
    print("   %s" % best, flush=True)

print("\n─── LE PLAFOND DE L OFFICIER ───")
oracle = sum(max(v.values()) for v in res.values()) / len(res)
fixes = {d: sum(v[d] for v in res.values()) / len(res) for d in noms}
meilleure_fixe = max(fixes, key=fixes.get)
print("  ORACLE DU CHOIX (la meilleure doctrine par scenario) ... %5.1f %%" % oracle)
print("  MEILLEURE DOCTRINE FIXE (`%s`) ................ %5.1f %%" % (meilleure_fixe, fixes[meilleure_fixe]))
marge = oracle - fixes[meilleure_fixe]
print("  ⭐ MARGE DU CHOIX ...................................... %+5.1f points" % marge)
gagnantes = set(max(v, key=v.get) for v in res.values())
print("\n  doctrines gagnantes distinctes : %d sur %d scenarios  (%s)" % (len(gagnantes), len(res), ", ".join(gagnantes)))
print("\n  -> %s" % ("IL Y A UNE MARGE : l identite de la meilleure doctrine VARIE, un officier a de quoi decider."
                     if marge >= 5.0 else
                     "MARGE NULLE : une doctrine FIXE fait aussi bien que le choix parfait."
                     " La question de l officier NE PEUT PAS SE POSER ICI — meme saturation que la perception."))
json.dump({"res": res, "oracle": oracle, "fixes": fixes, "marge": marge}, open("/mnt/data/marge_choix.json", "w"), indent=1)
