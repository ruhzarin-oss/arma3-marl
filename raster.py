#!/usr/bin/env python3
"""raster — l'observation EGOCENTRIQUE MULTI-CANAUX, lue par convolution.

POURQUOI CE FICHIER EXISTE
  `assault_terrain._local_grid()` fait deja une fenetre KxK de [couvert, pente], mais
  (a) ALIGNEE SUR LE MONDE — son propre commentaire dit « rotation egocentrique = etape + »
  (b) APLATIE dans un MLP, donc la structure spatiale est detruite avant d etre lue.
  Ici on redresse les deux, et on ajoute les canaux qui manquaient : le PRIX du terrain
  (le champ de danger, generalise de K directions a K x K cellules), les ennemis, les allies.

CE QU IL NE FAIT PAS
  Il ne touche PAS `assault_terrain.py`. Tout se lit sur l objet env deja construit, donc
  aucun banc existant ne change de comportement. C est deliberе.

LE REPERE
  Convention du depot : `cap = atan2(dx, dy)`, angle mesure depuis +y vers +x, et
  `cx = apx + sin(th)*R`. On garde exactement cette convention.
  Cap de reference th0 = azimut vers l OBJECTIF (qui est a l origine, cf. `dgx = -apx`).
  Donc dans le raster, L OBJECTIF EST TOUJOURS EN HAUT. C est ce qui rend la convolution
  legitime : une meme configuration geometrique produit le meme motif de pixels, quel que
  soit l endroit de la carte ou elle se produit. Sans rotation, le CNN devrait reapprendre
  chaque motif dans huit orientations.
"""
import math
import torch

CANAUX_DEFAUT = ("couvert", "pente", "bati", "danger", "ennemis", "allies")

# ─── LA FENETRE SE DIMENSIONNE, ELLE NE SE CHOISIT PAS ⟨sonde2, 25/08⟩ ───────────
# Part des defenseurs vivants tombant dans la fenetre, doctrine frontale du depot,
# 256 environnements, graine 11 :
#       pas 0 (170 m du but)   span 120 : 0,000 | 180 : 0,000 | 240 : 0,014 | 300 : 0,978
#       pas 6  (95 m)          span 120 : 0,482 | 180 : 0,994 | 240 : 1,000 | 300 : 1,000
# On retient SPAN=300 : c est la seule qui montre le defenseur AU DEPART. Ce n est pas
# un gout — c est le defaut nomme dans `agent-percoit-pas-manoeuvre` : « a 170 m, rien
# dans son observation ne lui dit qu il paie deja », et c est pour ca qu il contourne a
# 132 m quand le bon crochet se fait a 184.
# K=24 -> 12,5 m par cellule. Le terrain lui-meme est echantillonne a 400/64 = 6,25 m ;
# on perd donc un facteur 2 de resolution, jamais plus.
K_DEFAUT, SPAN_DEFAUT = 24, 300.0


def _grille_ego(e, K, span, ego=True):
    """Les coordonnees MONDE des K x K cellules, pour chaque homme. -> (N, A, K, K) x2

    Indexation : [.., i, j] avec i = AVANT (croissant vers l objectif), j = LATERAL.
    Grille centree sur l homme, cote `span` metres.
    """
    N, A, d = e.N, e.A, e.dev
    off = (torch.arange(K, device=d).float() / (K - 1) - 0.5) * span      # (K,)
    f = off.view(1, 1, K, 1).expand(N, A, K, K)                           # avant
    l = off.view(1, 1, 1, K).expand(N, A, K, K)                           # lateral
    if ego:
        th0 = torch.atan2(-e.apx, -e.apy)                                 # azimut vers l objectif
        s = torch.sin(th0).view(N, A, 1, 1); c = torch.cos(th0).view(N, A, 1, 1)
    else:
        s = torch.zeros(N, A, 1, 1, device=d); c = torch.ones(N, A, 1, 1, device=d)
    gx = e.apx.view(N, A, 1, 1) + f * s + l * c
    gy = e.apy.view(N, A, 1, 1) + f * c - l * s
    return gx, gy


def _splat(e, K, span, px, py, poids, ego=True, sauf_soi=False):
    """Depose des points MONDE (px,py) dans la grille egocentrique. -> (N, A, K, K)

    `px,py,poids` sont (N, M) : M points par environnement, communs aux A hommes.
    Depot au plus proche voisin, accumule (`index_add_`), hors-champ ignore.
    `sauf_soi` : l homme i ne se depose pas lui-meme (il EST le centre de son image ;
    l y remettre gaverait une cellule d une constante, une entree morte de plus).
    """
    N, A, d = e.N, e.A, e.dev
    M = px.shape[1]
    dx = px.view(N, 1, M) - e.apx.view(N, A, 1)
    dy = py.view(N, 1, M) - e.apy.view(N, A, 1)
    if ego:
        th0 = torch.atan2(-e.apx, -e.apy).view(N, A, 1)
        s, c = torch.sin(th0), torch.cos(th0)
        f = dx * s + dy * c        # composante AVANT
        l = dx * c - dy * s        # composante LATERALE
    else:
        f, l = dy, dx
    demi = span * 0.5
    ii = torch.round((f + demi) / span * (K - 1)).long()
    jj = torch.round((l + demi) / span * (K - 1)).long()
    ok = (ii >= 0) & (ii < K) & (jj >= 0) & (jj < K) & (poids.view(N, 1, M) > 0)
    if sauf_soi:
        assert M == A, "sauf_soi n a de sens que si les points SONT les hommes"
        ok = ok & ~torch.eye(A, dtype=torch.bool, device=d).view(1, A, A)
    plat = torch.zeros(N * A * K * K, device=d)
    idx = (torch.arange(N * A, device=d).view(N, A, 1) * (K * K)
           + ii.clamp(0, K - 1) * K + jj.clamp(0, K - 1))
    plat.index_add_(0, idx[ok].reshape(-1),
                    (poids.view(N, 1, M).expand(N, A, M))[ok].reshape(-1))
    return plat.view(N, A, K, K)


