"""BRIQUE 2+3 — LE CHEF DE COMPOSITION. Route par agent : RESCUE(->d6) / COVER(->soldier_shell).
Les DEUX skills sont GELES (vrais cerveaux entraines) -> zero effondrement. PPO sur le seul chef.
Couture : d6 lit env._obs() (29), soldier_shell lit env.B._obs() (22). Meme action (10).
Test : a D=8 (ou d6-solo plafonne ~17%), le chef qui compose les 2 fait-il mieux ?"""
import sys, time, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
D6 = "/home/younes/compose-embodiment/hostage_v1_FINAL.pt"
SH = "/home/younes/compose-embodiment/soldier_shell.pt"
NROLES = 2   # 0 = COVER (soldier_shell) ; 1 = RESCUE (d6)


class Chef(nn.Module):
    def __init__(self, gdim, A, h=256):
        super().__init__()
        self.tr = nn.Sequential(nn.Linear(gdim, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.role = nn.Linear(h, A * NROLES); self.v = nn.Linear(h, 1); self.A = A

    def forward(self, o):
        z = self.tr(o); return self.role(z).view(-1, self.A, NROLES), self.v(z).squeeze(-1)


def chef_obs(env):
    N, S = env.N, env.S
    ag = torch.stack([env.B.apx / S, env.B.apy / S, env.B._aalive().float()], -1).reshape(N, -1)
    dg = torch.stack([env.B.dpx / S, env.B.dpy / S, env.B._dalive().float()], -1).reshape(N, -1)
    h = torch.stack([env.hpx / S, env.hpy / S, env.hdmg, env.picked], -1)
    e = torch.stack([env.extx / S, env.exty / S], -1)
    return torch.cat([ag, dg, h, e], -1)


def chef_policy(net, o, sample=True):
    rl, v = net(o); d = torch.distributions.Categorical(logits=rl)
    r = d.sample() if sample else rl.argmax(-1)
    return r, d.log_prob(r).sum(1), v, d.entropy().sum(1)


def worker_act(d6, sh, env, roles):
    with torch.no_grad():
        a_res = torch.distributions.Categorical(logits=d6.a_logits(env._obs())).sample()
        a_cov = torch.distributions.Categorical(logits=sh.a_logits(env.B._obs())).sample()
    return torch.where(roles == 1, a_res, a_cov)   # role 1=RESCUE(d6), 0=COVER(soldier_shell)


def rollout(chef, d6, sh, env, K, decisions, train=True, mode="chef"):
    N, A = env.N, env.A; env.reset()
    buf = {k: [] for k in ("o", "r", "lp", "v", "rew", "dn")}
    succ = nep = pick = wipe = 0; rolecnt = torch.zeros(NROLES, device=DEV)
    for di in range(decisions):
        go = chef_obs(env)
        if mode == "chef":
            if train:
                roles, lp, v, _ = chef_policy(chef, go, True)
            else:
                with torch.no_grad(): roles, lp, v, _ = chef_policy(chef, go, False)
        else:   # solo = tout RESCUE (d6 pur)
            roles = torch.ones(N, A, dtype=torch.long, device=DEV); lp = v = None
        rolecnt += torch.bincount(roles.reshape(-1), minlength=NROLES).float()
        racc = torch.zeros(N, device=DEV); dany = torch.zeros(N, dtype=torch.bool, device=DEV)
        for _ in range(K):
            act = worker_act(d6, sh, env, roles)
            _, rw, done, info = env.step(act); racc = racc + rw.mean(-1); dm = done.bool(); dany |= dm
            if dm.any():
                succ += info["success"][dm].float().sum().item(); pick += info["picked"][dm].float().sum().item()
                wipe += info["squad_wipe"][dm].float().sum().item(); nep += int(dm.sum())
        if train and mode == "chef":
            buf["o"].append(go); buf["r"].append(roles); buf["lp"].append(lp.detach()); buf["v"].append(v.detach()); buf["rew"].append(racc); buf["dn"].append(dany.float())
    m = {"resc": succ / max(nep, 1), "pick": pick / max(nep, 1), "wipe": wipe / max(nep, 1), "roles": (rolecnt / rolecnt.sum().clamp(min=1)).tolist()}
    return buf, m


def main(iters=150, envs=2048, K=6, decisions=20, D=8, lr=3e-4):
    torch.manual_seed(0)
    env = HostageEnv(num_envs=envs, A=9, D=D, device=DEV, seed=0); env.ff_hit = 0.0; env.exfil_hit = 0.0
    A = env.A
    d6 = Net(29, 10, 512, 3).to(DEV); d6.load_state_dict(torch.load(D6, map_location=DEV)); d6.eval()
    sh = Net(22, 10, 512, 3).to(DEV); sh.load_state_dict(torch.load(SH, map_location=DEV)); sh.eval()
    for p in d6.parameters(): p.requires_grad_(False)
    for p in sh.parameters(): p.requires_grad_(False)
    gdim = chef_obs(env).shape[-1]; chef = Chef(gdim, A).to(DEV); opt = torch.optim.Adam(chef.parameters(), lr=lr)
    _, b = rollout(chef, d6, sh, HostageEnv(num_envs=2048, A=9, D=D, device=DEV, seed=999), K, decisions, train=False, mode="solo")
    print("BASELINE d6-solo (D=%d) : RESCOUSSE %.0f%% | pickup %.0f%% | aneantie %.0f%%" % (D, 100 * b["resc"], 100 * b["pick"], 100 * b["wipe"]), flush=True)
    t0 = time.time()
    for it in range(iters):
        env.ff_hit = 0.0; env.exfil_hit = 0.0
        buf, m = rollout(chef, d6, sh, env, K, decisions, train=True, mode="chef")
        T = len(buf["o"]); o = torch.stack(buf["o"]); r = torch.stack(buf["r"]); lp = torch.stack(buf["lp"]); val = torch.stack(buf["v"]); rew = torch.stack(buf["rew"]); dn = torch.stack(buf["dn"])
        adv = torch.zeros(T, envs, device=DEV); g = torch.zeros(envs, device=DEV)
        for t in reversed(range(T)):
            nxt = val[t + 1] if t + 1 < T else torch.zeros(envs, device=DEV); nd = 1.0 - dn[t]
            delta = rew[t] + 0.99 * nxt * nd - val[t]; g = delta + 0.99 * 0.95 * nd * g; adv[t] = g
        ret = adv + val; adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        of = o.reshape(T * envs, -1); rf = r.reshape(T * envs, A); lpf = lp.reshape(T * envs); af = adv.reshape(T * envs); rtf = ret.reshape(T * envs)
        for _ in range(4):
            rl, v = chef(of); d = torch.distributions.Categorical(logits=rl); lp2 = d.log_prob(rf).sum(1); ratio = (lp2 - lpf).exp()
            l_pi = -torch.min(ratio * af, ratio.clamp(0.8, 1.2) * af).mean(); l_v = 0.5 * (v - rtf).pow(2).mean(); l_e = -0.01 * d.entropy().sum(1).mean()
            opt.zero_grad(); (l_pi + l_v + l_e).backward(); nn.utils.clip_grad_norm_(chef.parameters(), 0.5); opt.step()
        if it % 15 == 0 or it == iters - 1:
            with torch.no_grad():
                _, me = rollout(chef, d6, sh, HostageEnv(num_envs=2048, A=9, D=D, device=DEV, seed=999), K, decisions, train=False, mode="chef")
            print("it %3d | CHEF resc %.0f%% pick %.0f%% aneantie %.0f%% | cover/rescue %.0f/%.0f%% | %.0fs" % (
                it, 100 * me["resc"], 100 * me["pick"], 100 * me["wipe"], 100 * me["roles"][0], 100 * me["roles"][1], time.time() - t0), flush=True)
    torch.save(chef.state_dict(), "/home/younes/compose-embodiment/chef_compose.pt")
    print("CHEF COMPOSE FINI -> chef_compose.pt", flush=True)


main()
