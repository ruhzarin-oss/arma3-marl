#!/usr/bin/env python3
"""generer_banc150b.py — LES CINQ BRAS, DONT L'AGENT.

⟨Fable, 04/08 : « Ou est l'agent ? A ce jour, l'agent n'a JAMAIS ete mesure par un
 instrument valide. »⟩

  agent         la trajectoire produite par le reseau, AVEC SES POSTURES
  droite        le temoin, meme depart
  droite_bis    le temoin rejoue -> controle nul
  oracle        le meilleur chemin depuis CE depart (plus court chemin de goulot)
  oracle_libre  le meilleur chemin en CHOISISSANT son depart -> le plafond

Les deux oracles sont calcules DEBOUT : ce sont des plafonds geometriques purs, pas des
concurrents a armes egales. L'agent, lui, porte ses postures — l'instrument ne les force
plus. ⟨le banc precedent ecrivait setUnitPos "UP" et eteignait le repertoire⟩

CHAQUE POINT PORTE SA POSTURE : [x, y, posture] avec 0 debout · 1 accroupi · 2 couche.

CE QUI FERAIT ECHOUER CETTE GENERATION — ecrit avant :
  C1 coherence de expo (vectorise contre boucle explicite), ecart < 1e-9
  C2 optimalite sur grille : l'oracle ne peut pas etre battu par la droite, meme espace
  C3 emboitement : l'oracle libre ne peut pas etre pire que l'oracle contraint
  C4 l'agent doit PARTIR du meme cercle que les autres (sinon rien n'est comparable)
"""
import json, math, sys
import numpy as np
import geom_ombre as g

TRAJ   = '/mnt/data/corpus/trajectoires_agent150.json'
SORTIE = '/home/younes/arma3-marl/bancs/arma/donnees_banc150b.sqf'
R_DEP, R_ARR, PAS_PT = 150.0, 40.0, 4.0

src = json.load(open(TRAJ))[:20]
print(f"  {len(src)} configurations · depart {R_DEP:.0f} m · arrivee {R_ARR:.0f} m")

e1 = g.controle_coherence(np.array(src[0]['defenseurs'], float))
print(f"  C1 coherence expo : {e1:.1e}", end='  ')
if e1 > 1e-9: raise SystemExit("ECHEC C1")
print("OK")

def ech(poly, post=None, pas=PAS_PT):
    """rechantillonne a pas fixe et porte la posture au sommet le plus proche."""
    poly = np.asarray(poly, float)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])
    if L[-1] < 1e-9: return [(float(poly[0][0]), float(poly[0][1]), int(post[0]) if post is not None else 0)]
    s = np.arange(0, L[-1] + 1e-9, pas)
    if s[-1] < L[-1] - 1e-6: s = np.append(s, L[-1])
    X = np.interp(s, L, poly[:, 0]); Y = np.interp(s, L, poly[:, 1])
    if post is None:
        return [(float(x), float(y), 0) for x, y in zip(X, Y)]
    P = [int(post[int(np.argmin(np.abs(L - u)))]) for u in s]
    return [(float(x), float(y), p) for x, y, p in zip(X, Y, P)]

lignes, diag, hors = [], [], []
for k, c in enumerate(src):
    defs = np.array(c['defenseurs'], float)
    traj = np.array(c['agent'], float)
    post = np.array(c['postures'], int)
    dep = traj[0]; r_dep = float(np.hypot(*dep))
    # C4 : l'agent part-il bien du cercle du banc ?
    if abs(r_dep - R_DEP) > 2.0: hors.append((k+1, round(r_dep, 1)))

    rayon = max(r_dep, float(np.linalg.norm(traj, axis=1).max())) + 3
    ax, E, R = g.grille(defs, rayon)
    ci = int(np.argmin(np.abs(ax - dep[1]))); cj = int(np.argmin(np.abs(ax - dep[0])))
    _, ch_or = g.dijkstra(E, R, [(ci, cj)], 'max', arrive=R_ARR)
    bord = [(i, j) for i, j in zip(*np.where(np.abs(R - r_dep) <= g.PAS_GRILLE))]
    if (ci, cj) not in bord: bord.append((ci, cj))
    _, ch_lib = g.dijkstra(E, R, bord, 'max', arrive=R_ARR)
    ch_dr = g.droite_sur_grille(E, R, (ci, cj), arrive=R_ARR)
    if ch_or is None or ch_lib is None: raise SystemExit(f"ECHEC : pas de chemin, config {k+1}")

    q = lambda ch: g.cout_chemin(ch, E, 'max')
    diag.append(dict(cfg=k+1, q_dr=q(ch_dr), q_or=q(ch_or), q_lib=q(ch_lib),
                     v2=q(ch_or) > q(ch_dr)+1e-9, v3=q(ch_lib) > q(ch_or)+1e-9,
                     couche=int((post == 2).sum()), npas=len(post)))

    u = dep / max(r_dep, 1e-9)
    droite = np.stack([dep, u*R_ARR])
    bras = [('agent',        ech(traj, post)),
            ('droite',       ech(droite)),
            ('droite_bis',   ech(droite)),
            ('oracle',       ech(g.en_metres(ch_or, ax))),
            ('oracle_libre', ech(g.en_metres(ch_lib, ax)))]
    lignes.append((defs, bras))

v2 = [d['cfg'] for d in diag if d['v2']]; v3 = [d['cfg'] for d in diag if d['v3']]
print(f"  C2 optimalite  : {len(v2)} violation(s) {v2 or ''}")
print(f"  C3 emboitement : {len(v3)} violation(s) {v3 or ''}")
if v2 or v3: raise SystemExit("ECHEC : le plus court chemin est faux.")
print(f"  C4 depart des agents sur le cercle de {R_DEP:.0f} m : "
      f"{'OK' if not hors else 'ECART ' + str(hors)}")

nc = sum(d['couche'] for d in diag); npas = sum(d['npas'] for d in diag)
print(f"\n  POSTURES DE L'AGENT : couche sur {nc}/{npas} pas ({nc/npas:.0%})")
print(f"     ⟨avant le cliquet : 0 sur 420. Si c'est encore 0, le repertoire reste mort⟩")

med = lambda v: float(np.median([d[v] for d in diag]))
print(f"\n  CE QUE LA GEOMETRIE PROMET (pic median)")
print(f"     droite {med('q_dr'):.3f} · oracle {med('q_or'):.3f} · oracle libre {med('q_lib'):.3f}")

def fmt(p): return "[" + ",".join(f"[{x:.1f},{y:.1f},{q}]" for x, y, q in p) + "]"
def fdef(d): return "[" + ",".join(f"[{x:.1f},{y:.1f},{a:.1f}]" for x, y, a in d) + "]"
corps = ",\n".join(
    f"[{fdef(defs)},[" + ",".join(f'["{n}",{fmt(p)}]' for n, p in bras) + "]]"
    for defs, bras in lignes)
open(SORTIE, 'w').write(
    "// genere par generer_banc150b.py — NE PAS EDITER A LA MAIN\n"
    f"// {R_DEP:.0f} m -> {R_ARR:.0f} m · un point tous les {PAS_PT:.0f} m · [x,y,posture]\n"
    "HMT_DATA = [\n" + corps + "\n];\n")

n = sum(len(p) for _, bras in lignes for _, p in bras)
print(f"\n  ecrit : {SORTIE}")
print(f"  {len(lignes)} configurations x 5 bras · {n} points · "
      f"rejeu estime {n*1.2/60:.0f} min")
