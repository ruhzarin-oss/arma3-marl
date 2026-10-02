"""L'ÉTAT-MAJOR d'un camp : il applique la doctrine ( doctrine.py ) à la guerre réelle ( guerre_reelle.py ) et apprend de
ses résultats. Younes, 02/10 : « c'est ça qu'il faut que le moteur apprenne […] SEAD, strike, DEAD, tout ; mets-toi en
mode chef d'état-major ».

À chaque tour, pour chaque camp :
  1. SITUATION : la base aérienne adverse à frapper ( la plus proche encore opérationnelle ) ; les PARAPLUIES sol-air
     adverses vivants ( unités et éléments d'installations, portée air réelle de la DB3000 ) qui la couvrent ou couvrent la
     route ( portée >= doctrine.PORTEE_LONGUE_KM ).
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
APPRENTISSAGE = 0.3                                       # pas des poids multiplicatifs
ESCORTE_PAR_FRAPPEURS = 4                                 # une paire d'escorte par 4 frappeurs, au plus ESCORTE_MAX
ESCORTE_MAX = 8
MARGE_KM = 10.0
DEC_DEAD = 2000                                           # missions DEAD : 2 000 + camp x 100 + k ( les OCA : 1 000 + … )


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
        self._cache = {}
        self.part_dead = {c: PART_DEAD_DEPART for c in g.camps}
        self.efficacite = {c: {"dead": 1.0, "oca": 1.0} for c in g.camps}
        self.missions = {}                               # id -> { type, camp, cibles, avions, t0, degats0, pertes, ouverte }
        self.k = {c: 0 for c in g.camps}
        self.journal = []                                # décisions et notes, pour l'agent et pour Younes
        self.a_clore = []                                # ( camp, id ) des frappes à fermer dans CMO à ce tour

    # ---- mémoire des portées ( la DB est lente : une lecture par type )
    def _p(self, quoi, dbid):
        cle = (quoi, dbid)
        if cle not in self._cache:
            self._cache[cle] = {"air": self.portee_air, "sol": self.portee_sol}[quoi](dbid) if dbid else 0.0
        return self._cache[cle]

    # ---- 1. la situation
    def parapluies(self, camp):
        """[ ( numéro, position, portée air km ) ] des défenses sol-air adverses VIVANTES à longue portée."""
        out = []
        for k, s in self.g.sol.items():
            if s["camp"] != camp and self._p("air", s["dbid"]) >= DOC.PORTEE_LONGUE_KM:
                out.append((k, s["pos"], self._p("air", s["dbid"])))
        for k, e in self.g.elements.items():
            if e["camp"] != camp and e["vivant"] and e["classe"] in ("sol-air", "radar") and self._p("air", e["dbid"]) >= DOC.PORTEE_LONGUE_KM:
                out.append((k, e["pos"], self._p("air", e["dbid"])))
        return out

    def couvrent(self, camp, cible_pos):
        """Les parapluies adverses qui couvrent la cible, ou le milieu de la route depuis les bases du camp."""
        miennes = [b["pos"] for b in self.g.bases.values() if b["camp"] == camp]
        if not miennes:
            return []
        centre = (sum(p[0] for p in miennes) / len(miennes), sum(p[1] for p in miennes) / len(miennes))
        milieu = ((centre[0] + cible_pos[0]) / 2, (centre[1] + cible_pos[1]) / 2)
        return [(k, pos, r) for k, pos, r in self.parapluies(camp)
                if km(pos, cible_pos) <= r + MARGE_KM or km(pos, milieu) <= r + MARGE_KM]

    # ---- 2. la décision et les ordres : rend ( frappes, affectations, escortes, réarmements ) pour le labo
    def planifier(self, ci, camp):
        g = self.g
        cible = g._choisir_cible(camp)
        decision = {"camp": camp, "tour": g.tours, "cible": cible and g.bases[cible]["fichier"]}
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
        n_esc = min(ESCORTE_MAX, 2 * math.ceil(len([k for k in g.affecte if g.affecte[k] == mid] + libres) / ESCORTE_PAR_FRAPPEURS))
        deja = [k for k, m in g.affecte.items() if m == -mid]
        if n_esc > len(deja):
            escortes.append((mid, self._escorteurs(camp, n_esc - len(deja))))
        # les réarmements : des frappeurs au sol deviennent DEAD tant que la part voulue n'est pas atteinte
        if typ == "dead":
            rearmes = self._rearmer(camp)
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

    def _rearmer(self, camp):
        """[ ( numéro, nouveau chargement ) ] : des frappeurs posés deviennent DEAD jusqu'à la part voulue."""
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
            lo = self.charg_mission(a["dbid"], "dead")
            if lo:
                out.append((k, lo))
        return out

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
                "missions": {str(i): dict(m, avions=sorted(m["avions"])) for i, m in self.missions.items()},
                "journal": self.journal[-200:]}

    def charger(self, e):
        self.part_dead, self.efficacite, self.k = e["part_dead"], e["efficacite"], e["k"]
        self.missions = {int(i): dict(m, avions=set(m["avions"]), degats0={int(k): v for k, v in m["degats0"].items()})
                         for i, m in e["missions"].items()}
        self.journal = e.get("journal", [])
