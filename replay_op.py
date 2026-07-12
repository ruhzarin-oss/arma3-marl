"""replay_op — film vue de dessus de l'epreuve operationnelle depuis la trace.
Montre : batiments(gris), ennemis(rouge x), objectif(*), chemin de l'avatar (bleu=bouge, orange=suppr),
depart(vert), fin(bleu). Revele si le soldat se coince sur un mur."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, re
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"

rows = open("/tmp/op_trace.csv").read().splitlines()
obj = None; av = []; acts = []; ens = []
for r in rows:
    p = r.split(",")
    if p[0] == "OBJ":
        obj = (int(p[1]), int(p[2])); continue
    av.append((int(p[1]), int(p[2]))); acts.append(int(p[3]))
    rest = p[6:]; e = [(int(rest[k]), int(rest[k + 1])) for k in range(0, len(rest) - 3, 4)]
    ens.append(e)
av = np.array(av)

env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis",
             log=SB + "/logs/server0.out", acc=1.0, seed=1)
ls = env._query('{ private _p = getPosATL _x; diag_log format ["BLD %%1 %%2", round(_p#0), round(_p#1)]; }'
                ' forEach (nearestObjects [[%d,%d,0],["House","Building"],130]);' % (obj[0], obj[1]), settle=0.25)
blds = [(int(m.group(1)), int(m.group(2))) for l in ls for m in [re.search(r"BLD (-?\d+) (-?\d+)", l)] if m]

fig, ax = plt.subplots(figsize=(9, 9))
for (bx, by) in blds:
    ax.scatter([bx], [by], c="#999", marker="s", s=70)
ax.scatter([obj[0]], [obj[1]], c="black", marker="*", s=280, label="objectif", zorder=5)
for (ex, ey) in (ens[-1] if ens else []):
    ax.scatter([ex], [ey], c="red", marker="x", s=150, zorder=5)
ACTC = {**{i: "#1f77b4" for i in range(8)}, 8: "gray", 9: "orange"}
for i in range(1, len(av)):
    ax.plot(av[i - 1:i + 1, 0], av[i - 1:i + 1, 1], "-", c=ACTC.get(acts[i], "#1f77b4"), lw=2.2)
ax.scatter([av[0, 0]], [av[0, 1]], c="green", s=110, zorder=6, label="depart")
ax.scatter([av[-1, 0]], [av[-1, 1]], c="blue", s=110, zorder=6, label="fin")
ax.set_aspect("equal"); ax.legend(loc="upper right")
ax.set_title("Replay op — batiments(gris) ennemis(rouge) objectif(*) | chemin bleu=bouge orange=suppr")
fig.tight_layout(); fig.savefig("/tmp/op_replay.png", dpi=110)
print("REPLAY OK : %d batiments, %d pas, %d ennemis (dernier cycle)" % (len(blds), len(av), len(ens[-1]) if ens else 0))
