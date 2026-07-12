"""train_grid — G-perc-1 : la GRILLE locale (contexte spatial : disposition du couvert autour de l'agent)
bat-elle les VARIABLES au POINT (G-perc-0) ? Memes tache (victoire par le feu) et reseau (MLP), seule l'obs
change. Si la grille gagne -> le contexte spatial aide -> on passe au Perceiver. Reutilise Net + ppo_mb."""
import argparse, time
import torch
from torch.distributions import Categorical
from train_koth_gpu import Net, ppo_mb
from assault_terrain import AssaultTerrain


def train(grid, iters=300, envs=4096, rollout=16, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2,
          epochs=4, vf=0.5, ent=0.01, hidden=256, layers=3, mb=65536, relief=40.0, hit=0.15, seed=0):
    dev = "cuda:0"; cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = AssaultTerrain(num_envs=envs, relief=relief, hit=hit, grid_obs=grid, device=dev, seed=seed)
    A, O, NA, N, T = env.A, env.obs_dim, env.n_actions, envs, rollout
    net = Net(O, NA, hidden, layers).to(dev); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env.reset()
    reach = torch.zeros((), device=dev); nep = torch.zeros((), device=dev); losss = torch.zeros((), device=dev); last = 0.0
    t0 = time.time(); gstep = 0
    print("=== %s | obs_dim=%d envs=%d ===" % ("GRILLE" if grid else "POINT ", O, N), flush=True)
    for it in range(iters):
        B = dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                 logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                 val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev))
        for t in range(T):
            with torch.no_grad():
                dd = Categorical(logits=net.a_logits(obs)); a = dd.sample()
                B["obs"][t] = obs; B["act"][t] = a; B["logp"][t] = dd.log_prob(a); B["val"][t] = net.value(obs)
            obs, rew, done, info = env.step(a); B["rew"][t] = rew; B["done"][t] = done
            dm = done.bool()
            if dm.any():
                reach += info["neutralized"][dm].float().sum(); losss += info["losses"][dm].sum(); nep += dm.sum()
            gstep += N
        with torch.no_grad():
            lv = net.value(obs)
        ppo_mb(net, opt, B, lv, cfg, dev, mb)
        if it % 50 == 0 or it == iters - 1:
            ne = nep.item(); last = reach.item() / ne if ne else 0.0
            print("  it %3d | neutralises %.0f%% | pertes %.0f%% | %.0f tr/s"
                  % (it, 100 * last, 100 * losss.item() / max(ne, 1), gstep / (time.time() - t0)), flush=True)
            reach.zero_(); nep.zero_(); losss.zero_()
    torch.save(net.state_dict(), "/home/younes/arma3-marl/assault_%s.pt" % ("grid" if grid else "point"))
    return last


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=300); p.add_argument("--envs", type=int, default=4096); p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    rg = train(True, iters=a.iters, envs=a.envs, seed=a.seed)
    rp = train(False, iters=a.iters, envs=a.envs, seed=a.seed)
    print("\n===== VERDICT G-perc-1 =====")
    print("neutralises final : GRILLE %.0f%% | POINT %.0f%% | ecart %+.0f pts" % (100 * rg, 100 * rp, 100 * (rg - rp)))
    print(">>> %s" % ("LA GRILLE BAT LE POINT -> contexte spatial utile (passer au Perceiver/CNN)" if rg - rp >= 0.08 else
          "grille ~ point -> contexte spatial peu utile au-dela des variables"))
    print("GPERC1 FINI")
