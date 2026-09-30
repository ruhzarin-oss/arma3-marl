"""Les 500 habitants : role, classe, age, famille, domicile, lieu de travail, horaire, sante, argent.
Chaque habitant garde son identite pour toujours, qu il soit simule ( donnee ) ou incarne dans Arma ( la bulle, E2 )."""
import importlib, math, weakref
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
    "hotellerie": (("capitale", "ville", "village"), "garde"),   # un hotel tourne jour et nuit : trois equipes ( 27/09 :
                                                                 # a l horaire du marche, 8 h - 19 h, le menage ne pouvait plus faire ses courses )
    # 27/09 ( population copiee sur le reel, `generer( ..., demographie=... )` ) : ceux qui ne travaillent pas. Le petit
    # enfant ( 0-5 ans ) reste a la maison ; l etudiant ( 18 ans et plus ) va aux cours dans la capitale de son marche,
    # comme l enfant a l ecole ; le chomeur et l inactif ( au foyer, decourage ) n ont ni lieu ni horaire de travail.
    "petit_enfant": ((), None), "etudiant": (("capitale",), "ecole"), "chomeur": ((), None), "inactif": ((), None),
}
SALAIRE_HORAIRE = {   # drachmes par heure travaillee ( public : paye par l Etat ; prive : par l entreprise )
    "chef_gouvernement": 30, "ministre": 22, "officier": 16, "soldat": 7, "policier": 9, "medecin": 20, "infirmier": 10,
    "enseignant": 10, "ouvrier": 8, "mineur": 9, "petrolier": 9, "convoyeur": 7, "marchand": 0, "paysan": 0, "patron": 0,
    "hotellerie": 6,     # 27/09 : salaire brut moyen de l hebergement et de la restauration, ~ 1 100 euros ( ERGANI 2023, a calibrer )
}
PENSION_JOUR = 20     # retraite versee par l Etat