def _danger_cellules(e, gx, gy):
    """LE PRIX DU TERRAIN, cellule par cellule. -> (N, A, K, K)

    Transcription FIDELE de `AssaultTerrain._champ_danger`, ou les K directions sur un
    cercle deviennent les K x K cellules de la grille. Meme somme sur les defenseurs
    vivants, meme filtrage par ligne de vue et par arc de tir, meme courbe de toucher.
    On donne le PRIX, jamais la reponse : le moins cher reste toujours de fuir.
    """
    N, A, D, S = e.N, e.A, e.D, e.scale
    K = gx.shape[-1]
    M = A * K * K
    cx = gx.reshape(N, M); cy = gy.reshape(N, M)
    danger = torch.zeros(N, M, device=e.dev)
    eye = e._eye()
    eye_c = (eye.unsqueeze(-1).unsqueeze(-1).expand(N, A, K, K).reshape(N, M)
             if torch.is_tensor(eye) else eye)
    for di in range(D):
        bx = e.dpx[:, di:di + 1].expand(N, M); by = e.dpy[:, di:di + 1].expand(N, M)
        vivant = e._dalive()[:, di:di + 1].float()
        los = e._losc(e.hm, cx, cy, bx, by, S, eye_a=eye_c, eye_b=1.7)
        dist = torch.sqrt((cx - bx) ** 2 + (cy - by) ** 2)
        act = vivant.expand(N, M).clone()
        if e.def_line and hasattr(e, "dface"):
            _ang = torch.atan2(cx - bx, cy - by)
            _adf = torch.atan2(torch.sin(_ang - e.dface[:, di:di + 1]),
                               torch.cos(_ang - e.dface[:, di:di + 1]))
            act = act * (_adf.abs() <= e._dfarc).float()
        if e.courbe is not None:
            p = e._p_balle(dist) * e.tir_par_pas * e.degat_par_impact
        else:
            p = e.hit * (dist < e.fire_range).float()
        danger = danger + p * los * act
    return danger.reshape(N, A, K, K)


def raster(e, K=16, span=120.0, ego=True, canaux=CANAUX_DEFAUT):
    """L observation raster. -> (N, A, C, K, K)

    Chaque canal est borne dans [0, ~1] par la meme normalisation que l obs vectorielle
    existante, pour qu aucun canal n ecrase les autres par son echelle seule.
    """
    N, A, d = e.N, e.A, e.dev
    gx, gy = _grille_ego(e, K, span, ego=ego)
    M = A * K * K
    fx = gx.reshape(N, M); fy = gy.reshape(N, M)
    out = []
    for nom in canaux:
        if nom == "couvert":
            from assault_terrain import TG
            v = TG.sample(e.cover, fx, fy, e.scale)
        elif nom == "pente":
            from assault_terrain import TG
            v = TG.sample(e.slope, fx, fy, e.scale) / 5.0
        elif nom == "bati":
            from assault_terrain import TG
            v = (TG.sample(e.dcover, fx, fy, e.scale) / 30.0).clamp(max=1.0)
        elif nom == "danger":
            out.append(_danger_cellules(e, gx, gy)); continue
        elif nom == "ennemis":
            out.append(_splat(e, K, span, e.dpx, e.dpy, e._dalive().float(), ego=ego)); continue
        elif nom == "allies":
            out.append(_splat(e, K, span, e.apx, e.apy, e._aalive().float(), ego=ego,
                              sauf_soi=True)); continue
        else:
            raise ValueError("canal inconnu : %s" % nom)
        out.append(v.reshape(N, A, K, K))
    return torch.stack(out, dim=2)


def brouilleur(K, C, device, seed=1234):
    """LE CONTROLE. Une permutation SPATIALE fixe, tiree une fois, appliquee a chaque canal.

    Elle detruit la geometrie et preserve EXACTEMENT la distribution marginale de chaque
    canal — memes valeurs, memes histogrammes, meme echelle, autres places. Si le bras
    brouille vaut le bras droit, le reseau ne lisait pas la geometrie : il lisait des
    statistiques, et le resultat ne veut rien dire.
    Permutation INDEPENDANTE par canal, pour casser aussi l alignement entre canaux
    (sinon « ici il y a du couvert ET peu de danger » survivrait au brouillage).
    """
    g = torch.Generator(device="cpu").manual_seed(seed)
    perms = torch.stack([torch.randperm(K * K, generator=g) for _ in range(C)]).to(device)
    def f(r):
        N, A, Cc, Kk, _ = r.shape
        flat = r.reshape(N, A, Cc, Kk * Kk)
        return torch.gather(flat, 3, perms.view(1, 1, Cc, Kk * Kk).expand(N, A, Cc, Kk * Kk)).reshape(N, A, Cc, Kk, Kk)
    return f
