"""TEST 1 — composition SCRIPTEE : d6 fait la rescousse ; POST-pickup, les non-porteurs basculent en ESCORTE.
Mesure si l'escorte FERME le trou d'exfil (otage vulnerable exfil_hit>0) vs d6-solo. Pas de chef appris."""
import sys, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
d6 = Net(29, 10, 512, 3).to(DEV); d6.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_v1_FINAL.pt", map_location=DEV)); d6.eval()
esc = Net(29, 10, 512, 3).to(DEV); esc.load_state_dict(torch.load("/home/younes/compose-embodiment/escort.pt", map_location=DEV)); esc.eval()
ar = torch.arange(9, device=DEV)


def run(mode, D=8, envs=4096, steps=170, exf=0.05, seed=123):
    env = HostageEnv(num_envs=envs, A=9, D=D, device=DEV, seed=seed); env.ff_hit = 0.0; env.exfil_hit = exf
    obs = env.reset(); succ = nep = pick = hd = 0
    with torch.no_grad():
        for _ in range(steps):
            env.ff_hit = 0.0; env.exfil_hit = exf
            da = torch.distributions.Categorical(logits=d6.a_logits(obs)).sample()
            if mode == "hybrid":
                ea = torch.distributions.Categorical(logits=esc.a_logits(obs)).sample()
                picked = env.picked > 0.5
                alive = env.B._aalive()
                dist = torch.where(alive, torch.sqrt((env.B.apx - env.hpx[:, None]) ** 2 + (env.B.apy - env.hpy[:, None]) ** 2), torch.full_like(env.B.apx, 1e9))
                carrier = dist.argmin(1)
                is_car = (ar[None] == carrier[:, None])
                use_esc = picked[:, None] & (~is_car)
                act = torch.where(use_esc, ea, da)
            else:
                act = da
            obs, rw, done, info = env.step(act); dm = done.bool()
            if dm.any():
                succ += info["success"][dm].float().sum().item(); pick += info["picked"][dm].float().sum().item()
                hd += info["hdead"][dm].float().sum().item(); nep += int(dm.sum())
    return 100 * succ / max(nep, 1), 100 * pick / max(nep, 1), 100 * hd / max(nep, 1)


for D in [8]:
    for exf in [0.05, 0.10, 0.15]:
        sa = run("solo", D=D, exf=exf); sb = run("hybrid", D=D, exf=exf)
        print("D=%d exfil_hit=%.2f | SOLO  rescousse %.0f%% pickup %.0f%% otage-tue %.0f%%" % (D, exf, sa[0], sa[1], sa[2]), flush=True)
        print("D=%d exfil_hit=%.2f | HYBRIDE rescousse %.0f%% pickup %.0f%% otage-tue %.0f%%  <-- d6+escorte" % (D, exf, sb[0], sb[1], sb[2]), flush=True)
print("EVAL COMPOSE FINI", flush=True)
