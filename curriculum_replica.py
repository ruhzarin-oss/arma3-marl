"""curriculum_replica v2 — paliers FINS (intermediaire 100m/8) + plus de generations/palier
+ metrique PARTIELLE (% defenseurs tues, pas juste tout-nettoye). Avance sur le partiel (signal dense).
Meme carte (replique), TA PBT + TON curriculum. args: P K maxgens A NE"""
import sys, time
import torch
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
P = int(sys.argv[1]) if len(sys.argv) > 1 else 6
K = int(sys.argv[2]) if len(sys.argv) > 2 else 8
MAXG = int(sys.argv[3]) if len(sys.argv) > 3 else 6
A = int(sys.argv[4]) if len(sys.argv) > 4 else 20
NE = int(sys.argv[5]) if len(sys.argv) > 5 else 512
NEVAL, THR_PART = NE, 0.60
PALIERS = [(30, 2), (55, 4), (80, 6), (100, 8), (115, 10)]   # + intermediaire 100m/8


def mkenv(n, sd, Rsp, D):
    return AssaultTerrain(num_envs=n, A=A, D=D, R_spawn=float(Rsp), relief=40.0, hit=0.10,
                          shell_obs=True, team_obs=True, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)


@torch.no_grad()
def eval_pf(net, env, steps=70):
    obs = env.reset(); full = part = 0.0; nep = 0; done_once = torch.zeros(env.N, dtype=torch.bool, device=DEV)
    for t in range(steps):
        act = net.a_logits(obs).argmax(-1)
        obs, _, done, info = env.step(act, auto_reset=False); dm = done.bool() & ~done_once
        if dm.any():
            full += info["neutralized"][dm].float().sum().item()
            part += info["dkilled"][dm].float().sum().item(); nep += int(dm.sum())
        done_once |= done.bool()
    return full / max(nep, 1), part / max(nep, 1)


e0 = mkenv(8, 1, 30, 2); O, NA = e0.obs_dim, e0.n_actions
nets = [Net(O, NA, 512, 3).to(DEV) for _ in range(P)]
opts = [torch.optim.Adam(n.parameters(), 3e-4) for n in nets]
print("===== CURRICULUM v2 (paliers fins + partiel) | A=%d, P=%d, %d paliers =====" % (A, P, len(PALIERS)), flush=True)
t0 = time.time(); last = (0.0, 0.0)
for pi, (Rsp, D) in enumerate(PALIERS):
    envs = [mkenv(NE, 300 + pi * 10 + s, Rsp, D) for s in range(P)]; ev = mkenv(NEVAL, 7 + pi, Rsp, D)
    obs = [e.reset() for e in envs]
    print("--- PALIER %d/%d : depart %d m, garnison %d ---" % (pi + 1, len(PALIERS), Rsp, D), flush=True)
    for gen in range(MAXG):
        for p in range(P):
            obs[p] = ppo_iters(nets[p], opts[p], envs[p], obs[p], K, O)
        res = [eval_pf(nets[p], ev) for p in range(P)]; fitp = [r[1] for r in res]; fitf = [r[0] for r in res]
        order = sorted(range(P), key=lambda p: fitp[p], reverse=True); b = order[0]
        print("   gen %d | meilleur: %.0f%% def. tues (tout-nettoye %.0f%%) | %.0fs" %
              (gen, 100 * fitp[b], 100 * fitf[b], time.time() - t0), flush=True)
        if fitp[b] >= THR_PART:
            print("   -> PALIER %d MAITRISE (%.0f%% tues), on durcit" % (pi + 1, 100 * fitp[b]), flush=True); break
        nt = max(1, P // 3)
        for j in range(nt):
            lo, wi = order[-1 - j], order[j]; nets[lo].load_state_dict(nets[wi].state_dict())
            with torch.no_grad():
                for pr in nets[lo].parameters():
                    pr.add_(torch.randn_like(pr) * 0.03)
            opts[lo] = torch.optim.Adam(nets[lo].parameters(), 3e-4); obs[lo] = envs[lo].reset()
    res = [eval_pf(nets[p], ev) for p in range(P)]; b = max(range(P), key=lambda p: res[p][1]); last = res[b]
    torch.save(nets[b].state_dict(), "/home/younes/arma3-marl/squad_curr2_A%d.pt" % A)
    print("   [palier %d] meilleur = %.0f%% tues / %.0f%% tout-nettoye -> squad_curr2_A%d.pt" % (pi + 1, 100 * last[1], 100 * last[0], A), flush=True)
    del envs, ev; torch.cuda.empty_cache()
print("\n>>> CURRICULUM v2 fini. COMPLEXE ENTIER (20v10) : %.0f%% def. tues / %.0f%% tout-nettoye" % (100 * last[1], 100 * last[0]), flush=True)
print("CURRICULUM FINI", flush=True)
