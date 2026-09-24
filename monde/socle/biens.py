"""LES BIENS FONGIBLES : le catalogue, et le stock de chaque detenteur ( socle, choix 2 ).

Un bien fongible se compte en quantite : une unite de nourriture en vaut une autre. Un vehicule, une arme, un
batiment ne sont PAS fongibles - ils ont une identite, un proprietaire, une usure : voir objets.py.

Deux choix, pour l echelle et pour Rust :
  - chaque bien a un identifiant ENTIER stable, son rang de declaration : un stock est une table d entiers, portable
    telle quelle ( u16 -> f64 ) ;
  - un stock est CREUX : seuls les biens presents occupent de la memoire. Le moteur E1 donne a chaque detenteur un
    dictionnaire des neuf biens ; a quatre-vingts biens ( molecules, munitions par calibre, pieces ), c est la memoire
    qui cederait.

Un stock ne s ecrit JAMAIS a la main : seulement par le grand livre ( comptes.GrandLivre ), qui compte chaque source
et chaque puits. C est ce qui rend la conservation verifiable."""
import math, re
from .. import config as C

FAMILLES = ("aliment", "eau", "matiere_premiere", "energie", "materiau", "chimie", "produit_fini", "piece", "sante",
            "munition")
CATEGORIES_TVA = ("normale", "reduite", "super_reduite", "exoneree")
NOM_VALIDE = re.compile(r"^[a-z][a-z0-9_]{0,39}$")     # francais sans accent : portable en enum Rust
ID_MAX = 65535                  # un bien tient sur 16 bits
PRIX_MAX = 1e9                  # drachmes par unite : au-dela, c est une erreur d unite, pas un prix
MASSE_MAX_KG = 1e5              # par unite : une unite peut etre une tonne de minerai, pas un navire
VOLUME_MAX_L = 1e6


class Bien:
    """Un bien fongible. Chaque champ sert une decision, une mesure ou la conservation :
      prix_monde       drachmes par unite au port : l echange avec l exterieur, la reference des marches
      categorie_tva    la categorie a laquelle le fisc applique son taux ( domaine 6 )
      masse_kg         par unite : la charge d un camion, d une cale ( domaines 14 et 15 ) ; None = pas encore calibre
      volume_l         par unite : la place dans un entrepot ; None = pas encore calibre
      conservation_j   duree de vie en stock, en jours ; inf si le bien ne se perime pas ( domaines 9 et 17 )
      source           d ou viennent ces chiffres, ou « a calibrer »"""
    __slots__ = ("id", "nom", "famille", "unite", "prix_monde", "categorie_tva", "masse_kg", "volume_l",
                 "conservation_j", "source")

    def __init__(self, id, nom, famille, unite, prix_monde, categorie_tva="normale", masse_kg=None, volume_l=None,
                 conservation_j=math.inf, source="a calibrer"):
        if not (isinstance(id, int) and 0 <= id <= ID_MAX): raise ValueError(f"identifiant de bien hors [0 ; {ID_MAX}] : {id!r}")
        if not isinstance(nom, str) or not NOM_VALIDE.match(nom): raise ValueError(f"nom de bien invalide : {nom!r}")
        if famille not in FAMILLES: raise ValueError(f"{nom} : famille inconnue {famille!r}")
        if not 0.0 < prix_monde <= PRIX_MAX: raise ValueError(f"{nom} : prix mondial hors ]0 ; {PRIX_MAX:g}] : {prix_monde!r}")
        if categorie_tva not in CATEGORIES_TVA: raise ValueError(f"{nom} : categorie de TVA inconnue {categorie_tva!r}")
        if masse_kg is not None and not 0.0 <= masse_kg <= MASSE_MAX_KG: raise ValueError(f"{nom} : masse hors bornes {masse_kg!r}")
        if volume_l is not None and not 0.0 <= volume_l <= VOLUME_MAX_L: raise ValueError(f"{nom} : volume hors bornes {volume_l!r}")
        if not conservation_j > 0.0: raise ValueError(f"{nom} : duree de conservation non positive {conservation_j!r}")
        self.id, self.nom, self.famille, self.unite = id, nom, famille, unite
        self.prix_monde, self.categorie_tva = float(prix_monde), categorie_tva
        self.masse_kg, self.volume_l, self.conservation_j, self.source = masse_kg, volume_l, conservation_j, source

    def __repr__(self): return f"Bien({self.id}, {self.nom})"


