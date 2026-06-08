"""train_league_gpu — LIGUE (PSRO/PFSP) sur GPU, KotH 3 camps ASYMETRIQUE.
Corrige le CYCLING : le learner s'entraine contre une POPULATION de versions figees (pas seulement les dernieres).
PFSP : on tire en priorite les adversaires qui BATTENT le learner (entrainement sur ses faiblesses).
learner = camp 0 ; camps 1 et 2 = adversaires tires du vivier. Asymetrie de spawn -> parties decisives -> robustesse mesurable.
Metrique-reine : learner_vs_pool (taux de victoire contre tout le vivier) doit MONTER puis RESTER haut (cycle dompte)."""
import time, argparse, copy
import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net, ppo_mb


def clone_frozen(net, dev):
    f = copy.deepcopy(net).to(dev)
    for p in f.parameters():
        p.requires_grad_(False)
    f.eval(); return f


def train(iters=400, envs=16384, rollout=16, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2, epochs=4,
          vf=0.5, ent=0.01, hidden=512, layers=3, mb=131072, snap_every=15, pfsp_p=2.0,
          hit=0.15, kappa=0.12, tie_pen=0.12, spawn_jit=0.25, seed=0, save="league", n=3, sight=1e9, attrition_win=True, secure_n=2, cap_need=6, timeout_decisive=False):
    dev = "cuda:0"; cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = KothGPU(num_envs=envs, n=n, hit=hit, kappa=kappa, tie_pen=tie_pen, spawn_jit=spawn_jit, sight=sight, attrition_win=attrition_win, secure_n=secure_n, cap_need=cap_need, timeout_decisive=timeout_decisive, device=dev, seed=seed)
    C, A, O, NA = env.C, env.A, env.obs_dim, env.n_actions; obs = env.reset(); N = envs; T = rollout
    learner = Net(O, NA, hidden, layers).to(dev); opt = torch.optim.Adam(learner.parameters(), lr=lr)
    pool = [clone_frozen(Net(O, NA, hidden, layers).to(dev), dev) for _ in range(2)]
    CAP = 512; wins_p = torch.zeros(CAP, device=dev); games_p = torch.zeros(CAP, device=dev)
    ot = list(obs)
    win_s = torch.zeros((), device=dev); draw_s = torch.zeros((), device=dev); dec_s = torch.zeros((), device=dev); done_s = torch.zeros((), device=dev)
    gstep = 0; t0 = time.time()
    print("LIGUE | dev=%s envs=%d net=%dx%d | snap_every=%d pfsp_p=%.1f spawn_jit=%.2f" % (dev, N, layers, hidden, snap_every, pfsp_p, spawn_jit), flush=True)
    for it in range(iters):
        P = len(pool)
        wr = torch.where(games_p[:P] > 0, wins_p[:P] / games_p[:P].clamp(min=1), torch.full((P,), 0.5, device=dev))
        w = ((1 - wr).clamp(min=0.02)) ** pfsp_p; w = w / w.sum()
        assign1 = torch.multinomial(w, N, replacement=True); assign2 = torch.multinomial(w, N, replacement=True)
        B = dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                 logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                 val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev))
        for t in range(T):
            with torch.no_grad():
                dd = Categorical(logits=learner.a_logits(ot[0])); a0 = dd.sample()
                B["obs"][t] = ot[0]; B["act"][t] = a0; B["logp"][t] = dd.log_prob(a0); B["val"][t] = learner.value(ot[0])
                a1 = torch.zeros(N, A, dtype=torch.long, device=dev); a2 = torch.zeros(N, A, dtype=torch.long, device=dev)
                for p in torch.unique(assign1).tolist():
                    m = assign1 == p; a1[m] = Categorical(logits=pool[p].a_logits(ot[1][m])).sample()
                for p in torch.unique(assign2).tolist():
                    m = assign2 == p; a2[m] = Categorical(logits=pool[p].a_logits(ot[2][m])).sample()
            nobs, rews, done, info = env.step([a0, a1, a2])
            B["rew"][t] = rews[0]; B["done"][t] = done
            dm = done.bool(); winner = info["winner"]; dec = winner >= 0
            lw = (winner == 0) & dm; draw = dm & (~dec)
            done_s += dm.sum(); dec_s += (dec & dm).sum(); win_s += lw.sum(); draw_s += draw.sum()
            for assign in (assign1, assign2):
                games_p[:P].scatter_add_(0, assign, (dec & dm).float())
                wins_p[:P].scatter_add_(0, assign, lw.float())
            ot = list(nobs); gstep += N
        with torch.no_grad():
            lv = learner.value(ot[0])
        ppo_mb(learner, opt, B, lv, cfg, dev, mb)
        if (it + 1) % snap_every == 0:
            pool.append(clone_frozen(learner, dev))
        if it % 10 == 0 or it == iters - 1:
            ds = done_s.item(); dc = dec_s.item()
            print("it %4d | pop=%d | learner_vs_pool %.2f | nuls %.2f | decid %.2f | %.0f tr/s | GPUmem %.1fGo"
                  % (it, len(pool), (win_s.item() / dc if dc else 0), (draw_s.item() / ds if ds else 0),
                     (dc / ds if ds else 0), gstep / (time.time() - t0), torch.cuda.max_memory_allocated() / 1e9), flush=True)
            win_s.zero_(); draw_s.zero_(); dec_s.zero_(); done_s.zero_()
    print("[fini] pop=%d | %.0f tr/s" % (len(pool), gstep / (time.time() - t0)), flush=True)
    torch.save(learner.state_dict(), "/home/younes/arma3-marl/%s_learner.pt" % save)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=400); p.add_argument("--envs", type=int, default=16384)
    p.add_argument("--rollout", type=int, default=16); p.add_argument("--hidden", type=int, default=512)
    p.add_argument("--layers", type=int, default=3); p.add_argument("--mb", type=int, default=131072)
    p.add_argument("--snap_every", type=int, default=15); p.add_argument("--pfsp_p", type=float, default=2.0)
    p.add_argument("--hit", type=float, default=0.15); p.add_argument("--kappa", type=float, default=0.12)
    p.add_argument("--tie_pen", type=float, default=0.12); p.add_argument("--spawn_jit", type=float, default=0.25)
    p.add_argument("--seed", type=int, default=0); p.add_argument("--save", type=str, default="league")
    p.add_argument("--n", type=int, default=3); p.add_argument("--sight", type=float, default=1e9)
    p.add_argument("--no_attrition", action="store_true")   # mode manœuvre : tuer tout le monde ≠ gagner
    p.add_argument("--secure_n", type=int, default=2); p.add_argument("--cap_need", type=int, default=6)
    p.add_argument("--timeout_decisive", action="store_true")   # à l'expiration, le plus de temps-zone gagne (brise les nuls)
    a = p.parse_args()
    train(iters=a.iters, envs=a.envs, rollout=a.rollout, hidden=a.hidden, layers=a.layers, mb=a.mb,
          snap_every=a.snap_every, pfsp_p=a.pfsp_p, hit=a.hit, kappa=a.kappa, tie_pen=a.tie_pen,
          spawn_jit=a.spawn_jit, seed=a.seed, save=a.save, n=a.n, sight=a.sight, attrition_win=not a.no_attrition,
          secure_n=a.secure_n, cap_need=a.cap_need, timeout_decisive=a.timeout_decisive)