# les quatre premiers postes sont ceux du moteur ( le coeur Rust ecrit 0, 1, 2 ; 3 = en mer ) ; les suivants sont ceux
# de l agenda du pays ( monde/pays/d05_agenda.py ), qui donne a chacun sa journee. Toujours AJOUTER a la fin : les codes
# deja ecrits dans une table ou un instantane ne doivent jamais changer de sens.
POSTES = ("maison", "travail", "hopital", "voyage", "trajet", "courses", "loisir", "culte", "ecole")
CODE_POSTE = {p: i for i, p in enumerate(POSTES)}
CODE_HORAIRE = {None: -1, "jour": 0, "bureau": 1, "nuit": 2, "ecole": 3, "marche": 4, "garde": 5}
HORAIRES_NOMS = tuple(k for k in CODE_HORAIRE if k is not None)      # code -> nom ( au_travail_ligne )
HORAIRE_DE_CODE = {c: h for h, c in CODE_HORAIRE.items()}
RESIDENT, ABSENT = 0, 1                  # la colonne « statut »
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
              "amendes": (np.int32, 0), "incarne": (np.uint8, 0), "eleve": (np.uint8, 0),
              # l identite ( archipel, 24/09 ) : carte d identite = numero d archipel + nationalite ; passeport
              "nia": (np.int64, -1), "nationalite": (np.int8, -1),
              "passeport": (np.int64, -1), "passeport_ile": (np.int8, -1),
              "passeport_emis_j": (np.int32, -1), "passeport_fin_j": (np.int32, -1),
              # 0 resident ; 1 ABSENT : son corps est ailleurs ( en mer, ou dans une autre ile ), ici il n est qu un
              # dossier - il ne mange pas a la maison, ne meurt pas, ne concoit pas, ne tombe pas malade ici
              "statut": (np.uint8, 0)}

    def __init__(self, par_n, capacite=1024):
        self.par_n = par_n                 # les lieux par numero ( Carte.par_n )
        self.n = 0
        self.capacite = capacite
        self.noms = {}                     # les seuls noms qui ne se deduisent pas du numero ( les ministres )
        self.rang_suivant = 0              # l ordre d arrivee dans les menages
        self.menages = None                # la table des menages
        self.code_ile = 0                  # le code de l ile de ce monde ( config.ILES_ARCHIPEL ) : il entre dans les numeros
        self.n_passeports = 0              # les passeports delivres par cette ile ( leur numero en suit le compte )
        for nom, (dt, defaut) in self.CHAMPS.items(): setattr(self, nom, np.full(capacite, defaut, dt))
        _preparer_vues(self)

    def __getstate__(self): return _sans_vues(self)
    def __setstate__(self, d): self.__dict__.update(d); _preparer_vues(self)

    def ajouter(self):
        if self.n == self.capacite: _agrandir(self, self.CHAMPS)
        i = self.n
        self.n += 1
        self.identifier(i)
        return i

    def identifier(self, i):
        """La carte d identite d un habitant ne ici : son numero d archipel ( jamais reutilise ) et sa nationalite."""
        self.nia[i] = (self.code_ile << C.BITS_NUMERO_LOCAL) | i
        self.nationalite[i] = self.code_ile


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
        self.ajouts = {}                   # les arrivees depuis la construction de l index, dans leur ordre
        self.sortis = set()                # les habitants indexes dont l entree de l index n est plus juste
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
        self.index, self.n_indexe, self.ajouts, self.sortis = (ordre, debuts), n, {}, set()

    # L index se tient A JOUR sans se refaire ( 24/09 : chaque changement de menage le refaisait en entier - 13 834 fois
    # pour installer 30 000 habitants, un cout qui croissait comme le carre de la population ). Un habitant qui quitte
    # la liste d un menage est note `sorti` ( son entree de l index ne compte plus ) ; qui y entre s ajoute a la fin
    # des arrivees de ce menage - son rang est le plus recent, l ordre d arrivee est garde.
    def rejoindre(self, hid, k):
        """Un habitant entre dans la liste du menage k, a la fin."""
        if self.index is None: return
        if hid < self.n_indexe: self.sortis.add(hid)
        self.ajouts.setdefault(k, []).append(hid)

    def quitter(self, hid, k):
        """Un habitant sort de la liste du menage k."""
        if self.index is None: return
        if hid < self.n_indexe: self.sortis.add(hid)
        a = self.ajouts.get(k)
        if a and hid in a: a.remove(hid)

    def membres_ids(self, k):
        if self.index is None or len(self.sortis) > max(4096, self.n_indexe // 4): self._construire()
        ordre, debuts = self.index
        ids = ordre[debuts[k]:debuts[k + 1]].tolist() if k + 1 < len(debuts) else []
        if self.sortis: ids = [i for i in ids if i not in self.sortis]
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
    nia = _i("nia"); passeport = _i("passeport"); passeport_fin_j = _i("passeport_fin_j")
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
    def nationalite(self):
        k = int(self._t.nationalite[self.id])
        return C.ILES_ARCHIPEL[k] if k >= 0 else None

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
        ancien = int(t.menage[self.id])
        if ancien == k: return                   # deja le sien : il garde sa place dans la liste ( ancien moteur )
        if ancien >= 0 and t.rang[self.id] >= 0 and t.menages is not None: t.menages.quitter(self.id, ancien)
        t.menage[self.id] = k
        if k >= 0:
            t.rang[self.id] = t.rang_suivant; t.rang_suivant += 1
            t.menages.rejoindre(self.id, k)
        else:
            t.rang[self.id] = -1

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


def au_travail_ligne(t, i, heure):
    """`Habitant.au_travail` lu directement dans la table ( 27/09 ) : pour un domaine qui interroge un habitant a la fois,
    sans fabriquer sa vue. Meme logique, memes nombres."""
    heure = heure - float(t.decalage[i]) / 60.0
    hor = int(t.horaire[i])
    if hor < 0 or not t.vivant[i] or t.etat[i] == CODE_ETAT["I"] and float(t.gravite[i]) > 0.5: return False
    if hor == CODE_HORAIRE["garde"]:        # trois equipes de 8 h : 6-14, 14-22, 22-6
        debut = (6, 14, 22)[int(t.equipe[i]) % 3]
        return (heure - debut) % 24 < 8
    a, b = C.HORAIRES[HORAIRES_NOMS[hor]]
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
        ancien = int(t.menage[h.id])
        if ancien >= 0 and t.rang[h.id] >= 0: self._mt.quitter(h.id, ancien)
        t.menage[h.id] = self.id
        t.rang[h.id] = t.rang_suivant; t.rang_suivant += 1
        self._mt.rejoindre(h.id, self.id)

    def _retirer(self, h):
        t = h._t
        if type(t) is _Brouillon or t.menage[h.id] != self.id: return
        t.rang[h.id] = -1                   # il pointe encore vers ce menage, mais n est plus dans sa liste
        self._mt.quitter(h.id, self.id)

    def adultes(self):
        return [h for h in self.membres if h.role not in ("enfant", "petit_enfant") and h.vivant]


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
        if t.nia[i] < 0: t.identifier(i)            # un nouveau-ne recoit sa carte d identite en entrant dans la table
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


# l epargne de depart d un adulte selon sa classe, en drachmes ( monde E1 )
EPARGNE_DEPART = {"aisee": 3000.0, "moyenne": 800.0, "populaire": 250.0}

# le metier de repli d un metier sans lieu dans ce pays ( on descend la chaine jusqu a un metier possible )
SUBSTITUTS = {"petrolier": "ouvrier", "mineur": "ouvrier", "ouvrier": "paysan", "soldat": "policier",
              "officier": "policier"}


def metier_possible(carte, role):
    types, _ = TRAVAIL[role]
    if not types: return True
    if types == ("gouvernement",): return True
    return bool(carte.de_type(*types))


# ================================================================== les metiers de chaque ile ( 27/09, HMT-126 b )
# Un metier industriel n a que les postes des sites de SON ile. Le monde E1 donnait a toute ile le melange de metiers
# d Altis, et les metiers sans site passaient a un metier de repli ( SUBSTITUTS ) : Stratis ( une fonderie ; ni mine,
# ni puits, ni centrale ) portait a l echelle 20 1 900 ouvriers pour les 120 postes de sa fonderie, a l arret faute
# d electricite ( 99,7 % payes 0 au jour 100 : session du moteur, 27/09 ). Les postes d un site, par unite d echelle,
# sont ceux qui font le melange d E1 sur la carte d Altis : 40 mineurs pour une mine et trois carrieres, 15 petroliers
# pour un puits, 40 ouvriers ( config.OUVRIERS_PAR_SITE ). Altis porte donc deja ses metiers : sur Altis, et sur toute
# carte dont Altis est la premiere ile ( les autres iles n y ajoutent pas de site industriel ), rien ne change au bit.
POSTES_PAR_SITE = {"mineur": {"mine": 10, "carriere": 10}, "petrolier": {"puits": 15}, "ouvrier": C.OUVRIERS_PAR_SITE}
# Ceux que les sites n emploient pas ( les postes LIBERES, d ou qu ils viennent : industrie sans site, raffinerie a
# son effectif reel, convoyeurs au reel ) travaillent dans les metiers OUVERTS de l ile ( ceux dont le lieu de travail y
# existe ), de sorte que ces metiers prennent la structure ANNUELLE de l emploi reel de la GRECE. Le surplus remplit
# d abord les metiers les plus en dessous de leur part reelle ( remplissage par le bas, `_vers_le_reel` ) : le melange
# d E1 a deja 110 paysans pour 20 marchands, trois fois la part agricole du reel ; un partage au prorata aurait encore
# gonfle l agriculture ( Stratis : 48 % de l emploi agricole contre 34 %, mesure du 27/09 ). Emploi de la Grece, moyenne
# ANNUELLE des quatre trimestres, en milliers de personnes de 15-74 ans en 2024 ( Eurostat lfsa_egan2 ) : agriculture et
# peche ( A ) 467,8, soit 11,0 % de l emploi ( 4 265,9 ) ; commerce ( G ) 712,9, soit 16,7 % ; transport ( H ) 240,4 ;
# hebergement et restauration ( I ) 398,8. 30/09 ( HMT-179 ) : la cible etait celle d une region d iles, l Egee du Nord
# ( EL41, lfst_r_lfe2en2 : A 15,3 et G-I 21,9 milliers sur 77,6 ) ; elle donnait a l agriculture 57 % du surplus
# ( A / G = 1,32, contre 0,66 en Grece ) et 36 a 43 % d emploi agricole a la naissance sur les iles, contre 11 % en
# Grece. Le pays simule est compare a la Grece ( ressemblance.py ) : sa cible est nationale.
# 29/09 ( HMT-140 ) : le partage precedent venait des personnes occupees des unites locales ( Eurostat sbs_r_nuts2021 ),
# qui comptent les saisonniers : l hebergement-restauration y pese 1,82 fois sa moyenne annuelle ( 725 726 contre
# 398 800 en Grece ), et la cible donnait a l hotellerie 31 % des postes ouverts ( 14,8 % de l emploi de l Egee du Nord,
# contre 9,35 % pour la Grece en moyenne annuelle ). L HOTELLERIE NE RECOIT PAS de postes liberes a la naissance : dans
# le moteur elle n est que le tourisme saisonnier du domaine 28, qui embauche son personnel a la saison ( occupation des
# lits de 0,08 en janvier a 0,93 en aout ) - c est le dessein d E1 ( config.ROLES : effectif 0 a la naissance, « on y
# entre par l embauche » ). Un hotelier ne en surplus etait un chomeur d hiver ( bras « effectif reel » de la raffinerie :
# +3,3 points de chomage ). Les CONVOYEURS non plus : ils ont leur regle au reel ( convoyeurs_au_reel, 4,4 pour 1 000
# habitants ) et ne se recreent pas par le surplus. Restent l agriculture et la peche ( A ) et le commerce ( G ), les
# metiers non saisonniers ouverts du moteur ; construction ( F, 5,7 ), transport hors fret ( H, taxis, cars, ports ),
# hebergement-restauration hors tourisme ( I, cafes et tavernes des habitants ), services aux entreprises ( M-N, 4,6 ) et
# autres services ( R-U, 4,2 ) n ont pas de metier dans le moteur : leur part se reporte sur ces deux ( a calibrer ).
# La peche est faite par les paysans des villages cotiers ( domaine 9 ). Si les sites d une ile demandent PLUS de bras
# que le melange d E1 ( Enoch : 7 centrales, 13 fonderies ), l industrie les prend aux metiers ouverts les plus
# au-dessus de leur part reelle ( remplissage par le haut ) : la taille du pays reste celle que fixe l echelle.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_egan2?geo=EL&time=2024&sex=T&age=Y15-74&unit=THS_PER
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfst_r_lfe2en2?geo=EL41&time=2024&age=Y15-74&sex=T&unit=THS_PER
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sbs_r_nuts2021?geo=EL&time=2023&indic_sbs=EMP_LOC_NR
PARTS_ANNUELLES = {"paysan": 467.8, "marchand": 712.9, "convoyeur": 240.4,
                   "hotellerie": 398.8}      # la structure annuelle des quatre metiers en Grece ( pour memoire )
ACCUEIL = {r: PARTS_ANNUELLES[r] for r in ("paysan", "marchand")}   # ceux qui recoivent des postes liberes
# Les hotels et restaurants d une ile : ou sont ses lits touristiques ( domaine 28, POIDS_LIEU : la capitale et ses
# plages, les villes, les villages ). Un poste d hotellerie ne en surplus va la ou sont les lits.
POIDS_HOTELLERIE = {"capitale": 4, "ville": 2, "village": 1}


# 28/09 ( HMT-126 b, suite ) : le patron du monde E1 possede une entreprise privee du moteur ( un site de production
# hors ferme : Monde.__init__ les lui donne au tour de role ) ; son seul revenu est le dividende de ses entreprises
# ( domaine 3, REVENU_PATRON_J pour le revenu attendu ). Huit patrons par unite d echelle pour les douze sites d Altis :
# a l echelle 20, 160 patrons pour 12 entreprises, 148 sans rien, et 100 % payes 0. Un patron par entreprise au plus
# ( un petit monde en a moins : un patron y possede plusieurs sites, comme Altis a l echelle 1, 8 pour 12 ) ; les
# autres sont des commercants independants, des marchands. Le reel : les employeurs sont 7,3 % de l emploi grec
# ( 312 600 sur 4 265 900 en 2024, Eurostat lfsa_egaps, SELF_S ), les independants sans salarie 19,7 % ; ce sont de
# petites entreprises, surtout du commerce et de la restauration, que le moteur n a pas : son independant du commerce
# est le marchand ( d04 : INDEPENDANTS ). Le compte des independants ( patrons, marchands, paysans ) ne change pas.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_egaps?geo=EL&time=2024&sex=T&age=Y15-74&unit=THS_PER
PATRON_SANS_ENTREPRISE = "marchand"


def entreprises_privees(carte):
    """Les entreprises privees du moteur sur cette carte : un site de production qui n est pas une ferme ( les memes que
    Monde.__init__, qui en donne une a chaque patron au tour de role )."""
    return len(carte.de_type(*[t for t in C.RECETTES if t != "ferme"]))


def postes_des_sites(carte, role):
    """Les postes d un metier industriel sur cette carte, par unite d echelle : la somme des postes de ses sites."""
    par_site = POSTES_PAR_SITE[role]
    return sum(par_site[l.type] for l in carte.de_type(*par_site))


def _vers_le_reel(c, w, total):
    """Des effectifs `c` ( flottants ) menes a la somme `total` en se rapprochant des parts `w` sans jamais aller contre :
    si total > somme( c ), f = max( c, l w ) ( on n enleve a personne ) ; sinon f = min( c, l w ) ( on n ajoute a
    personne ) ; l par dichotomie ( 200 pas, deterministe ). Rend f ( flottants, somme total )."""
    c = np.asarray(c, np.float64); w = np.asarray(w, np.float64)
    haut_ = total > c.sum()
    f = (lambda l: np.maximum(c, l * w)) if haut_ else (lambda l: np.minimum(c, l * w))
    lo, hi = 0.0, 1.0
    while f(hi).sum() < total: hi *= 2.0
    for _ in range(200):
        mi = 0.5 * (lo + hi)
        if f(mi).sum() < total: lo = mi
        else: hi = mi
    return f(hi)


def effectifs(carte, echelle, entiers=True):
    """{ metier de config.ROLES : effectif a la naissance } sur CETTE carte, a cette echelle ( sans tirage ). Chaque
    metier du monde E1 a son effectif a l echelle ( au moins 1, comme toujours ) ; un metier industriel a les postes de
    ses sites ( 0 sans site ) ; un patron a au moins une entreprise privee, les autres sont marchands
    ( PATRON_SANS_ENTREPRISE ) ; la difference de l industrie va aux metiers ouverts de l ile les plus en dessous de leur
    part reelle ( ACCUEIL ), ou est prise a ceux qui sont le plus au-dessus ( _vers_le_reel ). La somme ne change pas : la taille du pays est celle de
    l echelle. Les metiers publics et militaires restent ceux d E1 ( SUBSTITUTS pour une ile sans base ). Avec
    `entiers=False`, les memes parts sans arrondi ( des poids : sur Altis, exactement les effectifs de config.ROLES )."""
    arrondi = (lambda x: max(1, int(round(x))) if x else 0) if entiers else float
    eff = {r: arrondi(n * echelle) for r, (n, _, _) in C.ROLES.items()}
    surplus = 0
    for r in POSTES_PAR_SITE:
        k = arrondi(postes_des_sites(carte, r) * echelle)
        surplus += eff[r] - k
        eff[r] = k
    garde = min(eff["patron"], entreprises_privees(carte))      # un patron a au moins une entreprise ( 28/09 )
    eff[PATRON_SANS_ENTREPRISE] += eff["patron"] - garde
    eff["patron"] = garde
    ouverts = [r for r in ACCUEIL if metier_possible(carte, r)]
    if surplus and ouverts:
        c = [float(eff[r]) for r in ouverts]
        f = _vers_le_reel(c, [ACCUEIL[r] for r in ouverts], max(0.0, sum(c) + surplus))
        d = f - np.asarray(c)                                   # ajouts ( surplus ) ou retraits ( manque ), flottants
        if entiers:
            k = int(round(abs(d.sum())))
            d = np.sign(surplus) * _quotas(k, np.abs(d))
        for r, x in zip(ouverts, d.tolist()): eff[r] += int(x) if entiers else x
    return eff


def _lieux_ponderes(carte, role):
    """Les lieux de travail d un metier, chacun repete selon ses postes ( divises par leur plus grand diviseur commun ) :
    la repartition au tour de role pourvoit chaque site au prorata de ses postes. Des postes egaux ( mines et
    carrieres ) donnent la liste simple des lieux, dans l ordre de la carte ( celle du monde E1 )."""
    types, _ = TRAVAIL[role]
    lieux = carte.de_type(*types)
    poids = POSTES_PAR_SITE.get(role) or (POIDS_HOTELLERIE if role == "hotellerie" else None)
    if poids is None or not lieux: return lieux
    g = 0
    for l in lieux: g = math.gcd(g, int(poids[l.type]))
    return [l for l in lieux for _ in range(int(poids[l.type]) // g)]


# ================================================================== l industrie au reel ( 29/09, HMT-140 cause 5, suite )
# Le monde E1 donne 40 mineurs et 40 ouvriers par unite d echelle ( 500 habitants ) : a 10 000 habitants, Altis emploie
# 735 personnes a ses six sites de d10 ( une mine, trois carrieres, deux fonderies ), 7 % de sa population, pour 0,15 a
# 3,8 heures payees par personne et par jour ( session du moteur, 29/09 : 120 jours, graine 71 ). Le reel : 1,5 % de
# l emploi grec ( B, C24, C25 ). Chaque site a desormais, par unite d echelle, le PLUS GRAND de deux niveaux, pour ne pas
# affamer un site qui travaille :
#  - le REEL : la part de son secteur dans l emploi de la Grece en 2024 ( Eurostat lfsa_egan22d, milliers de personnes de
#    15-74 ans, 4 265,9 en tout ) - mine : minerais metalliques ( B07 ) 2,3 ; carriere : autres industries extractives
#    ( B08 ) 4,6 ; fonderie : metallurgie ( C24 ) 17,1 et produits metalliques ( C25 ) 47,3, car la fonderie du moteur
#    est une acierie integree avec forge et usinage ( d10, PLAN_ALTIS ). La part, portee aux 306 travailleurs civils d une
#    unite d echelle ( config.ROLES ), se partage entre les sites du type sur Altis ;
#  - le TRAVAIL FOURNI : les heures payees par jour du calendrier ( jours 11 a 120 ; le site du type qui travaille le plus,
#    sur les deux mesures du moteur, avant et apres la reparation du demarrage ) en emplois a plein temps de 1 880 heures
#    par an ( OCDE, comme d10 ; un site ferme le samedi, le dimanche et les feries : 8 heures par jour compteraient un
#    ouvrier qui travaille 7 jours sur 7 ), rapportees aux nes : le recensement du domaine 4 ne laisse a son poste qu une
#    partie des nes ( mine : 136 des 200 ).
# Mine : travail 4,94 par unite ( reel 0,17 ) ; carriere : travail 0,83 ( reel 0,11 ) ; fonderie : reel 2,31 ( travail
# 1,40 ). A 10 000 habitants : 99 a la mine, 17 par carriere, 46 par fonderie, soit 241 au lieu de 1 040.
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_egan22d?geo=EL&time=2024&sex=T&age=Y15-74&unit=THS_PER
EMPLOI_GRECE_2024 = 4265.9
EMPLOI_SECTEUR_2024 = {"mine": 2.3, "carriere": 4.6, "fonderie": 17.1 + 47.3}
SITES_D_ALTIS = {"mine": 1, "carriere": 3, "fonderie": 2}
# le site qui travaille le plus : heures payees par jour, equipe moyenne, nes ( Altis a l echelle 20 )
TRAVAIL_MESURE = {"mine": (345.3, 135.8, 200), "carriere": (58.4, 137.3, 200), "fonderie": (98.0, 81.8, 120)}
ECHELLE_MESURE = 20.0
HEURES_PLEIN_TEMPS_J = 1880.0 / 365.0
CIVILS_E1 = sum(k for r, (k, _, _) in C.ROLES.items() if r not in ("enfant", "retraite", "soldat", "officier"))
LONGUEUR_SUITE = 1 << 16      # au-dela ( plus de ~ 65 000 travailleurs d un metier ), la suite recommence


def postes_reels(t):
    """Les postes d un site de d10 ( mine, carriere, fonderie ) par unite d echelle : max( reel, travail fourni )."""
    reel = EMPLOI_SECTEUR_2024[t] / EMPLOI_GRECE_2024 * CIVILS_E1 / SITES_D_ALTIS[t]
    h, equipe, nes = TRAVAIL_MESURE[t]
    return max(reel, h / HEURES_PLEIN_TEMPS_J * nes / equipe / ECHELLE_MESURE)


def _suite_des_postes(lieux, poids, longueur=LONGUEUR_SUITE):
    """Les lieux dans l ordre ou ils recoivent leurs postes : un chacun d abord ( dans l ordre de la carte ), puis au plus
    fort quotient poids / ( 2 s + 1 ), s les postes deja recus ( Sainte-Lague ) ; a egalite, le premier de la carte. Chaque
    prefixe est un partage au prorata des poids, a une personne pres : le tour de role de la generation ( les N premiers
    de la liste ) pourvoit chaque site comme ses postes, a toute echelle, meme avec des postes non entiers."""
    w = np.asarray(poids, np.float64)
    m = np.floor(longueur * w / w.sum()).astype(np.int64) + 3
    site = np.repeat(np.arange(len(w)), m)
    rang = np.concatenate([np.arange(k) for k in m.tolist()])
    prio = np.where(rang == 0, np.inf, w[site] / (2.0 * rang + 1.0))
    ordre = np.lexsort((site, -prio))[:longueur]
    return [lieux[i] for i in site[ordre].tolist()]


_SUITES = {}


def _suite_en_cache(lieux, poids):
    """_suite_des_postes, gardee pour les memes lieux ( les memes objets, tenus par le cache ) et les memes poids."""
    cle = (tuple(id(l) for l in lieux), tuple(float(x) for x in poids))
    v = _SUITES.get(cle)
    if v is None:
        if len(_SUITES) >= 16: _SUITES.pop(next(iter(_SUITES)))
        v = _SUITES[cle] = (tuple(lieux), _suite_des_postes(lieux, poids))
    return v[1]


POSTES_REELS = {t: postes_reels(t) for t in SITES_D_ALTIS}
POSTES_PAR_SITE["mineur"] = {**POSTES_PAR_SITE["mineur"], "mine": POSTES_REELS["mine"], "carriere": POSTES_REELS["carriere"]}
POSTES_PAR_SITE["ouvrier"] = {**POSTES_PAR_SITE["ouvrier"], "fonderie": POSTES_REELS["fonderie"]}   # la raffinerie : inchangee

_lieux_avant_industrie = _lieux_ponderes


def _lieux_aux_postes(carte, role, *n):
    """`_lieux_ponderes` ( la fonction d avant ) ; des postes non entiers ( les sites de d10 au reel ) sans effectif donne :
    la suite de Sainte-Lague, dont chaque prefixe est au prorata des postes. Un effectif donne ( le bras de la raffinerie
    partage lui-meme au plus fort reste ) ou des postes entiers gardent la fonction d avant."""
    poids = POSTES_PAR_SITE.get(role)
    if poids is None or (n and n[0] is not None): return _lieux_avant_industrie(carte, role, *n)
    lieux = carte.de_type(*TRAVAIL[role][0])
    if not lieux or all(float(poids[l.type]).is_integer() for l in lieux): return _lieux_avant_industrie(carte, role, *n)
    return _suite_en_cache(lieux, [poids[l.type] for l in lieux])


_lieux_ponderes = _lieux_aux_postes

# ================================================================== les convoyeurs au reel ( 29/09, HMT-140 cause 5 )
# Le monde E1 donne 25 convoyeurs pour 500 habitants ( config.ROLES ), 50 pour 1 000 : a 10 000 habitants, Altis lance
# 56 convois de 4,7 km par jour, 51 heures de conduite, et laisse ~ 350 de ses ~ 440 convoyeurs sans travail des le jour
# 5 ( mesure du 29/09, tronc 72f0873 ). Le reel : le fret routier et le demenagement ( NACE H49.4 ) emploient 45 591
# personnes en Grece en 2024 ( Eurostat sbs_sc_ovw ; 37 183 en 2019, sbs_na_1a_se_r2 ) pour 10 375 764 habitants
# ( demo_pjan ) : 4,4 pour 1 000 habitants, 1,07 % de l emploi. Au moins un convoyeur par marche : sans chauffeur a sa
# capitale, aucun convoi n y part. Les autres sont verses aux metiers ouverts par le meme remplissage vers la structure
# reelle ANNUELLE que les bras de l industrie ( population.ACCUEIL : agriculture et commerce ; ni l hotellerie,
# saisonniere, que le domaine 28 embauche a la saison, ni les convoyeurs, qui ne se recreent pas ).
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sbs_sc_ovw?geo=EL&nace_r2=H494&indic_sbs=EMP_NR&size_emp=TOTAL
CONVOYEURS_POUR_MILLE = 1000.0 * 45591 / 10375764
# ( 30/09 ) 4,4 pour 1 000 est un ratio d EMPLOI ( H49.4 : personnes occupees ) : il vaut pour les convoyeurs AU TRAVAIL
# apres le recensement du domaine 4, qui ne laisse a leur poste qu une partie des nes ( monde E1, graine 71, 10 000
# habitants, tronc e8f1ee8 : 363 convoyeurs au travail sur 500 nes ). Au mode par defaut, les nes sont la cible divisee
# par cette survie ; une population copiee sur le reel ( `habitants` donne ) nait avec son statut : nes = cible.
SURVIE_RECENSEMENT = 363 / 500
ACCUEIL_CONVOYEURS = {"paysan": 467.8, "marchand": 712.9}   # = population.ACCUEIL ( porte ) : Grece, lfsa_egan2 2024


def _metier_ouvert(carte, role):
    types = TRAVAIL[role][0]
    return not types or types == ("gouvernement",) or bool(carte.de_type(*types))


def _remplir_vers(c, w, total):
    """Le remplissage vers les parts w sans aller contre ( le meme que population._vers_le_reel )."""
    c = np.asarray(c, np.float64); w = np.asarray(w, np.float64)
    haut_ = total > c.sum()
    f = (lambda l: np.maximum(c, l * w)) if haut_ else (lambda l: np.minimum(c, l * w))
    lo, hi = 0.0, 1.0
    while f(hi).sum() < total: hi *= 2.0
    for _ in range(200):
        mi = 0.5 * (lo + hi)
        if f(mi).sum() < total: lo = mi
        else: hi = mi
    return f(hi)


def _parts_entieres(total, poids):
    """Le partage entier de total au prorata de poids, plus forts restes ( le meme que population._quotas )."""
    poids = np.asarray(poids, np.float64)
    if total <= 0 or poids.sum() <= 0: return np.zeros(len(poids), np.int64)
    x = total * poids / poids.sum()
    q = np.floor(x).astype(np.int64)
    reste = int(total) - int(q.sum())
    if reste > 0: q[np.argsort(-(x - q), kind="stable")[:reste]] += 1
    return q


def convoyeurs_au_reel(carte, eff, entiers=True, habitants=None):
    """L etape de fin des effectifs : les convoyeurs ramenes a CONVOYEURS_POUR_MILLE des habitants EN EMPLOI ( monde E1 :
    somme des effectifs, et les nes divises par SURVIE_RECENSEMENT ; `habitants` pour une population copiee sur un pays
    reel, sans correction ), au moins un par capitale, jamais plus qu avant ; le surplus aux autres metiers ouverts, vers
    la structure reelle. La somme ne change pas."""
    if "convoyeur" not in eff or eff["convoyeur"] <= 0: return eff
    eff = dict(eff)
    n = float(sum(eff.values())) if habitants is None else float(habitants)
    vise = CONVOYEURS_POUR_MILLE * n / 1000.0 / (SURVIE_RECENSEMENT if habitants is None else 1.0)
    vise = max(vise, float(len(carte.capitales)))
    k = min(eff["convoyeur"], max(1, int(round(vise))) if entiers else vise)
    surplus = eff["convoyeur"] - k
    ouverts = [r for r in ACCUEIL_CONVOYEURS if r != "convoyeur" and r in eff and _metier_ouvert(carte, r)]
    if surplus <= 0 or not ouverts: return eff
    eff["convoyeur"] = k
    c = [float(eff[r]) for r in ouverts]
    d = _remplir_vers(c, [ACCUEIL_CONVOYEURS[r] for r in ouverts], sum(c) + surplus) - np.asarray(c)
    if entiers: d = _parts_entieres(int(surplus), np.maximum(d, 0.0))
    for r, x in zip(ouverts, d.tolist()): eff[r] += int(x) if entiers else x
    return eff


_effectifs_avant_convoyeurs = effectifs
FRETS = ("e1", "d15")      # qui porte le fret : les convois du moteur ( E1 ), ou le domaine 15


def effectifs(carte, echelle, entiers=True, emploi_civil_par_habitant=None, fret="e1"):
    """Les effectifs de la generation ( la fonction d avant ), puis, si le domaine 15 porte le fret ( fret="d15", le
    monde complet ), les convoyeurs au reel en derniere etape. fret="e1" ( defaut ) : les convoyeurs d E1, au bit - les
    convois du moteur, mecanisme d essai des mondes sans domaine 15, prennent leurs chauffeurs a la capitale du marche qui
    paie et en demandent bien plus que le reel ( 29/09 : avec 3 chauffeurs a 500 habitants, 12 514 convois refuses en
    40 jours et le marche de la mine sans gazole 20 jours ). Pour une population copiee sur un pays reel,
    `emploi_civil_par_habitant` donne sa taille ( generer_reel : les postes civils sur l emploi civil par habitant ) :
    c est sur elle que se comptent les 4,4 pour 1 000."""
    if fret not in FRETS: raise ValueError(f"fret inconnu {fret!r} : {FRETS}")
    eff = _effectifs_avant_convoyeurs(carte, echelle, entiers)
    if fret == "e1": return eff
    hab = None
    if emploi_civil_par_habitant is not None:
        civils = sum(v for r, v in eff.items() if r not in ("enfant", "retraite", "soldat", "officier"))
        hab = int(round(civils / emploi_civil_par_habitant))
    return convoyeurs_au_reel(carte, eff, entiers, hab)

def generer(carte, rng, echelle=1.0, table=None, demographie=None, fret="e1"):
    """Cree la population et ses menages, deterministe a graine fixee. `echelle` multiplie chaque metier : le pays
    garde ses proportions, il change de taille. `demographie` ( None : le monde E1 ) : une population copiee sur un
    pays reel ( DEMOGRAPHIES ), voir `generer_reel`. Les metiers industriels suivent les sites de l ile ( effectifs )."""
    if demographie is not None: return generer_reel(carte, rng, echelle, table, demographie, fret)
    table = table if table is not None else Table(carte.par_n)
    mt = TableMenages(table); table.menages = mt
    H = Population(table)
    eff = effectifs(carte, echelle, fret=fret)
    for role, (n, classe, _) in C.ROLES.items():
        # 27/09 : un metier sans poste ne nait pas ( hotellerie d E1 : on y entre par l embauche ; industrie sans site )
        if eff[role] == 0: continue
        # archipel ( 24/09 ) : un pays sans le lieu d un metier public n a pas ce metier ( pas de base, pas de soldats ) ;
        # ces gens exercent le metier de repli ( SUBSTITUTS ), avec sa classe. Sur Altis, rien ne change.
        vrai = role
        while not metier_possible(carte, vrai): vrai = SUBSTITUTS[vrai]
        if vrai != role: classe = C.ROLES[vrai][1]
        for _ in range(eff[role]):
            age = int(rng.integers(6, 18)) if role == "enfant" else int(rng.integers(65, 86)) if role == "retraite" \
                else int(rng.integers(20, 65))
            Habitant.nouveau(table, vrai, classe, age)
    # lieux de travail : repartition equilibree sur les lieux du bon type
    compteur = {}
    for h in H:
        types, horaire = TRAVAIL[h.role]
        h.horaire = horaire
        if not types: continue
        if types == ("gouvernement",): cands = [carte.gouvernement]
        else: cands = _lieux_ponderes(carte, h.role)   # les ouvriers vont ou il faut des bras : la raffinerie d abord
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
        m.caisse = sum(EPARGNE_DEPART[x.classe] for x in m.adultes())
        m.garde_manger = 2.0 * len(m.membres)
    # l eleve : un enfant de la capitale du gouvernement ( Kavala sur Altis ), le plus jeune
    enfants = [h for h in H if h.role == "enfant" and h.domicile.id == carte.gouvernement.id] or [h for h in H if h.role == "enfant"]
    min(enfants, key=lambda h: (h.age, h.id)).eleve = True
    return H, M


# ================================================================== une population copiee sur le reel ( 27/09 )
# `generer( ..., demographie="grece" )` : la pyramide des ages, des menages qui sont des familles et l activite d un
# pays reel ( cibles et sources : monde/demographie_grece.py ; portes : monde/porte_population_grece.py ). L economie
# reste celle d E1 : `echelle` fixe les travailleurs CIVILS ( les metiers de config.ROLES a l echelle, meme arrondi que
# `generer` ) ; la population est ce qu il faut autour d eux pour que le taux d emploi soit celui du pays.
DEMOGRAPHIES = {"grece": "demographie_grece"}
# le motif d un inactif ou d un retraite avant l age ( colonne « motif » du recensement ) : le domaine 4 en fait un statut
MOTIFS = ("aucun", "au_foyer", "decourage", "invalide", "retraite_anticipee")
CODE_MOTIF = {m: k for k, m in enumerate(MOTIFS)}
HABITABLES = ("capitale", "ville", "village")
MILITAIRES = ("soldat", "officier")
# le metier cherche ( chomeur ) ou quitte ( inactif ) : un metier libre, au prorata des effectifs d E1 et du sexe
METIERS_LIBRES = ("paysan", "mineur", "petrolier", "ouvrier", "convoyeur")
AGE_MAJEUR, AGE_ECOLE = 18, 6          # comme au domaine 1 ( pays/d01_population.py )
# les statuts de la generation ( internes ) : ils deviennent un metier et un motif
(S_EMPLOI, S_CHOMAGE, S_ETUDES, S_FOYER, S_INVALIDE, S_RETRAITE_ANT, S_DECOURAGE, S_PETIT, S_ECOLE,
 S_RETRAITE) = range(10)


def _cibles(demographie):
    if demographie not in DEMOGRAPHIES:
        raise ValueError(f"demographie inconnue {demographie!r} : {tuple(DEMOGRAPHIES)}")
    return importlib.import_module("." + DEMOGRAPHIES[demographie], __package__)


def _quotas(total, poids):
    """Le partage entier de `total` au prorata de `poids` : les plus forts restes, a egalite le premier. Sans tirage :
    a toute taille, chaque part est a moins d une unite de sa cible."""
    poids = np.asarray(poids, np.float64)
    if total <= 0 or poids.sum() <= 0: return np.zeros(len(poids), np.int64)
    x = total * poids / poids.sum()
    q = np.floor(x).astype(np.int64)
    reste = int(total) - int(q.sum())
    if reste > 0: q[np.argsort(-(x - q), kind="stable")[:reste]] += 1
    return q


def _repli(carte, role):
    while not metier_possible(carte, role): role = SUBSTITUTS[role]
    return role


def _pyramide(rng, n, R):
    """Les ages et les sexes : chaque groupe de 5 ans de chaque sexe a son quota de la pyramide, l age tire
    uniformement dans le groupe. Rend ( age, sexe ), dans l ordre des groupes."""
    cellules = [(s, k) for s in (R.HOMME, R.FEMME) for k in range(len(R.GROUPES))]
    q = _quotas(n, [R.PYRAMIDE[s][k] for s, k in cellules])
    age = np.empty(n, np.int64); sexe = np.empty(n, np.int8); i = 0
    for (s, k), m in zip(cellules, q.tolist()):
        lo = R.GROUPES[k]
        hi = R.GROUPES[k + 1] if k + 1 < len(R.GROUPES) else R.AGE_MAX_TIRE + 1
        age[i:i + m] = lo + rng.integers(0, hi - lo, m); sexe[i:i + m] = s; i += m
    return age, sexe


def _asfr(R, ecart):
    """La fecondite a l age `ecart` ( tableau ), par la table de groupes de 5 ans."""
    ecart = np.asarray(ecart)
    out = np.zeros(ecart.shape)
    for a, f in R.ASFR.items(): out[(ecart >= a) & (ecart < a + 5)] = f
    return out


def _tirer_parents(rng, qui, age, cands, poids_cand, R, ecart_de, fratries=False):
    """Pour chaque personne de `qui` ( dans l ordre ), une personne de `cands` tiree par age : l age de l ecart
    ( `ecart_de( age du candidat, age de la personne )` ) pondere par la fecondite, fois le poids du candidat ; puis un
    candidat de l age tire, au prorata de son poids. Avec `fratries`, ceux qui ont tire le meme age de parent et la meme
    classe de poids sont groupes en fratries ( tailles FRATRIES ), une fratrie par parent : sans elles, un tirage
    independant par enfant donne des familles de Poisson, trop de familles d un enfant et de quatre. Rend les numeros
    tires ( -1 : aucun candidat ). Une passe par age : le cout suit la population, pas son carre."""
    out = np.full(qui.size, -1, np.int64)
    if not qui.size or not cands.size: return out
    amax = int(age.max()) + 1
    ac = age[cands]
    ordre = np.lexsort((cands, ac))                     # candidats groupes par age
    cands, ac, pc = cands[ordre], ac[ordre], poids_cand[ordre]
    debut = np.searchsorted(ac, np.arange(amax + 1))
    cumul = np.concatenate(([0.0], np.cumsum(pc)))
    masse = cumul[debut[1:]] - cumul[debut[:-1]]        # poids total des candidats de chaque age
    aq = age[qui]
    tire = np.full(qui.size, -1, np.int64)              # la position tiree dans `cands`
    age_tire = np.full(qui.size, -1, np.int64)
    for a in np.unique(aq).tolist():
        k = np.nonzero(aq == a)[0]
        w = _asfr(R, ecart_de(np.arange(amax), a)) * masse
        if w.sum() <= 0: continue
        u = rng.random((k.size, 2))
        x = np.minimum(np.searchsorted(np.cumsum(w), u[:, 0] * w.sum(), side="right"), amax - 1)
        # dans l age tire, au prorata du poids : la position dans le cumul des poids de cet age
        v = cumul[debut[x]] + u[:, 1] * masse[x]
        tire[k] = np.clip(np.searchsorted(cumul, v, side="right") - 1, debut[x], debut[x + 1] - 1)
        age_tire[k] = x
    if fratries:
        # par ( age du parent, poids du parent tire ) : les enfants en fratries, chaque fratrie chez un parent distinct
        # de ce groupe, tire au prorata du poids ( sans remise tant qu il en reste )
        ok = np.nonzero(tire >= 0)[0]
        cle = age_tire[ok] * 1000003 + np.rint(pc[tire[ok]] * 1000).astype(np.int64)
        ok = ok[np.argsort(cle, kind="stable")]; cle = np.sort(cle, kind="stable")
        tailles, parts = np.array([t for t, _ in R.FRATRIES]), np.cumsum([q for _, q in R.FRATRIES])
        for d, f in zip(*_tranches(cle)):
            enfants = ok[d:f][rng.permutation(f - d)]
            x = int(age_tire[enfants[0]])
            dans = np.arange(debut[x], debut[x + 1])
            dans = dans[np.rint(pc[dans] * 1000) == np.rint(pc[tire[enfants[0]]] * 1000)]
            g = tailles[np.minimum(np.searchsorted(parts, rng.random(enfants.size), side="right"), len(tailles) - 1)]
            bornes = np.minimum(np.cumsum(g), enfants.size)
            bornes = bornes[:np.searchsorted(bornes, enfants.size) + 1]
            parents = dans[rng.permutation(dans.size)]
            debuts = np.concatenate(([0], bornes[:-1]))
            for j, (b0, b1) in enumerate(zip(debuts.tolist(), bornes.tolist())):
                tire[enfants[b0:b1]] = parents[j % parents.size]
    ok = tire >= 0
    out[ok] = cands[tire[ok]]
    return out


def _tranches(cle):
    """Les ( debuts, fins ) des suites de valeurs egales d un tableau trie."""
    if not cle.size: return np.zeros(0, np.int64), np.zeros(0, np.int64)
    d = np.concatenate(([0], np.nonzero(np.diff(cle))[0] + 1))
    return d, np.append(d[1:], cle.size)


def _familles(rng, age, sexe, R):
    """Les familles d une population ( ages et sexes ) : les couples, les mineurs chez leur mere, les jeunes adultes
    chez leurs parents, des parents ages chez un enfant. Rend ( conjoint, mere, pere, hote, racine ) : `hote` est celui
    chez qui l on vit ( -1 : chez soi ), `racine` le bout de cette chaine, qui fait le menage."""
    n = len(age); F, M = R.FEMME, R.HOMME
    conj = np.full(n, -1, np.int64); mere = np.full(n, -1, np.int64); pere = np.full(n, -1, np.int64)
    hote = np.full(n, -1, np.int64)
    ages = age.tolist()
    amax = int(age.max()) + 1 if n else 1
    # 1. les couples : chaque femme en couple ( sa part par age ) epouse l homme libre dont l age est le plus proche de
    #    son age + ECART_AGE_COUPLE ( bruit normal ), a ECART_AGE_MAX ans pres ; l homme vit chez elle
    f = np.nonzero((sexe == F) & (age >= AGE_MAJEUR))[0]
    f = f[rng.random(f.size) < R.par_age(R.EN_COUPLE_FEMMES, age[f])]
    f = f[rng.permutation(f.size)]
    cible = np.rint(age[f] + R.ECART_AGE_COUPLE + rng.normal(0.0, R.ECART_AGE_SD, f.size)).astype(np.int64)
    h = np.nonzero((sexe == M) & (age >= AGE_MAJEUR))[0]
    seaux = [[] for _ in range(amax)]
    for i in h[rng.permutation(h.size)].tolist(): seaux[ages[i]].append(i)
    for i, t in zip(f.tolist(), cible.tolist()):
        for d in range(R.ECART_AGE_MAX + 1):
            j = next((x for x in ((t - d, t + d) if d else (t,)) if AGE_MAJEUR <= x < amax and seaux[x]), None)
            if j is not None:
                m = seaux[j].pop()
                conj[i], conj[m], hote[m] = m, i, i
                break
    femmes = np.nonzero((sexe == F) & (age >= AGE_MAJEUR))[0]
    poids = np.where(conj[femmes] >= 0, 1.0, R.FECONDITE_SOLO)

    def filiation(qui, meres):
        ok = meres >= 0
        qui, meres = qui[ok], meres[ok]
        mere[qui] = meres; hote[qui] = meres
        c = conj[meres]
        a_pere = (c >= 0) & (age[np.maximum(c, 0)] - age[qui] >= 18) & (age[np.maximum(c, 0)] - age[qui] <= 55)
        pere[qui[a_pere]] = c[a_pere]

    # 2. les mineurs : une mere de 15 a 49 ans a la naissance, selon la fecondite de cet age ( FECONDITE_SOLO pour une
    #    femme sans conjoint ) ; son conjoint est le pere s il a de 18 a 55 ans de plus que l enfant ( comme au domaine 1 )
    mineurs = np.nonzero(age < AGE_MAJEUR)[0]
    filiation(mineurs, _tirer_parents(rng, mineurs, age, femmes, poids, R, lambda am, a: am - a, fratries=True))
    # 3. les jeunes adultes hors couple chez leurs parents : la part publiee vaut pour TOUS les jeunes de l age ; elle se
    #    reporte sur ceux qui vivent sans conjoint
    jeunes = np.nonzero((age >= AGE_MAJEUR) & (R.par_age(R.CHEZ_LES_PARENTS, age) > 0))[0]
    if jeunes.size:
        cle = age[jeunes] * 2 + sexe[jeunes]
        tous = np.bincount(cle, minlength=2 * amax)
        seuls = np.bincount(cle[conj[jeunes] < 0], minlength=2 * amax)
        part = np.where(tous[cle] > 0, seuls[cle] / np.maximum(tous[cle], 1), 1.0)
        p = np.minimum(1.0, R.par_age(R.CHEZ_LES_PARENTS, age[jeunes]) / np.maximum(part, 1e-9))
        jeunes = jeunes[(rng.random(jeunes.size) < p) & (conj[jeunes] < 0)]
        # la situation d aujourd hui de la mere ne dit plus grand-chose de celle de la naissance ( veuve, divorcee ) :
        # toutes les femmes pesent pareil
        filiation(jeunes, _tirer_parents(rng, jeunes, age, femmes, np.ones(femmes.size), R, lambda am, a: am - a))
    # 4. les parents ages, seuls et sans personne chez eux, vivent chez un enfant ( une part par age ) : un adulte chez
    #    lui ou en couple, de 15 a 49 ans plus jeune ( 18 a 52 pour un pere ), tire comme une naissance a l envers
    heberge = np.zeros(n, bool); heberge[hote[hote >= 0]] = True
    vieux = np.nonzero((age >= 65) & (conj < 0) & (hote < 0) & ~heberge)[0]
    vieux = vieux[rng.random(vieux.size) < R.par_age(R.CHEZ_UN_ENFANT, age[vieux])]
    tetes = np.nonzero((age >= AGE_MAJEUR) & ((hote < 0) | ((conj >= 0) & (hote == conj))))[0]
    tetes = tetes[~np.isin(tetes, vieux)]
    for s, dec in ((F, 0), (M, 3)):
        qui = vieux[sexe[vieux] == s]
        enf = _tirer_parents(rng, qui, age, tetes, np.ones(tetes.size), R, lambda ae, a, dec=dec: a - ae - dec)
        ok = enf >= 0
        qui, enf = qui[ok], enf[ok]
        hote[qui] = enf
        lien = mere if s == F else pere
        libre = lien[enf] < 0
        lien[enf[libre]] = qui[libre]
    # 5. le menage de chacun : le bout de la chaine des hotes ( les ages montent le long d une chaine d enfants et
    #    descendent le long d une chaine de parents ages : aucune boucle )
    racine = np.arange(n)
    while True:
        suivant = np.where(hote[racine] >= 0, hote[racine], racine)
        if np.array_equal(suivant, racine): break
        racine = suivant
    return conj, mere, pere, hote, racine


def _activite(rng, age, sexe, menage, n_emploi, R):
    """Le statut de chacun ( S_... ). Les 0-5 ans sont petits enfants, les 6-17 ans a l ecole, les 65 ans et plus a la
    retraite. De 18 a 64 ans, par sexe et groupe de 5 ans : `n_emploi` personnes en emploi au prorata des taux d emploi
    ( quotas ), des chomeurs au taux de chomage, les autres inactifs par motif ( MOTIFS_INACTIFS ), tires."""
    n = len(age)
    statut = np.full(n, S_RETRAITE, np.int64)
    statut[age < 18] = S_ECOLE
    statut[age < AGE_ECOLE] = S_PETIT
    cellules = [(s, k, a) for s in (R.HOMME, R.FEMME) for k, a in enumerate(R.GROUPES_ACTIFS)]
    groupe = [int(((sexe == s) & (age >= a) & (age < a + 5)).sum()) for s, _, a in cellules]
    emploi = _quotas(n_emploi, [g * R.EMPLOI[s][k] for g, (s, k, _) in zip(groupe, cellules)])
    tu = np.array([R.CHOMAGE[s][k] for s, k, _ in cellules])
    chomage = _quotas(int(round(float((emploi * tu / (1.0 - tu)).sum()))), emploi * tu / (1.0 - tu))
    inactifs = []
    for (s, k, a), e, c in zip(cellules, emploi.tolist(), chomage.tolist()):
        ids = np.nonzero((sexe == s) & (age >= max(a, R.AGE_ACTIF)) & (age < a + 5))[0]
        ids = ids[rng.permutation(ids.size)]
        e = min(e, ids.size); c = min(c, ids.size - e)
        statut[ids[:e]] = S_EMPLOI; statut[ids[e:e + c]] = S_CHOMAGE
        inactifs.append(ids[e + c:])
    inactifs = np.concatenate(inactifs) if inactifs else np.zeros(0, np.int64)
    p = np.cumsum(R.motifs_inactifs(age[inactifs], sexe[inactifs]), axis=1)
    m = (rng.random(inactifs.size)[:, None] >= p).sum(axis=1).clip(0, 4)
    code = np.array([S_ETUDES, S_FOYER, S_INVALIDE, S_RETRAITE_ANT, S_DECOURAGE])[m]
    adultes = np.bincount(menage[age >= AGE_MAJEUR], minlength=int(menage.max()) + 1)
    code[(code == S_FOYER) & (adultes[menage[inactifs]] < 2)] = S_DECOURAGE     # au foyer : un autre adulte au menage
    statut[inactifs] = code
    return statut


def _metiers_par_sexe(rng, postes, sexe, R):
    """Les postes civils ( un metier par poste ) donnes aux personnes en emploi selon leur sexe : la part d hommes de
    chaque metier ( PART_HOMMES ) est decalee d un meme ecart logistique pour que le compte des hommes tombe juste ;
    hommes et femmes pris au hasard. Rend un code de metier par personne, dans l ordre de `sexe`."""
    metiers = list(dict.fromkeys(postes))
    nb = np.array([postes.count(m) for m in metiers], np.float64)
    ph = np.clip(np.array([R.PART_HOMMES.get(m, 0.5) for m in metiers]), 0.01, 0.99)
    lg = np.log(ph / (1.0 - ph))
    hommes = np.nonzero(sexe == R.HOMME)[0]; femmes = np.nonzero(sexe != R.HOMME)[0]
    lo, hi = -40.0, 40.0
    for _ in range(80):
        mi = 0.5 * (lo + hi)
        if (nb / (1.0 + np.exp(-(lg + mi)))).sum() < hommes.size: lo = mi
        else: hi = mi
    nh = np.minimum(_quotas(hommes.size, nb / (1.0 + np.exp(-(lg + lo)))), nb.astype(np.int64))
    manque = hommes.size - int(nh.sum())                  # un arrondi bute sur un metier plein : un autre le prend
    for j in np.argsort(-(nb - nh), kind="stable").tolist():
        if manque <= 0: break
        k = min(manque, int(nb[j] - nh[j])); nh[j] += k; manque -= k
    hommes = hommes[rng.permutation(hommes.size)]; femmes = femmes[rng.permutation(femmes.size)]
    out = np.full(sexe.size, -1, np.int64)
    ih = jf = 0
    for m, k, kh in zip(metiers, nb.astype(np.int64).tolist(), nh.tolist()):
        out[hommes[ih:ih + kh]] = CODE_ROLE[m]; out[femmes[jf:jf + k - kh]] = CODE_ROLE[m]
        ih += kh; jf += k - kh
    return out


def _reserver(table, champs, n):
    while table.capacite < n: _agrandir(table, champs)


def generer_reel(carte, rng, echelle, table, demographie, fret="e1"):
    """La population d un pays reel autour des travailleurs civils du monde E1. Pose `table.recensement` : ce que la
    generation sait et que les domaines relisent a leur recensement ( sexe, conjoint, mere, pere ; le metier cherche
    ou quitte des chomeurs et des inactifs ; le motif des inactifs ). Deterministe : tous les tirages par `rng`, dans
    un ordre fixe ; les habitants et les menages ecrits en colonnes, sans une vue."""
    R = _cibles(demographie)
    table = table if table is not None else Table(carte.par_n)
    mt = TableMenages(table); table.menages = mt
    # 1. les postes civils d E1 a l echelle, dans l ordre de config.ROLES ( le metier de repli du pays ) ; les metiers
    #    industriels ont les postes des sites de l ile, le reste va aux metiers ouverts ( effectifs, 27/09 )
    eff = effectifs(carte, echelle, emploi_civil_par_habitant=R.emploi_par_habitant() - R.PART_MILITAIRES, fret=fret)
    postes = []
    for role in C.ROLES:
        if eff[role] == 0 or role in ("enfant", "retraite") + MILITAIRES: continue
        postes += [_repli(carte, role)] * eff[role]
    # 2. la taille du pays : les civils sont les personnes en emploi que l armee laisse
    n = int(round(len(postes) / (R.emploi_par_habitant() - R.PART_MILITAIRES)))
    n_mil = int(round(R.PART_MILITAIRES * n))
    age, sexe = _pyramide(rng, n, R)
    conj, mere, pere, hote, racine = _familles(rng, age, sexe, R)
    _, menage = np.unique(racine, return_inverse=True)
    statut = _activite(rng, age, sexe, menage, len(postes) + n_mil, R)
    # 3. les metiers : l armee d abord ( 19-54 ans, au prorata du sexe ), puis les postes civils selon le sexe
    role = np.full(n, -1, np.int64); motif = np.zeros(n, np.int8); metier = np.full(n, -1, np.int64)
    emploi = np.nonzero(statut == S_EMPLOI)[0]
    a0, a1 = R.AGES_MILITAIRES
    cand = emploi[(age[emploi] >= a0) & (age[emploi] < a1)]
    ps = R.PART_HOMMES["soldat"]
    cle = np.log(rng.random(cand.size)) / np.where(sexe[cand] == R.HOMME, ps, 1.0 - ps)   # tirage pondere sans remise
    armee = cand[np.argsort(-cle, kind="stable")[:n_mil]]
    n_off = int(round(armee.size * R.PART_OFFICIERS))
    role[armee[:n_off]] = CODE_ROLE[_repli(carte, "officier")]
    role[armee[n_off:]] = CODE_ROLE[_repli(carte, "soldat")]
    civils = emploi[~np.isin(emploi, armee)]
    if civils.size != len(postes):
        raise ValueError(f"{demographie} : {civils.size} civils en emploi pour {len(postes)} postes ( armee {armee.size} "
                         f"sur {n_mil} ) : la pyramide n a pas assez de personnes d age actif a cette echelle")
    role[civils] = _metiers_par_sexe(rng, postes, sexe[civils], R)
    for s, r in ((S_PETIT, "petit_enfant"), (S_ECOLE, "enfant"), (S_RETRAITE, "retraite"), (S_INVALIDE, "retraite"),
                 (S_RETRAITE_ANT, "retraite"), (S_ETUDES, "etudiant"), (S_CHOMAGE, "chomeur"), (S_FOYER, "inactif"),
                 (S_DECOURAGE, "inactif")):
        role[statut == s] = CODE_ROLE[r]
    for s, mo in ((S_FOYER, "au_foyer"), (S_DECOURAGE, "decourage"), (S_INVALIDE, "invalide"),
                  (S_RETRAITE_ANT, "retraite_anticipee")):
        motif[statut == s] = CODE_MOTIF[mo]
    sans = np.nonzero(np.isin(statut, (S_CHOMAGE, S_FOYER, S_DECOURAGE)))[0]
    # le metier cherche suit les effectifs de l ile ( 27/09 : sur Altis, ceux d E1 ; sans mine, personne ne cherche
    # un poste de mineur )
    unite = effectifs(carte, 1.0, entiers=False, fret=fret)
    w = np.array([[unite[m] * (R.PART_HOMMES[m] if s == R.HOMME else 1.0 - R.PART_HOMMES[m]) for m in METIERS_LIBRES]
                  for s in (R.FEMME, R.HOMME)])
    w = np.cumsum(w / w.sum(axis=1, keepdims=True), axis=1)
    j = (rng.random(sans.size)[:, None] >= w[(sexe[sans] == R.HOMME).astype(np.int64)]).sum(axis=1).clip(0, len(METIERS_LIBRES) - 1)
    metier[sans] = np.array([CODE_ROLE[_repli(carte, m)] for m in METIERS_LIBRES])[j]
    # 4. l ordre des lignes : les menages dans un ordre tire, et dans chacun le chef, son conjoint, puis par age
    n_m = int(menage.max()) + 1
    rang_m = np.empty(n_m, np.int64); rang_m[rng.permutation(n_m)] = np.arange(n_m)
    ids = np.arange(n)
    place = np.where(ids == racine, 0, np.where(conj == racine, 1, 2))
    ordre = np.lexsort((ids, -age, place, rang_m[menage]))        # ordre[ligne] = personne
    ligne = np.empty(n, np.int64); ligne[ordre] = ids
    mg = rang_m[menage][ordre]                                     # le menage de chaque ligne ( croissant )
    ro = role[ordre]
    # 5. la classe : celle du metier pour qui travaille ; celle du premier travailleur du menage pour les autres
    #    ( un menage sans travailleur : populaire, comme les retraites d E1 )
    code_classe = np.array([CODE_CLASSE[C.ROLES[r][1]] for r in ROLES], np.int64)
    trav = np.isin(ro, [CODE_ROLE[r] for r in ROLES if TRAVAIL[r][0] and r not in ("enfant", "etudiant")])
    tl = np.nonzero(trav)[0]
    chefs_m, premier = np.unique(mg[tl], return_index=True)
    chef = np.full(n_m, -1, np.int64); chef[chefs_m] = tl[premier]      # la ligne du premier travailleur du menage
    classe_m = np.full(n_m, CODE_CLASSE["populaire"], np.int64); classe_m[chefs_m] = code_classe[ro[chef[chefs_m]]]
    classe = np.where(trav, code_classe[np.maximum(ro, 0)], classe_m[mg])
    # 6. les lieux de travail : les postes de chaque metier sont ceux de `generer` ( repartition equilibree ). Le
    #    premier travailleur de chaque menage prend le poste suivant, et le menage vit au lieu habitable le plus proche ;
    #    les autres travailleurs prennent le poste restant le plus proche de chez eux.
    def candidats(r):
        types, _ = TRAVAIL[r]
        if types == ("gouvernement",): return [carte.gouvernement]
        return _lieux_ponderes(carte, r)
    habitable = {}
    def logis(l):
        if l.n not in habitable:
            habitable[l.n] = l if l.type in HABITABLES else carte.plus_proche(l, HABITABLES)
        return habitable[l.n]
    effectif = {ROLES[c]: int(k) for c, k in zip(*np.unique(ro[tl], return_counts=True))}
    cands = {r: candidats(r) for r in effectif}
    compteur = {r: 0 for r in effectif}
    travail = np.full(n, -1, np.int64); equipe = np.zeros(n, np.int64)
    domicile_m = np.full(n_m, -1, np.int64)
    for k in chefs_m.tolist():
        i = int(chef[k]); r = ROLES[ro[i]]
        c = compteur[r]; l = cands[r][c % len(cands[r])]
        travail[i], equipe[i] = l.n, c
        compteur[r] = c + 1
        domicile_m[k] = logis(l).n
    restes = {}                                                     # role -> { lieu : [ equipes libres ] }
    for r, tot in effectif.items():
        d = restes[r] = {}
        for c in range(compteur[r], tot): d.setdefault(cands[r][c % len(cands[r])].n, []).append(c)
    proches = {}
    for i in tl[np.isin(tl, chef[chefs_m], invert=True)].tolist():
        r = ROLES[ro[i]]; dom = int(domicile_m[mg[i]])
        cle = (r, dom)
        if cle not in proches:
            lieux = list(dict.fromkeys(l.n for l in cands[r]))
            proches[cle] = sorted(lieux, key=lambda x: (carte.par_n[dom].distance(carte.par_n[x]), x))
        x = next(x for x in proches[cle] if restes[r].get(x))
        travail[i], equipe[i] = x, restes[r][x].pop(0)
    # les menages sans travailleur vivent ou vivent les autres : le domicile d un menage de travailleurs tire au hasard
    sans_trav = np.nonzero(domicile_m < 0)[0]
    domicile_m[sans_trav] = domicile_m[chefs_m[rng.integers(0, chefs_m.size, sans_trav.size)]]
    dom = domicile_m[mg]
    marche = np.array([l.marche.n if l.marche is not None else -1 for l in carte.par_n], np.int64)
    ecole = np.isin(ro, (CODE_ROLE["enfant"], CODE_ROLE["etudiant"]))
    travail[ecole] = marche[dom[ecole]]                             # l ecole ( ou l universite ) de son marche
    horaire = np.array([CODE_HORAIRE[TRAVAIL[r][1]] for r in ROLES], np.int64)[ro]
    # 7. les colonnes des habitants et des menages
    _reserver(table, Table.CHAMPS, n)
    t = table; t.n = n
    t.role[:n] = ro; t.public[:n] = np.array([1 if C.ROLES[r][2] else 0 for r in ROLES], np.uint8)[ro]
    t.classe[:n] = classe; t.age[:n] = age[ordre]
    t.menage[:n] = mg; t.rang[:n] = np.arange(n); t.rang_suivant = n
    t.domicile[:n] = dom; t.hopital[:n] = marche[dom]; t.lieu[:n] = dom
    t.travail[:n] = travail; t.horaire[:n] = horaire; t.equipe[:n] = equipe
    t.decalage[:n] = rng.integers(-30, 31, n)
    t.nia[:n] = (int(t.code_ile) << C.BITS_NUMERO_LOCAL) | np.arange(n, dtype=np.int64); t.nationalite[:n] = t.code_ile
    _reserver(mt, TableMenages.CHAMPS, n_m)
    mt.n = n_m
    mt.domicile[:n_m] = domicile_m
    epargne = np.array([EPARGNE_DEPART[c] for c in CLASSES])
    adulte = (age[ordre] >= AGE_MAJEUR) & (ro != CODE_ROLE["enfant"]) & (ro != CODE_ROLE["petit_enfant"])
    mt.caisse[:n_m] = np.bincount(mg, weights=np.where(adulte, epargne[classe], 0.0), minlength=n_m)
    mt.garde_manger[:n_m] = 2.0 * np.bincount(mg, minlength=n_m)
    # l eleve : l enfant le plus jeune de la capitale du gouvernement ( a defaut, du pays )
    enf = np.nonzero(ro == CODE_ROLE["enfant"])[0]
    ici = enf[dom[enf] == carte.gouvernement.n]
    enf = ici if ici.size else enf
    t.eleve[enf[np.lexsort((enf, t.age[enf]))[0]]] = 1
    # ce que les domaines relisent a leur recensement ( une ligne par habitant )
    vers = lambda x: np.where(x >= 0, ligne[np.maximum(x, 0)], -1).astype(np.int32)
    table.recensement = {"demographie": demographie, "sexe": sexe[ordre].astype(np.int8), "conjoint": vers(conj[ordre]),
                         "mere": vers(mere[ordre]), "pere": vers(pere[ordre]), "metier": metier[ordre].astype(np.int16),
                         "motif": motif[ordre]}
    return Population(table), Menages(mt)
