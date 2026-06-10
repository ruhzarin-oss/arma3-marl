"""Mesure la PORTE sur le jeu enrichi (faction faible aleatoire) : BLU CMDP selon la strategie.
A neutre | B rang-oracle (leader->defendre sinon prendre) | D etat-riche-oracle (lit QUI est faible).
Si D > B nettement -> lire l'etat aide -> porte OUVERTE -> l'officier/RL-LLM a un vrai job."""
import torch
from koth_enriched import KothEnriched
from koth_gpu import POSTURES
from train_koth_gpu import Net

DEV = "cuda:0"; N = 4096; T = 200; LAM = 0.5
rl = Net(10, 4, 512, 3).to(DEV); rl.load_state_dict(torch.load("league_maneuver_learner.pt", map_location=DEV)); rl.eval()
P = {k: torch.tensor(POSTURES[k], device=DEV, dtype=torch.float32) for k in POSTURES}


def bias_blu(mode, env, ctrl):
    rank0 = (1 + (ctrl > ctrl[0]).sum(0)).unsqueeze(-1)        # (N,1)
    if mode == "A":
        return P["neutre"].expand(env.N, 4)
    base = torch.where(rank0 == 1, P["defendre"], P["prendre_colline"])    # rang-oracle
    if mode == "B":
        return base
    wf = env.weak_faction.unsqueeze(-1)                        # (N,1)
    out = torch.where((wf == 1) | (wf == 2), P["prendre_colline"], base)   # ennemi faible -> exploiter
    out = torch.where(wf == 0, P["defendre"], out)                          # BLU faible -> defendre
    return out


@torch.no_grad()
def run(mode):
    env = KothEnriched(num_envs=N, device=DEV, weak_p=0.7, seed=0); ot = list(env.reset())
    for _ in range(T):
        ctrl = torch.stack([env.ctrl_time[c] for c in range(env.C)], 0)
        b0 = bias_blu(mode, env, ctrl)
        acts = []
        for c in range(env.C):
            lg = rl.a_logits(ot[c])
            if c == 0:
                lg = lg + b0.unsqueeze(1)
            acts.append(torch.distributions.Categorical(logits=lg).sample())
        ot, _, done, info = env.step(acts); ot = list(ot)
    tot = sum(env.ctrl_time[c].mean() for c in range(env.C)) + 1e-6
    cs = float(env.ctrl_time[0].mean() / tot); ls = 1 - float(env._alive(0).float().mean())
    return cs, ls, cs - LAM * ls


print("=== PORTE ENRICHIE (faction faible aleatoire) — BLU ===", flush=True)
for m, lab in (("A", "A neutre"), ("B", "B rang-oracle"), ("D", "D etat-riche-oracle")):
    cs, ls, cm = run(m)
    print("%-22s | controle %.3f | pertes %.3f | CMDP %.3f" % (lab, cs, ls, cm), flush=True)
print("\nD > B nettement => lire l'etat (qui est faible) AIDE => porte OUVERTE => officier/RL-LLM justifie.", flush=True)
