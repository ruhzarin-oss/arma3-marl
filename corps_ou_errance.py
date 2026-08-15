"""Lents parce qu ils BOUGENT MOINS, ou parce qu ils BOUGENT AILLEURS ?
  · deplacement TOTAL par pas  = ce que le corps rend
  · avance NETTE vers l objectif = ce que la decision rend
  · rendement = nette / totale   -> 1,0 = ligne droite, 0 = tourner en rond
"""
import sys, glob, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import charger, COLS
import boucle as B
S = 200.0

def stats_arma():
    tot, net = [], []
    for f in sorted(glob.glob("/mnt/data/harmattan-sandbox/logs/live20/ep_*.npz")):
        Z = np.load(f, allow_pickle=True)
        A = Z["obs18"][:, COLS]; pas = np.asarray(Z["pas"]); u = np.unique(pas)
        P = [A[pas==p][:, :2]*S for p in u]
        for a, b in zip(P[:-1], P[1:]):
            n = min(len(a), len(b))
            if n == 0: continue
            tot.append(np.linalg.norm(b[:n]-a[:n], axis=1).mean())
            net.append((np.linalg.norm(a[:n],axis=1) - np.linalg.norm(b[:n],axis=1)).mean())
    return np.array(tot), np.array(net)

pol = charger(B.DEV); e = B.monde(64, 101)
e.reset(); tg, ng = [], []
for t in range(60):
    px, py = e.apx.clone(), e.apy.clone()
    with torch.no_grad(): l, v = pol(e._obs())
    _, _, done, _ = e.step(l.argmax(-1), auto_reset=False)
    tg.append(float(torch.sqrt((e.apx-px)**2 + (e.apy-py)**2).mean()))
    ng.append(float((torch.sqrt(px**2+py**2) - torch.sqrt(e.apx**2+e.apy**2)).mean()))
    if bool(done.all()): break
ta, na = stats_arma(); tg, ng = np.array(tg), np.array(ng)

print(f"  {'':<10}{'deplacement':>14}{'avance nette':>14}{'rendement':>12}")
for nom, T, N in [("GYMNASE", tg, ng), ("ARMA", ta, na)]:
    r = np.median(N)/max(np.median(T),1e-9)
    print(f"  {nom:<10}{np.median(T):>11.2f} m {np.median(N):>11.2f} m {r:>11.2f}")
print(f"\n  rapport des DEPLACEMENTS  gymnase/Arma : x{np.median(tg)/max(np.median(ta),1e-9):.1f}")
print(f"  rapport des AVANCES NETTES              : x{np.median(ng)/max(np.median(na),1e-9):.1f}")
print("\n─── LA LECTURE ───")
rt = np.median(tg)/max(np.median(ta),1e-9); rn = np.median(ng)/max(np.median(na),1e-9)
if rt > 1.8:
    print(f"  ⇒ LE CORPS. Ils se deplacent x{rt:.1f} moins loin par pas : les actions ne mordent")
    print("     pas sur Arma comme au gymnase. La decision n est pas en cause.")
elif rn > 1.8 and rt < 1.4:
    print(f"  ⇒ L ERRANCE. Ils bougent AUTANT (x{rt:.1f}) mais avancent x{rn:.1f} moins :")
    print("     ils depensent leur mouvement ailleurs que vers l objectif.")
else:
    print(f"  ⇒ LES DEUX, a parts comparables (deplacement x{rt:.1f}, avance x{rn:.1f}).")
