"""DOMAINE 28 - TOURISME : LES VISITEURS ETRANGERS, L HOTELLERIE ET LA RESTAURATION ( 27/09, Younes : « exporter
( tourisme, peche, huile ) : le vrai remede » ).

Pourquoi ce domaine. Une ile de 100 000 habitants sur la terre de Stratis ou de Malden ressemble a Malte : elle importe
presque toute sa nourriture et la paie par ses services. Sans exportations, la guerre des iles a montre ( 27/09 ) que
les reserves de change s epuisent - Stratis a -55 millions d euros au jour 349, meme en paix vers le jour 265 - et que
plus rien ne s importe : 98 % des menages sans nourriture. Le tourisme est la premiere exportation des iles grecques
( Banque de Grece 2023 : 20,6 milliards d euros de recettes, 18 % des exportations de biens et services ).

FICHE
1. Classes. EtablissementTouristique ( les hotels, pensions et restaurants d un lieu, comptes ensemble : lits, caisse,
   proprietaire, personnel vise, compteurs du jour ), Tourisme ( l etat du domaine : etablissements, facteur de risque
   de l ile, series ). Aucune colonne par habitant : les salaries sont ceux du domaine 4, au metier « hotellerie »
   ( un metier du moteur ajoute a la fin de config.ROLES, effectif 0 a la naissance du monde : on y entre par
   l embauche ) ; les visiteurs sont des nuitees, pas des corps.
2. Invariants. L argent des visiteurs entre par le grand livre ( recevoir_de_l_exterieur, motif recette_touristique,
   ligne services de la balance des paiements : domaine 7 ) dans la caisse de l etablissement, en monnaie de l ile au
   taux du jour ( les visiteurs paient en euros ). Il en sort par la paie du domaine 4 ( l etablissement est un
   employeur declare ), la TVA a l Etat ( taux reduit du catalogue : 13 % en Grece pour l hebergement et la
   restauration ), la nourriture des visiteurs ( au marche de son lieu ce qui depasse un jour de la demande des
   habitants, importee par lui pour le reste ; consommee : livre.flux ), les
   fournitures importees ( domaine 7, declarer_import, sous le controle des changes ) et, chaque mois, le dividende a
   son proprietaire ; il credite a ses employes les heures pointees a leur poste ( 17 h 50, avant la paie ). Le
   fonds de roulement de depart vient de l etranger ( investissement direct, domaine 7 ). Rien ne
   nait ailleurs. Nuitees servies = min( demande, lits, personnel / personnel par lit occupe, nourriture achetee ).
3. Decision `effectif_saison` ( chaque lundi a 6 h, chaque etablissement ) : fermer, demi, plein, renfort. Traits :
   occupation attendue du mois ( le calendrier des arrivees, que la profession connait ), occupation des 7 derniers
   jours, caisse en jours de personnel plein, facteur de risque ( avis aux voyageurs ), personnel present sur personnel
   plein, prix de la nourriture au marche sur le prix mondial. Note ( horizon 7 jours : une semaine de saison ) :
   chaque jour, ( nuitees servies / demande du jour + marge du jour / recette possible ) / 2 - servir ceux qui
   viennent, sans payer un personnel sans clients. Regle : fermer si l occupation attendue ( risque compris ) est sous
   15 % ; demi si la caisse tient moins de 7 jours de personnel plein ; plein sinon. Temoin : toujours plein.
4. Evenements. Individuels : etablissement_ouvert. Comptes : nuitees, nuitees_refusees, recettes_touristiques,
   repas_touristes, repas_touristes_manquants, fournitures_manquantes, fin_de_saison.
5. Liens. Lit le calendrier ( mois ), le taux de change et les devises ( domaine 7 ), les prix et les stocks du
   marche ( domaine 3 ), la quarantaine du gouvernement ( un lieu en quarantaine ou occupe ne recoit personne ). Paie
   et recoit : recettes ( exterieur -> etablissement ), investissement direct ( exterieur -> etablissement, a
   l installation ), salaires ( domaine 4 ), TVA ( -> Etat ), nourriture ( -> marche ), fournitures ( -> exterieur ),
   dividende ( -> menage proprietaire ). Donne aux autres : fixer_risque( p, facteur, motif ) ( la guerre : l horloge
   de la guerre des iles le pose ), etat_tourisme( p ).
6. Portes : tests_d28_tourisme.py.
7. Arma : aucun objet. Les hotels sont des batiments du domaine 13 ( pas encore relies ) ; un visiteur n a pas de corps.
8. Cout. Une passe par jour sur les etablissements ( un par lieu habitable : 8 sur Stratis ), une passe sur la table
   pour compter le personnel ; negligeable devant le moteur."""
