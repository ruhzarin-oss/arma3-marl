#!/usr/bin/env python3
"""convertir.py — le journal de la nuit devient des tenseurs.

2,8 Go de texte en entrée, des tableaux binaires en sortie. C'est l'étape 0 du plan de Fable :
rien ne s'entraîne avant que ceci passe ses vérifications.

LES CINQ PIÈGES, CÂBLÉS ICI ⟨Fable, 03/08⟩
  1. le -1 de la géométrie est un MASQUE, jamais une valeur. Il sort dans un canal séparé.
  2. chaque arête porte l'ÂGE de son balayage — elle peut avoir 9 s de retard, et un modèle
     qui l'ignore croira que l'information est fraîche.
  3. on indexe sur le TICK DE SIMULATION, pas sur l'horloge murale : le ralenti du serveur
     touche l'horloge, pas la physique ⟨mesuré : à densité égale, tirs 1,03 · morts 1,00⟩.
  4. les identifiants sont suivis à travers la montée de 100 à 250 hommes. Aucun n'est
     recyclé ⟨vérifié sur 2 651 identifiants⟩, mais on le RE-vérifie ici.
  5. la découpe apprentissage/test se fait par BLOC DE TEMPS, jamais par tick tiré au sort —
     sinon le test a déjà vu la scène et toute mesure est fausse.

DEUX PASSES : la première inventorie, la seconde remplit.

POURQUOI ON N'INDEXE PAS PAR IDENTIFIANT. Premier jet : une colonne par identifiant distinct
de la nuit — 10 034, à cause des renforts continus qui remplacent les pertes. Résultat :
un tenseur de 69,57 Go vide à 97,5 %, puisqu'à un instant donné il n'y a que ~250 hommes.
On indexe donc par PLACE OCCUPÉE dans le tick, et l'identifiant devient un canal comme un
autre. Le tenseur tombe à ~2,3 Go, et la correspondance place->identifiant se relit à tout
moment depuis le canal 0.
"""
import re, sys, json, hashlib, os
import numpy as np
from collections import defaultdict

LOG = sys.argv[1] if len(sys.argv) > 1 else '/mnt/data/corpus/nuit_20260803.log'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/mnt/data/corpus/tenseurs'
os.makedirs(OUT, exist_ok=True)

# 11 grandeurs par homme, dans l'ordre où l'émetteur les écrit
CHAMPS = ['id','x','y','z','vivant','camp','tir','azimut','posture','suppression','neuf']
NC = len(CHAMPS)                          # l'identifiant est un CANAL, pas un index de ligne

re_S   = re.compile(r'HMT\|S\|(\d+)\|(\d+)\|(\d+)\|([\d.]+)\|(\d+)\|\[(.*)\]"?\s*$')
re_ent = re.compile(r'\[(-?\d+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(\d),(\d),(\d),(-?\d+),(\d),(-?[\d.]+),(\d)\]')
re_A   = re.compile(r'HMT\|A\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|([\d.]+)\|(.*?)"?\s*$')
re_AGE = re.compile(r'HMT\|AGE\|(\d+)\|([\d.]+)\|(.*?)"?\s*$')
re_kil = re.compile(r'HMT\|E\|killed\|([\d.]+)\|(-?\d+)\|(-?\d+)')
re_hit = re.compile(r'HMT\|E\|hit\|([\d.]+)\|(-?\d+)\|(-?\d+)\|([\d.]+)')
re_fir = re.compile(r'HMT\|E\|fired\|([\d.]+)\|(-?\d+)')
re_spw = re.compile(r'HMT\|N\|spawn\|([\d.]+)\|(\d+)\|(-?[\d.]+)\|(-?[\d.]+)\|(-?[\d.]+)\|(\d)\|(\S+)\|(\S+)')

# ===================== PASSE 1 — INVENTAIRE =====================
print("PASSE 1 — inventaire", flush=True)
ticks_vus = defaultdict(set)       # tick -> morceaux reçus
ticks_tot = {}                     # tick -> morceaux annoncés
ticks_n   = defaultdict(int)       # tick -> entités effectivement lues
ids = set()
n_S = n_A = n_AGE = 0
for l in open(LOG, errors='ignore'):
    m = re_S.search(l)
    if m:
        n_S += 1
        t, morceau, total = int(m.group(1)), int(m.group(2)), int(m.group(3))
        ticks_vus[t].add(morceau); ticks_tot[t] = total
        for e in re_ent.finditer(m.group(6)):
            ids.add(int(e.group(1))); ticks_n[t] += 1
        continue
    if re_A.search(l):   n_A += 1;   continue
    if re_AGE.search(l): n_AGE += 1

