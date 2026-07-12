"""train_replica — ASSAUT EN ESCOUADE sur la replique du complexe Arma (batiments solides).
Equipe (A attaquants, conscience d'equipe = feu+mouvement) vs garnison (D), win-by-fire.
args: iters envs A D"""
import sys
from train_soldier import run
iters = int(sys.argv[1]) if len(sys.argv) > 1 else 300
envs = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
A = int(sys.argv[3]) if len(sys.argv) > 3 else 20
D = int(sys.argv[4]) if len(sys.argv) > 4 else 10
print("===== ASSAUT EN ESCOUADE SUR LA REPLIQUE : %d attaquants vs %d defenseurs (murs solides) =====" % (A, D), flush=True)
rp, lp = run(True, iters, envs, A, D, 40.0, 0.10, 0, tag="squad", replica=True, team_obs=True)
print("\n>>> ESCOUADE final : garnison neutralisee %.0f%% | pertes %.0f%%" % (100 * rp, 100 * lp), flush=True)
print("SQUAD TRAIN FINI", flush=True)
