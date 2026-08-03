#!/usr/bin/env python3
"""carte_ombre.py — LE COULOIR EXISTE-T-IL ?

⟨Fable, 03/08 : « Trace la carte de visibilite. Un damier d'ombre et de lumiere, pas un
chemin. Puis regarde si une zone d'ombre CONTINUE relie le bord exterieur au rayon de 40 m.
Cas 1 : le couloir existe, le controle positif est un plus court chemin sur ce damier.
Cas 2 : aucun couloir — le banc posait une question impossible, il faut changer la TACHE. »⟩

Calcul purement geometrique sur les configurations deja exportees. Aucune simulation.
Demi-cone : 35 degres, mesure sur Arma le 03/08 (plateau plat 0-30, zero des 40).
"""
import json, math, numpy as np
from collections import deque

CHAMP = 35.0
R_EXT, R_ARR = 80.0, 40.0
PAS = 2.0

src = json.load(open('/mnt/data/corpus/trajectoires_agent_SAUVE.json'))[:20]
res = []
for c in src:
    d = np.array(c['defenseurs'])
    xy, az = d[:, :2], d[:, 2]

    # damier : vu / pas vu, sur une grille carree qui couvre le disque
    n = int(2*R_EXT/PAS) + 1
    ax = np.linspace(-R_EXT, R_EXT, n)
    X, Y = np.meshgrid(ax, ax)
    vu = np.zeros_like(X, dtype=bool)
    for (dx, dy), a in zip(xy, az):
        vx, vy = X - dx, Y - dy
        gis = np.degrees(np.arctan2(vx, vy)) % 360
        ec = np.abs((gis - a + 180) % 360 - 180)
        vu |= (ec <= CHAMP)

    rad = np.hypot(X, Y)
    dedans = rad <= R_EXT
    ombre = dedans & ~vu

    # un couloir d'ombre relie-t-il le bord exterieur au rayon d'arrivee ?
    depart = ombre & (rad >= R_EXT - 2*PAS)
    arrivee = ombre & (rad <= R_ARR + PAS)
    atteint = np.zeros_like(ombre)
    q = deque(zip(*np.where(depart)))
    for i, j in q: atteint[i, j] = True
    while q:
        i, j = q.popleft()
        for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
            a2, b2 = i+di, j+dj
            if 0 <= a2 < n and 0 <= b2 < n and ombre[a2, b2] and not atteint[a2, b2]:
                atteint[a2, b2] = True; q.append((a2, b2))
    couloir = bool((atteint & arrivee).any())

    part_ombre = float(ombre[dedans].mean())
    couv = float(sum(2*CHAMP for _ in xy))
    res.append((couloir, part_ombre, couv, len(xy)))

r = np.array([(1 if a else 0, b, c, d) for a, b, c, d in res])
print(f"  {len(res)} configurations, {r[:,3].mean():.1f} defenseurs en moyenne")
print(f"  couverture cumulee des cones : {r[:,2].mean():.0f} degres  (un tour = 360)")
print(f"  part du disque dans l ombre  : {r[:,1].mean():.0%}")
print()
n_ok = int(r[:,0].sum())
print(f"  CONFIGURATIONS AVEC UN COULOIR D OMBRE CONTINU  :  {n_ok} / {len(res)}")
print()
if n_ok == 0:
    print("  CAS 2 — AUCUN COULOIR. Le banc posait une question impossible.")
    print("  Il faut changer la TACHE : etre vu le plus TARD possible, et non arriver invisible.")
    print("  La distance de detection cesse d etre une mesure, elle devient la definition.")
elif n_ok >= len(res)*0.7:
    print("  CAS 1 — LE COULOIR EXISTE presque partout.")
    print("  Le controle positif doit etre un plus court chemin calcule point par point.")
else:
    print(f"  CAS MIXTE — le couloir n existe que dans {n_ok}/{len(res)} configurations.")
    print("  Certifier par famille, avec un seuil propre a chacune.")
