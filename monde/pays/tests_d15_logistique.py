"""Les portes du domaine 15 ( logistique ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests logistique

Le monde des portes a plusieurs iles : Altis et Malden ( `essais.monde( [...], iles=( "Altis", "Malden" ) )` ). La lecon
payee du 22-23/09 : a 2 000 habitants sur six iles, la faim passait de 2,2 % a 11,9 % parce que la nourriture ne
traversait pas la mer. Le controle positif en est tire : les fermes de Malden ne produisent plus rien ( secheresse
totale, `Monde.chocs` ) ; sans fret, l ile a faim ; avec le fret, elle doit manger."""
import math
import sys
import time
import numpy as np
from .. import config as C, monde as W
from . import essais as T, d15_logistique as M, d14_transport as T14

ILES = ("Altis", "Malden")
MALDEN = "Malden:LaTrinite"


def _secheresse_malden(w, jours=60):
    v = [l.id for l in w.carte.lieux.values() if l.type == "village" and l.ile == "Malden"]
    w.chocs.append({"debut": 0, "jours": jours, "lieux": v, "facteur": 0.0})


def _monde_malden(modes=None, graine=C.GRAINE, domaines=("logistique",)):
    w, p = T.monde(list(domaines), graine, modes=modes, iles=ILES)
    _secheresse_malden(w)
    return w, p


# ================================================================== la flotte et la physique
def test_flotte_et_physique():
    """Porte : apres 4 jours ( les camions importes arrivent en 3 ), chaque transporteur a au moins un camion du domaine
    14, et sa flotte est celle que le Parc compte ( `vehicules_de` ) ; aucune anomalie du parc du domaine 14 ( aucun
    vehicule ne nait hors de son registre ) ; un camion porte au moins 1 000 rations ( le camion du moteur : 60 ) ; la
    traversee Altis - Malden du ferry dure de 3 a 8 heures ; navires et avion sont au Parc."""
    w, p = T.monde(["logistique"], iles=ILES)
    T.jours(w, 4)
    lg = p.domaine("logistique")
    camions = {tr.marche_id: sum(1 for v in tr.vehicules if v[0] == "camion") for tr in lg.transporteurs}
    accord = all(sorted(v[0] for v in tr.vehicules) == sorted(n for nom, k, _ in T14.vehicules_de(p, tr) for n in [nom] * k)
                 for tr in lg.transporteurs)
    anomalies = T14.anomalies_parc(p)
    rations = T14.caracteristiques("camion").charge_kg / M.masse_kg(p, "nourriture")
    ferry = next(li for li in lg.lignes if li.genre == "ferry")
    h = ferry.km / (M.NAVIRES[lg.navires[ferry.navire].modele][5] * M.KMH_PAR_NOEUD)
    au_parc = all(x.objet in p.socle.parc.objets for x in list(lg.navires) + list(lg.avions))
    ok = min(camions.values()) >= 1 and accord and not anomalies and rations >= 1000 and 3 <= h <= 8 and au_parc \
        and len(lg.navires) == 2 and len(lg.avions) == 1
    return ok, (f"camions par capitale {camions} ; flotte = Parc {accord} ; anomalies du parc 14 : {len(anomalies)} ; un camion "
                f"porte {rations:.0f} rations ; ferry {lg.navires[ferry.navire].modele} {ferry.km:.0f} km en {h:.1f} h, "
                f"jours {ferry.jours} ; navires {len(lg.navires)}, avions {len(lg.avions)}, au Parc {au_parc}")


# ================================================================== conservation et falsificateurs
def _chercher(w, p, predicat, pas_max=6 * C.PAS_PAR_JOUR):
    for _ in range(pas_max):
        x = predicat()
        if x is not None: return x
        w.pas_suivant()
    return predicat()


