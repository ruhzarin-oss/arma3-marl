"""BRANCHER LE SOCLE SUR UN MONDE E1, sans toucher a monde.py.

`brancher( w )` pose sur un Monde vivant :
  - un grand livre qui PARTAGE ses cumuls ( w.flux, w.ext ) : moteur et nouveaux domaines comptent au meme endroit ;
  - ce grand livre a la place de w.transferer, avec le meme contrat ( plafonne a la caisse, rend le montant paye ) :
    tous les paiements du moteur gagnent leur motif, rien d autre ne change ;
  - un registre de ses neuf familles de detenteurs, qui reproduit argent_total et biens_totaux ;
  - la conservation, le rapprochement, le parc, l echeancier, le journal, le hasard par domaine, le calendrier.

Tout est picklable : un monde branche passe dans l instantane et reprend a l identique.

Pour integrer dans le moteur ( a faire par qui tient monde.py ) : appeler `brancher( self )` a la fin de
Monde.__init__, puis remplacer argent_total / biens_totaux / verifier_conservation par le registre et la
conservation du socle, et faire passer importer, exporter_or et les ventes au port ( commerce_exterieur ) par
`payer_l_exterieur` / `recevoir_de_l_exterieur` et `importer` / `exporter` du grand livre."""
from .. import config as C
from . import biens as B, comptes as K, registre as R, objets as O, echeancier as E, journal as J
from . import hasard as H, calendrier as T

# Les motifs de paiement du moteur E1 ( grep de monde.py le 23/09 ) et leur nature dans les comptes nationaux.
MOTIFS_E1 = {
    "salaire": "remuneration", "salaire public": "remuneration",
    "pension": "prestation",
    "tva": "impot_production",
    "impot sur le revenu": "impot_revenu", "impot": "impot_revenu",
    "dividende": "revenu_propriete",
    "benefice marchand": "revenu_propriete",      # D.42 : ce que le marchand preleve sur son affaire
    "revenu agricole": "revenu_propriete",        # D.42 : ce que les membres de la cooperative prelevent
    "subvention": "subvention",
    "amende": "transfert_courant",
    "commande publique": "achat", "achat intrant": "achat", "vente": "achat", "commerce": "achat",
    "nourriture": "achat", "remede": "achat", "electricite": "achat", "carburant du convoi": "achat",
    "fret maritime": "achat",
}


# ------------------------------------------------------------------ les familles du moteur E1
# Des fonctions de module, jamais des lambdas : l instantane doit pouvoir les pickler.
def _menages(w): return w.menages
def _entreprises(w): return w.entreprises.values()
def _marches(w): return w.marches.values()
def _gouvernement(w): return (w.gouv,)
def _stocks_publics(w): return w.publics.values()
def _garnisons(w): return w.garnisons.values()
def _convois(w): return w.convois
def _voyages(w): return getattr(w, "voyages", ())
def _reseau(w): return (w.reseau,)
def _biens_menage(mg): return (("nourriture", mg.garde_manger),)
def _biens_stocks(d): return d.stocks.items()
def _biens_table(d): return d.items()
def _biens_convoi(c): return c.cargaison.items()
def _biens_voyage(v): return v.get("cargaison", {}).items()
def _biens_reseau(r): return (("electricite", r.stock),)


FAMILLES_E1 = (   # nom, secteur, membres, argent, biens, classe
    ("menages", "menages", _menages, "caisse", _biens_menage, "Menage"),
    ("entreprises", "entreprises", _entreprises, "caisse", _biens_stocks, "Entreprise"),
    ("marches", "entreprises", _marches, "caisse", _biens_stocks, "Marche"),
    ("gouvernement", "administrations", _gouvernement, "caisse", None, "Gouvernement"),
    ("stocks_publics", "administrations", _stocks_publics, None, _biens_table, None),
    ("garnisons", "administrations", _garnisons, None, _biens_table, None),
    ("convois", "entreprises", _convois, None, _biens_convoi, None),            # en route : a leur payeur
    ("voyages", "entreprises", _voyages, None, _biens_voyage, None),            # en mer : au marchand qui voyage
    ("reseau", "administrations", _reseau, None, _biens_reseau, None),
)


class Socle:
    __slots__ = ("catalogue", "livre", "creances", "registre", "conservation", "rapprochement", "parc", "echeancier",
                 "journal", "hasard", "calendrier")

    def __init__(self, **pieces):
        for k in self.__slots__: setattr(self, k, pieces[k])


def registre_du_moteur(w, catalogue, sans=()):
    """Le registre des detenteurs d un Monde E1. `sans` : des familles a omettre ( controle positif )."""
    reg = R.Registre(w, catalogue)
    for nom, secteur, membres, argent, biens, classe in FAMILLES_E1:
        if nom not in sans: reg.inscrire(nom, secteur, membres, argent, biens, classe)
    return reg


def brancher(w, strict=False, journal=None):
    """Pose le socle sur le monde `w` et le rend ( aussi en w.socle ). `strict` : refuser tout motif non declare ;
    faux par defaut sur le moteur E1, dont les motifs non declares sont comptes dans livre.non_declares."""
    cat = B.catalogue_du_moteur()
    livre = K.GrandLivre(cat, flux=w.flux, ext=w.ext, strict=strict)
    for nom, nature in MOTIFS_E1.items(): livre.declarer_motif(nom, nature, "moteur_e1")
    for b in C.BIENS: livre.declarer_motif(b, "achat", "moteur_e1")        # achats des menages : le motif est le bien
    w.transferer = livre.transferer
    reg = registre_du_moteur(w, cat)
    hasard = H.Hasard(w.graine)
    parc = O.Parc(hasard)
    s = Socle(catalogue=cat, livre=livre, creances=K.Creances(), registre=reg,
              conservation=R.Conservation(reg, livre, parc), rapprochement=R.Rapprochement(reg, livre), parc=parc,
              echeancier=E.Echeancier(pas_courant=w.pas), journal=J.Journal(journal), hasard=hasard,
              calendrier=T.Calendrier())
    w.socle = s
    return s
