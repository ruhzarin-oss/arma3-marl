#!/usr/bin/env python3
"""table_arbitrage.py — SOMME OU MAXIMUM : LEQUEL DES DEUX EXPLIQUE LE REFUS ?

⟨Fable, 04/08 : « Produis la table : 20 lignes x {somme-oracle, somme-agent, max-oracle,
 max-agent} + distance Arma. Ca regle d'un coup le controle positif manquant ET l'arbitrage.
 Coût : une soiree, zero GPU, zero Arma. »⟩

LA QUESTION. L'agent ne transfere pas. Deux causes possibles, et on refuse d'en debattre :
  A. LE CLIQUET — la sandbox SOMME l'exposition, Arma prend un MAXIMUM irreversible.
     L'objectif etait mal specifie : l'agent optimisait une grandeur qui n'existe pas.
  B. LE MUR — meme sous la regle MAX, la sandbox classe mal les trajectoires, et il manque
     une piece au simulateur.

CE QUI SEPARE LES DEUX — predictions deposees AVANT le calcul :
  · Si A : sous SOMME, l'oracle (long, serpentant) score PIRE ou egal a l'agent sur une part
    notable des configurations — la somme punit la longueur, donc la sandbox preferait le
    rachat. Et sous MAX, l'oracle ECRASE l'agent sur ~19/20.
  · Si B : sous MAX aussi, la sandbox donne a l'agent un score proche de l'oracle, alors
    qu'Arma les separe. Confirmation : correlation de rang entre le score sandbox-max et la
    distance de reperage mesuree dans Arma. > 0,7 = simulateur fidele, le probleme est
    l'apprentissage. Basse = il manque vraiment une piece.

CE QUI FERAIT ECHOUER CETTE MESURE — ecrit avant, comme toujours :
  C1 COHERENCE  : mon expo() doit reproduire celle de la sandbox. Verifiee contre une
                  seconde implementation ecrite differemment (boucle explicite). Les erreurs
                  d'axes et de diffusion sont LA classe de faute ici. Ecart tolere : 1e-9.
  C2 OPTIMALITE : par construction, l'oracle-max ne peut pas etre battu sous la regle max,
                  ni l'oracle-somme sous la regle somme. Si une seule configuration le viole,
                  le plus court chemin est faux et toute la table est nulle.
  C3 EMBOITEMENT: l'oracle LIBRE (qui choisit son point de depart) ne peut pas etre pire que
                  l'oracle CONTRAINT (meme depart que l'agent). Inegalite logique.
  C4 CONTROLE NUL : sur une configuration ou tous les defenseurs regardent a l'oppose, il n'y
                  a rien a eviter — oracle et ligne droite doivent se rejoindre.
  C5 CONTROLE DE PRESENCE : la ligne droite doit etre nettement plus exposee que l'oracle.
                  Si l'oracle n'achete rien, la geometrie ne se laisse pas manoeuvrer et
                  aucun agent ne pouvait reussir.
"""
import json, math, re, heapq
import numpy as np

TRAJ = '/mnt/data/corpus/trajectoires_agent_SAUVE.json'
LOG  = '/mnt/data/harmattan-sandbox/logs/serverBA.out'
SRC  = '/home/younes/arma3-marl/agent_complet.py'

# ---------------------------------------------------------------- les constantes du monde
# On les LIT dans le simulateur au lieu de les recopier : une constante recopiee est une
# constante qui divergera. ⟨le 03/08, la vitesse couchee valait 0,33 ici et 0,23 la-bas⟩
def const(nom, defaut=None):
    for l in open(SRC, encoding='utf-8'):
        l = l.split('#')[0]                       # jamais depuis un commentaire
        m = re.search(rf'\b{nom}\s*=\s*([\d.]+)', l)
        if m: return float(m.group(1))
    if defaut is None: raise SystemExit(f"ECHEC : constante {nom} introuvable dans {SRC}")
    return defaut

CHAMP         = const('CHAMP')
SEUIL_COUCHE  = const('SEUIL_COUCHE')
PENTE_COUCHE  = const('PENTE_COUCHE')
ARRIVE        = const('ARRIVE')
print(f"  constantes lues dans le simulateur : champ {CHAMP:.0f} deg · "
      f"seuil couche {SEUIL_COUCHE:.0f} m · pente {PENTE_COUCHE:.0f} · arrivee {ARRIVE:.0f} m")