def test_conservation_en_transit():
    """Porte : Altis et Malden, secheresse sur Malden, 9 jours : la conservation du socle tient ; le rapprochement des
    lots ( `anomalies_transit` ) est vide chaque soir ; au moins un lot livre par la route et un par la mer.
    Falsificateurs : 5 unites posees a la main dans la cale d un navire en mer, puis 3 unites retirees a la main d un
    convoi routier qui porte un lot - la conservation ET le rapprochement voient chacune ( ecart >= 90 % de l erreur
    posee ), puis redeviennent nuls quand l erreur est retiree ( ils voient l erreur, pas du bruit )."""
    w, p = _monde_malden()
    lg = p.domaine("logistique")
    propres = 0
    for _ in range(9):
        T.jours(w, 1)
        propres += not M.anomalies_transit(p)
    tenue, msg = p.socle.conservation.tenue()
    st, tr = M.statistiques(p)
    livres_route, livres_mer = tr["route"][0], tr["ferry"][0] + tr["caboteur"][0]
    cat = p.socle.catalogue

    def navire_charge():
        for n in lg.navires:
            if n.terminal < 0 and n.a_bord: return n
        return None

    def convoi_lot():
        for c in w.convois:
            info = lg.convois.get(c.id)
            if info is not None and info[2] >= 0 and c.cargaison: return c
        return None
    vu = []
    n = _chercher(w, p, navire_charge)
    if n is not None:
        b = lg.lots[n.a_bord[0]].bien; bid = cat.id(b)
        n.stock._ajouter(bid, 5.0)
        d = p.socle.conservation.ecarts()[1][b]
        a = [x for x in M.anomalies_transit(p) if x[0] == "detenteur" and x[1] == "navire"]
        n.stock._retirer(bid, 5.0)
        vu.append(("cale", d >= 4.5 and bool(a), p.socle.conservation.tenue()[0] and not M.anomalies_transit(p), round(d, 3)))
    c = _chercher(w, p, convoi_lot)
    if c is not None:
        b = next(iter(c.cargaison)); q0 = c.cargaison[b]; x = min(3.0, q0)
        c.cargaison[b] = q0 - x
        d = p.socle.conservation.ecarts()[1][b]
        a = [y for y in M.anomalies_transit(p) if y[0] == "convoi"]
        c.cargaison[b] = q0
        vu.append(("convoi", d <= -0.9 * x and bool(a), p.socle.conservation.tenue()[0] and not M.anomalies_transit(p), round(d, 3)))
    falsif = len(vu) == 2 and all(v[1] and v[2] for v in vu)
    ok = tenue and propres == 9 and livres_route >= 1 and livres_mer >= 1 and falsif
    return ok, (f"{msg} ; rapprochement des lots vide {propres}/9 soirs ; lots livres : route {livres_route}, mer "
                f"{livres_mer}, avion {tr['avion'][0]} ; {int(st['convois'])} convois, {int(st['traversees'])} traversees, "
                f"{st['tonnes_mer']:.1f} t par mer ; falsificateurs ( vu, puis nul apres retrait, ecart ) {vu}")


# ================================================================== le controle positif : une ile sans production
def _faim_malden(w, p, jours, debut):
    f_m, f_n = [], []
    for j in range(jours):
        T.jours(w, 1)
        if j >= debut: f_m.append(w.faim_region.get(MALDEN, 0.0)); f_n.append(T.faim(w))
    return float(np.mean(f_m)), float(np.mean(f_n))


def test_faim_ile_sans_production():
    """Controle positif ( la lecon des 11,9 % ) : les fermes de Malden ne produisent plus rien pendant 14 jours. Mer
    fermee ( `fermer_la_mer` ), la faim de la region de Malden, moyenne des jours 4 a 13, est d au moins 30 % : la
    secheresse mord, l instrument voit l effet pose. Mer ouverte ( regle ), elle est au plus la moitie, et la faim
    nationale baisse. Le temoin aveugle ( expedier sans condition vers l ile la plus chere ) est mesure et rapporte."""
    w0, p0 = _monde_malden()
    M.fermer_la_mer(p0)
    ferme_m, ferme_n = _faim_malden(w0, p0, 14, 4)
    w1, p1 = _monde_malden()
    ouvert_m, ouvert_n = _faim_malden(w1, p1, 14, 4)
    w2, p2 = _monde_malden(modes={"expedier_lot": "temoin"})
    temoin_m, temoin_n = _faim_malden(w2, p2, 14, 4)
    tenue = all(x.socle.conservation.tenue()[0] for x in (p0, p1, p2))
    ok = ferme_m >= 0.30 and ouvert_m <= 0.5 * ferme_m and ouvert_n < ferme_n and tenue
    s1 = M.statistiques(p1)
    return ok, (f"faim de Malden ( jours 4-13 ) : mer fermee {ferme_m:.1%}, mer ouverte {ouvert_m:.1%}, temoin aveugle "
                f"{temoin_m:.1%} ; faim nationale {ferme_n:.1%} / {ouvert_n:.1%} / {temoin_n:.1%} ; regle : "
                f"{s1[0]['tonnes_mer']:.1f} t par mer, subvention de la ligne {s1[0]['subventions']:.0f} drachmes ; "
                f"conservation {tenue}")


