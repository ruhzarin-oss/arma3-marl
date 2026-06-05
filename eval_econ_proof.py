"""eval_econ_proof — PROUVE que l'économie est exploitée / décisive (pas du hand-waving).
P1 (corrélation) : cerveau entraîné (league_econ) vs scriptés → le VAINQUEUR a-t-il plus de tier que le PERDANT ?
P2 (causalité)   : MÊME cerveau dans les 3 camps (comportement identique), mais camp0 démarre tier+3 →
                   s'il gagne > 0.33 (hasard), c'est l'ÉQUIPEMENT qui décide, pas le comportement."""
import torch
from koth_gpu import KothGPU
from train_koth_gpu import Net

dev = "cuda:0"; MODEL = "/home/younes/arma3-marl/league_econ_learner.pt"
import argparse
_p = argparse.ArgumentParser()
_p.add_argument("--tier_dmg", type=float, default=0.25); _p.add_argument("--tier_armor", type=float, default=0.10)
_p.add_argument("--lvl_dmg", type=float, default=0.15); _p.add_argument("--tier_range", type=float, default=0.20)
_p.add_argument("--boost", type=float, default=3.0)
_p.add_argument("--model", type=str, default=MODEL)
_p.add_argument("--model_old", type=str, default="/home/younes/arma3-marl/league_econ_learner.pt")
ARGS = _p.parse_args()
EK = dict(tier_dmg=ARGS.tier_dmg, tier_armor=ARGS.tier_armor, lvl_dmg=ARGS.lvl_dmg, tier_range=ARGS.tier_range)

def load(env, path=None):
    net = Net(env.obs_dim, env.n_actions, 512, 3).to(dev)
    net.load_state_dict(torch.load(path or ARGS.model, map_location=dev)); net.eval(); return net

def act(net, o):
    with torch.no_grad():
        return torch.distributions.Categorical(logits=net.a_logits(o)).sample()

def part1(envs=4096, n=12, steps=400):
    env = KothGPU(num_envs=envs, n=n, econ=True, device=dev, seed=7, **EK); net = load(env); ot = list(env.reset())
    win = torch.zeros((), device=dev); dec = torch.zeros((), device=dev)
    wt = torch.zeros((), device=dev); lt = torch.zeros((), device=dev); tn = torch.zeros((), device=dev)
    for t in range(steps):
        a0 = act(net, ot[0]); sc = env.scripted_acts()
        nobs, r, done, info = env.step([a0, sc[1], sc[2]], auto_reset=False)
        dm = done.bool(); w = info["winner"]; d = (w >= 0) & dm
        dec += d.sum(); win += ((w == 0) & dm).sum()
        if d.any():
            idx = d.nonzero(as_tuple=True)[0]; ww = w[idx]; tm = env.tier.mean(2)[:, idx]
            wtier = tm.gather(0, ww.view(1, -1)).squeeze(0); ltier = (tm.sum(0) - wtier) / (env.C - 1)
            wt += wtier.sum(); lt += ltier.sum(); tn += idx.numel()
        ot = list(nobs); env._reset_rows(dm.nonzero(as_tuple=True)[0])
    print("[P1 CORRÉLATION] RL(entraîné) vs scriptés | RL_winrate %.3f | tier VAINQUEUR %.2f vs PERDANT %.2f  (écart +%.2f)"
          % (win.item() / max(1, dec.item()), wt.item() / max(1, tn.item()), lt.item() / max(1, tn.item()),
             (wt.item() - lt.item()) / max(1, tn.item())), flush=True)

def part2(envs=4096, n=12, steps=400, boost=None):
    boost = ARGS.boost if boost is None else boost
    env = KothGPU(num_envs=envs, n=n, econ=True, device=dev, seed=9, **EK); net = load(env); ot = list(env.reset())
    env.tier[0] += boost
    wc = torch.zeros(3, device=dev); dec = torch.zeros((), device=dev)
    for t in range(steps):
        a = [act(net, ot[c]) for c in range(3)]
        nobs, r, done, info = env.step(a, auto_reset=False)
        dm = done.bool(); w = info["winner"]; d = (w >= 0) & dm
        if d.any():
            for c in range(3): wc[c] += ((w == c) & dm).sum()
            dec += d.sum()
        ridx = dm.nonzero(as_tuple=True)[0]; env._reset_rows(ridx)
        if ridx.numel() > 0: env.tier[0, ridx] += boost   # re-boost camp0 au respawn
        ot = list(nobs)
    fr = (wc / dec.clamp(min=1)).tolist()
    print("[P2 CAUSALITÉ] même cerveau partout, camp0 tier+%g | winrate camp0 %.3f / camp1 %.3f / camp2 %.3f  (hasard 0.33)"
          % (boost, fr[0], fr[1], fr[2]), flush=True)

def part3(envs=4096, n=12, steps=400):
    env = KothGPU(num_envs=envs, n=n, econ=True, device=dev, seed=11, **EK)
    new = load(env, ARGS.model); old = load(env, ARGS.model_old); ot = list(env.reset())
    wc = torch.zeros(3, device=dev); dec = torch.zeros((), device=dev)
    nt = torch.zeros((), device=dev); ot_ = torch.zeros((), device=dev); tn = torch.zeros((), device=dev)
    for t in range(steps):
        a0 = act(new, ot[0]); a1 = act(old, ot[1]); a2 = act(old, ot[2])
        nobs, r, done, info = env.step([a0, a1, a2], auto_reset=False)
        dm = done.bool(); w = info["winner"]; d = (w >= 0) & dm
        if d.any():
            for c in range(3): wc[c] += ((w == c) & dm).sum()
            dec += d.sum(); idx = d.nonzero(as_tuple=True)[0]; tm = env.tier.mean(2)[:, idx]
            nt += tm[0].sum(); ot_ += tm[1:].mean(0).sum(); tn += idx.numel()
        ot = list(nobs); env._reset_rows(dm.nonzero(as_tuple=True)[0])
    fr = (wc / dec.clamp(min=1)).tolist()
    print("[P3 A-T-IL APPRIS] NOUVEAU(camp0) vs ANCIEN(camps1,2) | winrate nouveau %.3f / anciens %.3f,%.3f  (hasard 0.33) | tier nouveau %.2f vs ancien %.2f"
          % (fr[0], fr[1], fr[2], nt.item() / max(1, tn.item()), ot_.item() / max(1, tn.item())), flush=True)

print("=== PREUVE : EST-CE BIEN L'ÉCONOMIE QUI EST EXPLOITÉE / DÉCISIVE ? ===", flush=True)
part1(); part2(); part3()
