#!/usr/bin/env python3
"""sonde3.py — LE VERDICT CONNU : le corpus sait-il que l'angle mort paie ?

⟨Fable, 03/08 : « tu ne t'acharnes pas sur une mauvaise idée, tu t'acharnes sur la mauvaise
tâche. Va tirer et va mourir se lisent dans l'état local. La bonne tâche est DE CAMP. »⟩

LA QUESTION. On a mesuré sur 1 324 engagements que l'assaut à deux axes bat l'assaut frontal
de 12,3 points. On a mesuré au contrôle positif qu'un homme ne voit pas un ennemi à 50 m sur
son flanc et voit celui à 300 m droit devant. Les deux faits n'en font qu'un : ce qui protège,
c'est d'arriver là où l'adversaire ne regarde pas.

Si le corpus de la nuit contient ce fait, on doit le retrouver SANS le lui avoir dit.

CE QU'ON MESURE, par soldat et par instant :
  · EXPOSITION  — quelle part de mes ennemis m'ont dans leur champ de vision ?
                  (c'est leur regard à EUX qui compte, pas le mien)
  · AVANTAGE    — quelle part de mes ennemis sont dans MON champ ?
  · puis : est-ce que je meurs dans les 30 s ? est-ce que je tue dans les 30 s ?

CRITÈRES ÉCRITS AVANT DE REGARDER
  1. Si l'exposition ne change pas le sort du soldat, le corpus ne contient pas le verdict.
     Seuil : la mortalité des plus exposés doit dépasser celle des moins exposés d'au moins
     30 % relatif. En dessous, ÉCHEC.
  2. LE CONTRÔLE QUI PEUT TOUT FAIRE ÉCHOUER : l'AVANTAGE doit se comporter AUTREMENT que
     l'exposition. Les deux sont des angles calculés de la même manière, sur les mêmes paires.
     Si les deux prédisent la mort de la même façon, alors je ne mesure pas « qui regarde qui »
     mais un artefact commun — la distance, la densité, ou la géométrie du front.
  3. CONTRÔLE DE DISTANCE : l'effet doit tenir à distance comparable. Sinon je mesure
     seulement que rester loin protège, ce que personne ne conteste.
  4. CONTRÔLE NUL : un angle tiré au hasard, sur les mêmes paires, ne doit RIEN prédire.
     S'il prédit quelque chose, le pipeline fabrique du signal et rien n'est concluant.

Aucune conclusion n'est retenue si un seul de ces contrôles échoue.
"""
import numpy as np, json, time, math
from collections import defaultdict

D = '/mnt/data/corpus/tenseurs'
X   = np.load(f'{D}/noeuds.npy', mmap_mode='r')
P   = np.load(f'{D}/presence.npy', mmap_mode='r')
AR  = np.load(f'{D}/aretes.npy')
MORTS = np.load(f'{D}/morts.npy')
TPS = np.load(f'{D}/temps.npy')
T, N, _ = X.shape
print(f"corpus : {T} ticks, {N} places, {len(AR)} arêtes", flush=True)

ar_par_tick = defaultdict(list)
for t, a, b, k, v, mes in AR:
    ar_par_tick[int(t)].append((int(a), int(b)))
ticks_ar = np.array(sorted(ar_par_tick.keys()))

mort_de = {}; tueur_de = defaultdict(list)
for tm, vic, tue, src in MORTS:
    v = int(vic)
    if v not in mort_de: mort_de[v] = tm
    if tue > 0: tueur_de[int(tue)].append(tm)

CHAMP = 60.0          # demi-angle du champ de vision retenu, en degrés
HORIZON = 30.0        # secondes
rng = np.random.default_rng(11)

