"""traque_league.py — CO-EVOLUTION ALTERNEE + LEAGUE pour la traque (FS multi-agent vs PAYS grille).
Chaque ROUND : on GELE le pays (tire de son pool) et on entraine les FS a le battre -> snapshot FS dans le pool ;
puis on GELE les FS (du pool) et on entraine le pays -> snapshot pays. Chaque camp s'entraine contre TOUT le pool
adverse (anti-oubli). On suit le face-a-face courant (survie FS) round par round : la course aux ruses.
Reutilise FSNet/act (traque_train) + CountryNet/act (traque_coevo). Warm-start des versions grille competentes."""
import time, argparse, statistics as st
import numpy as np, torch, torch.nn as nn
from torch.distributions import Categorical
from traque_env import TraqueEnv
from traque_train import FSNet, act as act_fs
from traque_coevo import CountryNet, act_country, evaluate

DEV = "cuda:0"; RNG = np.random.default_rng(0); H_FS = 160; H_CO = 128
CFG = (0.99, 0.95, 0.2, 4, 0.5, 0.02)   # gamma,lam,clip,epochs,vf,ent


def snap(net):
    return {k: v.detach().clone() for k, v in net.state_dict().items()}


def train_fs_seg(env, fs, fopt, czf, cpool, iters, T):
    gamma, lam, clip, epochs, vf, ent = CFG; F = env.n_fs; O = env.obs_dim; M = env.M; N = env.N
    obs = env._obs()
    for it in range(iters):
        czf.load_state_dict(cpool[int(RNG.integers(len(cpool)))])
        BO = torch.zeros(T, N, F, O, device=DEV); BTG = torch.zeros(T, N, F, dtype=torch.long, device=DEV)
        BPO = torch.zeros(T, N, F, dtype=torch.long, device=DEV); BLP = torch.zeros(T, N, F, device=DEV)
        BV = torch.zeros(T, N, F, device=DEV); BR = torch.zeros(T, N, F, device=DEV); BM = torch.zeros(T, N, M, device=DEV); BD = torch.zeros(T, N, device=DEV)
        for t in range(T):
            na = env.node_alive.clone()
            with torch.no_grad():
                tg, po, lp, v = act_fs(fs, obs, na); ca, _, _ = act_country(czf, env.obs_country())
            no, r, done, info = env.step(tg, po, ca)
            BO[t] = obs; BTG[t] = tg; BPO[t] = po; BLP[t] = lp; BV[t] = v; BR[t] = r; BM[t] = na; BD[t] = done; obs = no
        with torch.no_grad():
            _, _, _, lv = act_fs(fs, obs, env.node_alive)
        adv = torch.zeros(T, N, F, device=DEV); g = torch.zeros(N, F, device=DEV)
        for t in reversed(range(T)):
            nv = lv if t == T - 1 else BV[t + 1]; nt = (1 - BD[t])[:, None]
            d = BR[t] + gamma * nv * nt - BV[t]; g = d + gamma * lam * nt * g; adv[t] = g
        ret = (adv + BV).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        fo = BO.reshape(-1, O); ftg = BTG.reshape(-1); fpo = BPO.reshape(-1); fl = BLP.reshape(-1)
        fm = BM[:, :, None, :].expand(T, N, F, M).reshape(-1, M)
        for _ in range(epochs):
            tl, pl, val = fs(fo); tl = tl.masked_fill(fm <= 0, -1e9); dt = Categorical(logits=tl); dp = Categorical(logits=pl)
            ratio = torch.exp(dt.log_prob(ftg) + dp.log_prob(fpo) - fl)
            ploss = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            loss = ploss + vf * ((val - ret) ** 2).mean() - ent * (dt.entropy() + dp.entropy()).mean()
            fopt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(fs.parameters(), 0.5); fopt.step()


