"""Les portes du domaine 12 ( services publics ). Seuils ecrits avant la premiere mesure.
python -m monde.pays.tests services_publics"""
import math, time
import numpy as np
from .. import monde as W
from ..socle import registre as RG
from . import essais as T, d08_territoire as TER, d12_services_publics as M


def _tol(x, volume): return 1e-6 + 1e-9 * abs(volume)


# ================================================================== l eau potable
def test_bilan_eau():
    """Porte : 20 jours. L eau potable produite = 0,97 x l eau brute que le territoire a vue prelever pour l usage
    domestique, et produite = consommee + perdue + reservoirs, au millionieme du volume. Conservation du socle tenue.
    Falsificateurs : 50 m3 produits sans captage ( sous le motif du domaine ) se voient au premier bilan ; 30 m3 poses
    a la main dans un reservoir se voient au second et a la conservation."""
    w, p = T.monde(["services_publics"])
    T.jours(w, 20)
    S = p.domaine("services_publics"); L = p.socle.livre
    e1, e2 = M.bilan_eau(p)
    vol = L.flux["produit"]["eau_potable"]
    tenue, msg = p.socle.conservation.tenue()
    ok0 = abs(e1) <= _tol(e1, vol) and abs(e2) <= _tol(e2, vol) and tenue and vol > 0
    sy = max(S.systemes, key=lambda s: s.i_nom)
    L.produire(sy.stock, S.eau_id, 50.0, "potabilisation")
    f1 = M.bilan_eau(p)[0]
    sy.stock._ajouter(S.eau_id, 30.0)
    f2 = M.bilan_eau(p)[1]
    tenue2, _ = p.socle.conservation.tenue()
    vu = abs(f1 - e1 - 50.0) < 1e-6 and abs(f2 - e2 + 30.0) < 1e-6 and not tenue2
    return ok0 and vu, (f"{vol:.0f} m3 produits en 20 jours : ecart au captage {e1:+.2e}, ecart au bilan {e2:+.2e} ; {msg} ; "
                        f"50 m3 sans captage vus {f1 - e1:+.1f}, 30 m3 poses a la main vus {f2 - e2:+.1f} et conservation "
                        f"{'rompue' if not tenue2 else 'INTACTE'}")


def test_consommation():
    """Porte : 20 jours, eau abondante. La consommation par habitant servi est dans la bande grecque ( 150 a 200 litres
    par jour ) et l eau non facturee de 30 a 45 % du volume injecte ( DEYA grecques : 35 a 40 % ). Chaque menage habite
    a recu une facture au moins ; la TVA de l eau est entree au Tresor."""
    w, p = T.monde(["services_publics"])
    T.jours(w, 31)
    conso, enf = M.mesures_eau(p)
    fm = p.col("menage", "sp_eau_m3")
    hab = [m for m in T.menages_habites(w)]
    factures = sum(1 for m in hab if fm[m.id] > 0) / max(1, len(hab))
    paye = sum(s for (mo, pa, re), (s, n) in p.socle.livre.jour_argent.items() if mo == "facture_eau")
    net = p.socle.livre.net_par_classe().get("RegieEau", 0.0)
    ok = M.BANDE_CONSO[0] <= conso <= M.BANDE_CONSO[1] and 0.30 <= enf <= 0.45 and factures >= 0.99 and w.tva_percue > 0
    return ok, (f"{conso * 1000:.0f} litres par habitant servi et par jour ; eau non facturee {enf:.1%} ; menages factures "
                f"{factures:.0%} ; recettes nettes des regies depuis l installation {net:.0f} drachmes")