# PIÈGE 4 — un tick amputé est REJETÉ, pas rafistolé. Le total annoncé sert à ça.
complets = sorted(t for t in ticks_vus if len(ticks_vus[t]) == ticks_tot[t])
amputes  = len(ticks_vus) - len(complets)
ids = sorted(i for i in ids if i > 0)
T = len(complets)
NMAX = max((ticks_n[t] for t in complets), default=0)
N = NMAX + 8                       # marge : la population de Battle Lines n'a pas de plafond connu
print(f"  lignes de nœuds {n_S}  arêtes {n_A}  âges {n_AGE}")
print(f"  ticks : {len(ticks_vus)}   complets {len(complets)} ({len(complets)/max(len(ticks_vus),1):.1%})   amputés {amputes} (REJETÉS)")
print(f"  identifiants distincts sur la nuit : {len(ids)}  (renforts inclus)")
print(f"  entités simultanées, maximum : {NMAX}  -> {N} places réservées")
print(f"  tenseur de nœuds : {T} x {N} x {NC}  =  {T*N*NC*4/1e9:.2f} Go en float32", flush=True)

tpos = {t: i for i, t in enumerate(complets)}

# ===================== PASSE 2 — REMPLISSAGE =====================
print("\nPASSE 2 — remplissage", flush=True)
X = np.lib.format.open_memmap(f'{OUT}/noeuds.npy', mode='w+', dtype=np.float32, shape=(T, N, NC))
M = np.lib.format.open_memmap(f'{OUT}/presence.npy', mode='w+', dtype=bool, shape=(T, N))
temps = np.zeros(T, dtype=np.float32)
curseur = np.zeros(T, dtype=np.int32)      # les morceaux d'un tick se remplissent à la suite

aretes = []      # (tick, de, vers, knowsAbout, vue, mesuree)
ages   = []      # (tick, homme, age, candidats, ecartes)
morts  = []      # (temps, victime, tueur)
impacts= []      # (temps, cible, tireur, degats)
tirs   = []      # (temps, tireur)
naiss  = {}      # id -> (temps, type, rang)

for l in open(LOG, errors='ignore'):
    m = re_S.search(l)
    if m:
        t = int(m.group(1))
        i = tpos.get(t)
        if i is None: continue          # tick amputé : on n'en prend RIEN
        temps[i] = float(m.group(4))
        j = curseur[i]
        for e in re_ent.finditer(m.group(6)):
            if j >= N: break
            X[i, j, :] = [float(e.group(k)) for k in range(1, 12)]   # canal 0 = identifiant
            M[i, j] = True
            j += 1
        curseur[i] = j
        continue
    m = re_A.search(l)
    if m:
        t = int(m.group(1))
        for seg in m.group(6).split(';'):
            p = seg.split(',')
            if len(p) != 4: continue
            try: a, b, k, v = int(p[0]), int(p[1]), float(p[2]), int(p[3])
            except ValueError: continue
            # les arêtes portent les IDENTIFIANTS, pas des places : une place change de sens
            # d'un tick à l'autre, un identifiant non.
            # PIÈGE 1 — le -1 devient un MASQUE, il ne se mélange pas aux valeurs
            aretes.append((t, a, b, k, (v if v >= 0 else 0), (1 if v >= 0 else 0)))
        continue
    m = re_AGE.search(l)
    if m:
        t = int(m.group(1))
        for seg in m.group(3).split(';'):
            p = seg.split(',')
            if len(p) != 4: continue
            try:
                h = int(p[0])
                ages.append((t, h, float(p[1]), int(p[2]), int(p[3])))
            except ValueError: pass
        continue
    m = re_kil.search(l)
    if m: morts.append((float(m.group(1)), int(m.group(2)), int(m.group(3)))); continue
    m = re_hit.search(l)
    if m: impacts.append((float(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4)))); continue
    m = re_fir.search(l)
    if m: tirs.append((float(m.group(1)), int(m.group(2)))); continue
    m = re_spw.search(l)
    if m: naiss[int(m.group(2))] = (float(m.group(1)), m.group(7), m.group(8))

X.flush(); M.flush()
aretes = np.array(aretes, dtype=np.float32) if aretes else np.zeros((0,6), np.float32)
ages   = np.array(ages,   dtype=np.float32) if ages   else np.zeros((0,5), np.float32)
print(f"  arêtes retenues : {len(aretes)}   âges : {len(ages)}")
print(f"  morts {len(morts)}   impacts {len(impacts)}   tirs {len(tirs)}", flush=True)

