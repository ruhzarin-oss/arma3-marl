"""Les portes du domaine 18 ( securite civile ). Seuils ecrits avant la premiere mesure.
python -m monde.pays.tests securite_civile"""
import math, pickle, time
import numpy as np
from .. import config as C, monde as W
from ..socle import registre as R
from . import essais as T, pays as P, d01_population as POP, d08_territoire as TER, d13_immobilier as IM
from . import d17_hopitaux as HP, d18_securite_civile as SC

PAS_J = C.PAS_PAR_JOUR
_CACHE = {}


def _a_l_heure(w, heure):
    """Fait vivre le monde jusqu au prochain pas qui tombe a `heure`."""
    for _ in range(PAS_J + 1):
        if abs(w.heure - heure) < 1e-9: return w
        w.pas_suivant()
    raise RuntimeError("heure jamais atteinte")


def _calme(p):
    """Seuls les feux poses par la porte : aucun depart tire au hasard."""
    SC.scenario(p, habitation=0.0, industriel=0.0, foret=0.0)


def _logements_occupes(p, types=("capitale", "ville"), membres_min=3):
    """Les logements occupes des lieux de ces types, par des menages d au moins `membres_min` vivants."""
    w = p.w; d13 = IM._dom(p); TB = d13.B; tb = w.table
    out = []
    for b in range(TB.n):
        occ = int(TB["occupant"][b])
        if TB["vivant"][b] != 1 or occ < 0: continue
        if IM.NOMS_MODELES[int(TB["modele"][b])] not in ("maison", "appartement"): continue
        if w.carte.lieux[d13.lieux[int(TB["lieu"][b])]].type not in types: continue
        if sum(1 for i in tb.menages.membres_ids(occ) if tb.vivant[i]) >= membres_min: out.append(b)
    return out


# ================================================================== les departs de feu
def test_departs_de_feu():
    """Porte des taux : 3 650 tirages journaliers de `tirer_departs` sur le parc reel d un pays de 2 000 habitants :
    feux de logement de 0,5 a 2 pour 1 000 logements et par an ; sites industriels de 0,02 a 0,5 feu par site et par
    an. Vegetation : 30 ans de FFDI du generateur du territoire ( Altis ), 200 tirages des departs sur ces 30 ans ( le
    bruit de Poisson d un seul tirage, ~ 100 feux, depassait la bande du controle ) : 1 a 4 feux pour 100 km2 d espace naturel et
    par an, dont au moins 60 % de juin a septembre ( Grece : ~ 70 % ). Controles positifs : habitation x3 -> x2,7 a
    x3,3 ; FFDI double -> x1,9 a x2,1."""
    w, p = T.monde(["securite_civile"], graine=5, echelle=4)
    S = SC._dom(p); d13 = IM._dom(p); TB = d13.B
    n_log = int(((TB["vivant"][:TB.n] == 1) & np.isin(TB["modele"][:TB.n], S.idx_logements)).sum())
    SC.scenario(p, foret=0.0)
    def compter(jours, graine):
        c = {"habitation": 0, "industriel": 0}
        for d in range(jours):
            for _, nature, _ in SC.tirer_departs(p, S, np.random.default_rng((graine, d))): c[nature] += 1
        return c
    c = compter(3650, 1)
    r_hab = c["habitation"] / n_log / 10.0
    r_ind = c["industriel"] / max(1, len(S.ateliers)) / 10.0
    SC.scenario(p, habitation=3.0, industriel=0.0)
    c3 = compter(3650, 1)
    x3 = c3["habitation"] / max(1, c["habitation"])
    ffdi = SC.ffdi_climatologique(TER.PROFILS["Altis"], 30, np.random.default_rng(7))
    lam = SC.lambda_foret(S.surface_nat["Altis"], ffdi, S.ffdi_moyen["Altis"])
    rng = np.random.default_rng(8)
    k = rng.poisson(lam, (200,) + lam.shape); k2 = rng.poisson(2.0 * lam, (200,) + lam.shape)   # 200 tirages des 30 ans
    par_an = k.sum() / 200.0 / 30.0 / (S.surface_nat["Altis"] / 100.0)
    ete = k[:, :, 151:273].sum() / max(1, k.sum())
    x2 = k2.sum() / max(1, k.sum())
    ok = (SC.BANDE_HABITATION[0] <= r_hab <= SC.BANDE_HABITATION[1] and 0.02 <= r_ind <= 0.5
          and SC.BANDE_FORET[0] <= par_an <= SC.BANDE_FORET[1] and ete >= 0.60 and 2.7 <= x3 <= 3.3 and 1.9 <= x2 <= 2.1)
    return ok, (f"logements {r_hab * 1000:.2f} pour 1 000 par an ( {n_log} logements ) ; sites {r_ind:.3f} par an "
                f"( {len(S.ateliers)} sites ) ; vegetation {par_an:.2f} pour 100 km2 par an ( FFDI moyen "
                f"{ffdi.mean():.1f}, installe {S.ffdi_moyen['Altis']:.1f} ), {ete:.0%} de juin a septembre ; "
                f"habitation x3 -> x{x3:.2f} ; FFDI double -> x{x2:.2f}")


