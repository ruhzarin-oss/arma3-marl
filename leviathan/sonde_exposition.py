#!/usr/bin/env python3
"""sonde_exposition.py — le banc repare SOUS-PUNIT-IL l exposition ?

La question, posee par l architecte et restee ouverte. L executeur temeraire — debout, sprint,
ignore le feu — domine partout, sur la prise ET sur les pertes. Deux lectures possibles :
  (a) FAIT DU MONDE : il traverse la zone dangereuse plus vite, donc il y passe moins de temps.
      Notre loi mesuree dit que la conscience adverse ne distingue pas l homme immobile du coureur,
      donc courir ne reduit pas la detection mais COMPRIME la duree d exposition.
  (b) DEFAUT DU BANC : les defenseurs touchent moins bien une cible rapide qu ils ne le devraient,
      et le monde recompense la vitesse pour une mauvaise raison. Ce serait le jumeau inverse du
      bac a sable quatre fois trop letal.

Le temoin qui separe les deux : le TAUX DE MORT PAR SECONDE PASSEE A UNE DISTANCE DONNEE.
  - si le taux par seconde est le MEME pour toutes les manoeuvres a distance egale, alors seule la
    duree change -> lecture (a), c est un fait, le modele devra l apprendre ;
  - si le temeraire meurt MOINS par seconde a distance egale, le monde le protege -> lecture (b),
    le banc a un defaut neuf et les cibles de la porte en heritent.

On mesure sur les episodes DEJA collectes : aucune nouvelle mesure sur le serveur.
Le premier temoin que j avais pris — << temps passe a moins de cent metres >> — melangeait duree et
intensite. Celui-ci les separe.
"""
import glob, json, math, os
from collections import defaultdict

SORTIE = '/mnt/data2/lab/replay/nuit0'
MODES = ['frontal', 'supfront', 'envelop', 'reckless']
BANDES = [(0, 40), (40, 70), (70, 100), (100, 140), (140, 200)]
PAS_S = 3.28          # duree d un pas de decision, en secondes

# temps passe et morts survenues, par manoeuvre et par bande de distance
temps = defaultdict(float)
morts = defaultdict(int)
morts_pire = defaultdict(int)
par_mode_A = defaultdict(lambda: {'ep': 0})

for f in sorted(glob.glob(os.path.join(SORTIE, 'n0_*.json'))):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    m, meta = d.get('metrics', {}), d.get('_meta', {})
    if m.get('east_start') != 8 or m.get('steps', 0) < 3:
        continue
    mode, A = meta.get('mode'), meta.get('A')
    fob, fr = d.get('fob'), d.get('frames', [])
    if not fob or len(fr) < 3:
        continue
    fx, fy = fob[0], fob[1]
    par_mode_A[(mode, A)]['ep'] += 1
    prec = None
    for x in fr:
        w = x.get('west', [])
        for i, u in enumerate(w):
            if len(u) < 3:
                continue
            vivant = bool(u[2])
            dist = math.hypot(u[0] - fx, u[1] - fy)
            b = None
            for lo, hi in BANDES:
                if lo <= dist < hi:
                    b = (lo, hi)
                    break
            if b is None:
                continue
            if vivant:
                temps[(mode, b)] += PAS_S
            # une mort est comptee dans la bande ou l homme se trouvait AU PAS PRECEDENT
            if prec is not None and i < len(prec) and prec[i][2] and not vivant:
                pb = None
                pd = math.hypot(prec[i][0] - fx, prec[i][1] - fy)
                for lo, hi in BANDES:
                    if lo <= pd < hi:
                        pb = (lo, hi)
                        break
                if pb:
                    morts[(mode, pb)] += 1
                    # BORNE DE PIRE CAS sur le glissement de bande. Le pas fait 3,28 s et le sprint
                    # 5-6 m/s : une mort glisse d AU PLUS une bande, et toujours vers le LOIN
                    # (la position d il y a un pas est plus lointaine). On recompte donc en
                    # ramenant chaque mort d une bande vers l objectif — volontairement
                    # defavorable au resultat. Si l ecart survit a ca, le biais ne l explique pas.
                    j = BANDES.index(pb)
                    morts_pire[(mode, BANDES[max(0, j - 1)])] += 1
        prec = w

