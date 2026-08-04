#!/usr/bin/env python3
"""geom_ombre.py — la geometrie de l'ombre, en un seul exemplaire.

⟨POURQUOI CE MODULE. Le 04/08, deux depouilleurs du meme banc ne convertissaient pas
 « jamais repere » de la meme facon, et personne ne s'en apercevait. La regle qui en sort :
 une grandeur calculee a deux endroits finira par diverger. Elle vit donc ici, une fois.⟩

Tout est MESURE sur Arma, rien n'est supposé :
  demi-cone 35 deg (plateau plat 0-30, zero des 40)   ⟨banc du cone, 03/08⟩
  couche : inutile sous 100 m, invisible au-dela de 130 m, seuil ~120 m  ⟨banc couvert⟩
"""
import math, heapq
import numpy as np

CHAMP        = 35.0
SEUIL_COUCHE = 120.0
PENTE_COUCHE = 12.0
ARRIVE       = 40.0
PAS_GRILLE   = 1.0
PAS_CHEMIN   = 1.0

def sig(x): return 1.0/(1.0+np.exp(-x))

def expo(pts, defs, posture=None):
    """exposition instantanee, MAXIMUM sur les defenseurs.
    ⟨le maximum et non la moyenne : knowsAbout est de CAMP, un seul homme qui voit suffit⟩"""
    p = np.asarray(pts, float).reshape(-1, 2)
    defs = np.asarray(defs, float)
    xy, az = defs[:, :2], defs[:, 2]
    v = p[:, None, :] - xy[None, :, :]
    d = np.maximum(np.linalg.norm(v, axis=-1), 1.0)
    gis = np.degrees(np.arctan2(v[..., 0], v[..., 1])) % 360
    ec = np.abs((gis - az[None, :] + 180) % 360 - 180)
    dans = sig((CHAMP - ec) * 1.2)
    base = 0.45 * (1.0 - np.clip(d/400, 0, 1))
    e = (base + (1.0-base)*dans) * (1.0 - np.clip(d/450, 0, 1))
    if posture is not None:
        couche = 1.0 - sig((d - SEUIL_COUCHE) / PENTE_COUCHE)
        e = e * np.where(np.asarray(posture, int)[:, None] == 2, couche, 1.0)
    return e.max(axis=1)

def expo_naive(pts, defs, posture=None):
    """la MEME chose, ecrite autrement : boucle explicite, aucun broadcast. Temoin permanent."""
    out = []
    for k, (px, py) in enumerate(np.asarray(pts, float).reshape(-1, 2)):
        best = 0.0
        for dx, dy, a in np.asarray(defs, float):
            vx, vy = px-dx, py-dy
            d = max(math.hypot(vx, vy), 1.0)
            ec = abs((math.degrees(math.atan2(vx, vy)) % 360 - a + 180) % 360 - 180)
            dans = 1/(1+math.exp(-(CHAMP-ec)*1.2))
            base = 0.45*(1 - min(max(d/400, 0), 1))
            e = (base + (1-base)*dans) * (1 - min(max(d/450, 0), 1))
            if posture is not None and int(posture[k]) == 2:
                e *= 1 - 1/(1+math.exp(-(d-SEUIL_COUCHE)/PENTE_COUCHE))
            best = max(best, e)
        out.append(best)
    return np.array(out)

def reechantillonne(poly, pas=PAS_CHEMIN):
    """une polyligne -> des points espaces de `pas`. Sans ca la SOMME dependrait du nombre
    de sommets et non du trajet, et deux chemins ne seraient plus comparables."""
    poly = np.asarray(poly, float)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])
    if L[-1] < 1e-9: return poly[:1]
    s = np.arange(0, L[-1] + 1e-9, pas)
    return np.stack([np.interp(s, L, poly[:, 0]), np.interp(s, L, poly[:, 1])], -1)

