"""Option 2 — brancher le trainer MARL sur ArmaSquadEnv et faire UN pas de gradient sur des
données Arma. (Smoke : valide la chaîne ; le vrai entraînement se fait sur le toy, vite, puis
fine-tune ici. Arma est trop lent pour entraîner beaucoup en direct.)"""
import numpy as np, torch, torch.nn as nn
from arma_env import ArmaSquadEnv
from train_harmattan import ActorCritic

dev = "cuda:0" if torch.cuda.is_available() else "cpu"
env = ArmaSquadEnv(opfor=2)
net = ActorCritic(env.obs_dim, env.n_actions, env.n, 64).to(dev)
opt = torch.optim.Adam(net.parameters(), lr=3e-4)
print("Politique branchee : obs=%d -> %d actions x %d agents | device %s" % (env.obs_dim, env.n_actions, env.n, dev))

T = 8
obs = env.reset()
bo, ba, br = [], [], []
for t in range(T):
    o = torch.tensor(obs, dtype=torch.float32, device=dev).unsqueeze(0)  # (1,n,od)
    with torch.no_grad():
        a, _ = net.act(o)
    acts = a[0].cpu().numpy()
    nobs, r, c, d, info = env.step(acts)
    bo.append(torch.tensor(obs, dtype=torch.float32, device=dev)); ba.append(a[0]); br.append(r - 0.5 * c)
    print("  pas %d | actions %s | r %.2f | pertes %d | vivants %d" % (t + 1, list(int(x) for x in acts), r, c, info["alive"]))
    obs = env.reset() if d else nobs

# Un pas A2C/PPO sur les donnees ARMA collectees
O = torch.stack(bo)            # (T,n,od)
A = torch.stack(ba)            # (T,n)
rew = torch.tensor(br, dtype=torch.float32, device=dev)
gamma = 0.99; G = torch.zeros_like(rew); acc = 0.0
for t in reversed(range(T)): acc = rew[t] + gamma * acc; G[t] = acc
G = (G - G.mean()) / (G.std() + 1e-8)
newlogp, ent = net.evaluate(O, A)        # (T,n)
V = net.value(O)                          # (T,)
adv = (G - V.detach())
ploss = -(newlogp * adv.unsqueeze(1)).mean()
vloss = ((V - G) ** 2).mean()
loss = ploss + 0.5 * vloss - 0.01 * ent.mean()
opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
print("MISE A JOUR DE GRADIENT EFFECTUEE sur donnees Arma | perte=%.4f" % float(loss))
print("OK chaine RL branchee sur Arma (option 2 validee)")
