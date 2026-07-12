"""memory_system — LE SYSTÈME DE MÉMOIRES du soldat incarné (HARMATTAN, étape 1bis).
La mémoire n'est pas UN réseau mais un SYSTÈME : sept mémoires distinctes, à des échelles de temps et des
supports différents, comme le cerveau humain. Chaque classe est une mémoire ; MemorySystem les relie.

  1 Sensorielle   : tampon brut des derniers instants perçus            (ring buffer)
  2 De travail    : l'état mental courant, ce qu'on gère maintenant      (état caché récurrent / résumé)
  3 Épisodique    : les contacts VÉCUS — où, quand, dans quel état       (registre à cases, décroissant)
  4 Sémantique    : la connaissance générale / doctrine                 (base de règles + priors)
  5 Procédurale   : les savoir-faire — comment exécuter une action      (réflexes appris -> commandes)
  6 Spatiale      : la carte mentale du terrain (danger, visité, but)   (grille d'occupation)
  7 Prospective   : les intentions différées (le plan)                  (file de tâches)
"""
import math, collections
import numpy as np


# ───────────────────────── 1. MÉMOIRE SENSORIELLE ─────────────────────────
class SensoryMemory:
    """Tampon ultra-court : les K derniers vecteurs de perception bruts (le 'dernier coup d'œil')."""
    def __init__(self, dim, k=4):
        self.k = k; self.dim = dim
        self.buf = collections.deque([np.zeros(dim, np.float32)] * k, maxlen=k)

    def update(self, obs):
        self.buf.append(np.asarray(obs, np.float32))

    def last(self):
        return self.buf[-1]

    def velocity(self):
        """variation entre les deux derniers instants — le mouvement apparent (déjà une trace temporelle)."""
        return self.buf[-1] - self.buf[-2]


# ───────────────────────── 2. MÉMOIRE DE TRAVAIL ─────────────────────────
class WorkingMemory:
    """Ce qu'on gère MAINTENANT. Support : l'état caché récurrent (h) du cerveau GRU, persistant d'un pas à
    l'autre. On le garde ici pour le réinitialiser proprement (mort, désengagement)."""
    def __init__(self):
        self.h = None
        self.focus = None          # cible/objet d'attention courant (id de contact)

    def reset(self):
        self.h = None; self.focus = None


# ───────────────────────── 3. MÉMOIRE ÉPISODIQUE ─────────────────────────
class EpisodicMemory:
    """Les ÉVÉNEMENTS vécus : 'j'ai vu le contact #2 à (x,y) il y a 30 s'. Registre à cases, mis à jour quand on
    voit, INTERROGEABLE même hors de vue, et qui s'efface lentement (confiance décroissante). C'est CETTE mémoire
    qui permet de 'ne pas perdre un contact' — pas l'état récurrent."""
    def __init__(self, tau=18.0):        # tau = constante d'oubli (secondes)
        self.tau = tau
        self.slots = {}                  # id -> dict(x,y,t_last,conf,dmg,seen_count)

    def observe(self, contacts, t):
        """contacts : liste de (id, x, y, dmg, visible). On rafraîchit ce qu'on VOIT."""
        for cid, x, y, dmg, vis in contacts:
            if vis:
                s = self.slots.get(cid, {"seen_count": 0})
                s.update(x=x, y=y, t_last=t, conf=1.0, dmg=dmg, seen_count=s["seen_count"] + 1)
                self.slots[cid] = s

    def recall(self, now, conf_min=0.15):
        """Ce dont on se SOUVIENT (confiance décrue par l'oubli), même si on ne voit plus rien."""
        out = []
        for cid, s in self.slots.items():
            conf = math.exp(-(now - s["t_last"]) / self.tau)
            if conf >= conf_min and s["dmg"] < 70:
                out.append({"id": cid, "x": s["x"], "y": s["y"], "conf": conf, "age": now - s["t_last"], "dmg": s["dmg"]})
        return out

    def nearest(self, now, px, py, conf_min=0.15):
        r = self.recall(now, conf_min)
        if not r:
            return None
        return min(r, key=lambda s: (s["x"] - px) ** 2 + (s["y"] - py) ** 2)


# ───────────────────────── 4. MÉMOIRE SÉMANTIQUE ─────────────────────────
class SemanticMemory:
    """La connaissance GÉNÉRALE, intemporelle : doctrine, seuils, priors sur le monde. Ne change pas d'un pas à
    l'autre (≈ les 'faits' que le soldat sait par formation)."""
    def __init__(self):
        self.facts = {
            "portee_vue_m": 110.0,
            "rayon_tenue_objectif_m": 15.0,
            "seuil_suppression_couvert": 0.6,
            "seuil_engagement_sup": 0.3,
            "vitesse_jog_ms": 2.5,
        }
        self.doctrine = {
            "sous_le_feu_lourd": "se couvrir puis riposter",
            "ennemi_vu_a_couvert": "suppresser pour fixer",
            "voie_libre": "bondir vers l'objectif",
            "objectif_atteint": "tenir et consolider",
        }

    def get(self, k):
        return self.facts.get(k)

    def regle(self, situation):
        return self.doctrine.get(situation, "tenir")