def test_coupures_et_qualite():
    """Controle positif : une secheresse ( reserves a 2 %, 25 jours sans pluie ) coupe l eau par quartiers - des lieux
    passent des jours sans eau, les coupures tournent ( au moins deux lieux touches, aucun lieu habite ne manque tous
    les jours alors que d autres sont servis ), et la qualite suit : E. coli par intrusion dans le reseau intermittent,
    facteur de gastro > 1,5 quelque part. Puis une crue posee sur un bassin : l eau brute trouble ( > 5 NTU ) ne se
    desinfecte plus a 3 log - E. coli du robinet multiplie par au moins 10 dans ce bassin. Temoin : le meme monde sans
    secheresse n a aucun jour sans eau."""
    w0, p0 = T.monde(["services_publics"])
    T.jours(w0, 12)
    temoin = int(p0.domaine("services_publics").eau.jours_sans_eau.sum())
    w, p = T.monde(["services_publics"])
    TER.imposer_secheresse(p, "Altis", 25, reserves=0.02)
    T.jours(w, 12)
    S = p.domaine("services_publics"); E = S.eau
    touches = int((E.jours_sans_eau > 0).sum()); total = int(E.jours_sans_eau.sum())
    habites = E.hab > 0
    toujours = int(((E.jours_sans_eau >= 12) & habites).sum())
    Te = p.domaine("territoire")
    fg = max(M.facteur_gastro(p, Te.lieux[k]) for k in np.nonzero(habites)[0].tolist())
    ecoli = float(E.ecoli[habites].max())
    # la crue
    w2, p2 = T.monde(["services_publics"])
    T.jours(w2, 2)
    S2 = p2.domaine("services_publics"); T2 = p2.domaine("territoire")
    sy = max(S2.systemes, key=lambda s: s.i_nom)
    k = int(sy.lieux[0])
    avant = float(S2.eau.ecoli[k])
    T2.catastrophes.append(TER.Catastrophe("inondation", "Altis", T2.bassins.nom[sy.bassin], 2, p2.jour, p2.jour + 2, 80.0))
    M._eau(p2)
    apres, turb = float(S2.eau.ecoli[k]), float(S2.eau.turb[k])
    ok = (temoin == 0 and touches >= 2 and total >= 5 and toujours <= max(0, touches - 2) and fg > 1.5
          and apres >= 10 * max(avant, 1e-9) and turb > 1.0)
    return ok, (f"temoin : {temoin} jour-lieu sans eau ; secheresse : {total} jours-lieux sans eau sur {touches} lieux "
                f"( {toujours} lieux sans eau tous les jours ) ; E. coli max {ecoli:.1f} / 100 ml ; facteur de gastro max "
                f"{fg:.2f} ; crue sur {T2.bassins.nom[sy.bassin]} : E. coli {avant:.4f} -> {apres:.3f}, turbidite {turb:.1f} NTU")


# ================================================================== les dechets
def test_bilan_dechets():
    """Porte : 20 jours. Dechets produits = collectes + accumulation aux conteneurs ; collectes = recycles + enfouis, au
    millionieme ; la collecte suit ( accumulation finale sous 4 jours de production ) ; la part recyclee est celle de la
    Grece ( 21 % ). Falsificateur : une tonne posee a la main dans un conteneur se voit au bilan et a la conservation."""
    w, p = T.monde(["services_publics"])
    T.jours(w, 20)
    S = p.domaine("services_publics"); L = p.socle.livre
    e1, e2 = M.bilan_dechets(p)
    prod = L.flux["produit"]["dechets"]
    aux = math.fsum(pt.stock[S.dechets_id] for pt in S.points)
    jour = float(S.eau.hab.sum()) * M.DECHETS_T_HAB_J
    part = S.c_recycle / max(1e-9, S.c_collecte)
    tenue, msg = p.socle.conservation.tenue()
    ok0 = abs(e1) <= _tol(e1, prod) and abs(e2) <= _tol(e2, prod) and tenue and aux <= 4 * jour and abs(part - M.PART_RECYCLEE) < 1e-6
    pt = max(S.points, key=lambda x: S.eau.hab[x.lieu])
    pt.stock._ajouter(S.dechets_id, 1.0)
    f1 = M.bilan_dechets(p)[0]
    tenue2, _ = p.socle.conservation.tenue()
    ok = ok0 and abs(f1 - e1 + 1.0) < 1e-6 and not tenue2
    return ok, (f"{prod:.2f} t produites en 20 jours ( {jour * 1000:.0f} kg par jour ) : ecarts {e1:+.1e} et {e2:+.1e} ; "
                f"{aux / jour:.1f} jours de production aux conteneurs ; recycle {part:.0%} ; {msg} ; tonne posee a la main "
                f"vue {f1 - e1:+.2f} et conservation {'rompue' if not tenue2 else 'INTACTE'}")


