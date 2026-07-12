"""SYSTEME v0 — ETAPE 1 : porter l'ATTENTION DANS L'ACTEUR sur le vrai combat (koth_gpu).
Jusqu'ici l'attention-acteur a gagne sur jouets (CoopNav, CoverHold). On teste le TRANSFERT au combat :
chaque soldat ATTEND ses coequipiers pour decider son geste (pas juste le critique).
Cross-play tete-a-tete : soldats ATTENTION-ACTEUR (camp 0) vs 2 camps SOLDATS PLATS. Hasard=0.33.
>0.33 = la coordination apprise transfere au combat reel.
"""
import sys, os, csv, time, numpy as np, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net, ppo_mb   # Net = soldat plat (baseline) ; ppo_mb = update PPO reutilise

DEV = "cuda:0"; OUT = "/home/younes/maac_nuit"; os.makedirs(OUT, exist_ok=True)
HID, LAY, HEADS = 512, 3, 4
ENVS = int(os.environ.get("ENVS", 8192)); ITERS = int(os.environ.get("ITERS", 160)); SEEDS = [0, 1, 2]

class NetActorAttn(nn.Module):
    """Soldat dont la POLITIQUE attend ses coequipiers (coordination apprise dans l'acteur).
    Critique = moyenne par agent (inchange, comme Net). Acteur = body -> self-attention sur les soldats -> pi."""
    def __init__(self, O, nact, hidden=512, layers=3, heads=4):
        super().__init__()
        body = []; din = O
        for _ in range(layers):
            body += [nn.Linear(din, hidden), nn.ReLU()]; din = hidden
        self.body = nn.Sequential(*body)
        self.attn = nn.MultiheadAttention(hidden, heads, batch_first=True)
        self.ln = nn.LayerNorm(hidden)
        self.pi = nn.Linear(2 * hidden, nact)
        self.v = nn.Linear(hidden, 1)
    def a_logits(self, obs):                 # obs (B,A,O) -> (B,A,nact)
        h = self.body(obs)                   # (B,A,H)
        ctx, _ = self.attn(h, h, h)          # chaque soldat regarde ses coequipiers
        h2 = self.ln(h + ctx)
        return self.pi(torch.cat([h, h2], -1))
    def value(self, obs):
        return self.v(self.body(obs)).squeeze(-1).mean(-1)

def make_net(kind, O, NA):
    return (NetActorAttn(O, NA, HID, LAY, HEADS) if kind == "attn" else Net(O, NA, HID, LAY)).to(DEV)

def bpath(kind, seed): return "/home/younes/arma3-marl/ka_%s_s%d_blu.pt" % (kind, seed)

def train_self(kind, seed):
    if os.path.exists(bpath(kind, seed)):
        print("[%s] %s s%d deja entraine" % (time.strftime("%H:%M"), kind, seed), flush=True); return
    cfg = dict(gamma=0.99, gae=0.95, clip=0.2, epochs=4, vf=0.5, ent=0.01)
    env = KothGPU(num_envs=ENVS, device=DEV, seed=seed)
    C, A, O, NA = env.C, env.A, env.obs_dim, env.n_actions
    nets = [make_net(kind, O, NA) for _ in range(C)]
    opts = [torch.optim.Adam(nets[c].parameters(), lr=3e-4) for c in range(C)]
    ot = list(env.reset()); T = 16; mb = 32768; t0 = time.time(); gstep = 0
    print("[%s] TRAIN %s s%d (%d envs, %d it)" % (time.strftime("%H:%M"), kind, seed, ENVS, ITERS), flush=True)
    for it in range(ITERS):
        B = [dict(obs=torch.zeros(T, ENVS, A, O, device=DEV), act=torch.zeros(T, ENVS, A, dtype=torch.long, device=DEV),
                  logp=torch.zeros(T, ENVS, A, device=DEV), rew=torch.zeros(T, ENVS, device=DEV),
                  val=torch.zeros(T, ENVS, device=DEV), done=torch.zeros(T, ENVS, device=DEV)) for _ in range(C)]
        for t in range(T):
            with torch.no_grad():
                acts = []
                for c in range(C):
                    dd = Categorical(logits=nets[c].a_logits(ot[c])); a = dd.sample()
                    B[c]["obs"][t] = ot[c]; B[c]["act"][t] = a; B[c]["logp"][t] = dd.log_prob(a); B[c]["val"][t] = nets[c].value(ot[c])
                    acts.append(a)
            nobs, rews, done, info = env.step(acts)
            for c in range(C): B[c]["rew"][t] = rews[c]; B[c]["done"][t] = done
            ot = list(nobs); gstep += ENVS
        for c in range(C):
            with torch.no_grad(): lv = nets[c].value(ot[c])
            ppo_mb(nets[c], opts[c], B[c], lv, cfg, DEV, mb)
        if it % 40 == 0: print("[%s]   %s s%d it %d %.0f tr/s" % (time.strftime("%H:%M"), kind, seed, it, gstep / (time.time() - t0)), flush=True)
    torch.save(nets[0].state_dict(), bpath(kind, seed)); print("sauve", bpath(kind, seed), flush=True)

