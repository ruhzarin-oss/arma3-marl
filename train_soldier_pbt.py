"""train_soldier_pbt — ajoute la SOUFFRANCE/SELECTION au soldat a coque de couvert.
Population de P politiques, gagnabilite VARIABLE (1v2..1v5 melangees), MORT QUI COUTE.
Selection PBT sur le DISCERNEMENT = gagne-le-gagnable ET survis-au-submerge ; bas tiers <- copies mutees du haut.
Sortie : soldier_suffer.pt + scorecard (victoire@gagnable / survie@submerge) qui doit monter sur LES DEUX.
args: gens kiter"""
import torch, math, time, sys
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
DEV = "cuda:0"


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, N = rew.shape
    adv = torch.zeros(T, N, device=rew.device); g = torch.zeros(N, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]
        nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]
        g = delta + gam * lam * nonterm * g
        adv[t] = g
    return adv


def ppo_iters(net, opt, env, obs, K, O, rollout=16):
    N, A = env.N, env.A
    for it in range(K):
        OB = torch.zeros(rollout, N, A, O, device=DEV); AC = torch.zeros(rollout, N, A, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, N, A, device=DEV); VL = torch.zeros(rollout, N, device=DEV)
        RW = torch.zeros(rollout, N, device=DEV); DN = torch.zeros(rollout, N, device=DEV)
        for t in range(rollout):
            with torch.no_grad():
                dist = torch.distributions.Categorical(logits=net.a_logits(obs))
                act = dist.sample(); lp = dist.log_prob(act); val = net.value(obs)
            nobs, rw, done, info = env.step(act)
            if rw.dim() > 1:
                rw = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rw; DN[t] = done; obs = nobs
        with torch.no_grad():
            lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL
        adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        advA = adv.unsqueeze(-1).expand(rollout, N, A)
        ob = OB.reshape(-1, A, O); ac = AC.reshape(-1, A); oldlp = LP.reshape(-1, A)
        advf = advA.reshape(-1, A); retf = ret.reshape(-1)
        for ep in range(4):
            dist = torch.distributions.Categorical(logits=net.a_logits(ob)); lp = dist.log_prob(ac)
            ratio = (lp - oldlp).exp(); s1 = ratio * advf; s2 = torch.clamp(ratio, 0.8, 1.2) * advf
            loss = -torch.min(s1, s2).mean() + 0.5 * ((net.value(ob) - retf) ** 2).mean() - 0.01 * dist.entropy().mean()
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
    return obs


@torch.no_grad()
def evaluate(net, env, steps=70):
    obs = env.reset(); won = surv = 0.0; nep = 0
    for t in range(steps):
        act = net.a_logits(obs).argmax(-1)
        obs, rw, done, info = env.step(act); dm = done.bool()
        if dm.any():
            won += info["neutralized"][dm].float().sum().item()
            surv += (~info["wiped"][dm]).float().sum().item(); nep += int(dm.sum())
    return won / max(nep, 1), surv / max(nep, 1)


if __name__ == "__main__":
    GENS = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    K = int(sys.argv[2]) if len(sys.argv) > 2 else 18
    P, NE, NEVAL = 8, 1536, 1024
    relief, hit = 40.0, 0.10
    mk = lambda D, Dmin, n, sd: AssaultTerrain(num_envs=n, A=1, D=D, D_min=Dmin, relief=relief, hit=hit,
                                               shell_obs=True, suffer=True, max_steps=60, device=DEV, seed=sd)
    train_envs = [mk(6, 2, NE, 100 + s) for s in range(P)]          # gagnabilite 1v2..1v5
    O, NA = train_envs[0].obs_dim, train_envs[0].n_actions
    nets = [Net(O, NA, 512, 3).to(DEV) for _ in range(P)]
    opts = [torch.optim.Adam(n.parameters(), 3e-4) for n in nets]
    obs = [e.reset() for e in train_envs]
    ev_win = mk(2, 2, NEVAL, 7)                                     # GAGNABLE (1v2)
    ev_ovh = mk(6, 6, NEVAL, 8)                                     # SUBMERGE (1v6)
    print("===== SOLDAT SOUFFRANCE/SELECTION (PBT P=%d, gagnabilite 1v2..1v5, mort coute) =====" % P, flush=True)
    t0 = time.time()
    for gen in range(GENS):
        for p in range(P):
            obs[p] = ppo_iters(nets[p], opts[p], train_envs[p], obs[p], K, O)
        fits = []
        for p in range(P):
            w, _ = evaluate(nets[p], ev_win)
            _, sv = evaluate(nets[p], ev_ovh)
            fits.append((w, sv, w + sv))
        order = sorted(range(P), key=lambda p: fits[p][2], reverse=True)
        b = order[0]
        print("  gen %d | MEILLEUR victoire@gagnable %.0f%% survie@submerge %.0f%% (fit %.2f) | moy_fit %.2f | %.0fs"
              % (gen, 100 * fits[b][0], 100 * fits[b][1], fits[b][2], sum(f[2] for f in fits) / P, time.time() - t0), flush=True)
        nt = P // 3                                                 # bas tiers <- copies mutees du haut tiers (varie, pas que #1)
        for j in range(nt):
            loser, winner = order[-1 - j], order[j]
            nets[loser].load_state_dict(nets[winner].state_dict())
            with torch.no_grad():
                for pr in nets[loser].parameters():
                    pr.add_(torch.randn_like(pr) * 0.02)
            opts[loser] = torch.optim.Adam(nets[loser].parameters(), 3e-4); obs[loser] = train_envs[loser].reset()
    # meilleur final
    fits = []
    for p in range(P):
        w, _ = evaluate(nets[p], ev_win); _, sv = evaluate(nets[p], ev_ovh); fits.append((w, sv, w + sv))
    b = max(range(P), key=lambda p: fits[p][2])
    torch.save(nets[b].state_dict(), "/home/younes/arma3-marl/soldier_suffer.pt")
    print("\n>>> FINAL discernement (meilleur) : victoire@gagnable %.0f%% | survie@submerge %.0f%%"
          % (100 * fits[b][0], 100 * fits[b][1]), flush=True)
    print("SUFFER FINI", flush=True)