PAS_GRILLE = 1.0     # maille du damier, en metres
PAS_CHEMIN = 1.0     # rrechantillonnage des trajectoires : chaque chemin est traite pareil

def sig(x): return 1.0/(1.0+np.exp(-x))

# ---------------------------------------------------------------- l'exposition, en numpy
# Transcription exacte de expo() dans agent_complet.py, agregation par le MAXIMUM.
def expo(pts, defs, posture=None):
    """pts (N,2) · defs (D,3) = x, y, cap · posture (N,) dans {0,1,2} ou None = debout.
    Rend (N,) : l'exposition instantanee, maximum sur les defenseurs."""
    p = np.asarray(pts, float).reshape(-1, 2)
    xy, az = defs[:, :2], defs[:, 2]
    v  = p[:, None, :] - xy[None, :, :]                      # (N,D,2)
    d  = np.maximum(np.linalg.norm(v, axis=-1), 1.0)
    gis = np.degrees(np.arctan2(v[..., 0], v[..., 1])) % 360
    ec  = np.abs((gis - az[None, :] + 180) % 360 - 180)
    dans = sig((CHAMP - ec) * 1.2)                           # plateau plat puis chute franche
    base = 0.45 * (1.0 - np.clip(d/400, 0, 1))               # part vue quelle que soit l'orientation
    e = (base + (1.0-base)*dans) * (1.0 - np.clip(d/450, 0, 1))
    if posture is not None:
        couche = 1.0 - sig((d - SEUIL_COUCHE) / PENTE_COUCHE)
        f = np.where(np.asarray(posture, int)[:, None] == 2, couche, 1.0)
        e = e * f
    return e.max(axis=1)

def expo_naive(pts, defs, posture=None):
    """La MEME chose, ecrite autrement : boucle explicite, aucun broadcast. Sert de temoin."""
    out = []
    for k, (px, py) in enumerate(np.asarray(pts, float).reshape(-1, 2)):
        best = 0.0
        for dx, dy, a in defs:
            vx, vy = px-dx, py-dy
            d = max(math.hypot(vx, vy), 1.0)
            gis = math.degrees(math.atan2(vx, vy)) % 360
            ec = abs((gis - a + 180) % 360 - 180)
            dans = 1/(1+math.exp(-(CHAMP-ec)*1.2))
            base = 0.45*(1 - min(max(d/400, 0), 1))
            e = (base + (1-base)*dans) * (1 - min(max(d/450, 0), 1))
            if posture is not None and int(posture[k]) == 2:
                e *= 1 - 1/(1+math.exp(-(d-SEUIL_COUCHE)/PENTE_COUCHE))
            best = max(best, e)
        out.append(best)
    return np.array(out)

# ---------------------------------------------------------------- les chemins
def reechantillonne(poly, pas=PAS_CHEMIN):
    """Une polyligne -> des points espaces de `pas` metres. Sans ca, la SOMME dependrait du
    nombre de sommets et non du trajet : l'oracle (des centaines de points de grille) et
    l'agent (21 points) ne seraient pas comparables."""
    poly = np.asarray(poly, float)
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    L = np.concatenate([[0], np.cumsum(seg)])
    if L[-1] < 1e-9: return poly[:1]
    s = np.arange(0, L[-1] + 1e-9, pas)
    return np.stack([np.interp(s, L, poly[:, 0]), np.interp(s, L, poly[:, 1])], -1)

def score(poly, defs, posture_poly=None):
    """Les DEUX regles sur le meme chemin : la somme (aire sous la courbe d'exposition,
    en metres) et le pic (ce qu'Arma retient, irreversiblement)."""
    p = reechantillonne(poly)
    post = None
    if posture_poly is not None:
        # on porte la posture le long du rrechantillonnage, au plus proche sommet
        src = np.asarray(poly, float)
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(src, axis=0), axis=1))])
        s = np.linspace(0, L[-1], len(p)) if L[-1] > 0 else np.zeros(len(p))
        post = np.array([posture_poly[int(np.argmin(np.abs(L - u)))] for u in s])
    e = expo(p, defs, post)
    return float(e.sum() * PAS_CHEMIN), float(e.max())

