"""LE PAYS : les domaines de la vie du pays, poses sur un Monde E1 et sur le socle, sans modifier monde.py.

`installer( w, domaines )` :
  - branche le socle ( w.socle ) s il ne l est pas deja ;
  - installe chaque domaine demande, apres ses dependances, dans l ordre de la carte des domaines ;
  - remplace w.pas_suivant par l HORLOGE du pays : le pas du moteur E1, puis les routines des domaines a leur minute,
    puis les echeances du pas ; au dernier pas du jour, la cloture ( grand livre, journal, domaines ).

Tout reste picklable : fonctions de module, jamais de lambda ; un pays passe dans l instantane et reprend a l identique.

Ce qu un domaine recoit ( `p` ) :
  p.w, p.socle                       le monde E1 et le socle
  p.jour, p.heure, p.pas             le temps du monde
  p.routine( heure, ordre, dom, f )  f( p ) chaque jour a cette heure ( multiple de 10 minutes ), apres le pas E1
  p.echeance( type, f )              declare un type d echeance ; f( p, cle, donnees ) quand elle tombe
  p.poser( dans_pas, type, cle, d )  pose une echeance dans `dans_pas` pas ( 0 = au prochain pas )
  p.cloture( dom, f )                f( p, comptes_du_jour ) a la cloture du jour
  p.colonnes["habitant"|"menage"]    des champs par entite, en tableaux numpy indexes par identifiant
  p.decideur( point )                le Decideur d un point, dans le mode demande a l installation
  p.hasard( dom ), p.du_jour( dom )  le flux de hasard du domaine ; son flux du jour
  p.noter( type, **champs ), p.compter( type, valeur )   le journal
  p.domaine( nom ), p.a( nom )       l etat d un autre domaine ; s il est installe
  p.reprendre( e, dom )              declare qu un domaine fait vivre l entreprise du moteur `e` a sa place : le moteur
                                     n y produit plus ( activite 0, reposee apres chaque regle de l aube )"""
import importlib
import numpy as np
from .. import config as C
from ..socle import brancher as BR, decision as D

# La carte des domaines ( 23/09 ) : nom, module, dependances. Une dependance vient toujours AVANT dans cet ordre.
DOMAINES = (   # dependances DURES seulement : celles dont le code du domaine appelle l API ; le reste est optionnel ( p.a )
    ("population", "d01_population", ()),
    ("banques", "d02_banques", ("population",)),
    ("economie", "d03_economie", ("population", "banques")),
    ("travail", "d04_travail", ("population", "economie")),
    ("agenda", "d05_agenda", ("population",)),
    ("etat", "d06_etat", ("population", "banques", "economie")),
    ("exterieur", "d07_exterieur", ("population", "banques", "etat")),
    ("territoire", "d08_territoire", ()),
    ("agriculture", "d09_agriculture", ("territoire", "economie")),
    ("industrie", "d10_industrie", ("territoire", "economie")),
    ("energie", "d11_energie", ("territoire", "economie")),
    ("services_publics", "d12_services_publics", ("territoire", "etat")),
    ("immobilier", "d13_immobilier", ("banques", "etat", "territoire", "industrie")),
    ("transport", "d14_transport", ("banques", "exterieur", "industrie", "energie")),
    ("logistique", "d15_logistique", ("exterieur", "immobilier", "transport")),
    ("medecine", "d16_medecine", ("population", "territoire")),
    ("hopitaux", "d17_hopitaux", ("medecine", "immobilier", "industrie")),
    ("securite_civile", "d18_securite_civile", ("immobilier", "transport", "hopitaux")),
    ("education", "d19_education", ("travail", "immobilier", "etat")),
    ("assurances", "d20_assurances", ("banques", "agriculture", "immobilier", "transport", "hopitaux")),
    ("justice", "d21_justice", ("etat", "banques", "immobilier")),
    ("medias", "d22_medias", ("etat",)),
    ("culture", "d23_culture", ("population", "agenda", "medias")),
    ("politique", "d24_politique", ("etat", "medias", "culture")),
    ("armee", "d25_armee", ("travail", "industrie", "transport", "education")),
    ("armee_soutien", "d26_armee_soutien", ("armee", "logistique", "hopitaux", "medias")),
    ("armee_tactique", "d27_armee_tactique", ("armee_soutien", "justice")),
)
MODULE = {nom: mod for nom, mod, _ in DOMAINES}
DEPEND = {nom: dep for nom, _, dep in DOMAINES}
RANG = {nom: k for k, (nom, _, _) in enumerate(DOMAINES)}
MINUTES_JOUR = 24 * 60
DERNIERE_MINUTE = MINUTES_JOUR - C.MINUTES_PAR_PAS