import math
import numpy as np
from .. import config as C, population as PO
from ..socle import decision as D, registre as R
from . import d03_economie as ECO, d04_travail as TR, d06_etat as ET, d07_exterieur as X
from .pays import EUROS_PAR_DRACHME

METIER = "hotellerie"
# Lits touristiques par habitant ( hotels et locations ). Grece : 1,26 million de lits d hotel ( Chambre hoteliere
# 2023 ) et environ 0,6 million en location courte duree pour 10,4 millions d habitants : 0,18 ; Egee du Sud et Crete
# 0,4 a 1 ; Malte 0,09 d hotel plus les locations. Une ile de 100 000 habitants sur si peu de terre : 0,25 ( a calibrer ).
LITS_PAR_HABITANT = 0.25
# Poids des lieux dans l offre de lits : la capitale et ses plages, les villes, les villages ( a calibrer ).
POIDS_LIEU = {"capitale": 4.0, "ville": 2.0, "village": 1.0}
# Occupation des lits par mois ( janvier a decembre ) : profil des iles grecques, ouvertes de mai a octobre ( INSETE,
# ELSTAT, ordre de grandeur ; moyenne annuelle 0,43 : a calibrer ).
OCCUPATION_MOIS = (0.08, 0.08, 0.12, 0.30, 0.55, 0.78, 0.90, 0.93, 0.78, 0.45, 0.10, 0.08)
# Depense d un visiteur par nuitee, tout compris ( hebergement, repas, achats, transport local ) : Banque de Grece 2023,
# 20,6 milliards d euros pour environ 220 millions de nuitees, 94 euros.
DEPENSE_NUIT_EUR = 95.0
# Personnel par lit occupe, hotels et restaurants ensemble : environ 400 000 emplois d ete en Grece ( ELSTAT, enquete
# forces de travail, hebergement et restauration ) pour environ 1,1 million de lits occupes en ete : 0,35 ; 0,30 ( a calibrer ).
PERSONNEL_PAR_LIT_OCCUPE = 0.30
RATION_PAR_NUIT = 1.0                 # un visiteur mange comme un habitant : une ration du moteur par jour
# La nourriture des visiteurs : l etablissement achete au marche de son lieu ce qui depasse un jour de la demande des
# habitants, et importe lui-meme le reste ( grossistes et centrales d achat des hotels ; sous le controle des changes ).
# Sans cette regle, les visiteurs mangeaient le stock des habitants : 6,7 % de menages sans nourriture en juin sur une
# petite Stratis ( fumee du 27/09 ). ( a calibrer )
RESERVE_HABITANTS_J = 1.0
# Fournitures importees ( linge, produits d accueil, boissons, entretien ) : le contenu en importations du tourisme grec,
# 20 a 30 % des recettes ( nourriture comprise ; la nourriture est ici achetee au marche ) : 15 % hors taxe ( a calibrer ).
PART_FOURNITURES = 0.15
FONDS_DE_ROULEMENT_J = 30             # jours de personnel plein apportes par l investisseur etranger a l installation
RESERVE_DIVIDENDE_J = 30              # le dividende du mois laisse en caisse 30 jours de personnel plein
# Avis aux voyageurs : l ile ou l on se bat ( champ de bataille ) et l ile belligerante qui ne combat pas chez elle.
# Ukraine 2022 et Israel 2024 : 70 a 90 % d arrivees en moins ( a calibrer ).
RISQUE_CHAMP_DE_BATAILLE = 0.15
RISQUE_BELLIGERANT = 0.5
ACTIONS = ("fermer", "demi", "plein", "renfort")
FACTEURS_EFFECTIF = (0.0, 0.5, 1.0, 1.25)
FERMER, DEMI, PLEIN, RENFORT = range(4)
SEUIL_OUVERTURE = 0.15
HORIZON_EFFECTIF = 7
EPS = 1e-9


