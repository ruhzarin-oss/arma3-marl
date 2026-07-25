#!/usr/bin/env python3
"""intentions.py — LE VOCABULAIRE de l'agent autonome (étage 1).

Avant : on disait au soldat « va au FOB », le jeu calculait le chemin. Il ne décidait RIEN.
Après : il choisit CE QU'IL FAIT MAINTENANT, et le mène À SON TERME. On ne le coupe pas en route.

  AVANCER(point)   se porter sur un point choisi        -> fini quand il y est (ou bloqué/temps écoulé)
  S'ABRITER        se plaquer sur place, petite cible   -> fini après un délai
  APPUYER(ennemi)  tenir et supprimer                   -> fini quand l'ennemi tombe (ou délai)
  DÉCROCHER(point) rompre vers l'arrière, à couvert     -> fini quand il y est

Les points candidats sont calculés depuis le PLAN BAKÉ (bake_map.py) : aucune requête au jeu.
Chaque candidat est noté sur 3 critères — progression vers l'objectif, couvert, exposition.

Ce module ne parle pas à Arma : il est PUR (positions -> intentions). Donc réutilisable tel quel
côté sandbox comme côté Arma — c'est la couture.
"""
import json, math
import numpy as np

# --- types d'intention (l'ordre compte : c'est le code envoyé à l'exécuteur SQF) ---
AVANCER, ABRITER, APPUYER, DECROCHER = 0, 1, 2, 3
NOMS = {AVANCER: "avancer", ABRITER: "s'abriter", APPUYER: "appuyer", DECROCHER: "décrocher"}


class TerrainExact:
    """Le RELEVÉ RÉEL demandé au moteur (bake_los.py) : altitude du sol + hauteur du premier obstacle,
    case par case. Remplace la reconstruction depuis les boîtes englobantes, qui bouchait les passages
    et ignorait le relief (à Pyrgos : 37 m de dénivelé purement et simplement absents du modèle)."""

    def __init__(self, npz):
        d = np.load(npz) if isinstance(npz, str) else npz
        self.sol = d["sol"]; self.obs = d["obs"]
        self.cx = float(d["cx"]); self.cy = float(d["cy"])
        self.cell = float(d["cell"]); self.R = float(d["radius"])
        self.N = self.sol.shape[0]
        self.avec_hauteurs = True
        try:
            from scipy import ndimage
            self.dcover = ndimage.distance_transform_edt(self.obs < 1.5) * self.cell
        except Exception:
            self.dcover = np.full_like(self.obs, 50.0)

    def idx(self, dx, dy):
        return int((dx + self.R) / self.cell), int((dy + self.R) / self.cell)

    def _in(self, i, j):
        return 0 <= i < self.N and 0 <= j < self.N

    def is_solid(self, dx, dy):
        """infranchissable = un obstacle de plus de 1,5 m (un muret se franchit, un mur non)"""
        i, j = self.idx(dx, dy)
        return not self._in(i, j) or bool(self.obs[j, i] > 1.5)

    def cover_at(self, dx, dy):
        i, j = self.idx(dx, dy)
        return float(self.dcover[j, i]) if self._in(i, j) else 99.0

    def los(self, ax, ay, bx, by, steps=28, ha=1.7, hb=1.0):
        """Vue A->B en altitude RÉELLE : on compare la ligne de visée au sommet (sol + obstacle).
        Le relief compte : depuis une hauteur, on voit par-dessus les toits."""
        ia, ja = self.idx(ax, ay); ib, jb = self.idx(bx, by)
        if not (self._in(ia, ja) and self._in(ib, jb)):
            return False
        za = self.sol[ja, ia] + ha
        zb = self.sol[jb, ib] + hb
        for k in range(1, steps):
            t = k / float(steps)
            i, j = self.idx(ax + (bx - ax) * t, ay + (by - ay) * t)
            if not self._in(i, j):
                continue
            if self.sol[j, i] + self.obs[j, i] > za + (zb - za) * t:
                return False
        return True


def charger_terrain(dossier, world, fx, fy):
    """Prend le relevé EXACT s'il existe, sinon retombe sur le plan reconstruit."""
    import os, glob as _g
    p = os.path.join(dossier, "los_%s_%d_%d.npz" % (world.lower(), fx, fy))
    if os.path.exists(p):
        return TerrainExact(p)
    for q in _g.glob(os.path.join(dossier, "map_*.json")):
        m = json.load(open(q))
        if abs(m.get("cx", 0) - fx) + abs(m.get("cy", 0) - fy) < 500:
            return Terrain(m)
    raise FileNotFoundError("aucun terrain pour %s [%d,%d]" % (world, fx, fy))


