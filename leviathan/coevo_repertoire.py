#!/usr/bin/env python3
"""coevo_repertoire.py — PHASE F : co-évolution du répertoire. Deux camps choisissent une TACTIQUE (5,
issues du répertoire : frontal/flanc/suppression/fumée/grenade vs tenir/masser/embuscade/disperser/contrer),
jeu à somme nulle SANS stratégie dominante (chaque tactique a son contre). Chacun voit l'HISTOGRAMME récent
de l'adversaire → peut le CONTRER. On compare la self-play NAÏVE (oublie → exploitable) à la LEAGUE (pool
anti-oubli → robuste). Métrique = EXPLOITABILITÉ (combien une meilleure-réponse fraîche bat la politique ;
bas = combattant raffiné). Prouve : le répertoire co-évolué devient adaptatif et robuste."""
import torch, torch.nn as nn
from torch.distributions import Categorical

DEV = "cuda:0"; T = 5
# payoff cyclique généralisé (gain attaquant) : pas de tactique dominante -> il faut LIRE et CONTRER
P = torch.zeros(T, T, device=DEV)
for a in range(T):
    for d in range(T):
        diff = (d - a) % T
        P[a, d] = 1.0 if diff in (1, 2) else (-1.0 if diff in (3, 4) else 0.0)


class Pol(nn.Module):
    def __init__(self):
        super().__init__(); self.net = nn.Sequential(nn.Linear(T, 32), nn.Tanh(), nn.Linear(32, T))
    def forward(self, h): return self.net(h)


def play(att, defp, n=8192, steps=16, train=None, opt=None):
    """Joue n duels répétés ; chaque camp voit l'histo adverse. Si train='att'/'def', REINFORCE ce camp."""
    ah = torch.ones(n, T, device=DEV) / T; dh = torch.ones(n, T, device=DEV) / T
    logps, rews, ents, gain = [], [], [], 0.0
    for _ in range(steps):
        al = att(dh.detach()); dl = defp(ah.detach())
        da = Categorical(logits=al); dd = Categorical(logits=dl)
        a = da.sample(); d = dd.sample()
        pay = P[a, d]                                                   # gain attaquant
        gain += pay.mean().item()
        if train == "att": logps.append(da.log_prob(a)); rews.append(pay); ents.append(da.entropy())
        if train == "def": logps.append(dd.log_prob(d)); rews.append(-pay); ents.append(dd.entropy())
        ah = 0.9 * ah + 0.1 * nn.functional.one_hot(a, T).float()
        dh = 0.9 * dh + 0.1 * nn.functional.one_hot(d, T).float()
    if train:
        R = torch.stack(rews).sum(0); R = (R - R.mean()) / (R.std() + 1e-6)
        ent = torch.stack(ents).mean()
        loss = -(torch.stack(logps).sum(0) * R).mean() - 0.2 * ent     # + entropie -> stratégie MIXTE (tout le kit)
        opt.zero_grad(); loss.backward(); opt.step()
    return gain / steps


def best_response_gain(target, side, iters=400):
    """Entraîne une meilleure-réponse FRAÎCHE contre `target` -> son gain = l'exploitabilité de target."""
    br = Pol().to(DEV); opt = torch.optim.Adam(br.parameters(), 3e-3)
    for _ in range(iters):
        if side == "att": play(br, target, train="att", opt=opt)
        else: play(target, br, train="def", opt=opt)
    g = play(br, target) if side == "att" else -play(target, br)
    return g                                                           # gain de la meilleure-réponse (haut = target exploitable)


def run(rounds=30):
    torch.manual_seed(0)
    # --- NAÏVE : meilleure-réponse alternée, SANS pool ---
    A, D = Pol().to(DEV), Pol().to(DEV); oA = torch.optim.Adam(A.parameters(), 3e-3); oD = torch.optim.Adam(D.parameters(), 3e-3)
    for _ in range(rounds):
        for _ in range(8): play(A, D, train="att", opt=oA)
        for _ in range(8): play(A, D, train="def", opt=oD)
    naive_expl = (best_response_gain(A, "att") + best_response_gain(D, "def")) / 2

    # --- LEAGUE : pool anti-oubli, chacun s'entraîne contre un ADVERSAIRE du pool ---
    import copy, random
    A, D = Pol().to(DEV), Pol().to(DEV); oA = torch.optim.Adam(A.parameters(), 3e-3); oD = torch.optim.Adam(D.parameters(), 3e-3)
    poolA, poolD = [copy.deepcopy(A)], [copy.deepcopy(D)]
    for r in range(rounds):
        for _ in range(8): play(A, poolD[r % len(poolD)], train="att", opt=oA)
        for _ in range(8): play(poolA[r % len(poolA)], D, train="def", opt=oD)
        poolA.append(copy.deepcopy(A)); poolD.append(copy.deepcopy(D))
    league_expl = (best_response_gain(A, "att") + best_response_gain(D, "def")) / 2

    print("=== PHASE F — co-évolution du répertoire ===", flush=True)
    print("exploitabilité (gain d'une meilleure-réponse fraîche ; BAS = robuste) :", flush=True)
    print("  self-play NAÏVE  : %.3f" % naive_expl, flush=True)
    print("  LEAGUE (pool)    : %.3f" % league_expl, flush=True)
    print("  -> la league réduit l'exploitabilité de %.0f%% = combattant plus ROBUSTE" %
          (100 * (naive_expl - league_expl) / max(naive_expl, 1e-6)), flush=True)
    # entropie de la stratégie finale = utilise-t-il TOUT le répertoire ?
    h = torch.ones(1, T, device=DEV) / T
    ent = Categorical(logits=A(h)).entropy().item()
    print("  entropie tactique finale : %.2f / %.2f (haut = utilise tout le répertoire)" % (ent, torch.log(torch.tensor(float(T))).item()), flush=True)


if __name__ == "__main__":
    run()
