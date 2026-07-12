"""KOTH — test d'ECHELLE sur l'env de combat REEL. Reutilise les cerveaux entraines a n=3
(par koth_night.py) et les fait jouer a n=3/6/12/24 sans reentrainer. Cross-play tete-a-tete :
1 cerveau ATTENTION (camp 0) vs 2 CONCAT (camps 1,2). 3 camps symetriques -> hasard=0.33.
Si le taux de victoire de l'attention TIENT ou MONTE avec n -> l'attention scale sur le vrai env.
"""
import sys; sys.path.insert(0, "/home/younes/arma3-marl")
import os, csv, time, numpy as np, torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net, NetAttn

DEV = "cuda:0"; OUT = "/home/younes/maac_nuit"
CSVP = os.path.join(OUT, "koth_scale.csv"); REPORT = os.path.join(OUT, "KOTH_SCALE_RAPPORT.md")
HID, LAY, HEADS, SEEDS, NVAL = 512, 3, 4, [0, 1, 2], [3, 6, 12, 24]

def bpath(kind, seed): return "/home/younes/arma3-marl/kn_%s_s%d_blu.pt" % (kind, seed)

def dims(n):
    e = KothGPU(num_envs=2, n=n, device=DEV, seed=0); d = (e.obs_dim, e.n_actions); del e; return d

def load_brain(kind, seed, O, NA):
    net = (NetAttn(O, NA, HID, LAY, HEADS) if kind == "attn" else Net(O, NA, HID, LAY)).to(DEV)
    net.load_state_dict(torch.load(bpath(kind, seed), map_location=DEV)); net.eval(); return net

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
    with open(CSVP, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["n", "test", "seed", "vs", "winrate", "dec"]); w.writeheader(); w.writerows(rows)
    with open(REPORT, "w") as f:
        f.write("# KOTH — test d'ECHELLE sur l'env REEL (entraine n=3, joue a n grand, sans reentrainer)\n\n")
        f.write("Genere %s. Cross-play : 1 cerveau **ATTENTION** (camp 0) vs 2 **CONCAT** (camps 1,2). Hasard = **0.33**.\n\n" % time.strftime("%Y-%m-%d %H:%M"))
        f.write("| n agents/camp | taux victoire ATTN | ± | n_runs |\n|---|---|---|---|\n")
        for n in NVAL:
            wr = [float(r["winrate"]) for r in rows if r["n"] == n and r["test"] == "attn_vs_2concat"]
            if wr: f.write("| %d | **%.3f** | %.3f | %d |\n" % (n, np.mean(wr), np.std(wr), len(wr)))
        f.write("\n**Lecture** : si le taux TIENT/MONTE quand n grandit, l'attention scale sur le vrai env de combat (vs la concat qui decroche).\n")

def main():
    print("=== KOTH SCALE TEST (env reel) demarre %s ===" % time.strftime("%H:%M"), flush=True)
    miss = [(k, s) for k in ["attn", "concat"] for s in SEEDS if not os.path.exists(bpath(k, s))]
    if miss:
        print("ATTENTION cerveaux manquants (koth_night pas fini ?):", miss, flush=True)
    rows = []
    for n in NVAL:
        O, NA = dims(n)
        for a_s in SEEDS:
            for pair in [(0, 1), (1, 2), (2, 0)]:
                try:
                    br = [load_brain("attn", a_s, O, NA), load_brain("concat", pair[0], O, NA), load_brain("concat", pair[1], O, NA)]
                    wr, dec = crossplay(br, n)
                    rows.append(dict(n=n, test="attn_vs_2concat", seed=a_s, vs=str(pair), winrate="%.3f" % wr[0], dec=dec))
                    print("[%s] n=%d ATTN(s%d) vs concat%s -> %.3f (dec %d)" % (time.strftime("%H:%M"), n, a_s, pair, wr[0], dec), flush=True)
                except Exception as e:
                    import traceback; print("ERR n=%d s%d: %s" % (n, a_s, e), flush=True); traceback.print_exc()
        write_report(rows)
        print("[%s] n=%d termine, rapport mis a jour" % (time.strftime("%H:%M"), n), flush=True)
    print("=== KOTH_SCALE_DONE %s ===" % time.strftime("%H:%M"), flush=True)

if __name__ == "__main__":
    main()
