"""LES OBJETS DURABLES : ce qui a une identite, un proprietaire, une usure, et souvent un corps dans Arma
( socle, choix 2 ).

Un vehicule n est pas « une unite de vehicule » : il a un numero, un proprietaire qui l a peut-etre paye a credit,
une usure, une panne, un voleur. Il se conserve donc par MODELE : chaque exemplaire vivant vient d une source declaree
( initial, fabrique, importe ) et n en sort que par un puits declare ( detruit, rebut, exporte ). Une cession ( vente,
vol, heritage, saisie ) change le proprietaire, jamais le nombre.

Deux representations, parce qu un pays de 50 millions d habitants a des dizaines de millions de vehicules :
  - l INDIVIDU ( Objet ) : un numero, un proprietaire, un lieu, une usure, un etat ;
  - la COHORTE : des exemplaires anonymes du meme modele, chez le meme proprietaire, au meme lieu - un nombre et une
    usure moyenne. On en tire un individu, de facon deterministe, quand un evenement le touche ( incarnation, vol,
    accident, vente ) ; on l y refond quand il redevient anonyme.

Les donnees propres a un domaine ( immatriculation, kilometrage, munitions chargees, surface d un batiment ) vivent
dans des tables a part, indexees par le numero de l objet : pas d heritage, des donnees simples, portables en Rust.
Le proprietaire est une reference au detenteur ( en Rust : son identifiant )."""
import re
from .hasard import SOUS_FLUX_OBJET

FAMILLES = ("vehicule", "navire", "aeronef", "arme", "optique", "equipement", "batiment", "machine")
SOURCES = ("initial", "fabrique", "importe")
PUITS = ("detruit", "rebut", "exporte")
ETATS = ("service", "panne", "immobilise")          # les etats d un objet VIVANT ; un puits le sort du parc
SERVICE, PANNE, IMMOBILISE = 0, 1, 2
NOM_VALIDE = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
PRIX_MAX = 1e10               # drachmes : un navire de guerre, pas davantage
MASSE_MAX_KG = 1e8            # un batiment, un navire
CONCENTRATION_USURE = 20.0    # dispersion de l usure d un individu tire d une cohorte ( loi beta ) : a calibrer


class Modele:
    """Un modele d objet durable : ce que tous ses exemplaires partagent.
      prix_monde    drachmes, neuf, au port : la reference de l import, de l assurance, de la casse
      masse_kg      pour le transport et le fret
      vie_h         heures d usage qui menent un exemplaire neuf a l usure complete ( 1 ) ; a calibrer par domaine
      arma          classname Arma 3, ou None si l objet n a pas de corps
      arma_preuve   comment le classname a ete verifie A L USAGE ( « cree et vu vivant sur Altis le 22/09 » ) ;
                    None tant que personne ne l a vu : le pont ne doit pas incarner un modele sans preuve ( le van
                    C_Van_01_box_F naissait mort sans erreur, 22/09 )"""
    __slots__ = ("id", "nom", "famille", "prix_monde", "masse_kg", "vie_h", "arma", "arma_preuve", "source")

    def __init__(self, id, nom, famille, prix_monde, masse_kg, vie_h, arma=None, arma_preuve=None, source="a calibrer"):
        if not NOM_VALIDE.match(nom): raise ValueError(f"nom de modele invalide : {nom!r}")
        if famille not in FAMILLES: raise ValueError(f"{nom} : famille inconnue {famille!r}")
        if not 0.0 < prix_monde <= PRIX_MAX: raise ValueError(f"{nom} : prix hors ]0 ; {PRIX_MAX:g}] : {prix_monde!r}")
        if not 0.0 < masse_kg <= MASSE_MAX_KG: raise ValueError(f"{nom} : masse hors ]0 ; {MASSE_MAX_KG:g}] : {masse_kg!r}")
        if not vie_h > 0.0: raise ValueError(f"{nom} : duree de vie non positive {vie_h!r}")
        if arma is not None and (not isinstance(arma, str) or not arma or not arma.isascii()):
            raise ValueError(f"{nom} : classname Arma invalide {arma!r}")
        if arma_preuve is not None and arma is None: raise ValueError(f"{nom} : une preuve sans classname")
        self.id, self.nom, self.famille, self.prix_monde = id, nom, famille, float(prix_monde)
        self.masse_kg, self.vie_h, self.arma, self.arma_preuve, self.source = masse_kg, vie_h, arma, arma_preuve, source


