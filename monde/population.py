"""Les 500 habitants : role, classe, age, famille, domicile, lieu de travail, horaire, sante, argent.
Chaque habitant garde son identite pour toujours, qu il soit simule ( donnee ) ou incarne dans Arma ( la bulle, E2 )."""
from . import config as C

# lieu de travail de chaque role : types de lieux, horaire
TRAVAIL = {
    "chef_gouvernement": (("gouvernement",), "bureau"), "ministre": (("gouvernement",), "bureau"),
    "officier": (("base",), "bureau"), "soldat": (("base",), "garde"),
    "policier": (("capitale",), "garde"), "medecin": (("capitale",), "garde"), "infirmier": (("capitale",), "garde"),
    "enseignant": (("capitale",), "ecole"), "patron": (("capitale",), "bureau"),
    "paysan": (("village",), "jour"), "mineur": (("mine", "carriere"), "jour"), "petrolier": (("puits",), "garde"),
    "ouvrier": (("raffinerie", "centrale", "fonderie", "pharmacie"), "jour"), "convoyeur": (("capitale",), "jour"),
    "marchand": (("capitale",), "marche"), "enfant": (("capitale",), "ecole"), "retraite": ((), None),
}
SALAIRE_HORAIRE = {   # drachmes par heure travaillee ( public : paye par l Etat ; prive : par l entreprise )
    "chef_gouvernement": 30, "ministre": 22, "officier": 16, "soldat": 7, "policier": 9, "medecin": 20, "infirmier": 10,
    "enseignant": 10, "ouvrier": 8, "mineur": 9, "petrolier": 9, "convoyeur": 7, "marchand": 0, "paysan": 0, "patron": 0,
}
PENSION_JOUR = 20     # retraite versee par l Etat


class Habitant:
    __slots__ = ("id", "nom", "role", "classe", "age", "menage", "domicile", "travail", "horaire", "equipe",
                 "lieu", "etat", "jours_etat", "gravite", "remede", "vivant", "faim", "heures_jour", "amendes",
                 "incarne", "eleve", "poste", "decalage")

    def __init__(self, id, role, classe, age):
        self.id, self.role, self.classe, self.age = id, role, classe, age
        self.nom = f"H{id:03d}"
        self.menage = None; self.domicile = None; self.travail = None; self.horaire = None; self.equipe = 0
        self.decalage = 0.0          # son quart d heure a lui : tout le monde ne part pas a la meme minute
        self.lieu = None; self.poste = "maison"     # ou il est DANS son lieu : maison, travail, hopital
        self.etat = "S"; self.jours_etat = 0.0; self.gravite = 0.0; self.remede = False; self.vivant = True
        self.faim = 0.0; self.heures_jour = 0.0; self.amendes = 0
        self.incarne = False; self.eleve = False

    def au_travail(self, heure):
        """Vrai si l horaire de cet habitant le met au travail a cette heure du monde.

        Le DECALAGE personnel ( +/- 30 min ) n est pas une coquetterie : mesure du 22/09, 765 corps qui partent a la
        meme minute font tomber la pire image du serveur a 3 par seconde, contre 29 au repos. Les departs etales
        coutent le meme travail, reparti."""
        heure = heure - self.decalage / 60.0
        if self.horaire is None or not self.vivant or self.etat == "I" and self.gravite > 0.5: return False
        if self.horaire == "garde":        # trois equipes de 8 h : 6-14, 14-22, 22-6
            debut = (6, 14, 22)[self.equipe % 3]
            return (heure - debut) % 24 < 8
        a, b = C.HORAIRES[self.horaire]
        return a <= heure < b if a < b else (heure >= a or heure < b)


class Menage:
    def __init__(self, id, domicile):
        self.id, self.domicile = id, domicile
        self.membres = []
        self.caisse = 0.0
        self.garde_manger = 0.0      # nourriture en reserve a la maison

    def adultes(self):
        return [h for h in self.membres if h.role not in ("enfant",) and h.vivant]


def generer(carte, rng):
    """Cree les 500 habitants et leurs menages, deterministe a graine fixee."""
    H = []
    for role, (n, classe, _) in C.ROLES.items():
        for _ in range(n):
            age = int(rng.integers(6, 18)) if role == "enfant" else int(rng.integers(65, 86)) if role == "retraite" \
                else int(rng.integers(20, 65))
            H.append(Habitant(len(H), role, classe, age))
    # lieux de travail : repartition equilibree sur les lieux du bon type
    compteur = {}
    for h in H:
        types, horaire = TRAVAIL[h.role]
        h.horaire = horaire
        if not types: continue
        if types == ("gouvernement",): cands = [carte.gouvernement]
        elif h.role == "ouvrier":         # les ouvriers vont ou il faut des bras : la raffinerie d abord
            cands = [l for l in carte.de_type(*types) for _ in range(C.OUVRIERS_PAR_SITE[l.type])]
        else: cands = carte.de_type(*types)
        k = compteur.get(h.role, 0); compteur[h.role] = k + 1
        h.travail = cands[k % len(cands)]
        h.equipe = k
    # domiciles : les actifs vivent au lieu habitable le plus proche de leur travail
    for h in H:
        if h.travail is not None and h.role != "enfant":
            h.domicile = h.travail if h.travail.type in ("capitale", "ville", "village") else \
                carte.plus_proche(h.travail, ("capitale", "ville", "village"))
    # menages : chaque adulte actif fonde un menage ; enfants et retraites rejoignent un menage au hasard
    M = []
    for h in H:
        if h.role not in ("enfant", "retraite"):
            m = Menage(len(M), h.domicile); m.membres.append(h); h.menage = m; M.append(m)
    for h in H:
        if h.role in ("enfant", "retraite"):
            m = M[int(rng.integers(0, len(M)))]
            m.membres.append(h); h.menage = m; h.domicile = m.domicile
            if h.role == "enfant":      # un enfant va a l ecole de la capitale de son marche
                h.travail = h.domicile.marche
    for h in H:
        h.lieu = h.domicile
        h.decalage = float(rng.integers(-30, 31))
    # epargne de depart selon la classe
    for m in M:
        m.caisse = sum({"aisee": 3000.0, "moyenne": 800.0, "populaire": 250.0}[x.classe] for x in m.adultes())
        m.garde_manger = 2.0 * len(m.membres)
    # l eleve : un enfant de Kavala, le plus jeune
    enfants = [h for h in H if h.role == "enfant" and h.domicile.id == "Kavala"] or [h for h in H if h.role == "enfant"]
    min(enfants, key=lambda h: (h.age, h.id)).eleve = True
    return H, M
