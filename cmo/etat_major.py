"""L'ÉTAT-MAJOR d'un camp : il applique la doctrine ( doctrine.py ) à la guerre réelle ( guerre_reelle.py ) et apprend de
ses résultats. Younes, 02/10 : « c'est ça qu'il faut que le moteur apprenne […] SEAD, strike, DEAD, tout ; mets-toi en
mode chef d'état-major ».

À chaque tour, pour chaque camp :
  1. SITUATION : la base aérienne adverse à frapper ( la plus proche encore opérationnelle ) ; les PARAPLUIES sol-air
     adverses vivants ( unités et éléments d'installations, portée air réelle de la DB3000 ) qui la couvrent ou couvrent la
     route ( portée >= doctrine.PORTEE_MENACE_KM ).
  2. DÉCISION : parapluie intact -> mission DEAD contre lui ( avions armés d'armes à distance de sécurité, d'antiradars
     ou d'armes furtives ; lanceurs sol-sol À PORTÉE ) ; les frappeurs ordinaires attendent. Ciel ouvert -> frappe OCA de la
     base ( frappeurs + lanceurs à portée ). Chaque frappe reçoit une ESCORTE de chasseurs, prise sur les bases les mieux
     défendues ( au moins une paire reste sur chaque base ).
  3. RÔLES : un avion de frappe AU SOL peut être réarmé en avion DEAD ( ScenEdit_SetLoadout par son nom ; le dépôt est
     rempli d'abord, au prix réel : sans arme en stock, CMO le laisse sans armement, sonde du 02/10 ).
  4. APPRENTISSAGE : chaque mission est notée à sa clôture : dégâts infligés à ses cibles / ( avions perdus + 1 ). La part
     d'avions réarmés en DEAD suit l'efficacité comparée des missions DEAD et OCA ( poids multiplicatifs, bornés ).

CHOIX À VALIDER PAR YOUNES : les seuils ( PART_DEAD initiale et bornes, taille d'escorte, marge de parapluie ).
"""
import math

import doctrine as DOC

PART_DEAD_DEPART, PART_DEAD_MIN, PART_DEAD_MAX = 0.5, 0.2, 0.8
CLASSIF_MIN = 2                                           # brouillard : un contact « type connu » au moins pour savoir que c'est un SAM
APPRENTISSAGE = 0.3                                       # pas des poids multiplicatifs
ESCORTE_PAR_FRAPPEURS = 4                                 # une paire d'escorte par 4 frappeurs, au plus ESCORTE_MAX
ESCORTE_MAX = 8
MARGE_KM = 10.0
DEC_DEAD = 2000                                           # missions DEAD : 2 000 + camp x 100 + k ( les OCA : 1 000 + … )

# LA COMPOSANTE AIR ( 03/10 ) : rôle -> ( décalage d'id, genre de mission CMO 1 AAW / 2 SEAD / 3 soutien, part de la route
# depuis nos avions vers la cible, marge aux parapluies connus km, marge aux bases adverses km, demi-zone km, emcon ).
# Le guet radar orbite au tiers de la route, hors de portée des SAM connus ; le ravitailleur plus en arrière ; le brouilleur
# en stand-off, juste hors de portée des défenses qui couvrent la cible ; la SEAD sur les défenses de la cible ; la barrière
# de chasse à mi-route ( CHOIX À VALIDER : parts et marges ).
ZONE_BASE = 500
SOUTIEN = {
    "guet": (0, 3, 0.35, 60.0, 150.0, 25.0, 1),
    "ravitailleur": (1, 3, 0.15, 100.0, 250.0, 30.0, 0),
    "brouilleur": (2, 3, None, 15.0, 60.0, 15.0, 2),
    "sead": (3, 2, None, None, None, 40.0, 0),
    "barriere": (4, 1, 0.5, 20.0, 80.0, 50.0, 0),
}
DEPLACEMENT_KM = 10.0                                     # une zone n'est redessinée que si elle bouge de plus


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


