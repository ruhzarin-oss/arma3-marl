#!/usr/bin/env python3
"""flanc_ideal.py — LE CONTRÔLE POSITIF DU BANC.

⟨Fable, 03/08 : « Tu as écrit le seuil avant, mais pas le contrôle positif. Fais passer au
banc un flanc scripté à la main, large et profond. S'il n'atteint pas non plus les 25 %,
aucun agent ne peut réussir — le banc mesure alors la géométrie de Battle Lines, pas la
qualité de l'agent. Une mesure doit savoir échouer, et aussi savoir RÉUSSIR. »⟩

Le chemin est calculé EXHAUSTIVEMENT, pas appris. Et son critère de choix vient d'ARMA, pas
de mon simulateur : l'azimut qui échappe au cône de 35° du plus grand nombre de défenseurs.
⟨demi-cône mesuré le 03/08 : plateau plat à 4,00 de 0° à 30°, zéro dès 40°⟩

Si ce chemin-là ne bat pas la ligne droite de 25 %, le banc n'a pas de région de réussite.
"""
import json, math, numpy as np

CHAMP = 35.0
RAYON = 80.0
NPTS  = 21

src = json.load(open('/mnt/data/corpus/trajectoires_agent.json'))[:20]
sorties = []
stats = []
for c in src:
    defs = np.array(c['defenseurs'])          # (n, 3) : x, y, azimut
    d_xy, d_az = defs[:, :2], defs[:, 2]

    # balayage exhaustif : pour chaque azimut d'approche, combien de défenseurs me voient ?
    meilleur, score_min = None, 1e9
    profil = []
    for a in range(0, 360, 3):
        p = np.array([math.sin(math.radians(a)), math.cos(math.radians(a))]) * RAYON
        v = p - d_xy
        gis = np.degrees(np.arctan2(v[:, 0], v[:, 1])) % 360
        ec = np.abs((gis - d_az + 180) % 360 - 180)
        vus = int((ec <= CHAMP).sum())
        profil.append(vus)
        if vus < score_min:
            score_min, meilleur = vus, a
    stats.append((score_min, min(profil), max(profil), len(defs)))

    # approche radiale depuis le meilleur azimut : le chemin le plus direct qui reste hors des cônes
    u = np.array([math.sin(math.radians(meilleur)), math.cos(math.radians(meilleur))])
    traj = [(u * RAYON * (1 - i/(NPTS-1))).tolist() for i in range(NPTS)]
    sorties.append(dict(config=c['config'], defenseurs=c['defenseurs'],
                        agent=[[float(x), float(y)] for x, y in traj],
                        postures=[0]*NPTS, depart=traj[0]))

json.dump(sorties, open('/mnt/data/corpus/trajectoires_agent.json','w'))
s = np.array(stats)
print(f"  {len(sorties)} chemins optimaux calcules")
print(f"  defenseurs par config : {s[:,3].mean():.1f}")
print(f"\n  COMBIEN DE DEFENSEURS VOIENT L APPROCHANT, au MEILLEUR azimut :")
print(f"    minimum atteignable : {s[:,0].mean():.2f} en moyenne")
print(f"    configurations ou AUCUN ne voit : {(s[:,0]==0).sum()} / {len(s)}")
print(f"    configurations ou au moins un voit TOUJOURS : {(s[:,0]>0).sum()} / {len(s)}")
print(f"\n  pire azimut : {s[:,2].mean():.1f} defenseurs en moyenne")
print(f"\n  -> si beaucoup de configs ont un minimum > 0, le banc mesure la GEOMETRIE")
print(f"     de Battle Lines et non la qualite de l agent.")
