#!/usr/bin/env python3
"""QUI MEURT, ET QUI PORTAIT LA PRISE ?

Trois hypotheses deja refutees par la mesure :
  1. sur-comptage de puissance de feu demasque    -> paires x1,13 seulement
  2. falaise au seuil de mort (0,7)               -> 10 % seulement entre 0,50 et 0,70
  3. exposition trop longue du flanqueur          -> 1,1 pas seulement, et x1,18 a l'ouverture

Ce qui reste dans les chiffres : survivants 1,88 -> 1,10 alors que la distance minimale
atteinte bouge a peine (60 -> 70 m). Quelqu'un meurt, et la prise s'effondre avec lui.

Or les deux roles n'ont pas le meme travail. Le FIXEUR s'arrete a 100 m et arrose : il
n'arrivera jamais sur l'objectif, quoi qu'il survive. Le FLANQUEUR est le seul qui puisse
prendre. Avec `secure_only=True`, gagner = un attaquant VIVANT a 25 m de l'objectif.

Donc si l'ouverture du cone tue les flanqueurs et epargne les fixeurs, la prise s'effondre
sans que ni la puissance de feu, ni l'exposition moyenne n'aient beaucoup bouge. C'est
testable directement : survie ET arrivee, par role.
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
def joue(lat):
    e = monde(lat)
    e.reset()
    dev = e.apx.device
    fini = torch.zeros(N, dtype=torch.bool, device=dev)
    arrive = torch.zeros(N, e.A, dtype=torch.bool, device=dev)   # a touche 25 m VIVANT
    for t in range(60):
        d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        act = cap(-e.apx, -e.apy)
        fixe = torch.zeros(N, e.A, dtype=torch.bool, device=dev); fixe[:, :2] = True
        act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
        if t < 14:
            act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        _, _, done, _ = e.step(act, auto_reset=False)
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        arrive = arrive | ((d < e.secure_r) & e._aalive() & (~fini).unsqueeze(1))
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    viv = e._aalive().float()
    return {"survie_fix": float(viv[:, :2].mean()), "survie_flanc": float(viv[:, 2:].mean()),
            "arrive_fix": float(arrive[:, :2].float().mean()),
            "arrive_flanc": float(arrive[:, 2:].float().mean()),
            "prise": float(arrive.any(1).float().mean())}


print("=== QUI MEURT, ET QUI PORTAIT LA PRISE ? ===", flush=True)
print("    doctrine CROCHET | fixeurs = attaquants 0-1 | flanqueurs = 2-3", flush=True)
print("    arrive = a touche les 25 m de l'objectif VIVANT", flush=True)
print("", flush=True)
print("%-18s %11s %11s %11s %11s %8s" %
      ("monde", "survie fix", "survie flanc", "arrive fix", "arrive flanc", "prise"), flush=True)
r = {}
for nom, lat in (("cone DUR", None), ("cone OUVRANT 4 s", 4.0)):
    v = joue(lat)
    r[nom] = v
    print("%-18s %10.0f%% %10.0f%% %10.0f%% %10.0f%% %7.1f%%"
          % (nom, 100 * v["survie_fix"], 100 * v["survie_flanc"],
             100 * v["arrive_fix"], 100 * v["arrive_flanc"], 100 * v["prise"]), flush=True)

d, o = r["cone DUR"], r["cone OUVRANT 4 s"]
print("", flush=True)
print("  survie du FLANQUEUR : %.0f %% -> %.0f %%  (x%.2f)"
      % (100 * d["survie_flanc"], 100 * o["survie_flanc"],
         o["survie_flanc"] / max(d["survie_flanc"], 1e-9)), flush=True)
print("  survie du FIXEUR    : %.0f %% -> %.0f %%  (x%.2f)"
      % (100 * d["survie_fix"], 100 * o["survie_fix"],
         o["survie_fix"] / max(d["survie_fix"], 1e-9)), flush=True)
print("  arrivee du flanqueur: %.0f %% -> %.0f %%"
      % (100 * d["arrive_flanc"], 100 * o["arrive_flanc"]), flush=True)
print("  arrivee du fixeur   : %.0f %% -> %.0f %%"
      % (100 * d["arrive_fix"], 100 * o["arrive_fix"]), flush=True)
print("", flush=True)
if o["arrive_fix"] < 0.02 and d["arrive_fix"] < 0.02:
    print("  >>> LE FIXEUR N'ARRIVE JAMAIS, dans aucun des deux mondes : il s'arrete a 100 m", flush=True)
    print("      pour arroser, c'est son role. TOUTE la prise repose donc sur le flanqueur.", flush=True)
    print("      Un monde qui tue le flanqueur ne reduit pas la prise : il la SUPPRIME.", flush=True)
print("DIAG_DONE", flush=True)