class Objet:
    """Un exemplaire. usure : 0 neuf, 1 use jusqu a la corde ; etat : SERVICE, PANNE ou IMMOBILISE ; ne : le pas
    ou il est entre dans le pays ( ou a ete tire de sa cohorte )."""
    __slots__ = ("id", "modele", "proprietaire", "lieu", "usure", "etat", "ne")

    def __init__(self, id, modele, proprietaire, lieu, usure, etat, ne):
        self.id, self.modele, self.proprietaire, self.lieu = id, modele, proprietaire, lieu
        self.usure, self.etat, self.ne = usure, etat, ne


class Cohorte:
    """Des exemplaires anonymes du meme modele, chez le meme proprietaire, au meme lieu : un nombre et une usure
    moyenne. Ils sont tous en service : un exemplaire en panne a une histoire, donc une identite."""
    __slots__ = ("modele", "proprietaire", "lieu", "nombre", "usure")

    def __init__(self, modele, proprietaire, lieu, nombre, usure):
        self.modele, self.proprietaire, self.lieu, self.nombre, self.usure = modele, proprietaire, lieu, nombre, usure


class Parc:
    """Tous les objets durables du pays : les modeles, les individus, les cohortes, et les comptes par modele."""
    __slots__ = ("hasard", "modeles", "par_nom", "objets", "cohortes", "vivants", "comptes", "cessions", "prochain_id")

    def __init__(self, hasard):
        self.hasard = hasard
        self.modeles = []; self.par_nom = {}
        self.objets = {}          # numero -> Objet
        self.cohortes = {}        # ( modele, proprietaire, lieu ) -> Cohorte
        self.vivants = []         # par modele : exemplaires vivants ( individus + cohortes ), tenu a chaque operation
        self.comptes = []         # par modele : { source ou puits : nombre }
        self.cessions = {}        # motif -> nombre d exemplaires cedes ( vente, vol, heritage, saisie... )
        self.prochain_id = 0

    # ------------------------------------------------------------------ les modeles
    def declarer_modele(self, nom, famille, prix_monde, masse_kg, vie_h, arma=None, arma_preuve=None, source="a calibrer"):
        if nom in self.par_nom: raise ValueError(f"modele {nom!r} deja declare")
        m = Modele(len(self.modeles), nom, famille, prix_monde, masse_kg, vie_h, arma, arma_preuve, source)
        self.modeles.append(m); self.par_nom[nom] = m
        self.vivants.append(0); self.comptes.append({n: 0 for n in SOURCES + PUITS})
        return m

    def modele(self, cle):
        if isinstance(cle, Modele): return cle
        return self.modeles[cle] if isinstance(cle, int) else self.par_nom[cle]

    def sans_preuve_arma(self):
        """Les modeles qui ont un classname que personne n a encore vu vivre dans Arma."""
        return [m.nom for m in self.modeles if m.arma is not None and m.arma_preuve is None]

    # ------------------------------------------------------------------ interne
    def _compter(self, mid, nature, n):
        self.comptes[mid][nature] += n
        self.vivants[mid] += n if nature in SOURCES else -n

    def _cohorte(self, mid, proprietaire, lieu):
        cle = (mid, proprietaire, lieu)
        c = self.cohortes.get(cle)
        if c is None: c = self.cohortes[cle] = Cohorte(mid, proprietaire, lieu, 0, 0.0)
        return c

    def _a_moi(self, objet):
        if self.objets.get(objet.id) is not objet: raise KeyError(f"objet {objet.id} absent du parc")

    def _a_moi_cohorte(self, c):
        if self.cohortes.get((c.modele, c.proprietaire, c.lieu)) is not c: raise KeyError("cohorte absente du parc")

    def _effacer_si_vide(self, c):
        if c.nombre == 0: del self.cohortes[(c.modele, c.proprietaire, c.lieu)]

    def _verser(self, c, n, proprietaire, lieu):
        """Deplace n exemplaires d une cohorte vers la cohorte ( proprietaire, lieu ) du meme modele."""
        if not (isinstance(n, int) and 1 <= n <= c.nombre): raise ValueError(f"nombre hors [1 ; {c.nombre}] : {n!r}")
        dest = self._cohorte(c.modele, proprietaire, lieu)
        if dest is c: return c
        dest.usure = (dest.nombre * dest.usure + n * c.usure) / (dest.nombre + n)
        dest.nombre += n; c.nombre -= n
        self._effacer_si_vide(c)
        return dest

    # ------------------------------------------------------------------ les sources
    def creer(self, modele, proprietaire, lieu, source, pas, usure=0.0):
        """Un exemplaire individuel qui entre dans le pays par une source declaree."""
        m = self.modele(modele)
        if source not in SOURCES: raise ValueError(f"source inconnue {source!r} : {SOURCES}")
        if not 0.0 <= usure <= 1.0: raise ValueError(f"usure hors [0 ; 1] : {usure!r}")
        o = Objet(self.prochain_id, m.id, proprietaire, lieu, float(usure), SERVICE, int(pas))
        self.prochain_id += 1
        self.objets[o.id] = o
        self._compter(m.id, source, 1)
        return o

    def creer_cohorte(self, modele, proprietaire, lieu, nombre, source, usure=0.0):
        """Des exemplaires anonymes qui entrent dans le pays ; ils rejoignent la cohorte ( proprietaire, lieu )."""
        m = self.modele(modele)
        if source not in SOURCES: raise ValueError(f"source inconnue {source!r} : {SOURCES}")
        if not (isinstance(nombre, int) and nombre >= 1): raise ValueError(f"nombre invalide : {nombre!r}")
        if not 0.0 <= usure <= 1.0: raise ValueError(f"usure hors [0 ; 1] : {usure!r}")
        c = self._cohorte(m.id, proprietaire, lieu)
        c.usure = (c.nombre * c.usure + nombre * usure) / (c.nombre + nombre)
        c.nombre += nombre
        self._compter(m.id, source, nombre)
        return c

    # ------------------------------------------------------------------ les puits
    def sortir(self, objet, puits):
        """Un exemplaire quitte le pays : detruit ( combat, incendie, accident sans reparation ), rebut, exporte."""
        if puits not in PUITS: raise ValueError(f"puits inconnu {puits!r} : {PUITS}")
        self._a_moi(objet)
        del self.objets[objet.id]
        self._compter(objet.modele, puits, 1)

    def sortir_de_cohorte(self, cohorte, nombre, puits):
        if puits not in PUITS: raise ValueError(f"puits inconnu {puits!r} : {PUITS}")
        self._a_moi_cohorte(cohorte)
        n = min(int(nombre), cohorte.nombre)
        if n <= 0: return 0
        cohorte.nombre -= n
        self._effacer_si_vide(cohorte)
        self._compter(cohorte.modele, puits, n)
        return n

    # ------------------------------------------------------------------ la vie d un objet
    def ceder(self, objet, vers, motif):
        """Changement de proprietaire. L argent de la vente, s il y en a, passe par le grand livre, pas ici."""
        self._a_moi(objet)
        objet.proprietaire = vers
        self.cessions[motif] = self.cessions.get(motif, 0) + 1

    def ceder_de_cohorte(self, cohorte, nombre, vers, motif):
        self._a_moi_cohorte(cohorte)
        dest = self._verser(cohorte, nombre, vers, cohorte.lieu)
        self.cessions[motif] = self.cessions.get(motif, 0) + nombre
        return dest

    def deplacer(self, objet, lieu):
        self._a_moi(objet)
        objet.lieu = lieu

    def deplacer_de_cohorte(self, cohorte, nombre, lieu):
        self._a_moi_cohorte(cohorte)
        return self._verser(cohorte, nombre, cohorte.proprietaire, lieu)

    def user(self, objet, heures):
        """L usure d un usage de `heures` heures, rapportee a la duree de vie du modele. Rend l usure atteinte ; la
        panne qui en decoule appartient au domaine de l objet."""
        if not heures >= 0.0: raise ValueError(f"heures d usage negatives : {heures!r}")
        objet.usure = min(1.0, objet.usure + heures / self.modeles[objet.modele].vie_h)
        return objet.usure

    def mettre_en_etat(self, objet, etat):
        if etat not in (SERVICE, PANNE, IMMOBILISE): raise ValueError(f"etat inconnu {etat!r}")
        self._a_moi(objet)
        objet.etat = etat

    def materialiser(self, cohorte, pas):
        """Tire un individu d une cohorte. Son usure suit une loi beta centree sur l usure moyenne, tiree du flux
        propre a SON numero : deterministe, et independant de tout autre tirage. L usure totale de la cohorte se
        conserve : ce qu emporte l individu est retire de la moyenne des autres."""
        self._a_moi_cohorte(cohorte)
        if cohorte.nombre < 1: raise ValueError("cohorte vide")
        oid = self.prochain_id
        u = cohorte.usure
        if 0.0 < u < 1.0:
            rng = self.hasard.sous_flux("objets", SOUS_FLUX_OBJET, oid)
            w = float(rng.beta(CONCENTRATION_USURE * u, CONCENTRATION_USURE * (1.0 - u)))
        else:
            w = u
        reste = cohorte.nombre - 1
        cohorte.usure = min(1.0, max(0.0, (cohorte.nombre * u - w) / reste)) if reste else 0.0
        cohorte.nombre = reste
        o = Objet(oid, cohorte.modele, cohorte.proprietaire, cohorte.lieu, w, SERVICE, int(pas))
        self.prochain_id += 1
        self.objets[oid] = o
        self._effacer_si_vide(cohorte)
        return o

    def fondre(self, objet):
        """Un individu redevient anonyme dans la cohorte de son modele, de son proprietaire et de son lieu. Refuse
        pour un objet en panne ou immobilise : il a une histoire, il garde son identite."""
        self._a_moi(objet)
        if objet.etat != SERVICE: raise ValueError(f"objet {objet.id} en etat {ETATS[objet.etat]} : il garde son identite")
        del self.objets[objet.id]
        c = self._cohorte(objet.modele, objet.proprietaire, objet.lieu)
        c.usure = (c.nombre * c.usure + objet.usure) / (c.nombre + 1)
        c.nombre += 1
        return c

    # ------------------------------------------------------------------ la conservation
    def nombre(self, modele):
        return self.vivants[self.modele(modele).id]

    def recompter(self):
        n = [0] * len(self.modeles)
        for o in self.objets.values(): n[o.modele] += 1
        for c in self.cohortes.values(): n[c.modele] += c.nombre
        return n

    def verifier(self):
        """Pour chaque modele : exemplaires recomptes, moins ( sources - puits ). Zero partout, sinon un objet est ne
        ou mort hors des sources et des puits declares."""
        n = self.recompter()
        res = {}
        for m in self.modeles:
            k = self.comptes[m.id]
            res[m.nom] = n[m.id] - (sum(k[s] for s in SOURCES) - sum(k[p] for p in PUITS))
        return res
