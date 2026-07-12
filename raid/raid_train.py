#!/usr/bin/env python3
"""raid_train.py — BOUCLE D'APPRENTISSAGE MAPPO pour le RAID FS (HARMATTAN, Brique 2).
Acteur par agent : ATTENTION sur les coequipiers + PORTE D'AUDACE (g module le poids de l'attention)
+ tete d'ALLOCATION facon pointeur (choisir lequel des 10 sous-objectifs viser).
Critique CENTRAL (MAPPO) : voit l'etat global d'equipe. Recompense d'equipe partagee, GAE, PPO clip.
  --mock  : env factice rapide (valide toute la mecanique sans Arma)
  --slots : serveurs Arma a utiliser en parallele (ex. 2,3)
Pilote l'env RaidEnv (raid_env.py) ; Arma est le goulot -> tourne sur CPU."""
import os, sys, argparse, math, random, time, threading
from contextlib import nullcontext
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
sys.path.insert(0, "/home/younes/arma3-marl/raid")

N_SF = 20; N_SUBOBJ = 10; N_MATE = N_SF - 1
F_SELF = 8; F_SUB = 5; F_MATE = 4; F_GLOB = F_SELF + 3   # F_SELF +1 = dist ennemi ; glob = moy(self_f)+[alerte,tenus,frac]
N_DEST = N_SUBOBJ + 1; N_POST = 3                   # destination (10 sous-obj + tenir) ; posture (debout/accroupi/couche)
DEV = "cpu"

# ---------------- construction de l'observation depuis l'etat brut ----------------
def build_obs(env, st):
    """st = (sf, df, al). Renvoie tenseurs par agent + masque vivants + feat globale critique."""
    sf, df, al = st["sf"], st["def"], st["alert"]
    ox, oy = env.obj; sub = env.subobj; held = st["held"]
    n_alive = max(1, sum(a[2] for a in sf)); frac = n_alive / N_SF; nheld = sum(held)
    self_f = np.zeros((N_SF, F_SELF), np.float32)
    sub_f = np.zeros((N_SF, N_SUBOBJ, F_SUB), np.float32)
    mate_f = np.zeros((N_SF, N_MATE, F_MATE), np.float32)
    alive = np.zeros(N_SF, np.float32)
    for i, a in enumerate(sf):
        ax, ay, al_i = a[0], a[1], a[2]; alive[i] = al_i
        d_obj = math.hypot(ax - ox, ay - oy)
        nd = min([math.hypot(ax - dx, ay - dy) for dx, dy in df], default=1000.0)   # distance ennemi le plus proche
        self_f[i] = [(ax - ox) / 1000, (ay - oy) / 1000, al_i, al / 4.0, d_obj / 1000, nheld / 10.0, frac, min(nd, 1000) / 1000]
        for k, (sx, sy) in enumerate(sub):
            d = math.hypot(ax - sx, ay - sy)
            dfn = 1.0 if any(math.hypot(dx - sx, dy - sy) < 40 for dx, dy in df) else 0.0
            sub_f[i, k] = [1.0 if held[k] else 0.0, (sx - ax) / 1000, (sy - ay) / 1000, d / 1000, dfn]
        j = 0
        for q, b in enumerate(sf):
            if q == i: continue
            mate_f[i, j] = [(b[0] - ax) / 1000, (b[1] - ay) / 1000, b[2], math.hypot(b[0] - ax, b[1] - ay) / 1000]
            j += 1
    glob = np.concatenate([self_f.mean(0), [al / 4.0, nheld / 10.0, frac]]).astype(np.float32)  # 7+3
    return self_f, sub_f, mate_f, alive, glob

