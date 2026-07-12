#!/usr/bin/env python3
"""benchmark_lambs.py — LE BENCHMARK : notre CORPS APPRIS (reflexes R1/R2/R3) vs une IA SCRIPTEE reactive (proxy LAMBS).
Meme scenario (1 soldat vs 3 tireurs), memes observations. Reponse a la question de depart : le soldat appris vaut-il le mod ?
NB : proxy = IA codee a la main (cherche le couvert, prone sous le feu, riposte vers la menace) ; le VRAI LAMBS est sur Arma."""
import math
import torch
from reflex_fight_env import ReflexFightEnv
from reflex_fight_train import FightNet, act

DEV = "cuda:0"; D = 8
ang = torch.arange(D, device=DEV) * (2 * math.pi / D); DX = torch.cos(ang); DY = torch.sin(ang)


def hand_coded(obs):
    # PROXY LAMBS (combattant) : riposte vers la menace, se met a terre sous le feu, TIENT et trade face a 1 tireur,
    # ne rompt vers le couvert que s'il est SUBMERGE (>=2 tireurs le voient). Heuristique reactive a la LAMBS.
    N = obs.shape[0]
    fire_dir = obs[:, 0:8]; exposed = obs[:, 8]; cvx = obs[:, 17]; cvy = obs[:, 18]
    fmax, fsec = fire_dir.max(1)
    fire = torch.where(fmax > 0.05, fsec + 1, torch.zeros(N, dtype=torch.long, device=DEV))     # riposte vers le feu
    zeros = torch.zeros(N, dtype=torch.long, device=DEV)
    msec = (cvx[:, None] * DX[None, :] + cvy[:, None] * DY[None, :]).argmax(1) + 1
    flee = exposed > 0.40                                                                        # >=2 tireurs me voient -> rompre
    move = torch.where(flee, msec, zeros)                                                        # sinon TIENT et trade
    stance = (exposed > 0.05).long()                                                            # prone sous le feu
    return move, stance, fire


@torch.no_grad()
def run(net, n=4096, seed=777):
    e = ReflexFightEnv(n, DEV, seed=seed); obs = e._obs(); al = []; kl = []; win = []
    for _ in range(e.max_steps * 2):
        m, s, f = act(net, obs, greedy=True)[:3] if net is not None else hand_coded(obs)
        obs, r, d, info = e.step(m, s, f)
        for i in torch.where(d > 0)[0].tolist():
            a = info["alive"][i].item(); k = info["killed"][i].item()
            al.append(a); kl.append(k); win.append(1.0 if (a > 0.5 and k >= e.K - 0.5) else 0.0)   # MISSION = tout nettoyer + survivre
    return 100.0 * sum(al) / len(al), sum(kl) / len(kl), 100.0 * sum(win) / len(win), e.K


net = FightNet(21, 8, 160).to(DEV); net.load_state_dict(torch.load("/home/younes/arma3-marl/leviathan/reflex_r23_voyant.pt")); net.eval()
sv_l, kl_l, wn_l, K = run(net)
sv_h, kl_h, wn_h, _ = run(None)
print("=== BENCHMARK : corps APPRIS vs IA scriptee combattante (proxy LAMBS) — 1 soldat vs 3 tireurs ===", flush=True)
print("CORPS APPRIS (nos reflexes R1/R2/R3) : MISSION REUSSIE %.0f%% | neutralise %.1f/%d | survie %.0f%%" % (wn_l, kl_l, K, sv_l), flush=True)
print("IA SCRIPTEE  (proxy LAMBS)           : MISSION REUSSIE %.0f%% | neutralise %.1f/%d | survie %.0f%%" % (wn_h, kl_h, K, sv_h), flush=True)
print("VERDICT (mission = tout nettoyer + survivre) : corps appris %+.0f pts de reussite vs le scripte" % (wn_l - wn_h), flush=True)
