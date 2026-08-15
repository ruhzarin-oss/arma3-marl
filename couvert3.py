"""AMENDEMENT FINAL : la protection ne se lit QUE chez les exposes.
Derivable de la formule sans regarder aucune donnee :
    dmg = p * los * tir * (1 - 0,7*incover)
`incover` ne multiplie qu un terme proportionnel a `los`. Chez un non-expose (los=0) le
terme est nul et le couvert ne PEUT rien faire. Les inclure dilue l effet.
DERNIER amendement : si le controle retombe, la question se ferme."""
import sys, glob, numpy as np, torch, math
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
import terrain_gpu as TG
DC, ALIVE, LOS = 6, 4, 7

pol = charger(B.DEV); e = B.monde(64, 101); e.reset()
Cg, Mg, Eg = [], [], []
for t in range(60):
    inc = TG.sample(e.cover, e.apx, e.apy, e.scale).clamp(max=1.0).reshape(-1).cpu().numpy()
    o  = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    with torch.no_grad(): l, v = pol(e._obs())
    e.step(l.argmax(-1), auto_reset=False)
    o2 = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    viv = o[:, ALIVE] > 0.5
    Cg.append((inc>0.5)[viv]); Eg.append((o[:,LOS]>0.5)[viv])
    Mg.append(((o[:,ALIVE]>0.5)&(o2[:,ALIVE]<=0.5))[viv])
Cg, Mg, Eg = np.concatenate(Cg), np.concatenate(Mg), np.concatenate(Eg)

Ca, Ma, Ea = [], [], []
for f in sorted(glob.glob("/mnt/data/harmattan-sandbox/logs/live20/ep_*.npz")):
    Z = np.load(f, allow_pickle=True)
    A = Z["obs18"][:, COLS]; pas = np.asarray(Z["pas"]); u = np.unique(pas)
    P = [A[pas==p] for p in u]
    for a, b in zip(P[:-1], P[1:]):
        n = min(len(a), len(b))
        if n == 0: continue
        viv = a[:n, ALIVE] > 0.5
        Ca.append((a[:n,DC]<1e-6)[viv]); Ea.append((a[:n,LOS]>0.5)[viv])
        Ma.append(((a[:n,ALIVE]>0.5)&(b[:n,ALIVE]<=0.5))[viv])
Ca, Ma, Ea = np.concatenate(Ca), np.concatenate(Ma), np.concatenate(Ea)

R = {}
print("─── PROTECTION CHEZ LES EXPOSES SEULEMENT ───\n")
for nom, C, M, E in [("GYMNASE", Cg, Mg, Eg), ("ARMA", Ca, Ma, Ea)]:
    C, M = C[E], M[E]
    nc, nl = C.sum(), (~C).sum(); mc, ml = int(M[C].sum()), int(M[~C].sum())
    pc = mc/max(nc,1); pl = ml/max(nl,1)
    R[nom] = dict(prot=(pl/pc if pc>0 else float("inf")), mc=mc, ml=ml, pc=pc, pl=pl)
    print(f"  {nom}")
    print(f"    exposé SUR le couvert : {nc:5d} pas · {mc:3d} morts · P = {pc:.4f}")
    print(f"    exposé hors couvert   : {nl:5d} pas · {ml:3d} morts · P = {pl:.4f}")
    print(f"    PROTECTION = {R[nom]['prot']:.2f}\n")

ok1 = all(R[k]["prot"] > 1 for k in R)
ok2 = all(R[k]["mc"] >= 30 and R[k]["ml"] >= 30 for k in R)
print("─── LES CONTROLES ───")
print(f"  1. protection > 1 partout ? " + " · ".join(f"{k} {R[k]['prot']:.2f}" for k in R) + " → " + ("✓ PASSE" if ok1 else "⛔ TOMBE"))
print(f"  2. ≥30 morts par groupe ?   " + " · ".join(f"{k} {R[k]['mc']}/{R[k]['ml']}" for k in R) + " → " + ("✓ PASSE" if ok2 else "⛔ TOMBE"))

if ok1 and ok2:
    r = R["GYMNASE"]["prot"]/R["ARMA"]["prot"]
    print(f"\n─── HYPOTHESE B ───\n  protection gymnase / Arma = {r:.2f}")
    print("  ⇒ " + ("le GYMNASE SUR-PROTEGE, B RETENUE." if r>2 else "Arma protege plus, B refutee dans l autre sens." if r<0.5 else "les deux protegent PAREIL, B REFUTEE."))
else:
    print("\n─── LA QUESTION SE FERME ───")
    print("  C etait le dernier amendement. B n est pas mesurable a cette taille.")
    pa = R["ARMA"]["pc"] if R["ARMA"]["pc"]>0 else 0.05
    besoin = math.ceil(30/max(R["ARMA"]["mc"],1) * 20)
    print(f"  Arma rend {R['ARMA']['mc']} morts exposes-sur-couvert en 20 episodes.")
    print(f"  Il en faudrait 30 par groupe → environ {besoin} EPISODES, soit {besoin*9//60} h de banc.")
    print("  La question reste OUVERTE, non tranchee, et son prix est chiffre.")
