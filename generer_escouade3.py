#!/usr/bin/env python3
"""generer_escouade.py — LE BANC D'ESCOUADE. La faille qu'il corrige :

  J'ai extrait une manoeuvre qui n'existe qu'A PLUSIEURS, puis reproche a UN HOMME SEUL
  de ne pas l'executer.

  Tous les succes du projet sont COLLECTIFS : formations 100 %, bounding overwatch 96 %,
  anneau de 6 qui perce, escouade de 9 a l'exfil, commandant appris 48 % contre 13 %.
  Et l'A/B qui a fonde tout le chantier — le flanc paie +12,3 points sur 1324 engagements
  — etait mesure A DEUX AXES : quelqu'un FIXAIT pendant que l'autre manoeuvrait.

  Le contournement n'a de valeur que RELATIVEMENT A UNE BASE DE FEU. Un homme seul qui
  contourne ne fixe personne : il marche simplement plus longtemps sous les yeux adverses.
  C'est exactement ce que mesure l'oracle du banc solo — 105 points, score 0.

QUATRE BRAS, sur les memes configurations defensives, de 150 m a 40 m :

  solo          1 homme par le flanc                  le temoin deja mesure
  bloc_1axe     6 hommes, tout droit                  l'escouade SANS manoeuvre
  deux_axes     3 fixent de face + 3 par le flanc     la manoeuvre complete
  flanc_seul    3 hommes par le flanc, sans appui     LE CONTROLE DECISIF

  Le quatrieme bras est celui qui tranche. Si le flanc reussit AUSSI BIEN sans base de feu,
  alors la fixation n'explique rien et mon analyse est fausse. Il isole l'effet cherche.

CE QUI CHANGE DANS LE DISPOSITIF, ET POURQUOI C'EST INDISPENSABLE

  LES CAPS DES DEFENSEURS NE SONT PLUS VERROUILLES.
  Tous les bancs precedents forcaient setDir toutes les 0,5 s. C'etait juste quand on
  mesurait la perception d'un homme seul ⟨un cap suppose et non mesure avait INVERSE une
  conclusion le 03/08⟩. Mais FIXER, c'est precisement attirer les regards. Verrouiller les
  caps ETEINT le mecanisme qu'on veut mesurer.
  Donc : caps LIBRES, et releves a 1 Hz. On mesure ce qui se passe au lieu de l'imposer.
  ⟨le controle nul est deja acquis : sans approchant, eyeDirection ne bouge pas d'un degre
   — 2063 releves du banc solo, ecart median 0°, maximum 0°⟩

CE QUI FERAIT ECHOUER LA MESURE — ecrit avant :
  P1 PRESENCE  : bloc_1axe doit etre repere. Sinon la position ne voit rien.
  P2 NUL       : deux_axes rejoue doit donner le meme verdict.
  P3 FIXATION  : le flanc de deux_axes doit survivre a PLUS de jalons que flanc_seul.
                 C'est LE test. Egalite = la base de feu ne fixe rien, et mon analyse tombe.
  P4 COLLECTIF : deux_axes doit battre solo ET bloc_1axe.
  P5 REGARDS   : si les caps ne bougent JAMAIS malgre une base de feu visible, alors le
                 mecanisme de fixation n'existe pas SANS TIR, et P3 ne peut pas etre positif.
                 Ce n'est alors pas une refutation de la these : c'est qu'il faut des armes.
"""
import json, math
import numpy as np
import geom_ombre as g

TRAJ   = '/mnt/data/corpus/trajectoires_agent150.json'
SORTIE = '/home/younes/arma3-marl/bancs/arma/donnees_escouade3.sqf'
R_DEP, R_ARR, PAS_PT = 150.0, 40.0, 4.0
ECART = 8.0          # espacement lateral entre hommes d'un meme groupe, en metres

src = json.load(open(TRAJ))[:20]
print(f"  {len(src)} configurations · {R_DEP:.0f} m -> {R_ARR:.0f} m · ecart {ECART:.0f} m")

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

