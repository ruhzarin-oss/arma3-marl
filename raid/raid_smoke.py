#!/usr/bin/env python3
"""raid_smoke.py — ASSAUT SCRIPTE TEMOIN (valide la Brique 0 : l'env Arma-dans-la-boucle tourne).
Politique triviale : SF i assigne au sous-objectif (i % 10), avance dessus a chaque pas.
But : prouver que reset/step/obs/reward/done fonctionnent et que la bataille se deroule sur Arma reel.
PAS d'apprentissage ici -- c'est le banc de validation de l'environnement."""
import sys
sys.path.insert(0, "/home/younes/arma3-marl/raid")
from raid_env import RaidEnv, N_SF, N_SUBOBJ

def main():
    env = RaidEnv(slot=2)
    obs = env.reset()
    if obs is None: print("RESET ECHEC", flush=True); return
    print("[smoke] reset ok : %d SF vivants, alerte=%.1f" % (obs["n_alive"], obs["alert"]), flush=True)
    total = 0.0; info = {}
    for t in range(50):
        targets = [env.subobj[i % N_SUBOBJ] for i in range(N_SF)]      # chacun fonce sur son sous-obj
        obs, r, done, info = env.step(targets)
        total += r
        print("[pas %2d] tenus=%2d/%d  vivants=%2d/%d  alerte=%.1f  def=%2d  qrf=%s  r=%+.1f%s" % (
            t + 1, info.get("held", 0), N_SUBOBJ, info.get("alive", 0), N_SF, info.get("alert", 0),
            info.get("def", 0), "OUI" if info.get("qrf") else "non", r,
            "   >>> " + info["result"] if info.get("result") else ""), flush=True)
        if done: break
    print("\n=== BILAN RAID (scripte) ===", flush=True)
    print("resultat=%s  sous-objectifs tenus=%d/%d  SF survivants=%d/%d  recompense totale=%.1f" % (
        info.get("result", "?"), info.get("held", 0), N_SUBOBJ, info.get("alive", 0), N_SF, total), flush=True)
    print("RAID_SMOKE_DONE", flush=True)
    env.close()

if __name__ == "__main__":
    main()
