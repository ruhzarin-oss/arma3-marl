"""LE REGISTRE DES DETENTEURS, LA CONSERVATION, LE RAPPROCHEMENT ( socle, choix 3 ).

`Monde.argent_total` et `Monde.biens_totaux` enumerent les detenteurs a la main. Un detenteur oublie la rend
aveugle : un bien cree chez lui n est jamais compte. Ici chaque famille de detenteurs S INSCRIT, et la conservation
parcourt le registre. Un domaine qui ajoute une classe qui detient de l argent ou des biens l inscrit a sa livraison.

Trois controles, du plus large au plus fin :
  - Conservation : argent et biens totaux = depart + sources - puits declares. Voit une creation hors source.
  - Parc.verifier ( objets.py ) : la meme chose pour les objets durables, par modele.
  - Rapprochement : pour chaque famille, la variation de sa caisse = ce que le grand livre l a vue recevoir et payer.
    Voit un paiement ecrit a la main ( `caisse -=` ), que la conservation ne voit pas : un deplacement ne cree rien.

Les sommes sont exactes ( math.fsum ) : a 50 millions d habitants, une somme naive perd des centimes dans l ordre
des additions, et la porte mesurerait l arrondi au lieu de la conservation."""
import math
from .comptes import SOURCES_BIENS, PUITS_BIENS

# Les secteurs institutionnels des comptes nationaux ( SCN 2008 ).
SECTEURS = {"entreprises": "S.11", "financier": "S.12", "administrations": "S.13", "menages": "S.14",
            "associations": "S.15", "exterieur": "S.2"}


class Famille:
    """Une famille de detenteurs.
      membres  fonction de module ( racine ) -> iterable de detenteurs ; jamais une lambda, que l instantane ne
               saurait pas pickler
      argent   nom de l attribut qui tient la monnaie, ou None
      biens    None ; "stock" ( un biens.Stock du socle, en attribut .stock ) ; ou fonction de module
               ( detenteur ) -> iterable de ( nom du bien, quantite ), pour les classes du moteur E1
      classe   nom de la classe Python de ses detenteurs : ce qui relie la famille aux lignes du grand livre"""
    __slots__ = ("nom", "secteur", "membres", "argent", "biens", "classe")

    def __init__(self, nom, secteur, membres, argent, biens, classe):
        self.nom, self.secteur, self.membres, self.argent, self.biens, self.classe = nom, secteur, membres, argent, biens, classe


def _pas_une_lambda(f, quoi):
    if not callable(f): raise ValueError(f"{quoi} doit etre une fonction")
    if getattr(f, "__name__", "") == "<lambda>": raise ValueError(f"{quoi} : une lambda ne se picklera pas dans l instantane")


class Registre:
    __slots__ = ("racine", "catalogue", "familles")

    def __init__(self, racine, catalogue):
        self.racine, self.catalogue = racine, catalogue
        self.familles = {}

    def inscrire(self, nom, secteur, membres, argent="caisse", biens=None, classe=None):
        if nom in self.familles: raise ValueError(f"famille {nom!r} deja inscrite")
        if secteur not in SECTEURS: raise ValueError(f"secteur inconnu {secteur!r} : {tuple(SECTEURS)}")
        _pas_une_lambda(membres, f"{nom}.membres")
        if biens is not None and biens != "stock": _pas_une_lambda(biens, f"{nom}.biens")
        if argent is not None:
            if classe is None: raise ValueError(f"{nom} : une famille qui detient de l argent nomme sa classe")
            deja = [f.nom for f in self.familles.values() if f.argent is not None and f.classe == classe]
            if deja: raise ValueError(f"{nom} : la classe {classe} est deja celle de {deja[0]} - le rapprochement les confondrait")
        self.familles[nom] = Famille(nom, secteur, membres, argent, biens, classe)

    def retirer(self, nom):
        del self.familles[nom]

    def argent_par_famille(self):
        return {f.nom: math.fsum(getattr(d, f.argent) for d in f.membres(self.racine))
                for f in self.familles.values() if f.argent is not None}

    def argent(self):
        return math.fsum(self.argent_par_famille().values())

    def biens(self):
        """Les quantites totales de chaque bien, par nom. Un bien inconnu du catalogue leve KeyError : un detenteur
        ne tient pas ce que le pays ne connait pas."""
        noms = self.catalogue.noms()
        acc = {b: [] for b in noms}
        for f in self.familles.values():
            if f.biens is None: continue
            if f.biens == "stock":
                for d in f.membres(self.racine):
                    for b, q in d.stock.q.items(): acc[noms[b]].append(q)
            else:
                for d in f.membres(self.racine):
                    for b, q in f.biens(d): acc[b].append(q)
        return {b: math.fsum(v) for b, v in acc.items()}


