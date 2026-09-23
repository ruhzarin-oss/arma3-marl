"""Les 500 habitants : role, classe, age, famille, domicile, lieu de travail, horaire, sante, argent.
Chaque habitant garde son identite pour toujours, qu il soit simule ( donnee ) ou incarne dans Arma ( la bulle, E2 )."""
import weakref
import numpy as np
from . import config as C

_Ref = weakref.KeyedRef

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


# les quatre premiers postes sont ceux du moteur ( le coeur Rust ecrit 0, 1, 2 ; 3 = en mer ) ; les suivants sont ceux
# de l agenda du pays ( monde/pays/d05_agenda.py ), qui donne a chacun sa journee. Toujours AJOUTER a la fin : les codes
# deja ecrits dans une table ou un instantane ne doivent jamais changer de sens.
POSTES = ("maison", "travail", "hopital", "voyage", "trajet", "courses", "loisir", "culte", "ecole")
CODE_POSTE = {p: i for i, p in enumerate(POSTES)}
CODE_HORAIRE = {None: -1, "jour": 0, "bureau": 1, "nuit": 2, "ecole": 3, "marche": 4, "garde": 5}
HORAIRE_DE_CODE = {c: h for h, c in CODE_HORAIRE.items()}
ETATS = ("S", "E", "I", "R")
CODE_ETAT = {e: i for i, e in enumerate(ETATS)}
ROLES = tuple(C.ROLES)
CODE_ROLE = {r: i for i, r in enumerate(ROLES)}
CLASSES = ("aisee", "moyenne", "populaire")
CODE_CLASSE = {c: i for i, c in enumerate(CLASSES)}


def _agrandir(table, champs):
    """Double la capacite d une table de colonnes : une naissance ne recopie pas le pays a chaque fois."""
    neuve = table.capacite * 2
    for nom, (dt, defaut) in champs.items():
        vieille = getattr(table, nom)
        t = np.full(neuve, defaut, dt); t[:table.capacite] = vieille
        setattr(table, nom, t)
    table.capacite = neuve


def _preparer_vues(table):
    """Le cache des vues vivantes d une table : deux lectures du meme habitant, tant que l une vit, rendent le MEME
    objet. Le code ecrit pour l ancien moteur compare par identite ( `x.menage is not mg`, `x is not h` ) : sans ce
    cache, chaque lecture fabriquait un objet neuf et ces tests etaient toujours vrais, sans erreur visible."""
    vues = table.vues = {}                 # numero -> reference faible de la vue vivante
    def oublier(r, vues=vues):
        if vues.get(r.key) is r: del vues[r.key]
    table._oubli = oublier


def _sans_vues(table):
    d = table.__dict__.copy(); d.pop("vues", None); d.pop("_oubli", None)
    return d


class Table:
    """Les habitants en COLONNES : un tableau par attribut, une ligne par habitant ( la ligne est son identifiant ).

    Il n y a plus d objet par habitant ( 23/09 : ~620 octets l objet contre 72 la ligne ; un milliard d objets aurait
    demande 675 Go ). Un `Habitant` n est qu une vue sur une ligne, fabriquee a la lecture puis oubliee. Tout ce qui
    decrit un habitant vit ici ; ce qui n est pas un nombre vit dans un code ( role, classe, etat, horaire, poste )."""

    CHAMPS = {"vivant": (np.uint8, 1), "lieu": (np.int32, -1), "poste": (np.uint8, 0), "heures": (np.float64, 0.0),
              "etat": (np.uint8, 0), "gravite": (np.float64, 0.0), "faim": (np.float64, 0.0),
              "horaire": (np.int8, -1), "equipe": (np.int32, 0), "decalage": (np.float64, 0.0),
              "travail": (np.int32, -1), "domicile": (np.int32, -1), "hopital": (np.int32, -1),
              "public": (np.uint8, 0), "role": (np.int16, -1), "travaille": (np.uint8, 0),
              "age": (np.float64, 0.0), "menage": (np.int32, -1), "rang": (np.int64, -1),
              "classe": (np.uint8, 0), "jours_etat": (np.float64, 0.0), "remede": (np.uint8, 0),
              "amendes": (np.int32, 0), "incarne": (np.uint8, 0), "eleve": (np.uint8, 0)}

    def __init__(self, par_n, capacite=1024):
        self.par_n = par_n                 # les lieux par numero ( Carte.par_n )
        self.n = 0
        self.capacite = capacite
        self.noms = {}                     # les seuls noms qui ne se deduisent pas du numero ( les ministres )
        self.rang_suivant = 0              # l ordre d arrivee dans les menages
        self.menages = None                # la table des menages
        for nom, (dt, defaut) in self.CHAMPS.items(): setattr(self, nom, np.full(capacite, defaut, dt))
        _preparer_vues(self)

    def __getstate__(self): return _sans_vues(self)
    def __setstate__(self, d): self.__dict__.update(d); _preparer_vues(self)

    def ajouter(self):
        if self.n == self.capacite: _agrandir(self, self.CHAMPS)
        self.n += 1
        return self.n - 1