def test_greve_collecte():
    """Controle positif : une greve de 10 jours des eboueurs d Altis ( du jour 2 au jour 12 ) : l accumulation aux
    conteneurs depasse celle du monde jumeau sans greve d au moins 8 jours de production ; 10 jours apres la reprise,
    elle est revenue sous 4 jours de production ; l insalubrite du lieu le plus touche depasse 7 jours."""
    def monde(greve):
        w, p = T.monde(["services_publics"])
        T.jours(w, 2)
        if greve: M.greve_collecte(p, "Altis", 10)
        T.jours(w, 10)
        return w, p
    def accu(p):
        S = p.domaine("services_publics")
        return math.fsum(pt.stock[S.dechets_id] for pt in S.points), float(S.eau.hab.sum()) * M.DECHETS_T_HAB_J
    w0, p0 = monde(False); w1, p1 = monde(True)
    a0, j0 = accu(p0); a1, j1 = accu(p1)
    Te = p1.domaine("territoire")
    pire = max(M.insalubrite(p1, lid) for lid in Te.lieux)
    T.jours(w1, 10)
    a2, j2 = accu(p1)
    ok = (a1 - a0) >= 8 * j1 and a2 <= 4 * j2 and pire > 7
    return ok, (f"apres 10 jours de greve : {a1:.2f} t aux conteneurs contre {a0:.2f} sans greve ( {(a1 - a0) / j1:.1f} jours "
                f"de production de plus ) ; insalubrite du pire lieu {pire:.1f} jours ; 10 jours apres la reprise : "
                f"{a2 / j2:.1f} jours")


# ================================================================== les routes
def test_routes_usure_et_entretien():
    """Porte : deux mondes jumeaux, sans equipes. Dans l un, 150 camions charges par jour pendant 10 jours sur le trajet
    d un village a sa capitale : chaque troncon du trajet perd ce que la loi des essieux dit ( 150 x 1,3 ESAL x 10 x
    K_ESAL ) a 10 % pres, les autres rien de plus. Puis une journee d equipe sur le premier troncon : son etat monte
    de ( km remis en etat / longueur ) a 1 % pres. Controle : sans camions, le vieillissement et la pluie usent quand
    meme ( etat moyen en baisse )."""
    def monde(camions):
        w, p = T.monde(["services_publics"])
        S = p.domaine("services_publics")
        for c in S.communes: c.credit_routes = -1e12
        return w, p
    w0, p0 = monde(False); w1, p1 = monde(True)
    S0, S1 = p0.domaine("services_publics"), p1.domaine("services_publics")
    Te = p1.domaine("territoire")
    k = max((k for k in range(len(Te.lieux)) if len(S1.routes.montee[k]) >= 2), key=lambda k: len(S1.routes.montee[k]))
    ch = np.array(S1.routes.montee[k], np.int64)
    dest = Te.lieux[int(S1.routes.racine[k])]
    e0_depart = S0.routes.etat.copy()
    for _ in range(10):
        T.jours(w0, 1); T.jours(w1, 1)
        M.passer(p1, Te.lieux[k], dest, 150, M.ESAL_CHARGE + M.ESAL_VIDE)
    T.jours(w0, 1); T.jours(w1, 1)
    perte = S0.routes.etat[ch] - S1.routes.etat[ch]
    attendu = 150 * (M.ESAL_CHARGE + M.ESAL_VIDE) * 10 * M.K_ESAL
    autres = np.setdiff1d(np.arange(len(S1.routes.a)), ch)
    autres_ecart = float(np.abs(S0.routes.etat[autres] - S1.routes.etat[autres]).max())
    usure_seule = float((e0_depart - S0.routes.etat).mean())
    t = int(ch[0]); R = S1.routes
    avant = float(R.etat[t])
    c = S1.communes[0]
    gain = M.travailler(p1, c, t)
    km = M.KM_EQUIPE_J * max(2.0, 8.0 - 2.0 * R.km_base[t] / M.VITESSE_EQUIPE_KMH) / 8.0
    attendu_g = min(1.0 - avant, km / R.longueur[t])
    ok = (np.all(np.abs(perte / attendu - 1.0) <= 0.10) and autres_ecart <= 0.1 * attendu and usure_seule > 0
          and abs(gain / attendu_g - 1.0) <= 0.01 and abs(R.etat[t] - avant - gain) < 1e-12)
    return ok, (f"trajet de {Te.lieux[k]} a {dest} ( {len(ch)} troncons ) : perte due aux camions "
                f"{', '.join(f'{x:.4f}' for x in perte)} pour {attendu:.4f} attendu ; ailleurs ecart max {autres_ecart:.1e} ; "
                f"sans camions, usure moyenne en 11 jours {usure_seule:.4f} ; une journee d equipe sur {t} : "
                f"{avant:.3f} -> {R.etat[t]:.3f} ( attendu +{attendu_g:.3f} )")