# ---------------- reseau : acteur (attention + audace + pointeur) + critique central ----------------
class RaidAC(nn.Module):
    def __init__(self, d=64, heads=4):
        super().__init__()
        self.self_enc = nn.Sequential(nn.Linear(F_SELF, d), nn.ReLU(), nn.Linear(d, d))
        self.mate_enc = nn.Sequential(nn.Linear(F_MATE, d), nn.ReLU())
        self.attn = nn.MultiheadAttention(d, heads, batch_first=True)
        self.gate = nn.Sequential(nn.Linear(F_SELF, d), nn.ReLU(), nn.Linear(d, 1))   # porte d'audace
        self.sub_enc = nn.Sequential(nn.Linear(F_SUB, d), nn.ReLU())
        self.ptr = nn.Sequential(nn.Linear(2 * d, d), nn.ReLU(), nn.Linear(d, 1))      # logit par sous-obj
        self.hold = nn.Linear(d, 1)                                                    # logit "tenir la position"
        self.posture = nn.Sequential(nn.Linear(d, d), nn.ReLU(), nn.Linear(d, N_POST)) # tete POSTURE (exposition/feu)
        self.critic = nn.Sequential(nn.Linear(F_GLOB, d), nn.ReLU(), nn.Linear(d, d), nn.ReLU(), nn.Linear(d, 1))
        self.last_g = None

    def actor(self, self_f, sub_f, mate_f):
        # self_f [B,N,7] sub_f [B,N,10,5] mate_f [B,N,19,4]  -> logits [B,N,10]
        B, N = self_f.shape[:2]
        s = self.self_enc(self_f)                                  # [B,N,d]
        m = self.mate_enc(mate_f.reshape(B * N, N_MATE, F_MATE))   # [B*N,19,d]
        q = s.reshape(B * N, 1, -1)
        att, _ = self.attn(q, m, m)                                # [B*N,1,d]
        att = att.reshape(B, N, -1)
        g = torch.sigmoid(self.gate(self_f))                       # [B,N,1] ; bas=audacieux=ignore coequipiers
        self.last_g = g.detach()
        h = s + g * att                                            # attention MODULEE par l'audace
        z = self.sub_enc(sub_f)                                    # [B,N,10,d]
        hexp = h.unsqueeze(2).expand(-1, -1, N_SUBOBJ, -1)         # [B,N,10,d]
        sub_logits = self.ptr(torch.cat([hexp, z], -1)).squeeze(-1)    # [B,N,10]
        dest_logits = torch.cat([sub_logits, self.hold(h)], -1)        # [B,N,11] (+ tenir la position)
        post_logits = self.posture(h)                                  # [B,N,3] posture
        return dest_logits, post_logits

    def value(self, glob):                                        # glob [B,10] -> [B]
        return self.critic(glob).squeeze(-1)

# ---------------- env factice (validation hors-Arma) ----------------
class MockEnv:
    def __init__(self, slot=0, obj_center=(14038, 16143), seed=0):
        self.obj = obj_center; self.slot = slot; self.rng = random.Random(seed)
        self.subobj = [(obj_center[0] + 180 * math.cos(2 * math.pi * i / N_SUBOBJ),
                        obj_center[1] + 180 * math.sin(2 * math.pi * i / N_SUBOBJ)) for i in range(N_SUBOBJ)]
        self.insertion = (obj_center[0] - 650, obj_center[1] - 650)
    def reset(self):
        ix, iy = self.insertion
        self.pos = [[ix + self.rng.uniform(-20, 20), iy + self.rng.uniform(-20, 20), 1] for _ in range(N_SF)]
        self.held = [False] * N_SUBOBJ; self.alert = 0.0; self.step_i = 0
        self.defs = [[self.obj[0] + self.rng.uniform(-80, 80), self.obj[1] + self.rng.uniform(-80, 80)] for _ in range(44)]
        return self._pack()
    def _pack(self):
        return {"sf": [list(p) for p in self.pos], "def": [list(d) for d in self.defs],
                "alert": self.alert, "held": list(self.held), "n_alive": sum(p[2] for p in self.pos), "subobj": self.subobj}
    def step(self, actions):
        self.step_i += 1
        EXPO = {0: 1.0, 1: 0.6, 2: 0.3}; SPD = {0: 1.0, 1: 0.7, 2: 0.4}    # posture : exposition / vitesse
        for i, (t, post) in enumerate(actions):
            p = self.pos[i]
            if not p[2]: continue
            tx, ty = t; dx, dy = tx - p[0], ty - p[1]; dd = math.hypot(dx, dy) or 1
            s = min(60, dd) * SPD.get(int(post), 0.7); p[0] += dx / dd * s; p[1] += dy / dd * s
            if math.hypot(p[0] - self.obj[0], p[1] - self.obj[1]) < 250: self.alert = min(4, self.alert + 0.5)
            if self.alert > 1 and self.rng.random() < 0.04 * self.alert * EXPO.get(int(post), 0.6): p[2] = 0   # pertes ~ alerte x exposition
        prev = sum(self.held)
        for k, (sx, sy) in enumerate(self.subobj):
            if any(p[2] and math.hypot(p[0] - sx, p[1] - sy) < 35 for p in self.pos): self.held[k] = True
        n_alive = sum(p[2] for p in self.pos); now = sum(self.held)
        r = 10.0 * (now - prev) - 0.1
        done = False; info = {"held": now, "alive": n_alive, "alert": self.alert, "def": len(self.defs)}
        if now >= N_SUBOBJ: r += 100; done = True; info["result"] = "VICTOIRE"
        elif n_alive <= 0: r -= 50; done = True; info["result"] = "ANEANTI"
        elif self.step_i >= 40: done = True; info["result"] = "TEMPS"
        return self._pack(), r, done, info
    def close(self): pass