class TableMenages:
    """Les menages en colonnes. Les MEMBRES d un menage ne sont pas stockes : ils se retrouvent par la colonne `menage`
    des habitants, dans leur ORDRE D ARRIVEE ( colonne `rang` ) - c est lui qui donne la classe d un nouveau-ne."""

    CHAMPS = {"caisse": (np.float64, 0.0), "garde_manger": (np.float64, 0.0), "domicile": (np.int32, -1)}

    def __init__(self, habitants, capacite=1024):
        self.h = habitants
        self.par_n = habitants.par_n
        self.n = 0
        self.capacite = capacite
        self.index = None                  # ( ordre des habitants trie par menage puis rang, debuts de chaque menage )
        self.n_indexe = 0
        self.ajouts = {}                   # les arrivees depuis la construction de l index ( les naissances )
        for nom, (dt, defaut) in self.CHAMPS.items(): setattr(self, nom, np.full(capacite, defaut, dt))
        _preparer_vues(self)

    def __getstate__(self): return _sans_vues(self)
    def __setstate__(self, d): self.__dict__.update(d); _preparer_vues(self)

    def _ajouter(self):
        if self.n == self.capacite: _agrandir(self, self.CHAMPS)
        self.n += 1
        return self.n - 1

    def nouveau(self, domicile):
        m = Menage(self._ajouter(), self)
        m.domicile = domicile
        return m

    def _construire(self):
        t = self.h
        n = t.n
        m = t.menage[:n]
        dedans = np.nonzero((m >= 0) & (t.rang[:n] >= 0))[0]     # rang -1 : retire de la liste de son menage
        ordre = dedans[np.lexsort((t.rang[dedans], m[dedans]))]
        debuts = np.searchsorted(m[ordre], np.arange(self.n + 1))
        self.index, self.n_indexe, self.ajouts = (ordre, debuts), n, {}

    def rejoindre(self, hid, k):
        """Un habitant entre dans le menage k. Un nouveau venu s ajoute a la fin ; un habitant deja indexe qui change
        de menage oblige a refaire l index."""
        if self.index is None: return
        if hid < self.n_indexe: self.index = None
        else: self.ajouts.setdefault(k, []).append(hid)

    def membres_ids(self, k):
        if self.index is None: self._construire()
        ordre, debuts = self.index
        ids = ordre[debuts[k]:debuts[k + 1]].tolist() if k + 1 < len(debuts) else []
        return ids + self.ajouts.get(k, [])


def menages_inscrits(t, n):
    """La colonne des menages, avec -1 pour qui n est pas dans la LISTE de son menage. L ancien moteur tenait deux
    faits separes, le pointeur `h.menage` et la liste `menage.membres` ; le code des domaines peut les desaccorder
    ( un habitant retire de la liste avant d etre pointe ailleurs ) et les routines comptent la liste."""
    return np.where(t.rang[:n] >= 0, t.menage[:n], -1)


class _Case:
    """Une colonne d une seule case : celle d un brouillon, quel que soit le numero demande."""
    __slots__ = ("v",)
    def __init__(self, v): self.v = v
    def __getitem__(self, i): return self.v
    def __setitem__(self, i, v): self.v = v


class _Brouillon:
    """La ligne d un habitant cree par l ANCIENNE interface, `Habitant(id, role, classe, age)`, avant d avoir une table :
    ce qu on lui ecrit attend ici, et `monde.habitants.append(h)` l inscrit a son numero."""
    def __init__(self):
        for nom, (dt, defaut) in Table.CHAMPS.items(): setattr(self, nom, _Case(defaut))
        self.noms = {}
        self.menages = None                # la table de son menage, des qu on lui en donne un

    @property
    def par_n(self): return self.menages.par_n if self.menages is not None else {}


class _BrouillonMenage:
    """La ligne d un menage cree par l ANCIENNE interface, `Menage(id, domicile)`, en attente de `monde.menages.append`."""
    def __init__(self, domicile):
        self.caisse, self.garde_manger = _Case(0.0), _Case(0.0)
        self.domicile = _Case(domicile.n if domicile is not None else -1)
        self.par_n = {domicile.n: domicile} if domicile is not None else {}
        self.h, self.vue = None, None

    def membres_ids(self, k): return []