# ---------------------------------------------------------------- le plus court chemin
def grille(defs, rayon):
    n = int(2*rayon/PAS_GRILLE) + 1
    ax = np.linspace(-rayon, rayon, n)
    X, Y = np.meshgrid(ax, ax)
    pts = np.stack([X.ravel(), Y.ravel()], -1)
    E = expo(pts, defs).reshape(n, n)          # oracle DEBOUT : il ne triche pas avec la posture
    R = np.hypot(X, Y)
    return ax, E, R

VOIS = [(-1,0,1.),(1,0,1.),(0,-1,1.),(0,1,1.),
        (-1,-1,2**.5),(-1,1,2**.5),(1,-1,2**.5),(1,1,2**.5)]

def dijkstra(E, R, departs, regle):
    """`regle` = 'somme' : cout cumule = integrale de l'exposition le long du chemin.
       `regle` = 'max'   : cout cumule = pic rencontre (plus court chemin de goulot).
    Rend (cout, chemin) vers la meilleure cellule du rayon d'arrivee."""
    n = E.shape[0]
    INF = float('inf')
    cout = np.full((n, n), INF)
    prev = np.full((n, n, 2), -1, int)
    tas = []
    for i, j in departs:
        c = E[i, j] * PAS_GRILLE if regle == 'somme' else E[i, j]
        if c < cout[i, j]:
            cout[i, j] = c; heapq.heappush(tas, (c, i, j))
    dedans = R <= (E.shape[0]-1)/2*PAS_GRILLE + 1e-9
    fin = None
    while tas:
        c, i, j = heapq.heappop(tas)
        if c > cout[i, j] + 1e-12: continue
        if R[i, j] <= ARRIVE: fin = (i, j); break
        for di, dj, w in VOIS:
            a, b = i+di, j+dj
            if not (0 <= a < n and 0 <= b < n and dedans[a, b]): continue
            nc = c + E[a, b]*w*PAS_GRILLE if regle == 'somme' else max(c, E[a, b])
            if nc < cout[a, b] - 1e-12:
                cout[a, b] = nc; prev[a, b] = (i, j); heapq.heappush(tas, (nc, a, b))
    if fin is None: return INF, None
    chemin = []
    i, j = fin
    while i >= 0:
        chemin.append((i, j)); i, j = prev[i, j]
    return cout[fin], chemin[::-1]

def en_metres(chemin, ax):
    return np.array([[ax[j], ax[i]] for i, j in chemin])   # X = colonne, Y = ligne

def droite_sur_grille(E, R, depart):
    """La ligne droite depart -> centre, mais PARCOURUE SUR LA GRILLE.
    ⟨sans elle, C2 comparait l'oracle (contraint a la grille) a une droite calculee en
     continu : deux espaces differents, donc une optimalite invraisemblable a tenir. Le
     premier jet a compte 14 violations sur 20 pour cette seule raison.⟩"""
    n = E.shape[0]
    i, j = depart
    ch = [(i, j)]
    while R[i, j] > ARRIVE:
        ci, cj = (n-1)/2, (n-1)/2
        vi, vj = ci - i, cj - j
        norme = max(math.hypot(vi, vj), 1e-9)
        di = int(round(vi/norme)); dj = int(round(vj/norme))
        if di == 0 and dj == 0: break
        i, j = i+di, j+dj
        if not (0 <= i < n and 0 <= j < n): break
        ch.append((i, j))
    return ch

def cout_chemin(ch, E, regle):
    """Le cout d'un chemin de grille, avec EXACTEMENT la formule du Dijkstra."""
    c = E[ch[0]] * PAS_GRILLE if regle == 'somme' else E[ch[0]]
    for (i, j), (a, b) in zip(ch, ch[1:]):
        w = math.hypot(a-i, b-j)
        c = c + E[a, b]*w*PAS_GRILLE if regle == 'somme' else max(c, E[a, b])
    return c