# ---------------- rollout d'un episode ----------------
def collect_episode(env, net, lock=None, greedy=False):
    st = env.reset()
    if st is None: return None
    SS, SB, SM, GL, AL, AC, LP, VL, RW = [], [], [], [], [], [], [], [], []
    done = False; info = {}
    while not done:
        self_f, sub_f, mate_f, alive, glob = build_obs(env, st)
        ts = torch.tensor(self_f).unsqueeze(0); tb = torch.tensor(sub_f).unsqueeze(0); tm = torch.tensor(mate_f).unsqueeze(0)
        with (lock or nullcontext()), torch.no_grad():
            dl, pl = net.actor(ts, tb, tm); dl = dl.squeeze(0); pl = pl.squeeze(0)   # [N,11], [N,3]
            v = net.value(torch.tensor(glob).unsqueeze(0)).item()
            dd = torch.distributions.Categorical(logits=dl); dp = torch.distributions.Categorical(logits=pl)
            ad = dl.argmax(-1) if greedy else dd.sample()         # [N] destination
            ap = pl.argmax(-1) if greedy else dp.sample()         # [N] posture
            lp = dd.log_prob(ad) + dp.log_prob(ap)                # [N]
        actions = []
        for i in range(N_SF):
            di = int(ad[i])
            xy = env.subobj[di] if di < N_SUBOBJ else (st["sf"][i][0], st["sf"][i][1])   # "tenir" = position actuelle
            actions.append((xy, int(ap[i])))
        st2, r, done, info = env.step(actions)
        SS.append(self_f); SB.append(sub_f); SM.append(mate_f); GL.append(glob)
        AL.append(alive); AC.append(np.stack([ad.numpy(), ap.numpy()], -1)); LP.append(lp.numpy()); VL.append(v); RW.append(r)
        st = st2
        if st is None: break
    return dict(ss=np.array(SS), sb=np.array(SB), sm=np.array(SM), gl=np.array(GL),
                al=np.array(AL), ac=np.array(AC), lp=np.array(LP), vl=np.array(VL), rw=np.array(RW), info=info)

def gae(rw, vl, gamma=0.99, lam=0.95):
    T = len(rw); adv = np.zeros(T, np.float32); last = 0.0
    for t in reversed(range(T)):
        nv = vl[t + 1] if t + 1 < T else 0.0
        delta = rw[t] + gamma * nv - vl[t]
        last = delta + gamma * lam * last; adv[t] = last
    ret = adv + vl
    return adv, ret

# ---------------- mise a jour PPO ----------------
def ppo_update(net, opt, batch, epochs=4, clip=0.2, mb=32, ent_c=0.01, vf_c=0.5):
    ss = torch.tensor(batch["ss"]); sb = torch.tensor(batch["sb"]); sm = torch.tensor(batch["sm"])
    gl = torch.tensor(batch["gl"]); al = torch.tensor(batch["al"]); ac = torch.tensor(batch["ac"]).long()
    oldlp = torch.tensor(batch["lp"]); adv = torch.tensor(batch["adv"]); ret = torch.tensor(batch["ret"])
    adv = (adv - adv.mean()) / (adv.std() + 1e-6)
    S = ss.shape[0]; idx = np.arange(S); stats = {}
    for _ in range(epochs):
        np.random.shuffle(idx)
        for s0 in range(0, S, mb):
            b = idx[s0:s0 + mb]
            dl, pl = net.actor(ss[b], sb[b], sm[b])               # [m,N,11], [m,N,3]
            dd = torch.distributions.Categorical(logits=dl); dp = torch.distributions.Categorical(logits=pl)
            lp = dd.log_prob(ac[b][..., 0]) + dp.log_prob(ac[b][..., 1])   # [m,N] (2 tetes)
            ent = dd.entropy() + dp.entropy()                     # [m,N]
            ratio = torch.exp(lp - oldlp[b])
            a = adv[b].unsqueeze(1)                               # [m,1]
            mask = al[b]                                          # [m,N] vivants
            surr = torch.min(ratio * a, torch.clamp(ratio, 1 - clip, 1 + clip) * a)
            pol = -(surr * mask).sum() / mask.sum().clamp(min=1)
            entl = -(ent * mask).sum() / mask.sum().clamp(min=1)
            v = net.value(gl[b]); vfl = F.mse_loss(v, ret[b])
            loss = pol + vf_c * vfl + ent_c * entl
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
            stats = {"pol": float(pol), "vf": float(vfl), "ent": float(-entl)}
    return stats