def fermeture(noms):
    """Les domaines demandes et toutes leurs dependances, dans l ordre de la carte."""
    vus, pile = set(), list(noms)
    while pile:
        n = pile.pop()
        if n not in MODULE: raise KeyError(f"domaine inconnu {n!r}")
        if n in vus: continue
        vus.add(n); pile.extend(DEPEND[n])
    return sorted(vus, key=RANG.get)


class Colonnes:
    """Des champs par entite ( habitant, menage ) en structure de tableaux : numpy aujourd hui, Vec<T> en Rust demain.
    Un domaine qui ajoute un champ a TOUS les habitants l ajoute ici, jamais dans Habitant, qui appartient au moteur.
    Indexees par l identifiant de l entite. Apres une croissance, le tableau change : le relire par `self[nom]` a chaque
    usage, ne jamais le garder d un jour a l autre."""
    __slots__ = ("cols", "defauts", "cap")

    def __init__(self, cap=1024):
        self.cols, self.defauts, self.cap = {}, {}, cap

    def ajouter(self, nom, dtype, defaut):
        if nom in self.cols: raise ValueError(f"colonne {nom!r} deja declaree : un domaine etend, il ne duplique pas")
        self.cols[nom] = np.full(self.cap, defaut, dtype=dtype)
        self.defauts[nom] = defaut

    def assurer(self, n):
        """Garantit la place pour les identifiants 0 .. n-1 ( croissance par doublement )."""
        if n <= self.cap: return
        cap = max(n, 2 * self.cap)
        for nom, a in self.cols.items():
            b = np.full(cap, self.defauts[nom], dtype=a.dtype); b[:self.cap] = a; self.cols[nom] = b
        self.cap = cap

    def __getitem__(self, nom): return self.cols[nom]
    def __contains__(self, nom): return nom in self.cols


def _neutraliser_repris(p):
    """6 h 10, apres la regle d activite de l aube : les entreprises reprises par un domaine ne produisent plus par le
    moteur ( la production du moteur commence a 7 h )."""
    for eid in p.repris: p.w.entreprises[eid].activite = 0.0


class Horloge:
    """Remplace w.pas_suivant : le pas du moteur, puis le pays. Un objet et non une fonction liee, pour que
    l instantane le reconstruise sans boucler sur lui-meme."""
    __slots__ = ("pays",)

    def __init__(self, pays): self.pays = pays

    def __call__(self): self.pays.pas_suivant()