# ================================================================== un port sature
def _age_mer(p):
    """Heures moyennes decision -> livraison des lots par mer ; un lot pas encore livre compte son age ( minorant )."""
    lg = p.domaine("logistique")
    h = [x for m in ("ferry", "caboteur") for x in lg.transits[m]]
    h += [(p.w.pas - x.pas_decision) / M.PAS_H for x in lg.lots.values() if x.mode in ("ferry", "caboteur")]
    return float(np.mean(h)) if h else 0.0, len(h)


def test_port_sature():
    """Porte : meme monde ( secheresse sur Malden ), 12 jours. Le port d Altis ne manutentionne plus que 0,2 % de sa
    capacite ( `regler_port` ) : le delai moyen des lots par mer ( decision -> livraison ; un lot non livre compte son
    age ) est au moins 1,5 fois celui du port normal, et des departs ont ete retardes par le chargement."""
    w0, p0 = _monde_malden()
    T.jours(w0, 12)
    a0, n0 = _age_mer(p0)
    w1, p1 = _monde_malden()
    M.regler_port(p1, "Altis", facteur=0.002)
    T.jours(w1, 12)
    a1, n1 = _age_mer(p1)
    r1 = p1.domaine("logistique").stats["retard_port_h"]
    tenue = p0.socle.conservation.tenue()[0] and p1.socle.conservation.tenue()[0] and not M.anomalies_transit(p1)
    ok = n0 >= 3 and n1 >= 3 and a1 >= 1.5 * a0 and r1 > 0 and tenue
    return ok, (f"port normal : {n0} lots par mer, {a0:.1f} h en moyenne ; port a 0,2 % : {n1} lots, {a1:.1f} h "
                f"( x{a1 / max(1e-9, a0):.2f} ), {r1:.1f} h de departs retardes ; faim de Malden au 12e jour "
                f"{w0.faim_region.get(MALDEN, 0):.0%} / {w1.faim_region.get(MALDEN, 0):.0%} ; conservation {tenue}")


# ================================================================== les chauffeurs au repos
def test_chauffeurs_au_repos():
    """Porte : avec l agenda ( domaine 5 ), du vendredi 15 juin au mardi 19 ( samedi, dimanche et lundi de Pentecote,
    ferie grec ) : aucun convoi ne part avec un convoyeur qui n est pas a son poste ( 0 ) ; il en part chaque jour ouvre
    ( au moins 5 ). Controle positif : les jours de repos, le choix du MOTEUR ( Monde.conducteur ) aurait donne au
    moins une fois un convoyeur reste chez lui - le defaut corrige existe bien dans ce monde."""
    w, p = T.monde(["logistique", "agenda"])
    lg = p.domaine("logistique")
    cal = p.socle.calendrier
    moteur_chez_lui = 0
    ouvres = set()
    for _ in range(5 * C.PAS_PAR_JOUR):
        w.pas_suivant()
        if not 7 <= w.heure < 15: continue
        if cal.ouvre(cal.date(w.pas)): ouvres.add(p.jour)
        elif w.minutes % 60 == 0:
            for cap in w.carte.capitales:
                h = type(w).conducteur(w, cap)
                if h is not None and not M.au_poste(h): moteur_chez_lui += 1
    lanc = list(lg.lancements)
    chez_lui = sum(1 for x in lanc if not x[4])
    par_jour = {}
    for x in lanc: par_jour[x[0]] = par_jour.get(x[0], 0) + 1
    repos = sum(1 for x in lanc if x[5])
    ok = chez_lui == 0 and len(ouvres) >= 2 and all(par_jour.get(j, 0) >= 5 for j in ouvres) and moteur_chez_lui >= 1
    return ok, (f"{len(lanc)} convois ( par jour {dict(sorted(par_jour.items()))}, jours ouvres {sorted(ouvres)} ), {repos} un "
                f"jour de repos, dont {chez_lui} avec un convoyeur hors de son poste ; le choix du moteur aurait pris "
                f"{moteur_chez_lui} fois un convoyeur reste chez lui ; faim au mardi matin {T.faim(w):.1%}")