# ───────────────────────── 5. MÉMOIRE PROCÉDURALE ─────────────────────────
class ProceduralMemory:
    """Les SAVOIR-FAIRE : comment EXÉCUTER chaque action (le 'comment', appris, sans y penser). Ici, la traduction
    d'une décision tactique en commandes concrètes pour le corps. C'est l'analogue des réflexes moteurs."""
    ACTIONS = ["TENIR", "AVANCER", "SUPPRESSER", "COUVERT"]

    def commande(self, unit, action, objectif, cible):
        gx, gy = objectif
        if action == 1:                                   # AVANCER
            return 'private _u = %s; _u setUnitPos "AUTO"; _u doMove [%d, %d, 0];' % (unit, gx, gy)
        if action == 2 and cible is not None:             # SUPPRESSER (vers la cible mémorisée/vue)
            cx, cy = cible
            return 'private _u = %s; doStop _u; _u setUnitPos "MIDDLE"; _u doWatch [%d,%d,0]; _u doSuppressiveFire [%d, %d, 1];' % (unit, cx, cy, cx, cy)
        if action == 3:                                   # COUVERT
            return 'private _u = %s; doStop _u; _u setUnitPos "DOWN";' % unit
        return 'private _u = %s; doStop _u;' % unit       # TENIR


# ───────────────────────── 6. MÉMOIRE SPATIALE ─────────────────────────
class SpatialMemory:
    """La CARTE MENTALE : une grille grossière du terrain autour de l'objectif. Chaque cellule retient le DANGER
    (un contact y a été vu) et le VISITÉ. Donne 'd'où vient la menace' même les yeux fermés."""
    def __init__(self, center, half_span=160.0, n=16):
        self.cx, self.cy = center; self.half = half_span; self.n = n
        self.danger = np.zeros((n, n), np.float32)
        self.visited = np.zeros((n, n), np.float32)

    def _cell(self, x, y):
        i = int((x - self.cx + self.half) / (2 * self.half) * self.n)
        j = int((y - self.cy + self.half) / (2 * self.half) * self.n)
        return min(max(i, 0), self.n - 1), min(max(j, 0), self.n - 1)

    def update(self, self_pos, recalled_contacts):
        i, j = self._cell(*self_pos); self.visited[i, j] = 1.0
        self.danger *= 0.985                                          # le danger s'estompe lentement
        for c in recalled_contacts:
            i, j = self._cell(c["x"], c["y"]); self.danger[i, j] = max(self.danger[i, j], c["conf"])

    def danger_total(self):
        return float(self.danger.sum())


# ───────────────────────── 7. MÉMOIRE PROSPECTIVE ─────────────────────────
class ProspectiveMemory:
    """Les INTENTIONS DIFFÉRÉES : le plan, ce qu'on a l'intention de faire ensuite. File de tâches que l'on
    avance quand l'étape courante est satisfaite (≈ 'se souvenir de faire X au point Y')."""
    def __init__(self, plan):
        self.plan = collections.deque(plan)               # ex: [("rejoindre", obj), ("tenir", obj)]

    def courant(self):
        return self.plan[0] if self.plan else None

    def avancer_si(self, satisfait):
        if satisfait and len(self.plan) > 1:
            self.plan.popleft()
        return self.courant()


# ───────────────────────── LE SYSTÈME ─────────────────────────
class MemorySystem:
    """Relie les sept mémoires. À chaque pas : update(perception) les nourrit ; le cerveau interroge l'ensemble."""
    def __init__(self, obs_dim, objectif, plan):
        self.sensorielle = SensoryMemory(obs_dim)
        self.travail = WorkingMemory()
        self.episodique = EpisodicMemory()
        self.semantique = SemanticMemory()
        self.procedurale = ProceduralMemory()
        self.spatiale = SpatialMemory(objectif)
        self.prospective = ProspectiveMemory(plan)
        self.objectif = objectif

    def update(self, obs_vec, self_pos, contacts, t):
        self.sensorielle.update(obs_vec)
        self.episodique.observe(contacts, t)
        rec = self.episodique.recall(t)
        self.spatiale.update(self_pos, rec)
        return rec

    def etat(self, now, px, py):
        """Petit résumé interrogeable de l'état mémoriel courant (pour le log / la décision)."""
        rec = self.episodique.recall(now)
        vus = [c for c in rec if c["age"] < 0.5]
        return {
            "contacts_connus": len(rec),
            "contacts_vus": len(vus),
            "contacts_de_memoire": len(rec) - len(vus),
            "danger_spatial": round(self.spatiale.danger_total(), 2),
            "intention": self.prospective.courant(),
            "nearest": self.episodique.nearest(now, px, py),
        }