def train_country_seg(env, co, copt, fzf, fpool, iters, T):
    gamma, lam, clip, epochs, vf, ent = CFG; OC = env.country_obs_dim; K = env.n_teams; N = env.N
    obs = env._obs()
    for it in range(iters):
        fzf.load_state_dict(fpool[int(RNG.integers(len(fpool)))])
        CO = torch.zeros(T, N, OC, device=DEV); CA = torch.zeros(T, N, K, dtype=torch.long, device=DEV)
        CLP = torch.zeros(T, N, device=DEV); CV = torch.zeros(T, N, device=DEV); CR = torch.zeros(T, N, device=DEV); BD = torch.zeros(T, N, device=DEV)
        for t in range(T):
            oc = env.obs_country()
            with torch.no_grad():
                tg, po, _, _ = act_fs(fzf, obs, env.node_alive); ca, clp, cv = act_country(co, oc)
            no, r, done, info = env.step(tg, po, ca)
            CO[t] = oc; CA[t] = ca; CLP[t] = clp; CV[t] = cv; CR[t] = info["rew_country"]; BD[t] = done; obs = no
        with torch.no_grad():
            _, _, clv = act_country(co, env.obs_country())
        adv = torch.zeros(T, N, device=DEV); g = torch.zeros(N, device=DEV)
        for t in reversed(range(T)):
            nv = clv if t == T - 1 else CV[t + 1]; nt = 1 - BD[t]
            d = CR[t] + gamma * nv * nt - CV[t]; g = d + gamma * lam * nt * g; adv[t] = g
        ret = (adv + CV).reshape(-1); advn = ((adv - adv.mean()) / (adv.std() + 1e-8)).reshape(-1)
        co_o = CO.reshape(-1, OC); co_a = CA.reshape(-1, K); cl = CLP.reshape(-1)
        for _ in range(epochs):
            lg, val = co(co_o); dd = Categorical(logits=lg); ratio = torch.exp(dd.log_prob(co_a).sum(-1) - cl)
            ploss = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            loss = ploss + vf * ((val - ret) ** 2).mean() - ent * dd.entropy().sum(-1).mean()
            copt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(co.parameters(), 0.5); copt.step()


def main(rounds=6, seg=60, envs=512, T=16, lr=3e-4, tag="traque_league", n_fs=40, fs_evade=1.0):
    env = TraqueEnv(num_envs=envs, device=DEV, n_fs=n_fs, fs_evade=fs_evade); O = env.obs_dim; M = env.M; OC = env.country_obs_dim; Z = env.Z; K = env.n_teams
    NF = env.n_fs
    fs = FSNet(O, M, H_FS).to(DEV); co = CountryNet(OC, Z, K, H_CO).to(DEV)
    czf = CountryNet(OC, Z, K, H_CO).to(DEV); fzf = FSNet(O, M, H_FS).to(DEV)
    base = "/home/younes/arma3-marl/leviathan/"
    try: fs.load_state_dict(torch.load(base + "traque_grid_fs.pt")); co.load_state_dict(torch.load(base + "traque_grid_pays.pt")); print("[warm] FS+pays <- grille", flush=True)
    except Exception as e: print("[warm] echec (%s)" % e, flush=True)
    fopt = torch.optim.Adam(fs.parameters(), lr=lr); copt = torch.optim.Adam(co.parameters(), lr=lr)
    pool_fs = [snap(fs)]; pool_co = [snap(co)]
    print("LEAGUE TRAQUE | N=%d rounds=%d seg=%d | FS=%d noeuds=%d zones=%d equipes=%d" % (envs, rounds, seg, env.n_fs, M, Z, K), flush=True)
    c0, a0, _ = evaluate(fs, co, n_fs=n_fs, fs_evade=fs_evade); print("depart : FS survivants %.1f/%d | coercion %.1f/88" % (a0, NF, c0), flush=True)
    t0 = time.time()
    for r in range(rounds):
        train_fs_seg(env, fs, fopt, czf, pool_co, seg, T); pool_fs.append(snap(fs))
        train_country_seg(env, co, copt, fzf, pool_fs, seg, T); pool_co.append(snap(co))
        c, a, s = evaluate(fs, co, n_fs=n_fs, fs_evade=fs_evade)
        print("ROUND %d (%.0fs) | face-a-face : FS survivants %.1f/%d | coercion %.1f/88 | capteurs %.1f/5 | pools %d/%d"
              % (r, time.time() - t0, a, NF, c, s, len(pool_fs), len(pool_co)), flush=True)
    torch.save(fs.state_dict(), base + "%s_fs.pt" % tag); torch.save(co.state_dict(), base + "%s_pays.pt" % tag)
    print("[fini] -> %s_fs.pt / %s_pays.pt" % (tag, tag), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=6); p.add_argument("--seg", type=int, default=60); p.add_argument("--envs", type=int, default=512); p.add_argument("--tag", type=str, default="traque_league")
    p.add_argument("--n_fs", type=int, default=40); p.add_argument("--fs_evade", type=float, default=1.0)
    a = p.parse_args()
    main(rounds=a.rounds, seg=a.seg, envs=a.envs, tag=a.tag, n_fs=a.n_fs, fs_evade=a.fs_evade)
