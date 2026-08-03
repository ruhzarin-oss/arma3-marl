#!/usr/bin/env python3
"""POURQUOI OUVRIR LE CONE ECRASE-T-IL LA PRISE DE 43 % A 7 % ?

Hypothese, formulee avant de mesurer : **le cone dur masquait un defaut de puissance de
feu**. Dans la boucle de degats, chaque defenseur tire sur TOUS les attaquants a la fois,
a chaque pas — un soldat d'Arma tire sur UN homme. Avec un cone de 120 deg, l'arc masquait
la plupart de ces paires. Ouvrir le cone les demasque toutes d'un coup.

Si l'hypothese est bonne, on doit voir :
  - le nombre de PAIRES (defenseur, attaquant) qui tirent effectivement bondir d'un facteur
    proche du rapport des surfaces d'arc (120 deg -> 360 deg, soit x3) ;
  - et surtout le nombre moyen d'attaquants pris a partie PAR DEFENSEUR depasser 1, ce qui
    n'a pas de sens pour un fantassin.

Si au contraire les paires bougent peu, l'hypothese tombe et il faut chercher ailleurs.

On ne touche a rien : on observe `active` telle que le monde la calcule deja.
"""
import sys
import math
import torch

sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain

COURBE = "/home/younes/arma3-marl/leviathan/courbe_toucher_juge.json"
SEC, TIR, DEG = 3.28, 1.15, 0.233
N, PAS = 512, 40


def monde(lat):
    k = dict(num_envs=N, A=4, D=8, seed=7, device="cuda:0", max_steps=60, R_spawn=170.0,
             postures=True, hull=True, def_line=True, def_rand=False, def_arc=math.pi / 3,
             secure_task=True, secure_only=True, courbe=COURBE,
             tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG, arc_obs=True)
    if lat is not None:
        k["arc_latence_s"] = lat
    return AssaultTerrain(**k)


@torch.no_grad()
def compte(lat):
    """Reproduit EXACTEMENT le test d'arc de la boucle de degats, et compte les paires."""
    e = monde(lat)
    e.reset()
    dev = e.apx.device
    paires = 0.0
    def_actifs = 0.0
    n_obs = 0
    for t in range(PAS):
        act = (torch.round(torch.atan2(-e.apx, -e.apy) / (math.pi / 4.0)).long() % 8)
        e._ouvrir_arcs()
        vivant = e._dalive().float()                                  # (N,D)
        dedans = torch.zeros(N, e.D, e.A, device=dev)
        for di in range(e.D):
            _ang = torch.atan2(e.apx - e.dpx[:, di:di + 1], e.apy - e.dpy[:, di:di + 1])
            _adf = torch.atan2(torch.sin(_ang - e.dface[:, di:di + 1]),
                               torch.cos(_ang - e.dface[:, di:di + 1]))
            _d = (_adf.abs() <= e._dfarc)
            ouv = getattr(e, "d_ouvert", None)
            if ouv is not None:
                _d = _d | ouv[:, di:di + 1]
            dist = torch.sqrt((e.apx - e.dpx[:, di:di + 1]) ** 2 + (e.apy - e.dpy[:, di:di + 1]) ** 2)
            los = e._losc(e.hm, e.apx, e.apy,
                          e.dpx[:, di:di + 1].expand(N, e.A), e.dpy[:, di:di + 1].expand(N, e.A),
                          e.scale, eye_a=e._eye(), eye_b=1.7)
            dedans[:, di, :] = _d.float() * (dist < e.fire_range).float() * (los > 0.5).float() \
                * vivant[:, di:di + 1] * e._aalive().float()
        par_def = dedans.sum(2)                                        # (N,D) cibles par defenseur
        actif = (par_def > 0).float()
        if float(actif.sum()) > 0:
            paires += float(dedans.sum() / N)
            def_actifs += float(actif.sum() / N)
            n_obs += 1
        e.step(act, auto_reset=False)
    if n_obs == 0:
        return None
    p = paires / n_obs
    da = def_actifs / n_obs
    return {"paires_par_pas": p, "defenseurs_qui_tirent": da,
            "cibles_par_defenseur": p / max(da, 1e-9)}


print("=== POURQUOI LE CONE OUVRANT ECRASE-T-IL LA PRISE ? ===", flush=True)
print("    D=8 defenseurs, A=4 attaquants, cone 120 deg, %d episodes" % N, flush=True)
print("", flush=True)
print("%-22s %14s %16s %20s" % ("monde", "paires/pas", "defenseurs qui tirent", "cibles/defenseur"), flush=True)
r = {}
for nom, lat in (("cone DUR", None), ("cone OUVRANT 4 s", 4.0)):
    v = compte(lat)
    r[nom] = v
    print("%-22s %14.2f %16.2f %20.2f"
          % (nom, v["paires_par_pas"], v["defenseurs_qui_tirent"], v["cibles_par_defenseur"]), flush=True)

print("", flush=True)
d, o = r["cone DUR"], r["cone OUVRANT 4 s"]
print("  ouvrir le cone multiplie les paires de tir par %.2f"
      % (o["paires_par_pas"] / max(d["paires_par_pas"], 1e-9)), flush=True)
print("  et les defenseurs qui tirent par %.2f"
      % (o["defenseurs_qui_tirent"] / max(d["defenseurs_qui_tirent"], 1e-9)), flush=True)
print("", flush=True)
if o["cibles_par_defenseur"] > 1.5:
    print("  >>> UN DEFENSEUR PREND A PARTIE %.1f ATTAQUANTS EN MEME TEMPS." % o["cibles_par_defenseur"], flush=True)
    print("      Un fantassin tire sur UN homme. Le cone dur masquait ce sur-comptage ;", flush=True)
    print("      l'ouvrir le revele. Ce n'est pas l'arc qui ecrase la prise, c'est la", flush=True)
    print("      puissance de feu que l'arc cachait.", flush=True)
else:
    print("  >>> le sur-comptage n'explique pas l'ecrasement : chercher ailleurs.", flush=True)
print("DIAG_DONE", flush=True)