class Habitant:
    """Une VUE sur une ligne de la table : aucune donnee ici, seulement un numero et la table. Deux vues du meme
    habitant sont egales ( meme numero ) sans etre le meme objet."""
    __slots__ = ("id", "_t", "__weakref__")

    def __new__(cls, table, id=None, *ancien):
        if not isinstance(table, Table): return cls._ancien(table, id, *ancien)
        id = int(id)
        vues = table.vues
        r = vues.get(id)
        if r is not None:
            h = r()
            if h is not None: return h
        h = object.__new__(cls)
        h._t = table; h.id = id
        vues[id] = _Ref(h, table._oubli, id)
        return h

    @classmethod
    def _ancien(cls, id, role=None, classe=None, age=0):
        """L ANCIENNE interface ( le code ecrit avant les colonnes ) : un habitant hors de toute table, dont les
        ecritures attendent dans un brouillon jusqu a `monde.habitants.append(h)`."""
        h = object.__new__(cls)
        h._t = _Brouillon(); h.id = int(id)
        h.role, h.classe, h.age = role, classe, age
        return h

    def __reduce__(self): return (Habitant, (self._t, self.id))

    @classmethod
    def nouveau(cls, table, role, classe, age):
        h = cls(table, table.ajouter())
        h.role, h.classe, h.age = role, classe, age
        h.menage = None; h.domicile = None; h.travail = None; h.horaire = None; h.equipe = 0
        h.decalage = 0.0             # son quart d heure a lui : tout le monde ne part pas a la meme minute
        h.lieu = None; h.poste = "maison"     # ou il est DANS son lieu : maison, travail, hopital
        h.etat = "S"; h.jours_etat = 0.0; h.gravite = 0.0; h.remede = False; h.vivant = True
        h.faim = 0.0; h.heures_jour = 0.0; h.amendes = 0
        h.incarne = False; h.eleve = False
        return h

    def __eq__(self, autre): return isinstance(autre, Habitant) and autre.id == self.id and autre._t is self._t
    def __hash__(self): return hash(self.id)
    def __repr__(self): return f"Habitant({self.id}, {self.role})"

    # --- les nombres ---
    def _f(nom):
        return property(lambda s: float(getattr(s._t, nom)[s.id]),
                        lambda s, v: getattr(s._t, nom).__setitem__(s.id, v))

    def _i(nom):
        return property(lambda s: int(getattr(s._t, nom)[s.id]),
                        lambda s, v: getattr(s._t, nom).__setitem__(s.id, v))

    def _b(nom):
        return property(lambda s: bool(getattr(s._t, nom)[s.id]),
                        lambda s, v: getattr(s._t, nom).__setitem__(s.id, 1 if v else 0))

    age = _f("age"); faim = _f("faim"); gravite = _f("gravite"); decalage = _f("decalage")
    jours_etat = _f("jours_etat"); heures_jour = _f("heures")
    equipe = _i("equipe"); amendes = _i("amendes")
    vivant = _b("vivant"); remede = _b("remede"); incarne = _b("incarne"); eleve = _b("eleve")

    # --- les codes ---
    @property
    def role(self):
        k = self._t.role[self.id]
        return ROLES[k] if k >= 0 else None

    @role.setter
    def role(self, v):
        self._t.role[self.id] = CODE_ROLE.get(v, -1)
        self._t.public[self.id] = 1 if v in C.ROLES and C.ROLES[v][2] else 0

    @property
    def classe(self): return CLASSES[self._t.classe[self.id]]

    @classe.setter
    def classe(self, v): self._t.classe[self.id] = CODE_CLASSE[v]

    @property
    def etat(self): return ETATS[self._t.etat[self.id]]

    @etat.setter
    def etat(self, v): self._t.etat[self.id] = CODE_ETAT[v]

    @property
    def horaire(self): return HORAIRE_DE_CODE[int(self._t.horaire[self.id])]

    @horaire.setter
    def horaire(self, v): self._t.horaire[self.id] = CODE_HORAIRE[v]

    @property
    def poste(self): return POSTES[self._t.poste[self.id]]

    @poste.setter
    def poste(self, v):
        if v not in CODE_POSTE: raise ValueError(f"poste inconnu du moteur : {v!r} ( a ajouter a population.POSTES )")
        self._t.poste[self.id] = CODE_POSTE[v]

    @property
    def nom(self): return self._t.noms.get(self.id) or f"H{self.id:03d}"

    @nom.setter
    def nom(self, v): self._t.noms[self.id] = v

    # --- les lieux ( des numeros dans la carte ) ---
    def _lieu(nom):
        def lire(s):
            k = getattr(s._t, nom)[s.id]
            return s._t.par_n[k] if k >= 0 else None
        def ecrire(s, v): getattr(s._t, nom)[s.id] = v.n if v is not None else -1
        return property(lire, ecrire)

    lieu = _lieu("lieu"); travail = _lieu("travail")

    @property
    def domicile(self):
        k = self._t.domicile[self.id]
        return self._t.par_n[k] if k >= 0 else None

    @domicile.setter
    def domicile(self, v):
        self._t.domicile[self.id] = v.n if v is not None else -1
        self._t.hopital[self.id] = v.marche.n if (v is not None and v.marche is not None) else -1   # l hopital du malade

    # --- le menage ---
    @property
    def menage(self):
        k = self._t.menage[self.id]
        return Menage(int(k), self._t.menages) if k >= 0 else None

    @menage.setter
    def menage(self, v):
        t = self._t
        k = v.id if v is not None else -1
        if type(t) is _Brouillon:
            t.menage.v = k
            if v is not None: t.menages = v._mt
            return
        if t.menage[self.id] == k: return        # deja le sien : il garde sa place dans la liste ( ancien moteur )
        t.menage[self.id] = k
        if k >= 0:
            t.rang[self.id] = t.rang_suivant; t.rang_suivant += 1
            t.menages.rejoindre(self.id, k)
        else:
            t.rang[self.id] = -1
            if t.menages is not None: t.menages.index = None

    del _f, _i, _b, _lieu

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
    """Une VUE sur une ligne de la table des menages."""
    __slots__ = ("id", "_mt", "__weakref__")

    def __new__(cls, id, mt=None):
        if not isinstance(mt, TableMenages):
            return mt.vue if type(mt) is _BrouillonMenage else cls._ancien(id, mt)
        id = int(id)
        vues = mt.vues
        r = vues.get(id)
        if r is not None:
            m = r()
            if m is not None: return m
        m = object.__new__(cls)
        m.id = id; m._mt = mt
        vues[id] = _Ref(m, mt._oubli, id)
        return m

    @classmethod
    def _ancien(cls, id, domicile):
        """L ANCIENNE interface, `Menage(id, domicile)` : un menage vide hors table, jusqu a `monde.menages.append(m)`."""
        m = object.__new__(cls)
        m.id = int(id); m._mt = _BrouillonMenage(domicile); m._mt.vue = m
        return m

    def __reduce__(self): return (Menage, (self.id, self._mt))

    def __eq__(self, autre): return isinstance(autre, Menage) and autre.id == self.id and autre._mt is self._mt
    def __hash__(self): return hash(("menage", self.id))
    def __repr__(self): return f"Menage({self.id})"

    @property
    def caisse(self): return float(self._mt.caisse[self.id])

    @caisse.setter
    def caisse(self, v): self._mt.caisse[self.id] = v

    @property
    def garde_manger(self): return float(self._mt.garde_manger[self.id])

    @garde_manger.setter
    def garde_manger(self, v): self._mt.garde_manger[self.id] = v

    @property
    def domicile(self):
        k = self._mt.domicile[self.id]
        return self._mt.par_n[k] if k >= 0 else None

    @domicile.setter
    def domicile(self, v):
        self._mt.domicile[self.id] = v.n if v is not None else -1
        if type(self._mt) is _BrouillonMenage and v is not None: self._mt.par_n[v.n] = v

    @property
    def membres(self):
        """Les membres, dans leur ordre d arrivee, dans une liste neuve a chaque lecture. `habitant.menage = menage` fait
        entrer quelqu un ; pour le code ecrit avant les colonnes, `membres.append(h)` et `membres.remove(h)` ecrivent
        aussi dans la table ( voir `Membres` )."""
        t = self._mt.h
        l = Membres([Habitant(t, i) for i in self._mt.membres_ids(self.id)])
        l._m = self
        return l

    def _inscrire(self, h):
        t = h._t
        if type(t) is _Brouillon: h.menage = self; return
        t.menage[h.id] = self.id
        t.rang[h.id] = t.rang_suivant; t.rang_suivant += 1
        self._mt.rejoindre(h.id, self.id)

    def _retirer(self, h):
        t = h._t
        if type(t) is _Brouillon or t.menage[h.id] != self.id: return
        t.rang[h.id] = -1                   # il pointe encore vers ce menage, mais n est plus dans sa liste
        self._mt.index = None

    def adultes(self):
        return [h for h in self.membres if h.role not in ("enfant",) and h.vivant]


