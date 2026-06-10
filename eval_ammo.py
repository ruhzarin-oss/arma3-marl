"""eval_ammo — compare deux escouades (abondance vs rarete) DANS l env de rarete (munitions=40).
Mesure l ingeniosite EMERGENTE : discipline de tir (munitions, % a sec), usage du couvert (recharge),
rapprochement (distance d engagement), survie, controle. Politique deterministe (argmax)."""
import argparse, torch, torch.nn as nn
from koth_gpu import KothGPU
NAMES = ["BLU", "OPF", "IND"]

class Net(nn.Module):
    def __init__(self, O, nact, hidden=512, layers=3):
        super().__init__(); body = []; din = O
        for _ in range(layers): body += [nn.Linear(din, hidden), nn.ReLU()]; din = hidden
        self.body = nn.Sequential(*body); self.pi = nn.Linear(hidden, nact); self.v = nn.Linear(hidden, 1)
    def a_logits(self, obs): return self.pi(self.body(obs))

def load_squad(tag, O, dev):
    nets = []
    for c in range(3):
        n = Net(O, 4).to(dev)
        n.load_state_dict(torch.load("/home/younes/arma3-marl/%s_%s.pt" % (tag, NAMES[c].lower()), map_location=dev))
        n.eval(); nets.append(n)
    return nets

def mean_engage(env):
    tot = 0.0; nn_ = 0; BIG = torch.tensor(1e18, device=env.dev)
    for s in range(env.C):
        others = env._others(s)
        epx = torch.cat([env.px[o] for o in others], 1); epy = torch.cat([env.py[o] for o in others], 1)
        eal = torch.cat([env._alive(o) for o in others], 1)
        ex = epx.unsqueeze(1) - env.px[s].unsqueeze(2); ey = epy.unsqueeze(1) - env.py[s].unsqueeze(2)
        ed2 = torch.where(eal.unsqueeze(1), ex * ex + ey * ey, BIG)
        nd = torch.sqrt(ed2.min(2).values); al = env._alive(s)
        if al.any(): tot += nd[al].mean().item(); nn_ += 1
    return tot / max(1, nn_)

def evaluate(tag, envs=8192, steps=120, ammo_max=40.0, dev="cuda:0"):
    env = KothGPU(num_envs=envs, ammo=True, ammo_max=ammo_max, device=dev, seed=123)
    O = env.obs_dim; nets = load_squad(tag, O, dev); ot = list(env.reset()); C = env.C
    acc = dict(ammo=0.0, dry=0.0, hold=0.0, avanc=0.0, supp=0.0, couvert=0.0, eng=0.0, alive=0.0, occ=0.0)
    n = 0
    with torch.no_grad():
        for t in range(steps):
            acts = [nets[c].a_logits(ot[c]).argmax(-1) for c in range(C)]
            for c in range(C):
                acc["hold"] += (acts[c] == 0).float().mean().item() / C
                acc["avanc"] += (acts[c] == 1).float().mean().item() / C
                acc["supp"] += (acts[c] == 2).float().mean().item() / C
                acc["couvert"] += (acts[c] == 3).float().mean().item() / C
            acc["ammo"] += env.ammo.mean().item()
            acc["dry"] += (env.ammo <= 0).float().mean().item()
            acc["alive"] += torch.stack([env._alive(c).float().mean() for c in range(C)]).mean().item()
            acc["eng"] += mean_engage(env)
            ot_, rew, done, info = env.step(acts)
            acc["occ"] += info["occ"].float().mean().item() if torch.is_tensor(info["occ"]) else float(info["occ"])
            ot = list(ot_); n += 1
    for k in acc: acc[k] /= n
    return acc

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--tags", nargs="+", default=["kothammo_abond", "kothammo_rare"])
    p.add_argument("--envs", type=int, default=8192); p.add_argument("--steps", type=int, default=120)
    a = p.parse_args()
    rows = {}
    for tag in a.tags: rows[tag] = evaluate(tag, envs=a.envs, steps=a.steps)
    cols = [("munitions moy", "ammo", "%.1f"), ("%% a sec", "dry", "%.3f"), ("%% COUVERT(recharge)", "couvert", "%.3f"),
            ("%% SUPPRESS", "supp", "%.3f"), ("%% AVANCER", "avanc", "%.3f"), ("dist engagement", "eng", "%.1f"),
            ("survie moy", "alive", "%.3f"), ("controle", "occ", "%.2f")]
    print("\n%-22s | %s" % ("metrique", " | ".join("%-16s" % t for t in a.tags)))
    print("-" * (24 + 20 * len(a.tags)))
    for label, key, fmt in cols:
        print("%-22s | %s" % (label, " | ".join("%-16s" % (fmt % rows[t][key]) for t in a.tags)))
