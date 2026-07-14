#!/usr/bin/env python3
"""coevo_formation — ÉTAGE HAUT : la co-évolution CHOISIT LA FORME.
Deux COMMANDANTs (attaquant / défenseur) apprennent à choisir la formation [parmi 15] selon l'ennemi
qui apprend aussi. Les SOLDATS (bas niveau, SHAMAL slot-follower FIXE) rejoignent leurs slots + combattent.
best-response ALTERNÉE + league (calque coevo_soldier). C'est ICI qu'émerge la SÉQUENCE de formes
que personne n'a scriptée (le dissident). Smoke : python coevo_formation.py smoke
"""
import sys, copy
import torch, torch.nn as nn
from torch.distributions import Categorical
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from train_koth_gpu import Net
import formations as FORM

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
BASE = "/home/younes/arma3-marl"
SOLDIER_CKPT = BASE + "/shamal_arma_win.pt"          # bas niveau FIXE (le soldat suit le vecteur-vers-slot)
OUT = BASE + "/leviathan/coevo_formation.pt"
KFORM = 10                                            # le commandant re-choisit la forme tous les K pas


class Commander(nn.Module):                           # obs d'escouade (6) -> logits sur 15 formes
    def __init__(s, sd=6, nf=15, h=64):
        super().__init__(); s.b = nn.Sequential(nn.Linear(sd, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh()); s.pi = nn.Linear(h, nf)
    def logits(s, o): return s.pi(s.b(o))


def load_soldier():
    net = Net(17, 13, 512, 3).to(DEV)
    try: net.load_state_dict(torch.load(SOLDIER_CKPT, map_location=DEV))
    except Exception as e: print("[soldat] pas de warm-start (%s)" % str(e)[:40], flush=True)
    net.eval(); return net


def mkenv(n, sd, A=9, B=9):
    return DuelTerrain(num_envs=n, A=A, B=B, replica=True, replica_path=BASE + "/replica.npz", max_steps=60, device=DEV, seed=sd)


def episode(env, ac, dc, soldier):
    obsA, obsB = env.reset(); N = env.N
    lpA = torch.zeros(N, device=DEV); lpB = torch.zeros(N, device=DEV)
    RA = torch.zeros(N, device=DEV); RB = torch.zeros(N, device=DEV)
    for t in range(env.max_steps):
        if t % KFORM == 0:                            # le COMMANDANT (re)choisit la forme
            da = Categorical(logits=ac.logits(env.squad_obs(0))); fa = da.sample()
            db = Categorical(logits=dc.logits(env.squad_obs(1))); fb = db.sample()
            lpA = lpA + da.log_prob(fa); lpB = lpB + db.log_prob(fb)
            env.set_forms(fa, fb); obsA, obsB = env._obs_A(), env._obs_B()   # slots recalculés
        with torch.no_grad():
            aA = soldier.a_logits(obsA).argmax(-1); aB = soldier.a_logits(obsB).argmax(-1)   # soldats FIXES
        (obsA, obsB), (rA, rB), done, info = env.step(aA, aB)
        RA = RA + rA; RB = RB + rB
    return lpA, lpB, RA, RB


def train_att(env, ac, oa, dpool, soldier, iters):
    for _ in range(iters):
        dc = dpool[torch.randint(len(dpool), (1,)).item()]
        lpA, _, RA, _ = episode(env, ac, dc, soldier)
        loss = -(lpA * (RA - RA.mean())).mean(); oa.zero_grad(); loss.backward(); oa.step()


def train_def(env, apool, dc, od, soldier, iters):
    for _ in range(iters):
        ac = apool[torch.randint(len(apool), (1,)).item()]
        _, lpB, _, RB = episode(env, ac, dc, soldier)
        loss = -(lpB * (RB - RB.mean())).mean(); od.zero_grad(); loss.backward(); od.step()


@torch.no_grad()
def report(env, ac, dc, soldier):
    obsA, obsB = env.reset(); w = 0.0; nep = 0; done_once = torch.zeros(env.N, dtype=torch.bool, device=DEV)
    fa_h = torch.zeros(env.n_forms, device=DEV); fb_h = torch.zeros(env.n_forms, device=DEV)
    for t in range(env.max_steps):
        if t % KFORM == 0:
            fa = ac.logits(env.squad_obs(0)).argmax(-1); fb = dc.logits(env.squad_obs(1)).argmax(-1)
            env.set_forms(fa, fb); obsA, obsB = env._obs_A(), env._obs_B()
            fa_h += torch.bincount(fa, minlength=env.n_forms).float(); fb_h += torch.bincount(fb, minlength=env.n_forms).float()
        aA = soldier.a_logits(obsA).argmax(-1); aB = soldier.a_logits(obsB).argmax(-1)
        (obsA, obsB), _, done, info = env.step(aA, aB, auto_reset=False); dm = done.bool() & ~done_once
        if dm.any(): w += info["att_wins"][dm].float().sum().item(); nep += int(dm.sum())
        done_once |= done.bool()
    return w / max(nep, 1), FORM.NAMES[int(fa_h.argmax())], FORM.NAMES[int(fb_h.argmax())]


def run(rounds=8, iters=25, N=1024):
    torch.manual_seed(0)
    env = mkenv(N, 1); soldier = load_soldier()
    print("=== CO-ÉVO ÉTAGE HAUT : les commandants choisissent la FORME (soldat SHAMAL fixe) + league ===", flush=True)
    ac = Commander().to(DEV); dc = Commander().to(DEV)
    oa = torch.optim.Adam(ac.parameters(), 3e-4); od = torch.optim.Adam(dc.parameters(), 3e-4)
    apool = [copy.deepcopy(ac).eval()]; dpool = [copy.deepcopy(dc).eval()]
    for r in range(rounds):
        train_att(env, ac, oa, dpool, soldier, iters)
        train_def(env, apool, dc, od, soldier, iters)
        apool.append(copy.deepcopy(ac).eval()); dpool.append(copy.deepcopy(dc).eval())
        wr, ta, tb = report(env, ac, dc, soldier)
        print("  round %d | att-gagne=%.2f | forme att=%-12s | forme def=%-12s | league=%d" % (r, wr, ta, tb, len(apool)), flush=True)
    torch.save({"att_cmd": ac.state_dict(), "def_cmd": dc.state_dict()}, OUT)
    print("=== FIN étage HAUT -> %s ===" % OUT, flush=True)


if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    if SMOKE: run(rounds=2, iters=3, N=64)
    else: run()
