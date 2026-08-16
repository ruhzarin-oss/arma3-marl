"""retrain — la politique reapprend dans le monde OPERE (couvert directionnel).
Un seul changement, un seul retrain ⟨Fable⟩. Criteres dans DEPOT_CHIRURGIE_COUVERT.md."""
import sys, time, torch, numpy as np
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from monde_fidele import MONDE_OPERE
B.CFG = MONDE_OPERE                      # ── L OPERATION EST ALLUMEE ──
print(f"  monde : couvert_directionnel = {B.CFG.get('couvert_directionnel')}", flush=True)
t0 = time.time()
pol = B.entrainer(iters=140)
print(f"  entraine en {(time.time()-t0)/60:.1f} min", flush=True)
torch.save(pol.state_dict(), "/home/younes/arma3-marl/boucle_pol_opere.pt")
print("  sauve : boucle_pol_opere.pt", flush=True)
# lecture sur graines held-out, dans le monde OPERE
res, met = B.evaluer(pol, B.GRAINES_TEST, n=256)
for k in res: print(f"  {k:<10} {np.mean(res[k]):5.1f} %   ({np.mean(met[k]):5.1f} m)", flush=True)
