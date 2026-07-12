"""train_viz — entrainement PPO (terrain + grille, le setup +37) qui ALIMENTE un dashboard d'entrainement :
 - staff/train_metrics.json : la courbe (neutralise % / pertes % par iteration) en direct
 - staff/train_replay.json  : un episode-echantillon (terrain + positions agents/defenseurs par pas) tous les K iters
Pour la these : on regarde la politique apprendre + le comportement emerger, et on enregistre."""
import json, time, os, argparse
import numpy as np
import torch
from torch.distributions import Categorical
from train_koth_gpu import Net, ppo_mb
from assault_terrain import AssaultTerrain
dev = "cuda:0"; STAFF = "/home/younes/arma3-marl/staff"; os.makedirs(STAFF, exist_ok=True)


def eval_replay(net, it, steps=55):
    e = AssaultTerrain(num_envs=1, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=777)
    obs = e.reset()
    G = 36
    hm = e.hm[0].detach().float()
    ds = torch.nn.functional.interpolate(hm[None, None], size=(G, G), mode="bilinear", align_corners=False)[0, 0]
    hmin, hmax = float(ds.min()), float(ds.max())
    terr = (((ds - hmin) / (hmax - hmin + 1e-6)) * 100).round().int().cpu().tolist()
    frames = []
    for t in range(steps):
        with torch.no_grad():
            a = net.a_logits(obs).argmax(-1)
        obs, _, done, info = e.step(a, auto_reset=False)
        frames.append({
            "ag": [[round(float(e.apx[0, i]), 1), round(float(e.apy[0, i]), 1), int(e.admg[0, i] < e.dmg_dead)] for i in range(e.A)],
            "df": [[round(float(e.dpx[0, j]), 1), round(float(e.dpy[0, j]), 1), int(e.ddmg[0, j] < e.dmg_dead)] for j in range(e.D)],
        })
        if bool(done[0]):
            break
    json.dump({"iter": it, "R": float(e.terr_R), "G": G, "terr": terr, "frames": frames}, open(STAFF + "/train_replay.json", "w"))


def train(iters, envs, K):
    cfg = dict(gamma=0.99, gae=0.95, clip=0.2, epochs=4, vf=0.5, ent=0.01)
    env = AssaultTerrain(num_envs=envs, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=0)
    A, O, NA, N, T = env.A, env.obs_dim, env.n_actions, envs, 16
    net = Net(O, NA, 256, 3).to(dev); opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    obs = env.reset(); hist = []; t0 = time.time(); gstep = 0
    for it in range(iters):
        B = dict(obs=torch.zeros(T, N, A, O, device=dev), act=torch.zeros(T, N, A, dtype=torch.long, device=dev),
                 logp=torch.zeros(T, N, A, device=dev), rew=torch.zeros(T, N, device=dev),
                 val=torch.zeros(T, N, device=dev), done=torch.zeros(T, N, device=dev))
        reach = nep = loss = rew_sum = 0.0
        for t in range(T):
            with torch.no_grad():
                dd = Categorical(logits=net.a_logits(obs)); a = dd.sample()
                B["obs"][t] = obs; B["act"][t] = a; B["logp"][t] = dd.log_prob(a); B["val"][t] = net.value(obs)
            obs, r, done, info = env.step(a); B["rew"][t] = r; B["done"][t] = done
            rew_sum += float(r.mean()); dm = done.bool()
            if dm.any():
                reach += float(info["neutralized"][dm].float().sum()); loss += float(info["losses"][dm].sum()); nep += int(dm.sum())
            gstep += N
        with torch.no_grad():
            lv = net.value(obs)
        ppo_mb(net, opt, B, lv, cfg, dev, 65536)
        neu = (reach / nep) if nep else 0.0; per = (loss / nep) if nep else 0.0
        hist.append({"it": it, "neu": round(100 * neu, 1), "per": round(100 * per, 1), "rew": round(rew_sum / T, 3),
                     "trs": round(gstep / (time.time() - t0))})
        json.dump({"title": "Entrainement : combat collaboratif sur terrain (grille +37)", "iters": iters, "hist": hist}, open(STAFF + "/train_metrics.json", "w"))
        if it % K == 0 or it == iters - 1:
            eval_replay(net, it)
            print("it %3d | neutralise %4.1f%% | pertes %4.1f%% | %s tr/s" % (it, 100 * neu, 100 * per, hist[-1]["trs"]), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/assault_viz.pt")
    print("TRAIN VIZ FINI", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--iters", type=int, default=220); p.add_argument("--envs", type=int, default=4096); p.add_argument("--K", type=int, default=8)
    a = p.parse_args(); train(a.iters, a.envs, a.K)
