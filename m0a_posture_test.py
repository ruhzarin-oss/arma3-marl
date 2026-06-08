"""M0a — TEST : une posture écrite à la main change-t-elle le comportement en jeu (sim koth_gpu) ?
Exécuteurs GELÉS (league_learner.pt). On assigne une posture stratégique par camp (biais de logits) et on
mesure la divergence : distribution d'actions, distance moyenne à la colline, part de victoires.
DONE si camp 'prendre_colline' avance/se rapproche/gagne nettement plus que camp 'defendre'."""
import torch
from torch.distributions import Categorical
from koth_gpu import KothGPU, posture_bias
from train_koth_gpu import Net

DEV = "cuda:0"
N = 8192
T = 120
POSTURE_BY_CAMP = ["defendre", "prendre_colline", "neutre"]   # camp0, camp1, camp2
ACTS = ["HOLD", "AVANCER", "SUPPRESS", "COUVERT"]

env = KothGPU(num_envs=N, device=DEV)                          # omniscient par défaut : la démo posture n'a pas besoin du brouillard
O, NA = env.obs_dim, env.n_actions
net = Net(O, NA, 512, 3).to(DEV)
net.load_state_dict(torch.load("league_learner.pt", map_location=DEV)); net.eval()
bias = [posture_bias(p, DEV) for p in POSTURE_BY_CAMP]

ot = list(env.reset())
act_hist = torch.zeros(3, 4, device=DEV)
dist_sum = torch.zeros(3, device=DEV); steps = 0
wins = torch.zeros(3, device=DEV); n_done = 0
with torch.no_grad():
    for t in range(T):
        acts = []
        for c in range(3):
            lg = net.a_logits(ot[c]) + bias[c]
            a = Categorical(logits=lg).sample()
            act_hist[c] += torch.bincount(a.reshape(-1), minlength=4).float()
            acts.append(a)
            dist_sum[c] += env._dist(c).mean()
        steps += 1
        ot2, rew, done, info = env.step(acts)
        dm = done.bool() if torch.is_tensor(done) else torch.as_tensor(done, device=DEV).bool()
        w = info["winner"]
        for c in range(3):
            wins[c] += ((w == c) & dm).sum()
        n_done += int(dm.sum())
        ot = list(ot2)

print("=== M0a — posture humaine -> comportement (exécuteurs GELÉS, %d envs, %d pas) ===" % (N, T))
print("%-16s | %-28s | dist.moy | part victoires" % ("posture (camp)", "actions HOLD/AV/SUP/COUV %"))
tot_w = wins.sum().clamp(min=1)
for c in range(3):
    h = act_hist[c] / act_hist[c].sum() * 100
    print("%-16s | %5.1f %5.1f %5.1f %5.1f       |  %6.3f  |  %5.1f%%"
          % (POSTURE_BY_CAMP[c], h[0], h[1], h[2], h[3], (dist_sum[c] / steps).item(), 100 * wins[c].item() / tot_w.item()))
print("\nLecture : 'defendre' doit HOLD plus + rester LOIN (dist haute) ; 'prendre_colline' doit AVANCER plus + se rapprocher (dist basse) + gagner plus.")
print("parties terminées: %d" % n_done)