class Terrain:
    """Le plan de la zone, rasterisé une fois : mur/pas mur, distance au bâti, ligne de vue."""

    def __init__(self, map_json, cell=2.0, margin=40.0):
        m = json.load(open(map_json)) if isinstance(map_json, str) else map_json
        self.cx, self.cy = m["cx"], m["cy"]
        self.cell = cell
        R = m.get("radius", 320.0) + margin
        self.R = R
        self.N = int(2 * R / cell)
        g = np.zeros((self.N, self.N), dtype=bool)
        h = np.zeros((self.N, self.N), dtype="float32")   # HAUTEUR du bâti (m) : un muret ne bloque pas la vue d'un immeuble
        for o in m.get("bat", []):
            dx, dy, cap, w, l = o[0], o[1], o[2], max(o[3], 1), max(o[4], 1)
            haut = float(o[5]) if len(o) > 5 else 6.0     # plans anciens (sans hauteur) : on suppose 6 m
            self._stamp(g, dx, dy, cap, w, l, h, haut)
        self.solid = g
        self.h = h
        self.avec_hauteurs = any(len(o) > 5 for o in m.get("bat", []))
        try:
            from scipy import ndimage
            self.dcover = ndimage.distance_transform_edt(~g) * cell   # distance au bâti (m)
        except Exception:
            self.dcover = np.full_like(g, 50.0, dtype="float32")

    def _stamp(self, g, dx, dy, cap, w, l, h=None, haut=0.0):
        """marque l'empreinte orientée d'un bâtiment (et sa hauteur) dans la grille"""
        a = math.radians(cap); ca, sa = math.cos(a), math.sin(a)
        hw, hl = w / 2.0, l / 2.0
        step = self.cell / 2.0
        u = np.arange(-hw, hw + step, step)
        v = np.arange(-hl, hl + step, step)
        for uu in u:
            for vv in v:
                x = dx + uu * ca + vv * sa
                y = dy - uu * sa + vv * ca
                i, j = self.idx(x, y)
                if 0 <= i < self.N and 0 <= j < self.N:
                    g[j, i] = True
                    if h is not None and haut > h[j, i]:
                        h[j, i] = haut

    def idx(self, dx, dy):
        return int((dx + self.R) / self.cell), int((dy + self.R) / self.cell)

    def is_solid(self, dx, dy):
        i, j = self.idx(dx, dy)
        return not (0 <= i < self.N and 0 <= j < self.N) or bool(self.solid[j, i])

    def cover_at(self, dx, dy):
        """distance au bâtiment le plus proche (m). Petit = à couvert."""
        i, j = self.idx(dx, dy)
        if not (0 <= i < self.N and 0 <= j < self.N):
            return 99.0
        return float(self.dcover[j, i])

    def los(self, ax, ay, bx, by, steps=24, ha=1.7, hb=1.0):
        """Ligne de vue A->B, EN TENANT COMPTE DES HAUTEURS.
        Un muret n'aveugle pas un homme debout : on ne bloque que si le bâti DÉPASSE la ligne de visée.
        ha = hauteur d'œil du tireur (1,7 m debout), hb = hauteur de la cible (1,0 m accroupi/couché)."""
        for k in range(1, steps):
            t = k / float(steps)
            x = ax + (bx - ax) * t
            y = ay + (by - ay) * t
            i, j = self.idx(x, y)
            if not (0 <= i < self.N and 0 <= j < self.N):
                continue
            if self.h[j, i] > (ha + (hb - ha) * t):
                return False
        return True


class Agent:
    """L'état d'intention d'un soldat : ce qu'il fait, depuis quand, et vers quoi."""

    def __init__(self, i):
        self.i = i
        self.kind = None
        self.target = None          # (dx, dy) relatif à l'objectif
        self.enemy = -1
        self.t0 = 0                 # tour de départ de l'intention
        self.last_d = None          # pour détecter le blocage
        self.stuck = 0

    def set(self, kind, t, target=None, enemy=-1):
        self.kind = kind; self.target = target; self.enemy = enemy
        self.t0 = t; self.last_d = None; self.stuck = 0

    def done(self, t, pos, enemies_alive, limits):
        """L'intention est-elle ACCOMPLIE ? (c'est ça qui remplace le tour à durée fixe)"""
        age = t - self.t0
        if self.kind is None:
            return True, "aucune"
        if self.kind in (AVANCER, DECROCHER):
            if self.target is None:
                return True, "sans cible"
            d = math.hypot(pos[0] - self.target[0], pos[1] - self.target[1])
            if d < 6.0:
                return True, "arrivé"
            if self.last_d is not None and (self.last_d - d) < 0.6:
                self.stuck += 1
                if self.stuck >= 5:            # en ville on contourne : laisser le temps au trajet
                    return True, "bloqué"
            else:
                self.stuck = 0
            self.last_d = d
            if age >= limits["move"]:
                return True, "temps écoulé"
        elif self.kind == ABRITER:
            if age >= limits["cover"]:
                return True, "abri tenu"
        elif self.kind == APPUYER:
            if self.enemy >= 0 and self.enemy not in enemies_alive:
                return True, "cible neutralisée"
            if age >= limits["support"]:
                return True, "appui donné"
        return False, ""


