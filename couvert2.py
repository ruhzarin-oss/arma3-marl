import sys, glob, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
import terrain_gpu as TG
DC, ALIVE = 6, 4

# ─── GYMNASE : incover LU DANS LE MOTEUR, la ou les degats le lisent
pol = charger(B.DEV); e = B.monde(64, 101); e.reset()
Cg, Mg = [], []
for t in range(60):
    inc = TG.sample(e.cover, e.apx, e.apy, e.scale).clamp(max=1.0).reshape(-1).cpu().numpy()
    o  = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    with torch.no_grad(): l, v = pol(e._obs())
    e.step(l.argmax(-1), auto_reset=False)
    o2 = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    viv = o[:, ALIVE] > 0.5
    Cg.append((inc > 0.5)[viv]); Mg.append(((o[:,ALIVE]>0.5)&(o2[:,ALIVE]<=0.5))[viv])
Cg, Mg = np.concatenate(Cg), np.concatenate(Mg)

# ─── ARMA : dcover == 0 cellule  <=>  la cellule courante EST du couvert
Ca, Ma = [], []
for f in sorted(glob.glob("/mnt/data/harmattan-sandbox/logs/live20/ep_*.npz")):
    Z = np.load(f, allow_pickle=True)
    A = Z["obs18"][:, COLS]; pas = np.asarray(Z["pas"]); u = np.unique(pas)
    P = [A[pas==p] for p in u]
    for a, b in zip(P[:-1], P[1:]):
        n = min(len(a), len(b))
        if n == 0: continue
        viv = a[:n, ALIVE] > 0.5
        Ca.append((a[:n, DC] < 1e-6)[viv]); Ma.append(((a[:n,ALIVE]>0.5)&(b[:n,ALIVE]<=0.5))[viv])
Ca, Ma = np.concatenate(Ca), np.concatenate(Ma)

R = {}
for nom, C, M in [("GYMNASE", Cg, Mg), ("ARMA", Ca, Ma)]:
    nc, nl = C.sum(), (~C).sum(); mc, ml = M[C].sum(), M[~C].sum()
    pc = mc/max(nc,1); pl = ml/max(nl,1)
    R[nom] = dict(prot=(pl/pc if pc>0 else float("inf")), mc=int(mc), ml=int(ml), part=100*C.mean())
    print(f"─── {nom} ───")
    print(f"  SUR le couvert : {nc:6d} pas · {mc:4d} morts · P = {pc:.4f}")
    print(f"  hors couvert   : {nl:6d} pas · {ml:4d} morts · P = {pl:.4f}")
    print(f"  PROTECTION = {R[nom]['prot']:.2f}   ·   part du temps SUR le couvert = {100*C.mean():.1f} %\n")

print("─── CONTROLES POSITIFS, REPRIS A L IDENTIQUE ───")
ok1 = all(R[k]["prot"] > 1 for k in R)
print(f"  1. protection > 1 partout ? " + " · ".join(f"{k} {R[k]['prot']:.2f}" for k in R) + " → " + ("✓ PASSE" if ok1 else "⛔ TOMBE — capteur muet"))
ok2 = all(R[k]["mc"] >= 30 and R[k]["ml"] >= 30 for k in R)
for k in R: print(f"  2. {k} : {R[k]['mc']} morts sur le couvert · {R[k]['ml']} hors")
print("     → " + ("✓ PASSE" if ok2 else "⛔ TOMBE — un groupe sous 30 morts"))

print("\n─── HYPOTHESE B : LA VALEUR DU COUVERT ───")
r = R["GYMNASE"]["prot"]/max(R["ARMA"]["prot"],1e-9)
print(f"  protection gymnase / Arma = {r:.2f}")
if not (ok1 and ok2): print("  ⚠️ LECTURE NON ADMISSIBLE — un controle est tombe.")
elif r > 2:   print("  ⇒ le GYMNASE SUR-PROTEGE. L agent a appris un abri qui ne tient pas sur Arma. B RETENUE.")
elif r < 0.5: print("  ⇒ Arma protege plus. B refutee dans l autre sens.")
else:         print("  ⇒ les deux couverts protegent PAREIL. B REFUTEE.")
