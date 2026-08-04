#!/usr/bin/env python3
"""generer_escouade4.py — LE BANC QUI DIAGNOSTIQUE SON PROPRE INSTRUMENT.

  Le banc n°3 est mort de sa mesure, pas de son hypothese. La « part d'hommes du groupe
  manoeuvrant reperes » ne prend presque jamais de valeur intermediaire : 3 essais sur 100
  sur trois bancs cumules. La detection est en CASCADE — des qu'un homme est repere, ses
  voisins le sont dans la seconde.

  Consequence mesuree le 04/08 : l'observation fondatrice « 31/60 contre 51/60 » n'etait pas
  une nouvelle mesure. C'est 11 groupes reperes contre 17, multiplie par 3 hommes. La part
  d'hommes vus ETAIT la metrique de groupe, rescalee.

DEUX CHANGEMENTS, ET UN SEUL COMPTE VRAIMENT

  1. ON MESURE UNE DISTANCE, PAS UN COMPTE. A quelle distance le groupe est-il repere.
     Une distance est continue : elle ne peut pas produire d'egalites. C'est le seul defaut
     de l'instrument precedent qu'on est SUR de corriger.

  2. UN CONTROLE POSITIF POUR LA CASCADE — c'est lui qui compte.
     Bras `flanc_etale` : meme chemin, meme effectif, ecartement porte de 8 m a 40 m.
     Si la detection s'etale quand les hommes s'ecartent, la cascade est une affaire de
     GEOMETRIE et une mesure par homme redevient legitime — a condition de separer les
     hommes. Si elle ne s'etale pas, la connaissance est de camp et instantanee, et toute
     mesure « combien d'hommes » est morte DEFINITIVEMENT, a n'importe quel ecartement.
     Ce banc a donc le droit de refuter la branche entiere. C'est le but.

  3. DEFENSEURS RESTREINTS A 5-8. Sur le banc n°3 les configs a 4 defenseurs ne reperaient
     jamais personne et celle a 12 reperait toujours tout le monde : plancher et plafond,
     elles ne peuvent pas departager. Le corpus contient 40 configs dans la bande ; on en
     prend 20.

CE QUI FERAIT ECHOUER LA MESURE — cf CRITERES_BANC_ESCOUADE4.md, deposé avant ce run :
  D0 CONTROLE POSITIF : `flanc_etale` doit donner un ecart de cascade median >= 15 m.
                        S'il echoue, la branche « combien d'hommes » est close pour de bon.
  D2 BRUIT            : bruit sur d_grp entre rejeux identiques <= 25 m, sinon D3 non lu.
  D3 HYPOTHESE        : lue SEULEMENT si D0 et D2 passent.
  D5 PRESENCE         : bloc_1axe repere dans >= 18 configs sur 20.
"""
import json, math
import numpy as np
import geom_ombre as g

TRAJ   = '/mnt/data/corpus/trajectoires_agent150.json'
SORTIE = '/home/younes/arma3-marl/bancs/arma/donnees_escouade4.sqf'
R_DEP, R_ARR, PAS_PT = 150.0, 40.0, 4.0
ECART = 8.0          # espacement lateral normal, en metres
ECART_ETALE = 40.0   # LE CONTROLE POSITIF : le meme groupe, cinq fois plus etale
DEF_MIN, DEF_MAX, N_CFG = 5, 8, 20

# LA BANDE QUI DEPARTAGE. Hors d'elle, le banc n°3 a mesure du plancher et du plafond.
tout = json.load(open(TRAJ))
src  = [c for c in tout if DEF_MIN <= len(c['defenseurs']) <= DEF_MAX][:N_CFG]
if len(src) < N_CFG:
    raise SystemExit(f"ECHEC : {len(src)} configs dans la bande {DEF_MIN}-{DEF_MAX}, il en faut {N_CFG}")
print(f"  {len(src)} configurations · {R_DEP:.0f} m -> {R_ARR:.0f} m")
print(f"  defenseurs retenus : {sorted(set(len(c['defenseurs']) for c in src))} "
      f"(bande {DEF_MIN}-{DEF_MAX}, {len(tout)} configs dans le corpus)")
print(f"  ecart normal {ECART:.0f} m · ecart du controle positif {ECART_ETALE:.0f} m")

e1 = g.controle_coherence(np.array(src[0]['defenseurs'], float))
print(f"  C1 coherence expo : {e1:.1e}", end='  ')
if e1 > 1e-9: raise SystemExit("ECHEC C1")
print("OK")

def ech(poly, pas=PAS_PT):
    poly = np.asarray(poly, float)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])
    if L[-1] < 1e-9: return [(float(poly[0][0]), float(poly[0][1]))]
    s = np.arange(0, L[-1] + 1e-9, pas)
    if s[-1] < L[-1] - 1e-6: s = np.append(s, L[-1])
    return list(zip(np.interp(s, L, poly[:, 0]), np.interp(s, L, poly[:, 1])))

def decale(pts, k, n, ecart=ECART):
    """place le k-ieme homme d'un groupe de n, perpendiculairement a la marche.
    Le groupe avance en ligne, comme une escouade — pas empile sur un point.
    ⟨`ecart` est devenu un parametre : c'est LA variable du controle positif D0⟩"""
    pts = np.asarray(pts, float)
    out = []
    off = (k - (n-1)/2) * ecart
    for i, p in enumerate(pts):
        j = min(i+1, len(pts)-1)
        d = pts[j] - pts[max(i-1, 0)]
        nr = np.linalg.norm(d)
        perp = np.array([-d[1], d[0]])/nr if nr > 1e-9 else np.array([1.0, 0.0])
        out.append(tuple(p + perp*off))
    return out

