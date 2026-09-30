"""Les 500 habitants : role, classe, age, famille, domicile, lieu de travail, horaire, sante, argent.
Chaque habitant garde son identite pour toujours, qu il soit simule ( donnee ) ou incarne dans Arma ( la bulle, E2 )."""
import numpy as np
from . import config as C

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


class Habitant:
    __slots__ = ("id", "nom", "role", "classe", "age", "menage", "domicile", "travail", "horaire", "equipe",
                 "lieu", "etat", "jours_etat", "gravite", "remede", "vivant", "faim", "heures_jour", "amendes",
                 "incarne", "eleve", "poste", "decalage")

    def __init__(self, id, role, classe, age):
        self.id, self.role, self.classe, self.age = id, role, classe, age
        self.nom = f"H{id:03d}"
        self.menage = None; self.domicile = None; self.travail = None; self.horaire = None; self.equipe = 0
        self.decalage = 0.0          # son quart d heure a lui : tout le monde ne part pas a la meme minute
        self.lieu = None; self.poste = "maison"     # ou il est DANS son lieu : maison, travail, hopital
        self.etat = "S"; self.jours_etat = 0.0; self.gravite = 0.0; self.remede = False; self.vivant = True
        self.faim = 0.0; self.heures_jour = 0.0; self.amendes = 0
        self.incarne = False; self.eleve = False

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
    def __init__(self, id, domicile):
        self.id, self.domicile = id, domicile
        self.membres = []
        self.caisse = 0.0
        self.garde_manger = 0.0      # nourriture en reserve a la maison

    def adultes(self):
        return [h for h in self.membres if h.role not in ("enfant",) and h.vivant]


def _effectif_patrons(carte, role, n, echelle):
    """28/09 : l effectif d un metier a la naissance ; un patron a au moins une entreprise privee ( un site de production
    hors ferme ), les patrons en trop naissent marchands ( patch_patrons.py ; population.effectifs dans le tronc )."""
    k = max(1, int(round(n * echelle)))
    if role not in ("patron", "marchand"): return k
    p = max(1, int(round(C.ROLES["patron"][0] * echelle)))
    garde = min(p, len(carte.de_type(*[t for t in C.RECETTES if t != "ferme"])))
    return garde if role == "patron" else k + p - garde


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


# les postes par site par unite d echelle, ceux de population.POSTES_PAR_SITE ( regle b ) avec les sites de d10 au reel
POSTES_INDUSTRIE = {"mineur": {"mine": postes_reels("mine"), "carriere": postes_reels("carriere")}, "petrolier": {"puits": 15},
                    "ouvrier": {**C.OUVRIERS_PAR_SITE, "fonderie": postes_reels("fonderie")}}


def industrie_au_reel(carte, eff, echelle):
    """Les metiers industriels a leurs postes ( ceux des sites de la carte, a l echelle ; un metier sans site : 0 ), le
    surplus aux metiers ouverts par le remplissage vers la structure reelle, comme population.effectifs."""
    eff = dict(eff)
    surplus = 0
    for r, par_site in POSTES_INDUSTRIE.items():
        x = sum(par_site[l.type] for l in carte.de_type(*par_site)) * echelle
        k = max(1, int(round(x))) if x else 0
        surplus += eff[r] - k
        eff[r] = k
    ouverts = [r for r in ACCUEIL_CONVOYEURS if _metier_ouvert(carte, r)]
    if surplus and ouverts:
        c = [float(eff[r]) for r in ouverts]
        d = _remplir_vers(c, [ACCUEIL_CONVOYEURS[r] for r in ouverts], max(0.0, sum(c) + surplus)) - np.asarray(c)
        k = int(round(abs(d.sum())))
        d = np.sign(surplus) * _parts_entieres(k, np.abs(d))
        for r, x in zip(ouverts, d.tolist()): eff[r] += int(x)
    return eff


_effectif_avant_industrie = _effectif_patrons


def _effectif_industrie(carte, role, n, echelle):
    """L effectif d un metier a la naissance ( la fonction d avant, quelle qu elle soit ), l industrie au reel appliquee ;
    un metier d effectif nul a 0. Elle prend le nom de la fonction qu elle enveloppe, sans redefinir sa ligne `def`."""
    eff = {r: (_effectif_avant_industrie(carte, r, k, echelle) if k else 0) for r, (k, _, _) in C.ROLES.items()}
    return industrie_au_reel(carte, eff, echelle)[role]


_effectif_patrons = _effectif_industrie


def _lieux_industrie(carte, role, types):
    """Les lieux de travail d un metier pour le tour de role, comme population._lieux_ponderes : des postes entiers
    repetent chaque site selon ses postes divises par leur plus grand diviseur commun ( la liste d E1 : les ouvriers
    14, 3, 6, 5 ; les mineurs une fois chaque site ) ; des postes non entiers donnent la suite de Sainte-Lague."""
    lieux = carte.de_type(*types)
    poids = POSTES_INDUSTRIE.get(role)
    if poids is None or not lieux: return lieux
    if all(float(poids[l.type]).is_integer() for l in lieux):
        g = int(np.gcd.reduce([int(poids[l.type]) for l in lieux]))
        return [l for l in lieux for _ in range(int(poids[l.type]) // g)]
    return _suite_en_cache(lieux, [poids[l.type] for l in lieux])

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

# le temoin et l archive des references sont des mondes « e1 » ( les convois du moteur ) : les convoyeurs d E1 ; la
# regle au reel n y est pas appliquee, seuls ses outils servent ( patch_industrie )


def generer(carte, rng, echelle=1.0):
    """Cree la population et ses menages, deterministe a graine fixee. `echelle` multiplie chaque metier : le pays
    garde ses proportions, il change de taille."""
    H = []
    for role, (n, classe, _) in C.ROLES.items():
        for _ in range(_effectif_patrons(carte, role, n, echelle)):
            age = int(rng.integers(6, 18)) if role == "enfant" else int(rng.integers(65, 86)) if role == "retraite" \
                else int(rng.integers(20, 65))
            H.append(Habitant(len(H), role, classe, age))
    # lieux de travail : repartition equilibree sur les lieux du bon type
    compteur = {}
    for h in H:
        types, horaire = TRAVAIL[h.role]
        h.horaire = horaire
        if not types: continue
        if types == ("gouvernement",): cands = [carte.gouvernement]
        else: cands = _lieux_industrie(carte, h.role, types)   # ( 29/09 ) les sites de d10 a leurs postes reels
        k = compteur.get(h.role, 0); compteur[h.role] = k + 1
        h.travail = cands[k % len(cands)]
        h.equipe = k
    # domiciles : les actifs vivent au lieu habitable le plus proche de leur travail
    for h in H:
        if h.travail is not None and h.role != "enfant":
            h.domicile = h.travail if h.travail.type in ("capitale", "ville", "village") else \
                carte.plus_proche(h.travail, ("capitale", "ville", "village"))
    # menages : chaque adulte actif fonde un menage ; enfants et retraites rejoignent un menage au hasard
    M = []
    for h in H:
        if h.role not in ("enfant", "retraite"):
            m = Menage(len(M), h.domicile); m.membres.append(h); h.menage = m; M.append(m)
    for h in H:
        if h.role in ("enfant", "retraite"):
            m = M[int(rng.integers(0, len(M)))]
            m.membres.append(h); h.menage = m; h.domicile = m.domicile
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