def load_brain(kind, seed, O, NA):
    net = make_net(kind, O, NA); net.load_state_dict(torch.load(bpath(kind, seed), map_location=DEV)); net.eval(); return net

def crossplay(brains, n_envs=4096, steps=320):
    env = KothGPU(num_envs=n_envs, device=DEV, seed=4242); obs = env.reset(); C = env.C
    wins = [0] * C; dec = 0
    for _ in range(steps):
        with torch.no_grad():
            acts = [Categorical(logits=brains[c].a_logits(obs[c])).sample() for c in range(C)]
        obs, rews, done, info = env.step(acts); dm = done.bool()
        for c in range(C): wins[c] += int(((info["winner"] == c) & dm).sum().item())
        dec += int((info["decided"] & dm).sum().item())
    return [w / dec if dec else 0.0 for w in wins], dec

def main():
    print("=== ETAPE 1 : attention-acteur sur koth (transfert combat) SMOKE check ENVS=%d ITERS=%d ===" % (ENVS, ITERS), flush=True)
    for kind in ["plain", "attn"]:
        for s in SEEDS: train_self(kind, s)
    e = KothGPU(num_envs=2, device=DEV, seed=0); O, NA = e.obs_dim, e.n_actions; del e
    rows = []
    for a_s in SEEDS:
        for pair in [(0, 1), (1, 2), (2, 0)]:
            try:
                br = [load_brain("attn", a_s, O, NA), load_brain("plain", pair[0], O, NA), load_brain("plain", pair[1], O, NA)]
                wr, dec = crossplay(br)
                rows.append(dict(test="attn_actor_vs_2plain", seed=a_s, vs=str(pair), winrate="%.3f" % wr[0], dec=dec))
                print("[%s] ATTN-ACTEUR(s%d) vs plats%s -> %.3f (dec %d)" % (time.strftime("%H:%M"), a_s, str(pair), wr[0], dec), flush=True)
            except Exception as ex:
                import traceback; print("ERR", ex, flush=True); traceback.print_exc()
    # controle : plat vs 2 plats
    for c_s in SEEDS:
        try:
            br = [load_brain("plain", c_s, O, NA), load_brain("plain", (c_s + 1) % 3, O, NA), load_brain("plain", (c_s + 2) % 3, O, NA)]
            wr, dec = crossplay(br); rows.append(dict(test="plain_ctrl", seed=c_s, vs="ctrl", winrate="%.3f" % wr[0], dec=dec))
            print("[%s] CTRL plat(s%d) -> %.3f" % (time.strftime("%H:%M"), c_s, wr[0]), flush=True)
        except Exception as ex: print("ERR ctrl", ex, flush=True)
    with open(os.path.join(OUT, "koth_actor_attn.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["test", "seed", "vs", "winrate", "dec"]); w.writeheader(); w.writerows(rows)
    av = [float(r["winrate"]) for r in rows if r["test"] == "attn_actor_vs_2plain"]
    cv = [float(r["winrate"]) for r in rows if r["test"] == "plain_ctrl"]
    with open(os.path.join(OUT, "KOTH_ACTOR_ATTN_RAPPORT.md"), "w") as f:
        f.write("# ETAPE 1 — attention-acteur sur le COMBAT REEL (koth)\n\n")
        f.write("Genere %s. Cross-play : soldats **ATTENTION-ACTEUR** (camp 0) vs 2 camps **PLATS**. Hasard=0.33.\n\n" % time.strftime("%Y-%m-%d %H:%M"))
        f.write("- **Victoire attention-acteur vs 2 plats : %.3f ± %.3f** (n=%d)\n" % (np.mean(av) if av else float("nan"), np.std(av) if av else 0, len(av)))
        f.write("- Controle plat vs 2 plats : %.3f ± %.3f (~0.33 attendu)\n\n" % (np.mean(cv) if cv else float("nan"), np.std(cv) if cv else 0))
        f.write("**>0.33 nettement = la coordination apprise (attention-acteur) TRANSFERE au combat reel.**\n")
    print("=== KOTH_ACTOR_ATTN_DONE %s ===" % time.strftime("%H:%M"), flush=True)

if __name__ == "__main__":
    main()
