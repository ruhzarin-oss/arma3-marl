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


def role_flotte(a):
    """Le rôle d'un avion dans sa flotte ( un frappeur réarmé en DEAD ou basculé en chasse reste un frappeur )."""
    return a.get("bascule") or ("frappe" if a["role"] == "dead" else a["role"])

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
SOUTIEN["balayage"] = (5, 1, None, None, None, 40.0, 0)   # balayage de chasse sur la cible, ciel ouvert seulement
SOUTIEN["reco"] = (6, 3, None, 20.0, 60.0, 15.0, 1)        # drones de reconnaissance : sur la cible, en stand-off si elle est couverte
SOUTIEN["elint"] = (7, 3, None, 40.0, 100.0, 25.0, 0)      # avions d'écoute ( RC-135, Il-20M ) : en stand-off, passifs
DEPLACEMENT_KM = 10.0                                     # une zone n'est redessinée que si elle bouge de plus
# LA GÉNÉRATION DE FORCE ( 03/10, Younes : « le moteur choisit lui-même les forces qu'il emploie, adaptation à la menace » ) :
# tous les ENGAGER_TOURS tours, l'état-major évalue la menace et ses besoins, puis engage depuis la réserve nationale les
# types les plus aptes ( valeur apprise par type et rôle ). Ratios de départ ( APPRIS ensuite ) et bornes : À VALIDER.
ENGAGER_TOURS = 10
RATIO_DEPART = {"aa": 1.0, "frappe": 1.0}                 # chasseurs par avion adverse menaçant ; frappeurs par cible
MAX_PAR_DECISION = 8                                      # avions engagés par rôle et par décision : une montée en puissance
PORTEE_MENACE_AIR_KM = 1500.0
# L'APPRENTISSAGE DES FORCES ( étape 3 ) : à chaque décision, le bilan de la fenêtre écoulée ajuste les ratios ( bornés ) et
# la valeur de chaque type dans chaque rôle ( sa survie ). À VALIDER : pas, bornes, seuil d'efficacité.
PAS_FORCES = 0.25
RATIO_MIN, RATIO_MAX = 0.5, 3.0
EFFICACITE_MIN = 50.0                                     # % de dégâts par avion perdu en dessous duquel la frappe coûte trop
ROLES_DEAD = ("dead", "bombardier")                       # qui part contre les défenses : armes à distance de sécurité
ROLES_OCA = ("frappe", "dead", "bombardier")              # ciel ouvert : tous les frappeurs
PORTEE_TERRE_MIN_KM = 50.0                                # en dessous ( canon seul ), un lance-missiles est antinavire pur
SEAD_PAR_CAMP = 2                                         # sans avions SEAD dédiés, une paire de frappeurs réarmée en antiradar


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