# ================================================================== la duree selon l etat des routes
def test_duree_selon_routes():
    """Porte : avec les services publics ( domaine 12 ), le trajet d un village a sa capitale ( le plus long d Altis ) :
    sur des troncons a l etat 0,15 ( ouverts, degrades ), la duree de route ( hors chargement ) est au moins 1,5 fois
    celle des troncons neufs ; la duree d un convoi reellement lance est exactement celle du domaine 12
    ( `duree_trajet_pas` ) plus le chargement ; un troncon coupe ( `couper_troncon` ) refuse le convoi."""
    w, p = T.monde(["logistique", "services_publics"])
    SP = M._sp(p); R = p.domaine("services_publics").routes
    vill = [l for l in w.carte.de_type("village") if l.ile == "Altis"]
    o = max(vill, key=lambda l: (w.carte.km_route(l, l.marche), l.id)); d = o.marche
    ch = SP.chemin(p, SP._index(p, o), SP._index(p, d))
    charg = round(M.CHARGEMENT_H * M.PAS_H)
    m = w.marches[d.id]
    T.jours(w, 0.25)
    cv = None
    for _ in range(C.PAS_PAR_JOUR):             # le premier pas ou un vehicule et un chauffeur sont libres
        if 7 <= w.heure < 14:
            R.etat[ch] = 1.0; R.ferme[ch] = False
            bon = M.duree_convoi_pas(p, o, d)[0] - charg
            R.etat[ch] = 0.15
            mauvais = M.duree_convoi_pas(p, o, d)[0] - charg
            attendu = SP.duree_trajet_pas(p, o, d)
            cv = M.lancer_convoi(p, d, o, {"nourriture": 10.0}, m, "approvisionnement", m)
            if cv is not None: break
        w.pas_suivant()
    lance = cv is not None and cv.arrivee - cv.depart == attendu + charg
    if cv is not None: m.stocks["nourriture"] -= 10.0     # le convoi porte ces 10 unites ( contrat du moteur )
    SP.couper_troncon(p, int(ch[0]))
    refus = M.lancer_convoi(p, d, o, {"nourriture": 1.0}, m, "approvisionnement", m) is None
    tenue = p.socle.conservation.tenue()[0]
    ok = mauvais >= 1.5 * bon and mauvais == attendu and lance and refus and tenue
    return ok, (f"{o.id} -> {d.id} ( {w.carte.km_route(o, d):.1f} km ) : routes neuves {bon} pas, a l etat 0,15 {mauvais} pas "
                f"( domaine 12 : {attendu} ) ; convoi lance a la bonne duree {lance} ; troncon coupe refuse {refus} ; "
                f"conservation {tenue}")


# ================================================================== la decision
def test_decision_expedier_lot():
    """Porte de la decision : secheresse sur Malden, 16 jours, les marches decident au hasard ( mode hasard ). La note
    depend du choix : part du choix ( epsilon carre intra-jour ) >= 0,01 et p de permutation < 0,05, sur au moins
    150 decisions et 100 notes murees ; la conservation tient."""
    w, p = _monde_malden(modes={"expedier_lot": "hasard"})
    T.jours(w, 16)
    dec = p.domaine("logistique").decideur
    part, pp = dec.part_du_choix(), dec.p_permutation()
    notes = dec.notes_par_action()
    murees = sum(n for n, _ in notes.values())
    tenue, msg = p.socle.conservation.tenue()
    ok = dec.n_decisions >= 150 and murees >= 100 and part >= 0.01 and pp < 0.05 and tenue
    return ok, (f"{dec.n_decisions} decisions, {murees} notes murees : " + ", ".join(f"{a} {m:+.3f} ( {n} )" for a, (n, m) in notes.items())
                + f" ; part du choix {part:.3f}, p = {pp:.3f} ; faim de Malden {w.faim_region.get(MALDEN, 0):.0%} ; {msg}")


