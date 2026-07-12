#!/usr/bin/env python3
# SMOKE-TRAIN etape 3 : prouve que le pipeline d'entrainement tourne bout-en-bout
# avec postures=True sur le Denver corrige. PAS le vrai run (juste 3 blocs PPO).
import sys, time, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
DEV = "cuda:0"
RP = "/home/younes/arma3-marl/replica_denver.npz"

print("=== SMOKE-TRAIN POSTURES (Denver corrige) ===")
env = AssaultTerrain(num_envs=64, A=4, D=2, R_spawn=30, relief=40.0, hit=0.10,
                     shell_obs=True, team_obs=True, replica=True, replica_path=RP,
                     max_steps=60, device=DEV, seed=1, postures=True)
O, NA = env.obs_dim, env.n_actions
print("obs_dim=%d  n_actions=%d  (attendu 29 / 13)" % (O, NA))
assert O == 29 and NA == 13, "TAILLES INATTENDUES"

net = Net(O, NA, 512, 3).to(DEV)
opt = torch.optim.Adam(net.parameters(), 3e-4)
obs = env.reset()
print("reseau construit sur (O=%d, NA=%d). 3 blocs PPO (K=2)..." % (O, NA), flush=True)
t0 = time.time()
for it in range(3):
    obs = ppo_iters(net, opt, env, obs, 2, O)          # 2 updates PPO reels
    print("  bloc %d/3 fait (%.1fs)" % (it + 1, time.time() - t0), flush=True)

finite = all(torch.isfinite(p).all().item() for p in net.parameters())
print("parametres finis (pas de NaN):", finite)

# eval gloutonne : la boucle complete (step + obs + reward) tourne avec postures
o = env.reset(); r_sum = 0.0; dk = 0.0; n = 0; seen = set()
with torch.no_grad():
    for _ in range(40):
        a = net.a_logits(o).argmax(-1)
        seen |= set(a.reshape(-1).tolist())
        o, r, d, info = env.step(a, auto_reset=True)
        r_sum += float(r.mean());
        if d.bool().any(): dk += float(info["dkilled"][d.bool()].sum()); n += int(d.sum())
r_ok = (r_sum == r_sum) and abs(r_sum) < 1e6
print("actions vues (echantillon):", sorted(seen), "| postures 10-12 emises:", any(x in seen for x in (10, 11, 12)))
print("reward moyen cumule (fini):", round(r_sum, 3), "| def. tues/episode:", round(dk / max(n, 1), 2))
ok = finite and r_ok
print("\n=== VERDICT : %s ===" % ("SMOKE-TRAIN OK — pipeline postures pret pour l'Etape 3" if ok else "PROBLEME"))
sys.exit(0 if ok else 1)
