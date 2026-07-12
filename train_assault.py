"""train_assault — G-perc-0 : entraine un attaquant PPO sur assault_terrain, AVEC perception du terrain
vs AVEUGLE (on masque pente/couvert/LOS, indices 5-7). Verdict : percevoir le terrain augmente-t-il les
objectifs atteints / baisse-t-il les pertes ? Reutilise Net + ppo_mb (train_koth_gpu). 100% GPU."""
import argparse, time
import torch
from torch.distributions import Categorical
from train_koth_gpu import Net, ppo_mb
from assault_terrain import AssaultTerrain

PERC_IDX = [5, 6, 7]   # pente, dist_couvert, LOS = la perception du terrain (masquee en mode aveugle)


def mask(o, perceive):
    if perceive:
        return o
    o = o.clone(); o[..., PERC_IDX] = 0.0; return o


def train(perceive, iters=200, envs=8192, rollout=16, lr=3e-4, gamma=0.99, gae=0.95, clip=0.2,
          epochs=4, vf=0.5, ent=0.01, hidden=256, layers=3, mb=65536, relief=40.0, hit=0.10, seed=0):
    dev = "cuda:0"; cfg = dict(gamma=gamma, gae=gae, clip=clip, epochs=epochs, vf=vf, ent=ent)
    env = AssaultTerrain(num_envs=envs, relief=relief, hit=hit, device=dev, seed=seed)
    A, O, NA, N, T = env.A, env.obs_dim, env.n_actions, envs, rollout
    net = Net(O, NA, hidden, layers).to(dev); opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env.reset()
    reach = torch.zeros((), device=dev); wipe = torch.zeros((), device=dev); nep = torch.zeros((), device=dev); losss = torch.zeros((), device=dev)
    t0 = time.time(); gstep = 0; last = 0.0
    tag = "PERCEPTION" if perceive else "AVEUGLE   "
    print("=== ENTRAINEMENT %s | envs=%d relief=%.0f net=%dx%d ===" % (tag, N, relief, layers, hidden), flush=True)
    for it in range(iters):
        B = dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                 logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                 val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev))
        for t in range(T):
            mo = mask(obs, perceive)
            with torch.no_grad():
                dd = Categorical(logits=net.a_logits(mo)); a = dd.sample()
                B["obs"][t] = mo; B["act"][t] = a; B["logp"][t] = dd.log_prob(a); B["val"][t] = net.value(mo)
            obs, rew, done, info = env.step(a)
            B["rew"][t] = rew; B["done"][t] = done
            dm = done.bool()
            if dm.any():
                reach += info["neutralized"][dm].float().sum(); wipe += info["wiped"][dm].float().sum()
                losss += info["losses"][dm].sum(); nep += dm.sum()
            gstep += N
        with torch.no_grad():
            lv = net.value(mask(obs, perceive))
        ppo_mb(net, opt, B, lv, cfg, dev, mb)
        if it % 20 == 0 or it == iters - 1:
            ne = nep.item()
            last = reach.item() / ne if ne else 0.0
            print("  it %3d | defenseurs neutralises %.0f%% | aneanti %.0f%% | pertes %.0f%% | %.0f tr/s"
                  % (it, 100 * last, 100 * wipe.item() / max(ne, 1), 100 * losss.item() / max(ne, 1), gstep / (time.time() - t0)), flush=True)
            reach.zero_(); wipe.zero_(); nep.zero_(); losss.zero_()
    torch.save(net.state_dict(), "/home/younes/arma3-marl/assault_%s.pt" % ("perc" if perceive else "blind"))
    return last


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=200); p.add_argument("--envs", type=int, default=8192)
    p.add_argument("--relief", type=float, default=40.0); p.add_argument("--hit", type=float, default=0.10); p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    rp = train(True, iters=a.iters, envs=a.envs, relief=a.relief, hit=a.hit, seed=a.seed)
    rb = train(False, iters=a.iters, envs=a.envs, relief=a.relief, hit=a.hit, seed=a.seed)
    print("\n===== VERDICT G-perc-0 =====")
    print("defenseurs neutralises final : PERCEPTION %.0f%% | AVEUGLE %.0f%% | ecart %+.0f pts" % (100 * rp, 100 * rb, 100 * (rp - rb)))
    print(">>> %s" % ("LA PERCEPTION PAIE -> G-perc-0 FRANCHIE" if rp - rb >= 0.10 else
          "ecart faible -> perception marginale (a creuser : tache/obs)"))
    print("GPERC0 FINI")
