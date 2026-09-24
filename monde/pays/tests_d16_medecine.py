"""Les portes du domaine 16 ( medecine ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests medecine"""
import math, time
import numpy as np
from .. import config as C, monde as W
from . import essais as T, d01_population as POP, d16_medecine as M

TRANSMISSIBLES = tuple(m.nom for m in M.MALADIES if m.transmissible)
GROUPES_SYNTH = np.array((3, 20, 25, 200, 50, 100, 30))   # taille des groupes par cadre, dans la population synthetique


# ================================================================== les lois, sur une population synthetique
def _r0_synthetique(m, n_index, rng, facteur_q=1.0, duree=None):
    """Des cas index dans une population synthetique sans immunite ( 20 000 personnes, groupes de contact retires chaque
    jour, cadres et heures de JOURNEE_TYPE ) ; chaque autre membre d un groupe recoit Poisson( taux_par_membre x heures )
    infections : la definition de R0 ( population entierement susceptible, sans epuisement ). Le q est celui du moteur
    ( q_contact, a l exposition de la journee type ) ; `duree` le recalcule avec une autre duree ( falsificateur )."""
    E = float((M.CONTACTS_H * M.JOURNEE_TYPE).sum())
    q = (M.q_contact(m, E) if duree is None else m.r0 / (E * duree)) * facteur_q
    h = M.tirer_histoires(m, 0.0, np.full(n_index, 40.0), rng)
    poids = np.where(h["asym"], m.k_asym, 1.0)
    N, total = 20000, 0
    cadres = [c for c in range(len(M.CADRES)) if M.JOURNEE_TYPE[c] > 0]
    for d in range(int(math.ceil(h["t_fin_cont"].max())) + 1):
        f = np.clip(np.minimum(d + 1.0, h["t_fin_cont"]) - np.maximum(float(d), h["t_inf"]), 0.0, 1.0) * poids
        act = np.nonzero(f > 0)[0]
        if not len(act): continue
        for c in cadres:
            taille = int(GROUPES_SYNTH[c]); G = N // taille
            gi = rng.integers(0, G, len(act))
            pres = np.bincount(gi, weights=f[act], minlength=G)
            taux = M.taux_par_membre(q, M.CONTACTS_H[c], pres, taille)
            total += int(rng.poisson(taux * M.JOURNEE_TYPE[c] * (taille - 1)).sum())
    return total / n_index, h


def test_r0_et_durees():
    """Porte : chaque maladie transmissible retrouve son R0 a 10 % pres sur la population synthetique ( 2 000 cas index
    si R0 < 5, 400 sinon, 300 pour la tuberculose ), et ses durees tirees retrouvent les lois declarees a 5 % pres
    ( latence, incubation, periode contagieuse, duree de la maladie ; 4 000 histoires ), la part d asymptomatiques a
    0,02 pres. Controle positif : un q double donne 1,85 a 2,15 fois plus d infections ( COVID ). Falsificateur : un q
    cale sur la duree de la MALADIE au lieu de la periode contagieuse est vu faux ( ecart > 10 % ) pour au moins 4
    maladies sur 7."""
    rng = np.random.default_rng(16)
    ok, msgs, faux_vus = True, [], 0
    for nom in TRANSMISSIBLES:
        m = M.PATHOS[M.IP[nom]]
        n = 300 if nom == "tuberculose" else 2000 if m.r0 < 5 else 400
        r, _ = _r0_synthetique(m, n, rng)
        h = M.tirer_histoires(m, 0.0, np.full(4000, 40.0), rng)
        s = ~h["asym"]
        mesures = {"latence": (h["t_inf"].mean(), m.latence[0]),
                   "incubation": (h["t_symp"].mean(), m.latence[0] + m.presympt[0]),
                   "contagieuse": ((h["t_fin_cont"] - h["t_inf"]).mean(), m.presympt[0] + m.contagion[0]),
                   "maladie": (h["duree_maladie"][s].mean(), m.maladie[0])}
        d_ok = all(abs(a / b - 1) <= 0.05 for a, b in mesures.values() if b > 0) and abs(h["asym"].mean() - m.asym) <= 0.02
        rf, _ = _r0_synthetique(m, n, rng, duree=m.maladie[0])
        faux_vus += abs(rf / m.r0 - 1) > 0.10
        ok &= abs(r / m.r0 - 1) <= 0.10 and d_ok
        msgs.append(f"{nom} R {r:.2f}/{m.r0:g} incub {mesures['incubation'][0]:.1f} j contag "
                    f"{mesures['contagieuse'][0]:.1f} j{'' if d_ok else ' DUREES FAUSSES'}")
    cov = M.PATHOS[M.IP["covid"]]
    r1, _ = _r0_synthetique(cov, 2000, rng); r2, _ = _r0_synthetique(cov, 2000, rng, facteur_q=2.0)
    ok &= 1.85 <= r2 / r1 <= 2.15 and faux_vus >= 4
    return ok, " ; ".join(msgs) + f" ; q double : x{r2 / r1:.2f} ; q cale sur la maladie vu faux pour {faux_vus}/7"