def tolerance(total):
    """L ecart admis : un millionieme de drachme, plus l arrondi relatif du double ( 1e-12 du total ). Mesure du
    22/09 : 4e-7 d accumulation sur 1,37 million de drachmes en 365 jours ( monde/tests.py, test_demographie )."""
    return 1e-6 + 1e-12 * abs(total)


class Conservation:
    """Argent et biens : maintenant = depart + sources - puits declares. Le depart est l etat au moment ou la
    conservation est posee ( un socle branche sur un monde deja vivant part de son etat du moment )."""
    __slots__ = ("registre", "livre", "parc", "argent0", "biens0", "ext0", "monnaie0", "flux0")

    def __init__(self, registre, livre, parc=None):
        self.registre, self.livre, self.parc = registre, livre, parc
        self.argent0 = registre.argent()
        self.biens0 = registre.biens()
        self.ext0 = dict(livre.ext)
        self.monnaie0 = dict(livre.monnaie)
        self.flux0 = {n: dict(livre.flux[n]) for n in SOURCES_BIENS + PUITS_BIENS}

    def ecarts(self):
        """Rend ( ecart d argent, { bien : ecart }, { modele : ecart d exemplaires } ). Zero partout, ou quelque
        chose est ne ou mort hors des sources et puits declares."""
        L = self.livre
        ext = (L.ext["entree"] - self.ext0["entree"]) - (L.ext["sortie"] - self.ext0["sortie"])
        emis = (L.monnaie["emise"] - self.monnaie0["emise"]) - (L.monnaie["detruite"] - self.monnaie0["detruite"])
        d_arg = self.registre.argent() - self.argent0 - ext - emis
        t = self.registre.biens()
        d_b = {}
        for b, q in t.items():
            entre = math.fsum(L.flux[n].get(b, 0.0) - self.flux0[n].get(b, 0.0) for n in SOURCES_BIENS)
            sort = math.fsum(L.flux[n].get(b, 0.0) - self.flux0[n].get(b, 0.0) for n in PUITS_BIENS)
            d_b[b] = q - self.biens0.get(b, 0.0) - (entre - sort)
        d_o = self.parc.verifier() if self.parc is not None else {}
        return d_arg, d_b, d_o

    def tenue(self):
        """( vrai si tout est conserve, resume du pire ecart )."""
        d_arg, d_b, d_o = self.ecarts()
        pire_b = max(d_b, key=lambda b: abs(d_b[b])) if d_b else None
        ok = (abs(d_arg) <= tolerance(self.argent0) and all(abs(v) <= tolerance(self.biens0.get(b, 0.0)) for b, v in d_b.items())
              and all(v == 0 for v in d_o.values()))
        return ok, (f"argent {d_arg:+.2e}, pire bien {pire_b} {d_b.get(pire_b, 0.0):+.2e}, "
                    f"objets {sum(abs(v) for v in d_o.values())} exemplaire(s) hors compte")


class Rapprochement:
    """Pour chaque famille qui detient de l argent : la variation de sa caisse, moins ce que le grand livre l a vue
    recevoir et payer. Un reste non nul dit qu un paiement est passe HORS du grand livre - un `caisse -=` ecrit a la
    main. La conservation ne le voit pas quand l argent passe d une famille a une autre : rien n est cree."""
    __slots__ = ("registre", "livre", "argent0", "net0")

    def __init__(self, registre, livre):
        self.registre, self.livre = registre, livre
        self.argent0 = registre.argent_par_famille()
        self.net0 = livre.net_par_classe()

    def restes(self):
        now = self.registre.argent_par_famille()
        net = self.livre.net_par_classe()
        res = {}
        for f in self.registre.familles.values():
            if f.argent is None: continue
            vu = net.get(f.classe, 0.0) - self.net0.get(f.classe, 0.0)
            res[f.nom] = (now[f.nom] - self.argent0.get(f.nom, 0.0)) - vu
        return res
