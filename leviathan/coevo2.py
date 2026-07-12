#!/usr/bin/env python3
"""coevo2.py — PHASE F FAITE BIEN : co-évolution 2-camps sur les VRAIES features (pas le toy bruité).
L'ATTAQUANT = l'orchestration (features réelles bruitées → tactique). Le DÉFENSEUR crée des SITUATIONS via
sa POSTURE (hold-open→EXPOSÉ, entrench→RETRANCHÉ, spread→À DÉCOUVERT, ambush→CLOUÉ, hardcover→COUVERT) et
choisit celle que l'attaquant gère le PIRE (meilleure-réponse). LEAGUE = on accumule les postures exploitées
→ l'attaquant les patche toutes → devient ROBUSTE + utilise TOUT le répertoire. Métrique STABLE = le PIRE-CAS
de l'attaquant sur les 5 postures (eval déterministe). Montre : naïf (1 posture) = exploitable ; league = robuste."""
import copy, torch, torch.nn as nn
from torch.distributions import Categorical

DEV = "cuda:0"; NS = 5


def gen(s, n):
    """Situation latente s (n,) → 7 features Arma réelles bruitées (comme orchestration_arma)."""
    dev = s.device
    lo = lambda: torch.rand(n, device=dev) * 0.3
    hi = lambda: 0.7 + torch.rand(n, device=dev) * 0.3
    dist = 0.2 + torch.rand(n, device=dev) * 0.7
    behind = torch.where(s == 1, hi(), lo()); entr = torch.where(s == 2, hi(), lo())
    expo = torch.where(s == 3, hi(), lo()); openg = torch.where(s == 3, 0.6 + torch.rand(n, device=dev) * 0.4, lo())
    fire = torch.where(s == 4, hi(), lo())
    vis = torch.where(s == 1, 0.3 + torch.rand(n, device=dev) * 0.4, 0.6 + torch.rand(n, device=dev) * 0.4)
    return torch.stack([dist, vis, behind, entr, expo, openg, fire], dim=1)


# postures : chacune concentre sur un type de situation (0.6) + fuite (0.1 ailleurs)
M = torch.full((NS, NS), 0.1, device=DEV)
for d in range(NS):
    M[d, d] = 0.6
M = M / M.sum(1, keepdim=True)


class Att(nn.Module):
    def __init__(self):
        super().__init__(); self.net = nn.Sequential(nn.Linear(7, 64), nn.Tanh(), nn.Linear(64, NS))
    def forward(self, x): return self.net(x)


def sample_s(mix, n):
    return Categorical(mix).sample((n,))


def train_on(att, opt, mixes, iters=60, n=4096):
    for _ in range(iters):
        mix = mixes[torch.randint(len(mixes), (1,)).item()]
        s = sample_s(mix, n); f = gen(s, n)
        dpi = Categorical(logits=att(f)); a = dpi.sample()
        r = (a == s).float()
        adv = r - r.mean()
        loss = -(dpi.log_prob(a) * adv).mean() - 0.05 * dpi.entropy().mean()
        opt.zero_grad(); loss.backward(); opt.step()


def clear_rate(att, mix, n=8192):
    s = sample_s(mix, n); f = gen(s, n)
    return (att(f).argmax(1) == s).float().mean().item()


def worst_case(att):
    return min(clear_rate(att, M[d]) for d in range(NS))


def run(rounds=8):
    torch.manual_seed(0)
    unif = torch.full((NS,), 1.0 / NS, device=DEV)

    # --- NAÏF : l'attaquant s'entraîne contre UNE seule posture (comme face à un défenseur figé) ---
    a_naive = Att().to(DEV); o = torch.optim.Adam(a_naive.parameters(), 3e-3)
    train_on(a_naive, o, [M[0]], iters=rounds * 60)                     # ne voit qu'un type de situation
    naive_wc = worst_case(a_naive)

    # --- LEAGUE : le défenseur exploite le pire trou, on l'ajoute au pool, l'attaquant patche ---
    a = Att().to(DEV); o = torch.optim.Adam(a.parameters(), 3e-3)
    pool = [unif]; traj = []
    for r in range(rounds):
        train_on(a, o, pool, iters=60)
        evals = [clear_rate(a, M[d]) for d in range(NS)]
        worst = int(torch.tensor(evals).argmin().item())               # meilleure-réponse du défenseur
        pool.append(M[worst])
        traj.append(min(evals))
    league_wc = worst_case(a)
    # diversité RÉELLE : combien de tactiques distinctes l'attaquant emploie sur l'ensemble des situations
    s = sample_s(unif, 8192); preds = a(gen(s, 8192)).argmax(1)
    used = preds.bincount(minlength=NS).float(); used = used / used.sum()
    div = int((used > 0.02).sum().item())

    print("=== PHASE F (bien) — co-évolution 2-camps sur features réelles ===", flush=True)
    print("pire-cas de l'attaquant par round (le défenseur attaque le trou) :", flush=True)
    print("  " + " -> ".join("%.0f%%" % (100 * x) for x in traj), flush=True)
    print("PIRE-CAS FINAL (robustesse sur TOUTES les postures) :", flush=True)
    print("  attaquant NAÏF (1 posture) : %.0f%%" % (100 * naive_wc), flush=True)
    print("  attaquant LEAGUE           : %.0f%%" % (100 * league_wc), flush=True)
    print("  -> +%.0f pts de robustesse pire-cas = combattant ADAPTATIF" % (100 * (league_wc - naive_wc)), flush=True)
    print("  tactiques distinctes employées : %d / %d (la league force tout le répertoire)" % (div, NS), flush=True)


if __name__ == "__main__":
    run()