# ============ RÉCUPÉRATION DES MORTS ORPHELINES ============
# 76 % des morts sans tueur ont un impact enregistré dans les 5 s ⟨mesuré ce matin⟩.
# Le tueur est donc récupérable par jointure. On MARQUE la provenance : une attribution
# reconstruite ne doit jamais se confondre avec une attribution directe.
print("\nRÉATTRIBUTION DES MORTS", flush=True)
par_cible = defaultdict(list)
for t, c, tir, d in impacts:
    if tir > 0: par_cible[c].append((t, tir))
for v in par_cible.values(): v.sort()

recup = 0
morts_f = []                       # (temps, victime, tueur, source)  source 0=direct 1=reconstruit 2=inconnu
for t, vic, k in morts:
    if k > 0:
        morts_f.append((t, vic, k, 0)); continue
    cands = [(tt, tir) for tt, tir in par_cible.get(vic, []) if t - 5.0 <= tt <= t]
    if cands:
        morts_f.append((t, vic, cands[-1][1], 1)); recup += 1
    else:
        morts_f.append((t, vic, -1, 2))
morts_f = np.array(morts_f, dtype=np.float32)
d = (morts_f[:,3] == 0).sum(); r = (morts_f[:,3] == 1).sum(); u = (morts_f[:,3] == 2).sum()
tot = len(morts_f)
print(f"  directes      : {d}  ({d/tot:.0%})")
print(f"  reconstruites : {r}  ({r/tot:.0%})   <- marquées, jamais confondues")
print(f"  sans cause    : {u}  ({u/tot:.0%})")
print(f"  attribuées au total : {(d+r)/tot:.0%}  (contre {d/tot:.0%} sans la jointure)", flush=True)

# ============ PIÈGE 5 — DÉCOUPE PAR BLOC DE TEMPS ============
# Jamais un tick tiré au sort : deux ticks voisins montrent la même scène à 200 ms d'écart.
# Le modèle testé aurait déjà vu la réponse. On coupe en blocs contigus et on en met de côté.
BLOC = 3000                                    # ~10 min de simulation par bloc
nb = max(T // BLOC, 3)
bornes = np.linspace(0, T, nb + 1).astype(int)
rng = np.random.default_rng(7)
ordre = rng.permutation(nb)
n_test = max(1, nb // 5)
blocs_test = set(ordre[:n_test].tolist())
split = np.zeros(T, dtype=np.int8)             # 0 = apprentissage, 1 = tenu à l'écart
for b in range(nb):
    if b in blocs_test: split[bornes[b]:bornes[b+1]] = 1
print(f"\nDÉCOUPE : {nb} blocs contigus, {n_test} tenus à l'écart "
      f"({split.mean():.0%} des ticks) — par BLOC, jamais par tick", flush=True)

np.save(f'{OUT}/aretes.npy', aretes)
np.save(f'{OUT}/ages.npy', ages)
np.save(f'{OUT}/morts.npy', morts_f)
np.save(f'{OUT}/temps.npy', temps)
np.save(f'{OUT}/split.npy', split)
np.save(f'{OUT}/ids.npy', np.array(ids, dtype=np.int32))

meta = {
    'source': LOG,
    'empreinte_source': hashlib.sha256(open(LOG,'rb').read(1<<26)).hexdigest()[:16] + '_partiel',
    'ticks_total': len(ticks_vus), 'ticks_complets': T, 'ticks_amputes': amputes,
    'places': N, 'entites_max_simultanees': int(NMAX), 'identifiants_nuit': len(ids),
    'champs': CHAMPS,
    'aretes': int(len(aretes)), 'aretes_mesurees': int(aretes[:,5].sum()) if len(aretes) else 0,
    'morts': int(tot), 'morts_directes': int(d), 'morts_reconstruites': int(r), 'morts_sans_cause': int(u),
    'tirs': len(tirs), 'impacts': len(impacts),
    'blocs': nb, 'blocs_tenus_a_lecart': n_test,
    'note_masque': 'aretes[:,4]=vue, aretes[:,5]=mesuree (0 => vue non observee, ne pas lire comme absence de vue)',
}
json.dump(meta, open(f'{OUT}/meta.json','w'), indent=2, ensure_ascii=False)
print(f"\nécrit dans {OUT}")
for k, v in meta.items():
    if k != 'source': print(f"  {k:24s} {v}")