class EtatMajor:
    def __init__(self, g, *, portee_air=None, portee_sol=None, charg_mission=None, portee_nav=None, portee_mer=None,
                 portee_site_mer=None):
        self.g = g
        self.portee_air = portee_air or DOC.portee_sol_air
        self.portee_sol = portee_sol or DOC.portee_sol_sol
        self.charg_mission = charg_mission or DOC.chargement
        self.portee_nav = portee_nav or DOC.portee_navire_sol
        self._portee_mer = portee_mer
        self._portee_site_mer = portee_site_mer
        self._cache, self._charg = {}, {}
        self.part_dead = {c: PART_DEAD_DEPART for c in g.camps}
        self.efficacite = {c: {"dead": 1.0, "oca": 1.0} for c in g.camps}
        self.missions = {}                               # id -> { type, camp, cibles, avions, t0, degats0, pertes, ouverte }
        self.k = {c: 0 for c in g.camps}
        self.journal = []                                # décisions et notes, pour l'agent et pour Younes
        self.a_clore = []                                # ( camp, id ) des frappes à fermer dans CMO à ce tour
        self.zones = {}                                  # id de zone -> ( lat, lon ) envoyée à CMO
        self.antinav = {c: None for c in g.camps}        # la frappe antinavire en cours de chaque camp { id, cibles }
        self.k_an = {c: 0 for c in g.camps}
        self.portee_mer = self._portee_mer or DOC.portee_navire_mer
        self.portee_site_mer = self._portee_site_mer or DOC.portee_site_mer
        # LA CARTE DES MENACES de chaque camp : les défenses sol-air adverses qu'il a identifiées ( contact classé >= 2 ) ou
        # connues d'avance ( garnisons du temps de paix ), à leur dernière position connue, jusqu'à leur destruction.
        self.memoire = {c: {} for c in g.camps}          # camp -> { numéro : [ lat, lon, tour ] }
        self.avant_guerre = False                        # les garnisons connues d'avance sont-elles sur la carte ?
        self.ratio = {c: dict(RATIO_DEPART) for c in g.camps}     # appris ( étape 3 )
        self.valeur = {}                                 # « dbid|rôle » -> valeur apprise d'un type dans un rôle ( 1 au départ )
        self.dernier_bilan = {c: 0 for c in g.camps}     # tour du dernier bilan d'apprentissage des forces
        # les leviers STRATÉGIQUES du chef d'état-major ( Qwen, chef_qwen.py ) : cible prioritaire, multiplicateurs des
        # ratios, réserves gardées
        self.cible_imposee = {c: None for c in g.camps}
        self.mult_chef = {c: {"aa": 1.0, "frappe": 1.0} for c in g.camps}
        self.reserves_gardees = {c: False for c in g.camps}

    # ---- mémoire des portées ( la DB est lente : une lecture par type )
    def _p(self, quoi, dbid):
        cle = (quoi, dbid)
        if cle not in self._cache:
            self._cache[cle] = {"air": self.portee_air, "sol": self.portee_sol, "nav": self.portee_nav}[quoi](dbid) if dbid else 0.0
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

    def renseigner(self):
        """La carte des menaces, chaque tour : une défense adverse vue et classée au moins « type connu » y entre ( ou y
        est déplacée ) ; perdue de vue, elle y reste à sa dernière position ; détruite, elle en sort. Avant-guerre ( ou
        à la première reprise ), les garnisons des défenses sol-air adverses y sont : l'OTAN sait où sont les S-400 de
        Kaliningrad depuis le temps de paix, comme la Russie connaît les Patriot polonais."""
        g = self.g
        for camp in g.camps:
            mem = self.memoire.setdefault(camp, {})
            if not self.avant_guerre:
                for k, s in g.sol.items():
                    if s["camp"] != camp and self._p("air", s["dbid"]) >= DOC.PORTEE_MENACE_KM and k not in mem:
                        mem[k] = [s["pos"][0], s["pos"][1], 0]
            for k, v in g.vus.get(camp, {}).items():
                if v[0] >= CLASSIF_MIN:
                    vrai = g.sol[k]["pos"] if k in g.sol else g.navires[k]["pos"] if k in g.navires else None
                    mem[k] = [v[2], v[3], g.tours] if (v[2] or v[3]) else [*vrai, g.tours] if vrai else None
            for k in [k for k in mem if (k not in g.sol and k not in g.navires) or mem[k] is None]:
                del mem[k]
        self.avant_guerre = True

    def _connu(self, camp, k):
        """Brouillard de guerre : une unité mobile adverse n'existe pour l'état-major que si elle est sur la carte des
        menaces de son camp ( identifiée, ou connue d'avance )."""
        if not self.g.brouillard:
            return True
        return k in self.memoire.get(camp, {})

    def _vu_ou(self, camp, k, vrai):
        """La position que le camp CROIT : la dernière connue sur sa carte des menaces, à défaut la vraie."""
        m = self.memoire.get(camp, {}).get(k) if self.g.brouillard else None
        return (m[0], m[1]) if m else vrai

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
            roles = ROLES_DEAD
        else:
            b = g.bases[cible]
            typ, cibles = "oca", [k for k in b["pistes"] + b["acces"] + b["depots"] if g.percu(camp, k) < 100.0]
            roles = ROLES_OCA                            # ciel ouvert : les avions DEAD et les bombardiers frappent aussi
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
        lanceurs += sorted(k for k, n in g.navires.items() if n["camp"] == camp and n["role"] == "lance_missiles"
                           and g.affecte.get(k) not in (mid, -1)
                           and any(p and km(n["pos"], p) <= self._p("nav", n["dbid"]) for p in positions))
        if libres or lanceurs:
            affect.append((mid, libres + lanceurs))
        # l'escorte : une paire par ESCORTE_PAR_FRAPPEURS frappeurs, prise là où il y a le plus de chasseurs
        # un lanceur au sol ne s'escorte pas, un bombardier qui tire de loin non plus
        avions_mid = [k for k, m in g.affecte.items() if m == mid and k in g.avions and g.avions[k]["role"] != "bombardier"]
        n_esc = min(ESCORTE_MAX, 2 * math.ceil(len(avions_mid + [k for k in libres if g.avions[k]["role"] != "bombardier"])
                                               / ESCORTE_PAR_FRAPPEURS))
        deja = [k for k, m in g.affecte.items() if m == -mid]
        if n_esc > len(deja):
            escortes.append((mid, self._escorteurs(camp, n_esc - len(deja))))
        # les réarmements : des frappeurs au sol deviennent DEAD tant que la part voulue n'est pas atteinte ; ceux qui n'ont
        # pas d'arme à distance passent en chasse pendant la DEAD et reviennent à la frappe quand le ciel est ouvert
        if typ == "dead":
            rearmes = self._rearmer_sead(camp)
            pris = {k for k, *_ in rearmes}
            rearmes += [x for x in self._rearmer(camp) if x[0] not in pris]
            pris |= {k for k, *_ in rearmes}
            rearmes += [x for x in self._basculer(camp, "aa") if x[0] not in pris]
        else:
            rearmes = self._basculer(camp, "frappe")
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
                              "t0": g.tours, "degats0": {k: self._degats(k, camp) for k in cibles}, "avions": set(), "pertes": 0}
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

    def _degats(self, k, camp):
        """Les dégâts d'une cible tels que le camp les CROIT ( évaluation des dégâts ) ; une unité au sol disparue est
        détruite ( l'arme qui la frappe la voit tomber )."""
        if k in self.g.elements:
            return self.g.percu(camp, k)
        return 0.0 if k in self.g.sol else 100.0

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

    def _rearmer_sead(self, camp):
        """[ ( numéro, chargement antiradar, « sead » ) ] : un camp SANS avions SEAD dédiés ( la Russie n'a pas de Tornado
        ECR ) réarme une paire de frappeurs posés en Kh-31P / Kh-58, comme ses Su-30SM et Su-35S en Ukraine."""
        g = self.g
        if sum(1 for a in g.avions.values() if a["camp"] == camp and a["role"] == "sead") >= SEAD_PAR_CAMP:
            return []
        out = []
        for k, a in sorted(g.avions.items()):
            if len(out) >= SEAD_PAR_CAMP:
                break
            if a["camp"] != camp or a["role"] != "frappe" or g.altitudes.get(k, 0) > 500 or abs(g.affecte.get(k, 0)) >= 1000:
                continue
            lo = self._cm(a["dbid"], "sead")
            if lo:
                out.append((k, lo, "sead"))
        return out[:len(out) // 2 * 2]

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

    def _barriere(self, camp, zids):
        """La chasse avancée ( barrière et balayage ) : à chaque base, au-delà de la paire qui la défend, la moitié des
        chasseurs ( par paires ). Ceux qui y sont y restent ( pas de valse ) ; les escortes passent avant."""
        zids = {zids} if isinstance(zids, int) else set(zids)
        g, par_base = self.g, {}
        for k, a in sorted(g.avions.items()):
            m = g.affecte.get(k, 0)
            if a["camp"] == camp and a["role"] == "aa" and abs(m) < 1000:
                par_base.setdefault(a["base"], []).append(k)
        out = []
        for base, ks in par_base.items():
            voulus = (max(0, len(ks) - 2) // 2) // 2 * 2
            deja = [k for k in ks if g.affecte.get(k) in zids]
            libres = [k for k in ks if g.affecte.get(k) not in zids]
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
        zb, zs = ZONE_BASE + ci * 10 + SOUTIEN["barriere"][0], ZONE_BASE + ci * 10 + SOUTIEN.get("balayage", (5,))[0]
        chasse = self._barriere(camp, (zb, zs))
        balayage = []
        if "balayage" in SOUTIEN and fr and fr.get("type") == "oca" and len(chasse) >= 4:   # ciel ouvert : on balaie la cible
            n = len(chasse) // 2 // 2 * 2
            balayage = ([k for k in chasse if g.affecte.get(k) == zs] + [k for k in chasse if g.affecte.get(k) != zs])[:n]
        for role, (dec, genre, t0, marge, marge_b, demi, emcon) in SOUTIEN.items():
            zid = ZONE_BASE + ci * 10 + dec
            if role == "barriere":
                ks = [k for k in chasse if k not in balayage]
            elif role == "balayage":
                ks = balayage
            else:
                ks = [k for k, a in sorted(g.avions.items()) if a["camp"] == camp and a["role"] == role]
            if not ks or (role in ("sead", "brouilleur", "reco", "elint") and not fr):
                continue
            if role == "balayage":
                P = T
            elif role in ("reco", "elint"):
                cov = self.couvrent(camp, T)
                if role == "reco" and not cov:
                    P = T
                else:
                    r = max((x[2] for x in cov), default=40.0)
                    d = km(C, T)
                    P = self._recul(camp, C, T, max(0.0, 1 - (r + marge + 10.0) / d) if d > 0 else 0.0, marge, marge_b)
            elif role == "sead":
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

    # ---- 2 quater. la composante navale : contrôle de la mer, lutte anti-sous-marine, frappes navales
    ZONE_NAVALE = 600                                    # 600 + camp x 10 + ( 0 contrôle de la mer, 1 lutte ASM )
    ROLES_MER = ("fregate", "corvette", "patrouilleur")      # les batteries côtières ( « cotier » ) tirent depuis la terre

    def marine(self, ci, camp):
        """( zones, affectations ) navales du camp : frégates et corvettes en CONTRÔLE DE LA MER, sous-marins en LUTTE
        ANTI-SOUS-MARINE, dans les zones du théâtre ( choix du réel, à valider ). Les lance-missiles de croisière vont aux
        frappes ( planifier ) ; les chasseurs de mines restent au port."""
        g = self.g
        zn = g.zones_navales.get(camp) or {}
        zones, affect = [], []
        for cle, genre, roles, dec in (("mer", 6, self.ROLES_MER, 0), ("asm", 5, ("sous_marin",), 1)):
            if cle not in zn:
                continue
            la, lo, demi = zn[cle]
            zid = self.ZONE_NAVALE + ci * 10 + dec
            ks = [k for k, n in sorted(g.navires.items()) if n["camp"] == camp and (n["role"] in roles or
                  ( cle == "mer" and n["role"] == "lance_missiles" and ( self._p("nav", n["dbid"]) < PORTEE_TERRE_MIN_KM
                                                                        or abs(g.affecte.get(k, 0)) < 1000 ) ))]
            if not ks:
                continue
            if zid not in self.zones:
                zones.append((zid, camp, genre, la, lo, demi, 0, 0, 0))
                self.zones[zid] = (la, lo)
            nouveaux = [k for k in ks if g.affecte.get(k) != zid]
            if nouveaux:
                affect.append((zid, nouveaux))
        return zones, affect

    DEC_ANTINAVIRE = 3000                                # 3 000 + camp x 100 + k
    PORTEE_ANTINAVIRE_KM = 400.0

    def antinavire(self, ci, camp):
        """( frappes navales, affectations ) : la frappe ANTINAVIRE contre les navires ennemis CONNUS ( carte des menaces )
        à moins de PORTEE_ANTINAVIRE_KM de nos forces. Navires à découvert : frappeurs inemployés ( pendant la DEAD, ils
        attendaient ), lance-missiles et batteries côtières à portée. Navires sous un parapluie sol-air connu : seulement
        les tireurs À DISTANCE DE SÉCURITÉ ( navires et batteries côtières dont l'arme antinavire porte jusqu'à eux ), jamais
        les avions ( 03/10 : la flotte russe reste sous les défenses de Kaliningrad )."""
        g = self.g
        C = self._centre(camp)
        cur = self.antinav.get(camp)
        decouverts, couverts = [], []
        if C is not None:
            menaces = self.parapluies(camp)
            for k in self.memoire.get(camp, {}):
                n = g.navires.get(k)
                if not n or n["camp"] == camp or n.get("genre") == "site":
                    continue
                P = self._vu_ou(camp, k, n["pos"])
                if km(P, C) > self.PORTEE_ANTINAVIRE_KM:
                    continue
                (couverts if any(km(pos, P) <= r + MARGE_KM for _, pos, r in menaces) else decouverts).append(k)
        tireurs = [k for k, n in sorted(g.navires.items()) if n["camp"] == camp
                   and (n["role"] in ("lance_missiles", "cotier", "fregate", "corvette")) and abs(g.affecte.get(k, 0)) < 1000
                   or (k in g.navires and g.navires[k]["camp"] == camp and cur and g.affecte.get(k) == cur["id"])]

        def portee(k):
            n = g.navires[k]
            return self._pm_site(n["dbid"]) if n.get("genre") == "site" else self._pm(n["dbid"])

        if decouverts:
            cibles = sorted(decouverts)
        else:
            cibles = sorted(k for k in couverts if any(km(g.navires[t]["pos"], self._vu_ou(camp, k, g.navires[k]["pos"])) <= portee(t)
                                                       for t in tireurs))
        frappes, affect = [], []
        if not cibles:
            if cur:
                self.a_clore.append((camp, cur["id"]))
                for k, m in list(g.affecte.items()):
                    if m == cur["id"]:
                        del g.affecte[k]
                self.antinav[camp] = None
            return frappes, affect
        if not cur or set(cur["cibles"]) != set(cibles):
            if cur:
                self.a_clore.append((camp, cur["id"]))
                for k, m in list(g.affecte.items()):
                    if m == cur["id"]:
                        del g.affecte[k]
            self.k_an[camp] += 1
            cur = self.antinav[camp] = {"id": self.DEC_ANTINAVIRE + ci * 100 + self.k_an[camp] % 100, "cibles": cibles}
            frappes.append((cur["id"], camp, cibles))
        mid = cur["id"]
        positions = [self._vu_ou(camp, k, g.navires[k]["pos"]) for k in cibles if k in g.navires]
        avions = []
        if decouverts:                                   # jamais d'avion sous un parapluie
            avions = [k for k, a in sorted(g.avions.items()) if a["camp"] == camp and a["role"] == "frappe"
                      and abs(g.affecte.get(k, 0)) < 1000][: 2 * len(cibles)]
            avions = avions[:len(avions) // 2 * 2]
        nav = [k for k in tireurs if g.affecte.get(k) != mid and any(km(g.navires[k]["pos"], p) <= portee(k) for p in positions)]
        if avions or nav:
            affect.append((mid, avions + nav))
        return frappes, affect

    def _pm_site(self, dbid):
        cle = ("mer_site", dbid)
        if cle not in self._cache:
            self._cache[cle] = self.portee_site_mer(dbid) if dbid else 0.0
        return self._cache[cle]

    def _pm(self, dbid):
        cle = ("mer", dbid)
        if cle not in self._cache:
            self._cache[cle] = self.portee_mer(dbid) if dbid else 0.0
        return self._cache[cle]

    def _centre_adverse(self, camp):
        pts = [b["pos"] for b in self.g.bases.values() if b["camp"] != camp and b["op"] and b["pos"]]
        if not pts:
            return None
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))

    # ---- 2 ter. la génération de force : besoins, puis engagement depuis la réserve
    def besoins(self, camp):
        """{ rôle : ( besoin, au théâtre ) } : la chasse selon la MENACE AÉRIENNE ( avions adverses de combat basés à moins
        de PORTEE_MENACE_AIR_KM de nos avions, connus par le renseignement d'ordre de bataille ), au moins une paire par base ;
        la frappe selon les cibles de la mission en cours ( éléments de la base, ou défenses à détruire ), au moins 4."""
        g = self.g
        C = self._centre(camp)
        menace = 0
        if C is not None:
            for a in g.avions.values():
                b = g.bases.get(a["base"])
                if a["camp"] != camp and a["role"] in ("aa", "frappe", "dead", "bombardier") and b and b["op"] \
                        and km(b["pos"], C) <= PORTEE_MENACE_AIR_KM:
                    menace += 1
        mes_bases = sum(1 for b in g.bases.values() if b["camp"] == camp and b["op"])
        fr = g.frappe.get(camp)
        cibles = len(fr["cibles"]) if fr else 0
        tenus = {"aa": 0, "frappe": 0}
        for a in g.avions.values():
            if a["camp"] == camp:
                r = "frappe" if a["role"] in ("frappe", "dead") or a.get("bascule") == "frappe" else a["role"]
                if r in tenus:
                    tenus[r] += 1
        for r in g.renforts:
            if g.camp_de_pays(r["pays"]) == camp and r["role"] in tenus:
                tenus[r["role"]] += r["n"]
        m = self.mult_chef.get(camp, {"aa": 1.0, "frappe": 1.0})
        return {"aa": (max(2 * mes_bases, math.ceil(self.ratio[camp]["aa"] * m["aa"] * menace)), tenus["aa"]),
                "frappe": (max(4, math.ceil(self.ratio[camp]["frappe"] * m["frappe"] * cibles)), tenus["frappe"]),
                "_menace_air": menace}

    def apprendre_forces(self, camp):
        """Le bilan de la fenêtre écoulée depuis la dernière décision, et ce que l'état-major en apprend :
        - CHASSE : nos pertes ( avions et éléments d'installations ) supérieures aux avions adverses abattus -> plus de
          chasseurs par avion menaçant ; l'inverse -> on redescend doucement ( économie des forces ) ; rien -> rien appris ;
        - FRAPPE : missions closes dans la fenêtre ; des dégâts sans perte -> plus de frappeurs par cible ; des pertes pour
          moins de EFFICACITE_MIN % de dégâts par avion perdu -> moins ;
        - VALEUR d'un type dans un rôle : moyenne glissante de sa survie dans la fenêtre ( les types qui meurent passent
          après les autres à l'engagement suivant ).
        Ratios bornés à [ RATIO_MIN, RATIO_MAX ]."""
        g = self.g
        t0 = self.dernier_bilan.get(camp, 0)
        dans = lambda t: t0 < t <= g.tours                                      # noqa: E731
        avions = [m for m in g.morts if m["genre"] == "avion" and dans(m["tour"])]
        mes_avions = [m for m in avions if g.camp_de_pays(m["pays"]) == camp]
        leurs_avions = [m for m in avions if g.camp_de_pays(m["pays"]) != camp]
        mes_elements = [d for d in g.detruits if d["camp"] == camp and dans(d["tour"])]
        r = self.ratio[camp]
        subi, inflige = len(mes_avions) + len(mes_elements), len(leurs_avions)
        if subi > inflige:
            r["aa"] = min(RATIO_MAX, r["aa"] * (1 + PAS_FORCES))
        elif inflige > subi:
            r["aa"] = max(RATIO_MIN, r["aa"] * (1 - PAS_FORCES / 3))
        clos = [x for x in self.journal if x.get("camp") == camp and "cloture" in x and dans(x["tour"])]
        degats, pertes = sum(x["degats"] for x in clos), sum(x["pertes"] for x in clos)
        if clos and degats > 0 and pertes == 0:
            r["frappe"] = min(RATIO_MAX, r["frappe"] * (1 + PAS_FORCES))
        elif clos and pertes > 0 and degats / pertes < EFFICACITE_MIN:
            r["frappe"] = max(RATIO_MIN, r["frappe"] * (1 - PAS_FORCES))
        presents = {}
        for a in g.avions.values():
            if a["camp"] == camp:
                cle = f'{a["dbid"]}|{role_flotte(a)}'
                presents[cle] = presents.get(cle, 0) + 1
        perdus = {}
        for m in mes_avions:
            if m.get("cle"):
                cle = f'{m["cle"][2]}|{"frappe" if m["cle"][3] == "dead" else m["cle"][3]}'
                perdus[cle] = perdus.get(cle, 0) + 1
        for cle in set(presents) | set(perdus):
            n = presents.get(cle, 0) + perdus.get(cle, 0)
            survie = 1.0 - perdus.get(cle, 0) / n if n else 1.0
            self.valeur[cle] = (1 - PAS_FORCES) * self.valeur.get(cle, 1.0) + PAS_FORCES * survie
        self.dernier_bilan[camp] = g.tours
        self.journal.append({"camp": camp, "tour": g.tours, "apprentissage": {
            "ratio": {k: round(v, 3) for k, v in r.items()}, "subi": subi, "inflige_air": inflige,
            "missions_closes": len(clos), "degats": round(degats, 1), "pertes_frappe": pertes,
            "valeurs_basses": {k: round(v, 2) for k, v in self.valeur.items() if v < 0.9}}})

    def engager(self, camp):
        """[ ( pays, dbid, rôle, n, base ) ] : pour chaque rôle en déficit, les types de la réserve des pays du camp qui
        savent le tenir ( un chargement pour ce rôle ), le plus VALABLE d'abord ( valeur apprise ), puis le plus abondant ;
        par paires, au plus MAX_PAR_DECISION par rôle ; vers la base d'attache de la flotte, ou la plus proche qui tient."""
        g, out = self.g, []
        bes = self.besoins(camp)
        for role in (() if self.reserves_gardees.get(camp) else ("aa", "frappe")):   # le chef peut garder ses réserves
            besoin, tenu = bes[role]
            manque = min(MAX_PAR_DECISION, max(0, besoin - tenu))
            cand = []
            for cle, n in g.reserve.items():
                pays, dbid = cle.rsplit("|", 1)
                dbid = int(dbid)
                if g.camp_de_pays(pays) != camp or n < 2 or not g.charg.get(dbid, {}).get(role):
                    continue
                cand.append((-self.valeur.get(f"{dbid}|{role}", 1.0), -n, pays, dbid))
            for _, _, pays, dbid in sorted(cand):
                if manque < 2:
                    break
                k = min(manque, int(g.reserve[f"{pays}|{dbid}"])) // 2 * 2
                base = self._base_attache(pays, dbid)
                if k >= 2 and base is not None:
                    out.append((pays, dbid, role, k, base))
                    manque -= k
        self.journal.append({"camp": camp, "tour": g.tours, "besoins": {r: list(v) if isinstance(v, tuple) else v for r, v in bes.items()},
                             "engage": [list(x) for x in out]})
        return out

    def _base_attache(self, pays, dbid):
        g = self.g
        for f, p, d, *_ in g.flottes:
            if p == pays and d == dbid:
                i = g.base_de_fichier(f)
                if i is not None and g.bases[i]["op"]:
                    return i
        ops = [i for i, b in g.bases.items() if b["op"] and g.camp_de_pays(b["pays"]) == g.camp_de_pays(pays)]
        mien = [i for i in ops if g.bases[i]["pays"] == pays] or ops
        C = self._centre(g.camp_de_pays(pays))
        return min(mien, key=lambda i: km(g.bases[i]["pos"], C) if C else 0) if mien else None

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
        degats = sum(max(0.0, self._degats(k, m["camp"]) - d0) for k, d0 in m["degats0"].items())
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
                "zones": {str(i): list(p) for i, p in self.zones.items()}, "antinav": self.antinav, "k_an": self.k_an, "ratio": self.ratio, "valeur": self.valeur, "dernier_bilan": self.dernier_bilan,
                "cible_imposee": self.cible_imposee, "mult_chef": self.mult_chef, "reserves_gardees": self.reserves_gardees,
                "memoire": {c: {str(k): v for k, v in m.items()} for c, m in self.memoire.items()}, "avant_guerre": self.avant_guerre,
                "missions": {str(i): dict(m, avions=sorted(m["avions"])) for i, m in self.missions.items()},
                "journal": self.journal[-200:]}

    def charger(self, e):
        self.part_dead, self.efficacite, self.k = e["part_dead"], e["efficacite"], e["k"]
        self.missions = {int(i): dict(m, avions=set(m["avions"]), degats0={int(k): v for k, v in m["degats0"].items()})
                         for i, m in e["missions"].items()}
        self.journal = e.get("journal", [])
        self.zones = {int(i): tuple(p) for i, p in (e.get("zones") or {}).items()}
        self.antinav = e.get("antinav") or self.antinav
        self.k_an = e.get("k_an") or self.k_an
        self.avant_guerre = e.get("avant_guerre", False)
        self.ratio = e.get("ratio") or self.ratio
        self.valeur = e.get("valeur") or {}
        self.dernier_bilan = e.get("dernier_bilan") or self.dernier_bilan
        self.cible_imposee = e.get("cible_imposee") or self.cible_imposee
        self.mult_chef = e.get("mult_chef") or self.mult_chef
        self.reserves_gardees = e.get("reserves_gardees") or self.reserves_gardees
        if e.get("memoire") is not None:
            self.memoire = {c: {int(k): v for k, v in m.items()} for c, m in e["memoire"].items()}
