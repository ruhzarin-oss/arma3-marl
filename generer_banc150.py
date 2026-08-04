#!/usr/bin/env python3
"""generer_banc150.py — REFAIRE LE BANC A 150 M.

POURQUOI. Le banc precedent faisait partir l'approchant a 80 m d'une position defendue,
alors que la detection frontale est mesuree a 105 m dans Arma : il partait DEJA VU.
Mesure du 04/08 : 24 des 34 trajectoires reperees l'etaient dans les 12 premiers metres,
ecart interquartile 8 m sur 40 m utiles — 20 % de dynamique. L'instrument etait ecrase
contre son plafond, et refusait tout le monde sans rien mesurer.

CE QUE CE BANC TESTE. Pas l'agent — il n'a jamais ete entraine au-dela de 80 m. Il teste
L'INSTRUMENT : a 150 m, la distance de reperage sait-elle enfin separer des trajectoires ?

TROIS BRAS, sur les memes configurations defensives :
  droite        la ligne droite, meme depart      -> le temoin
  oracle        le meilleur chemin DEPUIS CE DEPART (plus court chemin de goulot sur le
                damier d'ombre) -> ce que la manoeuvre peut acheter
  oracle_libre  le meilleur chemin en CHOISISSANT son point de depart sur le cercle
                -> la table du 04/08 dit que 88 % du gain est la. Arma doit trancher.
  droite_bis    la ligne droite, rejouee -> CONTROLE NUL

Tous les bras vont de 150 m a 40 m du centre. ⟨on ne demande plus d'atteindre le centre :
mesure du 03/08, a dix metres du milieu d'un groupe on est dans le cone de tout le monde,
quel que soit le chemin. Le banc demandait l'impossible.⟩

CE QUI FERAIT ECHOUER CETTE MESURE — ecrit avant, et verifie apres le run :
  P1 PRESENCE  : la ligne droite depuis 150 m DOIT etre reperee. Sinon la position ne voit
                 rien et rien ne se compare.
  P2 DYNAMIQUE : l'ecart interquartile des distances de reperage doit couvrir au moins 25 %
                 des 110 m utiles, soit >= 27 m. C'est LE controle qui manquait : sans lui
                 on refuse des agents avec un instrument sature.
  P3 NUL       : droite et droite_bis doivent donner des distances voisines (< 15 m d'ecart
                 median). Si la variance entre repetitions depasse l'ecart entre bras, on ne
                 conclut rien.
  P4 REGION DE REUSSITE : oracle_libre doit etre repere au moins 25 % plus loin que la
                 droite. S'il n'y arrive pas, AUCUN agent ne peut passer ce banc et c'est la
                 TACHE qu'il faut changer, pas l'agent.
"""
import json, math
import numpy as np
import geom_ombre as g

TRAJ   = '/mnt/data/corpus/trajectoires_agent_SAUVE.json'
SORTIE = '/home/younes/arma3-marl/bancs/arma/donnees_banc150.sqf'
R_DEP  = 150.0      # le rayon de depart : AU-DELA des 105 m de detection frontale mesuree
R_ARR  = 40.0
PAS_PT = 4.0        # un point tous les 4 m, comme le banc du cone qui a certifie 18/18

src = json.load(open(TRAJ))[:20]
print(f"  {len(src)} configurations · depart a {R_DEP:.0f} m · arrivee a {R_ARR:.0f} m")

# ---------------------------------------------------------------- C1, a chaque execution
e1 = g.controle_coherence(np.array(src[0]['defenseurs'], float))
print(f"  C1 coherence expo : {e1:.1e}", end='  ')
if e1 > 1e-9: raise SystemExit("ECHEC C1")
print("OK")

def echantillonne(poly, pas=PAS_PT):
    poly = np.asarray(poly, float)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])
    if L[-1] < 1e-9: return poly[:1]
    s = np.arange(0, L[-1] + 1e-9, pas)
    if s[-1] < L[-1] - 1e-6: s = np.append(s, L[-1])
    return np.stack([np.interp(s, L, poly[:, 0]), np.interp(s, L, poly[:, 1])], -1)