# ================================================================== l API des domaines 17, 18, 26
RECUS = {}


def _recevoir_hopital(p, lot, src):
    """Un recepteur d essai : le lot entre au stock public des hopitaux ( domaine 17 le fera pour ses pharmacies )."""
    from . import d07_exterieur as EXT
    q = p.socle.livre.deplacer(src, EXT.StockE1(p.w.publics["hopitaux"], p.socle.catalogue), p.socle.catalogue.id(lot.bien),
                               lot.q, "livraison_hopital")
    RECUS[lot.id] = (q, p.w.pas)


def test_api_envoyer():
    """Porte de l API ( domaines 17, 18, 26 ) : l Etat confie 20 remedes du marche de Kavala aux hopitaux de Pyrgos par la
    route et 20 a ceux de Malden par avion, un vendredi a 9 h. Les deux lots arrivent entiers a leur recepteur, la route
    en moins de 12 heures, l avion en moins de 24 ; le rapprochement des lots et la conservation tiennent ; l Etat a paye
    le fret."""
    RECUS.clear()
    w, p = T.monde(["logistique"], iles=ILES)
    M.recevoir_lot(p, "hopital_essai", _recevoir_hopital)
    while w.heure < 9: w.pas_suivant()
    kav = w.marches["Kavala"]; kav.stocks["remedes"] += 0.0
    caisse0 = w.gouv.caisse
    from . import d07_exterieur as EXT
    src = EXT.StockE1(kav.stocks, p.socle.catalogue)
    a = M.envoyer(p, w.gouv, src, "remedes", 20.0, "Kavala", "Pyrgos", "hopital_essai", mode="route")
    b = M.envoyer(p, w.gouv, src, "remedes", 20.0, "Kavala", MALDEN, "hopital_essai", mode="avion")
    depart = w.pas
    propres = 0
    for _ in range(2):
        T.jours(w, 1); propres += not M.anomalies_transit(p)
    ra, rb = RECUS.get(a), RECUS.get(b)
    ha = (ra[1] - depart) / M.PAS_H if ra else None
    hb = (rb[1] - depart) / M.PAS_H if rb else None
    tenue = p.socle.conservation.tenue()[0]
    ok = (a >= 0 and b >= 0 and ra is not None and rb is not None and abs(ra[0] - 20.0) < 1e-9 and abs(rb[0] - 20.0) < 1e-9
          and ha <= 12 and hb <= 24 and propres == 2 and tenue and w.gouv.caisse < caisse0)
    return ok, (f"lots {a} ( route ) et {b} ( avion ) : recus {ra} et {rb} ; route {ha} h, avion {hb} h ; rapprochement "
                f"vide {propres}/2 ; conservation {tenue} ; vols {int(p.domaine('logistique').stats['vols'])}")


def test_pays_vivable():
    return T.porte_commune("logistique", n_jours=12)


# ================================================================== le cout
def test_cout():
    """Le domaine coute au plus 30 % d une journee de plus que ses dependances seules, a 10 000 habitants ( Altis ), et
    ses routines propres au plus 15 % de la journee."""
    def jour_moyen(doms):
        w, p = T.monde(doms, echelle=20)
        T.jours(w, 4)                               # la flotte commandee est arrivee ( 3 jours )
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants), p
    t_dep, n, _ = jour_moyen(["transport", "immobilier"])
    t_log, _, p = jour_moyen(["logistique"])
    lg = p.domaine("logistique")
    propre = sum(lg.chrono.values()) / 6
    ok = t_log <= 1.3 * t_dep and propre <= 0.15 * t_log
    return ok, (f"{n} habitants : dependances {t_dep:.2f} s par jour, avec la logistique {t_log:.2f} s "
                f"( {t_log / t_dep - 1:+.0%} ) ; routines propres {propre * 1000:.0f} ms par jour "
                f"( {', '.join(f'{k} {v / 6 * 1000:.0f}' for k, v in sorted(lg.chrono.items()))} ms ) ; "
                f"{int(lg.stats['convois'] / 6)} convois par jour ; faim {T.faim(p.w):.1%}")


