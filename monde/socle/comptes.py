"""LE GRAND LIVRE : tout mouvement d argent et de bien du pays, avec son motif ( socle, choix 1 ).

Pourquoi un grand livre plutot que `Monde.transferer` seul ? Trois faits lus dans le code le 23/09 :
  - `transferer` jetait son motif : impossible de dresser un compte de resultat, des comptes nationaux, ni de savoir
    combien le pays a verse en salaires hier ;
  - un paiement impossible etait tronque sans trace : un salaire impaye disparaissait au lieu de devenir une dette ;
  - l Etat payait ses importations sans passer par `transferer`, et pouvait descendre sous zero sans preteur.

Le contrat de `transferer` ne change pas : il paie au plus ce que le payeur a, et rend le montant paye. Le grand livre
peut donc remplacer `Monde.transferer` sans changer un centime du monde ( porte test_socle_ne_change_pas_le_monde ).
Ce qu il ajoute : chaque paiement est range par ( motif, classe du payeur, classe du receveur ), chaque impaye est
compte, et un paiement impossible peut devenir une CREANCE nommee.

Les motifs sont DECLARES, avec leur nature dans les comptes nationaux ( SCN 2008 / SEC 2010 ) : un motif mal ecrit
creerait sinon une categorie fantome que personne ne voit. En mode strict il est refuse.

Deux monnaies, deux controles. La monnaie centrale ( les caisses, aujourd hui ) se conserve : elle n entre et ne sort
que par l exterieur ( `recevoir_de_l_exterieur`, `payer_l_exterieur` ) et par l emission ( `emettre`,
`detruire_monnaie`, reservees a la banque centrale du domaine 2 ). La monnaie bancaire, que les prets creent et que
les remboursements detruisent, se controlera par l equilibre des bilans ( domaine 2 ).

Les biens : huit natures de flux, et rien ne nait ni ne disparait hors d elles.
  sources : produit ( une recette de production ), importe
  puits   : consomme ( consommation finale ou intrant ), brule, perime, perdu ( accident, casse, incendie ),
            detruit ( combat ), exporte
Un deplacement entre deux detenteurs n est ni une source ni un puits."""
import math

NATURES = {
    "achat":             "P    achats et ventes de biens et de services",
    "remuneration":      "D.1  salaires et traitements",
    "impot_production":  "D.2  impots sur les produits et la production ( TVA, douanes, accises )",
    "subvention":        "D.3  subventions",
    "revenu_propriete":  "D.4  interets, dividendes, revenus preleves par les membres d une cooperative, loyers de terrains",
    "impot_revenu":      "D.5  impots sur le revenu et le patrimoine",
    "cotisation":        "D.61 cotisations sociales",
    "prestation":        "D.62 prestations sociales ( pensions, allocations )",
    "transfert_courant": "D.7  primes et indemnites d assurance, amendes, dons",
    "transfert_capital": "D.9  heritages, aides a l investissement",
    "financier":         "F    depots, prets, remboursements de principal : ni revenu ni depense",
    "illegal":           "hors SCN : pots-de-vin, vol, rancon, contrebande - comptes a part, jamais dans l assiette",
}
SOURCES_BIENS = ("produit", "importe")
PUITS_BIENS = ("consomme", "brule", "perime", "perdu", "detruit", "exporte")
FLUX_BIENS = SOURCES_BIENS + PUITS_BIENS
EXTERIEUR = "Exterieur"            # classe des flux avec le reste du monde
EMISSION = "Emission"              # classe des flux de creation et de destruction de monnaie centrale
TOLERANCE_IMPAYE = 1e-9            # drachmes : en dessous, c est de l arrondi, pas un impaye


class MotifInconnu(KeyError):
    pass


class Motif:
    __slots__ = ("nom", "nature", "domaine")

    def __init__(self, nom, nature, domaine):
        self.nom, self.nature, self.domaine = nom, nature, domaine


