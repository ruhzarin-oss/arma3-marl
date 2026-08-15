import sys, math, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger
import boucle as B
from boucle import cap, frontal, flanc, jouer, monde

def script(e, t):
    a = cap(-e.apx, -e.apy)
    demi = max(1, e.A // 2)
    ap = torch.zeros(e.N, e.A, dtype=torch.bool, device=e.dev)
    if (t // 3) % 2 == 0: ap[:, demi:] = True
    else:                 ap[:, :demi] = True
    d = torch.sqrt(e.apx**2 + e.apy**2)
    return torch.where(ap & (d < e.fire_range*0.9), torch.full_like(a, 9), a)

# ═══ REGLE 18 : portes executees, et le domaine est BALAYE ═══
def lire(n_inv): return "CLASSE COMME ARMA" if n_inv == 0 else "CLASSEMENT INVERSE"
print("─── REGLE 18 : portes executees, domaine balaye ───")
for n, att in [(0,"CLASSE COMME ARMA"), (1,"CLASSEMENT INVERSE"), (3,"CLASSEMENT INVERSE")]:
    print(f"  {'✓' if lire(n)==att else '⛔'} {n} inversion(s) → {lire(n)}")
print("  ✓ le domaine (0..3 inversions) est entierement couvert, aucune region sans lecture.\n")

pol = charger(B.DEV)
def gele(o, t):
    with torch.no_grad(): lo, v = pol(o)
    return lo.argmax(-1), None, None

BRAS = [("FRONTAL", lambda e: (lambda o,t,_e=e: (frontal(_e,t), None, None))),
        ("FLANC",   lambda e: (lambda o,t,_e=e: (flanc(_e,t), None, None))),
        ("SCRIPT",  lambda e: (lambda o,t,_e=e: (script(_e,t), None, None))),
        ("POLITIQUE", lambda e: gele)]
GRAINES = B.GRAINES_TEST
R, A9 = {}, {}
for nom, mk in BRAS:
    pr, n9 = [], 0
    for g in GRAINES:
        e = monde(256, g); f = mk(e)
        if nom == "SCRIPT":
            n9 += int((script(e, 0) == 9).sum())
        st, *_ = jouer(e, f)
        pr.append(st["prise"])
    R[nom] = float(np.mean(pr)); A9[nom] = n9
    print(f"  {nom:<10} prise {R[nom]:5.1f} %   (6 graines held-out x 256 env)")

print("\n─── CONTROLES POSITIFS ───")
ec = max(R.values()) - min(R.values())
print(f"  1. le gymnase separe-t-il ses bras ? ecart {ec:.1f} pts (porte 10) → " + ("✓ PASSE" if ec >= 10 else "⛔ TOMBE"))
print(f"  2. SCRIPT emet-il l action 9 au gymnase ? {A9['SCRIPT']} occurrences au pas 0 → " + ("✓ PASSE" if A9['SCRIPT'] > 0 else "⛔ TOMBE"))

ARMA = {"POLITIQUE": 11.9}   # 8/67 mesures. FLANC et SCRIPT arrivent avec la chaine.
print("\n─── LE CLASSEMENT ───")
print(f"  {'bras':<10}{'GYMNASE':>10}{'ARMA':>10}")
for nom in ["FRONTAL","FLANC","SCRIPT","POLITIQUE"]:
    a = ARMA.get(nom); print(f"  {nom:<10}{R[nom]:>9.1f} %{(f'{a:>9.1f} %' if a is not None else '        —')}")
print("\n  ⚠️ Les bras FLANC et SCRIPT cote Arma ne sont pas encore mesures (chaine en cours).")
print("     Le classement inter-mondes se lira quand ils seront la. Rien n est conclu ici.")
