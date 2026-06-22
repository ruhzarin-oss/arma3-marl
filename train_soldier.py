"""train_soldier — apprend au SOLDAT SEUL (A=1) a se battre win-by-fire avec l'obs de l'avatar
(COQUE de couvert + menace + LOS + degats). PPO vectorise GPU. Compare COQUE vs SANS-COQUE.
Le but : un cerveau APPRIS pour l'avatar Arma, la ou la regle codee main echouait.
args: iters envs"""
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


def run(shell, iters, envs, A, D, relief, hit, seed, rollout=16, tag="soldier", replica=False, team_obs=False):
    env = AssaultTerrain(num_envs=envs, A=A, D=D, relief=relief, hit=hit, shell_obs=shell, team_obs=team_obs, max_steps=60,
                         replica=replica, replica_path="/home/younes/arma3-marl/replica.npz", device=DEV, seed=seed)
    O, NA, N = env.obs_dim, env.n_actions, envs
    net = Net(O, NA, 512, 3).to(DEV)
    opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    obs = env.reset(); t0 = time.time(); rr = lo = 0.0
    for it in range(iters):
        OB = torch.zeros(rollout, N, A, O, device=DEV); AC = torch.zeros(rollout, N, A, dtype=torch.long, device=DEV)
        LP = torch.zeros(rollout, N, A, device=DEV); VL = torch.zeros(rollout, N, device=DEV)
        RW = torch.zeros(rollout, N, device=DEV); DN = torch.zeros(rollout, N, device=DEV)
        neut = loss_f = 0.0; nep = 0
        for t in range(rollout):
            with torch.no_grad():
                logits = net.a_logits(obs); dist = torch.distributions.Categorical(logits=logits)
                act = dist.sample(); lp = dist.log_prob(act); val = net.value(obs)
            nobs, rw, done, info = env.step(act)
            if rw.dim() > 1:
                rw = rw.mean(-1)
            OB[t] = obs; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rw; DN[t] = done
            obs = nobs; dm = done.bool()
            if dm.any():
                neut += info["neutralized"][dm].float().sum().item(); loss_f += info["losses"][dm].sum().item(); nep += int(dm.sum())
        with torch.no_grad():
            lastv = net.value(obs)
        adv = gae(RW, VL, DN, lastv); ret = adv + VL
        adv = (adv - adv.mean()) / (adv.std() + 1e-6)
        advA = adv.unsqueeze(-1).expand(rollout, N, A)
        ob = OB.reshape(-1, A, O); ac = AC.reshape(-1, A); oldlp = LP.reshape(-1, A)
        advf = advA.reshape(-1, A); retf = ret.reshape(-1)
        for ep in range(4):
            logits = net.a_logits(ob); dist = torch.distributions.Categorical(logits=logits)
            lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            s1 = ratio * advf; s2 = torch.clamp(ratio, 0.8, 1.2) * advf
            pl = -torch.min(s1, s2).mean()
            v = net.value(ob); vl = ((v - retf) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent
            opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        rr = neut / max(nep, 1); lo = loss_f / max(nep, 1)
        if it % 20 == 0 or it == iters - 1:
            print("  [%s] it %3d | neutralises %3.0f%% | pertes %3.0f%% | %.0f tr/s"
                  % (tag, it, 100 * rr, 100 * lo, (it + 1) * rollout * N / (time.time() - t0)), flush=True)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/soldier_%s.pt" % tag)
    return rr, lo


if __name__ == "__main__":
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    envs = int(sys.argv[2]) if len(sys.argv) > 2 else 8192
    A, D, relief, hit = 1, 2, 40.0, 0.10
    print("===== SOLDAT win-by-fire (A=%d vs D=%d, relief=%.0f) : COQUE vs SANS =====" % (A, D, relief), flush=True)
    rp, lp = run(True, iters, envs, A, D, relief, hit, 0, tag="shell")
    rb, lb = run(False, iters, envs, A, D, relief, hit, 0, tag="noshell")
    print("\n>>> FINAL neutralises : COQUE %.0f%% (pertes %.0f%%) | SANS %.0f%% (pertes %.0f%%) | ecart %+.0f pts"
          % (100 * rp, 100 * lp, 100 * rb, 100 * lb, 100 * (rp - rb)), flush=True)
    print("SOLDIER FINI", flush=True)