def test_routes_coupees_et_convois():
    """Porte : un troncon detruit ( seisme pose a la main ) isole les lieux qu il dessert : ils entrent dans
    w.coupures et, apres l aube, dans routes_temporaires ; plus aucun convoi n en part pendant 2 jours alors qu il en
    partait dans le monde jumeau. Et des routes degradees ( etat 0,2 partout ) ralentissent les convois : leur duree
    moyenne est au moins 1,5 fois celle du jumeau aux routes neuves."""
    def monde():
        w, p = T.monde(["services_publics"])
        for c in p.domaine("services_publics").communes: c.credit_routes = -1e12
        return w, p
    w0, p0 = monde(); w1, p1 = monde()
    S1 = p1.domaine("services_publics"); R = S1.routes; Te = p1.domaine("territoire")
    # le troncon dont les lieux font partir le plus de convois ( un site de production )
    sites = [k for k in range(len(Te.lieux)) if w1.carte.lieux[Te.lieux[k]].type in ("mine", "carriere", "puits")]
    k = sites[0]
    t = S1.routes.montee[k][0]
    M.couper_troncon(p1, t, "seisme")
    isoles = set(M.lieux_isoles(p1))
    def partis(w, lieux, j0):
        return sum(1 for c in w.convois if c.origine.id in lieux)
    vus0, vus1 = set(), set()
    for _ in range(2 * 144):
        w0.pas_suivant(); w1.pas_suivant()
        for c in w0.convois:
            if c.origine.id in isoles: vus0.add(c.id)
        for c in w1.convois:
            if c.origine.id in isoles: vus1.add(c.id)
    dans_coupures = isoles <= {c["lieu"] for c in w1.coupures}
    dans_temp = isoles <= set(getattr(w1, "routes_temporaires", set()))
    # ralentissement
    def durees(etat):
        w, p = monde()
        S = p.domaine("services_publics")
        S.routes.etat[:] = etat
        d = []
        vus = set()
        for _ in range(2 * 144):
            w.pas_suivant()
            for c in w.convois:
                if c.id not in vus: vus.add(c.id); d.append(c.arrivee - c.depart)
        return float(np.mean(d)) if d else 0.0, len(d)
    dn, nn = durees(1.0); dd, nd = durees(0.2)
    ok = dans_coupures and dans_temp and len(vus0) >= 1 and len(vus1) == 0 and dd >= 1.5 * dn and nd > 0
    return ok, (f"troncon {t} detruit : {len(isoles)} lieux isoles ( {', '.join(sorted(isoles))} ) dans coupures {dans_coupures}, "
                f"routes_temporaires {dans_temp} ; convois partis de ces lieux en 2 jours : {len(vus0)} dans le jumeau, "
                f"{len(vus1)} ici ; duree moyenne d un convoi : {dn:.2f} pas ( routes neuves, {nn} convois ) contre {dd:.2f} "
                f"( etat 0,2, {nd} convois )")