class Membres(list):
    """La liste des membres d un menage. L ancien moteur la tenait a la main ; ici `append` et `remove` l ecrivent
    dans la table : `append` inscrit ( a la fin de la liste ), `remove` retire de la liste sans changer le pointeur
    `h.menage` - exactement l etat que l ancien moteur laissait entre les deux lignes d un demenagement."""
    __slots__ = ("_m",)

    def append(self, h):
        if h in self: return
        list.append(self, h); self._m._inscrire(h)

    def remove(self, h):
        list.remove(self, h); self._m._retirer(h)


class Population:
    """Les habitants du pays, sans un seul objet stocke : chaque lecture fabrique une vue. `len`, l indexation et
    l iteration marchent comme sur une liste ; `append` ne fait rien ( la ligne existe deja )."""
    __slots__ = ("_t",)

    def __init__(self, table): self._t = table
    def __len__(self): return self._t.n

    def __getitem__(self, i):
        n = self._t.n
        if isinstance(i, slice): return [Habitant(self._t, k) for k in range(*i.indices(n))]
        i = int(i)
        if i < 0: i += n
        if not 0 <= i < n: raise IndexError(i)
        return Habitant(self._t, i)

    def __iter__(self):
        t = self._t
        return (Habitant(t, i) for i in range(t.n))

    def append(self, h):
        """Ne fait rien pour un habitant deja dans la table ; inscrit a son numero un habitant cree par l ancienne
        interface ( `Habitant(id, role, classe, age)` ), qui doit etre le suivant."""
        b = h._t
        if type(b) is not _Brouillon: return
        t = self._t
        if h.id != t.n: raise ValueError(f"habitant {h.id} ajoute a la ligne {t.n} : les numeros doivent se suivre")
        i = t.ajouter()
        for nom in Table.CHAMPS: getattr(t, nom)[i] = getattr(b, nom).v
        t.rang[i] = -1
        if b.noms: t.noms[i] = b.noms[h.id]
        h._t = t
        t.vues[i] = _Ref(h, t._oubli, i)
        k = int(b.menage.v)
        if k >= 0:
            t.rang[i] = t.rang_suivant; t.rang_suivant += 1
            t.menages.rejoindre(i, k)