class GrandLivre:
    """Le seul chemin de l argent et des biens. `flux` et `ext` peuvent etre ceux d un Monde E1 : moteur et domaines
    nouveaux comptent alors dans les memes cumuls ( brancher.py )."""
    __slots__ = ("catalogue", "motifs", "strict", "flux", "ext", "monnaie", "jour_argent", "jour_biens", "impayes",
                 "non_declares", "net_cumule", "n_transferts")

    def __init__(self, catalogue, flux=None, ext=None, strict=True):
        self.catalogue = catalogue
        self.motifs = {}
        self.strict = strict
        self.flux = flux if flux is not None else {}
        for n in FLUX_BIENS:
            f = self.flux.setdefault(n, {})
            for b in catalogue.noms(): f.setdefault(b, 0.0)
        self.ext = ext if ext is not None else {"entree": 0.0, "sortie": 0.0}
        self.monnaie = {"emise": 0.0, "detruite": 0.0}
        self.jour_argent = {}      # ( motif, classe du payeur, classe du receveur ) -> [ montant, nombre ], du jour
        self.jour_biens = {}       # ( nature, motif, bien ) -> quantite, du jour
        self.impayes = {}          # motif -> [ montant manquant, nombre ], du jour
        self.non_declares = {}     # motif -> nombre d usages ( mode non strict ), cumule
        self.net_cumule = {}       # classe -> recu - paye, cumule aux clotures
        self.n_transferts = 0

    # ------------------------------------------------------------------ les motifs
    def declarer_motif(self, nom, nature, domaine):
        if nature not in NATURES: raise ValueError(f"nature inconnue {nature!r} : {tuple(NATURES)}")
        ancien = self.motifs.get(nom)
        if ancien is not None and ancien.nature != nature:
            raise ValueError(f"motif {nom!r} deja declare en {ancien.nature}, pas en {nature}")
        self.motifs[nom] = Motif(nom, nature, domaine)

    def _motif_inconnu(self, motif):
        if self.strict: raise MotifInconnu(motif)
        self.non_declares[motif] = self.non_declares.get(motif, 0) + 1

    def _ranger(self, motif, payeur, receveur, montant):
        cle = (motif, payeur, receveur)
        r = self.jour_argent.get(cle)
        if r is None: self.jour_argent[cle] = [montant, 1]
        else: r[0] += montant; r[1] += 1

    def _impaye(self, motif, manque):
        r = self.impayes.get(motif)
        if r is None: self.impayes[motif] = [manque, 1]
        else: r[0] += manque; r[1] += 1

    # ------------------------------------------------------------------ l argent, a l interieur
    def transferer(self, de, vers, montant, motif):
        """Meme contrat que Monde.transferer : paie au plus ce que le payeur a, rend le montant paye."""
        if motif not in self.motifs: self._motif_inconnu(motif)
        paye = max(0.0, min(montant, de.caisse))
        de.caisse -= paye; vers.caisse += paye
        self._ranger(motif, type(de).__name__, type(vers).__name__, paye)
        if montant - paye > TOLERANCE_IMPAYE: self._impaye(motif, montant - paye)
        self.n_transferts += 1
        return paye

    def payer_ou_devoir(self, de, vers, montant, motif, creances, jour, echeance=None):
        """Paie ce qui peut l etre ; le reste devient une creance de `vers` sur `de`. Un salaire impaye est une dette
        du patron, pas un salaire qui n a jamais existe. Rend ( montant paye, creance ou None )."""
        paye = self.transferer(de, vers, montant, motif)
        reste = montant - paye
        c = creances.constater(vers, de, reste, motif, jour, echeance) if reste > TOLERANCE_IMPAYE else None
        return paye, c

    # ------------------------------------------------------------------ l argent, aux frontieres du pays
    def recevoir_de_l_exterieur(self, vers, montant, motif):
        """Le reste du monde paie ( une exportation, une aide, un migrant qui arrive avec son epargne )."""
        if motif not in self.motifs: self._motif_inconnu(motif)
        if not 0.0 <= montant < math.inf: raise ValueError(f"montant exterieur invalide : {montant!r}")
        vers.caisse += montant; self.ext["entree"] += montant
        self._ranger(motif, EXTERIEUR, type(vers).__name__, montant)
        return montant

    def payer_l_exterieur(self, de, montant, motif):
        """Le pays paie le reste du monde. Plafonne a la caisse, comme tout paiement : un decouvert est un pret, et
        un pret a un preteur ( domaine 2 ), pas une caisse negative."""
        if motif not in self.motifs: self._motif_inconnu(motif)
        paye = max(0.0, min(montant, de.caisse))
        de.caisse -= paye; self.ext["sortie"] += paye
        self._ranger(motif, type(de).__name__, EXTERIEUR, paye)
        if montant - paye > TOLERANCE_IMPAYE: self._impaye(motif, montant - paye)
        return paye

    def emettre(self, vers, montant, motif):
        """Creation de monnaie centrale. Reservee a la banque centrale ( domaine 2 ) : c est la seule source
        interieure d argent."""
        if motif not in self.motifs: self._motif_inconnu(motif)
        if not 0.0 <= montant < math.inf: raise ValueError(f"montant emis invalide : {montant!r}")
        vers.caisse += montant; self.monnaie["emise"] += montant
        self._ranger(motif, EMISSION, type(vers).__name__, montant)
        return montant

    def detruire_monnaie(self, de, montant, motif):
        if motif not in self.motifs: self._motif_inconnu(motif)
        paye = max(0.0, min(montant, de.caisse))
        de.caisse -= paye; self.monnaie["detruite"] += paye
        self._ranger(motif, type(de).__name__, EMISSION, paye)
        return paye

    # ------------------------------------------------------------------ les biens
    def _ranger_bien(self, nature, motif, bien, q):
        cle = (nature, motif, bien)
        self.jour_biens[cle] = self.jour_biens.get(cle, 0.0) + q

    def deplacer(self, de, vers, bien, q, motif):
        """D un stock a un autre ; rend la quantite reellement deplacee ( au plus ce que `de` avait )."""
        if not 0.0 <= q < math.inf: raise ValueError(f"quantite invalide : {q!r}")
        pris = de._retirer(bien, q)
        if pris > 0.0: vers._ajouter(bien, pris)
        self._ranger_bien("deplace", motif, bien, pris)
        return pris

    def source(self, vers, bien, q, nature, motif):
        if nature not in SOURCES_BIENS: raise ValueError(f"source inconnue {nature!r} : {SOURCES_BIENS}")
        if not 0.0 <= q < math.inf: raise ValueError(f"quantite invalide : {q!r}")
        vers._ajouter(bien, q)
        f, nom = self.flux[nature], self.catalogue.biens[bien].nom      # un bien declare apres coup entre a zero
        f[nom] = f.get(nom, 0.0) + q
        self._ranger_bien(nature, motif, bien, q)
        return q

    def puits(self, de, bien, q, nature, motif):
        """Rend la quantite reellement sortie : on ne consomme pas ce qu on n a pas."""
        if nature not in PUITS_BIENS: raise ValueError(f"puits inconnu {nature!r} : {PUITS_BIENS}")
        if not 0.0 <= q < math.inf: raise ValueError(f"quantite invalide : {q!r}")
        pris = de._retirer(bien, q)
        f, nom = self.flux[nature], self.catalogue.biens[bien].nom
        f[nom] = f.get(nom, 0.0) + pris
        self._ranger_bien(nature, motif, bien, pris)
        return pris

    def produire(self, vers, bien, q, motif): return self.source(vers, bien, q, "produit", motif)
    def importer(self, vers, bien, q, motif): return self.source(vers, bien, q, "importe", motif)
    def consommer(self, de, bien, q, motif): return self.puits(de, bien, q, "consomme", motif)
    def bruler(self, de, bien, q, motif): return self.puits(de, bien, q, "brule", motif)
    def perimer(self, de, bien, q, motif): return self.puits(de, bien, q, "perime", motif)
    def perdre(self, de, bien, q, motif): return self.puits(de, bien, q, "perdu", motif)
    def detruire(self, de, bien, q, motif): return self.puits(de, bien, q, "detruit", motif)
    def exporter(self, de, bien, q, motif): return self.puits(de, bien, q, "exporte", motif)

    # ------------------------------------------------------------------ les comptes du jour
    def net_par_classe(self):
        """Pour chaque classe de detenteur : ce qu elle a recu moins ce qu elle a paye, depuis le debut, jour en cours
        compris. C est ce que le rapprochement compare a la variation de sa caisse."""
        net = dict(self.net_cumule)
        for (m, p, r), (s, n) in self.jour_argent.items():
            net[p] = net.get(p, 0.0) - s
            net[r] = net.get(r, 0.0) + s
        return net

    def cloturer_jour(self):
        """Rend les comptes du jour et remet a zero les compteurs journaliers ; les cumuls ( flux, ext, monnaie )
        restent. Une fois par jour : c est la matiere de la statistique publique ( domaine 6 )."""
        argent = sorted((m, p, r, s, n) for (m, p, r), (s, n) in self.jour_argent.items())
        par_nature = {}
        for m, p, r, s, n in argent:
            nature = self.motifs[m].nature if m in self.motifs else "non_declare"
            par_nature[nature] = par_nature.get(nature, 0.0) + s
            self.net_cumule[p] = self.net_cumule.get(p, 0.0) - s
            self.net_cumule[r] = self.net_cumule.get(r, 0.0) + s
        res = {"argent": argent, "par_nature": par_nature,
               "biens": sorted((n, m, self.catalogue.biens[b].nom, q) for (n, m, b), q in self.jour_biens.items()),
               "impayes": {m: tuple(v) for m, v in sorted(self.impayes.items())}}
        self.jour_argent = {}; self.jour_biens = {}; self.impayes = {}
        return res


