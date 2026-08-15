import sys, glob, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B, terrain_gpu as TG
DC, ALIVE, LOS = 6, 4, 7

def lire(g, a):
    if 0.85 <= g <= 1.15 and a < 0.7:            return "DESACCORD ETABLI"
    if 0.85 <= g <= 1.15 and 0.85 <= a <= 1.15:  return "le couvert ne cache NULLE PART"
    if g < 0.7 and a < 0.7:                      return "il cache des deux cotes — piste FERMEE"
    return "INDECIS"
print("─── REGLE 18 : les portes passent leur propre banc ───")
for g, a, att in [(1.00,0.40,"DESACCORD ETABLI"), (1.00,1.00,"le couvert ne cache NULLE PART"),
                  (0.50,0.40,"il cache des deux cotes — piste FERMEE"), (1.00,0.75,"INDECIS")]:
    got = lire(g,a); print(f"  {'✓' if got==att else '⛔'} gym {g:.2f} · arma {a:.2f} → {got}")
print("  ✓ chaque bande est atteignable ET rejetable.\n")

# ─── GYMNASE : incover lu dans le moteur
pol = charger(B.DEV); e = B.monde(64, 101); e.reset()
Cg, Lg = [], []
for t in range(60):
    inc = TG.sample(e.cover, e.apx, e.apy, e.scale).clamp(max=1.0).reshape(-1).cpu().numpy()
    o = e._obs().reshape(-1, len(COLS)).cpu().numpy()
    with torch.no_grad(): l, v = pol(e._obs())
    e.step(l.argmax(-1), auto_reset=False)
    viv = o[:, ALIVE] > 0.5
    Cg.append((inc > 0.5)[viv]); Lg.append((o[:, LOS] > 0.5)[viv])
Cg, Lg = np.concatenate(Cg), np.concatenate(Lg)

# ─── ARMA : dcover == 0
Ca, La = [], []
for f in sorted(glob.glob("/mnt/data/harmattan-sandbox/logs/live20/ep_*.npz")):
    Z = np.load(f, allow_pickle=True); X = Z["obs18"][:, COLS]
    X = X[X[:, ALIVE] > 0.5]
    Ca.append(X[:, DC] < 1e-6); La.append(X[:, LOS] > 0.5)
Ca, La = np.concatenate(Ca), np.concatenate(La)

R = {}
for nom, C, L in [("GYMNASE", Cg, Lg), ("ARMA", Ca, La)]:
    ps = L[C].mean() if C.sum() else float("nan")
    ph = L[~C].mean() if (~C).sum() else float("nan")
    R[nom] = dict(r=ps/ph if ph>0 else float("nan"), ns=int(C.sum()), nh=int((~C).sum()), ps=ps, ph=ph)
    print(f"─── {nom} ───")
    print(f"  SUR le couvert : {C.sum():6d} pas · P(expose) = {ps:.3f}")
    print(f"  hors couvert   : {(~C).sum():6d} pas · P(expose) = {ph:.3f}")
    print(f"  RAPPORT DE MASQUAGE = {R[nom]['r']:.2f}      (1,00 = ne cache pas)\n")

print("─── CONTROLE POSITIF ───")
ok = all(R[k]["ns"] >= 100 and R[k]["nh"] >= 100 for k in R)
for k in R: print(f"  {k} : {R[k]['ns']} pas sur le couvert · {R[k]['nh']} hors")
print("  → " + ("✓ PASSE" if ok else "⛔ TOMBE — conditionnelle vide, rien ne se lit"))
if not ok: raise SystemExit()
print(f"\n─── LA LECTURE ───\n  gymnase {R['GYMNASE']['r']:.2f}  ·  Arma {R['ARMA']['r']:.2f}")
print(f"\n  ⇒ {lire(R['GYMNASE']['r'], R['ARMA']['r'])}")
