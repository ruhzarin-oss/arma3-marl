#!/usr/bin/env python3
"""azimut — L'ECHEC SUIT-IL L'ECART AU CAP APPRIS ?

Hypothese : la politique certifiee sur le site GELE (azimut 310) a appris « marche au
315 » plutot que « va vers le but ». Prediction testable : sur sites tires, l'echec doit
croitre avec l'ecart angulaire entre l'azimut du site et 310.

⚠️ CE CONTROLE SAIT ECHOUER : si le taux d'echec est PLAT en fonction de l'ecart,
l'hypothese tombe et le declin reste inexplique.
"""
import re, glob, os, collections

def analyse(inst, nom, t0, t1):
    R = [f for f in glob.glob(f"/mnt/c/Users/Younes/hmtech{inst}/*.rpt") if "2026-09-02_10-15" in f][0]
    sit, res, ordre = {}, {}, []
    for l in open(R, errors="ignore"):
        if not (len(l) > 8 and l[2] == ":" and l[:2].isdigit()): continue
        if l[:5] < t0 or l[:5] > t1: continue
        m = re.search(r"SITEUSE (\d+) ([\d.]+) ([\d.]+) (\d+)", l)
        if m and int(m[1]) not in sit: sit[int(m[1])] = int(m[4])
        m = re.search(r"\] RESULT (\d+) (\d+) [\d.]+ [\d.]+ \d+ \d+ (\d+)", l)
        if m and int(m[1]) not in res:
            res[int(m[1])] = (int(m[2]), int(m[3])); ordre.append(int(m[1]))

    ecarts = collections.defaultdict(lambda: [0, 0])
    for u in ordre:
        if u not in sit: continue
        prise, voids = res[u]
        if voids: continue
        d = abs(sit[u] - 310) % 360
        d = min(d, 360 - d)
        b = min(d // 30 * 30, 150)
        ecarts[b][0] += prise; ecarts[b][1] += 1

    print(f"\n=== {nom} ===")
    print("  ecart au cap 310    pris/joues     taux")
    for b in sorted(ecarts):
        p, n = ecarts[b]
        print(f"    {b:3d}-{b+29:3d} deg{'+' if b==150 else ' '}      {p:3d}/{n:3d}     {100*p/n:5.1f} %")
    return ecarts

analyse(1, "graine 0 (plate, 90,9 %)",     "13:07", "14:12")
analyse(2, "graine 1 (declinante, 82,0 %)", "13:07", "14:12")
