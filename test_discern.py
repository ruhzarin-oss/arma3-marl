"""test_discern — le soldat souffrance/selection DISCERNE-T-IL vraiment ?
Joue l'agent sur GAGNABLE (1v2) vs SUBMERGE (1v6) et mesure le CHANGEMENT de comportement :
avance+engage sur le gagnable / se retient (n'avance pas dans le feu) sur le submerge.
+ visu des trajectoires (foncer dedans vs s'arreter/decrocher). Sortie : table + /tmp/discern_viz.png
args: checkpoint"""
import torch, sys
import numpy as np
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
DEV = "cuda:0"
CK = sys.argv[1] if len(sys.argv) > 1 else "soldier_suffer.pt"


def mk(D, n, sd):
    return AssaultTerrain(num_envs=n, A=1, D=D, D_min=D, relief=40.0, hit=0.10,
                          shell_obs=True, suffer=True, max_steps=60, device=DEV, seed=sd)


env0 = mk(2, 8, 1)
net = Net(env0.obs_dim, env0.n_actions, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/arma3-marl/" + CK, map_location=DEV)); net.eval()


@torch.no_grad()
def behav(D, n=2048, steps=70):
    env = mk(D, n, 123); obs = env.reset()
    init_d = torch.sqrt(env.apx ** 2 + env.apy ** 2).squeeze(1).clone()
    min_d = init_d.clone()
    supp = torch.zeros(n, device=DEV); nst = torch.zeros(n, device=DEV)
    done_once = torch.zeros(n, dtype=torch.bool, device=DEV)
    win = surv = dead = 0.0; nep = 0
    for t in range(steps):
        act = net.a_logits(obs).argmax(-1)
        live = ~done_once
        supp += ((act.squeeze(1) == 9) & live).float(); nst += live.float()
        obs, rw, done, info = env.step(act)
        d_now = torch.sqrt(env.apx ** 2 + env.apy ** 2).squeeze(1)
        min_d = torch.where(live, torch.minimum(min_d, d_now), min_d)
        dm = done.bool() & ~done_once
        if dm.any():
            win += info["neutralized"][dm].float().sum().item()
            surv += (~info["wiped"][dm]).float().sum().item()
            dead += info["wiped"][dm].float().sum().item(); nep += int(dm.sum())
        done_once = done_once | done.bool()
    return dict(win=win / max(nep, 1), surv=surv / max(nep, 1), dead=dead / max(nep, 1),
                approach=float((init_d - min_d).mean()) / env.scale, eng=float((supp / nst.clamp(min=1)).mean()))


@torch.no_grad()
def record(D, k=4, steps=60):
    env = mk(D, k, 555); obs = env.reset()
    cover = env.cover.cpu().numpy(); dpx = env.dpx.cpu().numpy(); dpy = env.dpy.cpu().numpy()
    xs = [[] for _ in range(k)]; ys = [[] for _ in range(k)]; out = ["TIMEOUT"] * k; dn = [False] * k
    for t in range(steps):
        act = net.a_logits(obs).argmax(-1)
        for e in range(k):
            if not dn[e]:
                xs[e].append(env.apx[e, 0].item()); ys[e].append(env.apy[e, 0].item())
        obs, rw, d, info = env.step(act, auto_reset=False)
        for e in range(k):
            if not dn[e] and d[e].item() > 0.5:
                dn[e] = True
                out[e] = "WIN" if info["neutralized"][e].item() else ("MORT" if info["wiped"][e].item() else "TIMEOUT")
    return cover, dpx, dpy, xs, ys, out


bw = behav(2); bo = behav(6)
print("===== DISCERNEMENT (%s) =====" % CK, flush=True)
print("                      GAGNABLE(1v2)   SUBMERGE(1v6)", flush=True)
print("  victoire            %5.0f%%          %5.0f%%" % (100 * bw["win"], 100 * bo["win"]), flush=True)
print("  survie              %5.0f%%          %5.0f%%" % (100 * bw["surv"], 100 * bo["surv"]), flush=True)
print("  mort                %5.0f%%          %5.0f%%" % (100 * bw["dead"], 100 * bo["dead"]), flush=True)
print("  approche (0=reste loin, 1=fonce a l'obj)  %.2f           %.2f" % (bw["approach"], bo["approach"]), flush=True)
print("  taux de suppression %5.0f%%          %5.0f%%" % (100 * bw["eng"], 100 * bo["eng"]), flush=True)
print("  -> DISCERNE si : avance/engage BAISSE et survie MONTE quand ca passe de gagnable a submerge", flush=True)

try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    for row, (D, lab) in enumerate([(2, "GAGNABLE 1v2"), (6, "SUBMERGE 1v6")]):
        cov, dpx, dpy, xs, ys, out = record(D, 4)
        for e in range(4):
            ax = axes[row, e]
            ax.imshow(cov[e], extent=[-200, 200, -200, 200], origin="lower", cmap="Greys", alpha=0.5, vmin=0, vmax=1)
            ax.scatter(dpx[e], dpy[e], c="red", marker="x", s=80, label="ennemis")
            if xs[e]:
                ax.plot(xs[e], ys[e], "-", c="#1f77b4", lw=1.5)
                ax.scatter([xs[e][0]], [ys[e][0]], c="green", s=40)   # depart
                ax.scatter([xs[e][-1]], [ys[e][-1]], c="blue", s=40)  # fin
            ax.set_title("%s : %s" % (lab.split()[0], out[e]), fontsize=10)
            ax.set_xlim(-200, 200); ax.set_ylim(-200, 200); ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("Trajectoires — couvert(gris) ennemis(rouge) depart(vert) fin(bleu)")
    fig.tight_layout(); fig.savefig("/tmp/discern_viz.png", dpi=100)
    print("\nPLOT_SAVED /tmp/discern_viz.png", flush=True)
except Exception as e:
    print("plot failed:", e, flush=True)
print("DISCERN FINI", flush=True)
