"""subie2 — REFAIT apres retractation. Le seuil 0,033 etait INFERIEUR a 1/30 = 0,03333,
donc « couvert a portee » excluait les 116 pas a exactement UNE cellule et se reduisait a
« SUR le couvert ». Corrige : <= 1/30 + eps."""
import sys, glob, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
DC, ALIVE, LOS = 6, 4, 7
PORTEE = 1.0/30.0 + 1e-9          # UNE cellule, bornes incluses
EXPO = 0.5

def lire(r_choix, d_forcee):
    if 0.7 <= r_choix <= 1.4 and d_forcee > 20: return "SUBIE"
    if r_choix > 1.4: return "CHOISIE"
    return "INDECIS"
print("─── REGLE 18 : les portes passent leur banc ───")
for a, b, att in [(1.05,35.0,"SUBIE"), (2.10,5.0,"CHOISIE"), (1.05,10.0,"INDECIS"), (0.40,35.0,"INDECIS")]:
    got = lire(a,b); print(f"  {'✓' if got==att else '⛔'} rapport {a:.2f}, forcee {b:+.0f} → {got}")
print()

def stats(O, nom):
    couv = O[:, DC] <= PORTEE; exp = O[:, LOS] > EXPO
    pc = exp[couv].mean(); ps = exp[~couv].mean(); f = 100*(~couv)[exp].mean()
    print(f"─── {nom} ───")
    print(f"  couvert a portee (<=1 cellule) : {couv.sum():6d} pas   ·   sans : {(~couv).sum():6d}")
    print(f"  P(expose | couvert A PORTEE) = {pc:.3f}")
    print(f"  P(expose | PAS de couvert)   = {ps:.3f}")
    print(f"  part de l exposition FORCEE  = {f:.1f} %\n")
    return dict(pc=pc, f=f, nc=int(couv.sum()), ns=int((~couv).sum()))

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

rg = stats(G, "GYMNASE"); ra = stats(A, "ARMA")
print("─── CONTROLE POSITIF ───")
c1 = min(rg["nc"], rg["ns"], ra["nc"], ra["ns"]) >= 100
print(f"  >=100 pas par situation, chaque monde ? min = {min(rg['nc'],rg['ns'],ra['nc'],ra['ns'])} → " + ("✓ PASSE" if c1 else "⛔ TOMBE"))
if not c1: raise SystemExit()
r = ra["pc"]/rg["pc"]; d = ra["f"] - rg["f"]
print(f"\n─── LA LECTURE ───\n  rapport P(expose | choix possible) = {r:.2f}   ·   ecart part forcee = {d:+.1f} pts")
print(f"\n  ⇒ {lire(r, d)}")
print(f"\n  (avant correction du seuil : rapport 3,13, lecture CHOISIE — sur un masque qui valait « dessus »)")