# ================================================================== l energie
def test_energie_pompage_eclairage():
    """Porte, avec le domaine 11 : un contrat prioritaire par systeme d eau, servi ; la commune paie l eclairage public
    ( facture_electricite de la Commune au gestionnaire ). Controle positif : la ligne du chef-lieu du plus grand
    systeme coupee 3 jours - le lendemain, son pompage tombe sous la moitie et ses lieux ont moins d eau."""
    w, p = T.monde(["services_publics", "energie"])
    from . import d11_energie as EN
    T.jours(w, 3)
    S = p.domaine("services_publics")
    sy = max(S.systemes, key=lambda s: s.i_nom)
    f_avant = sy.f_elec
    eclairage = sum(s for (mo, pa, re), (s, n) in p.socle.livre.jour_argent.items()
                    if mo == "facture_electricite" and pa == "Commune")
    comptes = p.comptes_hier or {}
    eclairage += sum(s for mo, pa, re, s, n in comptes.get("argent", ()) if mo == "facture_electricite" and pa == "Commune")
    EN.couper_ligne(p, sy.chef_lieu, 3)
    T.jours(w, 2)
    f_apres = sy.f_elec
    phi = float(S.eau.phi[sy.lieux].mean())
    ok = len(S.contrats) >= 1 and f_avant > 0.95 and eclairage > 0 and f_apres < 0.5 and phi < 0.9
    return ok, (f"{len(S.contrats)} contrats de pompage ; {sy.chef_lieu} alimente {f_avant:.0%} des heures ; eclairage "
                f"paye par la commune {eclairage:.1f} drachmes ( veille et jour ) ; ligne coupee : alimente {f_apres:.0%}, "
                f"part servie de ses lieux {phi:.0%}")


# ================================================================== la decision
def test_decision_entretien():
    """Porte de la decision ( conventions, par. 4 ) : apres un hiver rude ( etats tires de 0,05 a 0,8, les troncons
    sous 0,10 fermes ), un programme d urgence de 14 equipes par jour pendant 30 jours ; les equipes choisissent leur
    critere au hasard ( mode hasard ). Au moins 150 notes murees ; part du choix ( epsilon carre intra-jour ) >= 0,01 et
    p de permutation < 0,05."""
    w, p = T.monde(["services_publics"], modes={"entretenir_route": "hasard"})
    S = p.domaine("services_publics"); R = S.routes
    rng = np.random.default_rng(5)
    R.etat[:] = rng.uniform(0.05, 0.8, len(R.a))
    for t in np.nonzero(R.etat < M.S_FERME)[0].tolist(): M._fermer(p, R, t, "hiver")
    M.programme_urgence(p, "Altis", 14, 30)
    T.jours(w, 26)
    dec = S.decideur
    n = sum(v[0] for v in dec.notes_par_action().values())
    part = dec.part_du_choix(); pp = dec.p_permutation()
    notes = dec.notes_par_action()
    brut = {}
    for j, a, note, x in S.notes: brut.setdefault(a, []).append(x)
    ok = n >= 150 and part >= 0.01 and pp < 0.05
    return ok, (f"{dec.n_decisions} decisions, {n} notes : "
                + ", ".join(f"{a} {m:.2f} ( {k} )" for a, (k, m) in notes.items())
                + f" ; service moyen en vehicules-km par jour : "
                + ", ".join(f"{M.CRITERES[a]} {np.mean(v):.0f}" for a, v in sorted(brut.items()))
                + f" ; part du choix {part:.3f}, p = {pp:.3f} ; troncons fermes {int(R.ferme.sum())}")


def test_pays_vivable():
    return T.porte_commune("services_publics", n_jours=12)


def test_cout():
    """Le domaine coute au plus 25 % d une journee du moteur ( avec ses dependances ), a 10 000 habitants : ses routines
    propres, mesurees sur 3 jours."""
    def jour_moyen(doms):
        w, p = T.monde(doms, echelle=20)
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants), p
    t_base, n, _ = jour_moyen(["territoire", "etat"])
    t_avec, _, p = jour_moyen(["services_publics"])
    t0 = time.perf_counter()
    for _ in range(3):
        M._routes_minuit(p); M._recenser(p); M._eau(p); M._equipes(p); M._collecter(p); M._produire_dechets(p)
        for h in range(24): M._convois(p)
        M._soir(p)
    propre = (time.perf_counter() - t0) / 3
    ok = propre <= 0.25 * t_base
    return ok, (f"{n} habitants : pays sans le domaine {t_base:.2f} s par jour, avec {t_avec:.2f} s "
                f"( {t_avec / t_base - 1:+.0%} ) ; routines propres {propre * 1000:.0f} ms par jour, "
                f"{propre / n * 1e6:.1f} us par habitant")


TESTS = [test_bilan_eau, test_consommation, test_coupures_et_qualite, test_bilan_dechets, test_greve_collecte,
         test_routes_usure_et_entretien, test_routes_coupees_et_convois, test_energie_pompage_eclairage,
         test_decision_entretien, test_pays_vivable, test_cout]
