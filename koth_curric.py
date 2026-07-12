"""KOTH — CURRICULUM a effectif variable sur l'env REEL. Teste si le vrai resultat de toy2d
(le curriculum bat le fixe a grande echelle) TRANSFERE sur le vrai env de combat.
Entraine un cerveau sur n=3,6,9,12 (round-robin), puis cross-play contre 2 cerveaux FIXES-n3
(de koth_night) a n=3/6/12/24. >0.33 = le curriculum domine le fixe a cette echelle.
"""
import sys; sys.path.insert(0, "/home/younes/arma3-marl")
import os, csv, time, numpy as np, torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net, NetAttn, ppo_mb

DEV = "cuda:0"; OUT = "/home/younes/maac_nuit"
HID, LAY, HEADS = 512, 3, 4
SMOKE = os.environ.get("SMOKE", "0") == "1"
ENVS = 2048 if SMOKE else 8192
ITERS = 6 if SMOKE else 220
N_SET = [3, 6, 9, 12]
EVAL_N = [3, 6, 12, 24]

def make_net(critic, O, NA):
    return (NetAttn(O, NA, HID, LAY, HEADS) if critic == "attn" else Net(O, NA, HID, LAY)).to(DEV)

def train_curric(critic, seed):
    cfg = dict(gamma=0.99, gae=0.95, clip=0.2, epochs=4, vf=0.5, ent=0.01)
    envs = {n: KothGPU(num_envs=ENVS, n=n, device=DEV, seed=seed + n) for n in N_SET}
    e0 = envs[N_SET[0]]; C, O, NA = e0.C, e0.obs_dim, e0.n_actions
    nets = [make_net(critic, O, NA) for _ in range(C)]
    opts = [torch.optim.Adam(nets[c].parameters(), lr=3e-4) for c in range(C)]
    ot = {n: list(envs[n].reset()) for n in N_SET}
    t0 = time.time(); gstep = 0; T = 16; mb = 32768
    for it in range(ITERS):
        n = N_SET[it % len(N_SET)]; env = envs[n]; N = ENVS; A = n; obs = ot[n]
        B = [dict(obs=torch.zeros(T, N, A, O, device=DEV), act=torch.zeros(T, N, A, dtype=torch.long, device=DEV),
                  logp=torch.zeros(T, N, A, device=DEV), rew=torch.zeros(T, N, device=DEV),
                  val=torch.zeros(T, N, device=DEV), done=torch.zeros(T, N, device=DEV)) for _ in range(C)]
        for t in range(T):
            with torch.no_grad():
                acts = []
                for c in range(C):
                    dd = Categorical(logits=nets[c].a_logits(obs[c])); a = dd.sample()
                    B[c]["obs"][t] = obs[c]; B[c]["act"][t] = a; B[c]["logp"][t] = dd.log_prob(a); B[c]["val"][t] = nets[c].value(obs[c])
                    acts.append(a)
            nobs, rews, done, info = env.step(acts)
            for c in range(C): B[c]["rew"][t] = rews[c]; B[c]["done"][t] = done
            obs = list(nobs); gstep += N
        ot[n] = obs
        for c in range(C):
            with torch.no_grad(): lv = nets[c].value(obs[c])
            ppo_mb(nets[c], opts[c], B[c], lv, cfg, DEV, mb)
        if it % 20 == 0:
            print("[%s] curric %s it %d n=%d %.0f tr/s" % (time.strftime("%H:%M"), critic, it, n, gstep / (time.time() - t0)), flush=True)
    p = "/home/younes/arma3-marl/kn_cur_%s_blu.pt" % critic
    torch.save(nets[0].state_dict(), p); print("sauve", p, flush=True); return p

def load_brain(path, critic, O, NA):
    net = make_net(critic, O, NA); net.load_state_dict(torch.load(path, map_location=DEV)); net.eval(); return net

def crossplay(brains, n, n_envs=4096, steps=320):
    env = KothGPU(num_envs=n_envs, n=n, device=DEV, seed=4242); obs = env.reset(); C = env.C
    wins = [0] * C; dec = 0
    for _ in range(steps):
        with torch.no_grad():
            acts = [Categorical(logits=brains[c].a_logits(obs[c])).sample() for c in range(C)]
        obs, rews, done, info = env.step(acts); dm = done.bool()
        for c in range(C): wins[c] += int(((info["winner"] == c) & dm).sum().item())
        dec += int((info["decided"] & dm).sum().item())
    return [w / dec if dec else 0.0 for w in wins], dec

def write_report(rows):
    with open(os.path.join(OUT, "koth_curric.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["critic", "n", "vs", "curric_winrate", "dec"]); w.writeheader(); w.writerows(rows)
    with open(os.path.join(OUT, "KOTH_CURRIC_RAPPORT.md"), "w") as f:
        f.write("# KOTH — le CURRICULUM d'effectif variable bat-il le FIXE sur le VRAI env ?\n\n")
        f.write("Genere %s. Cross-play : cerveau **CURRICULUM** (n=3..12, camp 0) vs 2 cerveaux **FIXES-n3** (camps 1,2).\n" % time.strftime("%Y-%m-%d %H:%M"))
        f.write("Hasard = **0.33**. >0.33 = le curriculum domine le fixe a cette echelle.\n\n")
        for critic in ["concat", "attn"]:
            f.write("## archi = %s\n\n| n agents/camp | victoire CURRICULUM vs fixe | n_runs |\n|---|---|---|\n" % critic)
            for n in EVAL_N:
                wr = [float(r["curric_winrate"]) for r in rows if r["critic"] == critic and r["n"] == n]
                if wr: f.write("| %d | **%.3f** ± %.3f | %d |\n" % (n, np.mean(wr), np.std(wr), len(wr)))
            f.write("\n")
        f.write("**Lecture** : si le curriculum MONTE au-dessus de 0.33 quand n grandit, le resultat toy2d TRANSFERE sur le vrai env de combat.\n")

def main():
    print("=== KOTH CURRICULUM (env reel) %s SMOKE=%s ===" % (time.strftime("%H:%M"), SMOKE), flush=True)
    e = KothGPU(num_envs=2, n=3, device=DEV, seed=0); O, NA = e.obs_dim, e.n_actions; del e
    rows = []
    for critic in ["concat", "attn"]:
        try:
            cur = train_curric(critic, 0)
            for n in EVAL_N:
                for pair in [(1, 2), (2, 1)]:
                    fp = ["/home/younes/arma3-marl/kn_%s_s%d_blu.pt" % (critic, s) for s in pair]
                    if not all(os.path.exists(p) for p in fp):
                        print("fixe manquant pour %s (koth_night ?)" % critic, flush=True); continue
                    br = [load_brain(cur, critic, O, NA), load_brain(fp[0], critic, O, NA), load_brain(fp[1], critic, O, NA)]
                    wr, dec = crossplay(br, n)
                    rows.append(dict(critic=critic, n=n, vs=str(pair), curric_winrate="%.3f" % wr[0], dec=dec))
                    print("[%s] %s n=%d CURRIC vs 2 fixe -> %.3f (dec %d)" % (time.strftime("%H:%M"), critic, n, wr[0], dec), flush=True)
            write_report(rows)
        except Exception as ex:
            import traceback; print("ERR critic %s: %s" % (critic, ex), flush=True); traceback.print_exc()
    print("=== KOTH_CURRIC_DONE %s ===" % time.strftime("%H:%M"), flush=True)

if __name__ == "__main__":
    main()