class EtablissementTouristique:
    """Les hotels, pensions et restaurants d un lieu, comptes ensemble. Detient une caisse ( famille « tourisme » du
    registre ), aucun bien : la nourriture achetee est servie et consommee le jour meme."""
    __slots__ = ("id", "lieu", "lits", "caisse", "proprietaire", "vise", "jour_decision", "nuitees_7j", "recettes",
                 "repas", "nuitees_total", "demande_jour", "servies_jour", "marge_jour", "possible_jour")

    def __init__(self, lieu, lits, proprietaire):
        if not lits > 0: raise ValueError(f"{lieu.id} : lits invalides {lits!r}")
        self.id, self.lieu, self.lits, self.caisse, self.proprietaire = f"tourisme@{lieu.id}", lieu, int(lits), 0.0, proprietaire
        self.vise = 0                       # personnel vise ( postes ouverts au domaine 4 )
        self.jour_decision = -1             # le jour de son dernier choix de personnel
        self.nuitees_7j = []                # nuitees servies des 7 derniers jours
        self.recettes = self.repas = self.nuitees_total = 0.0
        self.demande_jour = self.servies_jour = self.marge_jour = self.possible_jour = 0.0


class Tourisme:
    __slots__ = ("etablissements", "risque", "motif_risque", "decideur", "serie", "cumul")

    def __init__(self):
        self.etablissements = []
        self.risque = 1.0
        self.motif_risque = "paix"
        self.decideur = None
        self.serie = []                     # ( jour, nuitees, demande, recettes, personnel, prix d une nuitee )
        self.cumul = {"nuitees": 0.0, "recettes": 0.0, "tva": 0.0, "fournitures": 0.0, "repas": 0.0, "repas_manquants": 0.0,
                      "dividendes": 0.0, "investissement": 0.0}


def _dom(p): return p.domaine("tourisme")
def _membres(w): return tuple(w.pays.domaines["tourisme"].etablissements)


# ================================================================== la demande
def mois(p): return p.socle.calendrier.date(p.pas).month


def avis(p):
    """L avis aux voyageurs effectif : 0 sous blocus ( 29/09, d07.sous_blocus : l ennemi tient tous les ports de l ile -
    aucun navire, et les compagnies ne volent pas vers une ile en guerre dont l ennemi tient le port ), le facteur de
    risque sinon ( fixer_risque )."""
    return 0.0 if X.sous_blocus(p) else _dom(p).risque


def occupation_attendue(p, mois_=None):
    """L occupation des lits que la profession attend ce mois-ci, avis aux voyageurs compris."""
    m = mois(p) if mois_ is None else int(mois_)
    return OCCUPATION_MOIS[m - 1] * avis(p)


def _ferme(p, e):
    """Un lieu en quarantaine ( une epidemie, ou une zone occupee par l ennemi : guerre/moteur.py ) ne recoit personne."""
    return e.lieu.id in p.w.gouv.lois.get("quarantaine", ())


def _personnel_ids(p, e):
    tb = p.w.table; n = tb.n
    return np.nonzero((tb.vivant[:n] == 1) & (tb.travail[:n] == e.lieu.n) & (tb.role[:n] == PO.CODE_ROLE[METIER]))[0]


def _cout_jour_plein(p, e, occupation=None):
    """Ce que coute par jour le personnel plein du mois : postes x heures de l horaire x taux du metier x charges."""
    occ = occupation_attendue(p) if occupation is None else occupation
    postes = math.ceil(e.lits * occ * PERSONNEL_PAR_LIT_OCCUPE)
    h = TR.HEURES_HORAIRE[PO.TRAVAIL[METIER][1]]
    return postes * h * TR.taux_de_base(METIER) * (1.0 + TR.TAUX_EMPLOYEUR)


def _prix_nuit(p):
    """La depense d une nuitee en monnaie de l ile, au taux du jour ( euros par unite )."""
    return DEPENSE_NUIT_EUR / max(EPS, X.taux_de_change(p))