def candidats(terr, pos, obj=(0.0, 0.0), n_dirs=8, dist=26.0, cone=None, avancer=True):
    """Les points où l'agent PEUT se porter. Calculés depuis le plan, pas depuis le jeu.
    Renvoie [(dx, dy, progression, couvert)] — les points dans un mur sont écartés."""
    px, py = pos
    d_now = math.hypot(px - obj[0], py - obj[1])
    cap_obj = math.atan2(obj[0] - px, obj[1] - py)
    out = []
    for k in range(n_dirs):
        a = 2 * math.pi * k / n_dirs
        if cone is not None:
            ecart = abs(math.atan2(math.sin(a - cap_obj), math.cos(a - cap_obj)))
            if avancer and ecart > cone:
                continue
            if not avancer and ecart < math.pi - cone:
                continue
        tx = px + math.sin(a) * dist
        ty = py + math.cos(a) * dist
        # SEULE exigence : la destination n'est pas DANS un mur. On n'exige PAS une ligne droite —
        # le jeu (doMove) sait contourner. Exiger la vue directe supprimait tous les points utiles en
        # ville et laissait l'agent sans option (bug du 25/07 : 104 gestes « bloqués » sur 225).
        if terr.is_solid(tx, ty):
            # on récupère le point libre le plus proche sur le même axe (le mur n'annule pas la direction)
            trouve = False
            for frac in (0.75, 0.5, 1.25):
                cx2 = px + math.sin(a) * dist * frac
                cy2 = py + math.cos(a) * dist * frac
                if not terr.is_solid(cx2, cy2):
                    tx, ty = cx2, cy2; trouve = True; break
            if not trouve:
                continue
        prog = d_now - math.hypot(tx - obj[0], ty - obj[1])
        out.append((tx, ty, prog, terr.cover_at(tx, ty)))
    return out


def expo(terr, pt, ennemis):
    """Combien d'ennemis VOIENT ce point (à travers le plan). Sert à préférer les routes masquées."""
    n = 0
    for (ex, ey) in ennemis:
        if terr.los(pt[0], pt[1], ex, ey, steps=20):
            n += 1
    return n


# ============================ PROF SCRIPTÉ (étage 1) =====================================
# Règles simples et LISIBLES. But : valider la mécanique (des gestes qui aboutissent),
# pas gagner. L'apprentissage viendra remplacer ce prof — c'est le rôle du warm-start.

def prof(ag, pos, obj, terr, ennemis, sous_le_feu, allies_pos, degats, cfg):
    """Choisit l'intention suivante d'un agent dont le geste précédent est ACCOMPLI."""
    d_obj = math.hypot(pos[0] - obj[0], pos[1] - obj[1])

    # 1. trop abîmé -> décrocher vers l'arrière, à couvert
    if degats > cfg["degats_repli"]:
        cand = candidats(terr, pos, obj, dist=cfg["bond"], cone=math.pi / 2, avancer=False)
        if cand:
            best = min(cand, key=lambda c: (expo(terr, (c[0], c[1]), ennemis), c[3]))
            return DECROCHER, (best[0], best[1]), -1

    # 2. sous le feu à découvert -> se plaquer (un temps court, pas un enracinement)
    if sous_le_feu and terr.cover_at(pos[0], pos[1]) > cfg["couvert_ok"]:
        return ABRITER, None, -1

    # 3. un ennemi ENGAGEABLE et un camarade plus avancé que moi -> je l'APPUIE
    # engageable = vue dégagée sur le plan OU assez proche pour un tir de suppression (la vue 2D est
    # trop pessimiste en ville : elle voyait un mur partout et l'appui ne se déclenchait jamais).
    vus = []
    for k, e in enumerate(ennemis):
        de = math.hypot(pos[0] - e[0], pos[1] - e[1])
        if de < cfg["portee_appui"] and (de < cfg["appui_proche"] or terr.los(pos[0], pos[1], e[0], e[1])):
            vus.append((k, e))
    if vus:
        plus_avances = sum(1 for a in allies_pos
                           if a is not None and math.hypot(a[0] - obj[0], a[1] - obj[1]) < d_obj - 5)
        if plus_avances >= 1:
            k, _ = min(vus, key=lambda ke: math.hypot(ke[1][0] - pos[0], ke[1][1] - pos[1]))
            return APPUYER, None, k

    # 4. sinon : AVANCER vers le meilleur candidat (progresser, en restant masqué)
    cand = candidats(terr, pos, obj, dist=cfg["bond"], cone=cfg["cone"], avancer=True)
    if not cand:
        cand = candidats(terr, pos, obj, dist=cfg["bond"] * 0.6)
    if cand:
        def note(c):
            e = expo(terr, (c[0], c[1]), ennemis)
            return (-c[2] * cfg["w_prog"]) + (e * cfg["w_expo"]) + (min(c[3], 30) * cfg["w_couvert"])
        best = min(cand, key=note)
        return AVANCER, (best[0], best[1]), -1
    return ABRITER, None, -1


CFG = dict(bond=26.0, cone=math.pi / 2, w_prog=1.0, w_expo=6.0, w_couvert=0.25,
           couvert_ok=12.0, degats_repli=0.55, portee_appui=200.0, appui_proche=90.0)
LIMITES = dict(move=9, cover=3, support=5)   # en TOURS de contrôle
