"""PROGRAMME DE NUIT HARMATTAN — moteur de file resilient (Blocs 1+2).
Consolide MAAC (multi-graine + sweep) et teste l'idee neuve : curriculum a effectif variable.
Resilient coupure : CSV-cle + reprise. Re-remplit en graines si la file se vide. Deadline.
"""
import sys; sys.path.insert(0, "/home/younes/arma3-marl")
import os, csv, time, numpy as np, torch, torch.nn as nn
from toy2d import VectorizedToy2D
from train_harmattan import ActorCritic

DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
OUT = "/home/younes/maac_nuit"; os.makedirs(OUT, exist_ok=True)
CSVP = os.path.join(OUT, "resultats_nuit_v2.csv")
REPORT = os.path.join(OUT, "RAPPORT_NUIT_v2.md")
O, NACT = 11, 5
EVAL_A = [5, 10, 20, 30, 50, 80, 150]   # jusqu'au MUR DES 150
DEADLINE = time.time() + 7 * 3600

def train_core(cfg, A_set, critic, heads, hidden):
    """Entraine un ActorCritic. A_set=[5] -> fixe ; A_set=[3,5,7,9,12] -> curriculum (attn requis)."""
    envs = {A: VectorizedToy2D(num_envs=cfg["envs"], seed=cfg["seed"] + A, n_agents=A) for A in A_set}
    net = ActorCritic(O, NACT, max(A_set), hidden, critic=critic, heads=heads).to(DEV)
    opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    T, g, lam, cp = cfg["rollout"], cfg["gamma"], cfg["gae"], cfg["cas_pen"]
    use_mask = (critic == "attn")
    ot = {A: torch.as_tensor(envs[A].reset(), dtype=torch.float32, device=DEV) for A in A_set}
    for it in range(cfg["iters"]):
        A = A_set[it % len(A_set)]; env = envs[A]; N = cfg["envs"]; obs_t = ot[A]
        b_obs = torch.zeros(T, N, A, O, device=DEV); b_act = torch.zeros(T, N, A, dtype=torch.long, device=DEV)
        b_logp = torch.zeros(T, N, A, device=DEV); b_rew = torch.zeros(T, N, device=DEV)
        b_val = torch.zeros(T, N, device=DEV); b_done = torch.zeros(T, N, device=DEV)
        b_alive = torch.ones(T, N, A, dtype=torch.bool, device=DEV)
        for t in range(T):
            ca = torch.as_tensor(env.alive, device=DEV)
            with torch.no_grad():
                a, logp = net.act(obs_t); v = net.value(obs_t, mask=(~ca) if use_mask else None)
            nobs, rew, cost, done, info = env.step(a.cpu().numpy())
            b_obs[t] = obs_t; b_act[t] = a; b_logp[t] = logp; b_val[t] = v; b_alive[t] = ca
            b_rew[t] = torch.as_tensor(rew - cp * cost, dtype=torch.float32, device=DEV)
            b_done[t] = torch.as_tensor(done.astype(np.float32), device=DEV)
            obs_t = torch.as_tensor(nobs, dtype=torch.float32, device=DEV)
        ot[A] = obs_t
        with torch.no_grad():
            last_v = net.value(obs_t, mask=(~torch.as_tensor(env.alive, device=DEV)) if use_mask else None)
        adv = torch.zeros(T, N, device=DEV); gae = torch.zeros(N, device=DEV)
        for t in reversed(range(T)):
            nnt = 1.0 - b_done[t]; nv = last_v if t == T - 1 else b_val[t + 1]
            delta = b_rew[t] + g * nv * nnt - b_val[t]; gae = delta + g * lam * nnt * gae; adv[t] = gae
        ret = (adv + b_val).reshape(T * N)
        f_obs = b_obs.reshape(T * N, A, O); f_act = b_act.reshape(T * N, A); f_logp = b_logp.reshape(T * N, A)
        f_alive = b_alive.reshape(T * N, A)
        fa = adv.reshape(T * N, 1).expand(T * N, A).reshape(-1); fa = (fa - fa.mean()) / (fa.std() + 1e-8)
        f_adv = fa.reshape(T * N, A)
        idx = np.arange(T * N); mb = max(1, (T * N) // cfg["minibatches"])
        for _ in range(cfg["epochs"]):
            np.random.shuffle(idx)
            for s0 in range(0, T * N, mb):
                j = torch.as_tensor(idx[s0:s0 + mb], device=DEV)
                oo = f_obs[j]; nlp, ent = net.evaluate(oo, f_act[j])
                ratio = torch.exp(nlp - f_logp[j]); a_ = f_adv[j]
                ploss = -torch.min(ratio * a_, torch.clamp(ratio, 1 - cfg["clip"], 1 + cfg["clip"]) * a_).mean()
                vloss = ((net.value(oo, mask=(~f_alive[j]) if use_mask else None) - ret[j]) ** 2).mean()
                loss = ploss + cfg["vf"] * vloss - cfg["ent"] * ent.mean()
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(net.parameters(), 0.5); opt.step()
    return net

def eval_net(net, eval_A, n_envs=512, max_steps=80):
    env = VectorizedToy2D(num_envs=n_envs, n_agents=eval_A, grid=12, seed=999)   # grille FIXE = geometrie constante (test juste)
    obs = torch.as_tensor(env.reset(), dtype=torch.float32, device=DEV); net.eval()
    succ, cas = [], []; ep = np.zeros(env.N)
    for _ in range(max_steps * 6):
        with torch.no_grad():
            a = net.actor(obs).argmax(-1).cpu().numpy()
        nobs, r, c, d, info = env.step(a); ep += c
        for n in np.where(d)[0]:
            succ.append(float(info["success"][n])); cas.append(ep[n]); ep[n] = 0
        obs = torch.as_tensor(nobs, dtype=torch.float32, device=DEV)
        if len(succ) >= 2500: break
    return (float(np.mean(succ)) if succ else float("nan"), float(np.mean(cas)) if cas else float("nan"))

# Grille : (label, critic, heads, hidden, A_set, iters)
GRID = [
    ("concat",      "concat",   4, 64,  [5],              250),  # baseline
    ("deepsets",    "deepsets", 4, 64,  [5],              250),  # ABLATION : pooling sans attention
    ("attn_fix",    "attn",     4, 64,  [5],              250),  # attention relationnelle
    ("attn_h1",     "attn",     1, 64,  [5],              250),
    ("attn_h2",     "attn",     2, 64,  [5],              250),
    ("attn_h8",     "attn",     8, 64,  [5],              250),
    ("attn_H128",   "attn",     4, 128, [5],              250),
    ("attn_curric", "attn",     4, 64,  [3, 5, 7, 9, 12], 600),  # IDEE NEUVE : curriculum effectif variable
    ("deep_curric", "deepsets", 4, 64,  [3, 5, 7, 9, 12], 600),  # curriculum SANS attention (controle)
]
BASE = dict(iters=250, envs=256, rollout=32, lr=3e-4, cas_pen=0.5, gamma=0.99, gae=0.95,
            clip=0.2, epochs=4, minibatches=4, vf=0.5, ent=0.01)

def key(label, seed): return "%s|s%d" % (label, seed)

def done_keys():
    s = set()
    if os.path.exists(CSVP):
        for row in csv.DictReader(open(CSVP)):
            s.add(row["key"])
    return s

def append_row(d):
    new = not os.path.exists(CSVP)
    with open(CSVP, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(d.keys()))
        if new: w.writeheader()
        w.writerow(d)

def write_report():
    if not os.path.exists(CSVP): return
    rows = list(csv.DictReader(open(CSVP)))
    labels = [g[0] for g in GRID]
    agg = {}
    for lb in labels:
        rs = [r for r in rows if r["label"] == lb]
        if not rs: continue
        agg[lb] = {}
        for k in EVAL_A:
            cs = [float(r["cas_A%d" % k]) for r in rs if r.get("cas_A%d" % k) not in (None, "", "nan")]
            ss = [float(r["succ_A%d" % k]) for r in rs if r.get("succ_A%d" % k) not in (None, "", "nan")]
            agg[lb][k] = (np.mean(ss) if ss else float("nan"), np.mean(cs) if cs else float("nan"),
                          np.std(cs) if cs else 0.0, len(rs))
    with open(REPORT, "w") as f:
        f.write("# RAPPORT DE NUIT — MAAC (toy2d)\n\n")
        f.write("Genere a %s. Total runs: %d.\n\n" % (time.strftime("%Y-%m-%d %H:%M"), len(rows)))
        f.write("## Pertes par episode (moyenne +/- ecart-type sur graines), entraine puis joue a A=...\n\n")
        f.write("| config | n | " + " | ".join("A=%d" % k for k in EVAL_A) + " |\n")
        f.write("|" + "---|" * (len(EVAL_A) + 2) + "\n")
        for lb in labels:
            if lb not in agg: continue
            n = agg[lb][EVAL_A[0]][3]
            cells = []
            for k in EVAL_A:
                s, c, sd, _ = agg[lb][k]
                cells.append("%.2f±%.2f" % (c, sd))
            f.write("| %s | %d | %s |\n" % (lb, n, " | ".join(cells)))
        f.write("\n## Reussite (objectif securise)\n\n")
        f.write("| config | " + " | ".join("A=%d" % k for k in EVAL_A) + " |\n")
        f.write("|" + "---|" * (len(EVAL_A) + 1) + "\n")
        for lb in labels:
            if lb not in agg: continue
            cells = ["%.2f" % agg[lb][k][0] for k in EVAL_A]
            f.write("| %s | %s |\n" % (lb, " | ".join(cells)))
        f.write("\n**Lecture clef** : comparer `concat` vs `attn_fix` (gain de l'attention) ")
        f.write("et `attn_fix` vs `attn_curric` (gain du curriculum a effectif variable, impossible en concat).\n")

def run_one(entry, seed):
    label, critic, heads, hidden, A_set, iters = entry
    cfg = dict(BASE); cfg["seed"] = seed; cfg["iters"] = iters
    net = train_core(cfg, A_set, critic, heads, hidden)
    row = dict(key=key(label, seed), label=label, critic=critic, heads=heads, hidden=hidden,
               curric=int(len(A_set) > 1), seed=seed, t=time.strftime("%H:%M"))
    for k in EVAL_A:
        s, c = eval_net(net, k); row["succ_A%d" % k] = "%.3f" % s; row["cas_A%d" % k] = "%.3f" % c
    append_row(row); write_report()
    del net; torch.cuda.empty_cache() if DEV == "cuda:0" else None
    return row

def night_loop():
    print("=== PROGRAMME DE NUIT MAAC demarre %s ===" % time.strftime("%H:%M"), flush=True)
    SEEDS = list(range(0, 6))
    while time.time() < DEADLINE:
        did = 0; dk = done_keys()
        for seed in SEEDS:
            for entry in GRID:
                if time.time() >= DEADLINE: break
                if key(entry[0], seed) in dk: continue
                t0 = time.time()
                print("[%s] %s seed=%d ..." % (time.strftime("%H:%M"), entry[0], seed), flush=True)
                try:
                    r = run_one(entry, seed); did += 1
                    print("   -> A30 pertes=%s A50 pertes=%s (%.0fs)" % (r.get("cas_A30"), r.get("cas_A50"), time.time() - t0), flush=True)
                except Exception as e:
                    import traceback; print("   ERR:", e, flush=True); traceback.print_exc()
        if did == 0:
            SEEDS = list(range(len(SEEDS), len(SEEDS) + 6))
            print("[%s] file vide -> +6 graines (total %d)" % (time.strftime("%H:%M"), SEEDS[-1] + 1), flush=True)
    print("=== NUIT_FIN %s ===" % time.strftime("%H:%M"), flush=True)

if __name__ == "__main__":
    night_loop()
