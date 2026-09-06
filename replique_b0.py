#!/usr/bin/env python3
"""replique_b0 — LE GYMNASE REPRODUIT-IL LE BANC GELE D'ARMA, AU BARREAU B0@30 ?

Pas d'entrainement. On rejoue le TRIPTYQUE de temoins mesure dans Arma le 30/08 et on
regarde si le gymnase rend les MEMES trois taux. C'est la certification de fidelite que
Fable exige avant d'autoriser le gymnase a entrainer ce barreau.

CIBLES (Arma, banc gele, n=51 par temoin, IC95 Wilson) :
    DOCTRINE   100,0 %   [93,0 ; 100]
    ALEATOIRE   11,8 %   [ 5,5 ; 23,4]
    NOOP         0,0 %   [ 0,0 ;  7,0]

LA GEOMETRIE REPLIQUEE, terme a terme :
    distance depart->objectif   30 m        -> R_spawn=30
    rayon de prise               6 m        -> secure_r=6
    budget de temps             20 s        -> max_steps = ceil(20 / 3,28) = 6 pas
    un geste toutes les          4 s        -> ~1,2 pas de gymnase : on decide a chaque pas
    effectifs                  1 contre 0   -> A=1, D=0
    monde                      MONDE_ARMA   -> la config la plus fidele qu'on sache batir

LE CATALOGUE EST REPLIQUE, PAS APPROXIME. Arma offre 13 gestes dont DEUX menent a
l'objectif (le bon cap absolu, et « vers l'objectif »). Le gymnase offre 8 caps + tenir +
feu + 3 postures : un seul mene a l'objectif. Comparer les deux taux du hasard sans
corriger ca mesurerait la difference d'espaces d'action, pas la fidelite du monde.
On exprime donc le catalogue d'Arma DANS les primitives du gymnase.
"""
import sys, math, json, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

DEV = "cuda:0"
N   = 2000          # episodes paralleles
PAS = 6             # 20 s / 3,28 s par pas
CIBLES = {"DOCTRINE": (93.0, 100.0), "ALEATOIRE": (5.5, 23.4), "NOOP": (0.0, 7.0)}

def wilson(k, n, z=1.96):
    ph = k / n; d = 1 + z*z/n
    c = (ph + z*z/(2*n)) / d
    h = z * ((ph*(1-ph)/n + z*z/(4*n*n)) ** 0.5) / d
    return (max(0.0, c-h) * 100, min(1.0, c+h) * 100)

def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi/4.0)).long() % 8)

def monde():
    cfg = dict(MONDE_ARMA)
    cfg.update(dict(secure_only=True, postures=True))
    # D=0 casse l'observation du gymnase (argmin sur une dimension vide). On prend donc
    # D=1 et on TUE le defenseur au pas zero : le monde est vide en fait, pas en forme.
    # `secure_only=True` fait que `win = took` seul, donc un defenseur mort ne finit pas
    # l'episode. Verifie sur assault_terrain.py:843.
    return AssaultTerrain(num_envs=N, A=1, D=1, D_min=1, R_spawn=30.0,
                          secure_r=6.0, max_steps=PAS, device=DEV, seed=7, **cfg)

# --- le catalogue d'Arma, exprime dans les primitives du gymnase -------------
# 0-7 : caps absolus | 8 : vers l'objectif | 9 : engager | 10-12 : postures
def geste_vers_primitive(e, g):
    """g : (N,A) etiquettes du catalogue Arma -> action du gymnase."""
    vers = cap(-e.apx, -e.apy)                 # « vers l'objectif » resolu a la volee
    a = g.clone()
    a = torch.where(g == 8, vers, a)           # le geste 8 devient le bon cap
    return a

def temoin(nom, e, t):
    N_, A_ = e.apx.shape
    if nom == "NOOP":
        return torch.full((N_, A_), 8, dtype=torch.long, device=e.dev)   # 8 = tenir, cote gymnase
    if nom == "ALEATOIRE":
        g = torch.randint(0, 13, (N_, A_), device=e.dev)
        return geste_vers_primitive(e, g)
    g = torch.full((N_, A_), 8, dtype=torch.long, device=e.dev)          # 8 = vers l'objectif
    return geste_vers_primitive(e, g)

def jouer(nom):
    e = monde()
    e.reset()
    e.ddmg[:] = 0.95          # le defenseur est mort d'entree : monde vide, barreau B0
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    d0 = torch.sqrt(e.apx**2 + e.apy**2).mean(1)
    for t in range(PAS):
        a = temoin(nom, e, t)
        _, _, done, info = e.step(a, auto_reset=False)
        pris |= info["took"] & ~fini
        fini |= done.bool()
        if bool(fini.all()): break
    d = torch.sqrt(e.apx**2 + e.apy**2).mean(1)
    return float(pris.float().mean()) * 100, int(pris.sum()), e.N, float((d0 - d).mean())

print(f"{'temoin':10s} {'n':>5s} {'taux':>7s} {'IC95 gymnase':>16s}   {'IC95 ARMA':>14s}  {'gagne_m':>8s}  verdict")
res = {}
for nom in ["DOCTRINE", "ALEATOIRE", "NOOP"]:
    taux, k, n, gm = jouer(nom)
    lo, hi = wilson(k, n)
    alo, ahi = CIBLES[nom]
    ok = (alo <= taux <= ahi)
    res[nom] = dict(taux=taux, k=k, n=n, ic=[lo, hi], arma=[alo, ahi], dans_ic=ok)
    print(f"{nom:10s} {n:5d} {taux:6.1f}% [{lo:5.1f} ; {hi:5.1f}]   [{alo:5.1f};{ahi:5.1f}]  {gm:7.1f}   {'DANS' if ok else 'HORS'}")

tous = all(v["dans_ic"] for v in res.values())
print()
print("VERDICT DE FIDELITE B0@30 :", "GYMNASE CERTIFIE" if tous else "GYMNASE REFUTE pour ce barreau")
json.dump(res, open("/home/younes/arma3-marl/REPLIQUE_B0.json", "w"), indent=1)