# ---------------------------------------------------------------- les donnees
src = json.load(open(TRAJ))[:20]
arma = {}
for l in open(LOG, errors='ignore'):
    m = re.search(r'HMT\|AG\|essai\|(\d+)\|(\w+)\|know\|([\d.]+)\|reste\|(\d+)\|dist_detect\|(-?\d+)', l)
    if m:
        c, lib = int(m.group(1)), m.group(2)
        arma.setdefault(c, {})[lib] = dict(know=float(m.group(3)), reste=int(m.group(4)),
                                           dd=int(m.group(5)))
print(f"  {len(src)} configurations · {len(arma)} rejouees dans Arma")

# ---------------------------------------------------------------- C1 : coherence de expo()
c = src[0]; D0 = np.array(c['defenseurs'], float)
ech = np.random.default_rng(0).uniform(-80, 80, (200, 2))
po  = np.random.default_rng(1).integers(0, 3, 200)
ecart = np.abs(expo(ech, D0, po) - expo_naive(ech, D0, po)).max()
print(f"\n  C1 coherence expo (vectorise vs boucle) : ecart max {ecart:.2e}", end='  ')
if ecart > 1e-9: raise SystemExit("ECHEC C1 — les deux implementations divergent, rien ne vaut.")
print("OK")

# ---------------------------------------------------------------- C4 : controle nul
Dnul = D0.copy()
Dnul[:, 2] = (np.degrees(np.arctan2(-Dnul[:, 0], -Dnul[:, 1])) + 180) % 360   # dos tourne au centre
ax_n, E_n, R_n = grille(Dnul, 80.0)
bord_n = [(i, j) for i, j in zip(*np.where((R_n >= 80-2*PAS_GRILLE) & (R_n <= 80)))]
c_or, ch_or = dijkstra(E_n, R_n, bord_n, 'max')
dep = np.array([0.0, 80.0])
_, m_dr = score(np.stack([dep, dep*ARRIVE/80]), Dnul)
print(f"  C4 controle nul (defenseurs dos tourne) : oracle {c_or:.3f} · droite {m_dr:.3f}", end='  ')
print("OK" if abs(c_or - m_dr) < 0.15 else "ATTENTION — ils devraient se rejoindre")

# ---------------------------------------------------------------- la table
print("\n" + "="*104)
print("  cfg |        SOMME (aire d'exposition)        |          MAX (le pic qu'Arma retient)        | Arma")
print("      | oracle   agent  agent-D  droite         | oracle   agent  agent-D  droite   or.libre   | ag.  dr.")
print("-"*104)

