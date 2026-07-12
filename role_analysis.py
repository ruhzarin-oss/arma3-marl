"""Couche 2 / mesure-avant-build : la COORDINATION emerge-t-elle deja dans l'equipe grille entrainee ?
On regarde le FEU+MOUVEMENT : par env-pas, l'equipe melange-t-elle suppresseurs (action 9) et manoeuvriers
(caps 0-7), ou tout le monde fait pareil ? + distribution des actions + role par slot."""
import torch
from train_koth_gpu import Net
from assault_terrain import AssaultTerrain
dev = "cuda:0"
env = AssaultTerrain(num_envs=2048, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=5)
net = Net(env.obs_dim, env.n_actions, 256, 3).to(dev)
net.load_state_dict(torch.load("assault_grid.pt", map_location=dev)); net.eval()
obs = env.reset()
act = torch.zeros(env.n_actions, device=dev); mixed = sonly = monly = total = 0
supp_by_slot = torch.zeros(env.A, device=dev); alive_by_slot = torch.zeros(env.A, device=dev)
for _ in range(120):
    with torch.no_grad():
        a = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
    al = env._aalive()
    s = (a == 9) & al; m = (a < 8) & al; nany = al.any(1)
    mixed += (s.any(1) & m.any(1) & nany).sum().item()
    sonly += (s.any(1) & ~m.any(1) & nany).sum().item()
    monly += (~s.any(1) & m.any(1) & nany).sum().item()
    total += nany.sum().item()
    for k in range(env.n_actions): act[k] += ((a == k) & al).sum()
    supp_by_slot += s.float().sum(0); alive_by_slot += al.float().sum(0)
    obs, _, _, _ = env.step(a)
tot = act.sum().item()
print("distribution des actions (agents vivants) :")
for k, nm in enumerate(["cap0", "cap1", "cap2", "cap3", "cap4", "cap5", "cap6", "cap7", "HOLD", "SUPPRESS"]):
    print("  %-9s %4.0f%%" % (nm, 100 * act[k].item() / tot))
print("\nFEU+MOUVEMENT (par env-pas, equipes vivantes) :")
print("  MIXTE (>=1 supprime ET >=1 bouge) : %.0f%%" % (100 * mixed / max(total, 1)))
print("  tous suppriment                   : %.0f%%" % (100 * sonly / max(total, 1)))
print("  tous bougent                      : %.0f%%" % (100 * monly / max(total, 1)))
print("taux de suppression par slot : %s (uniforme = pas de role fixe par slot)"
      % ["%.0f%%" % (100 * supp_by_slot[i].item() / max(alive_by_slot[i].item(), 1)) for i in range(env.A)])
print(">>> %s" % ("FEU+MOUVEMENT EMERGE" if mixed > 0.4 * total else "coordination FAIBLE -> a forcer (obs coequipiers / COMA)"))
