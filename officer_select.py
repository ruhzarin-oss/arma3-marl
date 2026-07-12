"""officer_select — LE COEUR : l'OFFICIER lit le terrain et CHOISIT l'axe d'approche (defile = exposition min),
l'EQUIPE EMERGENTE (assault_grid.pt, qui sait deja se battre a 46%) EXECUTE. Zero reentrainement.
Test : officier-qui-choisit (adaptatif) vs axe au hasard vs pire axe. La plus-value de l'officier = le CHOIX."""
import math
import torch
from train_koth_gpu import Net
from assault_terrain import AssaultTerrain
import terrain_gpu as TG
dev = "cuda:0"
K = 8


def exposure_by_bearing(env):
    """Pour chaque env et chaque cap d'approche : exposition du trajet (fraction vue par un defenseur). (N,K)."""
    N, R = env.N, env.R_spawn; expo = torch.zeros(N, K, device=dev); ts = torch.linspace(0, 1, 12, device=dev)
    for k in range(K):
        th = k * 2 * math.pi / K; sx = R * math.sin(th); sy = R * math.cos(th)
        px = (sx * (1 - ts))[None].expand(N, 12); py = (sy * (1 - ts))[None].expand(N, 12)
        seen = torch.zeros(N, 12, device=dev)
        for di in range(env.D):
            bx = env.dpx[:, di:di + 1].expand(N, 12); by = env.dpy[:, di:di + 1].expand(N, 12)
            seen = torch.maximum(seen, TG.los_clear(env.hm, px, py, bx, by, env.terr_R))
        expo[:, k] = seen.mean(1)
    return expo


def place_at(env, kbear):
    """Re-place l'escouade au cap kbear (terrain + defenseurs inchanges), reset de l'episode."""
    th = kbear.float() * 2 * math.pi / K; sx = env.R_spawn * torch.sin(th); sy = env.R_spawn * torch.cos(th)
    ar = torch.arange(env.A, device=dev).float()
    env.apx = sx[:, None] + (ar % 2) * 6 - 3; env.apy = sy[:, None] + (ar - 1) * 6
    env.admg.zero_(); env.t.zero_(); env.last_supp.zero_(); env._prev_dk.zero_()
    env.prev_d = torch.sqrt(env.apx ** 2 + env.apy ** 2).mean(1) / env.scale


def run(net, choice, N=4096, steps=60, seed=9):
    env = AssaultTerrain(num_envs=N, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=seed)
    env.reset()
    expo = exposure_by_bearing(env)
    if choice == "officier":   kb = expo.argmin(1)        # OFFICIER : meilleur axe (defile)
    elif choice == "pire":     kb = expo.argmax(1)        # pire axe (a decouvert)
    else:                      kb = torch.randint(0, K, (N,), device=dev)   # hasard (pas d'officier)
    place_at(env, kb); obs = env._obs()
    neut = wipe = loss = 0.0; nep = 0
    for _ in range(steps):
        with torch.no_grad():
            a = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
        obs, _, done, info = env.step(a, auto_reset=False); dm = done.bool()
        if dm.any():
            neut += info["neutralized"][dm].float().sum().item(); wipe += info["wiped"][dm].float().sum().item()
            loss += info["losses"][dm].sum().item(); nep += int(dm.sum())
    # episodes non termines (timeout non capte par done==max_steps ? done inclut timeout) -> nep couvre tout a steps>=max
    return neut / max(nep, 1), loss / max(nep, 1), nep


if __name__ == "__main__":
    env0 = AssaultTerrain(num_envs=8, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=0)
    net = Net(env0.obs_dim, env0.n_actions, 256, 3).to(dev)
    net.load_state_dict(torch.load("assault_grid.pt", map_location=dev)); net.eval()
    print("OFFICIER-SELECTEUR : il choisit l'axe d'approche, l'equipe emergente execute :")
    for ch in ["officier", "hasard", "pire"]:
        n, l, ne = run(net, ch)
        lbl = {"officier": "OFFICIER (defile)", "hasard": "hasard (pas d'officier)", "pire": "pire axe (decouvert)"}[ch]
        print("  %-26s : neutralise %3.0f%% | pertes %3.0f%% (%d ep)" % (lbl, 100 * n, 100 * l, ne))
