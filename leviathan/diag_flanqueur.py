#!/usr/bin/env python3
"""COMBIEN DE TEMPS LE FLANQUEUR RESTE-T-IL SOUS LE FEU ?

Deux hypotheses deja refutees par la mesure :
  1. « le cone dur masquait un sur-comptage de puissance de feu » -> ouvrir le cone ne
     multiplie les paires que par 1,13. (Et ce comptage etait fait sous la doctrine
     FRONTALE, ou l'arc ne protege personne : erreur de ma part.)
  2. « les attaquants finissent juste sous le seuil de mort » -> seulement 10 % entre 0,50
     et 0,70. Pas de falaise.

Ce qui reste, et qui se mesure : **l'echelle de temps**. Arma a mesure un sursis de 4 s sur
un engagement qui dure une dizaine de secondes — le sursis y vaut une grosse fraction du
duel. Dans le sandbox, le crochet met 25 a 30 pas, soit 80 a 100 secondes. Un sursis de 4 s
n'y est plus qu'un pas sur trente.

Si c'est ca, le sandbox n'a pas tort sur l'arc : il a tort sur la DUREE de l'approche. Et
alors ce n'est pas τ qu'il faut toucher (interdit : c'est une mesure), c'est la geometrie
de l'episode qu'il faut confronter a celle du banc Arma.

On mesure, par role, sous la doctrine CROCHET :
  - le nombre de pas passes a portee ET en vue d'un defenseur qui peut tirer ;
  - la part de ces pas ou l'arc protegeait encore (cone dur) ou plus (cone ouvrant).
"""
import sys
import math
import torch

sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain

COURBE = "/home/younes/arma3-marl/leviathan/courbe_toucher_juge.json"
SEC, TIR, DEG = 3.28, 1.15, 0.233
N = 1024


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
    # pas passes sous le feu, par attaquant
    sous_feu = torch.zeros(N, e.A, device=dev)
    for t in range(60):
        d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        act = cap(-e.apx, -e.apy)
        fixe = torch.zeros(N, e.A, dtype=torch.bool, device=dev); fixe[:, :2] = True
        act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
        if t < 14:
            act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        vv = (~fini).unsqueeze(1)
        e._ouvrir_arcs()
        # un attaquant est SOUS LE FEU s'il existe un defenseur vivant qui le voit,
        # est a portee, et dont l'arc l'autorise a tirer (cone ou sursis ecoule)
        peut = torch.zeros(N, e.A, dtype=torch.bool, device=dev)
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
            peut = peut | (_d & (dist < e.fire_range) & (los > 0.5)
                           & e._dalive()[:, di:di + 1] & e._aalive())
        sous_feu = sous_feu + (peut & vv).float()
        _, _, done, info = e.step(act, auto_reset=False)
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    return {"fixeurs": float(sous_feu[:, :2].mean()), "flanqueurs": float(sous_feu[:, 2:].mean())}


print("=== COMBIEN DE PAS LE FLANQUEUR PASSE-T-IL SOUS LE FEU ? ===", flush=True)
print("    doctrine CROCHET | 1 pas = 3,28 s (mesure Arma)", flush=True)
print("", flush=True)
print("%-18s %14s %14s %14s %14s" % ("monde", "fixeurs (pas)", "fix. (s)", "flanqueurs (pas)", "flanq. (s)"), flush=True)
r = {}
for nom, lat in (("cone DUR", None), ("cone OUVRANT 4 s", 4.0)):
    v = joue(lat)
    r[nom] = v
    print("%-18s %14.1f %14.0f %14.1f %14.0f"
          % (nom, v["fixeurs"], v["fixeurs"] * SEC, v["flanqueurs"], v["flanqueurs"] * SEC), flush=True)

print("", flush=True)
d, o = r["cone DUR"], r["cone OUVRANT 4 s"]
mult = o["flanqueurs"] / max(d["flanqueurs"], 1e-9)
print("  ouvrir le cone multiplie le temps sous le feu du FLANQUEUR par %.2f" % mult, flush=True)
print("  (fixeur : x%.2f — il etait deja de face, l'arc ne le protegeait pas)"
      % (o["fixeurs"] / max(d["fixeurs"], 1e-9)), flush=True)
print("", flush=True)
print("  Le sursis mesure sur Arma vaut 4 s, soit UN pas de sandbox.", flush=True)
print("  Le flanqueur passe %.0f s sous le feu dans le monde ouvrant." % (o["flanqueurs"] * SEC), flush=True)
print("  Le sursis represente donc %.0f %% de son exposition."
      % (100.0 * 1.0 / max(o["flanqueurs"], 1e-9)), flush=True)
if o["flanqueurs"] > 8:
    print("", flush=True)
    print("  >>> ECHELLE DE TEMPS INCOMPATIBLE. Arma a mesure un sursis de 4 s sur un", flush=True)
    print("      engagement de quelques dizaines de secondes ; ici le flanqueur reste", flush=True)
    print("      %.0f s sous le feu. Le sursis y est negligeable par construction." % (o["flanqueurs"] * SEC), flush=True)
    print("      Ce n'est pas tau qu'il faut toucher — c'est la DUREE de l'approche qu'il", flush=True)
    print("      faut confronter a celle du banc Arma.", flush=True)
print("DIAG_DONE", flush=True)
