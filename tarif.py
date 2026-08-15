import sys, glob, numpy as np, torch, math
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
LOS, ALIVE = 7, 4

def tarif(exp, mort, nom):
    """exp, mort : tableaux booleens par (homme, pas)."""
    ne, nn = exp.sum(), (~exp).sum()
    me, mn = mort[exp].sum(), mort[~exp].sum()
    pe = me/max(ne,1); pn = mn/max(nn,1)
    t = pe/pn if pn > 0 else float("inf")
    print(f"  {nom}")
    print(f"    exposes     : {ne:6d} pas · {me:4d} morts · P = {pe:.4f}")
    print(f"    non exposes : {nn:6d} pas · {mn:4d} morts · P = {pn:.4f}")
    print(f"    TARIF = {t:.2f}    (morts au total : {me+mn})")
    return t, me+mn, pe, pn

# ─── ARMA : 20 episodes de la serie 3
E, M = [], []
for f in sorted(glob.glob("/mnt/data/harmattan-sandbox/logs/live20/ep_*.npz")):
    Z = np.load(f, allow_pickle=True)
    A = Z["obs18"][:, COLS]; pas = np.asarray(Z["pas"]); u = np.unique(pas)
    P = [A[pas==p] for p in u]
    for a, b in zip(P[:-1], P[1:]):
        n = min(len(a), len(b))
        if n == 0: continue
        viv = a[:n, ALIVE] > 0.5
        E.append((a[:n, LOS] > 0.5)[viv]); M.append(((a[:n,ALIVE]>0.5) & (b[:n,ALIVE]<=0.5))[viv])
Ea, Ma = np.concatenate(E), np.concatenate(M)

# ─── GYMNASE : meme politique, memes definitions
pol = charger(B.DEV); e = B.monde(64, 101); e.reset()
Eg, Mg = [], []
for t in range(60):
    o = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    with torch.no_grad(): l, v = pol(e._obs())
    e.step(l.argmax(-1), auto_reset=False)
    o2 = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    viv = o[:, ALIVE] > 0.5
    Eg.append((o[:, LOS] > 0.5)[viv]); Mg.append(((o[:,ALIVE]>0.5) & (o2[:,ALIVE]<=0.5))[viv])
Eg, Mg = np.concatenate(Eg), np.concatenate(Mg)

print("─── LE TARIF, MEME DEFINITION DES DEUX COTES ───\n")
tg, ng, peg, png = tarif(Eg, Mg, "GYMNASE")
print()
ta, na, pea, pna = tarif(Ea, Ma, "ARMA (serie 3, corps repare)")

print("\n─── CONTROLES POSITIFS ───")
ok1 = tg > 1 and ta > 1
print(f"  1. tarif > 1 dans chaque monde ? gymnase {tg:.2f} · Arma {ta:.2f} → " + ("✓ PASSE" if ok1 else "⛔ TOMBE — capteur muet"))
ok2 = ng >= 30 and na >= 30
print(f"  2. au moins 30 morts de chaque cote ? gymnase {ng} · Arma {na} → " + ("✓ PASSE" if ok2 else "⛔ TOMBE — on ne lit pas"))
print(f"  3. `los` separe-t-il ? part exposee : gymnase {100*Eg.mean():.1f} % · Arma {100*Ea.mean():.1f} %")
if not (ok1 and ok2): raise SystemExit("\n  ⇒ la mesure ne rend pas de lecture.")

r = ta/tg
print(f"\n─── LA PORTE ───\n  rapport Arma / gymnase = {r:.2f}")
if   r > 2:   v = "ARMA FAIT PAYER BEAUCOUP PLUS CHER. Le gymnase est trop clement :\n     l agent a appris a s exposer a un prix qui n existe pas la-bas."
elif r < 0.5: v = "Arma fait payer MOINS cher. Le tarif n explique pas l echec — piste FERMEE."
else:         v = "LES DEUX MONDES FACTURENT PAREIL. Le tarif n explique pas l ecart,\n     il faut chercher ailleurs."
print(f"\n  ⇒ {v}")
