#!/usr/bin/env python3
"""banc_essai_code.py — LE TEST BIDON : un monde dont on connait deja les reponses.

Pourquoi. Un modele qui echoue peut echouer pour deux raisons tres differentes : le monde est dur,
ou mon code est faux. Tant qu on ne les separe pas, on ne sait rien. On fabrique donc un examen
dont on connait le corrige.

Pourquoi PAS le bac a sable condamne, comme prevu : son moteur leve des assertions GPU des qu on
le pousse hors de son regime habituel (trois endroits differents en une heure). Deboguer un moteur
qu on a condamne pour perdre du temps sur un test de code serait absurde. On ecrit donc un monde
JOUET, en trente lignes, dont la loi est ECRITE ICI et donc parfaitement connue :

  - chaque attaquant marche vers l objectif a vitesse constante, avec un decalage d angle propre a
    sa manoeuvre : trajectoire deterministe, donc predictible EXACTEMENT ;
  - un attaquant meurt avec une probabilite qui decroit avec la distance a l objectif : dynamique
    stochastique mais de loi connue ;
  - les defenseurs sont immobiles.

Un modele du monde correctement code doit predire les trajectoires presque parfaitement — il n y a
rien a deviner — et apprendre la loi de mortalite. S il n y arrive pas, le code est faux, et rien
de ce qu il dira d Arma ne veut dire quoi que ce soit.

Ecrit dans le MEME schema que le banc Arma, pour que le meme chargeur les lise.
"""
import argparse, json, math, os, random

ap = argparse.ArgumentParser()
ap.add_argument('--episodes', type=int, default=400)
ap.add_argument('--pas', type=int, default=60)
ap.add_argument('--sortie', default='/mnt/data2/lab/replay/banc_essai')
ap.add_argument('--graine', type=int, default=0)
a = ap.parse_args()
random.seed(a.graine)
os.makedirs(a.sortie, exist_ok=True)
for f in os.listdir(a.sortie):
    os.remove(os.path.join(a.sortie, f))

# LES MANOEUVRES DOIVENT SE DISTINGUER, sinon l examen est infalsifiable. Premiere version :
# toutes prenaient l objectif 100 % du temps, donc predire << 100 % partout >> passait trivialement
# et le classement portait sur des ex aequo. C est exactement le piege qu on s interdit ailleurs.
# Ici le biais d angle allonge le trajet, donc l exposition, donc les pertes : chaque manoeuvre a
# desormais son propre taux de prise, et l ordre est CONNU par construction.
MANOEUVRES = {'frontal': 0.0, 'supfront': 0.30, 'envelop': 0.75, 'reckless': -0.15}
VITESSE = 6.0           # m par pas
R_SPAWN = 170.0
P_MORT = 0.075          # a l objectif ; decroit avec la distance

ecrit = 0
for nom, biais in MANOEUVRES.items():
    for A in (8, 12):
        n = a.episodes // (len(MANOEUVRES) * 2)
        for _ in range(n):
            # depart : arc autour de l objectif
            az0 = random.uniform(0, 2 * math.pi)
            att = []
            for j in range(A):
                d = az0 + (j - A / 2) * 0.05
                att.append([R_SPAWN * math.sin(d), R_SPAWN * math.cos(d), 1])
            defs = [[45 * math.sin(2 * math.pi * k / 8), 45 * math.cos(2 * math.pi * k / 8), 1]
                    for k in range(8)]
            frames = []
            for t in range(a.pas):
                frames.append({
                    't': t,
                    'west': [[round(w[0], 2), round(w[1], 2), w[2], 1] for w in att],
                    'east': [[round(e[0], 2), round(e[1], 2), e[2]] for e in defs],
                    'firew': [0] * A,
                })
                for w in att:
                    if not w[2]:
                        continue
                    r = math.hypot(w[0], w[1])
                    if r > 1.0:
                        # cap vers l objectif, plus le biais de la manoeuvre : DETERMINISTE
                        ang = math.atan2(-w[0], -w[1]) + biais
                        w[0] += VITESSE * math.sin(ang)
                        w[1] += VITESSE * math.cos(ang)
                    # loi de mortalite CONNUE : forte pres de l objectif, nulle au-dela de 200 m
                    p = P_MORT * max(0.0, 1.0 - r / 200.0)
                    if random.random() < p:
                        w[2] = 0
            vivants = sum(1 for w in att if w[2])
            pris = any(w[2] and math.hypot(w[0], w[1]) < 25.0 for w in att)
            json.dump({'fob': [0.0, 0.0], 'A': A, 'B': 8, 'mode': nom,
                       'metrics': {'east_start': 8, 'west_start': A, 'steps': len(frames),
                                   'took': pris, 'west_end': vivants},
                       'frames': frames,
                       '_meta': {'mode': nom, 'A': A, 'rep': ecrit, 'instance': -1}},
                      open(os.path.join(a.sortie, 'n0_%s_A%d_r%04d.json' % (nom, A, ecrit)), 'w'))
            ecrit += 1
print('ecrits : %d episodes dans %s' % (ecrit, a.sortie))
print('  loi : marche a %.0f m/pas vers l objectif avec biais d angle par manoeuvre ;' % VITESSE)
print('        mortalite %.3f par pas a l objectif, nulle au-dela de 200 m.' % P_MORT)
print('BANC_ESSAI_DONE')
