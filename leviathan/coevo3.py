#!/usr/bin/env python3
"""coevo3.py — PHASE F.1 : la league de coevo2 portee au format LIVE.
10 features + archi EXACTE de orchestration_arma_voyant.pt -> produit orchestration_arma_league.pt (drop-in clash_live).
Meme mecanique que coevo2 (+59) : le defenseur exploite le pire trou (oracle best-response), on l'ajoute au pool,
l'attaquant patche tout -> robuste pire-cas + utilise TOUT le repertoire."""
import torch, torch.nn as nn
from torch.distributions import Categorical

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
NS = 5
OUT = "/home/younes/arma3-marl/leviathan/orchestration_arma_league.pt"


def gen(s, n):
    """latent s (n,) 0-4 -> 10 features (identique a orchestration_arma_env : 7 situationnelles + inventaire bruite)."""
    dev = s.device
    lo = lambda: torch.rand(n, device=dev) * 0.3
    hi = lambda: 0.7 + torch.rand(n, device=dev) * 0.3
    dist = 0.2 + torch.rand(n, device=dev) * 0.7
    behind = torch.where(s == 1, hi(), lo())
    entr = torch.where(s == 2, hi(), lo())
    expo = torch.where(s == 3, hi(), lo())
    openg = torch.where(s == 3, 0.6 + torch.rand(n, device=dev) * 0.4, lo())
    fire = torch.where(s == 4, hi(), lo())
    vis = torch.where(s == 1, 0.3 + torch.rand(n, device=dev) * 0.4, 0.6 + torch.rand(n, device=dev) * 0.4)
    gren = torch.rand(n, device=dev)
    smoke = torch.rand(n, device=dev)
    allies = torch.rand(n, device=dev)
    return torch.stack([dist, vis, behind, entr, expo, openg, fire, gren, smoke, allies], dim=1)


M = torch.full((NS, NS), 0.1, device=DEV)
for d in range(NS):
    M[d, d] = 0.6
M = M / M.sum(1, keepdim=True)


class OrchNet(nn.Module):                                          # ARCHI LIVE (drop-in orchestration_arma_voyant.pt)
    def __init__(s):
        super().__init__()
        s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def pol(att, f):
    return att(f)[0]


def sample_s(mix, n):
    return Categorical(mix).sample((n,))


def train_on(att, opt, mixes, iters=80, n=4096):
    for _ in range(iters):
        mix = mixes[torch.randint(len(mixes), (1,)).item()]
        s = sample_s(mix, n); f = gen(s, n)
        dpi = Categorical(logits=pol(att, f)); a = dpi.sample()
        r = (a == s).float(); adv = r - r.mean()
        loss = -(dpi.log_prob(a) * adv).mean() - 0.05 * dpi.entropy().mean()
        opt.zero_grad(); loss.backward(); opt.step()


def clear_rate(att, mix, n=8192):
    s = sample_s(mix, n); f = gen(s, n)
    return (pol(att, f).argmax(1) == s).float().mean().item()


def worst_case(att):
    return min(clear_rate(att, M[d]) for d in range(NS))


def run(rounds=8):
    torch.manual_seed(0)
    unif = torch.full((NS,), 1.0 / NS, device=DEV)

    a_naive = OrchNet().to(DEV); o = torch.optim.Adam(a_naive.parameters(), 3e-3)
    train_on(a_naive, o, [M[0]], iters=rounds * 80)                # 1 seule posture (defenseur fige)
    naive_wc = worst_case(a_naive)

    a = OrchNet().to(DEV); o = torch.optim.Adam(a.parameters(), 3e-3)
    pool = [unif]; traj = []
    for r in range(rounds):
        train_on(a, o, pool, iters=80)
        evals = [clear_rate(a, M[d]) for d in range(NS)]
        worst = int(torch.tensor(evals).argmin().item())           # meilleure-reponse du defenseur = le pire trou
        pool.append(M[worst]); traj.append(min(evals))
    league_wc = worst_case(a)

    s = sample_s(unif, 8192); preds = pol(a, gen(s, 8192)).argmax(1)
    used = preds.bincount(minlength=NS).float(); used = used / used.sum()
    div = int((used > 0.02).sum().item())

    torch.save(a.state_dict(), OUT)
    print("=== PHASE F.1 — league 10 features (archi live), device=%s ===" % DEV, flush=True)
    print("pire-cas par round : " + " -> ".join("%.0f%%" % (100 * x) for x in traj), flush=True)
    print("PIRE-CAS FINAL  naif=%.0f%%  league=%.0f%%  (+%.0f pts)" % (100 * naive_wc, 100 * league_wc, 100 * (league_wc - naive_wc)), flush=True)
    print("tactiques distinctes employees : %d / %d" % (div, NS), flush=True)
    print("SAVE -> %s (drop-in clash_live)" % OUT, flush=True)


if __name__ == "__main__":
    run()
