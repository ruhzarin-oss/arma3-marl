"""REMEDE A LA VARIANCE : curriculum INVERSE (depart pres de l'objectif -> recule) + exploration ++.
Les graines qui rataient restaient coincees a « ne jamais pousser ». Le curriculum garantit que
CHAQUE graine goute la percee tot (depart facile), puis generalise au depart lointain.
Test : attention + audace + curriculum, 6 graines. Cible : eliminer les echecs (variance basse, percee ~1).
"""
import sys; sys.path.insert(0, "/home/younes/arma3-marl")
import numpy as np, torch, torch.nn as nn
from torch.distributions import Categorical
from breach_test import Breach, AttnActor, Critic, DEV

def train_curric(actor_cls, seed=0, iters=300, N=1024, A=6, T=40, lr=3e-4, clip=0.2, epochs=4, mbs=4, gamma=0.99, lam=0.95, ent_c=0.03):
    env = Breach(N, A, T=T, audace=True, seed=seed); od = env.obs_dim; G = env.G
    torch.manual_seed(seed)
    actor = actor_cls(od, env.n_actions).to(DEV); critic = Critic(od).to(DEV)
    opt = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=lr)
    of, ot = env.reset()
    for it in range(iters):
        frac = max(0.0, 1.0 - it / (0.6 * iters))                 # 1 tot -> 0 a 60%
        hi = int(round(1 + frac * ((G - 3) - 1)))                 # spawn pres de l'obj (G-3) -> bas (1)
        env.start_lo, env.start_hi = max(0, hi - 1), hi
        b_of = torch.zeros(T, N, A, od, device=DEV); b_ot = torch.zeros(T, N, A, A, 3, device=DEV)
        b_a = torch.zeros(T, N, A, dtype=torch.long, device=DEV); b_lp = torch.zeros(T, N, A, device=DEV)
        b_v = torch.zeros(T, N, device=DEV); b_r = torch.zeros(T, N, device=DEV); b_d = torch.zeros(T, N, device=DEV)
        for t in range(T):
            with torch.no_grad():
                dist = Categorical(logits=actor.logits(of, ot)); a = dist.sample(); v = critic.value(of)
            (of2, ot2), r, done, info = env.step(a)
            b_of[t] = of; b_ot[t] = ot; b_a[t] = a; b_lp[t] = dist.log_prob(a); b_v[t] = v; b_r[t] = r; b_d[t] = done.float()
            of, ot = of2, ot2
        with torch.no_grad(): last_v = critic.value(of)
        adv = torch.zeros(T, N, device=DEV); g = torch.zeros(N, device=DEV)
        for t in reversed(range(T)):
            nnt = 1 - b_d[t]; nv = last_v if t == T - 1 else b_v[t + 1]
            delta = b_r[t] + gamma * nv * nnt - b_v[t]; g = delta + gamma * lam * nnt * g; adv[t] = g
        ret = (adv + b_v).reshape(T * N)
        fof = b_of.reshape(T * N, A, od); fot = b_ot.reshape(T * N, A, A, 3)
        fa = b_a.reshape(T * N, A); flp = b_lp.reshape(T * N, A)
        fad = adv.reshape(T * N, 1).expand(T * N, A); fad = (fad - fad.mean()) / (fad.std() + 1e-8)
        idx = np.arange(T * N); mb = (T * N) // mbs
        for _ in range(epochs):
            np.random.shuffle(idx)
            for s in range(0, T * N, mb):
                j = torch.as_tensor(idx[s:s + mb], device=DEV)
                dist = Categorical(logits=actor.logits(fof[j], fot[j]))
                ratio = torch.exp(dist.log_prob(fa[j]) - flp[j]); a_ = fad[j]
                pl = -torch.min(ratio * a_, torch.clamp(ratio, 1 - clip, 1 + clip) * a_).mean()
                vl = ((critic.value(fof[j]) - ret[j]) ** 2).mean(); ent = dist.entropy().mean()
                loss = pl + 0.5 * vl - ent_c * ent
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(list(actor.parameters()) + list(critic.parameters()), 0.5); opt.step()
    # eval au depart COMPLET (le vrai test)
    env.start_lo, env.start_hi = 0, 1; br, cs = [], []; of, ot = env.reset()
    for _ in range(T * 5):
        with torch.no_grad(): a = Categorical(logits=actor.logits(of, ot)).sample()
        (of, ot), r, done, info = env.step(a); dm = done.bool()
        if dm.any(): br.append(info["breached"][dm].mean().item()); cs.append(info["cas"][dm].mean().item())
    return float(np.mean(br)) if br else 0.0, float(np.mean(cs)) if cs else 0.0

if __name__ == "__main__":
    SMOKE = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    ITERS = 10 if SMOKE else 300; SEEDS = [0, 1] if SMOKE else [0, 1, 2, 3, 4, 5]
    print("=== CURRICULUM INVERSE : attention+audace, depart facile->lointain, %d graines ===" % len(SEEDS), flush=True)
    b, c = [], []
    for s in SEEDS:
        br, cs = train_curric(AttnActor, seed=s, iters=ITERS); b.append(br); c.append(cs)
        print("[curric] seed %d -> perce %.2f pertes %.2f" % (s, br, cs), flush=True)
    print(">>> CURRICULUM : perce %.2f +/- %.2f | pertes %.2f  (vs sans-curric 0.67 +/- 0.47)" % (np.mean(b), np.std(b), np.mean(c)), flush=True)
    print("CURRIC_DONE", flush=True)
