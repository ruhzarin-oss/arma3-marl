import sys
sys.path.insert(0, "/home/younes/arma3-marl")
from train_soldier import run

# Mesure l'apport de la perception d'EQUIPE (team_obs) en ESCOUADE (A=4),
# la ou la conscience des coequipiers doit compter (feu + mouvement coordonne).
# Couvert (shell) TOUJOURS ON des deux cotes -> on isole le Δ de team.
I, E = 150, 8192
print("=== SQUAD : apport de team_obs (shell ON partout) ===", flush=True)
best = None
for A, D, hit in [(4, 4, 0.16), (4, 6, 0.16), (4, 6, 0.20)]:
    rs, _ = run(True, I, E, A, D, 40.0, hit, 0, tag="sqb")
    rt, _ = run(True, I, E, A, D, 40.0, hit, 0, tag="sqt", team_obs=True)
    d = 100 * (rt - rs)
    print(">>> A=%d D=%d hit=%.2f : SHELL %.0f%% | +TEAM %.0f%% | Δ team %+.0f"
          % (A, D, hit, 100*rs, 100*rt, d), flush=True)
    if best is None or d > best[0]:
        best = (d, A, D, hit)
print(">>> MEILLEUR Δ team : %+.0f a A=%d D=%d hit=%.2f" % best, flush=True)
print("SQUAD FINI", flush=True)