# ================================================================== le jour touristique ( 21 h )
def _jour(p):
    d = _dom(p); w = p.w; L = p.socle.livre
    if not d.etablissements: return
    rng = p.du_jour("tourisme_arrivees")
    bruit = rng.lognormal(0.0, 0.10, len(d.etablissements))
    occ = occupation_attendue(p)
    prix = _prix_nuit(p)
    tva = ET._etat(p).fisc.tva["reduite"] if p.a("etat") else 0.0
    tot_n = tot_d = tot_r = tot_pers = 0.0
    for k, e in enumerate(d.etablissements):
        demande = 0.0 if _ferme(p, e) else e.lits * occ * float(bruit[k])
        personnel = len(_personnel_ids(p, e))
        cap = min(float(e.lits), personnel / PERSONNEL_PAR_LIT_OCCUPE)
        voulu = min(demande, cap)
        # la nourriture des visiteurs : au marche du lieu ce qui depasse un jour de la demande des habitants ( le marche
        # ne compte comme demande que ce qu il vend : le reste, importe par l etablissement lui-meme, ne fait pas monter
        # son prix - devises de la banque centrale ; sans elles, pas de repas, pas de visiteur )
        m = w.marches.get(e.lieu.marche.id) if e.lieu.marche is not None else None
        servies = cout_repas = 0.0
        if voulu > EPS:
            besoin = voulu * RATION_PAR_NUIT
            q = 0.0
            if m is not None:
                em = p.domaine("economie").marches.get(m.lieu.id) if p.a("economie") else None
                reserve = RESERVE_HABITANTS_J * (em.demande_lisse.get("nourriture", 0.0) if em is not None else 0.0)
                q = min(besoin, max(0.0, m.stocks["nourriture"] - reserve))
                if q > EPS and m.prix["nourriture"] > 0:
                    paye = L.transferer(e, m, q * m.prix["nourriture"], "nourriture")
                    q = paye / m.prix["nourriture"]; cout_repas += paye
                    m.stocks["nourriture"] -= q; m.demande["nourriture"] += q
                    L.flux["consomme"]["nourriture"] += q
            reste = besoin - q
            if reste > EPS:
                tmp = X.StockE1({}, p.socle.catalogue)
                qi, pi = X.importer_au_port(p, e, tmp, "nourriture", reste, "import_biens")
                if qi > EPS: L.consommer(tmp, X._id(p, "nourriture"), qi, "repas_touristes")
                q += qi; cout_repas += pi
                if reste - qi > EPS: p.compter("repas_touristes_manquants", reste - qi); d.cumul["repas_manquants"] += reste - qi
            e.repas += q; d.cumul["repas"] += q
            p.compter("repas_touristes", q)
            servies = q / RATION_PAR_NUIT
        refusees = max(0.0, demande - servies)
        recette = servies * prix
        if recette > EPS:
            L.recevoir_de_l_exterieur(e, recette, "recette_touristique")
            e.recettes += recette; d.cumul["recettes"] += recette
            ht = recette / (1.0 + tva)
            if tva > 0:
                t = L.transferer(e, w.gouv, recette - ht, "tva"); w.tva_percue += t; d.cumul["tva"] += t
            fob = PART_FOURNITURES * ht
            paye_f = X.declarer_import(p, e, fob / (1.0 + X.FRET.get("produit_fini", 0.05)), "produit_fini", motif="import_biens")
            if paye_f <= 0: p.compter("fournitures_manquantes", fob)
            d.cumul["fournitures"] += paye_f
        else: ht = 0.0
        e.nuitees_7j.append(servies); del e.nuitees_7j[:-7]
        e.nuitees_total += servies; d.cumul["nuitees"] += servies
        cout_pers = sum(TR.cout_horaire(p, PO.Habitant(w.table, int(i))) for i in _personnel_ids(p, e)) * TR.HEURES_HORAIRE[PO.TRAVAIL[METIER][1]]
        e.demande_jour, e.servies_jour = demande, servies
        e.possible_jour = e.lits * occ * prix / (1.0 + tva)
        e.marge_jour = ht - cout_repas - cout_pers - PART_FOURNITURES * ht
        tot_n += servies; tot_d += demande; tot_r += recette; tot_pers += personnel
        p.compter("nuitees", servies); p.compter("nuitees_refusees", refusees)
        p.compter("recettes_touristiques", recette)
        # la note de la semaine de personnel choisie lundi : servir ceux qui viennent, sans payer un personnel sans clients
        sert = servies / demande if demande > EPS else 1.0
        marge = max(-1.0, min(1.0, e.marge_jour / max(EPS, e.possible_jour, cout_pers)))
        if d.decideur is not None: d.decideur.noter(e.id, 0.5 * (sert + marge), p.jour)
    d.serie.append((p.jour, tot_n, tot_d, tot_r, tot_pers, prix)); del d.serie[:-400]