L = []
for k, c in enumerate(src):
    defs = np.array(c['defenseurs'], float)
    traj = np.array(c['agent'], float)
    post = np.array(c['postures'], int)
    dep = traj[0]
    r_dep = float(np.hypot(*dep))
    rayon = max(r_dep, float(np.linalg.norm(traj, axis=1).max())) + 3
    ax, E, R = grille(defs, rayon)

    # depart de l'agent -> cellule de grille ; ligne droite = meme depart, droit au centre
    ci = int(np.argmin(np.abs(ax - dep[1]))); cj = int(np.argmin(np.abs(ax - dep[0])))
    droite = np.stack([dep, dep*ARRIVE/r_dep])

    s_or, ch_s = dijkstra(E, R, [(ci, cj)], 'somme')
    m_or, ch_m = dijkstra(E, R, [(ci, cj)], 'max')
    # ORACLE LIBRE : il choisit son point de depart SUR LE MEME CERCLE que l'agent.
    # ⟨premier jet : je le faisais partir du bord de la grille, un cercle PLUS GRAND que
    #  celui de l'agent — l'ensemble contraint n'y etait meme pas inclus, d'ou 7 violations
    #  de l'emboitement logique⟩
    bord = [(i, j) for i, j in zip(*np.where(np.abs(R - r_dep) <= PAS_GRILLE))]
    if (ci, cj) not in bord: bord.append((ci, cj))
    _, ch_lib = dijkstra(E, R, bord, 'max')

    # les CONTROLES se jouent sur la grille, ou l'optimalite est stricte
    ch_dr = droite_sur_grille(E, R, (ci, cj))
    g_or_s, g_or_m = cout_chemin(ch_s, E, 'somme'), cout_chemin(ch_m, E, 'max')
    g_dr_s, g_dr_m = cout_chemin(ch_dr, E, 'somme'), cout_chemin(ch_dr, E, 'max')
    g_lib_m = cout_chemin(ch_lib, E, 'max') if ch_lib else float('inf')

    s_ag, m_ag = score(traj, defs, post)          # l'agent avec SES postures
    s_agD, m_agD = score(traj, defs)              # le meme chemin, debout : isole l'effet posture
    s_dr, m_dr = score(droite, defs)
    # l'oracle est calcule DEBOUT : on le rescore sur son propre chemin, meme convention
    s_orc, _ = score(en_metres(ch_s, ax), defs) if ch_s else (float('inf'), 0)
    _, m_orc = score(en_metres(ch_m, ax), defs) if ch_m else (0, float('inf'))
    _, m_lib = score(en_metres(ch_lib, ax), defs) if ch_lib else (0, float('inf'))

    a = arma.get(k+1, {})
    dd_a = a.get('agent', {}).get('dd', None); dd_d = a.get('droite', {}).get('dd', None)
    L.append(dict(cfg=k+1, s_or=s_orc, s_ag=s_ag, s_agD=s_agD, s_dr=s_dr,
                  m_or=m_orc, m_ag=m_ag, m_agD=m_agD, m_dr=m_dr, m_lib=m_lib,
                  g_or_s=g_or_s, g_dr_s=g_dr_s, g_or_m=g_or_m, g_dr_m=g_dr_m, g_lib_m=g_lib_m,
                  n_couche=int((post == 2).sum()), n_pas=len(post),
                  dd_a=dd_a, dd_d=dd_d,
                  know_d=a.get('droite', {}).get('know', None),
                  reste_a=a.get('agent', {}).get('reste', None)))
    f = lambda v: f"{v:6.2f}" if v is not None and np.isfinite(v) else "     ."
    g = lambda v: f"{v:4d}" if v is not None else "   ."
    print(f"  {k+1:3d} | {f(s_orc)} {f(s_ag)} {f(s_agD)} {f(s_dr)}         "
          f"| {f(m_orc)} {f(m_ag)} {f(m_agD)} {f(m_dr)} {f(m_lib)}   | {g(dd_a)} {g(dd_d)}")

np.save('/mnt/data/corpus/table_arbitrage.npy', np.array(
    [[d['s_or'], d['s_ag'], d['s_agD'], d['s_dr'],
      d['m_or'], d['m_ag'], d['m_agD'], d['m_dr'], d['m_lib']] for d in L], float))

# ---------------------------------------------------------------- les controles de la table
print("="*104)
# C2 se juge SUR LA GRILLE, ou l'optimalite est stricte : meme espace, meme fonctionnelle.
viol2m = [d['cfg'] for d in L if d['g_or_m'] > d['g_dr_m'] + 1e-9]
viol2s = [d['cfg'] for d in L if d['g_or_s'] > d['g_dr_s'] + 1e-6]
viol3  = [d['cfg'] for d in L if d['g_lib_m'] > d['g_or_m'] + 1e-9]
print(f"\n  C2 optimalite sur grille : max {len(viol2m)} violation(s) {viol2m or ''} · "
      f"somme {len(viol2s)} violation(s) {viol2s or ''}")
print(f"  C3 emboitement (oracle libre <= contraint) : {len(viol3)} violation(s) {viol3 or ''}")
if viol2m or viol2s or viol3:
    raise SystemExit("\n  ECHEC : le plus court chemin est faux. La table ne vaut rien.")

# de combien la discretisation coute-t-elle ? mesure, pas supposee
disc = np.median([d['s_dr'] and abs(d['g_dr_s'] - d['s_dr'])/max(d['s_dr'], 1e-9) for d in L])
print(f"  cout de la discretisation (droite grille vs droite continue) : {disc:.1%} en mediane")

nc = sum(d['n_couche'] for d in L); npas = sum(d['n_pas'] for d in L)
print(f"  postures de l'agent : couche sur {nc}/{npas} pas ({nc/npas:.0%}) — "
      f"{'il ne se couche jamais' if nc == 0 else 'il se couche'}")

