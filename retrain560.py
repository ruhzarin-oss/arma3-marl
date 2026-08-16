import sys, time, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from monde_fidele import MONDE_OPERE
B.CFG = MONDE_OPERE
print(f"  monde OPERE · budget 560 iterations (x4)", flush=True)
t0 = time.time()
pol = B.entrainer(iters=560)
print(f"  entraine en {(time.time()-t0)/60:.1f} min", flush=True)
torch.save(pol.state_dict(), "/home/younes/arma3-marl/boucle_pol_opere_560.pt")
res, met = B.evaluer(pol, B.GRAINES_TEST, n=256)
print("\n  ─── LECTURE SUR GRAINES HELD-OUT, MONDE OPERE ───", flush=True)
for k in res: print(f"    {k:<10} {np.mean(res[k]):5.1f} %   ({np.mean(met[k]):5.1f} m)", flush=True)
print(f"\n  (a 140 iterations : appris 4,3 · frontal 4,4 · flanc 25,0)", flush=True)
