"""eval_suffer_replica — fait jouer l'agent souffrance (soldier_suffer.pt) sur la REPLIQUE du complexe,
pour VOIR : neutralise-t-il, survit-il, ou se planque-t-il ? + film du chemin. (decalage de domaine assume.)"""
import torch, numpy as np
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
DEV = "cuda:0"; RP = "/home/younes/arma3-marl/replica.npz"
net = Net(24, 10, 512, 3).to(DEV)
net.load_state_dict(torch.load("/home/younes/arma3-marl/soldier_suffer.pt", map_location=DEV)); net.eval()
mk = lambda n, sd: AssaultTerrain(num_envs=n, A=1, D=3, relief=40.0, hit=0.10, shell_obs=True, suffer=True,
                                  replica=True, replica_path=RP, max_steps=60, device=DEV, seed=sd)

# stats agregees
env = mk(512, 0); obs = env.reset()
won = surv = 0.0; nep = 0; done_once = torch.zeros(512, dtype=torch.bool, device=DEV)
init_d = torch.sqrt(env.apx ** 2 + env.apy ** 2).squeeze(1).clone(); min_d = init_d.clone()
for t in range(70):
    with torch.no_grad():
        act = net.a_logits(obs).argmax(-1)
    obs, _, done, info = env.step(act)
    d = torch.sqrt(env.apx ** 2 + env.apy ** 2).squeeze(1)
    min_d = torch.where(~done_once, torch.minimum(min_d, d), min_d)
    dm = done.bool() & ~done_once
    if dm.any():
        won += info["neutralized"][dm].float().sum().item(); surv += (~info["wiped"][dm]).float().sum().item(); nep += int(dm.sum())
    done_once |= done.bool()
print("=== soldier_suffer sur la REPLIQUE (1 vs 3) ===", flush=True)
print("garnison neutralisee %.0f%% | survie %.0f%% | approche min %.0f m de l'objectif (depart ~%.0f m) | n=%d" % (
    100 * won / max(nep, 1), 100 * surv / max(nep, 1), float(min_d.mean()), float(init_d.mean()), nep), flush=True)

# film d'un episode
e = mk(1, 3); o = e.reset(); xs = []; ys = []; acts = []; out = "TIMEOUT"; dn = False
dpx = e.dpx[0].cpu().numpy(); dpy = e.dpy[0].cpu().numpy()
for t in range(60):
    with torch.no_grad():
        a = int(net.a_logits(o).argmax(-1).item())
    if not dn:
        xs.append(e.apx[0, 0].item()); ys.append(e.apy[0, 0].item()); acts.append(a)
    o, _, d, info = e.step(torch.tensor([[a]], device=DEV), auto_reset=False)
    if not dn and d[0].item() > 0.5:
        dn = True; out = "NEUTRALISE" if info["neutralized"][0].item() else ("MORT" if info["wiped"][0].item() else "TIMEOUT")
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sg = e._solid.cpu().numpy()
fig, ax = plt.subplots(figsize=(9, 9))
ax.imshow(sg, extent=[-e.scale, e.scale, -e.scale, e.scale], origin="lower", cmap="gray_r")
ax.scatter(dpx, dpy, c="red", marker="x", s=140, label="defenseurs", zorder=5)
ax.scatter([0], [0], c="black", marker="*", s=220, label="objectif", zorder=5)
ACTC = {**{i: "#1f77b4" for i in range(8)}, 8: "gray", 9: "orange"}
for i in range(1, len(xs)):
    ax.plot(xs[i - 1:i + 1], ys[i - 1:i + 1], "-", c=ACTC.get(acts[i], "#1f77b4"), lw=2.5)
if xs:
    ax.scatter([xs[0]], [ys[0]], c="green", s=100, zorder=6, label="depart"); ax.scatter([xs[-1]], [ys[-1]], c="blue", s=100, zorder=6, label="fin")
ax.legend(loc="upper right"); ax.set_aspect("equal")
ax.set_title("soldier_suffer sur la REPLIQUE : %s  (bleu=bouge orange=suppr, murs=gris)" % out)
fig.savefig("/tmp/suffer_replica.png", dpi=110)
print("FILM : issue =", out, "| /tmp/suffer_replica.png", flush=True)