class Menages:
    """Les menages du pays, sans objet stocke."""
    __slots__ = ("_mt",)

    def __init__(self, mt): self._mt = mt
    def __len__(self): return self._mt.n

    def __getitem__(self, i):
        n = self._mt.n
        if isinstance(i, slice): return [Menage(k, self._mt) for k in range(*i.indices(n))]
        i = int(i)
        if i < 0: i += n
        if not 0 <= i < n: raise IndexError(i)
        return Menage(i, self._mt)

    def __iter__(self):
        mt = self._mt
        return (Menage(k, mt) for k in range(mt.n))

    def append(self, m):
        """Inscrit a son numero un menage cree par l ancienne interface ( `Menage(id, domicile)` ), qui doit etre le
        suivant ; ne fait rien pour un menage deja dans la table."""
        b = m._mt
        if type(b) is not _BrouillonMenage: return
        mt = self._mt
        if m.id != mt.n: raise ValueError(f"menage {m.id} ajoute a la ligne {mt.n} : les numeros doivent se suivre")
        k = mt._ajouter()
        mt.caisse[k], mt.garde_manger[k], mt.domicile[k] = b.caisse.v, b.garde_manger.v, b.domicile.v
        m._mt = mt
        mt.vues[k] = _Ref(m, mt._oubli, k)


def generer(carte, rng, echelle=1.0, table=None):
    """Cree la population et ses menages, deterministe a graine fixee. `echelle` multiplie chaque metier : le pays
    garde ses proportions, il change de taille."""
    table = table if table is not None else Table(carte.par_n)
    mt = TableMenages(table); table.menages = mt
    H = Population(table)
    for role, (n, classe, _) in C.ROLES.items():
        for _ in range(max(1, int(round(n * echelle)))):
            age = int(rng.integers(6, 18)) if role == "enfant" else int(rng.integers(65, 86)) if role == "retraite" \
                else int(rng.integers(20, 65))
            Habitant.nouveau(table, role, classe, age)
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
    M = Menages(mt)
    for h in H:
        if h.role not in ("enfant", "retraite"):
            h.menage = mt.nouveau(h.domicile)
    for h in H:
        if h.role in ("enfant", "retraite"):
            m = M[int(rng.integers(0, len(M)))]
            h.menage = m; h.domicile = m.domicile
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