# ---------------- boucle principale ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--seizehold", action="store_true")   # MISSION : 20 FS prennent+consolident vs 500
    ap.add_argument("--iters", type=int, default=200)
    ap.add_argument("--episodes", type=int, default=2)     # episodes collectes par iteration
    ap.add_argument("--slots", type=str, default="2")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--ckpt", type=str, default="/home/younes/maac_nuit/raid_policy.pt")
    ap.add_argument("--rolldir", type=str, default="/home/younes/maac_nuit/rollouts")   # rollouts Arma -> nourrit le modele du monde (#2)
    a = ap.parse_args()
    torch.manual_seed(0); np.random.seed(0)
    net = RaidAC().to(DEV); opt = torch.optim.Adam(net.parameters(), lr=a.lr)
    netlock = threading.Lock()
    os.makedirs(a.rolldir, exist_ok=True); roll_n = 0
    if a.seizehold:
        sys.path.insert(0, "/home/younes/arma3-marl/raid")
        from fast_seizehold import FastSeizeHold
        envs = [FastSeizeHold(seed=i) for i in range(a.episodes)]
        a.mock = True                                               # meme chemin de controle, pas de boot Arma
    elif a.mock:
        envs = [MockEnv(seed=i) for i in range(a.episodes)]
    else:
        from raid_env import RaidEnv
        slots = [int(s) for s in a.slots.split(",")]
        envs = [RaidEnv(slot=s, verbose=False) for s in slots]      # 1 serveur Arma par slot, collecte en parallele
    print("=== MAPPO RAID | mock=%s | iters=%d | serveurs=%d (%s) ===" % (a.mock, a.iters, len(envs), a.slots), flush=True)
    def _safe(e):
        try: return collect_episode(e, net, netlock)
        except Exception as ex: print("[slot %s] episode KO: %s" % (getattr(e, "slot", "?"), ex), flush=True); return None
    if not a.mock:                                                  # boot ETAGE (evite la tempete de N boots Altis simultanes)
        def _boot_env(e):
            try: e._boot(); return True
            except Exception as ex: print("[slot %s] boot KO: %s" % (e.slot, ex), flush=True); return False
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=6) as bp:
            list(bp.map(_boot_env, envs))
        envs = [e for e in envs if getattr(e, "booted", False)]
        print("serveurs operationnels : %d/%d (boot %.0fs)" % (len(envs), len(slots), time.time() - t0), flush=True)
        if not envs: print("aucun serveur -> abandon", flush=True); return
    best = -1e9
    for it in range(a.iters):
        with ThreadPoolExecutor(max_workers=len(envs)) as pool:
            eps = list(pool.map(_safe, envs))                       # un episode par serveur, en parallele
        eps = [e for e in eps if e is not None]
        for e in eps:                                               # dump rollout (nourrit le modele du monde #2)
            np.savez(os.path.join(a.rolldir, "ep_%06d.npz" % roll_n),
                     ss=e["ss"], sb=e["sb"], sm=e["sm"], ac=e["ac"], rw=e["rw"]); roll_n += 1
        if not eps: print("[it %d] aucune episode (env ?)" % it, flush=True); continue
        SS, SB, SM, GL, AL, AC, LP, ADV, RET = [], [], [], [], [], [], [], [], []
        rets, helds, alives = [], [], []
        for e in eps:
            adv, ret = gae(e["rw"], e["vl"])
            SS.append(e["ss"]); SB.append(e["sb"]); SM.append(e["sm"]); GL.append(e["gl"])
            AL.append(e["al"]); AC.append(e["ac"]); LP.append(e["lp"]); ADV.append(adv); RET.append(ret)
            rets.append(e["rw"].sum()); helds.append(e["info"].get("held", 0)); alives.append(e["info"].get("alive", 0))
        batch = dict(ss=np.concatenate(SS), sb=np.concatenate(SB), sm=np.concatenate(SM), gl=np.concatenate(GL),
                     al=np.concatenate(AL), ac=np.concatenate(AC), lp=np.concatenate(LP),
                     adv=np.concatenate(ADV), ret=np.concatenate(RET))
        stats = ppo_update(net, opt, batch)
        gmean = float(net.last_g.mean()) if net.last_g is not None else 0.0
        mret = float(np.mean(rets))
        fps0 = (envs[0].fps() if (not a.mock and envs) else 0) or 0
        print("[it %3d] retour=%+7.1f  tenus=%.1f/10  vivants=%.1f/20  audace_g=%.2f  ep=%d/%d fps=%d  pol=%.3f vf=%.1f ent=%.2f" % (
            it, mret, float(np.mean(helds)), float(np.mean(alives)), gmean, len(eps), len(envs), int(fps0),
            stats.get("pol", 0), stats.get("vf", 0), stats.get("ent", 0)), flush=True)
        if mret > best:
            best = mret; torch.save(net.state_dict(), a.ckpt)
        if it % 10 == 0: torch.save(net.state_dict(), a.ckpt + ".last")
    for e in envs:
        try: e.close()
        except Exception: pass
    print("MAPPO_DONE best=%.1f" % best, flush=True)

if __name__ == "__main__":
    main()
