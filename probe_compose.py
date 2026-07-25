"""BRIQUE 1 — verif de la couture : les 2 skills gelés tournent dans le MEME env otage.
d6 lit env._obs() (29) ; soldier_shell lit env.B._obs() (22). Meme espace d'action (10)."""
import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"

env = HostageEnv(num_envs=1024, A=9, D=6, device=DEV, seed=0); env.ff_hit = 0.0; env.exfil_hit = 0.0
o29 = env._obs(); o22 = env.B._obs()
print("d6 obs", tuple(o29.shape), "| couvert obs", tuple(o22.shape), flush=True)
assert o29.shape[-1] == 29 and o22.shape[-1] == 22, "couture KO"

d6 = Net(29, 10, 512, 3).to(DEV); d6.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_v1_FINAL.pt", map_location=DEV)); d6.eval()
sh = Net(22, 10, 512, 3).to(DEV); sh.load_state_dict(torch.load("/home/younes/compose-embodiment/soldier_shell.pt", map_location=DEV)); sh.eval()
print("d6 et soldier_shell charges OK", flush=True)


def run(skill, D=6):
    e = HostageEnv(num_envs=1024, A=9, D=D, device=DEV, seed=7); e.ff_hit = 0.0; e.exfil_hit = 0.0
    e.reset(); succ = nep = wipe = 0; sup = mov = steps = 0.0
    for _ in range(160):
        with torch.no_grad():
            logits = d6.a_logits(e._obs()) if skill == "d6" else sh.a_logits(e.B._obs())
            a = torch.distributions.Categorical(logits=logits).sample()
        sup += (a == 9).float().mean().item(); mov += (a < 8).float().mean().item(); steps += 1
        _, _, dn, info = e.step(a); dm = dn.bool()
        if dm.any():
            succ += info["success"][dm].float().sum().item(); wipe += info["squad_wipe"][dm].float().sum().item(); nep += int(dm.sum())
    print("%-13s | rescousse %.0f%% | aneantie %.0f%% | suppress %.2f | bouge %.2f" % (
        skill, 100 * succ / max(nep, 1), 100 * wipe / max(nep, 1), sup / steps, mov / steps), flush=True)


print("--- comportement de chaque skill seul dans HostageEnv (D=6) ---", flush=True)
run("d6"); run("soldier_shell")
print("BRIQUE1 OK", flush=True)
