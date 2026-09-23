"""Les 500 habitants : role, classe, age, famille, domicile, lieu de travail, horaire, sante, argent.
Chaque habitant garde son identite pour toujours, qu il soit simule ( donnee ) ou incarne dans Arma ( la bulle, E2 )."""
import numpy as np
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


POSTES = ("maison", "travail", "hopital", "voyage")
CODE_POSTE = {p: i for i, p in enumerate(POSTES)}
CODE_HORAIRE = {None: -1, "jour": 0, "bureau": 1, "nuit": 2, "ecole": 3, "marche": 4, "garde": 5}
CODE_ETAT = {"S": 0, "E": 1, "I": 2, "R": 3}
CODE_ROLE = {r: i for i, r in enumerate(C.ROLES)}


class Table:
    """Les habitants en COLONNES : un tableau par attribut, une ligne par habitant ( la ligne est son identifiant ).

    C est la forme que le coeur Rust lit sur tous les coeurs a la fois ( monde/essai_coeur.py : x183 sur `deplacer`
    a un million d habitants ). Deux sortes de colonnes :
      - celles que Rust ECRIT ( lieu, poste, heures, travaille ) : la colonne fait foi, l habitant la lit ;
      - celles que Rust LIT ( vivant, etat, gravite, faim, horaire... ) : l habitant garde sa valeur et la recopie
        dans la colonne a chaque ecriture, pour que Python lise vite et que Rust lise juste."""

    CHAMPS = {"vivant": (np.uint8, 1), "lieu": (np.int32, -1), "poste": (np.uint8, 0), "heures": (np.float64, 0.0),
              "etat": (np.uint8, 0), "gravite": (np.float64, 0.0), "faim": (np.float64, 0.0),
              "horaire": (np.int8, -1), "equipe": (np.int32, 0), "decalage": (np.float64, 0.0),
              "travail": (np.int32, -1), "domicile": (np.int32, -1), "hopital": (np.int32, -1),
              "public": (np.uint8, 0), "role": (np.int16, -1), "travaille": (np.uint8, 0)}

    def __init__(self, par_n, capacite=1024):
        self.par_n = par_n                 # les lieux par numero ( Carte.par_n )
        self.n = 0
        self.capacite = capacite
        for nom, (dt, defaut) in self.CHAMPS.items(): setattr(self, nom, np.full(capacite, defaut, dt))

    def ajouter(self):
        """Une ligne de plus ; la capacite double quand elle est pleine ( une naissance ne recopie pas le pays )."""
        if self.n == self.capacite:
            neuve = self.capacite * 2
            for nom, (dt, defaut) in self.CHAMPS.items():
                vieille = getattr(self, nom)
                t = np.full(neuve, defaut, dt); t[:self.capacite] = vieille
                setattr(self, nom, t)
            self.capacite = neuve
        self.n += 1
        return self.n - 1


class Habitant:
    __slots__ = ("id", "nom", "_role", "classe", "age", "menage", "_domicile", "_travail", "_horaire", "_equipe",
                 "_etat", "jours_etat", "_gravite", "remede", "_vivant", "_faim", "amendes",
                 "incarne", "eleve", "_decalage", "_t")

    def __init__(self, id, role, classe, age, table):
        self._t = table
        ligne = table.ajouter()
        assert ligne == id, f"la ligne de la table ( {ligne} ) doit etre l identifiant de l habitant ( {id} )"
        self.id, self.role, self.classe, self.age = id, role, classe, age
        self.nom = f"H{id:03d}"
        self.menage = None; self.domicile = None; self.travail = None; self.horaire = None; self.equipe = 0
        self.decalage = 0.0          # son quart d heure a lui : tout le monde ne part pas a la meme minute
        self.lieu = None; self.poste = "maison"     # ou il est DANS son lieu : maison, travail, hopital
        self.etat = "S"; self.jours_etat = 0.0; self.gravite = 0.0; self.remede = False; self.vivant = True
        self.faim = 0.0; self.heures_jour = 0.0; self.amendes = 0
        self.incarne = False; self.eleve = False

    # --- ce que Rust LIT : la valeur vit ici ( lecture rapide en Python ), recopiee dans la table a chaque ecriture ---
    @property
    def role(self): return self._role

    @role.setter
    def role(self, v):
        self._role = v
        self._t.role[self.id] = CODE_ROLE.get(v, -1)
        self._t.public[self.id] = 1 if v in C.ROLES and C.ROLES[v][2] else 0

    @property
    def domicile(self): return self._domicile

    @domicile.setter
    def domicile(self, v):
        self._domicile = v
        self._t.domicile[self.id] = v.n if v is not None else -1
        self._t.hopital[self.id] = v.marche.n if (v is not None and v.marche is not None) else -1   # l hopital du malade

    @property
    def travail(self): return self._travail

    @travail.setter
    def travail(self, v):
        self._travail = v
        self._t.travail[self.id] = v.n if v is not None else -1

    @property
    def horaire(self): return self._horaire

    @horaire.setter
    def horaire(self, v):
        self._horaire = v
        self._t.horaire[self.id] = CODE_HORAIRE[v]

    @property
    def equipe(self): return self._equipe

    @equipe.setter
    def equipe(self, v):
        self._equipe = v
        self._t.equipe[self.id] = v

    @property
    def decalage(self): return self._decalage

    @decalage.setter
    def decalage(self, v):
        self._decalage = v
        self._t.decalage[self.id] = v

    @property
    def etat(self): return self._etat

    @etat.setter
    def etat(self, v):
        self._etat = v
        self._t.etat[self.id] = CODE_ETAT[v]

    @property
    def gravite(self): return self._gravite

    @gravite.setter
    def gravite(self, v):
        self._gravite = v
        self._t.gravite[self.id] = v

    @property
    def faim(self): return self._faim

    @faim.setter
    def faim(self, v):
        self._faim = v
        self._t.faim[self.id] = v

    @property
    def vivant(self): return self._vivant

    @vivant.setter
    def vivant(self, v):
        self._vivant = v
        self._t.vivant[self.id] = 1 if v else 0

    # --- ce que Rust ECRIT : la colonne fait foi, l habitant la lit ---
    @property
    def lieu(self):
        k = self._t.lieu[self.id]
        return self._t.par_n[k] if k >= 0 else None

    @lieu.setter
    def lieu(self, v): self._t.lieu[self.id] = v.n if v is not None else -1

    @property
    def poste(self): return POSTES[self._t.poste[self.id]]

    @poste.setter
    def poste(self, v): self._t.poste[self.id] = CODE_POSTE[v]

    @property
    def heures_jour(self): return float(self._t.heures[self.id])

    @heures_jour.setter
    def heures_jour(self, v): self._t.heures[self.id] = v

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


def generer(carte, rng, echelle=1.0, table=None):
    """Cree la population et ses menages, deterministe a graine fixee. `echelle` multiplie chaque metier : le pays
    garde ses proportions, il change de taille."""
    H = []
    table = table if table is not None else Table(carte.par_n)
    for role, (n, classe, _) in C.ROLES.items():
        for _ in range(max(1, int(round(n * echelle)))):
            age = int(rng.integers(6, 18)) if role == "enfant" else int(rng.integers(65, 86)) if role == "retraite" \
                else int(rng.integers(20, 65))
            H.append(Habitant(len(H), role, classe, age, table))
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
