"""train_adapter — ETAGE 1 du chef. Rend d6 ROLE-AWARE sans le casser.
d6 GELE. Petit adaptateur entrainable : (obs, role) -> biais sur les logits + value.
  logits_worker = d6.a_logits(obs) + adaptateur_biais(obs, role)   (biais init a 0 -> demarre = d6)
Recompense PAR AGENT selon SON role (chaque role a un objectif POSITIF -> pas d'effondrement) :
  APPUI(0)  : se rapprocher du garde + suppression utile (le pinner)
  ASSAUT(1) : se rapprocher de l'objectif (otage/extraction)
  PORTEUR(2): idem objectif (recup + porte ; d6 gere la micro)
+ bonus succes partage, - mort individuelle. Roles tires AU HASARD par episode -> l'adaptateur voit tout.
Validation : on force tous les agents a un role et on regarde le comportement."""
import sys, math, torch
import torch.nn as nn
sys.path.insert(0, "/home/younes/compose-embodiment")
from hostage_env import HostageEnv
sys.path.insert(0, "/home/younes/arma3-marl")
from train_koth_gpu import Net
DEV = "cuda:0"
D6 = "/home/younes/compose-embodiment/hostage_v1_FINAL.pt"
NROLES = 3
OUT = "/home/younes/compose-embodiment/role_adapter.pt"


class Adapter(nn.Module):
    def __init__(self, obs_dim, nact, h=128):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs_dim + NROLES, h), nn.ReLU(), nn.Linear(h, h), nn.ReLU())
        self.bias = nn.Linear(h, nact); self.v = nn.Linear(h, 1)
        nn.init.zeros_(self.bias.weight); nn.init.zeros_(self.bias.bias)   # demarre = d6 pur

    def forward(self, obs, role_oh):
        z = self.body(torch.cat([obs, role_oh], -1))
        return 5.0 * self.bias(z), self.v(z).squeeze(-1)   # x5 : autorite pour rediriger un d6 confiant


def gae(rew, val, done, lastv, gam=0.99, lam=0.95):
    T, B = rew.shape; adv = torch.zeros(T, B, device=rew.device); g = torch.zeros(B, device=rew.device)
    for t in reversed(range(T)):
        nv = lastv if t == T - 1 else val[t + 1]; nonterm = 1.0 - done[t]
        delta = rew[t] + gam * nv * nonterm - val[t]; g = delta + gam * lam * nonterm * g; adv[t] = g
    return adv


def guard_dist_supp(env, act):
    # par agent : distance au garde vivant le + proche, et "suppression utile" (act==9 & garde en LOS+portee)
    ax, ay, S, N, A, D = env.B.apx, env.B.apy, env.S, env.N, env.A, env.D
    gpx, gpy, dal = env.B.dpx, env.B.dpy, env.B._dalive()
    dx = gpx[:, None, :] - ax[:, :, None]; dy = gpy[:, None, :] - ay[:, :, None]
    d2 = torch.where(dal[:, None, :], dx * dx + dy * dy, torch.full_like(dx, 1e18)); km = d2.argmin(2)
    ngx = torch.gather(gpx[:, None, :].expand(N, A, D), 2, km[..., None]).squeeze(2)
    ngy = torch.gather(gpy[:, None, :].expand(N, A, D), 2, km[..., None]).squeeze(2)
    gd = torch.sqrt((ngx - ax) ** 2 + (ngy - ay) ** 2)
    los = env.B._losc(env.B.hm, ax, ay, ngx, ngy, S)
    inr = (los > 0.5) & (gd < env.fire_range) & dal.any(1, keepdim=True)
    usupp = ((act == 9) & inr).float()
    return gd, usupp


def obj_dist(env):
    ax, ay = env.B.apx, env.B.apy; pk = (env.picked[:, None] > 0.5)
    dh = torch.sqrt((ax - env.hpx[:, None]) ** 2 + (ay - env.hpy[:, None]) ** 2)
    de = torch.sqrt((ax - env.extx[:, None]) ** 2 + (ay - env.exty[:, None]) ** 2)
    return torch.where(pk, de, dh)


