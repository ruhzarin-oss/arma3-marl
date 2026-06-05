"""train_vs_scripted — ÉTAPE B : un camp RL (camp 0) apprend CONTRE deux camps SCRIPTÉS (baseline fixe).
Métrique propre : RL_winrate (camp 0 gagne la partie à 3) — hasard = 0.33 ; s'il MONTE au-dessus, le RL apprend.
On regarde aussi niv RL vs niv scripté : si le RL monte plus haut, il a appris à EXPLOITER l'économie (se battre/tenir → plus fort)."""
import time, argparse, torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net, ppo_mb


def train(iters=150, envs=16384, n=12, rollout=16, lr=3e-4, gamma=.99, gae=.95, clip=.2,
          epochs=4, vf=.5, ent=.01, hidden=512, layers=3, mb=131072, seed=0, save="vs_scripted"):
    dev = "cuda:0"; cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = KothGPU(num_envs=envs, n=n, device=dev, seed=seed)
    C, A, O, NA = env.C, env.A, env.obs_dim, env.n_actions; obs = env.reset(); N = envs; T = rollout
    learner = Net(O, NA, hidden, layers).to(dev); opt = torch.optim.Adam(learner.parameters(), lr=lr)
    ot = list(obs)
    win_s = torch.zeros((), device=dev); done_s = torch.zeros((), device=dev); dec_s = torch.zeros((), device=dev)
    t0 = time.time(); gstep = 0
    print("RL(camp0) vs SCRIPTÉ(camps1,2) | envs=%d n=%d net=%dx%d | hasard=0.33" % (N, n, layers, hidden), flush=True)
    for it in range(iters):
        B = dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                 logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                 val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev))
        for t in range(T):
            with torch.no_grad():
                dd = Categorical(logits=learner.a_logits(ot[0])); a0 = dd.sample()
                B["obs"][t] = ot[0]; B["act"][t] = a0; B["logp"][t] = dd.log_prob(a0); B["val"][t] = learner.value(ot[0])
            sc = env.scripted_acts()                      # actions scriptées (on garde camps 1,2)
            nobs, rews, done, info = env.step([a0, sc[1], sc[2]])
            B["rew"][t] = rews[0]; B["done"][t] = done
            dm = done.bool(); winner = info["winner"]; dec = winner >= 0
            done_s += dm.sum(); dec_s += (dec & dm).sum(); win_s += ((winner == 0) & dm).sum()
            ot = list(nobs); gstep += N
        with torch.no_grad():
            lv = learner.value(ot[0])
        ppo_mb(learner, opt, B, lv, cfg, dev, mb)
        if it % 10 == 0 or it == iters - 1:
            ds = done_s.item(); dc = dec_s.item()
            print("it %3d | RL_winrate %.2f | décidé %.2f | niv RL/scripté %.2f/%.2f | tier RL/scripté %.2f/%.2f | %.0f tr/s"
                  % (it, (win_s.item() / dc if dc else 0), (dc / ds if ds else 0),
                     env.level[0].mean().item(), env.level[1:].mean().item(),
                     env.tier[0].mean().item(), env.tier[1:].mean().item(),
                     gstep / (time.time() - t0)), flush=True)
            win_s.zero_(); done_s.zero_(); dec_s.zero_()
    print("[fini] modèle -> %s_learner.pt" % save, flush=True)
    torch.save(learner.state_dict(), "/home/younes/arma3-marl/%s_learner.pt" % save)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=150); p.add_argument("--envs", type=int, default=16384)
    p.add_argument("--n", type=int, default=12); p.add_argument("--hidden", type=int, default=512)
    p.add_argument("--layers", type=int, default=3); p.add_argument("--mb", type=int, default=131072)
    p.add_argument("--seed", type=int, default=0); p.add_argument("--save", type=str, default="vs_scripted")
    a = p.parse_args()
    train(iters=a.iters, envs=a.envs, n=a.n, hidden=a.hidden, layers=a.layers, mb=a.mb, seed=a.seed, save=a.save)