print('=== TAUX DE MORT PAR MINUTE PASSEE, PAR BANDE DE DISTANCE A L OBJECTIF ===')
print('  (si les manoeuvres se valent a distance egale, seule la DUREE les separe : c est un fait)')
print()
en_tete = '  %-10s' % 'mode'
for lo, hi in BANDES:
    en_tete += ' %11s' % ('%d-%d m' % (lo, hi))
print(en_tete)
tab = {}
for mode in MODES:
    ligne = '  %-10s' % mode
    for b in BANDES:
        t = temps[(mode, b)]
        k = morts[(mode, b)]
        if t < 60:
            ligne += ' %11s' % '-'
            continue
        taux = 60.0 * k / t
        tab[(mode, b)] = taux
        ligne += ' %11.2f' % taux
    print(ligne)

print()
print('  --- temps total passe par bande (minutes) ---')
for mode in MODES:
    print('  %-10s %s' % (mode, '  '.join('%6.0f' % (temps[(mode, b)] / 60.0) for b in BANDES)))

print()
print('=== LECTURE ===')
verdicts = []
for b in BANDES:
    vals = [(tab[(m, b)], m) for m in MODES if (m, b) in tab]
    if len(vals) < 3:
        continue
    vals.sort()
    bas, haut = vals[0], vals[-1]
    ecart = (haut[0] - bas[0]) / max(bas[0], 1e-9)
    tem = tab.get(('reckless', b))
    med = sorted(v for v, _ in vals)[len(vals) // 2]
    if tem is None:
        continue
    rel = (tem - med) / max(med, 1e-9)
    verdicts.append(rel)
    print('  %3d-%-3d m : temeraire %.2f/min | mediane %.2f/min | ecart %+.0f %%'
          % (b[0], b[1], tem, med, 100 * rel))

if verdicts:
    moy = sum(verdicts) / len(verdicts)
    print()
    if moy < -0.25:
        print('  >>> le temeraire meurt %.0f %% MOINS par minute a distance egale.' % (-100 * moy))
        print('      Le banc PROTEGE la vitesse : ce n est pas la duree qui explique sa victoire.')
        print('      Defaut du monde ; les cibles de la porte en heritent.')
    elif moy > 0.25:
        print('  >>> le temeraire meurt %.0f %% PLUS par minute a distance egale.' % (100 * moy))
        print('      Il gagne donc MALGRE une mortalite superieure, par la seule compression de la')
        print('      duree d exposition. C est un fait du monde.')
    else:
        print('  >>> a distance egale, les manoeuvres se valent (ecart %+.0f %%).' % (100 * moy))
        print('      Seule la DUREE d exposition les separe : la victoire du temeraire est un FAIT')
        print('      du monde, conforme a notre loi mesuree (courir ne reduit pas la detection,')
        print('      mais comprime le temps passe sous le feu). Les cibles de la porte sont saines.')
print()
print('=== BORNE DE PIRE CAS : morts ramenees d une bande VERS l objectif ===')
tabp = {}
for mode in MODES:
    ligne = '  %-10s' % mode
    for b in BANDES:
        t = temps[(mode, b)]
        if t < 60:
            ligne += ' %11s' % '-'
            continue
        taux = 60.0 * morts_pire[(mode, b)] / t
        tabp[(mode, b)] = taux
        ligne += ' %11.2f' % taux
    print(ligne)
vp = []
for b in BANDES:
    vals = [tabp[(m, b)] for m in MODES if (m, b) in tabp]
    if len(vals) < 3 or ('reckless', b) not in tabp:
        continue
    med = sorted(vals)[len(vals) // 2]
    vp.append((tabp[('reckless', b)] - med) / max(med, 1e-9))
if vp:
    moyp = sum(vp) / len(vp)
    print()
    print('  ecart du temeraire en PIRE CAS : %+.0f %%  (mesure brute : %+.0f %%)'
          % (100 * moyp, 100 * (sum(verdicts) / len(verdicts)) if verdicts else 0))
    if moyp < -0.10:
        print('  >>> l ecart SURVIT a la correction defavorable : le biais d attribution ne')
        print('      l explique pas.')
    else:
        print('  >>> l ecart NE SURVIT PAS : le biais d attribution suffit a l expliquer.')
        print('      La mesure brute ne prouve rien ; il faut la position au moment du tir.')
print('SONDE_EXPO_DONE')