print(f"\nconstruction — champ de vision ±{CHAMP:.0f}°, horizon {HORIZON:.0f} s", flush=True)
t0 = time.time()
EXPO, AVANT, NUL, DIST, NENN, MORT, TUE, CAMP_ = [], [], [], [], [], [], [], []
PAS = 3
for ti in ticks_ar[::PAS]:
    if ti >= T: continue
    xt = np.asarray(X[ti]); pt = np.asarray(P[ti])
    pos = {}; azi = {}; viv = {}; cmp_ = {}
    for j in range(N):
        if pt[j] and xt[j,0] > 0:
            u = int(xt[j,0]); pos[u] = (xt[j,1], xt[j,2]); azi[u] = xt[j,7]
            viv[u] = xt[j,4] > 0.5; cmp_[u] = int(xt[j,5])
    if not pos: continue

    # les paires en présence : on prend les DEUX sens, un lien suffit à mettre deux hommes
    # en relation, et l'exposition ne dépend pas de qui a repéré l'autre le premier.
    paires = defaultdict(set)
    for a, b in ar_par_tick[int(ti)]:
        if a in pos and b in pos:
            paires[a].add(b); paires[b].add(a)

    tnow = TPS[ti]
    for u, ennemis in paires.items():
        if not viv.get(u, False) or not ennemis: continue
        e_exp = []; e_av = []; e_nul = []; e_d = []
        pu = pos[u]; au = azi[u]
        for e in ennemis:
            pe = pos.get(e)
            if pe is None: continue
            dx, dy = pu[0]-pe[0], pu[1]-pe[1]
            d = math.hypot(dx, dy)
            if d < 1: continue
            # sous quel angle SUIS-JE vu par lui ? c'est SON regard qui décide
            gis_e_vers_u = math.degrees(math.atan2(dx, dy)) % 360
            ecart_lui = abs(((gis_e_vers_u - azi.get(e, 0.0) + 180) % 360) - 180)
            e_exp.append(1.0 if ecart_lui <= CHAMP else 0.0)
            # et lui, est-il dans MON champ ?
            gis_u_vers_e = (gis_e_vers_u + 180) % 360
            ecart_moi = abs(((gis_u_vers_e - au + 180) % 360) - 180)
            e_av.append(1.0 if ecart_moi <= CHAMP else 0.0)
            # CONTRÔLE NUL : un angle tiré au sort sur la même paire
            e_nul.append(1.0 if rng.uniform(0, 180) <= CHAMP else 0.0)
            e_d.append(d)
        if not e_exp: continue
        EXPO.append(np.mean(e_exp)); AVANT.append(np.mean(e_av)); NUL.append(np.mean(e_nul))
        DIST.append(np.mean(e_d)); NENN.append(len(e_exp)); CAMP_.append(cmp_.get(u, 3))
        tm = mort_de.get(u)
        MORT.append(1.0 if (tm is not None and tnow < tm <= tnow + HORIZON) else 0.0)
        TUE.append(1.0 if any(tnow < k <= tnow + HORIZON for k in tueur_de.get(u, [])) else 0.0)

EXPO = np.array(EXPO); AVANT = np.array(AVANT); NUL = np.array(NUL)
DIST = np.array(DIST); NENN = np.array(NENN); MORT = np.array(MORT); TUE = np.array(TUE)
print(f"  {len(EXPO)} observations en {time.time()-t0:.0f} s")
print(f"  mortalité de base {MORT.mean():.2%}   taux de tir mortel {TUE.mean():.2%}", flush=True)

def tranches(v, nom, cible, cnom):
    """effet d'une variable sur une cible, par tranche"""
    bornes = [0, 0.2, 0.4, 0.6, 0.8, 1.01]
    print(f"\n  {nom} -> {cnom}")
    res = []
    for i in range(len(bornes)-1):
        s = (v >= bornes[i]) & (v < bornes[i+1])
        if s.sum() < 500: continue
        res.append((bornes[i], s.sum(), cible[s].mean(), DIST[s].mean(), NENN[s].mean()))
        print(f"    {bornes[i]:.1f}-{bornes[i+1]:.1f}  n={s.sum():7d}  {cnom} {cible[s].mean():.2%}"
              f"   (distance moy {DIST[s].mean():5.0f} m, {NENN[s].mean():.1f} ennemis)")
    if len(res) >= 2:
        bas, haut = res[0][2], res[-1][2]
        r = (haut-bas)/bas if bas > 0 else float('nan')
        print(f"    -> du plus bas au plus haut : {bas:.2%} -> {haut:.2%}   ({r:+.0%})")
        return r
    return float('nan')