# ================================================================== les heures ( 17 h 50 )
def _heures(p):
    """17 h 50, avant la paie de 18 h : l etablissement credite a chacun de ses employes les heures ou le domaine 4 l a
    pointe a son poste depuis la derniere paie ( ses equipes de jour et de nuit ). Pas une heure de plus : la paie
    confronte les heures creditees au pointage. ( 27/09 : sans ce credit, 587 employes travaillaient sans etre payes. )"""
    tb = p.w.table; n = tb.n
    ids = np.nonzero((tb.vivant[:n] == 1) & (tb.role[:n] == PO.CODE_ROLE[METIER]) & (tb.travail[:n] >= 0))[0]
    if not len(ids): return
    pt = p.col("habitant", "tr_pointage")[ids].astype(np.float64) * (C.MINUTES_PAR_PAS / 60.0)
    tb.heures[ids] = np.maximum(tb.heures[ids], pt)


# ================================================================== la decision du lundi
def _observer(c):
    p, e = c
    m = p.w.marches.get(e.lieu.marche.id) if e.lieu.marche is not None else None
    plein = max(1, math.ceil(e.lits * max(occupation_attendue(p), EPS) * PERSONNEL_PAR_LIT_OCCUPE))
    cout = max(EPS, _cout_jour_plein(p, e))
    pm = C.PRIX_MONDE["nourriture"]
    return (min(1.0, occupation_attendue(p)),
            min(1.0, sum(e.nuitees_7j) / max(1.0, 7.0 * e.lits)),
            min(1.0, max(0.0, e.caisse) / (30.0 * cout)),
            min(1.0, avis(p)),
            min(1.0, len(_personnel_ids(p, e)) / plein),
            min(1.0, (m.prix["nourriture"] / pm / 3.0) if m is not None else 1.0))


def _regle(x, c):
    if x[0] < SEUIL_OUVERTURE: return FERMER
    if x[2] < 7.0 / 30.0: return DEMI
    return PLEIN


def _temoin(x, c, rng): return PLEIN


POINT = D.PointDeDecision(
    "effectif_saison", "tourisme",
    (("occupation_mois", "le calendrier des arrivees, publie par la profession, et l avis aux voyageurs"),
     ("occupation_7j", "ses nuitees servies des 7 derniers jours"),
     ("caisse_j", "sa caisse, en 30 jours de personnel plein"),
     ("risque", "l avis aux voyageurs de l ile ( guerre )"),
     ("personnel", "son personnel present, sur le personnel plein du mois"),
     ("prix_nourriture", "le prix de la nourriture a son marche, sur trois fois le prix mondial")),
    ACTIONS, _observer, _regle, _temoin,
    "chaque jour de la semaine qui suit : ( nuitees servies / demande + marge / recette possible ) / 2, pour CET etablissement",
    horizon_j=HORIZON_EFFECTIF)


def _lundi(p):
    """6 h le lundi ( et le premier matin d un etablissement ) : chaque etablissement choisit son personnel de la
    semaine ; le domaine 4 embauche ( postes ouverts, 6 h 20 ) ; au-dessus du vise, les derniers entres partent ( fin
    de saison )."""
    lundi = p.socle.calendrier.jour_semaine(p.pas) == 0
    d = _dom(p); w = p.w
    for e in d.etablissements:
        if not lundi and e.jour_decision >= 0: continue
        e.jour_decision = p.jour
        a = d.decideur.decider(e.id, (p, e))
        plein = math.ceil(e.lits * occupation_attendue(p) * PERSONNEL_PAR_LIT_OCCUPE)
        e.vise = int(round(plein * FACTEURS_EFFECTIF[a]))
        TR.ouvrir_postes(p, e.lieu.id, METIER, e.vise)
        ids = _personnel_ids(p, e)
        if len(ids) > e.vise:
            for i in ids[e.vise:][::-1].tolist():
                ECO.licencier(p, PO.Habitant(w.table, int(i)), "fin_de_saison")
                p.compter("fin_de_saison")


