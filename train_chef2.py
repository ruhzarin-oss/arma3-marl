"""train_chef2 — ETAGE 2 : LE CHEF sur soldats role-aware (adaptateur).
Chef APPRIS assigne un role/agent toutes les K etapes. Soldat = d6 GELE + adaptateur GELE :
   logits = d6.a_logits(obs) + adaptateur(obs, role)     (l'ordre passe par l'adaptateur, pas d'override)
PPO sur le seul chef. Baseline = d6-solo pur (sans chef ni adaptateur). Test : chef > solo a D=8 ?"""
import sys, time, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
D6 = "/home/younes/compose-embodiment/hostage_v1_FINAL.pt"
ADP = "/home/younes/compose-embodiment/role_adapter.pt"
NROLES = 3


class Adapter(nn.Module):   # meme archi que train_adapter (pour recharger role_adapter.pt)
    def __init__(self, obs_dim, nact, h=128):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs_dim + NROLES, h), nn.ReLU(), nn.Linear(h, h), nn.ReLU())
        self.bias = nn.Linear(h, nact); self.v = nn.Linear(h, 1)

    def forward(self, obs, role_oh):
        z = self.body(torch.cat([obs, role_oh], -1))
        return 5.0 * self.bias(z), self.v(z).squeeze(-1)


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


def rollout(chef, d6, ad, eyeR, env, K, decisions, train=True, mode="chef"):
    # mode: "chef"=role appris ; "solo"=d6 pur (baseline) ; "fixed"=tout PORTEUR via adaptateur
    N, A = env.N, env.A; obs = env.reset()
    buf = {k: [] for k in ("o", "r", "lp", "v", "rew", "dn")}
    succ = nep = pick = wipe = 0; rolecnt = torch.zeros(NROLES, device=DEV)
    for di in range(decisions):
        go = chef_obs(env)
        if mode == "chef":
            if train:
                roles, lp, v, _ = chef_policy(chef, go, True)
            else:
                with torch.no_grad(): roles, lp, v, _ = chef_policy(chef, go, False)
        else:
            roles = torch.full((N, A), 2, dtype=torch.long, device=DEV); lp = v = None
        rolecnt += torch.bincount(roles.reshape(-1), minlength=NROLES).float()
        racc = torch.zeros(N, device=DEV); dany = torch.zeros(N, dtype=torch.bool, device=DEV)
        for _ in range(K):
            with torch.no_grad():
                if mode == "solo":
                    logits = d6.a_logits(obs)
                else:
                    bias, _ = ad(obs, eyeR[roles]); logits = d6.a_logits(obs) + bias
                act = torch.distributions.Categorical(logits=logits).sample()
            obs, rw, done, info = env.step(act); racc = racc + rw.mean(-1); dm = done.bool(); dany |= dm
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
    O, NA, A = env.obs_dim, env.n_actions, env.A
    d6 = Net(O, NA, 512, 3).to(DEV); d6.load_state_dict(torch.load(D6, map_location=DEV)); d6.eval()
    ad = Adapter(O, NA).to(DEV); ad.load_state_dict(torch.load(ADP, map_location=DEV)); ad.eval()
    for p in d6.parameters(): p.requires_grad_(False)
    for p in ad.parameters(): p.requires_grad_(False)
    eyeR = torch.eye(NROLES, device=DEV)
    gdim = chef_obs(env).shape[-1]; chef = Chef(gdim, A).to(DEV); opt = torch.optim.Adam(chef.parameters(), lr=lr)
    _, b = rollout(chef, d6, ad, eyeR, HostageEnv(num_envs=2048, A=9, D=D, device=DEV, seed=999), K, decisions, train=False, mode="solo")
    print("BASELINE d6-solo pur (D=%d) : RESCOUSSE %.0f%% | pickup %.0f%% | aneantie %.0f%%" % (D, 100 * b["resc"], 100 * b["pick"], 100 * b["wipe"]), flush=True)
    t0 = time.time()
    for it in range(iters):
        env.ff_hit = 0.0; env.exfil_hit = 0.0
        buf, m = rollout(chef, d6, ad, eyeR, env, K, decisions, train=True, mode="chef")
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
                _, me = rollout(chef, d6, ad, eyeR, HostageEnv(num_envs=2048, A=9, D=D, device=DEV, seed=999), K, decisions, train=False, mode="chef")
            print("it %3d | CHEF resc %.0f%% pick %.0f%% aneantie %.0f%% | assaut/appui/porteur %.0f/%.0f/%.0f%% | %.0fs" % (
                it, 100 * me["resc"], 100 * me["pick"], 100 * me["wipe"], 100 * me["roles"][1], 100 * me["roles"][0], 100 * me["roles"][2], time.time() - t0), flush=True)
    torch.save(chef.state_dict(), "/home/younes/compose-embodiment/chef2.pt")
    print("CHEF2 FINI -> chef2.pt", flush=True)


main()
