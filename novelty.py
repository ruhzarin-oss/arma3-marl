#!/usr/bin/env python3
"""novelty.py — DÉTECTEUR DE NOUVEAUTÉ. Mesure la distance COMPORTEMENTALE entre le prof scripté
(LAMBS distillé) et SHAMAL appris. L'Elo dit qui est plus fort ; ceci dit si le comportement est NEUF.
Sortie : distance globale + LES features qui changent le plus (= la tactique inventée)."""
import numpy as np, torch, math, sys
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from shamal_teacher import shamal_action
DEV = "cuda:0"; MAP = "/home/younes/arma3-marl/replica_athens.npz"; N = 512


def mkenv(sd):
    return AssaultTerrain(num_envs=N, A=9, D=6, R_spawn=115.0, relief=40.0, hit=0.10, shell_obs=True,
                          team_obs=True, suffer=True, postures=True, hull=True, replica=True,
                          replica_path=MAP, max_steps=60, device=DEV, seed=sd)


@torch.no_grad()
def profile(pol, name):
    """Roule la politique, agrege un VECTEUR de comportement (histogramme d'actions + stats tactiques)."""
    e = mkenv(7); o = e.reset(); NA = e.n_actions
    act_hist = torch.zeros(NA, device=DEV); expo = 0.0; dist = 0.0; spread = 0.0; steps = 0
    for _ in range(60):
        a = pol(e, o)                                        # (N,A)
        act_hist += torch.bincount(a.reshape(-1), minlength=NA).float()
        o, r, d, info = e.step(a, auto_reset=False)
        al = e._aalive().float()
        expo += info["exposed"].mean().item()
        dist += ((torch.sqrt(e.apx ** 2 + e.apy ** 2) * al).sum() / al.sum().clamp(min=1) / e.scale).item()
        dx = e.apx.unsqueeze(1) - e.apx.unsqueeze(2); dy = e.apy.unsqueeze(1) - e.apy.unsqueeze(2)
        spread += (torch.sqrt(dx ** 2 + dy ** 2).mean() / e.scale).item()
        steps += 1
    act_frac = (act_hist / act_hist.sum()).cpu().numpy()
    feats = np.concatenate([act_frac, [expo / steps, dist / steps, spread / steps]])
    names = ["a%d" % i for i in range(NA)] + ["exposition", "dist_objectif", "etalement"]
    print("[%s] fait" % name, flush=True)
    return feats, names


def pol_teacher(e, o): return shamal_action(e)
def make_net_pol(net):
    def p(e, o): return net.a_logits(o).argmax(-1)
    return p


probe = mkenv(0); O, NA = probe.obs_dim, probe.n_actions; del probe
net = Net(O, NA, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/arma3-marl/shamal_win.pt", map_location=DEV)); net.eval()

fT, names = profile(pol_teacher, "prof LAMBS")
fS, _ = profile(make_net_pol(net), "SHAMAL appris")

# normaliser (echelle par feature) pour une distance juste
sd = np.maximum(np.abs(fT), 1e-6)
dist_glob = float(np.sqrt(((fS - fT) / sd) ** 2).mean())
delta = (fS - fT)
order = np.argsort(-np.abs(delta / sd))

print("\n=== DISTANCE COMPORTEMENTALE prof -> SHAMAL : %.3f ===" % dist_glob)
print("  (0 = identique ; plus haut = plus NEUF)")
print("\n  CE QUI CHANGE LE PLUS (= la tactique inventee) :")
for i in order[:6]:
    print("    %-14s : prof %.3f -> SHAMAL %.3f   (%+.3f)" % (names[i], fT[i], fS[i], delta[i]))