def decale(pts, k, n):
    """place le k-ieme homme d'un groupe de n, perpendiculairement a la marche.
    Le groupe avance en ligne, comme une escouade — pas empile sur un point."""
    pts = np.asarray(pts, float)
    out = []
    off = (k - (n-1)/2) * ECART
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
    # LE FLANC : le meilleur chemin en choisissant son abordage — c'est lui qui a battu la
    # droite dans le banc solo (21/28 contre 13/26). On lui donne maintenant un appui.
    bord = [(i, j) for i, j in zip(*np.where(np.abs(R - r_dep) <= g.PAS_GRILLE))]
    if (ci, cj) not in bord: bord.append((ci, cj))
    _, ch_flanc = g.dijkstra(E, R, bord, 'max', arrive=R_ARR)
    if ch_flanc is None: raise SystemExit(f"ECHEC : pas de chemin de flanc, config {k+1}")
    flanc = ech(g.en_metres(ch_flanc, ax))
    # L'AXE FIXANT : la ligne droite depuis le depart impose. Elle se fait voir — c'est
    # son role. ⟨banc solo : la droite est vue, score median 2 sur 4⟩
    droit = ech(np.stack([dep, u*R_ARR]))

    q = lambda ch: g.cout_chemin(ch, E, 'max')
    ch_dr = g.droite_sur_grille(E, R, (ci, cj), arrive=R_ARR)
    diag.append(dict(cfg=k+1, q_dr=q(ch_dr), q_fl=q(ch_flanc),
                     viol=q(ch_flanc) > q(ch_dr)+1e-9))

    # un bras = une liste de groupes ; un groupe = [role, [trajets d'hommes]]
    # role "M" = manoeuvrant (c'est LUI qu'on note) · "F" = fixant (il se fait voir)
    bras = [
        ('solo',       [('M', [flanc])]),
        ('bloc_1axe',  [('M', [decale(droit, i, 6) for i in range(6)])]),
        ('deux_axes',  [('F', [decale(droit, i, 3) for i in range(3)]),
                        ('M', [decale(flanc, i, 3) for i in range(3)])]),
        ('flanc_seul', [('M', [decale(flanc, i, 3) for i in range(3)])]),
        # CONTROLE NEGATIF : deux bras identiques SANS base de feu. Si l'ecart apparait
        # aussi entre eux, l'effet mesure est un artefact d'ordre et non de la fixation.
        ('flanc_seul_bis', [('M', [decale(flanc, i, 3) for i in range(3)])]),
        ('deux_axes_bis', [('F', [decale(droit, i, 3) for i in range(3)]),
                           ('M', [decale(flanc, i, 3) for i in range(3)])]),
    ]
    lignes.append((defs, bras))

viol = [d['cfg'] for d in diag if d['viol']]
print(f"  C2 optimalite du flanc : {len(viol)} violation(s) {viol or ''}")
if viol: raise SystemExit("ECHEC : le chemin de flanc est faux.")
med = lambda v: float(np.median([d[v] for d in diag]))
print(f"  pic median : droite {med('q_dr'):.3f} · flanc {med('q_fl'):.3f}")

def fp(p): return "[" + ",".join(f"[{x:.1f},{y:.1f}]" for x, y in p) + "]"
def fg(gr): return "[" + ",".join(f'["{r}",[' + ",".join(fp(h) for h in hs) + "]]" for r, hs in gr) + "]"
def fd(d): return "[" + ",".join(f"[{x:.1f},{y:.1f},{a:.1f}]" for x, y, a in d) + "]"
corps = ",\n".join(
    f"[{fd(defs)},[" + ",".join(f'["{n}",{fg(gr)}]' for n, gr in bras) + "]]"
    for defs, bras in lignes)
open(SORTIE, 'w').write(
    "// genere par generer_escouade.py — NE PAS EDITER A LA MAIN\n"
    f"// {R_DEP:.0f} m -> {R_ARR:.0f} m · ecart {ECART:.0f} m · roles M=manoeuvrant F=fixant\n"
    "HMT_DATA = [\n" + corps + "\n];\n")

n_h = sum(len(hs) for _, bras in lignes for _, gr in bras for _, hs in gr)
n_p = sum(len(h) for _, bras in lignes for _, gr in bras for _, hs in gr for h in hs)
print(f"\n  ecrit : {SORTIE}")
print(f"  {len(lignes)} configurations x {len(lignes[0][1])} bras · {n_h} hommes · {n_p} points")
print(f"  rejeu estime : {n_p*1.2/60/max(n_h/ (n_p/  max(n_p,1)),1):.0f} min "
      f"(les hommes d'un groupe avancent ENSEMBLE, pas l'un apres l'autre)")
pas_max = max(len(h) for _, bras in lignes for _, gr in bras for _, hs in gr for h in hs)
n_bras = sum(len(bras) for _, bras in lignes)
print(f"  duree reelle ~ {n_bras*pas_max*1.2/60:.0f} min : un bras = un rejeu simultane")