def score(poly, defs, posture_poly=None):
    """les DEUX regles sur le meme chemin : la somme (aire) et le pic (ce qu'Arma retient)."""
    p = reechantillonne(poly)
    post = None
    if posture_poly is not None:
        src = np.asarray(poly, float)
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(src, axis=0), axis=1))])
        s = np.linspace(0, L[-1], len(p)) if L[-1] > 0 else np.zeros(len(p))
        post = np.array([posture_poly[int(np.argmin(np.abs(L - u)))] for u in s])
    e = expo(p, defs, post)
    return float(e.sum() * PAS_CHEMIN), float(e.max())

def grille(defs, rayon):
    n = int(2*rayon/PAS_GRILLE) + 1
    ax = np.linspace(-rayon, rayon, n)
    X, Y = np.meshgrid(ax, ax)
    E = expo(np.stack([X.ravel(), Y.ravel()], -1), defs).reshape(n, n)
    return ax, E, np.hypot(X, Y)

VOIS = [(-1,0,1.),(1,0,1.),(0,-1,1.),(0,1,1.),
        (-1,-1,2**.5),(-1,1,2**.5),(1,-1,2**.5),(1,1,2**.5)]

def dijkstra(E, R, departs, regle, arrive=ARRIVE):
    """'somme' : cout = integrale de l'exposition. 'max' : cout = pic rencontre
    (plus court chemin de goulot — c'est CA qu'Arma retient, irreversiblement)."""
    n = E.shape[0]
    cout = np.full((n, n), np.inf)
    prev = np.full((n, n, 2), -1, int)
    tas = []
    for i, j in departs:
        c = E[i, j]*PAS_GRILLE if regle == 'somme' else E[i, j]
        if c < cout[i, j]:
            cout[i, j] = c; heapq.heappush(tas, (c, i, j))
    dedans = R <= (n-1)/2*PAS_GRILLE + 1e-9
    fin = None
    while tas:
        c, i, j = heapq.heappop(tas)
        if c > cout[i, j] + 1e-12: continue
        if R[i, j] <= arrive: fin = (i, j); break
        for di, dj, w in VOIS:
            a, b = i+di, j+dj
            if not (0 <= a < n and 0 <= b < n and dedans[a, b]): continue
            nc = c + E[a, b]*w*PAS_GRILLE if regle == 'somme' else max(c, E[a, b])
            if nc < cout[a, b] - 1e-12:
                cout[a, b] = nc; prev[a, b] = (i, j); heapq.heappush(tas, (nc, a, b))
    if fin is None: return np.inf, None
    ch = []; i, j = fin
    while i >= 0: ch.append((i, j)); i, j = prev[i, j]
    return cout[fin], ch[::-1]

def cout_chemin(ch, E, regle):
    """le cout d'un chemin de grille, avec EXACTEMENT la formule du Dijkstra.
    ⟨les controles se jugent la-dessus : meme espace, meme fonctionnelle, optimalite stricte⟩"""
    c = E[ch[0]]*PAS_GRILLE if regle == 'somme' else E[ch[0]]
    for (i, j), (a, b) in zip(ch, ch[1:]):
        w = math.hypot(a-i, b-j)
        c = c + E[a, b]*w*PAS_GRILLE if regle == 'somme' else max(c, E[a, b])
    return c

def en_metres(ch, ax):
    return np.array([[ax[j], ax[i]] for i, j in ch])       # X = colonne, Y = ligne

def droite_sur_grille(E, R, depart, arrive=ARRIVE):
    """la ligne droite depart -> centre, PARCOURUE SUR LA GRILLE."""
    n = E.shape[0]; i, j = depart; ch = [(i, j)]
    while R[i, j] > arrive:
        vi, vj = (n-1)/2 - i, (n-1)/2 - j
        nr = max(math.hypot(vi, vj), 1e-9)
        di, dj = int(round(vi/nr)), int(round(vj/nr))
        if di == 0 and dj == 0: break
        i, j = i+di, j+dj
        if not (0 <= i < n and 0 <= j < n): break
        ch.append((i, j))
    return ch

def controle_coherence(defs, graine=0):
    """C1 — la version vectorisee et la version en boucle doivent coincider."""
    ech = np.random.default_rng(graine).uniform(-150, 150, (200, 2))
    po = np.random.default_rng(graine+1).integers(0, 3, 200)
    return float(np.abs(expo(ech, defs, po) - expo_naive(ech, defs, po)).max())
