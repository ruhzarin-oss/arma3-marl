#!/usr/bin/env python3
"""13 % DE FEU EN PLUS, 36 POINTS DE PRISE EN MOINS : OU EST LA FALAISE ?

Premiere hypothese REFUTEE par la mesure : ouvrir le cone ne multiplie les paires de tir
que par 1,13, pas par trois. Le sur-comptage (1,8 attaquant par defenseur) existe, mais il
est present dans LES DEUX mondes — il n'explique pas l'ecrasement.

Il reste une seule facon d'expliquer 43 % -> 7 % avec 13 % de feu en plus : **le monde est
au bord d'une falaise**. Si les attaquants terminent tout juste SOUS le seuil de mort
(dmg_dead = 0,7), un petit surcroit de degats les fait tous basculer d'un coup.

On regarde donc la distribution des degats accumules, pas leur moyenne. Trois choses :
  - ou se situe la masse par rapport a 0,7 ;
  - combien d'attaquants sont vivants a la fin ;
  - a quelle distance de l'objectif ils meurent.

Si la masse est collee juste sous 0,7 dans le cone dur, la falaise est demontree.
Si elle est loin du seuil, l'explication est ailleurs et on le dira.
"""
import sys
import math
import torch

sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain

COURBE = "/home/younes/arma3-marl/leviathan/courbe_toucher_juge.json"
SEC, TIR, DEG = 3.28, 1.15, 0.233
N = 2048


def monde(lat):
    k = dict(num_envs=N, A=4, D=8, seed=7, device="cuda:0", max_steps=60, R_spawn=170.0,
             postures=True, hull=True, def_line=True, def_rand=False, def_arc=math.pi / 3,
             secure_task=True, secure_only=True, courbe=COURBE,
             tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG, arc_obs=True)
    if lat is not None:
        k["arc_latence_s"] = lat
    return AssaultTerrain(**k)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


@torch.no_grad()
def joue(lat, doctrine):
    e = monde(lat)
    e.reset()
    dev = e.apx.device
    fini = torch.zeros(N, dtype=torch.bool, device=dev)
    pris = torch.zeros(N, dtype=torch.bool, device=dev)
    d_fin = torch.full((N,), 1e9, device=dev)
    for t in range(60):
        d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        act = cap(-e.apx, -e.apy)
        if doctrine == "flanc":
            fixe = torch.zeros(N, e.A, dtype=torch.bool, device=dev); fixe[:, :2] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            if t < 14:
                act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        vv = ~fini
        _, _, done, info = e.step(act, auto_reset=False)
        pris = pris | (info["took"] & vv)
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        vivants = e._aalive()
        dmin = torch.where(vivants, d, torch.full_like(d, 1e9)).min(1).values
        d_fin = torch.where(vv, torch.minimum(d_fin, dmin), d_fin)
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    dm = e.admg.flatten()
    return {"prise": float(pris.float().mean()),
            "dmg": dm,
            "vivants_fin": float(e._aalive().float().sum(1).mean()),
            "dist_min": float(d_fin[d_fin < 1e8].mean())}


print("=== OU EST LA FALAISE ? (seuil de mort dmg_dead = 0,7) ===", flush=True)
print("    D=8, A=4, cone 120 deg, %d episodes, doctrine CROCHET" % N, flush=True)
print("", flush=True)
BORNES = [0.0, 0.1, 0.3, 0.5, 0.6, 0.65, 0.7, 0.8, 1.01]
print("%-18s %6s %8s %8s   %s" % ("monde", "prise", "vivants", "dist min", "repartition des degats"), flush=True)
res = {}
for nom, lat in (("cone DUR", None), ("cone OUVRANT", 4.0)):
    r = joue(lat, "flanc")
    res[nom] = r
    h = []
    for i in range(len(BORNES) - 1):
        m = ((r["dmg"] >= BORNES[i]) & (r["dmg"] < BORNES[i + 1])).float().mean()
        h.append("%.0f" % (100 * float(m)))
    print("%-18s %5.1f%% %8.2f %8.0f m   %s"
          % (nom, 100 * r["prise"], r["vivants_fin"], r["dist_min"], " ".join("%3s" % x for x in h)), flush=True)
print("%-18s %6s %8s %8s   %s" % ("", "", "", "",
      " ".join("%3s" % ("<%.2f" % BORNES[i + 1]) for i in range(len(BORNES) - 1))), flush=True)

print("", flush=True)
d, o = res["cone DUR"], res["cone OUVRANT"]
sous = float(((d["dmg"] >= 0.5) & (d["dmg"] < 0.7)).float().mean())
morts_d = float((d["dmg"] >= 0.7).float().mean())
morts_o = float((o["dmg"] >= 0.7).float().mean())
print("  cone DUR      : %.0f %% des attaquants finissent entre 0,50 et 0,70 (juste sous le seuil)" % (100 * sous), flush=True)
print("  morts          : %.0f %% (dur) -> %.0f %% (ouvrant)" % (100 * morts_d, 100 * morts_o), flush=True)
print("", flush=True)
if sous > 0.20 and morts_o > morts_d + 0.10:
    print("  >>> FALAISE CONFIRMEE. Une masse d'attaquants termine juste SOUS le seuil de", flush=True)
    print("      mort dans le cone dur. 13 %% de feu en plus suffit a la faire basculer.", flush=True)
    print("      Le monde n'est pas robuste : la prise depend d'un seuil, pas d'une pente.", flush=True)
else:
    print("  >>> pas de falaise a ce seuil. L'ecrasement vient d'ailleurs :", flush=True)
    print("      regarder la distance minimale atteinte et les survivants.", flush=True)
print("DIAG_DONE", flush=True)