# ================================================================== le controle positif et les victimes
def _campagne(suspendu, graine=31, n=24):
    """1 500 habitants ; deux nuits, 12 feux de logement par nuit de 22 h a 4 h ( un toutes les 30 minutes ) dans des
    logements occupes de villes et de capitales ; puis deux jours. `suspendu` : aucun engin ne part."""
    cle = (suspendu, graine, n)
    if cle in _CACHE: return _CACHE[cle]
    w, p = T.monde(["securite_civile"], graine=graine, echelle=3)
    _calme(p)
    if suspendu: SC.suspendre(p)
    T.jours(w, 1)
    cands = _logements_occupes(p)
    pris = [cands[int(k)] for k in np.linspace(0, len(cands) - 1, n).round().astype(int)]
    ids = []
    for nuit in range(2):
        _a_l_heure(w, 22.0)
        for j in range(n // 2):
            ids.append(SC.allumer(p, "habitation", b=pris[nuit * (n // 2) + j]))
            for _ in range(3): w.pas_suivant()
    T.jours(w, 2)
    _CACHE[cle] = (w, p, [i for i in ids if i >= 0])     # -1 : le logement brulait deja ( propagation d un voisin )
    return _CACHE[cle]


def _bilan_feux(p, ids):
    S = SC._dom(p)
    fs = [S.finis[i] for i in ids if i in S.finis]
    dm = [s.dommage for s in fs]
    return {"finis": len(fs), "dommage": float(np.mean(dm)) if dm else 0.0,
            "detruits": sum(1 for x in dm if x >= 4) / max(1, len(dm)), "sauves": sum(s.sauves for s in fs),
            "morts": sum(s.morts for s in fs), "blesses": sum(s.blesses for s in fs),
            "delai": float(np.median([s.delai_min for s in fs if s.delai_min >= 0])) if any(s.delai_min >= 0 for s in fs)
            else -1.0}


def test_feu_attaque_contre_non_attaque():
    """Controle positif. Les memes 24 feux de logement de nuit, dans deux mondes de meme graine ; dans le second, aucun
    engin ne part. Attaques : au plus 25 % detruits ( D4-D5 ) et un dommage moyen d au plus 3 ; non attaques : au moins
    90 % detruits ; l ecart de dommage moyen d au moins 1,5 niveau. Et un feu de vegetation allume a midi pres d un
    village, par temps chaud et sec : attaque, il brule au moins 5 fois moins d hectares en 12 heures."""
    _, pa, ia = _campagne(False)
    _, pb, ib = _campagne(True)
    a, b = _bilan_feux(pa, ia), _bilan_feux(pb, ib)
    ha = []
    for susp in (False, True):
        w, p = T.monde(["securite_civile"], graine=37, echelle=2)
        _calme(p)
        TER.forcer_meteo(p, "Altis", 10, pluie=0.0, chaleur_c=6.0)
        if susp: SC.suspendre(p)
        T.jours(w, 2)
        _a_l_heure(w, 12.0)
        vil = sorted(l for l in SC._dom(p).voisins if w.carte.lieux[l].type == "village")[0]
        sid = SC.allumer(p, "foret", lieu=vil, d0=1.0)
        for _ in range(72): w.pas_suivant()
        S = SC._dom(p); s = S.actifs.get(sid) or S.finis.get(sid)
        ha.append((SC.hectares(s.L, s.LB), s.fin or "en cours", TER.risque_incendie(p, "Altis")[0]))
    ok = (a["finis"] == len(ia) >= 20 and b["finis"] == len(ib) >= 20 and a["detruits"] <= 0.25 and a["dommage"] <= 3.0 and b["detruits"] >= 0.90
          and b["dommage"] - a["dommage"] >= 1.5 and ha[1][0] >= 5.0 * ha[0][0] and ha[1][0] > 0)
    return ok, (f"{len(ia)} et {len(ib)} feux allumes ; logements attaques : dommage moyen {a['dommage']:.2f}, {a['detruits']:.0%} detruits, delai median "
                f"{a['delai']:.0f} min ; non attaques : {b['dommage']:.2f}, {b['detruits']:.0%} detruits ; vegetation "
                f"( FFDI {ha[0][2]:.0f} ) : attaque {ha[0][0]:.1f} ha ( {ha[0][1]} ), non attaque {ha[1][0]:.1f} ha "
                f"( {ha[1][1]} )")


def test_victimes():
    """Les memes campagnes. Attaques : au moins 3 pieges ; au moins 60 % sauves ; chaque piege est sauve ou mort ; chaque
    mort passe par `deceder` ( deces_j pose, cause accident ) ; chaque sauve d ISS >= 9 est entre dans le systeme de soins
    ( domaine 17 ) ou y est mort ; les intoxiques legers sont blesses par la medecine. Non attaques : aucun sauve, tous
    les pieges morts."""
    w, p, ids = _campagne(False)
    _, pb, ib = _campagne(True)
    S = SC._dom(p); Sb = SC._dom(pb)
    fs = [S.finis[i] for i in ids]; fb = [Sb.finis[i] for i in ib]
    pieges = sum(s.sauves + s.morts for s in fs)
    col = p.colonnes["habitant"]
    morts = [i for s in fs for i in s.victimes if not w.habitants[i].vivant]
    par_deceder = all(col["deces_j"][i] >= 0 and POP.CAUSES[int(col["cause_deces"][i])] == "accident" for i in morts)
    vus_17 = {x[1] for x in p.domaine("hopitaux").historique} | set(p.domaine("hopitaux").actifs)
    iss = {}
    for e in p.socle.journal.derniers("blessure", 10000):
        if e["nature"] == "brulure": iss[e["habitant"]] = max(iss.get(e["habitant"], 0), e["iss"])
    blessures = set(iss)
    victimes = [i for s in fs for i in s.victimes]
    soignes = all(i in vus_17 or not w.habitants[i].vivant for i in victimes if iss.get(i, 0) >= 9)
    b_sauves = sum(s.sauves for s in fb); b_morts = sum(s.morts for s in fb)
    ok = (pieges >= 3 and sum(s.sauves for s in fs) >= 0.6 * pieges and par_deceder and soignes
          and all(not s.pieges for s in fs) and b_sauves == 0 and b_morts >= 1
          and all(i in blessures or not w.habitants[i].vivant for i in victimes))
    return ok, (f"attaques : {pieges} pieges, {sum(s.sauves for s in fs)} sauves, {sum(s.morts for s in fs)} morts, "
                f"{sum(s.blesses for s in fs)} blesses ( {len(set(victimes) & vus_17)} passes par les hopitaux ), morts par "
                f"deceder {'oui' if par_deceder else 'NON'} ; non attaques : {b_sauves} sauves, {b_morts} morts")


# ================================================================== conservation, falsificateurs
def test_conservation():
    """3 jours a 1 000 habitants avec les services publics, des feux de logement ( taux x 300 ) et un feu de vegetation :
    le Parc de mes engins est propre ( comptes = naissances et sorties, individus = ma table ) ; l eau prelevee = versee +
    citernes + perdue au millionieme de m3, et ce que j ai tire aux bornes = le compteur `c_incendie` des services publics ;
    la conservation du socle tient ; le rapprochement du Service est nul ; un instantane pris pendant le feu reprend a
    l identique. Falsificateurs : 1 m3 ajoute a une citerne a la
    main, un engin sorti du Parc a la main, 5 drachmes retirees de la caisse du Service : chacun est vu."""
    w, p = T.monde(["securite_civile", "services_publics"], graine=13, echelle=2)
    S = SC._dom(p)
    rap = R.Rapprochement(p.socle.registre, p.socle.livre)
    SC.scenario(p, habitation=300.0)
    T.jours(w, 1); _a_l_heure(w, 13.0)
    vil = sorted(l for l in S.voisins if w.carte.lieux[l].type == "village")[0]
    SC.allumer(p, "foret", lieu=vil)
    for _ in range(3): w.pas_suivant()
    repris = pickle.loads(pickle.dumps(w))                  # un instantane pendant le feu, engins en route
    T.jours(w, 2); T.jours(repris, 2)
    identique = (SC._dom(repris.pays).archives == S.archives and repris.argent_total() == w.argent_total()
                 and SC.bilan_eau(repris.pays) == SC.bilan_eau(p))
    a0 = SC.audit_engins(p); e0 = SC.bilan_eau(p)
    c12 = p.domaine("services_publics").c_incendie
    tenue, msg = p.socle.conservation.tenue()
    reste0 = rap.restes().get("service_incendie", 0.0)
    fin = len(S.archives); verse = S.eau["verse"]
    e = next(x for x in S.engins if x.vivant and x.mission < 0)
    e.eau += 1.0; e1 = SC.bilan_eau(p); e.eau -= 1.0
    S.service.caisse -= 5.0; reste1 = rap.restes()["service_incendie"]; S.service.caisse += 5.0
    o = p.socle.parc.objets[e.oid]; p.socle.parc.sortir(o, "detruit"); a1 = SC.audit_engins(p)
    ok = (SC.audit_propre(a0) and abs(e0) <= 1e-6 and abs(S.eau["borne"] - c12) <= 1e-6 and tenue and abs(reste0) <= 1e-6
          and fin >= 2 and verse > 0 and identique and abs(e1 + 1.0) <= 1e-6 and abs(reste1 + 5.0) <= 1e-6 and not SC.audit_propre(a1))
    return ok, (f"{fin} sinistres, instantane pendant le feu {'repris a l identique' if identique else 'DIFFERENT'}, "
                f"{verse:.1f} m3 verses, {S.eau['borne']:.1f} m3 aux bornes ( services publics "
                f"{c12:.1f} ) ; bilan de l eau {e0:+.1e} m3 ; engins {'propres' if SC.audit_propre(a0) else a0} ; "
                f"conservation {msg} ; rapprochement du Service {reste0:+.1e} ; falsificateurs : eau {e1:+.2f} m3, caisse "
                f"{reste1:+.2f} dr, engin sorti {'vu' if not SC.audit_propre(a1) else 'NON VU'}")


def test_falsificateur_sinistres():
    """Sur la campagne attaquee : les audits sont vides. Un sinistre fini par consume maquille en « eteint par attaque »
    sans engin ni eau, et un batiment passe a D3 a la main ( hors endommager ) : chacun est vu."""
    w, p, ids = _campagne(False)
    S = SC._dom(p); TB = IM._dom(p).B
    a0, d0 = SC.audit_sinistres(p), SC.audit_degats(p)
    s = next((S.finis[i] for i in sorted(S.finis) if S.finis[i].nature == "habitation"), None)
    garde = (s.fin, s.pas_arrivee, list(s.engins), s.eau)
    s.fin, s.pas_arrivee, s.engins, s.eau = "attaque", -1, [], 0.0
    a1 = SC.audit_sinistres(p)
    s.fin, s.pas_arrivee, s.engins, s.eau = garde
    b = next(b for b in range(TB.n) if TB["vivant"][b] == 1 and TB["dommage"][b] == 0)
    TB["dommage"][b] = 3; d1 = SC.audit_degats(p); TB["dommage"][b] = 0
    ok = not a0 and not d0 and any(x[1] == s.id for x in a1) and any(x[1] == b for x in d1)
    return ok, (f"audits propres : sinistres {len(a0)} manquement(s), degats {len(d0)} ; maquillage vu {a1[:1]} ; "
                f"degat hors endommager vu {d1[:1]}")


# ================================================================== le delai
def test_delai_distance():
    """A 1 000 habitants : un feu de logement toutes les 90 minutes dans 12 lieux habites de plus en plus loin de leur
    caserne. Le delai de premiere arrivee realise ( en pas ) = le plafond du delai calcule sur 10 minutes ; le delai croit
    avec la distance ( Spearman >= 0,8 ) ; aucun delai sous le temps de route a la vitesse de l engin ; mediane des feux
    dans le lieu de la caserne : 12 minutes au plus."""
    w, p = T.monde(["securite_civile"], graine=17, echelle=2)
    _calme(p); S = SC._dom(p)
    T.jours(w, 1); _a_l_heure(w, 8.0)
    d13 = IM._dom(p); TB = d13.B
    cas = {c.lieu: c for c in S.casernes}
    def km(l):
        c = S.casernes[S.caserne_de_marche[w.carte.lieux[l].marche.id]]
        return 0.0 if c.lieu == l else w.carte.km_route(w.carte.lieux[c.lieu], w.carte.lieux[l])
    lieux = sorted({d13.lieux[int(TB["lieu"][b])] for b in range(TB.n) if TB["vivant"][b] == 1
                    and IM.NOMS_MODELES[int(TB["modele"][b])] in ("maison", "appartement")
                    and w.carte.lieux[d13.lieux[int(TB["lieu"][b])]].marche is not None}, key=lambda l: (km(l), l))
    pris = [lieux[int(k)] for k in np.linspace(0, len(lieux) - 1, 12).round().astype(int)]
    ids = []
    for l in pris:
        b = next(b for b in range(TB.n) if TB["vivant"][b] == 1 and d13.lieux[int(TB["lieu"][b])] == l
                 and IM.NOMS_MODELES[int(TB["modele"][b])] in ("maison", "appartement"))
        ids.append((SC.allumer(p, "habitation", b=b), l))
        for _ in range(9): w.pas_suivant()
    T.jours(w, 1)
    rows = []
    for sid, l in ids:
        s = S.finis.get(sid) or S.actifs.get(sid)
        k0 = s.engins[0] if s.engins else None
        rows.append((km(l), s.delai_min, s.pas_arrivee - s.pas_appel, l in cas))
    x = np.array([r[0] for r in rows]); y = np.array([r[1] for r in rows])
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    rho = float(np.corrcoef(rx, ry)[0, 1])
    pas_ok = all(r[2] == max(1, math.ceil(r[1] / C.MINUTES_PAR_PAS - 1e-9)) for r in rows)
    plancher = all(r[1] >= r[0] / max(SC.VITESSE) * 60.0 for r in rows)
    ville = [r[1] for r in rows if r[3]]
    ok = rho >= 0.8 and pas_ok and plancher and ville and float(np.median(ville)) <= 12.0
    return ok, (f"12 feux de 0 a {x.max():.1f} km : delais {y.min():.0f} a {y.max():.0f} min, Spearman {rho:.2f} ; pas "
                f"realises = delai calcule {'oui' if pas_ok else 'NON'} ; mediane au lieu de la caserne "
                f"{float(np.median(ville)) if ville else -1:.0f} min")


def test_route_coupee():
    """Avec les services publics : les troncons du trajet d une caserne a son village le plus eloigne sont coupes. Le
    delai calcule s allonge d au moins 50 % ; un feu allume ensuite est atteint au plus tot au plafond de ce delai."""
    from . import d12_services_publics as SP
    w, p = T.monde(["securite_civile", "services_publics"], graine=19, echelle=2)
    _calme(p); S = SC._dom(p)
    T.jours(w, 1); _a_l_heure(w, 10.0)
    c = S.casernes[0]
    d13 = IM._dom(p); TB = d13.B
    batis = {d13.lieux[int(TB["lieu"][b])] for b in range(TB.n) if TB["vivant"][b] == 1}
    vils = [l for l in sorted(S.voisins) if w.carte.lieux[l].type in ("village", "ville") and l in batis
            and w.carte.lieux[l].marche is not None and w.carte.lieux[l].marche.id == c.lieu]
    v = max(vils, key=lambda l: (w.carte.km_route(w.carte.lieux[c.lieu], w.carte.lieux[l]), l))
    avant = SC.delai_intervention_min(p, c.lieu, v)
    ch = SP.chemin(p, SP._index(p, c.lieu), SP._index(p, v))
    for t in ch.tolist(): SP.couper_troncon(p, t, "porte")
    apres = SC.delai_intervention_min(p, c.lieu, v)
    b = next(b for b in range(TB.n) if TB["vivant"][b] == 1 and d13.lieux[int(TB["lieu"][b])] == v)
    sid = SC.allumer(p, "habitation", b=b)
    T.jours(w, 1)
    s = S.finis.get(sid) or S.actifs.get(sid)
    atteint = s.pas_arrivee - s.pas_appel
    ok = len(ch) >= 1 and apres >= 1.5 * avant and atteint >= math.ceil(apres / C.MINUTES_PAR_PAS - 1e-9)
    return ok, (f"{c.lieu} -> {v} : {len(ch)} troncon(s) coupe(s), delai {avant:.0f} -> {apres:.0f} min ; feu atteint en "
                f"{atteint} pas ( {s.fin or 'en cours'}, dommage {s.dommage} )")


# ================================================================== catastrophes et secours routiers
def _catastrophes(suspendu):
    w, p = T.monde(["securite_civile"], graine=41, echelle=3)
    _calme(p)
    if suspendu: SC.suspendre(p)
    S = SC._dom(p)
    T.jours(w, 1); _a_l_heure(w, 2.0)
    cap = sorted(w.marches)[0]
    SC.seisme(p, {cap: 9.0})
    dec = [s.id for s in S.actifs.values() if s.nature == "decombres"] + \
          [s.id for s in S.finis.values() if s.nature == "decombres"]
    pieges = sum(len(S.actifs[i].pieges) for i in dec if i in S.actifs)
    T.jours(w, 1)
    tb = w.table
    hab = np.bincount(tb.domicile[:tb.n][(tb.vivant[:tb.n] != 0) & (tb.domicile[:tb.n] >= 0)], minlength=len(w.carte.par_n))
    ville = max((l for l in sorted(w.carte.lieux) if w.carte.lieux[l].type == "ville"),
                key=lambda l: (hab[w.carte.lieux[l].n], l))
    cr = SC.inonder(p, ville, 3)
    _a_l_heure(w, 20.0)
    for k in range(10):
        p.noter("accident_de_la_route", lieu=sorted(w.carte.lieux)[k], modele="citadine", victimes=2, tues=0)
    _a_l_heure(w, 20.5); w.pas_suivant()
    rt = [s.id for s in S.actifs.values() if s.nature == "route"]
    T.jours(w, 1)
    def s_(i): return S.finis.get(i) or S.actifs.get(i)
    return {"pieges": pieges, "sauves": sum(s_(i).sauves for i in dec), "morts": sum(s_(i).morts for i in dec),
            "restent": sum(len(s_(i).pieges) for i in dec), "crue": s_(cr) if cr >= 0 else None,
            "route": [s_(i) for i in rt], "audit": [x for x in SC.audit_degats(p) + SC.audit_sinistres(p)
                                                    if x[0] != "commerce_seisme_sans_sinistre"],
            "d13": sum(1 for x in SC.audit_degats(p) if x[0] == "commerce_seisme_sans_sinistre")}


def test_seisme_crue_route():
    """1 500 habitants. Un seisme d intensite IX sur une capitale a 2 h : les effondres ( D4, D5 ) retiennent des pieges ;
    attaques, au moins 60 % des pieges vivants sont sortis ( ecrasement, domaine 16 ), tous sont sortis ou morts en deux
    jours ; sans engins, aucun n est sorti et il meurt plus de monde. Une crue de degre 3 : au moins 90 % des exposes
    evacues, aucun sans engins. Dix accidents avec coinces : les secours routiers finissent par desincarceration ;
    aucun sans engins. Audits de degats et de sinistres propres ( hors le defaut connu du domaine 13 : un commerce tire
    de sa cohorte par un seisme recoit son dommage sans sinistre enregistre ; compte a part )."""
    a, b = _catastrophes(False), _catastrophes(True)
    ca, cb = a["crue"], b["crue"]
    ok = (a["pieges"] >= 5 and a["sauves"] >= 0.6 * a["pieges"] and a["restent"] == 0 and b["sauves"] == 0
          and b["morts"] > a["morts"] and ca is not None and ca.evacues >= 0.9 * (ca.evacues + len(ca.exposes) + ca.morts)
          and cb is not None and cb.evacues == 0 and a["route"] and all(s.fin == "secours" for s in a["route"])
          and all(s.fin != "secours" for s in b["route"]) and not a["audit"])
    return ok, (f"seisme : {a['pieges']} pieges, {a['sauves']} sortis, {a['morts']} morts, {a['restent']} restent ; sans "
                f"engins {b['sauves']} sortis, {b['morts']} morts ; crue : {ca.evacues if ca else 0} evacues, "
                f"{ca.morts if ca else 0} morts ( sans engins {cb.evacues if cb else 0} evacues, "
                f"{cb.morts if cb else 0} morts ) ; secours routiers {len(a['route'])} "
                f"( {sum(1 for s in a['route'] if s.fin == 'secours')} desincarceres ; sans engins "
                f"{sum(1 for s in b['route'] if s.fin == 'secours')} ) ; audits {len(a['audit'])} manquement(s) ; defaut du domaine 13 : "
                f"{a['d13']} commerce(s) endommage(s) par le seisme sans sinistre enregistre")


# ================================================================== la decision
def _monde_ete(mode, graine=53, jours_feux=10):
    """3 000 habitants, un ete chaud sans pluie ( +4 degres ) et des departs multiplies ( logements x 8 000, sites x 30,
    vegetation x 30 : ~ 40 sinistres par jour pour 6 engins ) pendant 10 jours, puis l horizon du point."""
    w, p = T.monde(["securite_civile"], graine=graine, echelle=6, modes={"dispatch": mode})
    TER.forcer_meteo(p, "Altis", jours_feux + 5, pluie=0.0, chaleur_c=4.0)
    SC.scenario(p, habitation=8000.0, industriel=30.0, foret=30.0)
    T.jours(w, jours_feux)
    _calme(p)
    T.jours(w, SC.HORIZON_DISPATCH + 1)
    return w, p


def _perte_moyenne(p):
    S = SC._dom(p)
    return float(np.mean([SC.perte(p, S, a[0]) for a in S.archives if a[0] in S.finis])) if S.archives else 0.0


def test_decision():
    """Porte du point `dispatch`, en mode hasard, dans l ete de `_monde_ete` : au moins 100 notes, au moins 3 jours ou
    chaque action a au moins 2 notes, part du choix >= 0,01 ET p de permutation < 0,05. En regard ( sans seuil ) : la
    perte moyenne par sinistre quand la regle, puis le temoin, decident.
    Historique des mesures ( seuils jamais changes ) : ( 1 ) un ete de secheresse imposee ( +6 degres ) : 55 decisions,
    part 0,000 - chaque feu de vegetation echappait quoi qu on envoie ( 35 000 ha, plafond non cumule, corrige ) ;
    ( 2 ) un tic de trop par pas ( les feux vivaient deux pas par pas, corrige ) ; ( 3 ) apres correction, a 2 000 et
    3 000 habitants et trois graines : 38 a 271 decisions, part 0,000 a 0,33, p 0,035 a 1 ; a 30 000 habitants ( 12
    engins, 500 a 1 300 decisions ) : part 0,000 a 0,015, p 0,15 a 1. Les moyennes par action se rapprochent quand les
    decisions se comptent par centaines : sous la penurie, le choix DEPLACE la perte entre ce sinistre et ceux qui
    attendent ( le temps-engin se conserve ) ; son effet vit dans l interaction avec le contexte ( victimes signalees,
    feu de vegetation ), que la part du choix, effet principal de l action a jour egal, ne voit pas."""
    w, p = _monde_ete("hasard")
    dec = SC._dom(p).decideur
    part, pval = dec.part_du_choix(), dec.p_permutation()
    notes = sum(n for n, _, _ in dec.stats.values())
    par_jour = {}
    for (j, a), (n_, _, _) in dec.stats.items(): par_jour.setdefault(j, {})[a] = n_
    jours_ok = sum(1 for d in par_jour.values() if all(d.get(a, 0) >= 2 for a in range(len(SC.ACTIONS))))
    S = SC._dom(p)
    pertes = {m: _perte_moyenne(_monde_ete(m)[1]) for m in ("regle", "temoin")}
    ok = notes >= 100 and jours_ok >= 3 and part >= 0.01 and pval < 0.05
    return ok, (f"{dec.n_decisions} decisions, {notes} notes, {jours_ok} jours a 2 notes par action ou plus ; part du "
                f"choix {part:.3f}, p {pval:.3f} ; notes " + ", ".join(f"{a} {m:.3f} ( {n} )" for a, (n, m) in
                                                                       dec.notes_par_action().items())
                + f" ; {len(S.archives)} sinistres ; perte moyenne par sinistre : hasard {_perte_moyenne(p):.3f}, regle "
                f"{pertes['regle']:.3f}, temoin {pertes['temoin']:.3f}")


# ================================================================== le financement
def test_financement():
    """5 jours a 1 000 habitants et deux feux de logement le premier jour : l Etat a dote le Service ; les soldes payes =
    professionnels vivants x jours x solde ( au centime pres par jour ) ; les engins rentres ont paye leur gazole et
    leur entretien ( domaine 14 ) ; la caisse du Service n est jamais negative ; aucun impaye du Service ;
    rapprochement nul."""
    w, p = T.monde(["securite_civile"], graine=23, echelle=2)
    S = SC._dom(p)
    for b in _logements_occupes(p, membres_min=1)[:2]: SC.allumer(p, "habitation", b=b)
    rap = R.Rapprochement(p.socle.registre, p.socle.livre)
    impayes = 0.0; mini = S.service.caisse; jours_pros = 0
    tb = w.table
    for _ in range(5):
        for _ in range(PAS_J):
            w.pas_suivant(); mini = min(mini, S.service.caisse)
        impayes += sum(v[0] for m, v in (p.comptes_hier or {}).get("impayes", {}).items()
                       if m in ("solde_pompier", "vacation_pompier", "dotation_securite_civile"))
        jours_pros += sum(1 for c in S.casernes for i in c.pros if tb.vivant[i])
    pros = sum(len(c.pros) for c in S.casernes)
    attendu = jours_pros * SC.SOLDE_EUROS_MOIS / SC.EUROS / 30.4
    reste = rap.restes()["service_incendie"]
    ok = (S.service.recu_etat > 0 and abs(S.service.soldes - attendu) <= 0.01 * 5 * pros and mini >= -1e-9
          and S.service.carburant > 0 and S.service.entretien > 0
          and impayes <= 1e-9 and abs(reste) <= 1e-6)
    return ok, (f"{pros} professionnels : soldes {S.service.soldes:.0f} dr pour {attendu:.0f} attendus ; dotation de l Etat "
                f"{S.service.recu_etat:.0f} dr ; carburant {S.service.carburant:.0f}, entretien {S.service.entretien:.0f} ; "
                f"caisse minimale {mini:.0f} ; impayes {impayes:.2f} ; rapprochement {reste:+.1e}")


def test_pays_vivable():
    return T.porte_commune("securite_civile", n_jours=12)


# ================================================================== le cout
def _climat_fixe(profil, annees, rng):
    return np.full((annees, 365), 5.0)



def test_cout():
    """A 10 000 habitants, avec le coeur Rust : les routines propres du domaine ( un jour ) coutent au plus 25 % d une
    journee du moteur seul. Installer le domaine ( sur ses dependances deja installees ), HORS la climatologie du FFDI
    ( un cout fixe par ile, qui ne depend pas de la population, mesure a part ), coute a 100 000 habitants au plus 20
    fois ce qu il coute a 10 000 ( lineaire : ~ 10 ; quadratique : ~ 100 )."""
    w0 = W.Monde(echelle=20)
    T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    inst = {}
    vrai = SC.ffdi_climatologique
    for ech in (20, 200):
        w = W.Monde(echelle=ech)
        P.installer(w, ["immobilier", "transport", "hopitaux"])
        SC.ffdi_climatologique = _climat_fixe            # la part qui suit la population, mesuree seule
        try:
            t0 = time.perf_counter(); P.installer(w, ["securite_civile"]); inst[ech] = time.perf_counter() - t0
        finally:
            SC.ffdi_climatologique = vrai
        if ech == 20: w20 = w
    p = w20.pays; S = SC._dom(p)
    T.jours(w20, 1)
    t0 = time.perf_counter()
    for _ in range(3):
        SC._avant_seisme(p); SC._apres_seisme(p); SC._departs(p); SC._crues(p); SC._meteo_du_jour(p); SC._garde(p)
        SC._secours_routiers(p); SC._paie(p); SC._cloture(p, None)
    propre = (time.perf_counter() - t0) / 3
    t0 = time.perf_counter()
    SC.ffdi_climatologique(TER.PROFILS["Altis"], SC.ANNEES_CLIMAT, np.random.default_rng(0))
    clim = time.perf_counter() - t0
    ratio = inst[200] / inst[20]
    ok = propre <= 0.25 * t_e1 and ratio <= 20.0
    return ok, (f"coeur Rust {'present' if W.COEUR is not None else 'ABSENT'} ; {len(w20.habitants)} habitants, "
                f"{len(S.engins)} engins, {sum(len(c.pros) + len(c.volontaires) for c in S.casernes)} pompiers : moteur "
                f"seul {t_e1:.2f} s par jour, routines propres {propre * 1000:.1f} ms ( {propre / t_e1:.1%} ) ; "
                f"installation hors climatologie {inst[20]:.3f} s a 10 000, {inst[200]:.3f} s a 100 000 ( x{ratio:.1f} ) ; "
                f"climatologie {clim:.2f} s par ile")


TESTS = [test_departs_de_feu, test_feu_attaque_contre_non_attaque, test_victimes, test_conservation,
         test_falsificateur_sinistres, test_delai_distance, test_route_coupee, test_seisme_crue_route, test_decision,
         test_financement, test_pays_vivable, test_cout]
