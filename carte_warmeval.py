"""EVAL ZERO-SHOT — le commandant DEJA ENTRAINE (commander_k4_d8.pt, ~48%) evalue tel quel :
OFF (verite-terrain, son monde d'entrainement) vs ON (carte brouillard) pour plusieurs T d'oubli.
Mesure DIRECTE du cout du brouillard sur un commandant competent. Aucune entrainement -> minutes.
"""
import sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from commander_env import CommanderEnv
DEV = "cuda:0"; A, K, D, MAXT = 8, 4, 8, 120
CKPT = "/home/younes/compose-embodiment/commander_k4_d8.pt"


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)

    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


def evalrun(net, kw, envs=2048, steps=16, seed=999):
    e = CommanderEnv(envs, A=A, K=K, D=D, device=DEV, seed=seed, max_steps=MAXT, **kw)
    obs = e.reset(); sec = neu = surv = nep = 0
    with torch.no_grad():
        for _ in range(steps):
            mu, _ = net(obs); a = mu.view(envs, K, 2)
            obs, rew, done, info = e.step(a)
            if done.any():
                dm = done
                sec += info["secured"][dm].float().sum().item(); neu += info["neut"][dm].float().sum().item()
                surv += (info["alive"] / A)[dm].sum().item(); nep += int(dm.sum()); e.reset_done(dm)
    return 100 * sec / max(nep, 1), 100 * neu / max(nep, 1), 100 * surv / max(nep, 1)


probe = CommanderEnv(2, A=A, K=K, D=D, device=DEV, seed=0, max_steps=MAXT)
net = CNet(probe.obs_dim, probe.act_dim, 256).to(DEV)
net.load_state_dict(torch.load(CKPT, map_location=DEV)); net.eval()
print("=== EVAL ZERO-SHOT du commandant entraine (D=%d) — verite vs brouillard ===" % D, flush=True)
off = evalrun(net, dict(use_carte=False))
print("  OFF verite-terrain : secu %3.0f%% | neut %3.0f%% | surv %3.0f%%  (son monde d'entrainement)" % off, flush=True)
print("  --- ON carte brouillard, zero-shot (jamais vu de fog a l'entrainement) ---", flush=True)
best = None
for T in [24.0, 12.0, 6.0, 3.0]:
    on = evalrun(net, dict(use_carte=True, carte_T=T))
    print("  ON  T=%-4g        : secu %3.0f%% | neut %3.0f%% | surv %3.0f%%  | fog tax %+.0f pts" % (T, on[0], on[1], on[2], on[0] - off[0]), flush=True)
    if best is None or on[0] > best[1][0]: best = (T, on)
print("  -> brouillard le mieux tolere : T=%g (secu %.0f%%, tax %+.0f pts)" % (best[0], best[1][0], best[1][0] - off[0]), flush=True)
print("  NB : zero-shot = borne BASSE. Un fine-tune ON recupere une partie du tax.", flush=True)
