"""shamal_bc — la COPIE : behavior cloning du prof SHAMAL dans une politique Net (train_koth_gpu).

On déroule le prof scripté dans AssaultTerrain, on collecte les paires (obs_étudiant -> action_prof),
et on entraîne le réseau par ENTROPIE CROISÉE à imiter le prof. Résultat = SHAMAL copié au niveau
LAMBS, qui servira de WARM-START au RL (shamal_rl.py) pour le DÉPASSER.

Aucun rendu, aucune physique. Même archi Net que le RL -> le warm-start est un simple load_state_dict.
Smoke (prouve le pipeline, ~s) :  python shamal_bc.py smoke
Vrai run (à NE lancer que sur ton feu vert) :  python shamal_bc.py
"""
import sys, time, os
import numpy as np
import torch
import torch.nn as nn
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from shamal_teacher import shamal_action

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
BASE = "/home/younes/arma3-marl"
RP = BASE + "/replica.npz"
ARMA = os.environ.get("SHAMAL_ARMA") == "1"   # SHAMAL_ARMA=1 -> obs allégée Arma-cheap (pont Arma) ; sinon obs sandbox
OUT = BASE + ("/shamal_arma_bc.pt" if ARMA else "/shamal_bc.pt")
# ENTRAÎNEMENT sur les villes de RELIEF (comme l'ablation) ; l'éval se fera sur les HELD-OUT
TRAIN_MAPS = [BASE + "/replica_%s.npz" % c for c in ("ronda", "matera", "positano", "sarajevo")]


def mkenv(n, sd, A=9, D=6, path=RP):
    return AssaultTerrain(num_envs=n, A=A, D=D, R_spawn=115.0, relief=40.0, hit=0.10,
                          shell_obs=not ARMA, team_obs=True, suffer=True, postures=True, hull=True,
                          arma_obs=ARMA, replica=True, replica_path=path, max_steps=60, device=DEV, seed=sd)


def collect(e, obs, T):
    """Déroule le prof T pas (auto_reset ON -> enchaîne les épisodes). Renvoie (obs, actions_prof) empilés."""
    OB = []; AC = []
    for _ in range(T):
        a = shamal_action(e)                 # cible privilégiée (le prof)
        OB.append(obs); AC.append(a)         # paire (ce que voit l'étudiant, ce que fait le prof)
        obs, _, _, _ = e.step(a)
    return torch.stack(OB), torch.stack(AC), obs   # (T,N,A,O), (T,N,A), obs_final


@torch.no_grad()
def agreement(net, e, steps=20):
    """Fraction d'actions où l'étudiant == prof (rollout piloté par le prof) = qualité de la copie."""
    obs = e.reset(); ok = tot = 0
    for _ in range(steps):
        a_t = shamal_action(e)
        a_s = net.a_logits(obs).argmax(-1)
        ok += (a_s == a_t).float().sum().item(); tot += a_t.numel()
        obs, _, _, _ = e.step(a_t)
    return ok / max(tot, 1)


def train(iters=200, N=1024, A=9, D=6, T=32, lr=3e-4, epochs=3, mbs=4, seed=0, maps=None, log=True):
    torch.manual_seed(seed)
    maps = maps or [RP]
    envs = [mkenv(N, seed + i, A, D, m) for i, m in enumerate(maps)]   # un env par carte d'entraînement
    obs = [e.reset() for e in envs]
    O, NA = envs[0].obs_dim, envs[0].n_actions
    net = Net(O, NA, 512, 3).to(DEV)
    opt = torch.optim.Adam(net.parameters(), lr)
    for it in range(iters):
        ei = it % len(envs)                                # tourne sur les cartes -> l'étudiant les voit toutes
        OB, AC, obs[ei] = collect(envs[ei], obs[ei], T)    # rollout du prof sur cette carte
        fob = OB.reshape(-1, A, O); fac = AC.reshape(-1, A)
        idx = np.arange(fob.shape[0]); mb = max(1, fob.shape[0] // mbs)
        tot = 0.0; nb = 0
        for _ in range(epochs):
            np.random.shuffle(idx)
            for s in range(0, fob.shape[0], mb):
                j = torch.as_tensor(idx[s:s + mb], device=DEV)
                logits = net.a_logits(fob[j])              # (mb,A,NA)
                loss = nn.functional.cross_entropy(logits.reshape(-1, NA), fac[j].reshape(-1))
                opt.zero_grad(); loss.backward()
                nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
                tot += loss.item(); nb += 1
        if log and (it % 20 == 0 or it == iters - 1):
            acc = sum(agreement(net, e) for e in envs) / len(envs)   # accord moyen sur les cartes
            print("  [BC it %3d] perte %.3f | accord prof %.1f%% (%d cartes)" % (it, tot / max(nb, 1), 100 * acc, len(envs)), flush=True)
    return net, envs


if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    ITERS = 2 if SMOKE else 200
    N = 64 if SMOKE else 1024
    MAPS = TRAIN_MAPS[:2] if SMOKE else TRAIN_MAPS         # smoke = 2 cartes ; vrai run = les 4 villes de relief
    print("=== SHAMAL behavior cloning (copie LAMBS) SMOKE=%s | %d cartes ===" % (SMOKE, len(MAPS)), flush=True)
    t0 = time.time()
    net, envs = train(iters=ITERS, N=N, maps=MAPS)
    torch.save(net.state_dict(), OUT)
    print("SHAMAL_BC_DONE  (%.0fs)  -> %s" % (time.time() - t0, OUT), flush=True)
