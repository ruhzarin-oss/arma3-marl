#!/usr/bin/env python3
"""coevo_command.py — CO-EVOLUTION : les DEUX camps APPRENNENT + league anti-oubli.
  ATTAQUANT (net : 10 features -> tactique) ET DEFENSEUR (net : -> posture = quelle situation presenter).
Meilleure-reponse ALTERNEE + POOL des versions passees (league). Montre :
  - NAIF (chacun ne bat que le DERNIER) : CYCLE, s'oublient, exploitable.
  - LEAGUE (chacun bat tout le POOL) : CONVERGE vers un equilibre ROBUSTE (attaquant use tout le repertoire,
    defenseur etale ses postures). C'est la difference figee -> vivant."""
import copy, torch, torch.nn as nn
from torch.distributions import Categorical

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
NS = 5
NAMES = ["EXPOSE", "COUVERT", "RETRANCHE", "DECOUVERT", "CLOUE"]


def gen(s, n):
    dev = s.device
    lo = lambda: torch.rand(n, device=dev) * 0.3
    hi = lambda: 0.7 + torch.rand(n, device=dev) * 0.3
    dist = 0.2 + torch.rand(n, device=dev) * 0.7
    behind = torch.where(s == 1, hi(), lo()); entr = torch.where(s == 2, hi(), lo())
    expo = torch.where(s == 3, hi(), lo()); openg = torch.where(s == 3, 0.6 + torch.rand(n, device=dev) * 0.4, lo())
    fire = torch.where(s == 4, hi(), lo()); vis = torch.where(s == 1, 0.3 + torch.rand(n, device=dev) * 0.4, 0.6 + torch.rand(n, device=dev) * 0.4)
    f = torch.stack([dist, vis, behind, entr, expo, openg, fire, torch.rand(n, device=dev), torch.rand(n, device=dev), torch.rand(n, device=dev)], 1)
    return (f + torch.randn(f.shape, device=dev) * 0.28).clamp(0, 1)   # AMBIGUITE : brouillard de guerre -> l'attaquant ne lit plus parfaitement la situation


class Att(nn.Module):
    def __init__(s):
        super().__init__(); s.net = nn.Sequential(nn.Linear(10, 64), nn.Tanh(), nn.Linear(64, NS))
    def forward(s, x):
        return s.net(x)


class Defe(nn.Module):                                          # politique de posture (quelle situation presenter)
    def __init__(s):
        super().__init__(); s.logits = nn.Parameter(torch.zeros(NS))
    def dist(s):
        return torch.softmax(s.logits, 0)


def onehot(k):
    return torch.eye(NS, device=DEV)[k]


def clear(att, dpost, n=8192):
    s = Categorical(dpost).sample((n,)).to(DEV)
    return (att(gen(s, n)).argmax(1) == s).float().mean().item()


def worst_case(att):
    return min(clear(att, onehot(k)) for k in range(NS))


def train_att(att, opt, defpool, iters, n=4096):
    for _ in range(iters):
        dp = defpool[torch.randint(len(defpool), (1,)).item()]
        s = Categorical(dp).sample((n,)).to(DEV); f = gen(s, n)
        pi = Categorical(logits=att(f)); a = pi.sample(); r = (a == s).float()
        loss = -(pi.log_prob(a) * (r - r.mean())).mean() - 0.03 * pi.entropy().mean()
        opt.zero_grad(); loss.backward(); opt.step()


def train_def(dfn, opt, attpool, iters, n=4096):
    for _ in range(iters):
        at = attpool[torch.randint(len(attpool), (1,)).item()]
        dp = dfn.dist()
        s = Categorical(dp).sample((n,)).to(DEV); f = gen(s, n)
        with torch.no_grad():
            correct = (at(f).argmax(1) == s).float()
        lp = Categorical(dp).log_prob(s); rew = 1 - correct                 # le defenseur veut que l'attaquant ECHOUE
        loss = -(lp * (rew - rew.mean())).mean() - 0.03 * Categorical(dp).entropy()
        opt.zero_grad(); loss.backward(); opt.step()


def run(rounds=12):
    torch.manual_seed(0); unif = torch.full((NS,), 1.0 / NS, device=DEV)

    # ---------- NAIF : chacun ne s'entraine que contre le DERNIER de l'autre ----------
    a = Att().to(DEV); d = Defe().to(DEV)
    oa = torch.optim.Adam(a.parameters(), 3e-3); od = torch.optim.Adam(d.parameters(), 5e-2)
    naive_traj = []
    for r in range(rounds):
        train_att(a, oa, [d.dist().detach()], 60)
        train_def(d, od, [a], 60)
        naive_traj.append(clear(a, d.dist().detach()))
    naive_wc = worst_case(a); naive_dpost = d.dist().detach()

    # ---------- LEAGUE : chacun bat tout le POOL des versions passees ----------
    a = Att().to(DEV); d = Defe().to(DEV)
    oa = torch.optim.Adam(a.parameters(), 3e-3); od = torch.optim.Adam(d.parameters(), 5e-2)
    apool = [Att().to(DEV)]; dpool = [unif]
    lg_traj = []
    for r in range(rounds):
        train_att(a, oa, dpool, 80)
        train_def(d, od, apool, 80)
        apool.append(copy.deepcopy(a).eval()); dpool.append(d.dist().detach())
        lg_traj.append(clear(a, d.dist().detach()))
    league_wc = worst_case(a); lg_dpost = d.dist().detach()

    # diversite attaquant (tactiques employees sur postures uniformes)
    s = Categorical(unif).sample((8192,)).to(DEV); used = a(gen(s, 8192)).argmax(1).bincount(minlength=NS).float(); used /= used.sum()
    div = int((used > 0.05).sum().item())

    print("=== CO-EVOLUTION 2-camps APPRENANTS (%s) ===" % DEV, flush=True)
    print("Taux de reussite attaquant par round :", flush=True)
    print("  NAIF   : " + " ".join("%.0f%%" % (100 * x) for x in naive_traj) + "   (oscille = cycle/oubli)", flush=True)
    print("  LEAGUE : " + " ".join("%.0f%%" % (100 * x) for x in lg_traj) + "   (se stabilise = equilibre)", flush=True)
    print("PIRE-CAS attaquant (robustesse sur TOUTES les postures pures) :", flush=True)
    print("  NAIF   = %.0f%%  (exploitable)" % (100 * naive_wc), flush=True)
    print("  LEAGUE = %.0f%%  (robuste)  -> +%.0f pts" % (100 * league_wc, 100 * (league_wc - naive_wc)), flush=True)
    print("Defenseur final (etalement des postures, 20%%=uniforme) :", flush=True)
    print("  NAIF   : " + " ".join("%s=%.0f%%" % (NAMES[k], 100 * naive_dpost[k]) for k in range(NS)) + "  (concentre)", flush=True)
    print("  LEAGUE : " + " ".join("%s=%.0f%%" % (NAMES[k], 100 * lg_dpost[k]) for k in range(NS)) + "  (etale)", flush=True)
    print("Attaquant LEAGUE : %d/%d tactiques employees (repertoire complet si =5)" % (div, NS), flush=True)
    torch.save({"attacker": a.state_dict(), "defender_logits": d.logits.detach()}, "/home/younes/compose-embodiment/coevo_command.pt")
    print("SAVE -> coevo_command.pt (attaquant + defenseur co-evolues)", flush=True)


if __name__ == "__main__":
    run()
