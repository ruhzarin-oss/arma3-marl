#!/usr/bin/env python3
"""lire_dco — les portes de `banc_dco`, telles qu elles sont ECRITES, sans en bouger une.

Aucun seuil n est relu depuis les donnees. Chaque porte est recopiee du docstring de
`banc_dco.py`, evaluee, et le verdict est imprime meme quand il est defavorable.
"""
import json, sys, math, random

SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/younes/arma3-marl/logs_train/banc_dco.jsonl"
random.seed(12345)
BRAS = {}
for l in open(SRC):
    d = json.loads(l)
    BRAS[d["bras"]] = d["episodes"]


def moy(v):
    return sum(v) / max(len(v), 1)


def perm(a, b, n=20000):
    """p bilateral par permutation sur la difference des moyennes."""
    obs = abs(moy(a) - moy(b))
    tout = a + b
    na = len(a)
    c = 0
    for _ in range(n):
        random.shuffle(tout)
        if abs(moy(tout[:na]) - moy(tout[na:])) >= obs - 1e-15:
            c += 1
    return (c + 1) / (n + 1)


def binom(k, n, p=0.5):
    """p bilateral exact."""
    from math import comb
    pk = comb(n, k) * p ** k * (1 - p) ** (n - k)
    s = sum(comb(n, i) * p ** i * (1 - p) ** (n - i)
            for i in range(n + 1)
            if comb(n, i) * p ** i * (1 - p) ** (n - i) <= pk + 1e-18)
    return min(1.0, s)


def col(bras, k, feu=False, cote=False):
    ep = BRAS[bras]
    if feu:
        ep = [e for e in ep if e["feu"] > 0]
    if cote:   # I4 : seuls les episodes ou « le cote » a un sens ET une bonne reponse
        ep = [e for e in ep if e["excursion"] > 20.0 and e["asym"] > 0.02]
    return [e[k] for e in ep]


def pentes_comparees(bras_a, bras_b, n=5000):
    """Ecart entre les pentes haltes/vivants des deux bras, p par permutation des ETIQUETTES.

    La pente seule est confondue avec la survie : elle est negative dans TOUS les bras.
    Ce qui distingue une camaraderie forte d une camaraderie bornee, c est l ECART.
    """
    def prep(bras):
        ep = [e for e in BRAS[bras] if e["feu"] > 0]
        return [(e["viv"], e["haltes"], e["cout"]) for e in ep]

    def pente_de(lot):
        x = [a for a, _, _ in lot]; y = [b for _, b, _ in lot]; z = [c for _, _, c in lot]
        def resid(v, w):
            mw, mv = moy(w), moy(v)
            sw = sum((wi - mw) ** 2 for wi in w)
            b = sum((vi - mv) * (wi - mw) for vi, wi in zip(v, w)) / sw if sw else 0.0
            return [vi - mv - b * (wi - mw) for vi, wi in zip(v, w)]
        xr, yr = resid(x, z), resid(y, z)
        sx = sum(v * v for v in xr)
        return sum(a * c for a, c in zip(xr, yr)) / sx if sx else 0.0

    la, lb = prep(bras_a), prep(bras_b)
    obs = pente_de(la) - pente_de(lb)
    tout = la + lb
    na = len(la)
    c = 0
    for _ in range(n):
        random.shuffle(tout)
        if (pente_de(tout[:na]) - pente_de(tout[na:])) <= obs + 1e-15:
            c += 1
    return pente_de(la), pente_de(lb), obs, (c + 1) / (n + 1)   # p UNILATERAL : a < b


def pente(bras):
    """Pente de `haltes` sur le nombre de vivants, A EXPOSITION EGALE (residualisee)."""
    ep = [e for e in BRAS[bras] if e["feu"] > 0]
    x = [e["viv"] for e in ep]; y = [e["haltes"] for e in ep]; z = [e["cout"] for e in ep]
    def resid(v, w):
        mw = moy(w); mv = moy(v)
        sw = sum((wi - mw) ** 2 for wi in w)
        b = sum((vi - mv) * (wi - mw) for vi, wi in zip(v, w)) / sw if sw else 0.0
        return [vi - mv - b * (wi - mw) for vi, wi in zip(v, w)]
    xr, yr = resid(x, z), resid(y, z)
    sx = sum(v * v for v in xr)
    b = sum(a * c for a, c in zip(xr, yr)) / sx if sx else 0.0
    # p par permutation des etiquettes x
    obs = abs(b)
    c = 0
    for _ in range(5000):
        random.shuffle(xr)
        bb = sum(a * cc for a, cc in zip(xr, yr)) / sx if sx else 0.0
        if abs(bb) >= obs - 1e-15:
            c += 1
    return b, (c + 1) / 5001


print("\n  PORTES PRE-ENREGISTREES DE banc_dco — evaluees telles qu ecrites")
print("  " + "=" * 72)

# ---- G0 : CONTROLE POSITIF
a, b = col("DCO", "cout"), col("FRONTAL", "cout")
rel = (moy(b) - moy(a)) / moy(a)
p0 = perm(a, b)
g0 = (abs(rel) >= 0.25) and (p0 < 0.01)
print(f"\n  G0  CONTROLE POSITIF — I2 doit separer FRONTAL de DCO de >= 25 %, p < 0,01")
print(f"      DCO {moy(a):.5f}   FRONTAL {moy(b):.5f}   ecart relatif {rel:+.1%}   p = {p0:.5f}")
print(f"      -> {'PASSE' if g0 else 'TOMBE'}")