# ================================================================== ( 29/09, run long HMT-119 ) la commande publique comptee une fois
def _demande_comptee(p, w, Q, ancien):
    """Une commande publique de remedes que personne ne peut servir ( les marches de l ile du gouvernement sans remedes ),
    vue 72 heures de suite par la logistique ; rend la demande de remedes comptee. `ancien` : le drapeau efface avant
    chaque heure, comme dans le domaine 15 d avant le correctif."""
    lg = M._lg(p)
    ms = [m for m in w.marches.values() if m.lieu.ile == w.carte.gouvernement.ile]
    stocks = {m.lieu.id: m.stocks["remedes"] for m in ms}; dem = {m.lieu.id: m.demande["remedes"] for m in ms}
    cmd = {"bien": "remedes", "quantite": Q, "destination": "hopitaux"}
    autres = list(w.gouv.commandes); w.gouv.commandes[:] = [cmd]
    d0 = math.fsum(m.demande["remedes"] for m in ms)
    for _ in range(72):
        for m in ms: m.stocks["remedes"] = 0.0
        if ancien: cmd.pop("_demande_comptee", None)
        M._commandes_publiques(p, lg)
    compte = math.fsum(m.demande["remedes"] for m in ms) - d0
    for m in ms: m.stocks["remedes"] = stocks[m.lieu.id]; m.demande["remedes"] = dem[m.lieu.id]
    w.gouv.commandes[:] = autres
    return compte, cmd["quantite"]


def test_commande_publique_une_fois():
    """Porte ( 29/09, run long HMT-119, ecrite avant la mesure ) : une commande publique non servie pendant 3 jours
    ( 72 heures de logistique ) entre UNE fois dans la demande du marche : la demande comptee egale la quantite
    commandee ( 1e-9 pres ), et la commande reste entiere ( rien de servi ). Controle positif : le domaine 15 d avant le
    correctif ( recompte a chaque heure ) donne 72 fois la quantite, 24 fois par jour, et la porte echoue."""
    w, p = T.monde(["logistique"])
    T.jours(w, 1)
    Q = 5000.0
    n, reste = _demande_comptee(p, w, Q, False)
    a, _ = _demande_comptee(p, w, Q, True)
    juge = lambda n: abs(n - Q) <= 1e-9 * Q
    ok = juge(n) and abs(reste - Q) <= 1e-9 and not juge(a) and abs(a - 72 * Q) <= 1e-9 * Q
    return ok, (f"commande de {Q:.0f} remedes non servie 72 heures : demande comptee {n:.1f} ( {n / Q:.2f} fois la "
                f"commande ), reste a servir {reste:.1f} ; domaine 15 d avant : {a:.1f} ( {a / Q:.0f} fois ), porte "
                f"{'passe ( FAUX )' if juge(a) else 'echoue ( attendu )'}")


# ================================================================== le fret attend le service des convoyeurs
def _appelant(nom, profondeur=8):
    f = sys._getframe(2)
    for _ in range(profondeur):
        if f is None: return False
        if f.f_code.co_name == nom: return True
        f = f.f_back
    return False


def _cinq_jours_de_fret(ancien):
    """5 jours avec l agenda : ( tentatives hors service de l heure pleine, dont refusees ; quantite d approvisionnement
    refusee hors service ; convois par jour ; jours ouvres ; conservation ). ancien : le domaine 15 d avant ( tente a
    toute heure )."""
    w, p = T.monde(["logistique", "agenda"])
    cal = p.socle.calendrier; lg = p.domaine("logistique")
    vrai, oc, ol = M._en_service, M.conducteur, M._lancer
    n = {"hors": 0, "refus_hors": 0, "fantome_hors": 0.0}
    def cond(p_, cap):
        r = oc(p_, cap)
        if _appelant("_expedier") and not _appelant("_charger_convoi") and not vrai(p_, cap):
            n["hors"] += 1; n["refus_hors"] += r is None
        return r
    def lan(p_, o, d, cargo, payeur, motif, marche, *a, **k):
        r = ol(p_, o, d, cargo, payeur, motif, marche, *a, **k)
        if motif == "approvisionnement" and r is None and not vrai(p_, marche.lieu): n["fantome_hors"] += sum(cargo.values())
        return r
    M.conducteur, M._lancer = cond, lan
    if ancien: M._en_service = lambda p_, c: True
    ouvres = set()
    try:
        for _ in range(5 * C.PAS_PAR_JOUR):
            w.pas_suivant()
            if 7 <= w.heure < 15 and cal.ouvre(cal.date(w.pas)): ouvres.add(p.jour)
    finally:
        M.conducteur, M._lancer, M._en_service = oc, ol, vrai
    par_jour = {}
    for x in lg.lancements: par_jour[x[0]] = par_jour.get(x[0], 0) + 1
    return n, par_jour, ouvres, p.socle.conservation.tenue()


