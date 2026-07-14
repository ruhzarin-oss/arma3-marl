#!/usr/bin/env python3
"""coevo_compose — LE CERVEAU QUI COMPOSE LE RÉPERTOIRE.
Chaque commandant sort [FORMATION (15), MANŒUVRE (4: assaut/defend/hunt/bounding)] selon l'ennemi,
et co-évolue (best-response + league). Le CORPS scripté (repertoire_action) exécute fidèlement.
C'est ICI que « quelle forme + quelle manœuvre, quand, contre qui » émerge — le dissident.
Smoke : python coevo_compose.py smoke"""
import sys, copy, torch, torch.nn as nn
from torch.distributions import Categorical
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from duel_terrain import DuelTerrain
from scripted_formation import repertoire_action
import formations as FORM

DEV = "cuda:0"; BASE = "/home/younes/arma3-marl"
OUT = BASE + "/leviathan/coevo_compose.pt"
KCMD = 10; MAN = ["assaut", "defend", "hunt", "bounding", "envelop"]


class Commander(nn.Module):                          # squad_obs (6) -> (forme 15, manœuvre 5)
    def __init__(s, sd=6, nf=15, nm=5, h=64):
        super().__init__(); s.b = nn.Sequential(nn.Linear(sd, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        s.f = nn.Linear(h, nf); s.m = nn.Linear(h, nm)
    def act(s, o): h = s.b(o); return s.f(h), s.m(h)


def mkenv(n, sd, A=12, B=8):
    return DuelTerrain(num_envs=n, A=A, B=B, replica=True, replica_path=BASE + "/replica.npz", max_steps=60, device=DEV, seed=sd)


def episode(env, ac, dc):
    obsA, obsB = env.reset(); N = env.N
    lpA = torch.zeros(N, device=DEV); lpB = torch.zeros(N, device=DEV); RA = torch.zeros(N, device=DEV); RB = torch.zeros(N, device=DEV)
    for t in range(env.max_steps):
        if t % KCMD == 0:                            # le commandant (re)choisit forme + manœuvre
            fla, mla = ac.act(env.squad_obs(0)); flb, mlb = dc.act(env.squad_obs(1))
            da = Categorical(logits=fla); ma = Categorical(logits=mla); fa = da.sample(); maa = ma.sample()
            db = Categorical(logits=flb); mb = Categorical(logits=mlb); fb = db.sample(); mbb = mb.sample()
            lpA = lpA + da.log_prob(fa) + ma.log_prob(maa); lpB = lpB + db.log_prob(fb) + mb.log_prob(mbb)
            env.set_forms(fa, fb); env.set_maneuvers(maa, mbb)
        with torch.no_grad(): aA = repertoire_action(env, 0); aB = repertoire_action(env, 1)   # corps scripté
        (obsA, obsB), (rA, rB), done, info = env.step(aA, aB)
        RA = RA + rA; RB = RB + rB
    return lpA, lpB, RA, RB


def train_att(env, ac, oa, dpool, iters):
    for _ in range(iters):
        dc = dpool[torch.randint(len(dpool), (1,)).item()]
        lpA, _, RA, _ = episode(env, ac, dc); loss = -(lpA * (RA - RA.mean())).mean(); oa.zero_grad(); loss.backward(); oa.step()


def train_def(env, apool, dc, od, iters):
    for _ in range(iters):
        ac = apool[torch.randint(len(apool), (1,)).item()]
        _, lpB, _, RB = episode(env, ac, dc); loss = -(lpB * (RB - RB.mean())).mean(); od.zero_grad(); loss.backward(); od.step()


@torch.no_grad()
def report(env, ac, dc):
    obsA, obsB = env.reset(); w = 0.0; nep = 0; done_once = torch.zeros(env.N, dtype=torch.bool, device=DEV)
    fh = [torch.zeros(env.n_forms, device=DEV), torch.zeros(env.n_forms, device=DEV)]
    mh = [torch.zeros(env.n_maneuvers, device=DEV), torch.zeros(env.n_maneuvers, device=DEV)]
    for t in range(env.max_steps):
        if t % KCMD == 0:
            fla, mla = ac.act(env.squad_obs(0)); flb, mlb = dc.act(env.squad_obs(1))
            fa = fla.argmax(-1); maa = mla.argmax(-1); fb = flb.argmax(-1); mbb = mlb.argmax(-1)
            env.set_forms(fa, fb); env.set_maneuvers(maa, mbb)
            fh[0] += torch.bincount(fa, minlength=env.n_forms).float(); mh[0] += torch.bincount(maa, minlength=env.n_maneuvers).float()
            fh[1] += torch.bincount(fb, minlength=env.n_forms).float(); mh[1] += torch.bincount(mbb, minlength=env.n_maneuvers).float()
        aA = repertoire_action(env, 0); aB = repertoire_action(env, 1)
        (obsA, obsB), _, done, info = env.step(aA, aB, auto_reset=False); dm = done.bool() & ~done_once
        if dm.any(): w += info["att_wins"][dm].float().sum().item(); nep += int(dm.sum())
        done_once |= done.bool()
    return (w / max(nep, 1), FORM.NAMES[int(fh[0].argmax())], MAN[int(mh[0].argmax())],
            FORM.NAMES[int(fh[1].argmax())], MAN[int(mh[1].argmax())])


def run(rounds=8, iters=25, N=1024):
    torch.manual_seed(0); env = mkenv(N, 1)
    print("=== CERVEAU qui COMPOSE : commandants -> [forme + manœuvre] | corps scripté | league ===", flush=True)
    ac = Commander().to(DEV); dc = Commander().to(DEV)
    oa = torch.optim.Adam(ac.parameters(), 3e-4); od = torch.optim.Adam(dc.parameters(), 3e-4)
    apool = [copy.deepcopy(ac).eval()]; dpool = [copy.deepcopy(dc).eval()]
    for r in range(rounds):
        train_att(env, ac, oa, dpool, iters); train_def(env, apool, dc, od, iters)
        apool.append(copy.deepcopy(ac).eval()); dpool.append(copy.deepcopy(dc).eval())
        wr, fa, ma, fb, mb = report(env, ac, dc)
        print("  round %d | att-gagne=%.2f | ATT: %s + %-8s | DEF: %s + %-8s | league=%d" % (r, wr, fa, ma, fb, mb, len(apool)), flush=True)
    torch.save({"att": ac.state_dict(), "def": dc.state_dict()}, OUT)
    print("=== FIN cerveau-répertoire -> %s ===" % OUT, flush=True)


if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    if SMOKE: run(rounds=2, iters=3, N=64)
    else: run()