class Catalogue:
    """Les biens du pays, dans leur ordre de declaration. Chaque domaine y declare les siens a sa livraison ; aucun
    ne redeclare un bien qui existe."""
    __slots__ = ("biens", "par_nom")

    def __init__(self):
        self.biens = []
        self.par_nom = {}

    def declarer(self, nom, famille, unite, prix_monde, **champs):
        if nom in self.par_nom: raise ValueError(f"bien {nom!r} deja declare : un domaine etend, il ne duplique pas")
        b = Bien(len(self.biens), nom, famille, unite, prix_monde, **champs)
        self.biens.append(b); self.par_nom[nom] = b
        return b

    def __getitem__(self, cle): return self.biens[cle] if isinstance(cle, int) else self.par_nom[cle]
    def __len__(self): return len(self.biens)
    def __iter__(self): return iter(self.biens)
    def id(self, nom): return self.par_nom[nom].id
    def noms(self): return [b.nom for b in self.biens]

    def non_calibres(self):
        """Les biens dont la masse ou le volume manque encore : le fret ne doit pas s en servir avant calibration."""
        return [b.nom for b in self.biens if b.masse_kg is None or b.volume_l is None]


# Les neuf biens du moteur E1 : famille, unite, categorie de TVA. Masse, volume et conservation ne sont pas calibres :
# chacun le sera par son domaine ( nourriture : 9 ; minerais : 10 ; energie : 11 ; remedes : 16-17 ).
# Categories de TVA : modele grec ( normale 24 %, reduite 13 % pour l alimentation, super-reduite 6 % pour les
# medicaments ) ; les TAUX appartiennent au domaine 6, le moteur E1 applique encore un taux unique.
BIENS_E1 = {
    "nourriture":  ("aliment", "ration d un habitant pour un jour ( config.NOURRITURE_PAR_JOUR = 1 )", "reduite"),
    "fer":         ("matiere_premiere", "unite de minerai du moteur E1", "normale"),
    "zinc":        ("matiere_premiere", "unite de minerai du moteur E1", "normale"),
    "or":          ("matiere_premiere", "unite d or du moteur E1", "normale"),
    "petrole":     ("energie", "unite de brut du moteur E1", "normale"),
    "carburant":   ("energie", "unite du moteur E1 : 0,03 par km et par vehicule ( config.CARBURANT_PAR_KM )", "normale"),
    "electricite": ("energie", "unite du reseau du moteur E1", "normale"),
    "outils":      ("produit_fini", "un outil : +25 % de production, use en 200 heures ( config.USURE_OUTIL_H )", "normale"),
    "remedes":     ("sante", "un traitement complet d une maladie", "super_reduite"),
}


def catalogue_du_moteur():
    """Le catalogue de depart : les neuf biens du moteur E1, dans l ordre de config.BIENS ( identifiants 0 a 8 ),
    a leurs prix de config.PRIX_MONDE. Les domaines suivants y ajoutent les leurs."""
    cat = Catalogue()
    for nom in C.BIENS:
        famille, unite, tva = BIENS_E1[nom]
        cat.declarer(nom, famille, unite, C.PRIX_MONDE[nom], categorie_tva=tva,
                     source="moteur E1 ( config.py ) ; masse, volume, conservation a calibrer")
    return cat


class Stock:
    """Les biens fongibles d un detenteur : identifiant de bien -> quantite. Creux : un bien absent ne coute rien.
    Lecture libre ; ecriture reservee au grand livre ( _ajouter, _retirer ), qui compte sources et puits."""
    __slots__ = ("q",)

    def __init__(self):
        self.q = {}

    def __getitem__(self, b): return self.q.get(b, 0.0)
    def __contains__(self, b): return b in self.q
    def __len__(self): return len(self.q)
    def items(self): return self.q.items()

    def _ajouter(self, b, q):
        self.q[b] = self.q.get(b, 0.0) + q

    def _retirer(self, b, q):
        """Retire au plus ce qui est la ; rend la quantite retiree. Un bien retire en entier ( reste zero EXACT )
        quitte la table : rien n est arrondi, donc rien n est cree ni detruit."""
        dispo = self.q.get(b, 0.0)
        q = min(q, dispo)
        if not q > 0.0: return 0.0
        reste = dispo - q
        if reste == 0.0: del self.q[b]
        else: self.q[b] = reste
        return q
