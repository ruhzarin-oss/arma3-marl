"""Campagne de nuit KOTH (env reel) — Bloc 3. Attention (MAAC) vs concatenation/baseline.
Entraine concat & attn en self-play (resumable : saute si cerveau deja sauve), puis CROSS-PLAY
tete-a-tete : 1 cerveau ATTN (camp 0) contre 2 CONCAT (camps 1,2). 3 camps symetriques -> hasard=0.33.
Resilient : reprise sur fichiers .pt, rapport reecrit a la fin.
"""
import sys; sys.path.insert(0, "/home/younes/arma3-marl")
import os, csv, time, numpy as np, torch
from torch.distributions import Categorical
from koth_gpu import KothGPU
from train_koth_gpu import Net, NetAttn, train

DEV = "cuda:0"; OUT = "/home/younes/maac_nuit"; os.makedirs(OUT, exist_ok=True)
CSVP = os.path.join(OUT, "koth_resultats.csv"); REPORT = os.path.join(OUT, "KOTH_RAPPORT.md")
ENVS, ITERS, SEEDS, HID, LAY, HEADS = 8192, 160, [0, 1, 2], 512, 3, 4

def bpath(kind, seed): return "/home/younes/arma3-marl/kn_%s_s%d_blu.pt" % (kind, seed)

def train_one(kind, seed):
    if os.path.exists(bpath(kind, seed)):
        print("[%s] %s s%d deja entraine, saute" % (time.strftime("%H:%M"), kind, seed), flush=True); return
    print("[%s] TRAIN %s s%d (env reel, %d envs, %d it)" % (time.strftime("%H:%M"), kind, seed, ENVS, ITERS), flush=True)
    train(iters=ITERS, envs=ENVS, rollout=16, hidden=HID, layers=LAY, mb=32768,
          seed=seed, save="kn_%s_s%d" % (kind, seed), attn=(kind == "attn"), heads=HEADS)

def env_dims():
    e = KothGPU(num_envs=2, device=DEV, seed=0); d = (e.obs_dim, e.n_actions, e.C); del e; return d

def load_brain(kind, seed, O, NA):
    net = (NetAttn(O, NA, HID, LAY, HEADS) if kind == "attn" else Net(O, NA, HID, LAY)).to(DEV)
    net.load_state_dict(torch.load(bpath(kind, seed), map_location=DEV)); net.eval(); return net

def crossplay(brains, n_envs=8192, steps=300):
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
    print("=== CAMPAGNE KOTH (env reel) demarre %s ===" % time.strftime("%H:%M"), flush=True)
    for kind in ["concat", "attn"]:
        for s in SEEDS:
            try: train_one(kind, s)
            except Exception as e:
                import traceback; print("ERR train %s s%d: %s" % (kind, s, e), flush=True); traceback.print_exc()
    O, NA, C = env_dims()
    rows = []
    # ATTN (camp0) vs 2 CONCAT (camps 1,2)
    for a_s in SEEDS:
        for pair in [(0, 1), (1, 2), (2, 0)]:
            try:
                br = [load_brain("attn", a_s, O, NA), load_brain("concat", pair[0], O, NA), load_brain("concat", pair[1], O, NA)]
                wr, dec = crossplay(br)
                rows.append(dict(test="attn_vs_2concat", seed=a_s, vs=str(pair), winrate="%.3f" % wr[0], dec=dec))
                print("[%s] ATTN(s%d) vs concat%s -> winrate %.3f (dec %d)" % (time.strftime("%H:%M"), a_s, pair, wr[0], dec), flush=True)
            except Exception as e:
                import traceback; print("ERR cross attn s%d %s: %s" % (a_s, pair, e), flush=True); traceback.print_exc()
    # CONTROLE : CONCAT (camp0) vs 2 CONCAT (doit etre ~0.33)
    for c_s in SEEDS:
        try:
            br = [load_brain("concat", c_s, O, NA), load_brain("concat", (c_s + 1) % 3, O, NA), load_brain("concat", (c_s + 2) % 3, O, NA)]
            wr, dec = crossplay(br)
            rows.append(dict(test="concat_ctrl", seed=c_s, vs="ctrl", winrate="%.3f" % wr[0], dec=dec))
            print("[%s] CTRL concat(s%d) -> winrate %.3f" % (time.strftime("%H:%M"), c_s, wr[0]), flush=True)
        except Exception as e:
            print("ERR ctrl s%d: %s" % (c_s, e), flush=True)
    if rows:
        with open(CSVP, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["test", "seed", "vs", "winrate", "dec"]); w.writeheader(); w.writerows(rows)
        av = [float(r["winrate"]) for r in rows if r["test"] == "attn_vs_2concat"]
        cv = [float(r["winrate"]) for r in rows if r["test"] == "concat_ctrl"]
        with open(REPORT, "w") as f:
            f.write("# KOTH (env reel) — Attention (MAAC) vs Concatenation, tete-a-tete\n\n")
            f.write("Genere %s. Cross-play : 1 cerveau **ATTENTION** (camp 0) contre 2 cerveaux **CONCAT** (camps 1,2).\n" % time.strftime("%Y-%m-%d %H:%M"))
            f.write("3 camps symetriques -> le hasard donne **0.33**. Au-dessus = l'attention domine.\n\n")
            f.write("- **Taux de victoire ATTN vs 2 concat : %.3f ± %.3f** (n=%d)\n" % (np.mean(av) if av else float("nan"), np.std(av) if av else 0, len(av)))
            f.write("- Controle concat vs 2 concat : %.3f ± %.3f (sanity ~0.33)\n\n" % (np.mean(cv) if cv else float("nan"), np.std(cv) if cv else 0))
            verdict = "ATTENTION DOMINE sur le vrai env" if (av and np.mean(av) > 0.40) else ("a-egalite/non concluant" if av else "pas de donnees")
            f.write("**Verdict : %s.**\n" % verdict)
    print("=== KOTH_NIGHT_DONE %s ===" % time.strftime("%H:%M"), flush=True)

if __name__ == "__main__":
    main()