def test_fret_attend_le_service():
    """Porte ( 29/09, arriere de HMT-140 cause 5 b, ecrite avant la mesure ) : le fret de l heure pleine ( ventes et
    approvisionnements des entreprises, commerce industriel entre marches, commandes publiques ) attend le service des
    convoyeurs de sa capitale. Avec l agenda, 5 jours du vendredi 15 juin au mardi 19 ( week-end et lundi de Pentecote ) :
    ( 1 ) hors service, 0 convoi tente, donc 0 refus faute de chauffeur, et 0 unite d approvisionnement comptee en demande
    pour un convoi qui ne part pas ; ( 2 ) les convois partent comme avant : au moins 5 chaque jour ouvre, et au moins
    95 % du nombre du domaine 15 d avant sur les 5 jours ; ( 3 ) conservation. Les lots ( _charger_convoi ) ne sont pas
    concernes. Controle positif : le domaine 15 d avant ( tente a toute heure ) tente des convois hors service et y compte
    des refus : la porte echoue sur lui. Mesure du 29/09 ( Altis, 10 000 habitants, 20 jours, tronc 6b054bd ) : 11 081
    refus pour 1 125 convois, tous sans convoyeur a son poste, 98 % par l heure pleine ; la demande comptee pour des
    approvisionnements qui ne partaient pas faisait 66 % de celle du zinc, 13 % du fer et du gazole.
    ( AMENDEE apres la premiere mesure, 29/09, cf8c317 : un jour ouvre ne compte que si ses heures de service, 7 h a 15 h,
    sont dans la fenetre, comme test_chauffeurs_au_repos. Le cinquieme jour n y entrait que par son premier pas, a minuit,
    et demandait 5 convois a un jour sans service, dans les deux bras : 82 convois de part et d autre, 0 tentative hors
    service contre 1 551. Les seuils ne changent pas. )"""
    n, pj, ouv, (tenue, msg) = _cinq_jours_de_fret(False)
    n0, pj0, ouv0, (tenue0, _) = _cinq_jours_de_fret(True)
    tot, tot0 = sum(pj.values()), sum(pj0.values())
    juge = lambda n, pj, ouv, tot, t: (n["hors"] == 0 and n["refus_hors"] == 0 and n["fantome_hors"] == 0.0 and len(ouv) >= 2
                                       and all(pj.get(j, 0) >= 5 for j in ouv) and tot >= 0.95 * tot0 and t)
    ok = juge(n, pj, ouv, tot, tenue) and not juge(n0, pj0, ouv0, tot0, tenue0)
    return ok, (f"hors service : {n['hors']} tentatives, {n['refus_hors']} refus, {n['fantome_hors']:.1f} unites d appro "
                f"refusees ; convois {tot} ( par jour {dict(sorted(pj.items()))}, jours ouvres {sorted(ouv)} ) ; {msg} ; "
                f"domaine 15 d avant : {n0['hors']} tentatives hors service, {n0['refus_hors']} refus, {n0['fantome_hors']:.1f} "
                f"unites, {tot0} convois ; porte {'passe ( FAUX )' if juge(n0, pj0, ouv0, tot0, tenue0) else 'echoue ( attendu )'}")


TESTS = [test_flotte_et_physique, test_conservation_en_transit, test_faim_ile_sans_production, test_port_sature,
         test_chauffeurs_au_repos, test_duree_selon_routes, test_decision_expedier_lot, test_api_envoyer, test_pays_vivable,
         test_cout, test_commande_publique_une_fois, test_fret_attend_le_service]