def test_diagnostic():
    """Porte : chaque examen a la sensibilite et la specificite declarees a 0,012 pres ( 40 000 malades et 40 000 non
    malades chacun ). Le diagnostic clinique ( symptomes seuls, a priori de consultation ) fait mieux que de toujours
    parier sur la maladie la plus frequente ( +5 points ), sans etre parfait ( au plus 97 % ) : il fait des erreurs,
    grippe et COVID se confondent. Falsificateur : un examen dont la sensibilite reelle est de 5 points sous la
    declaree est vu."""
    rng = np.random.default_rng(7); n = 40000
    ok, pire = True, 0.0
    for ex in M.EXAMENS:
        se = M.resultat_examen(ex, np.ones(n, bool), rng.random(n)).mean()
        sp = 1.0 - M.resultat_examen(ex, np.zeros(n, bool), rng.random(n)).mean()
        pire = max(pire, abs(se - ex.sensibilite), abs(sp - ex.specificite))
    ok &= pire <= 0.012
    ex = M.EX["tdr_strep"]
    truque = M.Examen("truque", ex.cible, ex.sensibilite - 0.05, ex.specificite, ex.lieu, "falsificateur")
    vu = abs(M.resultat_examen(truque, np.ones(n, bool), rng.random(n)).mean() - ex.sensibilite) > 0.012
    # le diagnostic clinique sur des cas symptomatiques tires selon les a priori
    noms = list(M.A_PRIORI); w = np.array([M.A_PRIORI[x] for x in noms]); w = w / w.sum()
    juste = total = conf = 0
    for nom, k in zip(noms, rng.multinomial(20000, w)):
        m = M.PATHOS[M.IP[nom]]
        h = M.tirer_histoires(m, 0.0, np.full(k, 40.0), rng)
        for s in h["symp"][~h["asym"]].tolist():
            d, _ = M.diagnostic_clinique(int(s), M.A_PRIORI)
            juste += d == nom; total += 1
            conf += (nom, d) in (("grippe", "covid"), ("covid", "grippe"))
    acc = juste / max(1, total); base = float(w.max())
    ok &= vu and base + 0.05 <= acc <= 0.97 and conf > 0
    return ok, (f"examens : pire ecart {pire:.4f} ; sensibilite truquee vue {vu} ; diagnostic clinique juste {acc:.1%} "
                f"( toujours la plus frequente : {base:.1%} ) ; grippe et COVID confondues {conf} fois")


def test_resistance():
    """Porte : a l usage grec de reference, la resistance de l amoxicilline reste a 0,005 pres de sa valeur grecque sur
    10 ans ; a l usage double elle gagne au moins 8 points en 5 ans ; sans usage elle en perd au moins 8. Dans le
    moteur ( 30 jours, rhume et angine en saison ), le medecin temoin ( toujours l antibiotique ) consomme plus de DDD
    et laisse une resistance plus haute que la regle. Falsificateur : une loi sans selection ( kappa nul ) ne bouge
    pas a l usage double, et se voit."""
    a = M.ABX["amoxicilline"]
    r_meme = a.pas(a.r_ref, a.u_ref, 3650)
    r_double, r_zero = a.pas(a.r_ref, 2 * a.u_ref, 5 * 365), a.pas(a.r_ref, 0.0, 5 * 365)
    b = M.Antibiotique("sans_selection", a.u_ref, a.r_ref, a.tau_ans, "falsificateur"); b.kappa = 0.0
    fx = b.pas(a.r_ref, 2 * a.u_ref, 5 * 365)
    vu = not fx >= a.r_ref + 0.08
    loi = abs(r_meme - a.r_ref) <= 0.005 and r_double >= a.r_ref + 0.08 and r_zero <= a.r_ref - 0.08
    res = {}
    for mode in ("temoin", "regle"):
        w, p = T.monde(["medecine"], graine=5, modes={"prescrire": mode})
        for nom in ("rhume", "angine", "grippe"): M.forcer_saison(p, nom, 1.0)
        M.introduire(p, "angine", 10)
        T.jours(w, 30)
        med = p.domaine("medecine")
        res[mode] = (float(med.usage[:, 0].mean()), float(med.resistance[:, 0].mean()), med.dec_prescrire.n_decisions,
                     med.compteurs.get("abx_ddd", 0.0))
    moteur = res["temoin"][0] > res["regle"][0] and res["temoin"][1] > res["regle"][1]
    ok = loi and vu and moteur
    return ok, (f"loi : 10 ans a l usage grec {r_meme:.3f} ( ref {a.r_ref} ), usage double {r_double:.3f}, sans usage "
                f"{r_zero:.3f} ; sans selection {fx:.3f} ( vu {vu} ) ; moteur : temoin usage {res['temoin'][0]:.2f} "
                f"DDD/1000/j, "
                f"resistance {res['temoin'][1]:.5f} ( {res['temoin'][2]} decisions ) contre regle {res['regle'][0]:.2f}, "
                f"{res['regle'][1]:.5f} ( {res['regle'][2]} )")


