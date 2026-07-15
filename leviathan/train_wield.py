#!/usr/bin/env python3
"""train_wield — apprendre à SHAMAL à MANIER les formes : tenir le rang hors engagement, le rompre pour
combattre. Fine-tune (REINFORCE) de l'attaquant dans duel_terrain avec form_w>0 et une FORME ALÉATOIRE
par env (il apprend à manier les 15). Défenseur = SHAMAL gelé. Récompense = combat + fidélité GATÉE
(s'efface dès qu'un ennemi est à portée) -> il apprend le JUGEMENT. Smoke : python train_wield.py smoke"""
import sys, copy, torch
from torch.distributions import Categorical
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from train_koth_gpu import Net
DEV = "cuda:0"; BASE = "/home/younes/arma3-marl"
SEED_CKPT = BASE + "/shamal_arma_win.pt"; OUT = BASE + "/shamal_wield.pt"


def mkenv(n, sd, fw):
    return DuelTerrain(num_envs=n, A=12, B=8, form_w=fw, mutual_support=True,   # OPTION B : la formation PAIE
                       replica=True, replica_path=BASE + "/replica.npz", max_steps=60, device=DEV, seed=sd)


def rand_forms(env):
    env.a_form_idx = torch.randint(env.n_forms, (env.N,), device=DEV)   # forme aléatoire par env -> apprend à manier les 15


def episode(env, att, defn):
    obsA, obsB = env.reset(); rand_forms(env); obsA = env._obs_A()
    N = env.N; lp = torch.zeros(N, device=DEV); R = torch.zeros(N, device=DEV)
    for t in range(env.max_steps):
        dA = Categorical(logits=att.a_logits(obsA)); aA = dA.sample(); lp = lp + dA.log_prob(aA).sum(1)
        with torch.no_grad(): aB = defn.a_logits(obsB).argmax(-1)
        (obsA, obsB), (rA, rB), done, info = env.step(aA, aB)
        R = R + rA
    return lp, R


@torch.no_grad()
def measure(att):
    """dist-au-slot + ESPACEMENT (voisin le + proche : bon ~4-20m, blob <4, isolé >25) + winrate."""
    env = mkenv(256, 7, 0.0); obsA, obsB = env.reset(); rand_forms(env); obsA = env._obs_A()
    z = torch.zeros(env.N, device=DEV); tot = 0.0; sp = 0.0; cnt = 0; w = 0.0; nep = 0
    done_once = torch.zeros(env.N, dtype=torch.bool, device=DEV); n = env.A; EYE = torch.eye(n, dtype=torch.bool, device=DEV)[None]
    for t in range(60):
        al = env._a_alive(); alf = al.float()
        sx, sy = env._side_slots(env.ax, env.ay, al, env.a_form_idx, env._tmplA, z, z, env.form_forward)
        tot += ((torch.sqrt((env.ax - sx) ** 2 + (env.ay - sy) ** 2) * alf).sum() / alf.sum().clamp(min=1)).item()
        ddx = env.ax.unsqueeze(1) - env.ax.unsqueeze(2); ddy = env.ay.unsqueeze(1) - env.ay.unsqueeze(2)
        d2 = torch.where(EYE | ~al.unsqueeze(1), torch.tensor(1e18, device=DEV), ddx * ddx + ddy * ddy)
        nnd = d2.min(2).values.sqrt()
        sp += ((nnd * alf).sum() / alf.sum().clamp(min=1)).item(); cnt += 1
        aA = att.a_logits(obsA).argmax(-1); aB = att.a_logits(obsB).argmax(-1)
        (obsA, obsB), _, done, info = env.step(aA, aB, auto_reset=False); dm = done.bool() & ~done_once
        if dm.any(): w += info["att_wins"][dm].float().sum().item(); nep += int(dm.sum())
        done_once |= done.bool()
    return tot / cnt, sp / cnt, w / max(nep, 1)


def train(iters=300, N=512, fw=0.05, lr=3e-4):
    env = mkenv(N, 1, fw)
    att = Net(17, 13, 512, 3).to(DEV); att.load_state_dict(torch.load(SEED_CKPT, map_location=DEV))
    defn = copy.deepcopy(att).eval()
    opt = torch.optim.Adam(att.parameters(), lr)
    d0, s0, w0 = measure(att); print("  [avant] dist-slot=%.1fm | espacement=%.1fm | winrate=%.2f" % (d0, s0, w0), flush=True)
    for it in range(iters):
        lp, R = episode(env, att, defn)
        loss = -(lp * (R - R.mean())).mean(); opt.zero_grad(); loss.backward(); opt.step()
        if it % 30 == 0 or it == iters - 1:
            dd, ss, ww = measure(att); print("  [it %3d] retour=%.2f | dist-slot=%.1fm | espacement=%.1fm | winrate=%.2f" % (it, R.mean().item(), dd, ss, ww), flush=True)
    torch.save(att.state_dict(), OUT)


if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    print("=== MANIEMENT DES FORMES : SHAMAL apprend à tenir le rang + rompre pour combattre (form_w=0.15) ===", flush=True)
    if SMOKE: train(iters=4, N=64)
    else: train(iters=300, N=512)
    print("WIELD_DONE", flush=True)
