"""run_geo — v4 CIVILS : valider les dynamiques (tout scripté).
Mesures v3 : type de fin (2-collines / élimination / timeout), durée par type, configuration gagnante,
rotation des collines, territoire du vainqueur, winrate par doctrine (fins décisives).
Mesures v4 (civils) : MORTS (cumul/pop initiale), RÉFUGIÉS (déplacements cumulés/pop initiale),
SURVIVANTS (pop finale/initiale), part de la pop mondiale CONTRÔLÉE par le vainqueur (Pyrrhus-check)."""
import time, argparse, torch
from geo_gpu import GeoGPU

p = argparse.ArgumentParser()
p.add_argument("--envs", type=int, default=8192); p.add_argument("--countries", type=int, default=3)
p.add_argument("--arc", type=int, default=4); p.add_argument("--steps", type=int, default=400)
p.add_argument("--hold", type=int, default=5, help="pas consécutifs à 2 collines pour gagner")
p.add_argument("--doctrines", type=str, default=None, help="une lettre A/E/Z par pays, ex. AEZ")
p.add_argument("--summary", action="store_true", help="une seule ligne de bilan (pour sweep)")
a = p.parse_args()

dev = "cuda:0"
env = GeoGPU(num_envs=a.envs, n_countries=a.countries, arc=a.arc, hold_T=a.hold, doctrines=a.doctrines, device=dev, seed=0)
print("GEO v3 | envs=%d | %d pays × arc %d = %d régions | doctrines %s | collines %s capitales %s | victoire = 2 collines × %d pas | max_steps=%d"
      % (a.envs, env.C, env.arc, env.R, env.doctrines, env.hill.tolist(), env.capital.tolist(), env.hold_T, env.max_steps), flush=True)
wins = torch.zeros(env.C, device=dev)            # victoires DÉCISIVES (2COLL+ÉLIM) par pays
t0 = time.time(); gstep = 0
Z = lambda: torch.zeros((), device=dev)
win_terr, done_n = Z(), Z()
d_hill, n_hill = Z(), Z()      # durée et nombre des fins par 2-collines
d_elim, n_elim = Z(), Z()      # ... par élimination
n_tout = Z()                   # timeouts
own_w = Z()                    # parmi les victoires 2-collines : le vainqueur tient SA colline
elim_s = Z()
hprev = None; flips = Z(); flip_n = Z()
S = {"n": 0.0, "hill": 0.0, "elim": 0.0, "tout": 0.0, "dh": 0.0, "de": 0.0, "own": 0.0, "vainq": 0.0, "fl": 0.0, "fln": 0.0,
     "morts": 0.0, "refug": 0.0, "surv": 0.0, "wpop": 0.0}
for it in range(a.steps):
    done, info = env.step(auto_reset=False)
    terr = info["terr"]; nal = info["nalive"]; dm = done.bool()
    hills = info["hills"]                                      # (N, C) propriétaire de la colline de chaque pays
    if hprev is not None:                                      # rotation : collines qui changent de mains
        live = (~dm).float()
        f = ((hills != hprev).float().sum(1) * live).sum()
        flips += f; flip_n += live.sum() * env.C
        S["fl"] += f.item(); S["fln"] += (live.sum() * env.C).item()
    hprev = hills.clone()
    if dm.any():
        idx = dm.nonzero(as_tuple=True)[0]
        w = info["winner"][idx]; wb = info["win_by"][idx]; tt = env.t[idx].float()
        win_terr += (terr[idx].max(1).values / env.R).sum(); done_n += idx.numel()
        elim_s += (env.C - nal[idx]).float().sum()
        h = wb == 0; e = wb == 1
        n_hill += h.float().sum(); d_hill += (tt * h.float()).sum()
        n_elim += e.float().sum(); d_elim += (tt * e.float()).sum()
        n_tout += (wb == 2).float().sum()
        own = (hills[idx, w] == w) & h                          # victoire 2-collines AVEC sa propre colline
        own_w += own.float().sum()
        dec = wb < 2                                            # fins décisives : qui gagne, par pays
        for c in range(env.C): wins[c] += ((w == c) & dec).float().sum()
        pc = info["pop_c"][idx]; ptot = pc.sum(1)               # civils : morts, réfugiés, survivants, Pyrrhus
        S["morts"] += (info["civ_dead"][idx] / env.pop0_total).sum().item()
        S["refug"] += (info["civ_moved"][idx] / env.pop0_total).sum().item()
        S["surv"] += (ptot / env.pop0_total).sum().item()
        S["wpop"] += (pc[torch.arange(idx.numel(), device=dev), w] / ptot.clamp(min=1e-6)).sum().item()
        S["n"] += idx.numel(); S["hill"] += h.float().sum().item(); S["elim"] += e.float().sum().item()
        S["tout"] += (wb == 2).float().sum().item()
        S["dh"] += (tt * h.float()).sum().item(); S["de"] += (tt * e.float()).sum().item()
        S["own"] += own.float().sum().item(); S["vainq"] += (terr[idx].max(1).values / env.R).sum().item()
    if not a.summary and (it % 25 == 0 or it == a.steps - 1):
        dn = done_n.item(); nh = n_hill.item(); ne = n_elim.item(); fn = flip_n.item()
        print("it %3d | vivants %.2f | flip/colline/pas %.3f | [finies: 2COLL %.2f (durée %.0f, sa-colline %.2f) | ÉLIM %.2f (durée %.0f) | timeout %.2f | vainq terr %.2f] | %.0f tr/s"
              % (it, nal.float().mean().item(), (flips.item() / fn if fn else 0),
                 (nh / dn if dn else 0), (d_hill.item() / nh if nh else 0), (own_w.item() / nh if nh else 0),
                 (ne / dn if dn else 0), (d_elim.item() / ne if ne else 0),
                 (n_tout.item() / dn if dn else 0), (win_terr.item() / dn if dn else 0),
                 gstep / (time.time() - t0)), flush=True)
        for z in (win_terr, done_n, d_hill, n_hill, d_elim, n_elim, n_tout, own_w, elim_s, flips, flip_n): z.zero_()
    env._reset(dm.nonzero(as_tuple=True)[0]); hprev[dm] = -2; gstep += env.N
if a.summary:
    n = S["n"] or 1; dec = wins.sum().item() or 1
    wd = " ".join("%s%d=%.3f" % (env.doctrines[c], c, wins[c].item() / dec) for c in range(env.C))
    print("DOCTRINES %s | HOLD %d | guerres %d | décisives %.2f | winrate(déc) %s | 2COLL %.2f (durée %.1f) | ÉLIM %.2f (durée %.1f) | vainq terr %.2f | CIVILS morts %.3f réfug %.2f surv %.3f | vainq ctrl pop %.2f"
          % (env.doctrines, a.hold, S["n"], dec / n, wd,
             S["hill"] / n, (S["dh"] / S["hill"] if S["hill"] else 0), S["elim"] / n,
             (S["de"] / S["elim"] if S["elim"] else 0), S["vainq"] / n,
             S["morts"] / n, S["refug"] / n, S["surv"] / n, S["wpop"] / n), flush=True)
print("[fini] %.0f tr/s" % (gstep / (time.time() - t0)), flush=True)