class EtatMajor:
    def __init__(self, g, *, portee_air=None, portee_sol=None, charg_mission=None):
        self.g = g
        self.portee_air = portee_air or DOC.portee_sol_air
        self.portee_sol = portee_sol or DOC.portee_sol_sol
        self.charg_mission = charg_mission or DOC.chargement
        self._cache, self._charg = {}, {}
        self.part_dead = {c: PART_DEAD_DEPART for c in g.camps}
        self.efficacite = {c: {"dead": 1.0, "oca": 1.0} for c in g.camps}
        self.missions = {}                               # id -> { type, camp, cibles, avions, t0, degats0, pertes, ouverte }
        self.k = {c: 0 for c in g.camps}
        self.journal = []                                # décisions et notes, pour l'agent et pour Younes
        self.a_clore = []                                # ( camp, id ) des frappes à fermer dans CMO à ce tour
        self.zones = {}                                  # id de zone -> ( lat, lon ) envoyée à CMO

    # ---- mémoire des portées ( la DB est lente : une lecture par type )
    def _p(self, quoi, dbid):
        cle = (quoi, dbid)
        if cle not in self._cache:
            self._cache[cle] = {"air": self.portee_air, "sol": self.portee_sol}[quoi](dbid) if dbid else 0.0
        return self._cache[cle]

    def _cm(self, dbid, mission):
        if (dbid, mission) not in self._charg:
            self._charg[(dbid, mission)] = self.charg_mission(dbid, mission)
        return self._charg[(dbid, mission)]

    # ---- 1. la situation
    def parapluies(self, camp):
        """[ ( numéro, position, portée air km ) ] des défenses sol-air adverses VIVANTES à longue portée."""
        out = []
        for k, s in self.g.sol.items():
            if s["camp"] != camp and self._p("air", s["dbid"]) >= DOC.PORTEE_MENACE_KM and self._connu(camp, k):
                out.append((k, self._vu_ou(camp, k, s["pos"]), self._p("air", s["dbid"])))
        for k, e in self.g.elements.items():
            if e["camp"] != camp and e["vivant"] and e["classe"] in ("sol-air", "radar") and self._p("air", e["dbid"]) >= DOC.PORTEE_MENACE_KM:
                out.append((k, e["pos"], self._p("air", e["dbid"])))
        return out

    def _connu(self, camp, k):
        """Brouillard de guerre : une unité mobile adverse n'existe pour l'état-major que si son camp la voit dans CMO,
        classée au moins « type connu » ( sinon il ne sait pas que c'est une défense sol-air )."""
        if not self.g.brouillard:
            return True
        v = self.g.vus.get(camp, {}).get(k)
        return v is not None and v[0] >= CLASSIF_MIN

    def _vu_ou(self, camp, k, vrai):
        """La position que le camp CROIT : celle du contact, à défaut la vraie."""
        v = self.g.vus.get(camp, {}).get(k) if self.g.brouillard else None
        return (v[2], v[3]) if v and (v[2] or v[3]) else vrai

    def _centre(self, camp, combat=True):
        """Le centre de gravité des avions de combat du camp ( leurs bases, pondérées ) : les bases lointaines des avions de
        soutien ( Mildenhall, Ivanovo ) ne tirent pas le front vers l'arrière. À défaut, le centre de ses bases."""
        g, n = self.g, {}
        for a in g.avions.values():
            if a["camp"] == camp and (not combat or a["role"] in ("aa", "frappe", "dead")) and a["base"] in g.bases:
                n[a["base"]] = n.get(a["base"], 0) + 1
        pts = [(g.bases[i]["pos"], w) for i, w in n.items() if g.bases[i]["pos"]] or \
              [(b["pos"], 1) for b in g.bases.values() if b["camp"] == camp and b["pos"]]
        if not pts:
            return None
        s = sum(w for _, w in pts)
        return (sum(p[0] * w for p, w in pts) / s, sum(p[1] * w for p, w in pts) / s)

    def couvrent(self, camp, cible_pos):
        """Les parapluies adverses qui couvrent la cible, ou le milieu de la route depuis nos avions de combat."""
        centre = self._centre(camp)
        if centre is None:
            return []
        milieu = ((centre[0] + cible_pos[0]) / 2, (centre[1] + cible_pos[1]) / 2)
        return [(k, pos, r) for k, pos, r in self.parapluies(camp)
                if km(pos, cible_pos) <= r + MARGE_KM or km(pos, milieu) <= r + MARGE_KM]

    # ---- 2. la décision et les ordres : rend ( frappes, affectations, escortes, réarmements ) pour le labo
    def planifier(self, ci, camp):
        g = self.g
        cible = g._choisir_cible(camp)
        decision = {"camp": camp, "tour": g.tours, "cible": g.bases[cible]["fichier"] if cible is not None else None}
        frappes, affect, escortes, rearmes = [], [], [], []
        if cible is None:
            decision["ordre"] = "aucune cible"
            self._fermer(camp)
            g.frappe[camp] = None
            self.journal.append(decision)
            return frappes, affect, escortes, rearmes
        menaces = self.couvrent(camp, g.bases[cible]["pos"])
        if menaces:
            typ, cibles = "dead", sorted(k for k, _, _ in menaces)
            roles = ("dead",)
        else:
            b = g.bases[cible]
            typ, cibles = "oca", [k for k in b["pistes"] + b["acces"] + b["depots"] if g.elements[k]["vivant"]]
            roles = ("frappe", "dead")                   # ciel ouvert : les avions DEAD frappent aussi la base
        mid = self._mission(ci, camp, typ, cibles, frappes)
        g.frappe[camp] = {"id": mid, "base": cible, "cibles": cibles, "type": typ}
        decision.update(ordre=typ, mission=mid, cibles=len(cibles), parapluies=len(menaces))
        # les frappeurs du bon rôle, par paires, et les lanceurs dont une cible est à portée
        libres = sorted(k for k, a in g.avions.items() if a["camp"] == camp and a["role"] in roles and g.affecte.get(k) != mid)
        libres = libres[:len(libres) // 2 * 2]
        positions = [self._position(k) for k in cibles]
        lanceurs = sorted(k for k, s in g.sol.items() if s["camp"] == camp and g.affecte.get(k) not in (mid, -1)
                          and s["dbid"] in getattr(g.T, "LANCEURS", set())
                          and any(p and km(s["pos"], p) <= self._p("sol", s["dbid"]) for p in positions))
        if libres or lanceurs:
            affect.append((mid, libres + lanceurs))
        # l'escorte : une paire par ESCORTE_PAR_FRAPPEURS frappeurs, prise là où il y a le plus de chasseurs
        avions_mid = [k for k, m in g.affecte.items() if m == mid and k in g.avions]   # un lanceur au sol ne s'escorte pas
        n_esc = min(ESCORTE_MAX, 2 * math.ceil(len(avions_mid + libres) / ESCORTE_PAR_FRAPPEURS))
        deja = [k for k, m in g.affecte.items() if m == -mid]
        if n_esc > len(deja):
            escortes.append((mid, self._escorteurs(camp, n_esc - len(deja))))
        # les réarmements : des frappeurs au sol deviennent DEAD tant que la part voulue n'est pas atteinte ; ceux qui n'ont
        # pas d'arme à distance passent en chasse pendant la DEAD et reviennent à la frappe quand le ciel est ouvert
        rearmes = (self._rearmer(camp) + self._basculer(camp, "aa")) if typ == "dead" else self._basculer(camp, "frappe")
        decision["engages"] = len(libres) + len(lanceurs)
        self.journal.append(decision)
        return frappes, affect, escortes, rearmes

    def _position(self, k):
        if k in self.g.elements:
            return self.g.elements[k]["pos"]
        if k in self.g.sol:
            return self.g.sol[k]["pos"]
        return None

    def _mission(self, ci, camp, typ, cibles, frappes):
        """La mission ouverte de ce type pour le camp, gardée tant que ses cibles sont les mêmes ; sinon clôture, notation
        et ouverture d'une nouvelle."""
        g = self.g
        ouverte = next((m for m in self.missions.values() if m["camp"] == camp and m["type"] == typ and m["ouverte"]), None)
        if ouverte and set(ouverte["cibles"]) == set(cibles):
            return ouverte["id"]
        self._fermer(camp)
        self.k[camp] += 1
        base = DEC_DEAD if typ == "dead" else 1000
        mid = base + ci * 100 + self.k[camp] % 100
        self.missions[mid] = {"id": mid, "type": typ, "camp": camp, "cibles": list(cibles), "ouverte": True,
                              "t0": g.tours, "degats0": {k: self._degats(k) for k in cibles}, "avions": set(), "pertes": 0}
        frappes.append((mid, camp, list(cibles)))
        return mid

    def _fermer(self, camp):
        """Clôture ( notée ) des missions ouvertes du camp, et de la frappe d'avant l'état-major ( reprise d'une guerre ) :
        CMO les efface ( HMT_clore ), leurs avions et lanceurs redeviennent libres."""
        g = self.g
        fermees = [m["id"] for m in self.missions.values() if m["camp"] == camp and m["ouverte"]]
        for i in fermees:
            self._clore(self.missions[i])
        anc = (g.frappe.get(camp) or {}).get("id")
        if anc and anc not in self.missions:
            fermees.append(anc)
        self.a_clore += [(camp, i) for i in fermees]
        for k, m in list(g.affecte.items()):
            if abs(m) in fermees:
                del g.affecte[k]

    def _degats(self, k):
        if k in self.g.elements:
            e = self.g.elements[k]
            return 100.0 if not e["vivant"] else e["degats"]
        return 0.0 if k in self.g.sol else 100.0          # une unité au sol disparue est détruite

    def _escorteurs(self, camp, n):
        g = self.g
        par_base = {}
        for k, a in g.avions.items():
            if a["camp"] == camp and a["role"] == "aa" and not (g.affecte.get(k, 0) and abs(g.affecte[k]) >= 1000):
                par_base.setdefault(a["base"], []).append(k)
        choix = []
        for base, ks in sorted(par_base.items(), key=lambda x: -len(x[1])):
            dispo = sorted(ks)[: max(0, len(ks) - 2)]        # au moins une paire reste défendre la base
            choix += dispo[: n - len(choix)]
            if len(choix) >= n:
                break
        return choix[: len(choix) // 2 * 2]

    def _basculer(self, camp, vers):
        """[ ( numéro, chargement, rôle ) ] des avions posés et libres qui changent de rôle ( swing-role ) : vers « aa »,
        les frappeurs sans chargement DEAD ; vers « frappe », ceux qui avaient basculé."""
        g, out = self.g, []
        for k, a in sorted(g.avions.items()):
            m = g.affecte.get(k, 0)
            if a["camp"] != camp or g.altitudes.get(k, 0) > 500 or abs(m) >= 1000:
                continue
            ch = g.charg.get(a["dbid"], {})
            if vers == "aa" and a["role"] == "frappe" and not self._cm(a["dbid"], "dead") and ch.get("aa"):
                out.append((k, ch["aa"], "aa"))
            elif vers == "frappe" and a["role"] == "aa" and a.get("bascule") == "frappe" and ch.get("frappe"):
                out.append((k, ch["frappe"], "frappe"))
        return out

    def _rearmer(self, camp):
        """[ ( numéro, nouveau chargement, « dead » ) ] : des frappeurs posés deviennent DEAD jusqu'à la part voulue."""
        g = self.g
        frappe = [k for k, a in g.avions.items() if a["camp"] == camp and a["role"] in ("frappe", "dead")]
        dead = [k for k in frappe if g.avions[k]["role"] == "dead"]
        voulus = int(len(frappe) * self.part_dead[camp]) // 2 * 2
        out = []
        for k in sorted(frappe):
            if len(dead) + len(out) >= voulus:
                break
            a = g.avions[k]
            if a["role"] != "frappe" or g.altitudes.get(k, 0) > 500:
                continue
            lo = self._cm(a["dbid"], "dead")
            if lo:
                out.append((k, lo, "dead"))
        return out

    # ---- 2 bis. la composante air : guet, ravitaillement, brouillage, SEAD, barrière
    def _recul(self, camp, C, T, t, marge, marge_b):
        """Le point de la route C -> T à la part t, reculé vers C jusqu'à être à `marge` km hors de portée de chaque
        parapluie adverse CONNU et à `marge_b` km de chaque base adverse opérationnelle."""
        menaces = self.parapluies(camp)
        bases = [b["pos"] for b in self.g.bases.values() if b["camp"] != camp and b["op"] and b["pos"]]
        tt = t
        while tt > 0:
            P = (C[0] + tt * (T[0] - C[0]), C[1] + tt * (T[1] - C[1]))
            if all(km(P, pos) >= r + marge for _, pos, r in menaces) and all(km(P, b) >= marge_b for b in bases):
                return P
            tt = round(tt - 0.05, 4)
        return C

    def _barriere(self, camp, zid):
        """La barrière de chasse : à chaque base, au-delà de la paire qui la défend, la moitié des chasseurs ( par paires )
        part en barrière avancée. Ceux qui y sont y restent ( pas de valse ) ; les escortes passent avant."""
        g, par_base = self.g, {}
        for k, a in sorted(g.avions.items()):
            m = g.affecte.get(k, 0)
            if a["camp"] == camp and a["role"] == "aa" and abs(m) < 1000:
                par_base.setdefault(a["base"], []).append(k)
        out = []
        for base, ks in par_base.items():
            voulus = (max(0, len(ks) - 2) // 2) // 2 * 2
            deja = [k for k in ks if g.affecte.get(k) == zid]
            libres = [k for k in ks if g.affecte.get(k) != zid]
            out += deja[:voulus] + libres[:max(0, voulus - len(deja))]
        return out

    def soutiens(self, ci, camp):
        """( zones, affectations ) des missions de la composante air du camp, pour labo.zones."""
        g = self.g
        C = self._centre(camp)
        fr = g.frappe.get(camp)
        T = g.bases[fr["base"]]["pos"] if fr and fr.get("base") in g.bases else self._centre_adverse(camp)
        if C is None or T is None:
            return [], []
        zones, affect = [], []
        for role, (dec, genre, t0, marge, marge_b, demi, emcon) in SOUTIEN.items():
            zid = ZONE_BASE + ci * 10 + dec
            if role == "barriere":
                ks = self._barriere(camp, zid)
            else:
                ks = [k for k, a in sorted(g.avions.items()) if a["camp"] == camp and a["role"] == role]
            if not ks or (role in ("sead", "brouilleur") and not fr):
                continue
            if role == "sead":
                cov = self.couvrent(camp, T)
                P = (sum(p[0] for _, p, _ in cov) / len(cov), sum(p[1] for _, p, _ in cov) / len(cov)) if cov else T
            elif role == "brouilleur":
                r = max((x[2] for x in self.couvrent(camp, T)), default=40.0)
                d = km(C, T)
                P = self._recul(camp, C, T, max(0.0, 1 - (r + 30.0) / d) if d > 0 else 0.0, marge, marge_b)
            else:
                P = self._recul(camp, C, T, t0, marge, marge_b)
            sur_place = {"guet": 1, "ravitailleur": 2 if len(ks) >= 4 else 1, "brouilleur": 1}.get(role, 0)
            ancien = self.zones.get(zid)
            if ancien is None or km(ancien, P) > DEPLACEMENT_KM:
                zones.append((zid, camp, genre, P[0], P[1], demi, 1, sur_place, emcon))
                self.zones[zid] = P
            nouveaux = [k for k in ks if g.affecte.get(k) != zid]
            if genre in (1, 2):                              # une patrouille ne part que par vols de deux, de la même base
                par_base = {}
                for k in nouveaux:
                    par_base.setdefault(g.avions[k]["base"], []).append(k)
                nouveaux = [k for v in par_base.values() for k in v[:len(v) // 2 * 2]]
            if nouveaux:
                affect.append((zid, nouveaux))
        return zones, affect

    def _centre_adverse(self, camp):
        pts = [b["pos"] for b in self.g.bases.values() if b["camp"] != camp and b["op"] and b["pos"]]
        if not pts:
            return None
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    # ---- 3. l'apprentissage
    def suivre(self, morts):
        """Chaque tour : les avions morts sont comptés contre la mission qui les employait."""
        for k in morts:
            m = self.missions.get(abs(self.g.affecte_avant.get(k, 0)))
            if m and m["ouverte"]:
                m["pertes"] += 1
        for k, mid in self.g.affecte.items():
            if abs(mid) in self.missions:
                self.missions[abs(mid)]["avions"].add(k)

    def _clore(self, m):
        m["ouverte"] = False
        degats = sum(max(0.0, self._degats(k) - d0) for k, d0 in m["degats0"].items())
        m["degats"], m["efficacite"] = degats, degats / (m["pertes"] + 1)
        c = m["camp"]
        e = self.efficacite[c]
        e[m["type"]] = (1 - APPRENTISSAGE) * e[m["type"]] + APPRENTISSAGE * (m["efficacite"] + 1e-3)
        # la part DEAD suit le rapport des efficacités ( poids multiplicatifs bornés )
        r = e["dead"] / (e["dead"] + e["oca"])
        self.part_dead[c] = min(PART_DEAD_MAX, max(PART_DEAD_MIN, (1 - APPRENTISSAGE) * self.part_dead[c] + APPRENTISSAGE * r))
        self.journal.append({"camp": c, "tour": self.g.tours, "cloture": m["id"], "type": m["type"], "degats": round(degats, 1),
                             "pertes": m["pertes"], "efficacite": round(m["efficacite"], 2), "part_dead": round(self.part_dead[c], 2)})

    def etat(self):
        return {"part_dead": self.part_dead, "efficacite": self.efficacite, "k": self.k,
                "zones": {str(i): list(p) for i, p in self.zones.items()},
                "missions": {str(i): dict(m, avions=sorted(m["avions"])) for i, m in self.missions.items()},
                "journal": self.journal[-200:]}

    def charger(self, e):
        self.part_dead, self.efficacite, self.k = e["part_dead"], e["efficacite"], e["k"]
        self.missions = {int(i): dict(m, avions=set(m["avions"]), degats0={int(k): v for k, v in m["degats0"].items()})
                         for i, m in e["missions"].items()}
        self.journal = e.get("journal", [])
        self.zones = {int(i): tuple(p) for i, p in (e.get("zones") or {}).items()}
