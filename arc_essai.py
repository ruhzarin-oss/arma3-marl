#!/usr/bin/env python3
"""arc_essai — LA TENTATIVE UNIQUE DE L ARC. Dépôt : DEPOT_ARC_PREENREGISTRE.md

TROIS BRAS, memes graines, meme budget, entraines DANS LE MEME RUN :
  ARC     14 colonnes : base9 + arc2 + posture3
  SANS    12 colonnes : base9 + posture3            <- le bras de reference, REMESURE ici
  BRUIT   14 colonnes, mais les deux colonnes d arc remplacees par du BRUIT
          -> CONTROLE NUL : si le bruit passe le seuil, c est le banc qui donne la victoire.

Seuil DEPOSE : l arc doit rendre >= 5 points de prise au-dessus du bras SANS, lu sur la BORNE
inferieure de l intervalle a 95 pour cent de l ecart apparie PAR GRAINE.
⚠️ Le 53,3 pourcent de l ancien monde ne sert pas de reference : il est partiel.
⚠️ Toute retouche apres cette lecture consomme la tentative.
"""
import math, sys, statistics as stx, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA
import boucle as B

ITERS = int(sys.argv[1]) if len(sys.argv) > 1 else 800
BRAS = {"ARC  ": dict(arc_obs=True), "SANS ": dict(arc_obs=False), "BRUIT": dict(arc_obs=True)}


def monde(kw, n, seed):
    cfg = dict(MONDE_ARMA); cfg.update(kw)
    return AssaultTerrain(num_envs=n, seed=seed, device="cuda:0", max_steps=B.PAS, **cfg)


def brouiller(o):
    """CONTROLE NUL : les deux colonnes d arc (9 et 10) remplacees par du bruit de meme
    amplitude. Le monde est IDENTIQUE ; seule l information portee change."""
    o = o.clone()
    o[..., 9:11] = torch.randn_like(o[..., 9:11])
    return o


print(f"\n  L ARC — tentative unique, {ITERS} iterations par bras, arc ETEINT dans SANS")
print("  " + "=" * 74)
res, met = {}, {}
for nom, kw in BRAS.items():
    bruit = (nom == "BRUIT")
    B.monde = lambda n, seed, _kw=kw: monde(_kw, n, seed)
    if bruit:
        _obs = AssaultTerrain._obs
        AssaultTerrain._obs = lambda self, _f=_obs: brouiller(_f(self))
    torch.manual_seed(0)
    pol = B.entrainer(iters=ITERS)
    r, m = B.evaluer(pol, B.GRAINES_TEST)
    if bruit:
        AssaultTerrain._obs = _obs
    res[nom] = r["appris"]; met[nom] = m["appris"]
    moy = lambda v: sum(v) / len(v)
    print(f"  {nom} : prise {moy(r['appris']):5.1f} %   metres {moy(m['appris']):6.1f}", flush=True)
    if nom == "ARC  ":
        torch.save(pol.state_dict(), "/home/younes/arma3-marl/arc_pol.pt")

print("  " + "=" * 74)
moy = lambda v: sum(v) / len(v)


def borne(a, b):
    d = [x - y for x, y in zip(a, b)]
    s = stx.stdev(d) if len(d) > 1 else 0.0
    return moy(d), moy(d) - 2.571 * s / math.sqrt(len(d))


e_arc, lo_arc = borne(res["ARC  "], res["SANS "])
e_bru, lo_bru = borne(res["BRUIT"], res["SANS "])
print(f"\n  LA PORTE — 5 points, lue SUR LA BORNE, appariee par graine")
print(f"    ARC   contre SANS : {e_arc:+6.1f} pt   borne {lo_arc:+6.1f}")
print(f"    BRUIT contre SANS : {e_bru:+6.1f} pt   borne {lo_bru:+6.1f}   (controle nul)")
g1 = lo_arc >= 5.0
g2 = lo_bru < 5.0
g3 = moy(met["ARC  "]) >= moy(met["SANS "]) * 0.95
print(f"\n    {'PASSE' if g1 else 'TOMBE'}  l arc rend >= 5 points, sur la borne")
print(f"    {'PASSE' if g2 else 'TOMBE'}  CONTROLE NUL : le bruit ne passe pas le seuil")
print(f"    {'PASSE' if g3 else 'TOMBE'}  anti-planque : {moy(met['ARC  ']):.1f} m contre {moy(met['SANS ']):.1f} m")
print("  " + "=" * 74)
if g1 and g2 and g3:
    print("    L ARC EST RETENU. Deux nombres certifies rendus a l agent, et ils paient.")
else:
    print("    L ARC N EST PAS RETENU. Par le depot : on n ajoute PAS une treizieme idee a la")
    print("    perception — c est l ALGORITHME qui se redepose. La tentative est consommee.")
print("\n    ⚠️ AUCUN VERDICT DE MISSION. Le monde est le notre ; Arma tranchera.")