def main(iters=200, envs=4096, rollout=24, D=6, lr=5e-4):
    torch.manual_seed(0)
    env = HostageEnv(num_envs=envs, A=9, D=D, device=DEV, seed=0); env.ff_hit = 0.0; env.exfil_hit = 0.0
    O, NA, A = env.obs_dim, env.n_actions, env.A
    d6 = Net(O, NA, 512, 3).to(DEV); d6.load_state_dict(torch.load(D6, map_location=DEV)); d6.eval()
    for p in d6.parameters(): p.requires_grad_(False)
    ad = Adapter(O, NA).to(DEV); opt = torch.optim.Adam(ad.parameters(), lr=lr)
    eyeR = torch.eye(NROLES, device=DEV)
    obs = env.reset()
    ROLE = torch.randint(0, NROLES, (envs, A), device=DEV)
    pdo = obj_dist(env); pdg, _ = guard_dist_supp(env, torch.zeros(envs, A, dtype=torch.long, device=DEV))
    for it in range(iters):
        env.ff_hit = 0.0; env.exfil_hit = 0.0
        OB = torch.zeros(rollout, envs, A, O, device=DEV); RO = torch.zeros(rollout, envs, A, dtype=torch.long, device=DEV)
        AC = torch.zeros(rollout, envs, A, dtype=torch.long, device=DEV); LP = torch.zeros(rollout, envs, A, device=DEV)
        VL = torch.zeros(rollout, envs, A, device=DEV); RW = torch.zeros(rollout, envs, A, device=DEV); DN = torch.zeros(rollout, envs, device=DEV)
        for t in range(rollout):
            roh = eyeR[ROLE]
            with torch.no_grad():
                bias, val = ad(obs, roh); logits = d6.a_logits(obs) + bias
                dist = torch.distributions.Categorical(logits=logits); act = dist.sample(); lp = dist.log_prob(act)
            nobs, rw_env, done, info = env.step(act)
            gd, usupp = guard_dist_supp(env, act); do = obj_dist(env)
            nd = (1.0 - done.float())[:, None]
            prog_obj = (pdo - do) / env.S * nd
            prog_g = (pdg - gd) / env.S * nd
            r_assaut = 2.0 * prog_obj
            r_appui = 1.5 * prog_g + 2.0 * usupp
            r_porteur = 2.0 * prog_obj
            rr = torch.where(ROLE == 0, r_appui, torch.where(ROLE == 1, r_assaut, r_porteur))
            adead = (env.B.admg > 0.7).float()
            rr = rr - 0.1 * adead - 0.005          # PUR signal de role (pas de bonus succes : il polluait)
            OB[t] = obs; RO[t] = ROLE; AC[t] = act; LP[t] = lp; VL[t] = val; RW[t] = rr; DN[t] = done
            obs = nobs; pdo = do; pdg = gd
            dm = done.bool()
            if dm.any():
                ROLE[dm] = torch.randint(0, NROLES, (int(dm.sum()), A), device=DEV)
                pdo[dm] = obj_dist(env)[dm]; g2, _ = guard_dist_supp(env, torch.zeros(envs, A, dtype=torch.long, device=DEV)); pdg[dm] = g2[dm]
        with torch.no_grad():
            bias, lastv = ad(obs, eyeR[ROLE])
        B = envs * A
        advf = gae(RW.reshape(rollout, B), VL.reshape(rollout, B), DN[:, :, None].expand(rollout, envs, A).reshape(rollout, B), lastv.reshape(B))
        retf = advf + VL.reshape(rollout, B); advf = (advf - advf.mean()) / (advf.std() + 1e-8)   # norm standard (d6 gele -> pas de risque)
        adv = advf.reshape(rollout, envs, A); ret = retf.reshape(rollout, envs, A)
        ob = OB.reshape(-1, A, O); ro = RO.reshape(-1, A); ac = AC.reshape(-1, A); oldlp = LP.reshape(-1, A); advA = adv.reshape(-1, A); retA = ret.reshape(-1, A)
        for ep in range(3):
            roh = eyeR[ro]; bias, v = ad(ob, roh); logits = d6.a_logits(ob) + bias
            dist = torch.distributions.Categorical(logits=logits); lp = dist.log_prob(ac); ratio = (lp - oldlp).exp()
            pl = -torch.min(ratio * advA, torch.clamp(ratio, 0.8, 1.2) * advA).mean(); vl = ((v - retA) ** 2).mean(); ent = dist.entropy().mean()
            loss = pl + 0.5 * vl - 0.01 * ent; opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(ad.parameters(), 0.5); opt.step()
        if it % 20 == 0 or it == iters - 1:
            # validation comportementale : force TOUT le monde a un role, mesure supp-rate et avance
            with torch.no_grad():
                msg = []
                for rname, rid in [("APPUI", 0), ("ASSAUT", 1), ("PORTEUR", 2)]:
                    e2 = HostageEnv(num_envs=512, A=9, D=D, device=DEV, seed=777); e2.ff_hit = 0; e2.exfil_hit = 0
                    o2 = e2.reset(); R2 = torch.full((512, 9), rid, dtype=torch.long, device=DEV)
                    sup = adv2 = 0.0; d0 = obj_dist(e2)
                    for _ in range(20):
                        b2, _ = ad(o2, eyeR[R2]); a2 = torch.distributions.Categorical(logits=d6.a_logits(o2) + b2).sample()
                        _, us = guard_dist_supp(e2, a2); o2, _, dn2, _ = e2.step(a2); sup += us.mean().item()
                    d1 = obj_dist(e2); msg.append("%s supp=%.2f davance=%.2f" % (rname, sup / 20, ((d0 - d1).mean().item()) / e2.S))
            print("it %3d | %s" % (it, " | ".join(msg)), flush=True)
    torch.save(ad.state_dict(), OUT)
    print("ADAPTER FINI -> role_adapter.pt", flush=True)


main()
