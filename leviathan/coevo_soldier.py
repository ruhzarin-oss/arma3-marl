#!/usr/bin/env python3
"""coevo_soldier — CO-ÉVOLUTION niveau SOLDAT : deux SHAMAL (attaquant + défenseur) qui apprennent
l'un contre l'autre dans duel_terrain (env bilatéral). Calque la boucle prouvée de coevo_live :
meilleure-réponse ALTERNÉE + POOL (league anti-oubli) + REINFORCE zéro-somme. Warm-start SHAMAL des 2 côtés.

Le squelette MINIMAL du prompt co-évo v2 : warm-start + best-response + petite league. On ajoute
les briques (nouveauté, exploiteurs...) SEULEMENT quand le symptôme apparaît.
Smoke :  python coevo_soldier.py smoke      |      Vrai run :  python coevo_soldier.py
"""
import sys, copy
import torch
from torch.distributions import Categorical
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from train_koth_gpu import Net

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
BASE = "/home/younes/arma3-marl"
SEED_CKPT = BASE + "/shamal_arma_win.pt"                 # graine SHAMAL (obs 17 = arma_obs)
RP = BASE + "/replica.npz"
OUT = BASE + "/leviathan/coevo_soldier.pt"


def mkenv(n, sd, A=9, B=9):
    return DuelTerrain(num_envs=n, A=A, B=B, R_spawn=120.0, replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)


def seed_net():
    net = Net(17, 13, 512, 3).to(DEV)
    try:
        net.load_state_dict(torch.load(SEED_CKPT, map_location=DEV)); tag = "warm-start SHAMAL"
    except Exception as e:
        tag = "SANS warm-start (%s)" % str(e)[:40]
    return net, tag


def episode(env, att, dfn):
    """rollout à horizon fixe (auto-reset) ; renvoie logp_att, logp_def, retour_att, retour_def."""
    obsA, obsB = env.reset()
    N = env.N
    lpA = torch.zeros(N, device=DEV); lpB = torch.zeros(N, device=DEV)
    RA = torch.zeros(N, device=DEV); RB = torch.zeros(N, device=DEV)
    for _ in range(env.max_steps):
        dA = Categorical(logits=att.a_logits(obsA)); aA = dA.sample()
        dB = Categorical(logits=dfn.a_logits(obsB)); aB = dB.sample()
        lpA = lpA + dA.log_prob(aA).sum(1); lpB = lpB + dB.log_prob(aB).sum(1)
        (obsA, obsB), (rA, rB), done, info = env.step(aA, aB)
        RA = RA + rA; RB = RB + rB
    return lpA, lpB, RA, RB


def train_att(env, att, oa, dpool, iters):
    for _ in range(iters):
        dfn = dpool[torch.randint(len(dpool), (1,)).item()]
        lpA, _, RA, _ = episode(env, att, dfn)                  # meilleure-réponse vs un défenseur tiré du pool
        loss = -(lpA * (RA - RA.mean())).mean()                 # REINFORCE : l'attaquant MAXIMISE son retour
        oa.zero_grad(); loss.backward(); oa.step()


def train_def(env, apool, dfn, od, iters):
    for _ in range(iters):
        at = apool[torch.randint(len(apool), (1,)).item()]
        _, lpB, _, RB = episode(env, at, dfn)                   # meilleure-réponse vs un attaquant tiré du pool
        loss = -(lpB * (RB - RB.mean())).mean()                 # le défenseur MAXIMISE SON retour (zéro-somme)
        od.zero_grad(); loss.backward(); od.step()


@torch.no_grad()
def winrate(env, att, dfn, reps=3):
    """fraction d'attaquant-gagne sur reps rollouts (déterministe = argmax)."""
    w = 0.0; nep = 0
    for _ in range(reps):
        obsA, obsB = env.reset(); done_once = torch.zeros(env.N, dtype=torch.bool, device=DEV)
        for _ in range(env.max_steps):
            aA = env_argmax(att, obsA); aB = env_argmax(dfn, obsB)
            (obsA, obsB), _, done, info = env.step(aA, aB, auto_reset=False)
            dm = done.bool() & ~done_once
            if dm.any(): w += info["att_wins"][dm].float().sum().item(); nep += int(dm.sum())
            done_once |= done.bool()
    return w / max(nep, 1)


def env_argmax(net, obs): return net.a_logits(obs).argmax(-1)


def run(rounds=8, iters=25, N=1024):
    torch.manual_seed(0)
    env = mkenv(N, 1)
    base, tag = seed_net()
    print("=== CO-ÉVOLUTION SOLDAT (duel_terrain) : 2 SHAMAL apprenants + league | %s ===" % tag, flush=True)
    att = copy.deepcopy(base).to(DEV); dfn = copy.deepcopy(base).to(DEV)
    oa = torch.optim.Adam(att.parameters(), 3e-4); od = torch.optim.Adam(dfn.parameters(), 3e-4)
    apool = [copy.deepcopy(base).eval()]; dpool = [copy.deepcopy(base).eval()]   # LEAGUE : pools des 2 côtés
    for r in range(rounds):
        train_att(env, att, oa, dpool, iters)
        train_def(env, apool, dfn, od, iters)
        apool.append(copy.deepcopy(att).eval()); dpool.append(copy.deepcopy(dfn).eval())
        wr_cur = winrate(env, att, dfn)                         # att courant vs def courant
        wr_base = winrate(env, att, dpool[0])                   # att courant vs def de base (SHAMAL brut)
        print("  round %d | attaquant-gagne vs def-appris=%.2f | vs def-base=%.2f | league=%d" % (r, wr_cur, wr_base, len(apool)), flush=True)
    torch.save({"attacker": att.state_dict(), "defender": dfn.state_dict()}, OUT)
    print("=== FIN co-évo soldat -> %s (2 SHAMAL co-évolués) ===" % OUT, flush=True)


if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    if SMOKE:
        run(rounds=2, iters=3, N=64)
    else:
        run()
