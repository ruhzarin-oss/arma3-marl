"""DIAGNOSTIC du plafond ~50% : la politique entrainee identifie-t-elle moins les cibles CAMOUFLEES ?
Et a-t-elle appris a DESCENDRE ? On charge recon.pt, on evalue, on ventile la reco par niveau de couvert
et on regarde l'altitude tenue."""
import sys, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from recon_env import ReconEnv
DEV = "cuda:0"


class CNet(nn.Module):
    def __init__(self, obs, act, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


T = 10; N = 4096
e = ReconEnv(N, T=T, device=DEV, seed=7)
net = CNet(e.obs_dim, e.act_dim, 256).to(DEV)
net.load_state_dict(torch.load("/home/younes/compose-embodiment/recon.pt", map_location=DEV)); net.eval()
obs = e.reset()
# bins de couvert figes a l'episode courant (cibles statiques)
lo = e.tcov < 0.33; mid = (e.tcov >= 0.33) & (e.tcov < 0.66); hi = e.tcov >= 0.66
alt_sum = torch.zeros(N, device=DEV); steps = 0
with torch.no_grad():
    for _ in range(e.maxT):
        mu, _ = net(obs); obs, rew, done, info = e.step(mu)
        alt_sum += e.dz; steps += 1
        # on fige l'analyse sur le 1er episode (avant reset) -> stop au 1er done massif
        if done.float().mean() > 0.5:
            break
rec = e.recog.float()
def frac(mask):
    m = mask.float(); return 100 * (rec * m).sum().item() / m.sum().clamp(min=1).item()
print("=== DIAGNOSTIC recon.pt (T=%d, %d envs, %d pas) ===" % (T, N, steps))
print("  identifie GLOBAL        : %.0f%%" % (100 * rec.mean().item()))
print("  identifie couvert BAS   : %.0f%%  (cibles a decouvert)" % frac(lo))
print("  identifie couvert MOYEN : %.0f%%" % frac(mid))
print("  identifie couvert HAUT  : %.0f%%  (cibles camouflees)" % frac(hi))
print("  altitude moyenne tenue  : %.0f m  (min=%.0f max=%.0f)  -> a-t-il descendu ?"
      % ((alt_sum / steps).mean().item(), e.zmin, e.zmax))
print("  part des cibles en couvert HAUT : %.0f%%" % (100 * hi.float().mean().item()))