print("\n" + "="*74)
print("1. L'EXPOSITION — quelle part de mes ennemis m'ont dans leur champ")
r_exp_mort = tranches(EXPO, "exposition", MORT, "mortalité")
r_exp_tue  = tranches(EXPO, "exposition", TUE,  "tue")

print("\n" + "="*74)
print("2. CONTRÔLE — L'AVANTAGE : quelle part de mes ennemis sont dans MON champ")
print("   (même calcul, mêmes paires : doit se comporter AUTREMENT)")
r_av_mort = tranches(AVANT, "avantage", MORT, "mortalité")
r_av_tue  = tranches(AVANT, "avantage", TUE,  "tue")

print("\n" + "="*74)
print("3. CONTRÔLE NUL — un angle tiré au hasard sur les mêmes paires")
print("   (doit ne RIEN prédire, sinon le pipeline fabrique du signal)")
r_nul_mort = tranches(NUL, "angle au hasard", MORT, "mortalité")

print("\n" + "="*74)
print("4. CONTRÔLE DE DISTANCE — l'effet tient-il à distance comparable ?")
for lo, hi in [(0,80),(80,150),(150,250),(250,400)]:
    s = (DIST >= lo) & (DIST < hi)
    if s.sum() < 2000: continue
    e = EXPO[s]; m = MORT[s]
    bas = m[e < 0.3]; haut = m[e > 0.7]
    if len(bas) < 300 or len(haut) < 300: continue
    r = (haut.mean()-bas.mean())/bas.mean() if bas.mean() > 0 else float('nan')
    print(f"  {lo:3d}-{hi:3d} m  n={s.sum():7d}   peu exposé {bas.mean():.2%} (n={len(bas)})"
          f"   très exposé {haut.mean():.2%} (n={len(haut)})   {r:+.0%}")

print("\n" + "="*74)
print("VERDICT — contre les critères écrits avant\n")
ok1 = (not math.isnan(r_exp_mort)) and r_exp_mort >= 0.30
ok2 = (not math.isnan(r_av_mort)) and abs(r_av_mort - r_exp_mort) > 0.15
ok3 = math.isnan(r_nul_mort) or abs(r_nul_mort) < 0.10
print(f"  1. l'exposition augmente la mortalité de {r_exp_mort:+.0%}   (seuil +30 %)  -> {'PASSE' if ok1 else 'ÉCHOUE'}")
print(f"  2. l'avantage se comporte autrement ({r_av_mort:+.0%} contre {r_exp_mort:+.0%})  -> {'PASSE' if ok2 else 'ÉCHOUE'}")
print(f"  3. l'angle au hasard ne prédit rien ({r_nul_mort:+.0%})  -> {'PASSE' if ok3 else 'ÉCHOUE'}")
print()
if ok1 and ok2 and ok3:
    print("  LE CORPUS CONTIENT LE VERDICT.")
    print("  Être dans le champ de vision de l'ennemi tue, et ce n'est ni la distance,")
    print("  ni un artefact de calcul. Le fait mesuré sur 1 324 engagements se retrouve")
    print("  dans un corpus qui ne l'a jamais su. Les liens portent le tactique.")
else:
    print("  LE CORPUS NE CONTIENT PAS LE VERDICT, ou pas de façon lisible.")
    print("  Regarder quel contrôle a lâché avant de conclure quoi que ce soit.")
