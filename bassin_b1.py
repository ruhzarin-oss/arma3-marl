#!/usr/bin/env python3
"""bassin_b1 — DECOUPER LE BASSIN DU BARREAU « SITE DEGELE ». Version 2.

⚠️ CE QUE LA VERSION 1 A RATE, et comment on l'a su. Elle heritait du critere de la
recherche d'origine : elle verifiait que le bout de la LIGNE DE VUE a 150 m est sec,
jamais que l'OBJECTIF REEL a 30 m l'est. Deux sites au bord d'une crique sont passes :
sol a 0 m sec, sol a 150 m sec de l'autre cote de la baie, objectif sous 60-70 cm d'eau.
La doctrine y a rate 2 fois sur 51 — le soldat ne bougeait pas d'un metre (dfin=30, vivant,
budget epuise). Et le MEME site reussissait 4/4 sur une autre instance, parce qu'avec un
jitter de ±1,2 m et ±6° l'objectif tombe tantot dans des hauts-fonds passables a gue,
tantot juste au-dela du seuil ou le pathfinding refuse.

⚠️ ON BORNE DONC LE TIRAGE, mais pas sur la difficulte : sur la POSSIBILITE. Un site dur
penalise une mauvaise politique plus qu'une bonne — c'est du signal. Un site ou l'issue
tient a l'humeur du moteur au bord de l'eau penalise tout le monde pareil — c'est du bruit
d'instrument. On exige 0,5 m de sol au-dessus du niveau de la mer sur TOUT le trajet.
"""
import re, json, random

BANDE_MIN = 1.00
HMIN_SEC  = 0.5
GELE = (8126.45, 10395.4)
GARDE = 200.0
GRAINE_SITE = 313131

cands = []
for l in open("/home/younes/arma3-marl/bassin_v2.txt"):
    m = re.search(r"BASSIN ([\d.-]+) ([\d.-]+) (\d+) ([\d.-]+) ([\d.-]+) ([\d.-]+) ([\d.-]+)", l)
    if m:
        cands.append(dict(x=float(m[1]), y=float(m[2]), az=int(m[3]), cl=float(m[4]),
                          dev=float(m[5]), pente=float(m[6]), hmin=float(m[7]),
                          score=round(float(m[4]) - 0.4*float(m[5]), 3)))

print(f"bassin brut               : {len(cands)}")
band = [r for r in cands if r["score"] >= BANDE_MIN]
print(f"bande score >= {BANDE_MIN:.2f}       : {len(band)}")
sec = [r for r in band if r["hmin"] >= HMIN_SEC]
print(f"trajet sec (hmin >= {HMIN_SEC} m) : {len(sec)}   ({len(band)-len(sec)} ecartes pour cause d'eau)")
loin = [r for r in sec if ((r["x"]-GELE[0])**2 + (r["y"]-GELE[1])**2)**0.5 >= GARDE]
print(f"hors des {GARDE:.0f} m du site gele : {len(loin)}   ({len(sec)-len(loin)} ecartes)")

FAUTIFS = [(8401.45, 9680.42, 300), (8346.45, 9680.42, 340)]
for f in FAUTIFS:
    dedans = any(abs(r["x"]-f[0])<1 and abs(r["y"]-f[1])<1 and r["az"]==f[2] for r in loin)
    print(f"  le site fautif [{f[0]:.0f},{f[1]:.0f}] az={f[2]} est-il encore la ? "
          f"{'OUI — LE FILTRE NE MARCHE PAS' if dedans else 'non, ecarte'}")

rng = random.Random(GRAINE_SITE)
rng.shuffle(loin)
n_j = len(loin) // 2
for nom, lot in [("jugement", loin[:n_j]), ("apprentissage", loin[n_j:])]:
    s = [r["score"] for r in lot]; p = [abs(r["pente"]) for r in lot]
    h = [r["hmin"] for r in lot]
    print(f"\n  {nom:14s} : {len(lot)} sites   score {min(s):.2f}-{max(s):.2f} (med {sorted(s)[len(s)//2]:.2f})"
          f"\n{'':18s}|pente| med {sorted(p)[len(p)//2]*100:.1f} % max {max(p)*100:.1f} %"
          f"   sol le plus bas du lot : {min(h):.1f} m")
    with open(f"/home/younes/arma3-marl/sites_{nom}.jsonl", "w") as f:
        for r in lot: f.write(json.dumps(r) + "\n")
