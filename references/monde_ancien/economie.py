"""L economie reelle : des entreprises qui produisent avec du travail et des intrants, trois marches regionaux ( Kavala,
Athira, Pyrgos ) ou les prix se forment par l offre et la demande, des convois qui transportent et brulent du carburant,
un reseau electrique, des salaires, des impots, et le port de Kavala ouvert sur le monde.
Tout mouvement d argent ou de bien passe par `transferer` / `deplacer` : c est ce qui rend la conservation verifiable."""
import math
from . import config as C


class Entreprise:
    """Un site de production. Proprietaire : un patron ( prive ) ; les fermes sont des cooperatives de village."""
    def __init__(self, lieu, type_):
        self.lieu, self.type = lieu, type_
        self.role, self.intrants, self.produits = C.RECETTES[type_]
        self.stocks = {b: 0.0 for b in C.BIENS}
        self.caisse = 5000.0 if type_ != "ferme" else 0.0
        self.proprietaire = None           # Habitant ( patron ) ou None ( cooperative )
        self.heures_outils = 0.0
        self.heures_du_jour = {}           # habitant -> heures travaillees aujourd hui
        self.produit_du_jour = {b: 0.0 for b in C.BIENS}
        self.activite = 1.0                # part de la capacite utilisee : l entreprise produit pour vendre, pas pour stocker

    @property
    def id(self): return f"{self.type}@{self.lieu.id}"


class Marche:
    """Le marche d une capitale : les marchands achetent aux producteurs et vendent aux menages, a un prix qui suit
    l offre et la demande du jour."""
    def __init__(self, lieu):
        self.lieu = lieu
        self.stocks = {b: 0.0 for b in C.BIENS}
        self.prix = dict(C.PRIX_MONDE)
        self.caisse = 20000.0
        self.demande = {b: 0.0 for b in C.BIENS}
        self.offre = {b: 0.0 for b in C.BIENS}
        self.marge = 0.10                  # les marchands achetent 10 % sous le prix de vente

    def ajuster_prix(self):
        """Une fois par jour : le prix monte si la demande depasse l offre, baisse sinon ; borne a [0,2 ; 5] fois le
        prix mondial. Les biens que personne n a demandes ni offerts gardent leur prix."""
        for b in C.BIENS:
            d, o = self.demande[b], self.offre[b] + self.stocks[b]
            if d + o <= 0: continue
            self.prix[b] *= math.exp(0.35 * (d - o) / (d + o))
            self.prix[b] = min(5 * C.PRIX_MONDE[b], max(0.2 * C.PRIX_MONDE[b], self.prix[b]))
            self.demande[b] = 0.0; self.offre[b] = 0.0


class Convoi:
    def __init__(self, id, origine, destination, cargaison, depart, arrivee, payeur, motif, conducteur):
        self.id, self.origine, self.destination = id, origine, destination
        self.cargaison, self.depart, self.arrivee = cargaison, depart, arrivee
        self.payeur, self.motif, self.conducteur = payeur, motif, conducteur


class Reseau:
    """Le reseau electrique national : les centrales y injectent, les sites y puisent, au tarif fixe par l Etat."""
    def __init__(self):
        self.stock = 200.0
        self.tarif = C.PRIX_MONDE["electricite"]
        self.capacite = 2000.0
