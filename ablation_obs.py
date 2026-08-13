#!/usr/bin/env python3
"""ablation_obs — LEQUEL DES DEUX A COUTE 27,8 POINTS ?

Le drapeau `arma_obs` changeait DEUX choses d un coup : il normalise `dcover` comme le pont
(÷30 cape) ET il retire `slope`. La politique est passee de 57,7 % a 29,9 %, et cette chute
n avait AUCUNE CAUSE IDENTIFIEE. ⟨Fable : « ton experience est confondue »⟩

QUATRE BRAS, memes graines, meme budget, meme porte. `arc_obs` est ETEINT PARTOUT — c est la
variable qu on ne veut pas laisser bouger pendant qu on en juge deux autres.

  REF   dcover gymnase, slope presente      (l etat d origine, 12 colonnes)
  DCOV  dcover comme le pont, slope presente            (12 colonnes)
  SLOP  dcover gymnase, slope retiree                   (11 colonnes)
  LES2  les deux                                        (11 colonnes)

⚠️ CE QUI EST DEPOSE AVANT LE PREMIER PAS :
  · si REF ≈ DCOV et SLOP ≈ LES2 -> c est `slope` qui portait les points.
  · si REF ≈ SLOP et DCOV ≈ LES2 -> c est `dcover`.
  · si les quatre se tiennent -> aucun des deux, et la chute venait d ailleurs (bruit de
    graine, budget). On le dira, et on ne choisira pas le recit qui arrange.
  · si SLOP est BAS alors qu Arma ne peut pas fournir cette colonne (borne 0,40 contre une
    moyenne de 0,59 au gymnase, prouve par les formules), alors les 57,7 % etaient GONFLES
    D UNE BEQUILLE DE GYMNASE — un sursitaire de plus, pas un acquis qui tombe. ⟨Fable⟩
"""
import math, sys, statistics as stx, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA
import boucle as B

BRAS = {
    "REF  slope+dcover gym": dict(arma_obs=False, obs_dcover_arma=False, obs_sans_slope=False),
    "DCOV dcover pont seul": dict(arma_obs=False, obs_dcover_arma=True,  obs_sans_slope=False),
    "SLOP slope retiree   ": dict(arma_obs=False, obs_dcover_arma=False, obs_sans_slope=True),
    "LES2 les deux        ": dict(arma_obs=False, obs_dcover_arma=True,  obs_sans_slope=True),
}
ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 800


def monde(kw, n, seed):
    cfg = dict(MONDE_ARMA); cfg.pop("arma_obs", None); cfg["arc_obs"] = False
    cfg.update(kw)
    return AssaultTerrain(num_envs=n, seed=seed, device="cuda:0", max_steps=B.PAS, **cfg)


print(f"\n  ABLATION — {len(BRAS)} bras x {ITERS} iterations, arc ETEINT partout")
print("  " + "=" * 74)
res = {}
for nom, kw in BRAS.items():
    B.monde = lambda n, seed, _kw=kw: monde(_kw, n, seed)
    torch.manual_seed(0)
    pol = B.entrainer(iters=ITERS)
    r, m = B.evaluer(pol, B.GRAINES_TEST)
    moy = lambda v: sum(v) / len(v)
    d = [a - b for a, b in zip(r["appris"], r["flanc"])]
    s = stx.stdev(d) if len(d) > 1 else 0.0
    lo = moy(d) - 2.571 * s / math.sqrt(len(d))
    res[nom] = (moy(r["appris"]), moy(r["frontal"]), moy(r["flanc"]), moy(d), lo, moy(m["appris"]))
    print(f"  {nom} : appris {res[nom][0]:5.1f} %  vs flanc {res[nom][3]:+6.1f} pt  "
          f"borne {res[nom][4]:+6.1f}  metres {res[nom][5]:5.1f}", flush=True)

print("  " + "=" * 74)
print(f"\n  {'bras':<24}{'prise':>8}{'ecart au flanc':>17}{'borne':>9}")
for nom, v in res.items():
    print(f"  {nom:<24}{v[0]:>7.1f}%{v[3]:>16.1f}{v[4]:>9.1f}")
a = list(res.values())
print("\n  LECTURE, contre les attentes deposees")
print("  " + "-" * 60)
d_dcov = abs(a[0][0] - a[1][0]); d_slop = abs(a[0][0] - a[2][0])
print(f"    retirer slope coute      {a[0][0] - a[2][0]:+.1f} points")
print(f"    normaliser dcover coute  {a[0][0] - a[1][0]:+.1f} points")
if d_slop > 2 * d_dcov and d_slop > 5:
    print("    -> C EST `slope` QUI PORTAIT LES POINTS.")
    print("       Or les formules prouvent qu Arma ne peut pas fournir cette colonne :")
    print("       elle y est bornee a 0,40 quand le gymnase en donne 0,59 en moyenne.")
    print("       Les 57,7 % etaient donc GONFLES D UNE BEQUILLE DE GYMNASE.")
elif d_dcov > 2 * d_slop and d_dcov > 5:
    print("    -> C EST `dcover`. La normalisation du pont detruit l information.")
else:
    print("    -> AUCUN DES DEUX NE DOMINE. La chute venait d ailleurs, et on le dit.")
