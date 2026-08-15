import sys, glob, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
DC, ALIVE, LOS = 6, 4, 7
COUV, EXPO = 0.033, 0.5

# ═══ REGLE 18 — LES PORTES SONT EXECUTEES AVANT DE JUGER ═══
def lire(r_choix, d_forcee):
    if 0.7 <= r_choix <= 1.4 and d_forcee > 20: return "SUBIE"
    if r_choix > 1.4: return "CHOISIE"
    return "INDECIS"
print("─── REGLE 18 : les portes passent leur propre banc ───")
cas = [("doit rendre SUBIE",   1.05, 35.0, "SUBIE"),
       ("doit rendre CHOISIE", 2.10,  5.0, "CHOISIE"),
       ("doit rendre INDECIS", 1.05, 10.0, "INDECIS"),
       ("doit rendre INDECIS", 0.40, 35.0, "INDECIS")]
ok = True
for nom, a, b, att in cas:
    got = lire(a, b); bon = got == att; ok &= bon
    print(f"  {'✓' if bon else '⛔'} {nom:<22} (rapport {a:.2f}, forcee {b:+.0f} pts) → {got}")
if not ok: raise SystemExit("  ⛔ une porte ne fait pas ce que le depot dit. On ne mesure pas.")
print("  ✓ chaque bande est atteignable ET rejetable. Les portes sont jugees.\n")

def stats(O, nom):
    couv = O[:, DC] <= COUV; exp = O[:, LOS] > EXPO
    p_choix = exp[couv].mean() if couv.sum() else float("nan")
    p_sans  = exp[~couv].mean() if (~couv).sum() else float("nan")
    forcee  = 100*(~couv)[exp].mean() if exp.sum() else float("nan")
    print(f"─── {nom} ───")
    print(f"  pas avec couvert a portee : {couv.sum():6d}   ·  sans : {(~couv).sum():6d}")
    print(f"  P(expose | couvert A PORTEE) = {p_choix:.3f}      <- s expose-t-il quand il a le CHOIX")
    print(f"  P(expose | PAS de couvert)   = {p_sans:.3f}")
    print(f"  part de l exposition FORCEE  = {forcee:.1f} %      <- exposition sans alternative")
    print(f"  exposition totale            = {100*exp.mean():.1f} %\n")
    return dict(pc=p_choix, ps=p_sans, f=forcee, nc=int(couv.sum()), ns=int((~couv).sum()))

pol = charger(B.DEV); e = B.monde(64, 101); e.reset()
G = []
for t in range(60):
    o = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    with torch.no_grad(): l, v = pol(e._obs())
    e.step(l.argmax(-1), auto_reset=False)
    G.append(o[o[:, ALIVE] > 0.5])
G = np.concatenate(G)

A = []
for f in sorted(glob.glob("/mnt/data/harmattan-sandbox/logs/live20/ep_*.npz")):
    Z = np.load(f, allow_pickle=True); X = Z["obs18"][:, COLS]
    A.append(X[X[:, ALIVE] > 0.5])
A = np.concatenate(A)

rg = stats(G, "GYMNASE"); ra = stats(A, "ARMA (serie 3, corps repare)")

print("─── CONTROLES POSITIFS ───")
c1 = min(rg["nc"], rg["ns"], ra["nc"], ra["ns"]) >= 100
print(f"  1. >=100 pas dans chaque situation, chaque monde ? min = {min(rg['nc'],rg['ns'],ra['nc'],ra['ns'])} → " + ("✓ PASSE" if c1 else "⛔ TOMBE"))
c2 = 0.01 < G[:,LOS].mean() < 0.99 and 0.01 < A[:,LOS].mean() < 0.99
print(f"  2. `los` separe-t-il ? gymnase {G[:,LOS].mean():.2f} · Arma {A[:,LOS].mean():.2f} → " + ("✓ PASSE" if c2 else "⛔ TOMBE"))
if not (c1 and c2): raise SystemExit("\n  ⇒ aucune lecture admissible.")

r = ra["pc"]/rg["pc"]; d = ra["f"] - rg["f"]
print(f"\n─── LA LECTURE ───")
print(f"  rapport P(expose | choix possible) Arma/gymnase = {r:.2f}")
print(f"  ecart de part FORCEE  Arma - gymnase           = {d:+.1f} points")
print(f"\n  ⇒ {lire(r, d)}")
