#!/usr/bin/env python3
"""enquete — LE DECLIN DE LA GRAINE 1 : site, ou tempo ?

⟨Fable⟩ « Une politique gelee, echantillonnee, sans gradient, NE PEUT PAS decliner ; ce
qui decline est donc soit l'ordre des sites, soit l'instance. Ton controle de sante a
certifie le mauvais objet : la doctrine a 51/51 prouve que le MONDE est intact, pas que
le TEMPO du run l'est. Un doMove scripte est indifferent a une latence qui grandit
episode apres episode ; une politique qui agit a chaque pas sous un budget de pas ne
l'est pas. »

On lit donc, serie par serie : le mode d'echec (immobile / budget epuise / autre) et la
duree MURALE par episode. Si les echecs tardifs sont des budgets epuises ET que la duree
murale monte, l'instance derivait.
"""
import re, glob, os, sys

FENETRES = [("13:07", "14:12")]     # la sonde de vacance
SERIES = 5

def lire(rpt, t0, t1):
    ep = []
    prec_t = None
    for l in open(rpt, errors="ignore"):
        if not (len(l) > 8 and l[2] == ":" and l[:2].isdigit()): continue
        h = l[:5]
        if h < t0 or h > t1: continue
        m = re.search(r"\] RESULT (\d+) (\d+) ([\d.]+) ([\d.]+) (\d+) (\d+) (\d+) (\d+)", l)
        if not m: continue
        t = int(l[:2])*3600 + int(l[3:5])*60 + int(l[6:8])
        mur = (t - prec_t) if prec_t is not None and 0 < t - prec_t < 300 else None
        prec_t = t
        ep.append(dict(uid=int(m[1]), prise=int(m[2]), temps=float(m[3]),
                       dfin=float(m[4]), voids=int(m[7]), mur=mur))
    return ep

for inst, nom in [(1, "graine 0 (plate)"), (2, "graine 1 (declinante)")]:
    R = sorted(glob.glob(f"/mnt/c/Users/Younes/hmtech{inst}/*.rpt"), key=os.path.getmtime)
    R = [r for r in R if "2026-09-02_10-15" in r][0]
    ep = lire(R, *FENETRES[0])
    print(f"\n########## instance {inst} — {nom} : {len(ep)} episodes ##########")
    n = len(ep) // SERIES
    for s in range(SERIES):
        lot = ep[s*n:(s+1)*n]
        if not lot: continue
        rat = [e for e in lot if e["prise"] == 0 and e["voids"] == 0]
        murs = [e["mur"] for e in lot if e["mur"]]
        immobiles = [e for e in rat if e["dfin"] >= 29]
        budget    = [e for e in rat if e["dfin"] < 29 and e["temps"] >= 19.5]
        autres    = [e for e in rat if e["dfin"] < 29 and e["temps"] < 19.5]
        print(f"  serie {s+1} : {len(lot)-len(rat)}/{len(lot)}   echecs={len(rat):2d}"
              f"  (immobile={len(immobiles)}  budget_epuise={len(budget)}  autre={len(autres)})"
              f"   duree murale {sum(murs)/len(murs):5.2f} s/ep")