# ================================================================== le dividende du mois
def _mois(p):
    if p.jour == 0 or p.jour % ECO.MOIS_J: return
    d = _dom(p); L = p.socle.livre
    for e in d.etablissements:
        x = e.caisse - RESERVE_DIVIDENDE_J * _cout_jour_plein(p, e, max(OCCUPATION_MOIS))
        if x > 1.0 and e.proprietaire is not None:
            d.cumul["dividendes"] += L.transferer(e, e.proprietaire, x, "dividende")


# ================================================================== l API
def fixer_risque(p, facteur, motif="guerre"):
    """L avis aux voyageurs de l ile : 1 en paix ; RISQUE_CHAMP_DE_BATAILLE ou RISQUE_BELLIGERANT en guerre."""
    if not 0.0 <= facteur <= 1.0: raise ValueError(f"facteur de risque hors [0 ; 1] : {facteur!r}")
    d = _dom(p); d.risque, d.motif_risque = float(facteur), str(motif)
    return d.risque


def etat_tourisme(p):
    d = _dom(p)
    s = d.serie[-7:]
    return {"etablissements": len(d.etablissements), "lits": sum(e.lits for e in d.etablissements), "risque": avis(p),
            "motif": "blocus" if X.sous_blocus(p) else d.motif_risque, "nuitees_7j": round(sum(x[1] for x in s)), "demande_7j": round(sum(x[2] for x in s)),
            "recettes_7j": round(sum(x[3] for x in s)), "personnel": int(s[-1][4]) if s else 0,
            "cumul": {k: round(v) for k, v in d.cumul.items()}}


# ================================================================== installation
def _proprietaire(p, rng):
    """Un menage aise de l ile, tire au hasard ; l Etat s il n y en a pas."""
    w = p.w
    aises = [m for m in w.menages if any(h.vivant and h.classe == "aisee" for h in m.membres)]
    return aises[int(rng.integers(0, len(aises)))] if aises else w.gouv


def installer(p):
    w = p.w; L = p.socle.livre
    if METIER not in PO.CODE_ROLE: raise RuntimeError(f"le metier {METIER!r} manque au moteur ( config.ROLES )")
    J = p.socle.journal
    J.declarer("etablissement_ouvert", "tourisme", "individuel", ("lieu", "lits", "proprietaire"))
    for t in ("nuitees", "nuitees_refusees", "recettes_touristiques", "repas_touristes", "repas_touristes_manquants",
              "fournitures_manquantes", "fin_de_saison"):
        J.declarer(t, "tourisme", "compte")
    d = Tourisme()
    p.domaines["tourisme"] = d
    p.socle.registre.inscrire("tourisme", "entreprises", _membres, "caisse", None, "EtablissementTouristique")
    rng = p.hasard("tourisme_installation")
    lieux = sorted((l for l in w.carte.lieux.values() if l.type in POIDS_LIEU and l.marche is not None), key=lambda l: l.id)
    vivants = int(w.table.vivant[:w.table.n].sum())
    poids = sum(POIDS_LIEU[l.type] for l in lieux)
    for l in lieux:
        lits = int(round(LITS_PAR_HABITANT * vivants * POIDS_LIEU[l.type] / poids))
        if lits < 1: continue
        e = EtablissementTouristique(l, lits, _proprietaire(p, rng))
        d.etablissements.append(e)
        TR.declarer_employeur(p, l.id, METIER, e)
        x = FONDS_DE_ROULEMENT_J * _cout_jour_plein(p, e, max(OCCUPATION_MOIS))
        L.recevoir_de_l_exterieur(e, x, "investissement_direct"); d.cumul["investissement"] += x
        p.noter("etablissement_ouvert", lieu=l.id, lits=lits, proprietaire=getattr(e.proprietaire, "id", "etat"))
    d.decideur = p.decideur(POINT)
    p.routine(6.0, 30, "tourisme", _lundi)
    p.routine(17 + 50 / 60, 50, "tourisme", _heures)
    p.routine(21.0, 50, "tourisme", _jour)
    p.routine(21 + 10 / 60, 50, "tourisme", _mois)
    return d