class Pays:
    __slots__ = ("w", "socle", "domaines", "routines", "gestionnaires", "colonnes", "decideurs", "modes", "clotures",
                 "comptes_hier", "repris")

    def __init__(self, w, modes=None):
        self.w = w
        self.socle = w.socle if getattr(w, "socle", None) is not None else BR.brancher(w)
        self.domaines = {}
        self.routines = {}          # minute du jour -> [ ( ordre, domaine, fonction ) ], tries
        self.gestionnaires = {}     # type d echeance -> fonction( pays, cle, donnees )
        self.colonnes = {"habitant": Colonnes(), "menage": Colonnes()}
        self.decideurs = {}         # nom du point -> Decideur
        self.modes = dict(modes or {})   # nom du point -> mode ( regle par defaut )
        self.clotures = []          # ( domaine, fonction( pays, comptes ) )
        self.comptes_hier = None    # les comptes du grand livre de la veille : la matiere de la statistique
        self.repris = {}            # identifiant d une entreprise du moteur -> domaine qui la fait vivre a sa place

    # ------------------------------------------------------------------ le temps
    @property
    def jour(self): return self.w.jour

    @property
    def heure(self): return self.w.heure

    @property
    def pas(self): return self.w.pas

    # ------------------------------------------------------------------ l enregistrement
    def routine(self, heure, ordre, domaine, fonction):
        minute = int(round(heure * 60))
        if minute % C.MINUTES_PAR_PAS or not 0 <= minute < MINUTES_JOUR:
            raise ValueError(f"{domaine} : heure {heure} hors grille de {C.MINUTES_PAR_PAS} minutes")
        if getattr(fonction, "__name__", "") == "<lambda>": raise ValueError(f"{domaine} : une lambda ne se pickle pas")
        lst = self.routines.setdefault(minute, [])
        lst.append((ordre, domaine, fonction))
        lst.sort(key=lambda r: (r[0], r[1]))

    def echeance(self, type_, fonction):
        self.socle.echeancier.declarer(type_)
        self.gestionnaires[type_] = fonction

    def poser(self, dans_pas, type_, cle, donnees=()):
        return self.socle.echeancier.poser(self.w.pas + max(0, int(dans_pas)), type_, cle, donnees)

    def cloture(self, domaine, fonction):
        self.clotures.append((domaine, fonction))

    def decideur(self, point, **kw):
        mode = self.modes.get(point.nom, "regle")
        d = D.Decideur(point, mode, rng=self.socle.hasard.flux("decision_" + point.nom), **kw)
        self.decideurs[point.nom] = d
        return d

    # ------------------------------------------------------------------ les services
    def domaine(self, nom):
        d = self.domaines.get(nom)
        if d is None: raise KeyError(f"domaine {nom!r} non installe")
        return d

    def a(self, nom): return nom in self.domaines

    def reprendre(self, e, domaine):
        """Un domaine prend en charge une entreprise du moteur ( ferme, mine, centrale... ) : le moteur n y produit
        plus. L activite est remise a zero apres chaque regle de l aube ( routine de 6 h 10 ). Le domaine produit
        lui-meme, compte les heures travaillees ( Habitant.heures_jour ) pour que la paie les paie, et tient les flux."""
        deja = self.repris.get(e.id)
        if deja is not None and deja != domaine: raise ValueError(f"{e.id} deja repris par {deja}")
        self.repris[e.id] = domaine
        e.activite = 0.0
        if not any(f is _neutraliser_repris for _, _, f in self.routines.get(370, ())):
            self.routine(6 + 10 / 60, 0, "pays", _neutraliser_repris)

    def hasard(self, domaine): return self.socle.hasard.flux(domaine)

    def du_jour(self, domaine): return self.socle.hasard.du_jour(domaine, self.w.jour)

    def noter(self, type_, **champs): self.socle.journal.noter(self.w.jour, self.w.heure, type_, **champs)

    def compter(self, type_, valeur=1.0): self.socle.journal.compter(type_, valeur)

    def col(self, entite, nom): return self.colonnes[entite][nom]

    # ------------------------------------------------------------------ le pas
    def pas_suivant(self):
        w = self.w
        minute = w.minutes % MINUTES_JOUR
        type(w).pas_suivant(w)                       # le pas du moteur E1 ( la methode de la classe, pas l horloge )
        for _, _, f in self.routines.get(minute, ()): f(self)
        for _, type_, cle, donnees in self.socle.echeancier.servir(w.pas - 1):
            self.gestionnaires[type_](self, cle, donnees)
        if minute == DERNIERE_MINUTE: self.cloturer_jour()

    def cloturer_jour(self):
        comptes = self.socle.livre.cloturer_jour()
        for _, f in self.clotures: f(self, comptes)
        self.socle.journal.cloturer_jour(self.w.jour)
        self.comptes_hier = comptes


def installer(w, domaines=None, modes=None):
    """Installe les domaines demandes ( tous par defaut ) et leurs dependances ; rend le pays ( aussi en w.pays ).
    `modes` : { nom d un point de decision : mode } ( regle, appris, fige, hasard, temoin )."""
    p = getattr(w, "pays", None)
    if p is None:
        p = Pays(w, modes)
        w.pays = p
    elif modes: p.modes.update(modes)
    for nom in fermeture(domaines if domaines is not None else list(MODULE)):
        if nom in p.domaines: continue
        module = importlib.import_module(f".{MODULE[nom]}", __package__)
        p.domaines[nom] = module.installer(p)
    w.pas_suivant = Horloge(p)
    return p
