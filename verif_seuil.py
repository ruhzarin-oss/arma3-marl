import sys, glob, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
from porter_boucle import COLS
DC = 6
A = []
for f in sorted(glob.glob("/mnt/data/harmattan-sandbox/logs/live20/ep_*.npz")):
    Z = np.load(f, allow_pickle=True); X = Z["obs18"][:, COLS]
    A.append(X[X[:, 4] > 0.5])
A = np.concatenate(A)
d = A[:, DC]
print(f"  1/30 exactement       = {1/30:.10f}")
print(f"  mon seuil « a portee »= 0.0330000000")
print(f"  1/30 <= 0.033 ?         {1/30 <= 0.033}   <-- LA QUESTION\n")
print("  valeurs distinctes de dcover et leurs effectifs :")
u, c = np.unique(np.round(d, 6), return_counts=True)
for v, n in list(zip(u, c))[:8]:
    print(f"    {v:.6f}  ({v*30:.0f} cellules)  : {n:5d} pas" + ("   <-- pris par « SUR »" if v < 1e-6 else "   <-- devait etre pris par « a portee »" if abs(v-1/30) < 1e-6 else ""))
print(f"\n  masque « SUR le couvert » (< 1e-6)  : {int((d < 1e-6).sum())} pas")
print(f"  masque « a portee »      (<= 0.033) : {int((d <= 0.033).sum())} pas")
print(f"  masque « a portee » CORRIGE (<= 1/30+eps) : {int((d <= 1/30 + 1e-9).sum())} pas")
print("\n  ⇒ " + ("LES DEUX MASQUES SONT IDENTIQUES — « a portee » n a jamais voulu dire a portee."
      if int((d < 1e-6).sum()) == int((d <= 0.033).sum()) else "les masques different, le verdict tient."))
