"""Porte ECO : BLU CMDP selon sa strategie eco (adversaires = renforts fixe). 
A jamais depenser | B toujours renforts | D oracle etat-aware (renforts si abime, investir si sur+riche, sinon garder).
D > B nettement => decision eco state-dependante => porte OUVERTE => officier-eco / RL-LLM justifie."""
import torch
from koth_eco import KothEco
from train_koth_gpu import Net

DEV = "cuda:0"; N = 4096; T = 420; ECO_EVERY = 15; LAM = 0.5
rl = Net(10, 4, 512, 3).to(DEV); rl.load_state_dict(torch.load("league_maneuver_learner.pt", map_location=DEV)); rl.eval()


def eco_blu(mode, env):
    if mode == "A": return torch.zeros(env.N, dtype=torch.long, device=DEV)
    if mode == "B": return torch.ones(env.N, dtype=torch.long, device=DEV)
    alive = env._alive(0).float().mean(1)           # frac vivants BLU
    inh = env.in_hill(0) > 0; rich = env.cash[0] >= env.E_COST
    act = torch.zeros(env.N, dtype=torch.long, device=DEV)        # garder
    act = torch.where(inh & rich, torch.full_like(act, 2), act)   # sur+riche -> investir
    act = torch.where(alive < 0.6, torch.ones_like(act), act)     # abime -> renforts (prioritaire)
    return act


@torch.no_grad()
def run(mode):
    env = KothEco(num_envs=N, device=DEV, seed=0); ot = list(env.reset())
    opp = torch.ones(env.N, dtype=torch.long, device=DEV)         # adversaires : renforts fixe
    for t in range(T):
        if t % ECO_EVERY == 0:
            env.eco_step([eco_blu(mode, env), opp, opp])
        acts = [torch.distributions.Categorical(logits=rl.a_logits(ot[c])).sample() for c in range(env.C)]
        ot, _, done, info = env.step(acts); ot = list(ot)
    tot = sum(env.ctrl_time[c].mean() for c in range(env.C)) + 1e-6
    cs = float(env.ctrl_time[0].mean() / tot); ls = 1 - float(env._alive(0).float().mean())
    return cs, ls, cs - LAM * ls


print("=== PORTE ECO — BLU (adversaires renforts fixe) ===", flush=True)
for m, lab in (("A", "A jamais depenser"), ("B", "B toujours renforts"), ("D", "D oracle etat-aware")):
    cs, ls, cm = run(m)
    print("%-22s | controle %.3f | pertes %.3f | CMDP %.3f" % (lab, cs, ls, cm), flush=True)
print("\nD > B nettement => la decision eco depend de la situation => porte OUVERTE => RL-LLM justifie.", flush=True)
