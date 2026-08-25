#!/usr/bin/env python3
"""entites — LES UNITÉS COMME UNE LISTE, PAS COMME DES PIXELS.

POURQUOI CE FICHIER EXISTE
  Le raster écrase chaque unité dans une cellule de 12,5 m. C'est précisément l'information
  que l'encodeur mesuré à +4,5 pts conservait : « transformeur d'ensemble, entrée = N agents
  × (x, y, camp, acteur, visible), invariant à l'ordre et à effectif variable ».
  Et c'est la bascule d'AlphaStar : SC2LE lisait des cartes convolutives et n'a pas gagné une
  partie contre l'IA la plus facile ; AlphaStar a mis les unités en LISTE D'ENTITÉS lue par
  attention, la carte devenant secondaire. OpenAI Five n'a jamais eu ni pixels ni carte.

CE QUI EST TENU CONSTANT AVEC LE BRAS B — et c'est tout l'intérêt
  Le TERRAIN reste une image lue par convolution (couvert, pente, bâti, danger). Seule la
  représentation des UNITÉS change : rasterisée dans B, exacte et attentionnelle ici.
  Un bras qui changerait les deux à la fois ne dirait pas lequel des deux porte l'écart.
"""
import math
import torch

# (f, l, dist, ennemi, allié, je_le_vois, IL_ME_VOIT) — repère du raster : objectif EN HAUT
#
# ⚠️ TROIS CORRECTIONS ⟨Fable, 25/08⟩, avant tout entraînement :
#  · `vivant` RETIRÉ — les morts sont masqués hors de l'attention, donc tout jeton présent
#    portait vivant=1 : une entrée CONSTANTE, exactement ce que les sondes interdisent.
#    On masque OU on drapeaute, jamais les deux.
#  · `IL_ME_VOIT` AJOUTÉ, et il n'est PAS le symétrique de `je_le_vois` : il vaut ligne de
#    vue ET être dans son ARC. Mesure : 18/18 touchés dans le cône contre 0/26 hors, et
#    être vu tue 2× plus fort que voir ne protège (+75 % sur 563 000 observations).
#    Sans ce trait, la seule voie vers l'angle mort est le canal `danger` du CNN — celle
#    que le bras B vient de montrer inerte.
#  · le POOLING passe de max seul à max ‖ moyenne — un max par dimension écrase les
#    cardinalités, or la détection en cascade dit que le NOMBRE de défenseurs structure le
#    régime (zone utile 5-8 défenseurs). Le coût est nul.
NF_TOK = 7
CANAUX_TERRAIN = ("couvert", "pente", "bati", "danger")


def entites(e):
    """Une ligne par unité, coordonnées EXACTES. -> jetons (N, A, U, 7), masque (N, A, U)

    U = D défenseurs + (A-1) camarades. L'homme lui-même n'est pas un jeton : il EST
    l'origine du repère. Les morts sont MASQUÉS, jamais mis à zéro — un zéro est une
    position, et l'attention le lirait comme « une unité au centre ».
    """
    N, A, D, S, d = e.N, e.A, e.D, e.scale, e.dev
    th0 = torch.atan2(-e.apx, -e.apy)                       # (N,A) azimut vers l objectif
    s = torch.sin(th0).unsqueeze(2); c = torch.cos(th0).unsqueeze(2)

    def bloc(px, py, je_vois, est_ennemi, me_voit):
        dx = px.unsqueeze(1) - e.apx.unsqueeze(2)           # (N,A,U)
        dy = py.unsqueeze(1) - e.apy.unsqueeze(2)
        f = (dx * s + dy * c) / S                            # AVANT, exact
        l = (dx * c - dy * s) / S                            # LATÉRAL, exact
        dist = torch.sqrt(dx * dx + dy * dy) / S
        un = torch.ones_like(f) * (1.0 if est_ennemi else 0.0)
        return torch.stack([f, l, dist, un, 1.0 - un, je_vois, me_voit], dim=3)

    # --- défenseurs : `vu` = la ligne de vue entre lui et moi (celle-là même qui décide du feu)
    losd = []
    for di in range(D):
        bx = e.dpx[:, di:di + 1].expand(N, A); by = e.dpy[:, di:di + 1].expand(N, A)
        losd.append(e._losc(e.hm, e.apx, e.apy, bx, by, S, eye_a=e._eye(), eye_b=1.7))
    losd = torch.stack(losd, dim=2)                          # (N,A,D) : je le vois
    # --- IL ME VOIT = ligne de vue ET je suis dans son arc de tir. Meme filtre que celui
    #     qui decide reellement du feu dans `_champ_danger` — on ne souffle pas la reponse,
    #     on donne la meme geometrie que le monde utilise pour facturer.
    if e.def_line and hasattr(e, "dface"):
        az = torch.atan2(e.apx.unsqueeze(2) - e.dpx.unsqueeze(1),
                         e.apy.unsqueeze(2) - e.dpy.unsqueeze(1))       # (N,A,D) defenseur -> moi
        rel = torch.atan2(torch.sin(az - e.dface.unsqueeze(1)), torch.cos(az - e.dface.unsqueeze(1)))
        dans_arc = (rel.abs() <= e._dfarc.view(N, 1, 1)).float()
    else:
        dans_arc = torch.ones_like(losd)
    me_voit = losd * dans_arc
    jd = bloc(e.dpx, e.dpy, losd, True, me_voit)

    # --- camarades : on se voit entre soi ; « il me voit » n a pas de sens -> 0
    va = e._aalive().float().unsqueeze(1).expand(N, A, A)
    ja = bloc(e.apx, e.apy, torch.ones_like(va), False, torch.zeros_like(va))

    jetons = torch.cat([jd, ja], dim=2)                      # (N,A,D+A,7)
    moi = torch.eye(A, dtype=torch.bool, device=d).view(1, A, A).expand(N, A, A)
    vd = e._dalive().float().unsqueeze(1).expand(N, A, D)
    vivant = torch.cat([vd, va], dim=2) > 0.5
    pas_moi = torch.cat([torch.ones(N, A, D, dtype=torch.bool, device=d), ~moi], dim=2)
    return jetons, vivant & pas_moi                          # masque : True = jeton REEL


def brouilleur_entites(seed=1234):
    """LE CONTRÔLE, calqué sur celui du football : on PERMUTE LES POSITIONS ENTRE UNITÉS.

    Dans la mesure d'origine, cette permutation faisait tomber 0,644 à 0,623 — c'est elle
    qui a établi que le réseau lisait la géométrie et pas le simple comptage. On garde
    l'identité (camp, vivant, vu) en place et on redistribue (f, l, dist) : mêmes unités,
    mêmes positions dans le lot, autre appariement.
    """
    g = torch.Generator(device="cpu").manual_seed(seed)
    def f(jetons, masque):
        N, A, U, F = jetons.shape
        p = torch.stack([torch.randperm(U, generator=g) for _ in range(8)]).to(jetons.device)
        idx = p[torch.arange(N * A, device=jetons.device) % 8]          # (N*A, U)
        pos = jetons[..., :3].reshape(N * A, U, 3)
        pos = torch.gather(pos, 1, idx.unsqueeze(-1).expand(N * A, U, 3))
        out = jetons.clone(); out[..., :3] = pos.reshape(N, A, U, 3)
        return out, masque
    return f
