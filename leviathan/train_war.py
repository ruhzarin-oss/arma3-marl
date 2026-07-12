"""train_war.py — ETAGE 3 : CO-EVOLUTION de deux nations LEVIATHAN sur leviathan_war (Stratis).

Meilleure-reponse ALTERNEE + LEAGUE (pool des versions passees, anti-oubli, cf coevo_sandbox).
On entraine NORD contre un SUD GELE tire du pool, on le snapshot, puis SUD contre le pool NORD, etc.
On suit l'ECHELLE de la course aux armements (le camp qui s'entraine doit battre tout le pool adverse).
Reutilise Net + act de train_leviathan (politique generique a n_heads tetes 3-way).
"""
import time, argparse
import numpy as np
import torch
from torch.distributions import Categorical
from leviathan_war import LeviathanWar
from train_leviathan import Net, act

DEV = "cuda:0"
RNG = np.random.default_rng(0)


def snap(net):
    return {k: v.detach().clone() for k, v in net.state_dict().items()}


def _t(x):
    return torch.as_tensor(x, dtype=torch.float32, device=DEV)


def train_side(env, learner, lopt, frozen, pool, learner_nord, iters, T, cfg):
    """Entraine learner (NORD si learner_nord) contre des adversaires GELES tires du pool. Renvoie winrate vs pool."""
    gamma, lam, clip, epochs, vf, ent = cfg
    on, os_ = env.reset(); ot = [_t(on), _t(os_)]
    N = ot[0].shape[0]; O = env.obs_dim; H = env.n_heads
    li = 0 if learner_nord else 1
    wins, dec = [], []
    for it in range(iters):
        frozen.load_state_dict(pool[int(RNG.integers(len(pool)))])
        bo = torch.zeros(T, N, O, device=DEV); ba = torch.zeros(T, N, H, dtype=torch.long, device=DEV)
        bl = torch.zeros(T, N, device=DEV); bv = torch.zeros(T, N, device=DEV)
        br = torch.zeros(T, N, device=DEV); bd = torch.zeros(T, N, device=DEV)
        for t in range(T):
            with torch.no_grad():
                a_l, lp_l, v_l, _ = act(learner, ot[li])
                a_f, _, _, _ = act(frozen, ot[1 - li])
            a_n, a_s = (a_l, a_f) if learner_nord else (a_f, a_l)
            on, os_, rn, rs, done, info = env.step(a_n, a_s)
            r_l = rn if learner_nord else rs
            bo[t] = ot[li]; ba[t] = a_l; bl[t] = lp_l; bv[t] = v_l; br[t] = r_l; bd[t] = done
            win_l = info["n_win"] if learner_nord else info["s_win"]
            for nn in torch.where(done > 0)[0].tolist():
                if bool(info["decided"][nn]):
                    wins.append(float(win_l[nn])); dec.append(1.0)
                else:
                    dec.append(0.0)
            ot = [_t(on), _t(os_)]
        with torch.no_grad():
            _, _, lastv, _ = act(learner, ot[li])
        adv = torch.zeros(T, N, device=DEV); g = torch.zeros(N, device=DEV)
        for t in reversed(range(T)):
            nv = lastv if t == T - 1 else bv[t + 1]; nt = 1 - bd[t]
            delta = br[t] + gamma * nv * nt - bv[t]; g = delta + gamma * lam * nt * g; adv[t] = g
        ret = (adv + bv).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = bo.reshape(-1, O); fa = ba.reshape(-1, H); fl = bl.reshape(-1)
        for _ in range(epochs):
            lg, val = learner(fo); d = Categorical(logits=lg); nlp = d.log_prob(fa).sum(-1)
            ratio = torch.exp(nlp - fl)
            pl = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            vl = ((val - ret) ** 2).mean(); en = d.entropy().sum(-1).mean()
            loss = pl + vf * vl - ent * en
            lopt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(learner.parameters(), 0.5); lopt.step()
    return float(np.mean(wins[-4000:])) if wins else 0.0


def main(rounds=8, seg_iters=60, envs=1024, T=24, hidden=128, lr=3e-4, tag="war"):
    cfg = (0.99, 0.95, 0.2, 4, 0.5, 0.01)
    env = LeviathanWar(num_envs=envs, device=DEV)
    O = env.obs_dim; H = env.n_heads
    nord = Net(O, H, hidden).to(DEV); sud = Net(O, H, hidden).to(DEV); fz = Net(O, H, hidden).to(DEV)
    nopt = torch.optim.Adam(nord.parameters(), lr=lr); sopt = torch.optim.Adam(sud.parameters(), lr=lr)
    pool_n = [snap(nord)]; pool_s = [snap(sud)]
    print("CO-EVOLUTION GUERRE | dev=%s N=%d O=%d n_heads=%d | rounds=%d seg_iters=%d" % (DEV, envs, O, H, rounds, seg_iters), flush=True)
    t0 = time.time()
    for r in range(rounds):
        nwr = train_side(env, nord, nopt, fz, pool_s, True, seg_iters, T, cfg); pool_n.append(snap(nord))
        swr = train_side(env, sud, sopt, fz, pool_n, False, seg_iters, T, cfg); pool_s.append(snap(sud))
        print("ROUND %d (%.0fs) | NORD bat pool SUD %.2f | SUD bat pool NORD %.2f | pools %d/%d"
              % (r, time.time() - t0, nwr, swr, len(pool_n), len(pool_s)), flush=True)
    torch.save(nord.state_dict(), "/home/younes/arma3-marl/leviathan/%s_nord.pt" % tag)
    torch.save(sud.state_dict(), "/home/younes/arma3-marl/leviathan/%s_sud.pt" % tag)
    print("[fini] -> %s_nord.pt / %s_sud.pt" % (tag, tag), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=8); p.add_argument("--seg_iters", type=int, default=60)
    p.add_argument("--envs", type=int, default=1024); p.add_argument("--tag", type=str, default="war")
    a = p.parse_args()
    main(rounds=a.rounds, seg_iters=a.seg_iters, envs=a.envs, tag=a.tag)
