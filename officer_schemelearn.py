"""officer_schemelearn — SELECTEUR DE SCHEMA APPRIS : un MLP predit, par situation, quel schema
(concentre/pince) gagne, depuis une representation RICHE (exposition des 8 axes + fusils par axe, en repere
canonique = meilleur axe en position 0). Les 2 features scalaires echouaient (+0/-3) mais gap avait le bon
signe -> un modele sur le vecteur complet capte-t-il le signal ? Train sur 1/2 des situations, mesure du gain
capture sur l'autre 1/2 (de-bruite). Si >= +3 : le schema est apprenable (officier = axe +10 ET schema)."""
import torch
import torch.nn as nn
from train_koth_gpu import Net
from assault_terrain import AssaultTerrain
from officer_select import exposure_by_bearing
from officer_maneuver import kB_far, place, outcome
from officer_synth import coverage
dev = "cuda:0"; K = 8


def collect(net, M=4096, R=24, seed=31):
    env = AssaultTerrain(num_envs=M, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=seed)
    env.reset(); expo = exposure_by_bearing(env); kA = expo.argmin(1); kB = kB_far(expo, kA)
    idx = (torch.arange(K, device=dev)[None] + kA[:, None]) % K           # repere canonique (depart = meilleur axe)
    guns = torch.stack([coverage(env, torch.full((M,), k, device=dev, dtype=torch.long)).sum(1) for k in range(K)], 1)
    feats = torch.cat([torch.gather(expo, 1, idx), torch.gather(guns, 1, idx) / 4.0], 1)  # (M,16)
    NC = torch.zeros(R, M, device=dev); NP = torch.zeros(R, M, device=dev)
    for r in range(R):
        place(env, kA, kA); NC[r], _ = outcome(net, env)
        place(env, kA, kB); NP[r], _ = outcome(net, env)
    return feats, NC.mean(0), NP.mean(0)


if __name__ == "__main__":
    env0 = AssaultTerrain(num_envs=8, relief=40.0, hit=0.15, grid_obs=True, device=dev, seed=0)
    net = Net(env0.obs_dim, env0.n_actions, 256, 3).to(dev)
    net.load_state_dict(torch.load("assault_grid.pt", map_location=dev)); net.eval()
    feats, pc, pp = collect(net)
    adv = pp - pc; label = (adv > 0).float()
    mu, sd = feats.mean(0), feats.std(0) + 1e-6; feats = (feats - mu) / sd
    M = feats.shape[0]; h = M // 2
    clf = nn.Sequential(nn.Linear(16, 64), nn.ReLU(), nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 1)).to(dev)
    opt = torch.optim.Adam(clf.parameters(), lr=1e-3, weight_decay=1e-4)
    w = adv.abs()  # poids : les situations ou le schema compte vraiment pesent plus
    for ep in range(400):
        logit = clf(feats[:h])[:, 0]
        loss = (nn.functional.binary_cross_entropy_with_logits(logit, label[:h], reduction="none") * w[:h]).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        pred = clf(feats[h:])[:, 0] > 0      # predit pince
    pcte, ppte, advte = pc[h:], pp[h:], adv[h:]
    cap = torch.where(pred, ppte, pcte).mean().item()
    bf = max(pcte.mean().item(), ppte.mean().item()); orc = torch.maximum(pcte, ppte).mean().item()
    conf = advte.abs() > 0.10                # situations ou un schema est nettement meilleur
    acc = ((pred == (advte > 0))[conf]).float().mean().item()
    print("=" * 72)
    print("SELECTEUR DE SCHEMA APPRIS (MLP sur exposition+fusils des 8 axes, repere canonique)")
    print("=" * 72)
    print("  situations TEST : %d | dont schema nettement decisif (|adv|>10pts) : %d" % (ppte.shape[0], int(conf.sum())))
    print("  precision du MLP sur les situations decisives : %.0f%% (50%% = au hasard)" % (100 * acc))
    print("  --- gain capture (de-bruite, TEST) ---")
    print("  meilleur schema FIXE     : %3.0f%%" % (100 * bf))
    print("  SELECTEUR APPRIS         : %3.0f%%  -> %+.0f pts vs fixe" % (100 * cap, 100 * (cap - bf)))
    print("  plafond oracle           : %3.0f%%  (+%.0f pts)" % (100 * orc, 100 * (orc - bf)))
    print(">>> %s" % ("LE SCHEMA EST APPRENABLE -> officier = axe (+10) ET schema (selecteur appris)"
                      if (cap - bf) >= 0.03 else
                      "meme appris, le schema ne se predit pas -> son +6 (oracle) est du bruit idiosyncratique, pas un signal lisible -> officier reste sur l'AXE"))
    print("SCHEMELEARN FINI")