lignes, diag = [], []
degenere = []
for k, c in enumerate(src):
    defs = np.array(c['defenseurs'], float)
    # CONTROLE DU DECOR : des defenseurs empiles au meme point ne tiendront pas dans Arma,
    # ils se repoussent. On le signale au lieu de le decouvrir dans les resultats.
    if len(defs) > 1:
        dmin = min(np.hypot(*(defs[i, :2]-defs[j, :2]))
                   for i in range(len(defs)) for j in range(i+1, len(defs)))
        if dmin < 1.0: degenere.append((k+1, len(defs), round(float(dmin), 2)))

    # l'azimut de depart : celui que l'agent avait, reporte a 150 m — memes conditions
    dep0 = np.array(c['agent'], float)[0]
    u = dep0 / max(np.linalg.norm(dep0), 1e-9)
    dep = u * R_DEP

    rayon = R_DEP + 3
    ax, E, R = g.grille(defs, rayon)
    ci = int(np.argmin(np.abs(ax - dep[1]))); cj = int(np.argmin(np.abs(ax - dep[0])))

    _, ch_or = g.dijkstra(E, R, [(ci, cj)], 'max', arrive=R_ARR)
    bord = [(i, j) for i, j in zip(*np.where(np.abs(R - R_DEP) <= g.PAS_GRILLE))]
    if (ci, cj) not in bord: bord.append((ci, cj))
    _, ch_lib = g.dijkstra(E, R, bord, 'max', arrive=R_ARR)
    ch_dr = g.droite_sur_grille(E, R, (ci, cj), arrive=R_ARR)
    if ch_or is None or ch_lib is None:
        raise SystemExit(f"ECHEC : aucun chemin trouve sur la configuration {k+1}")

    # CONTROLES sur la grille, ou l'optimalite est stricte
    q_or, q_lib, q_dr = (g.cout_chemin(x, E, 'max') for x in (ch_or, ch_lib, ch_dr))
    diag.append(dict(cfg=k+1, q_dr=q_dr, q_or=q_or, q_lib=q_lib,
                     viol_opt=q_or > q_dr + 1e-9, viol_emb=q_lib > q_or + 1e-9))

    droite = np.stack([dep, u*R_ARR])
    bras = [('droite',       echantillonne(droite)),
            ('oracle',       echantillonne(g.en_metres(ch_or, ax))),
            ('oracle_libre', echantillonne(g.en_metres(ch_lib, ax))),
            ('droite_bis',   echantillonne(droite))]
    lignes.append((defs, bras))

viol_opt = [d['cfg'] for d in diag if d['viol_opt']]
viol_emb = [d['cfg'] for d in diag if d['viol_emb']]
print(f"  C2 optimalite  (oracle <= droite sur grille) : {len(viol_opt)} violation(s) {viol_opt or ''}")
print(f"  C3 emboitement (libre <= contraint)          : {len(viol_emb)} violation(s) {viol_emb or ''}")
if viol_opt or viol_emb: raise SystemExit("ECHEC : le plus court chemin est faux.")

if degenere:
    print(f"\n  ATTENTION — defenseurs empiles (ils se repousseront dans Arma) :")
    for cfg, n, d in degenere: print(f"     config {cfg} : {n} defenseurs, ecart minimal {d} m")

# ---------------------------------------------------------------- ce que la geometrie promet
med = lambda v: float(np.median([d[v] for d in diag]))
print(f"\n  CE QUE LA GEOMETRIE PROMET (pic d'exposition, mediane sur {len(diag)} configs)")
print(f"     ligne droite ................................. {med('q_dr'):.3f}")
print(f"     meilleur chemin depuis le depart impose ...... {med('q_or'):.3f}")
print(f"     meilleur chemin en choisissant son depart .... {med('q_lib'):.3f}")
gain_tot = med('q_dr') - med('q_lib')
if gain_tot > 1e-6:
    print(f"     part du gain tenant au CHOIX DU DEPART : "
          f"{(med('q_or')-med('q_lib'))/gain_tot:.0%}")
if med('q_dr') - med('q_or') < 0.02:
    print(f"     ⟨reserve : depuis le depart impose, meme le chemin parfait n'achete presque")
    print(f"      rien. Si Arma le confirme, c'est la TACHE qu'il faut changer.⟩")

# ---------------------------------------------------------------- l'export SQF
def fmt_pts(p): return "[" + ",".join(f"[{x:.1f},{y:.1f}]" for x, y in p) + "]"
def fmt_def(d): return "[" + ",".join(f"[{x:.1f},{y:.1f},{a:.1f}]" for x, y, a in d) + "]"

# PAS DE VIRGULE FINALE. ⟨le 03/08, une virgule en fin de liste rendait le fichier de
# donnees invalide, HMT_DATA restait indefini, et le banc partait quand meme.⟩
corps = ",\n".join(
    f"[{fmt_def(defs)},[" + ",".join(f'["{nom}",{fmt_pts(p)}]' for nom, p in bras) + "]]"
    for defs, bras in lignes)
with open(SORTIE, 'w') as f:
    f.write("// genere par generer_banc150.py — NE PAS EDITER A LA MAIN\n")
    f.write(f"// depart {R_DEP:.0f} m · arrivee {R_ARR:.0f} m · un point tous les {PAS_PT:.0f} m\n")
    f.write("HMT_DATA = [\n" + corps + "\n];\n")

npts = sum(len(p) for _, bras in lignes for _, p in bras)
print(f"\n  ecrit : {SORTIE}")
print(f"  {len(lignes)} configurations x 4 bras · {npts} points au total")
print(f"  duree estimee du run : {npts*1.2/60:.0f} min de rejeu + mise en place")