med = lambda v: float(np.median([d[v] for d in L]))
print(f"\n  C5 presence : sous MAX, droite {med('m_dr'):.3f} · oracle {med('m_or'):.3f}  "
      f"-> l'oracle achete {(1-med('m_or')/max(med('m_dr'),1e-9)):.0%} du pic")

# ---------------------------------------------------------------- L'ARBITRAGE
print("\n" + "="*104)
print("  L'ARBITRAGE — les predictions deposees avant le calcul")
print("="*104)

# A. sous SOMME, l'oracle-max (long, serpentant) est-il PIRE que l'agent ?
s_or_max = []
for k, c in enumerate(src):
    defs = np.array(c['defenseurs'], float)
    traj = np.array(c['agent'], float); dep = traj[0]
    rayon = max(np.hypot(*dep), np.abs(traj).max()) + 2
    ax, E, R = grille(defs, rayon)
    ci = int(np.argmin(np.abs(ax - dep[1]))); cj = int(np.argmin(np.abs(ax - dep[0])))
    _, ch_m = dijkstra(E, R, [(ci, cj)], 'max')
    s_or_max.append(score(en_metres(ch_m, ax), defs)[0] if ch_m else float('inf'))

pire = sum(1 for k, d in enumerate(L) if s_or_max[k] >= d['s_ag'] - 1e-6)
print(f"\n  1. Sous la regle SOMME, le chemin de l'oracle-max score PIRE (ou egal) que celui")
print(f"     de l'agent dans  {pire} / {len(L)}  configurations.")
print(f"     -> la somme punissait bien la manoeuvre : la sandbox PREFERAIT le rachat." if pire >= len(L)*0.4
      else f"     -> la somme ne punissait pas la manoeuvre. Le cliquet n'explique pas le refus.")

ecrase = sum(1 for d in L if d['m_or'] < d['m_ag'] - 0.02)
print(f"\n  2. Sous la regle MAX, l'oracle ecrase l'agent dans  {ecrase} / {len(L)}  configurations.")
print(f"     ecart median du pic : agent {med('m_ag'):.3f} contre oracle {med('m_or'):.3f}")

# B. le simulateur classe-t-il comme Arma ? correlation de rang, ecrite a la main
def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    if len(a) < 4: return float('nan'), 0
    r = lambda v: np.argsort(np.argsort(v)).astype(float)
    ra, rb = r(a), r(b)
    return float(np.corrcoef(ra, rb)[0, 1]), len(a)

# Arma : dist_detect ELEVEE = repere de loin = MAUVAIS. Sandbox : pic ELEVE = MAUVAIS.
# Les deux vont donc dans le meme sens, la correlation doit etre POSITIVE.
# -1 = JAMAIS repere : c'est le MEILLEUR resultat, pas le pire. Le compter tel quel le
# placerait au rang le plus bas et inverserait sa contribution. ⟨lire_agent.py le convertit
# deja en 80 m ; je l'avais oublie ici — le controle de coherence entre les deux depouilleurs
# n'existait pas⟩
dda = lambda v: (80 if v is not None and v < 0 else v)
rho_ag, n_ag = spearman([d['m_ag'] for d in L], [dda(d['dd_a']) for d in L])
rho_dr, n_dr = spearman([d['m_dr'] for d in L], [dda(d['dd_d']) for d in L])
tous_s = [d['m_ag'] for d in L] + [d['m_dr'] for d in L]
tous_a = [dda(d['dd_a']) for d in L] + [dda(d['dd_d']) for d in L]
rho_t, n_t = spearman(tous_s, tous_a)
print(f"\n  3. Le simulateur classe-t-il les trajectoires comme Arma ?")
print(f"     correlation de rang (pic sandbox <-> distance de reperage Arma)")
print(f"       sur les chemins d'agent  : rho = {rho_ag:+.2f}  (n={n_ag})")
print(f"       sur les lignes droites   : rho = {rho_dr:+.2f}  (n={n_dr})")
print(f"       sur les deux ensemble    : rho = {rho_t:+.2f}  (n={n_t})")
print(f"     -> {'FIDELE : le probleme est l apprentissage, pas le monde.' if rho_t > 0.7 else 'BASSE — mais NE PAS conclure avant le test de dynamique ci-dessous :' if rho_t < 0.4 else 'INTERMEDIAIRE : ni innocente ni condamne.'}")
if rho_t < 0.4:
    print(f"        une correlation nulle accuse le simulateur SEULEMENT si l'instrument de")
    print(f"        reference sait, lui, separer les trajectoires.")

