"""run_scripted_koth — étape A : valider les MÉCANIQUES (économie/niveaux/équipement) à grande échelle,
TOUT scripté (aucun apprentissage). On regarde si le jeu TOURNE : niveaux qui montent, argent qui circule,
matchs décisifs, durée raisonnable, et le SNOWBALL (le vainqueur est-il juste celui qui a le plus haut niveau ?)."""
import time, argparse, torch
from koth_gpu import KothGPU

p = argparse.ArgumentParser()
p.add_argument("--envs", type=int, default=5714)   # 5714 x 3 x 35 = ~600 000 agents
p.add_argument("--n", type=int, default=35)
p.add_argument("--steps", type=int, default=300)
p.add_argument("--base_money", type=float, default=0.6); p.add_argument("--base_xp", type=float, default=0.3)
p.add_argument("--k_money", type=float, default=8.0); p.add_argument("--k_xp", type=float, default=6.0)
p.add_argument("--zone_money", type=float, default=2.0)
a = p.parse_args()

dev = "cuda:0"
env = KothGPU(num_envs=a.envs, n=a.n, device=dev, seed=0,
              base_money=a.base_money, base_xp=a.base_xp, k_money=a.k_money, k_xp=a.k_xp, zone_money=a.zone_money)
tot = a.envs * env.C * a.n
print("KOTH SCRIPTÉ | envs=%d x %d camps x %d agents = %d agents | econ=%s | secure_r=%g cap_need=%d rot=%d"
      % (a.envs, env.C, a.n, tot, env.econ, env.secure_r, env.cap_need, env.rot_period), flush=True)
env.reset()
t0 = time.time(); gstep = 0
done_s = torch.zeros((), device=dev); dec_s = torch.zeros((), device=dev)
mlen_s = torch.zeros((), device=dev); mlen_n = torch.zeros((), device=dev)
snow_w = torch.zeros((), device=dev); snow_l = torch.zeros((), device=dev); snow_n = torch.zeros((), device=dev)

for it in range(a.steps):
    acts = env.scripted_acts()
    obs, rew, done, info = env.step(acts, auto_reset=False)   # pas d'auto-reset : on lit l'état de fin de match
    dm = done.bool(); winner = info["winner"]; dec = (winner >= 0) & dm
    done_s += dm.sum(); dec_s += dec.sum()
    if dm.any():
        mlen_s += env.t[dm].float().sum(); mlen_n += dm.sum()
    if dec.any():
        idx = dec.nonzero(as_tuple=True)[0]; w = winner[idx]
        lm = env.tier.mean(2)[:, idx]                        # (C, k) TIER moyen par camp (le vrai différenciateur)
        wl = lm.gather(0, w.view(1, -1)).squeeze(0)          # tier du vainqueur
        ll = (lm.sum(0) - wl) / (env.C - 1)                  # tier moyen des perdants
        snow_w += wl.sum(); snow_l += ll.sum(); snow_n += idx.numel()
    env._reset_rows(dm.nonzero(as_tuple=True)[0])            # reset manuel des parties finies
    gstep += env.N
    if it % 20 == 0 or it == a.steps - 1:
        ds = done_s.item(); dc = dec_s.item(); mn = mlen_n.item(); sn = snow_n.item()
        print("it %3d | niv.moy %.2f | tier.moy %.2f | argent.moy %.1f | décisif %.2f | durée %.1f pas | tier V/P %.2f/%.2f | %.0f tr/s | %.1fGo"
              % (it, info["lvl"].item(), info["tier"].item(), info["money"].item(),
                 (dc / ds if ds else 0), (mlen_s.item() / mn if mn else 0),
                 (snow_w.item() / sn if sn else 0), (snow_l.item() / sn if sn else 0),
                 gstep / (time.time() - t0), torch.cuda.max_memory_allocated() / 1e9), flush=True)
        done_s.zero_(); dec_s.zero_(); mlen_s.zero_(); mlen_n.zero_(); snow_w.zero_(); snow_l.zero_(); snow_n.zero_()
print("[fini] %.0f tr/s moyen" % (gstep / (time.time() - t0)), flush=True)
