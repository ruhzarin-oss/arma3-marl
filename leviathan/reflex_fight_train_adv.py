#!/usr/bin/env python3
"""reflex_fight_train_adv.py — entraine le corps a AVANCER SOUS LE FEU (variante avec objectif).
Meme PPO / FightNet que reflex_fight_train, mais sur ReflexFightEnvAdv (objectif + recompense d'avance).
Mesure EN PLUS : % qui ATTEIGNENT l'objectif (le geste manquant / anti-gel). Sort reflex_advance_voyant.pt.
Sauve toutes les 50 iters (un run de nuit garde sa progression)."""
import time, argparse
import torch, torch.nn as nn
from torch.distributions import Categorical
from reflex_fight_env_adv import ReflexFightEnvAdv
from reflex_fight_train import FightNet, act

DEV = "cuda:0"


def load_warm(net, path):
    """warm-start depuis un corps deja competent au TIR/COUVERT (reflex_r23wh, obs=21) : ne re-apprend QUE l'avance."""
    old = torch.load(path, map_location=DEV); new = net.state_dict()
    for k in new:
        if k in old and old[k].shape == new[k].shape:
            new[k] = old[k]
        elif k == "b.0.weight" and k in old:                          # [h,23] <- [h,21] : garde tir/couvert, 2 colonnes objectif fraiches
            new[k][:, :old[k].shape[1]] = old[k]
    net.load_state_dict(new)
    print("[warm] tir/couvert charge depuis %s (reste a apprendre : l'avance)" % path.split("/")[-1], flush=True)


@torch.no_grad()
def evaluate(net, blind, n=4096, seed=999, adv=0.18):
    e = ReflexFightEnvAdv(n, DEV, blind=blind, seed=seed, adv=adv); obs = e._obs()
    al = []; kl = []; rc = []; dd = []
    for _ in range(e.max_steps * 2):
        m, s, f, _, _ = act(net, obs, greedy=True); obs, r, d, info = e.step(m, s, f)
        for i in torch.where(d > 0)[0].tolist():
            al.append(info["alive"][i].item()); kl.append(info["killed"][i].item())
            rc.append(info["reached"][i].item()); dd.append(info["dobj"][i].item())
    if not al: return (0.0, 0.0, 0.0, 99.0, e.K)
    return (100.0 * sum(al) / len(al), sum(kl) / len(kl), 100.0 * sum(rc) / len(rc), sum(dd) / len(dd), e.K)


def train(blind, iters=1500, envs=4096, T=24, lr=3e-4, h=160, adv=0.18, tag="reflex_advance", warm=None):
    gamma, lam, clip, epochs, vf, ent = 0.99, 0.95, 0.2, 4, 0.5, 0.03
    env = ReflexFightEnvAdv(envs, DEV, blind=blind, adv=adv); O = env.obs_dim; D = env.D
    net = FightNet(O, D, h).to(DEV)
    if warm: load_warm(net, warm)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    obs = env._obs(); t0 = time.time()
    print("AVANCE-SOUS-FEU %s | dev=%s N=%d O=%d adv=%.3f" % ("AVEUGLE" if blind else "VOYANT", DEV, envs, O, adv), flush=True)
    for it in range(iters):
        frac = min(1.0, it / max(1.0, iters * 0.6))                         # CURRICULUM : killzone courte+legere -> pleine+lourde
        env.p_base = 0.10 + 0.18 * frac; env.span = 0.45 + 0.55 * frac
        BO = torch.zeros(T, envs, O, device=DEV)
        BM = torch.zeros(T, envs, dtype=torch.long, device=DEV); BS = torch.zeros(T, envs, dtype=torch.long, device=DEV)
        BF = torch.zeros(T, envs, dtype=torch.long, device=DEV); BLP = torch.zeros(T, envs, device=DEV)
        BV = torch.zeros(T, envs, device=DEV); BR = torch.zeros(T, envs, device=DEV); BD = torch.zeros(T, envs, device=DEV)
        for t in range(T):
            with torch.no_grad(): m, s, f, lp, v = act(net, obs)
            no, r, d, info = env.step(m, s, f)
            BO[t] = obs; BM[t] = m; BS[t] = s; BF[t] = f; BLP[t] = lp; BV[t] = v; BR[t] = r; BD[t] = d; obs = no
        with torch.no_grad(): _, _, _, _, lastv = act(net, obs)
        gae = torch.zeros(T, envs, device=DEV); g = torch.zeros(envs, device=DEV)
        for t in reversed(range(T)):
            nv = lastv if t == T - 1 else BV[t + 1]; nt = 1 - BD[t]
            delta = BR[t] + gamma * nv * nt - BV[t]; g = delta + gamma * lam * nt * g; gae[t] = g
        ret = (gae + BV).reshape(-1); advn = ((gae - gae.mean()) / (gae.std() + 1e-8)).reshape(-1)
        fo = BO.reshape(-1, O); fm = BM.reshape(-1); fs = BS.reshape(-1); ff = BF.reshape(-1); fl = BLP.reshape(-1)
        for _ in range(epochs):
            ml, sl, fll, val = net(fo)
            dm = Categorical(logits=ml); ds = Categorical(logits=sl); dfd = Categorical(logits=fll)
            nlp = dm.log_prob(fm) + ds.log_prob(fs) + dfd.log_prob(ff); ratio = torch.exp(nlp - fl)
            ploss = -torch.min(ratio * advn, torch.clamp(ratio, 1 - clip, 1 + clip) * advn).mean()
            vl = ((val - ret) ** 2).mean(); en = (dm.entropy() + ds.entropy() + dfd.entropy()).mean()
            loss = ploss + vf * vl - ent * en
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
        if it % 50 == 0 or it == iters - 1:
            sv, kk, rr, dm, K = evaluate(net, blind, adv=adv)
            print("  it %4d | ATTEINT %2.0f%% | dist_obj %2.0f (depart~76) | survie %2.0f%% | neutr %.1f/%d | p=%.2f | %.0fs" % (it, rr, dm, sv, kk, K, env.p_base, time.time() - t0), flush=True)
            torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s_voyant.pt" % tag)
    torch.save(net.state_dict(), "/home/younes/arma3-marl/leviathan/%s_%s.pt" % (tag, "aveugle" if blind else "voyant"))
    return evaluate(net, blind, adv=adv)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iters", type=int, default=1500); p.add_argument("--envs", type=int, default=4096)
    p.add_argument("--adv", type=float, default=0.18); p.add_argument("--tag", default="reflex_advance")
    p.add_argument("--warm", default="/home/younes/arma3-marl/leviathan/reflex_r23wh_voyant.pt")  # "" = from scratch
    a = p.parse_args()
    print("=== CORPS : AVANCER SOUS LE FEU (objectif + recompense d'avance) ===", flush=True)
    sv, kk, rr, dm, K = train(blind=False, iters=a.iters, envs=a.envs, adv=a.adv, tag=a.tag, warm=(a.warm or None))
    print("\n=== RESULTAT VOYANT : ATTEINT %.0f%% | dist_obj %.0f | survie %.0f%% | neutralises %.1f/%d ===" % (rr, dm, sv, kk, K), flush=True)