# ================================================================== le domaine dans le moteur
def _attaque(p, nom, n0):
    med = p.domaine("medecine")
    return med.deja[:n0, M.IM[nom]].sum() / max(1, n0)


def test_epidemies_moteur():
    """Porte : une epidemie par maladie dans le moteur ( 1 000 habitants, agenda installe, contacts etalonnes la premiere
    semaine ). COVID introduit ( 20 cas ) jusqu a extinction ( 150 jours au plus ) : taux d attaque de 30 a 95 %,
    letalite par infection de 0,1 a 3 % ( esperance des issues tirees : 1 000 habitants font trop peu de morts pour
    une mesure directe ), des hospitalises, et le R realise par les 20 premiers cas ( leurs infections comptees
    une a une ) a 30 % pres de R0 = 2,8 : l etalonnage sur les contacts du pays tient. Dans un autre monde, 60 jours,
    grippe en pleine saison et gastro introduites ( 10 cas chacune ) : grippe 5 a 50 %, gastro 5 a 80 % ; rhume
    endemique de 1 a 8 episodes par personne et par an, angine de 0,02 a 0,6 ( l incidence de la fenetre, qui tombe en
    ete, est ramenee a l annee par le facteur de saison du modele : moyenne annuelle / moyenne de la fenetre ;
    correction du 23/09, la premiere mesure comparait un ete a un chiffre annuel ). Chaque jour a midi, tout grave
    vivant est a l hopital de sa capitale et personne n y est sans l etre ( 0 incoherence ), et l etat du moteur resume
    les affections ( 0 incoherence ). Toute mort passe par deceder."""
    msgs, ok = [], True
    # --- COVID
    w, p = T.monde(["agenda", "medecine"], graine=21, echelle=2)
    T.jours(w, 8)
    n0 = len(w.habitants)
    index = M.introduire(p, "covid", 20)
    traces = M.suivre_transmission(p, index)
    med = p.domaine("medecine")
    hop_max, incoh_hop, incoh_e1, j = 0, 0, 0, 0
    for j in range(150):
        for _ in range(C.PAS_PAR_JOUR // 4): w.pas_suivant()              # 6 h -> midi
        incoh_hop += len(M.hopital_incoherent(p)); incoh_e1 += len(M.incoherences_e1(p))
        hop_max = max(hop_max, sum(1 for h in w.habitants if h.vivant and h.poste == "hopital"))
        for _ in range(C.PAS_PAR_JOUR - C.PAS_PAR_JOUR // 4): w.pas_suivant()
        k = med.aff.k
        if j > 20 and not (med.aff.actif[:k] & (med.aff.path[:k] == M.IP["covid"])).any(): break
    att = _attaque(p, "covid", n0)
    morts = med.compteurs.get(("deces", "covid"), 0)
    inf = med.compteurs.get(("infections", "covid"), 0)
    ifr = med.compteurs.get(("letal_attendu", "covid"), 0.0) / max(1, inf)
    r_moteur = float(np.mean([traces[i] for i in index]))
    hors = M.morts_hors_deceder(p)
    covid_ok = 0.30 <= att <= 0.95 and 0.001 <= ifr <= 0.03 and hop_max > 0 and 0.7 <= r_moteur / 2.8 <= 1.3
    ok &= covid_ok and not hors
    q = {n_: round(float(med.q[M.IM[n_]]), 3) for n_ in ("grippe", "covid", "rougeole", "rhume")}
    msgs.append(f"COVID {j + 1} jours : R des 20 premiers cas {r_moteur:.2f}, attaque {att:.0%}, letalite attendue "
                f"{ifr:.2%} ( {morts} morts tirees pour {inf} infections ), jusqu a {hop_max} hospitalises ; contacts "
                f"etalonnes {med.expo_ref:.2f} contacts-eq/j ( malade {med.expo_malade or 0:.2f} ), q {q} ; diagnostics "
                f"faux {med.compteurs.get('diagnostics_errones', 0)} sur {med.compteurs.get('diagnostics', 0)} ; morts "
                f"hors deceder {len(hors)}")
    # --- grippe, gastro, rhume, angine
    w2, p2 = T.monde(["agenda", "medecine"], graine=22, echelle=2)
    T.jours(w2, 8)
    med2 = p2.domaine("medecine"); n2 = len(w2.habitants)
    M.forcer_saison(p2, "grippe", 1.0)
    M.introduire(p2, "grippe", 10); M.introduire(p2, "gastro", 10)
    c0 = {x: med2.compteurs.get(("infections", x), 0) for x in ("rhume", "angine")}
    ja0 = M._jour_an(p2)
    saison = {}
    for x in ("rhume", "angine"):
        mx = M.PATHOS[M.IP[x]]
        saison[x] = (1.0 - mx.saison[0] / 2.0) / np.mean([M.facteur_saison(mx, (ja0 + d) % 365) for d in range(60)])
    for _ in range(60):
        for _ in range(C.PAS_PAR_JOUR // 4): w2.pas_suivant()
        incoh_hop += len(M.hopital_incoherent(p2)); incoh_e1 += len(M.incoherences_e1(p2))
        for _ in range(C.PAS_PAR_JOUR - C.PAS_PAR_JOUR // 4): w2.pas_suivant()
    viv = sum(h.vivant for h in w2.habitants)
    inc = {x: (med2.compteurs.get(("infections", x), 0) - c0[x]) / viv * 365.0 / 60.0 * saison[x]
           for x in ("rhume", "angine")}
    gr, ga = _attaque(p2, "grippe", n2), _attaque(p2, "gastro", n2)
    autres_ok = 0.05 <= gr <= 0.50 and 0.05 <= ga <= 0.80 and 1.0 <= inc["rhume"] <= 8.0 and 0.02 <= inc["angine"] <= 0.6
    ok &= autres_ok and incoh_hop == 0 and incoh_e1 == 0 and not M.morts_hors_deceder(p2)
    msgs.append(f"60 jours : grippe {gr:.0%}, gastro {ga:.0%}, rhume {inc['rhume']:.1f} et angine {inc['angine']:.2f} "
                f"par personne et par an ; incoherences hopital {incoh_hop}, etat {incoh_e1}")
    return ok, " ; ".join(msgs)


def test_vaccination():
    """Controle positif : la rougeole ( 3 cas introduits, 60 jours, 500 habitants ) dans le pays vaccine a la
    couverture grecque, contre le meme pays dont les enfants n ont pas ete vaccines. Sans vaccination : au moins
    30 infections ; avec : au plus le quart. Falsificateur : des doses inscrites sans effet ( le statut immun des
    enfants vaccines efface ) donnent au moins la moitie de l epidemie sans vaccination - l inscription seule ne
    protege pas, et cela se voit."""
    res = {}
    for cas in ("vaccine", "sans", "sans_effet"):
        w, p = T.monde(["medecine"], graine=31)
        med = p.domaine("medecine"); n = len(w.habitants)
        k = M.IM["rougeole"]
        age = (p.jour - p.col("habitant", "naissance_j")[:n]) / 365.0
        enfants = np.nonzero(age < 18)[0]
        if cas == "sans": med.doses[enfants, 0] = 0
        if cas in ("sans", "sans_effet"):
            med.statut[enfants, k] = 0
        M.introduire(p, "rougeole", 3)
        T.jours(w, 60)
        res[cas] = (int(med.deja[:n, k].sum()), int(med.doses[:n, 0].astype(bool).sum()))
    v, s, f = res["vaccine"][0], res["sans"][0], res["sans_effet"][0]
    ok = s >= 30 and v <= 0.25 * s and f >= 0.5 * s
    return ok, (f"rougeole en 60 jours : pays vaccine {v} infections ( {res['vaccine'][1]} vaccines ), sans vaccination "
                f"{s}, doses sans effet {f} ( {res['sans_effet'][1]} doses inscrites )")


def test_deceder():
    """Porte : trois lesions insurvivables ( ISS 75 : accident, combat, violence ) tuent sur le coup, par deceder, avec
    leur cause ; en 10 jours, chaque mort causee par ce domaine a sa date et sa cause dans l etat civil, et aucun mort
    n est hors de deceder. Falsificateur : un habitant tue a la main ( vivant = False ) est vu avant la reprise du soir."""
    w, p = T.monde(["medecine"], graine=41)
    med = p.domaine("medecine")
    T.jours(w, 1)
    victimes = [h for h in w.habitants if h.vivant and h.role not in ("enfant",)][:3]
    for h, cause in zip(victimes, ("accident", "combat", "violence")):
        M.blesser(p, h, "balistique" if cause != "accident" else "route", 75, cause=cause)
    T.jours(w, 10)
    col = p.colonnes["habitant"]
    justes = all(col["deces_j"][hid] >= 0 and POP.CAUSES[int(col["cause_deces"][hid])] == c for hid, c in med.tues.items())
    tues3 = all(not h.vivant and med.tues.get(h.id) == c for h, c in zip(victimes, ("accident", "combat", "violence")))
    hors0 = M.morts_hors_deceder(p)
    x = next(h for h in w.habitants if h.vivant)
    x.vivant = False
    vu = x.id in M.morts_hors_deceder(p)
    ok = justes and tues3 and not hors0 and vu
    return ok, (f"{len(med.tues)} morts causees par la medecine, toutes a l etat civil avec leur cause : {justes} ; "
                f"ISS 75 tues sur le coup : {tues3} ; hors deceder {len(hors0)} ; mort a la main vue {vu}")


def test_hopital_e1():
    """Porte : un blesse grave ( ISS 20 ) est a l hopital de sa capitale au pas suivant, un blesse leger ( ISS 4 ) n y
    est pas - avec le deplacement du moteur, puis avec celui de l agenda. Falsificateurs : une gravite ecrite a la main
    dans Habitant ( sans affection ) est vue par incoherences_e1 ; un grave renvoye chez lui a la main est vu par
    hopital_incoherent."""
    msgs, ok = [], True
    for doms in (["medecine"], ["agenda", "medecine"]):
        w, p = T.monde(doms, graine=51)
        T.jours(w, 1)
        for _ in range(3 * 6): w.pas_suivant()          # 9 h
        gens = [h for h in w.habitants if h.vivant and h.role not in ("enfant", "retraite") and h.poste != "hopital"]
        g, l = gens[0], gens[1]
        M.blesser(p, g, "travail", 20); M.blesser(p, l, "chute", 4)
        w.pas_suivant()
        grave_la = g.poste == "hopital" and g.lieu is g.domicile.marche
        leger_pas = l.poste != "hopital"
        for _ in range(6): w.pas_suivant()
        coh = not M.hopital_incoherent(p) and not M.incoherences_e1(p)
        x = next(h for h in w.habitants if h.vivant and h.etat == "S")
        x.gravite = 0.9; x.etat = "I"
        vu1 = ("etat", x.id) in M.incoherences_e1(p)
        x.gravite = 0.0; x.etat = "S"
        g.lieu, g.poste = g.domicile, "maison"
        vu2 = g.id in M.hopital_incoherent(p)
        ok &= grave_la and leger_pas and coh and vu1 and vu2
        msgs.append(f"{'+'.join(doms)} : grave a l hopital {grave_la}, leger dehors {leger_pas}, coherent {coh}, "
                    f"gravite a la main vue {vu1}, grave renvoye vu {vu2}")
    return ok, " ; ".join(msgs)


def test_decisions():
    """Porte des deux decisions, en mode hasard ( 1 000 habitants, 30 jours, rhume, angine et grippe en saison,
    30 angines introduites, 40 pneumonies declenchees ) : au moins 60 decisions de consulter et 30 de prescrire, et
    chacune a une note qui depend du choix ( part du choix >= 0,01 ). Les pneumonies sont ajoutees le 23/09 apres la
    premiere mesure, seuils inchanges : sans elles, 33 et 16 malades bacteriens seulement, trop peu pour lire l effet
    de l antibiotique ( une angine traitee gagne moins d un jour ). Pour que la porte ne passe pas pour une mauvaise
    raison ( le cout de la consultation, la penalite de resistance ), la SANTE seule, sans cout ni penalite, doit aussi
    repondre au choix chez les malades bacteriens : l antibiotique ( ou le test ) fait mieux que rien, consulter fait
    mieux qu attendre."""
    w, p = T.monde(["medecine"], graine=61, echelle=2, modes={"consulter": "hasard", "prescrire": "hasard"})
    for nom in ("rhume", "angine", "grippe"): M.forcer_saison(p, nom, 1.0)
    M.introduire(p, "angine", 30); M.declencher(p, "pneumonie", 40)
    T.jours(w, 30)
    med = p.domaine("medecine")
    dc, dp = med.dec_consulter, med.dec_prescrire
    pc, pp = dc.part_du_choix(), dp.part_du_choix()

    def sante(point, actions):
        v = [e[5] / e[6] for e in med.suivi if e[0] == point and e[2] and e[6] >= M.HORIZON_SOINS and e[1] in actions]
        return (float(np.mean(v)) if v else float("nan")), len(v)
    c1, n_c1 = sante("consulter", (1,)); c0, n_c0 = sante("consulter", (0,))
    a1, n_a1 = sante("prescrire", (1, 2)); a0, n_a0 = sante("prescrire", (0,))
    effet = n_c1 >= 10 and n_c0 >= 10 and n_a1 >= 10 and n_a0 >= 10 and c1 > c0 and a1 > a0
    ok = dc.n_decisions >= 60 and dp.n_decisions >= 30 and pc >= 0.01 and pp >= 0.01 and effet
    nc, npr = dc.notes_par_action(), dp.notes_par_action()
    return ok, (f"consulter : {dc.n_decisions} decisions, part du choix {pc:.3f}, notes "
                + ", ".join(f"{a} {m:.3f} ( {n} )" for a, (n, m) in nc.items())
                + f" ; prescrire : {dp.n_decisions}, part {pp:.3f}, "
                + ", ".join(f"{a} {m:.3f} ( {n} )" for a, (n, m) in npr.items())
                + f" ; sante des bacteriens : consulte {c1:.3f} ( {n_c1} ) contre attend {c0:.3f} ( {n_c0} ), "
                f"antibiotique ou test {a1:.3f} ( {n_a1} ) contre rien {a0:.3f} ( {n_a0} )")


# ================================================================== une annee, sur une population synthetique grecque
AGES_GRECE = ((0, 5, 0.042), (5, 15, 0.100), (15, 25, 0.103), (25, 45, 0.245), (45, 65, 0.285), (65, 75, 0.117),
              (75, 85, 0.076), (85, 100, 0.032))    # ELSTAT, recensement 2021 ( ordre de grandeur )
ENDEMIQUES = ("grippe", "gastro", "rhume", "angine", "rougeole", "tuberculose")


def _annee_synthetique(n, rng, mult_letal=1.0):
    """Un an ( du 1er janvier ) de maladies endemiques sur n Grecs en melange homogene, avec les lois du domaine
    ( q a l exposition de la journee type, saisons, importations, histoires naturelles, letalite avec soins standard,
    pneumonies sporadiques et de complication, tuberculose latente ) : les deces infectieux par tranche d age."""
    bandes = np.array([p for _, _, p in AGES_GRECE]); bandes /= bandes.sum()
    b = rng.choice(len(AGES_GRECE), n, p=bandes)
    age = np.array([rng.uniform(AGES_GRECE[k][0], AGES_GRECE[k][1]) for k in b])
    ch = np.zeros(n, np.int64)
    for bit, tab in M.PREVALENCE_CHRONIQUE.items(): ch |= np.where(rng.random(n) < M.interpole(tab, age), bit, 0)
    rr = M.rr_normalise(ch, age)
    rr_pneu = M.rr_normalise(ch, age, M.RR_PNEUMONIE)
    E = M.EXPOSITION_A_PRIORI
    deces = np.zeros(len(AGES_GRECE))
    infections = {nom: 0 for nom in ENDEMIQUES}
    etat = {}
    for nom in ENDEMIQUES:
        k = M.IM[nom]
        imm = np.zeros(n, bool)
        if nom in M.ENDEMIQUES_AU_DEPART: imm = rng.random(n) < M.regime_permanent(M.PATHOS[M.IP[nom]], 0)[0]
        if nom == "rougeole": imm = rng.random(n) < np.where(age >= 18, M.ADULTES_IMMUNS_ROUGEOLE, 0.95)
        duree = M.PATHOS[M.IP[nom]].immunite_j
        etat[nom] = {"imm_fin": np.where(imm, rng.random(n) * duree if nom != "rougeole" else 1e9, -1.0),
                     "latent": (rng.random(n) < M.par_age(M.TB_LATENTE, age)) if nom == "tuberculose" else np.zeros(n, bool),
                     "inf": np.zeros(n, bool), "h": {}, "qui": np.zeros(0, np.int64)}
    pneu = M.PATHOS[M.IP["pneumonie"]]
    cas_pneu = []
    for d in range(365):
        for nom in ENDEMIQUES:
            m = M.PATHOS[M.IP[nom]]; e = etat[nom]
            nouveaux = []
            if len(e["qui"]):
                h = e["h"]
                f = np.clip(np.minimum(d + 1.0, h["t_fin_cont"]) - np.maximum(float(d), h["t_inf"]), 0, 1)
                Iw = float((f * np.where(h["asym"], m.k_asym, 1.0)).sum())
                lam = M.q_contact(m, E) * E * M.facteur_saison(m, d) * Iw / n
                sus = np.nonzero(~e["inf"] & (e["imm_fin"] < d) & ~e["latent"])[0]
                nouveaux.append(sus[rng.random(len(sus)) < 1.0 - math.exp(-lam)])
            k_imp = rng.poisson(m.import_100k * n / 1e5 * M.facteur_saison(m, d))
            if k_imp:
                c = rng.integers(0, n, k_imp)
                nouveaux.append(c[~e["inf"][c] & (e["imm_fin"][c] < d)])
            if nom == "tuberculose":
                lat = np.nonzero(e["latent"])[0]
                r = lat[rng.random(len(lat)) < M.REACTIVATION_TB_AN / 365.0]
                e["latent"][r] = False; nouveaux.append(r)
            new = np.unique(np.concatenate(nouveaux)) if nouveaux else np.zeros(0, np.int64)
            if nom == "tuberculose" and len(new):
                prog = rng.random(len(new)) < m.progression
                e["latent"][new[~prog]] = True; new = new[prog]
            if len(new):
                infections[nom] += len(new)
                h = M.tirer_histoires(m, float(d), age[new], rng, rr[new] if m.rr_chronique else None)
                e["inf"][new] = True
                e["h"] = {c: np.concatenate([e["h"][c], h[c]]) if e["h"] else h[c] for c in h}
                e["qui"] = np.concatenate([e["qui"], new])
                c = M.COMPLICATION_PNEUMONIE.get(nom)
                if c: cas_pneu.append(new[~h["asym"] & (h["u2"] < c)])
            # fins : deces ( soins standard : soutien et traitement specifique ) ou guerison
            if len(e["qui"]):
                h = e["h"]
                fin = h["t_fin"] < d + 1.0
                if fin.any():
                    letal = np.where(h["grave"] | m.letal_legers, h["letal"], 0.0) * mult_letal
                    mort = fin & ~h["asym"] & (h["u_issue"] < letal)
                    np.add.at(deces, b[e["qui"][mort]], 1)
                    q = e["qui"][fin]
                    e["inf"][q] = False
                    e["imm_fin"][q] = d + (m.immunite_j if m.immunite_j > 0 else -1.0)
                    garde = ~fin
                    e["h"] = {c: v[garde] for c, v in h.items()}; e["qui"] = e["qui"][garde]
        # pneumonies sporadiques ( BPCO x3, diabete x1,5, cardiopathie x2, rapportes a l age ) et de complication
        spor = np.nonzero(rng.random(n) < M.par_age(pneu.incidence, age) / 365.0 * rr_pneu)[0]
        cas = np.concatenate([spor] + cas_pneu) if cas_pneu else spor
        cas_pneu = []
        if len(cas):
            h = M.tirer_histoires(pneu, float(d), age[cas], rng, rr[cas])
            mort = h["grave"] & (h["u_issue"] < h["letal"] * mult_letal)
            np.add.at(deces, b[cas[mort]], 1)
    return deces, np.bincount(b, minlength=len(AGES_GRECE)), infections


def _externes(age):
    """Morts externes attendues par an a chaque age, avec les lois du domaine : route, travail ( 55 % d actifs de 18 a
    64 ans, au taux moyen ), suicide des deprimes."""
    def attendu(dist, a):
        v = 0.0
        for (lo, hi), pr in dist:
            v += pr * float(np.mean(M.letalite_iss(np.arange(lo, hi + 1), a)))
        return v
    route = np.where(age >= 5, M.ROUTE_VICTIMES_100K_AN / 1e5, 0.0) * np.array([attendu(M.ISS_ROUTE, a) for a in age])
    taux_travail = np.mean(list(M.ACCIDENTS_TRAVAIL.values())) / 1e5
    travail = (np.where((age >= 18) & (age < 65), 0.55 * taux_travail, 0.0)
               * np.array([attendu(M.ISS_TRAVAIL, a) for a in age]))
    suicide = np.where(age >= 15, M.PREVALENCE_DEPRESSION * M.SUICIDE_AN_DEPRIME * 1.3, 0.0)
    return route + travail + suicide


def test_annee():
    """Porte : un an de maladies endemiques ( grippe, gastro, rhume, angine, rougeole vaccinee, tuberculose, pneumonies )
    sur 40 000 Grecs de synthese. La mortalite infectieuse est de 20 a 150 pour 100 000 ( Grece : grippe, pneumonies et
    maladies infectieuses, ~70 pour 100 000 ) et l esperance de vie de la table naturelle NETTE du domaine 1, completee
    des morts infectieuses et externes de ce domaine, reste de 79,5 a 83,5 ans ( Grece 2019 : 81,7 ). Controle positif :
    une letalite triplee donne 2,2 a 3,8 fois plus de morts infectieuses. Ajout du 23/09 ( memes seuils que la porte du
    moteur ) : rhume de 1 a 8 episodes et angine de 0,02 a 0,6 par personne et par an."""
    rng = np.random.default_rng(3)
    n = 40000
    deces, effectifs, infections = _annee_synthetique(n, rng)
    d3, _, _ = _annee_synthetique(n, np.random.default_rng(3), mult_letal=3.0)
    rhume, angine = infections["rhume"] / n, infections["angine"] / n
    taux = deces / np.maximum(1, effectifs)
    inf_100k = deces.sum() / n * 1e5
    ages = np.arange(POP.AGE_MAX)
    bande = np.searchsorted([lo for lo, _, _ in AGES_GRECE], ages, side="right") - 1
    m_inf = taux[bande]
    m_ext = _externes(ages.astype(float))
    e0 = []
    for sexe in (POP.HOMME, POP.FEMME):
        t = POP.TableDeMortalite()
        t.q[:, :POP.AGE_MAX] *= (1.0 - M.par_age(M.PART_CAUSES_MODELISEES, ages))
        q = t.q[sexe, :POP.AGE_MAX]
        t.q[sexe, :POP.AGE_MAX] = 1.0 - (1.0 - q) * (1.0 - m_inf) * (1.0 - m_ext)
        e0.append(t.esperance_de_vie(sexe))
    e = float(np.mean(e0))
    ratio = d3.sum() / max(1, deces.sum())
    ok = (20 <= inf_100k <= 150 and 79.5 <= e <= 83.5 and 2.2 <= ratio <= 3.8 and 1.0 <= rhume <= 8.0
          and 0.02 <= angine <= 0.6)
    return ok, (f"{int(deces.sum())} morts infectieuses pour {n} habitants en un an ( {inf_100k:.0f} pour 100 000 ; "
                f"par tranche : " + ", ".join(f"{lo}+ {1e5 * v:.0f}" for (lo, _, _), v in zip(AGES_GRECE, taux))
                + f" ) ; externes a 40 ans {1e5 * m_ext[40]:.1f} pour 100 000 ; esperance de vie hommes {e0[0]:.1f}, "
                f"femmes {e0[1]:.1f} ; letalite triplee : x{ratio:.2f} ; rhume {rhume:.2f} et angine {angine:.3f} par "
                f"personne et par an ; grippe {infections['grippe'] / n:.0%}, gastro {infections['gastro'] / n:.2f} "
                f"par personne")


# ================================================================== pharmacies, conservation, cout
def test_pharmacie():
    """Porte : 20 jours - la somme des lots de chaque pharmacie egale son stock, les commandes de l Etat arrivent
    ( importations payees ), un lot perime sort par le grand livre ( perime ), la conservation tient. Controle positif :
    l insuline d une pharmacie videe, ses diabetiques insulinodependants passent des jours sans traitement. Falsificateur :
    trois doses posees a la main dans un stock sont vues par la conservation et par les lots."""
    w, p = T.monde(["medecine"], graine=71)
    med = p.domaine("medecine"); L = p.socle.livre
    ph = med.pharmacies[0]
    b = med.id_mol["vaccin_grippe"]
    M._entrer(p, med, ph, "vaccin_grippe", 5.0, "importe", "essai")
    ph.lots[b][-1][1] = p.jour + 2
    perime0 = L.flux["perime"].get("vaccin_grippe", 0.0)
    T.jours(w, 4)
    perime = L.flux["perime"].get("vaccin_grippe", 0.0) - perime0
    bi = med.id_mol["insuline"]
    M.prendre(p, ph, "insuline", ph.stock[bi], "essai")
    med.chaine_externe = True                             # plus de commande : la rupture dure
    n = len(w.habitants)
    ch = p.col("habitant", "med_chroniques")[:n]
    ins = [h.id for h in w.habitants if h.vivant and ch[h.id] & M.INSULINE and med.region_de_lieu[h.domicile.marche.id] == 0]
    T.jours(w, 2)
    sj = p.col("habitant", "med_sans_traitement_j")
    rupture = bool(ins) and all(sj[i] >= 1 or not w.habitants[i].vivant for i in ins)
    med.chaine_externe = False
    T.jours(w, 14)
    lots = M.ecarts_lots(p)
    tenue, msg = p.socle.conservation.tenue()
    commandes = med.compteurs.get("commandes", 0)
    ph.stock._ajouter(b, 3.0)
    vu_c = not p.socle.conservation.tenue()[0]
    vu_l = bool(M.ecarts_lots(p))
    ok = not lots and abs(perime - 5.0) < 1e-9 and tenue and rupture and commandes > 0 and vu_c and vu_l
    return ok, (f"lots = stocks : {not lots} ; perime {perime:.1f} / 5 ; {commandes} commandes livrees ; {msg} ; rupture "
                f"d insuline vue chez {len(ins)} diabetiques : {rupture} ; doses a la main vues ( conservation {vu_c}, "
                f"lots {vu_l} )")


def test_pays_vivable():
    return T.porte_commune("medecine", n_jours=12)


def test_cout():
    """Le domaine coute au plus 35 % d une journee du moteur ( avec population et territoire ), a 10 000 habitants,
    rhume endemique et grippe du moteur compris : il remplace la contagion du moteur, qui parcourait deja la
    population chaque heure."""
    def jour_moyen(doms):
        w = W.Monde(echelle=20)
        T.P.installer(w, doms)
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants), w
    t_base, n, _ = jour_moyen(["population", "territoire"])
    t_med, _, w = jour_moyen(["medecine"])
    med = w.pays.domaine("medecine")
    ok = t_med <= 1.35 * t_base
    return ok, (f"{n} habitants : population et territoire {t_base:.2f} s par jour, avec la medecine {t_med:.2f} s "
                f"( {t_med / t_base - 1:+.0%} ) ; {med.aff.n_actives()} affections en cours")


TESTS = [test_r0_et_durees, test_diagnostic, test_resistance, test_epidemies_moteur, test_vaccination, test_deceder,
         test_hopital_e1, test_decisions, test_annee, test_pharmacie, test_pays_vivable, test_cout]