med_dr, med_or, med_lib = med('m_dr'), med('m_or'), med('m_lib')
print(f"\n  4. QUI DECIDE : le chemin, ou le point de depart ?")
print(f"     pic median — ligne droite {med_dr:.3f}")
print(f"                  meilleur chemin depuis LE DEPART IMPOSE  {med_or:.3f}   "
      f"(gagne {med_dr-med_or:.3f})")
print(f"                  meilleur chemin en CHOISISSANT son depart {med_lib:.3f}   "
      f"(gagne {med_or-med_lib:.3f})")
part = (med_or-med_lib) / max(med_dr-med_lib, 1e-9)
print(f"     -> {part:.0%} de tout ce qu'il y a a gagner tient au CHOIX DU DEPART,")
print(f"        et non a la maniere de marcher ensuite.")
# ---------------------------------------------------------------- L'INSTRUMENT EST-IL SATURE ?
# Une correlation nulle a deux lectures : le simulateur predit mal, OU l'instrument de
# reference ne discrimine rien. Il faut trancher avant d'accuser le simulateur.
# ⟨mesure certifiee le 03/08 : dans le cone, on est repere vers 105 m. Le banc fait partir
#  l'agent a 80 m — donc DEJA a l'interieur de la portee de detection.⟩
r_dep_med = float(np.median([np.hypot(*np.array(c['agent'], float)[0]) for c in src]))
brut = [d['dd_a'] for d in L] + [d['dd_d'] for d in L]
brut = [v for v in brut if v is not None]
# « jamais repere » (-1) et « repere des le premier metre » (80) sont deux resultats OPPOSES
# que la convention de depouillement confond en une seule valeur. On les separe ici.
jam = sum(1 for v in brut if v < 0)
tous = [dda(v) for v in brut]
vus = [v for v in brut if v >= 0]
imm = sum(1 for v in vus if v >= r_dep_med - 12)       # repere dans les 12 premiers metres
print(f"\n     L'INSTRUMENT DISCRIMINE-T-IL ?  depart a {r_dep_med:.0f} m, "
      f"detection frontale mesuree a 105 m dans Arma.")
print(f"     jamais repere : {jam}/{len(brut)}.  Parmi les {len(vus)} reperes, "
      f"{imm} le sont dans les 12 premiers metres ({imm/max(len(vus),1):.0%}).")
iqr = float(np.percentile(vus, 75) - np.percentile(vus, 25))
dyn = iqr / max(r_dep_med - ARRIVE, 1e-9)     # part de la plage utile reellement exploree
print(f"     distances des reperes : mediane {np.median(vus):.0f} m · "
      f"ecart interquartile {iqr:.0f} m sur {r_dep_med-ARRIVE:.0f} m utiles "
      f"-> DYNAMIQUE {dyn:.0%}")
if dyn < 0.25:
    print(f"     -> INSTRUMENT ECRASE CONTRE SON PLAFOND. On part a {r_dep_med:.0f} m alors que la")
    print(f"        detection frontale se fait a 105 m : l'approchant est DEJA VU au depart.")
    print(f"        Avec {dyn:.0%} de dynamique, une correlation nulle ne prouve RIEN sur le")
    print(f"        simulateur. La question 3 reste OUVERTE — il faut refaire le banc plus loin.")
else:
    print(f"     -> le banc discrimine ; la correlation nulle accuse bien le simulateur.")

print(f"\n  5. Ce qu'Arma a mesure, pour memoire :")
va = [d for d in L if d['dd_a'] is not None and d['know_d'] is not None and d['know_d'] >= 1.5]
if va:
    da = np.mean([80 if d['dd_a'] < 0 else d['dd_a'] for d in va])
    dg = np.mean([80 if d['dd_d'] < 0 else d['dd_d'] for d in va])
    print(f"     sur {len(va)} configurations valides : agent repere a {da:.1f} m, "
          f"droite a {dg:.1f} m -> {(da-dg)/dg:+.0%}  (seuil ecrit avant : +25 %)")
print()
