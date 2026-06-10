"""duel_ammo — DUEL direct : escouade RARETE vs escouade ABONDANCE dans la MEME bataille (env rarete=40).
3 rotations de sieges (la rarete occupe chaque camp une fois, abondance les 2 autres) pour annuler
l asymetrie de spawn. Verdict = part de victoires de la rarete vs l attendu 1/3."""
import torch, torch.nn as nn
from koth_gpu import KothGPU
NAMES = ["blu", "opf", "ind"]

class Net(nn.Module):
    def __init__(self, O, nact, hidden=512, layers=3):
        super().__init__(); body = []; din = O
        for _ in range(layers): body += [nn.Linear(din, hidden), nn.ReLU()]; din = hidden
        self.body = nn.Sequential(*body); self.pi = nn.Linear(hidden, nact); self.v = nn.Linear(hidden, 1)
    def a_logits(self, obs): return self.pi(self.body(obs))

def load(tag, seat, O, dev):
    n = Net(O, 4).to(dev)
    n.load_state_dict(torch.load(f"/home/younes/arma3-marl/{tag}_{NAMES[seat]}.pt", map_location=dev)); n.eval()
    return n

def run_rotation(rare_seat, envs=8192, steps=360, dev="cuda:0"):
    env = KothGPU(num_envs=envs, ammo=True, ammo_max=40.0, device=dev, seed=777 + rare_seat)
    O = env.obs_dim
    nets = [load("kothammo_rare" if c == rare_seat else "kothammo_abond", c, O, dev) for c in range(3)]
    ot = list(env.reset()); wins = torch.zeros(3, device=dev); dec = torch.zeros((), device=dev)
    with torch.no_grad():
        for t in range(steps):
            acts = [nets[c].a_logits(ot[c]).argmax(-1) for c in range(3)]
            ot_, rew, done, info = env.step(acts); ot = list(ot_)
            dm = done.bool() & info["decided"]
            for c in range(3): wins[c] += ((info["winner"] == c) & dm).sum()
            dec += dm.sum()
    return wins, dec

tot_rare, tot_abond, tot_dec = 0.0, 0.0, 0.0
for seat in range(3):
    wins, dec = run_rotation(seat)
    r = wins[seat].item(); a = wins.sum().item() - r; d = dec.item()
    tot_rare += r; tot_abond += a; tot_dec += d
    print(f"rotation siege={seat} : RARETE {r/max(1,d):.3f} | ABONDANCE (moy/2 sieges) {a/2/max(1,d):.3f} | n={int(d)} batailles decidees")
print()
print(f"TOTAL ({int(tot_dec)} batailles) : part RARETE = {tot_rare/max(1,tot_dec):.3f} (attendu si egal : 0.333)")
print(f"                    part ABONDANCE par siege = {tot_abond/2/max(1,tot_dec):.3f}")