# ---- G0b : CONTROLE NUL
print(f"\n  G0b CONTROLE NUL — DCO contre DCO' : rien ne doit sortir a p < 0,05/6 = 0,00833")
pires = []
for k, feu, cote in (("prise", False, False), ("cout", False, False), ("vus", False, False),
                     ("accord", False, True), ("haltes", True, False), ("viv", False, False)):
    p = perm(col("DCO", k, feu, cote), col("DCO'", k, feu, cote))
    pires.append((k, p))
    print(f"      {k:<8} p = {p:.5f}" + ("   <-- SORT" if p < 0.05 / 6 else ""))
g0b = all(p >= 0.05 / 6 for _, p in pires)
print(f"      -> {'PASSE' if g0b else 'TOMBE'}")

# ---- G1 : le flanc
ao = col("ORACLE", "accord", cote=True)
g1c = moy(ao) >= 0.80
print(f"\n  G1c CONTROLE D INSTRUMENT — ORACLE (contourne du cote couvert par construction)")
print(f"      doit obtenir I4 >= 0,80 : {moy(ao):.3f} sur {len(ao)} episodes")
print(f"      -> {'PASSE — l instrument sait tirer' if g1c else 'TOMBE — I4 EST AVEUGLE'}")

ad, ar = col("DCO", "accord", cote=True), col("DCO+R1", "accord", cote=True)
kd, nd = int(sum(ad)), len(ad)
kr, nr = int(sum(ar)), len(ar)
pr = binom(kr, nr)
g1 = g1c and (0.42 <= moy(ad) <= 0.58) and (moy(ar) > 0.65) and (pr < 0.05)
print(f"\n  G1  D1 — accord avec le couvert : DCO dans [0,42;0,58] ET R1 > 0,65 (p < 0,05)")
print(f"      DCO {moy(ad):.3f} ({kd}/{nd})   DCO+R1 {moy(ar):.3f} ({kr}/{nr})  p = {pr:.4f}")
print(f"      -> {'PASSE' if g1 else 'TOMBE'}"
      + ("" if g1c else "   (non lisible : G1c tombee)"))

# ---- G2 : la suppression
hd, hr = col("DCO", "haltes", True), col("DCO+R2", "haltes", True)
rel2 = (moy(hd) - moy(hr)) / moy(hd)
p2 = perm(hd, hr)
g2 = (rel2 >= 0.20) and (p2 < 0.05)
print(f"\n  G2  D2 — I5 doit baisser de >= 20 % de DCO a DCO+R2, p < 0,05")
print(f"      DCO {moy(hd):.4f}   DCO+R2 {moy(hr):.4f}   baisse {rel2:+.1%}   p = {p2:.5f}")
print(f"      -> {'PASSE' if g2 else 'TOMBE'}")

# ---- G3 : la camaraderie
def dd(bras_a, bras_b, n=20000):
    """Difference de differences : [haltes(4h) - haltes(8h)] de A, contre le meme de B.

    La camaraderie doit faire s arreter MOINS une escouade de 8 qu une de 4. L ecart 4h-8h
    est donc positif quand elle pese, et l instrument compare cet ecart entre deux bras.
    p unilateral : ecart(A) > ecart(B).
    """
    a4, a8 = col(bras_a, "haltes", True), col(bras_a + "@8", "haltes", True)
    b4, b8 = col(bras_b, "haltes", True), col(bras_b + "@8", "haltes", True)
    obs = (moy(a4) - moy(a8)) - (moy(b4) - moy(b8))
    t4, t8 = a4 + b4, a8 + b8
    na4, na8 = len(a4), len(a8)
    c = 0
    for _ in range(n):
        random.shuffle(t4); random.shuffle(t8)
        d = (moy(t4[:na4]) - moy(t8[:na8])) - (moy(t4[na4:]) - moy(t8[na8:]))
        if d >= obs - 1e-15:
            c += 1
    return (moy(a4) - moy(a8)), (moy(b4) - moy(b8)), obs, (c + 1) / (n + 1)


ea, eb, obs_c, p_ctrl = dd("CAM5", "DCO")
g3c = p_ctrl < 0.05
print(f"\n  G3c CONTROLE D INSTRUMENT — ecart de haltes entre 4 et 8 hommes : CAM5")
print(f"      (camaraderie x5) doit l avoir SIGNIFICATIVEMENT plus grand que DCO")
print(f"      CAM5 4h-8h {ea:+.4f}   DCO 4h-8h {eb:+.4f}   dif-de-dif {obs_c:+.4f}   p = {p_ctrl:.5f}")
print(f"      -> {'PASSE — l instrument sait tirer' if g3c else 'TOMBE — I6 RESTE AVEUGLE'}")

ed, er, obs3, p3 = dd("DCO", "DCO+R3")
g3 = g3c and (p3 < 0.05)
print(f"\n  G3  D3 — ecart 4h-8h de DCO significativement plus grand que celui de DCO+R3")
print(f"      DCO {ed:+.4f}   DCO+R3 {er:+.4f}   dif-de-dif {obs3:+.4f}   p = {p3:.5f}")
print(f"      -> {'PASSE' if g3 else 'TOMBE'}"
      + ("" if g3c else "   (non lisible : G3c tombee)"))

print("\n  " + "=" * 72)
if not g0:
    print("  VERDICT : G0 TOMBE — LE BANC EST MUET. Les portes G1-G3 ne sont pas lisibles,")
    print("            quels que soient leurs chiffres. C est le resultat de la journee.")
else:
    n = sum([g1, g2, g3])
    print(f"  VERDICT : G0 et G0b {'passees' if g0b else 'NON passees'} — "
          f"{n}/3 defauts retrouves a l aveugle.")