lignes, diag = [], []
for k, c in enumerate(src):
    defs = np.array(c['defenseurs'], float)
    dep = np.array(c['agent'], float)[0]
    r_dep = float(np.hypot(*dep))
    u = dep / max(r_dep, 1e-9)

    rayon = r_dep + 3
    ax, E, R = g.grille(defs, rayon)
    ci = int(np.argmin(np.abs(ax - dep[1]))); cj = int(np.argmin(np.abs(ax - dep[0])))
    bord = [(i, j) for i, j in zip(*np.where(np.abs(R - r_dep) <= g.PAS_GRILLE))]
    if (ci, cj) not in bord: bord.append((ci, cj))
    _, ch_flanc = g.dijkstra(E, R, bord, 'max', arrive=R_ARR)
    if ch_flanc is None: raise SystemExit(f"ECHEC : pas de chemin de flanc, config {k+1}")
    flanc = ech(g.en_metres(ch_flanc, ax))
    droit = ech(np.stack([dep, u*R_ARR]))

    q = lambda ch: g.cout_chemin(ch, E, 'max')
    ch_dr = g.droite_sur_grille(E, R, (ci, cj), arrive=R_ARR)
    diag.append(dict(cfg=k+1, q_dr=q(ch_dr), q_fl=q(ch_flanc),
                     viol=q(ch_flanc) > q(ch_dr)+1e-9, nd=len(c['defenseurs'])))

    # SIX BRAS. `solo` est retire : un homme seul ne peut pas cascader, il n'apprend
    # rien sur la cascade, et il coutait 45 s par configuration.
    bras = [
        ('bloc_1axe',      [('M', [decale(droit, i, 6) for i in range(6)])]),
        ('deux_axes',      [('F', [decale(droit, i, 3) for i in range(3)]),
                            ('M', [decale(flanc, i, 3) for i in range(3)])]),
        ('deux_axes_bis',  [('F', [decale(droit, i, 3) for i in range(3)]),
                            ('M', [decale(flanc, i, 3) for i in range(3)])]),
        ('flanc_seul',     [('M', [decale(flanc, i, 3) for i in range(3)])]),
        ('flanc_seul_bis', [('M', [decale(flanc, i, 3) for i in range(3)])]),
        # LE CONTROLE POSITIF D0 : meme chemin, meme effectif, SEUL l'ecartement change.
        ('flanc_etale',    [('M', [decale(flanc, i, 3, ECART_ETALE) for i in range(3)])]),
    ]
    lignes.append((defs, bras))

viol = [d['cfg'] for d in diag if d['viol']]
print(f"  C2 optimalite du flanc : {len(viol)} violation(s) {viol or ''}")
if viol: raise SystemExit("ECHEC : le chemin de flanc est faux.")
med = lambda v: float(np.median([d[v] for d in diag]))
print(f"  pic median : droite {med('q_dr'):.3f} · flanc {med('q_fl'):.3f}")

# C3 — LE CONTROLE POSITIF DOIT ETRE REELLEMENT ETALE. Une verification de geometrie,
# avant tout run : si les trajets `flanc_etale` ne sont pas plus ecartes que `flanc_seul`,
# D0 ne teste rien et le banc ne doit pas partir.
ecarts = []
for defs, bras in lignes:
    d = dict(bras)
    for nom in ('flanc_seul', 'flanc_etale'):
        hs = d[nom][0][1]
        p = [np.asarray(h[len(h)//2], float) for h in hs]
        ecarts.append((nom, float(np.linalg.norm(p[0] - p[-1]))))
e_norm  = np.median([v for n, v in ecarts if n == 'flanc_seul'])
e_etale = np.median([v for n, v in ecarts if n == 'flanc_etale'])
print(f"  C3 largeur du front (median, a mi-parcours) : "
      f"flanc_seul {e_norm:.1f} m · flanc_etale {e_etale:.1f} m")
if e_etale < 3 * e_norm:
    raise SystemExit("ECHEC C3 : le controle positif n'est pas assez etale, D0 ne testerait rien.")

def fp(p): return "[" + ",".join(f"[{x:.1f},{y:.1f}]" for x, y in p) + "]"
def fg(gr): return "[" + ",".join(f'["{r}",[' + ",".join(fp(h) for h in hs) + "]]" for r, hs in gr) + "]"
def fd(d): return "[" + ",".join(f"[{x:.1f},{y:.1f},{a:.1f}]" for x, y, a in d) + "]"
corps = ",\n".join(
    f"[{fd(defs)},[" + ",".join(f'["{n}",{fg(gr)}]' for n, gr in bras) + "]]"
    for defs, bras in lignes)
open(SORTIE, 'w').write(
    "// genere par generer_escouade4.py — NE PAS EDITER A LA MAIN\n"
    f"// {R_DEP:.0f} m -> {R_ARR:.0f} m · ecart {ECART:.0f} m · etale {ECART_ETALE:.0f} m\n"
    f"// defenseurs {DEF_MIN}-{DEF_MAX} · roles M=manoeuvrant F=fixant\n"
    "HMT_DATA = [\n" + corps + "\n];\n")

n_h = sum(len(hs) for _, bras in lignes for _, gr in bras for _, hs in gr)
n_p = sum(len(h) for _, bras in lignes for _, gr in bras for _, hs in gr for h in hs)
pas_max = max(len(h) for _, bras in lignes for _, gr in bras for _, hs in gr for h in hs)
n_bras = sum(len(bras) for _, bras in lignes)
print(f"\n  ecrit : {SORTIE}")
print(f"  {len(lignes)} configurations x {len(lignes[0][1])} bras · {n_h} hommes · {n_p} points")
print(f"  duree reelle ~ {n_bras*pas_max*1.2/60:.0f} min : un bras = un rejeu simultane")