class Creance:
    """Une dette nommee : `debiteur` doit `montant` drachmes a `creancier`, pour `motif`, depuis le jour `nee`."""
    __slots__ = ("id", "creancier", "debiteur", "montant", "motif", "nee", "echeance")

    def __init__(self, id, creancier, debiteur, montant, motif, nee, echeance):
        self.id, self.creancier, self.debiteur, self.montant = id, creancier, debiteur, montant
        self.motif, self.nee, self.echeance = motif, nee, echeance


class Creances:
    """Les dettes entre detenteurs. Une creance n est PAS de la monnaie : elle ne compte pas dans la conservation de
    l argent, elle dit qu un paiement est du. Le domaine 2 y ajoutera l interet ; le domaine 21 le recouvrement."""
    __slots__ = ("actives", "par_debiteur", "prochain_id", "reglees", "abandonnees")

    def __init__(self):
        self.actives = {}          # id -> Creance
        self.par_debiteur = {}     # debiteur -> [ id ]
        self.prochain_id = 0
        self.reglees = 0           # nombre de creances soldees
        self.abandonnees = {}      # raison -> montant perdu par les creanciers

    def constater(self, creancier, debiteur, montant, motif, jour, echeance=None):
        if not 0.0 < montant < math.inf: raise ValueError(f"montant de creance invalide : {montant!r}")
        if echeance is not None and echeance < jour: raise ValueError("echeance anterieure a la naissance de la dette")
        c = Creance(self.prochain_id, creancier, debiteur, float(montant), motif, jour, echeance)
        self.prochain_id += 1
        self.actives[c.id] = c
        self.par_debiteur.setdefault(debiteur, []).append(c.id)
        return c

    def _retirer(self, c):
        del self.actives[c.id]
        ids = self.par_debiteur[c.debiteur]
        ids.remove(c.id)
        if not ids: del self.par_debiteur[c.debiteur]

    def regler(self, c, livre, montant=None):
        """Le debiteur paie ce qu il peut ( au plus `montant`, au plus la dette ), sous le motif d origine : un salaire
        paye en retard reste une remuneration. Rend le montant paye."""
        if self.actives.get(c.id) is not c: raise KeyError(f"creance {c.id} inconnue ou soldee")
        voulu = c.montant if montant is None else min(montant, c.montant)
        paye = max(0.0, min(voulu, c.debiteur.caisse))
        if paye > 0.0: paye = livre.transferer(c.debiteur, c.creancier, paye, c.motif)
        c.montant -= paye
        if c.montant <= 1e-9:
            self._retirer(c); self.reglees += 1
        return paye

    def abandonner(self, c, raison):
        """Le creancier renonce ( faillite, deces, prescription ) : la dette disparait, aucun argent ne bouge.
        Rend le montant perdu."""
        if self.actives.get(c.id) is not c: raise KeyError(f"creance {c.id} inconnue ou soldee")
        self._retirer(c)
        self.abandonnees[raison] = self.abandonnees.get(raison, 0.0) + c.montant
        return c.montant

    def de(self, debiteur):
        return [self.actives[i] for i in self.par_debiteur.get(debiteur, ())]

    def total(self):
        return math.fsum(c.montant for c in self.actives.values())
