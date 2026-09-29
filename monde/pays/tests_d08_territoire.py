"""Les portes du domaine 8 ( territoire ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests territoire"""
import math, time
import numpy as np
from .. import monde as W
from . import essais as T, d08_territoire as M

ILES = ("Altis", "Malden", "Stratis", "Tanoa", "Enoch", "Sara")


# ================================================================== le climat, sur le generateur seul
def _mensuel(serie, R, ans, f):
    x = serie.reshape(R, ans, M.JOURS_AN)
    return np.array([f(x[:, :, M.DEBUT_MOIS[m]:M.DEBUT_MOIS[m] + M.MOIS_J[m]]) for m in range(12)])


def _trimestres(v): return np.array([v[m] + v[(m + 1) % 12] + v[(m + 2) % 12] for m in range(12)])


def _saison_ok(sim, prof):
    """Le critere ecrit avant la mesure : le trimestre le plus pluvieux simule tombe a un mois pres de celui du profil.
    Constat du 23/09, APRES la mesure ( le critere n est pas change ) : a Sahrani, les deux meilleurs trimestres du
    profil ( juillet-septembre 478 mm, septembre-novembre 484 mm ) sont a 1,3 % l un de l autre, sous l erreur
    d echantillonnage de ~3 % ; ce critere y passe ou echoue selon la graine ( 1 graine sur 4 ). A trancher par Claude
    principal : la correlation des trimestres glissants est rapportee a cote, sans entrer dans la porte."""
    a, b = int(np.argmax(_trimestres(sim))), int(np.argmax(_trimestres(prof)))
    return min((a - b) % 12, (b - a) % 12) <= 1


def _phase(sim, prof):
    """Diagnostic, hors porte : correlation des 12 sommes glissantes de trois mois, simulees et du profil."""
    return float(np.corrcoef(_trimestres(sim), _trimestres(prof))[0, 1])


def _nrmse(sim, prof): return float(np.sqrt(np.mean((sim - prof) ** 2)) / np.mean(prof))


def test_climat():
    """Porte : 20 tirages de 5 ans par ile ( 100 annees-station ) retrouvent chaque profil - pluie annuelle a 10 % pres,
    pluie mensuelle a 15 % pres en ecart quadratique ( rapporte a la moyenne mensuelle ), les trois mois les plus
    pluvieux au bon endroit ( a un mois pres ), temperature de chaque mois a 1 degre pres, jours de pluie par an a 15 %
    pres, variabilite d une annee a l autre realiste ( coefficient de variation de 0,12 a 0,40 ). Altis : persistance de
    la pluie ( correlation d un jour au suivant de 0,15 a 0,55, novembre-mars ), des anomalies de temperature ( 0,55 a
    0,90 ), pluie journaliere maximale de l annee de 30 a 80 mm en mediane. Livonie : neige au sol 60 a 140 jours par an,
    bilan du manteau exact. Controle positif : janvier deux fois plus pluvieux donne 1,7 a 2,3 fois plus de pluie en
    janvier. Falsificateur : un profil decale de six mois est reconnu faux."""
    R, ANS = 20, 5
    D = ANS * M.JOURS_AN
    double = M.PROFILS["Altis"].decale(0); double.pluie = double.pluie.copy(); double.pluie[0] *= 2
    profils = [M.PROFILS[i] for i in ILES for _ in range(R)] + [double] * R + [M.PROFILS["Altis"].decale(6)] * R
    sim = M.simuler(profils, D, np.random.default_rng(8))
    res, ok, msgs = {}, True, []
    for k, ile in enumerate(ILES + ("double", "decale")):
        s = slice(k * R, (k + 1) * R)
        pr = M.PROFILS["Altis" if k >= len(ILES) else ile]
        pl, tm = sim["pluie"][s], sim["tmoy"][s]
        annuel = pl.reshape(R, ANS, M.JOURS_AN).sum(2)
        mens = _mensuel(pl, R, ANS, lambda x: x.sum(2).mean())
        tmens = _mensuel(tm, R, ANS, lambda x: x.mean())
        res[ile] = dict(an=annuel.mean() / pr.pluie.sum(), nrmse=_nrmse(mens, pr.pluie), saison=_saison_ok(mens, pr.pluie),
                        phase=_phase(mens, pr.pluie),
                        dt=float(np.abs(tmens - (pr.tmax + pr.tmin) / 2).max()),
                        jours=(pl >= M.SEUIL_PLUIE).sum(1).mean() / ANS / pr.jours_pluie.sum(),
                        cv=float(annuel.std() / annuel.mean()), mens=mens)
        if k < len(ILES):
            r = res[ile]
            bon = (abs(r["an"] - 1) <= 0.10 and r["nrmse"] <= 0.15 and r["saison"] and r["dt"] <= 1.0
                   and abs(r["jours"] - 1) <= 0.15 and 0.12 <= r["cv"] <= 0.40)
            ok &= bon
            msgs.append(f"{ile}{'' if bon else ' ECHEC'} an x{r['an']:.3f} mois {r['nrmse']:.3f} trimestre "
                        f"{'juste' if r['saison'] else 'DECALE'} ( phase {r['phase']:.2f} ) T {r['dt']:.2f} C "
                        f"jours x{r['jours']:.2f} CV {r['cv']:.2f}")
    # Altis : persistance et extremes
    s = slice(0, R); pl = sim["pluie"][s]; tm = sim["tmoy"][s]
    o = (pl >= M.SEUIL_PLUIE).astype(float)
    doy = np.arange(D) % M.JOURS_AN
    hiver = (doy < M.DEBUT_MOIS[3]) | (doy >= M.DEBUT_MOIS[10])
    paire = hiver[:-1] & hiver[1:]
    r_occ = float(np.corrcoef(o[:, :-1][:, paire].ravel(), o[:, 1:][:, paire].ravel())[0, 1])
    tab = M.TableClimat([M.PROFILS["Altis"]])
    a = tm - tab.tmoy[0, doy]
    r_t = float(np.corrcoef(a[:, :-1].ravel(), a[:, 1:].ravel())[0, 1])
    pmax = float(np.median(pl.reshape(R, ANS, M.JOURS_AN).max(2)))
    alt = 0.15 <= r_occ <= 0.55 and 0.55 <= r_t <= 0.90 and 30 <= pmax <= 80
    # Livonie : la neige
    s = slice(ILES.index("Enoch") * R, (ILES.index("Enoch") + 1) * R)
    neige_j = float((sim["neige_sol"][s] > 1.0).sum(1).mean() / ANS)
    ecart_neige = float(np.abs(sim["neige_tombee"][s].sum(1) - sim["fonte"][s].sum(1) - sim["neige_sol"][s][:, -1]).max())
    liv = 60 <= neige_j <= 140 and ecart_neige <= 1e-9
    # controles
    jan = res["double"]["mens"][0] / res["Altis"]["mens"][0]
    positif = 1.7 <= jan <= 2.3
    f = res["decale"]
    vu = f["nrmse"] > 0.15 or not f["saison"]
    ok = ok and alt and liv and positif and vu
    return ok, ("; ".join(msgs) + f" ; Altis : persistance pluie {r_occ:.2f}, temperature {r_t:.2f}, max journalier median "
                f"{pmax:.0f} mm ; Livonie : neige au sol {neige_j:.0f} j/an, bilan du manteau {ecart_neige:.1e} mm ; "
                f"janvier double : x{jan:.2f} ; profil decale : ecart mensuel {f['nrmse']:.2f}, trimestre "
                f"{'juste' if f['saison'] else 'decale'} -> vu {vu}")


# ================================================================== l eau, dans le monde
def test_bilan_eau():
    """Porte : les six iles, 60 jours, avec des prelevements et des rejets d un domaine tiers : le bilan de l eau brute
    de chaque bassin ferme a 1 litre pres ( stock - depart = recharge + captage - evaporation - exutoire - debordements
    - prelevements + forcages ), les bilans des sols et de la neige au millionieme de mm, aucun stock negatif, et chaque
    flux a vraiment coule ( sinon le bilan fermerait pour rien ). Falsificateurs : 1 000 m3 retires d une nappe a la
    main, 250 m3 ajoutes a une retenue a la main - les deux se voient, au m3."""
    w, p = T.monde(["territoire"], iles=ILES)
    Tt = p.domaine("territoire"); B = Tt.bassins
    livre = 0.0
    for _ in range(60):
        T.jours(w, 1)
        livre += M.prelever(p, "Kavala", 50.0, "industrie")
        M.rejeter(p, "Kavala", "plomb", 0.01)
    e = M.bilan_eau(p)
    pire = float(np.abs(e).max())
    par_ile = [abs(float(e[B.ile == i].sum())) for i in range(len(ILES))]
    flux = dict(recharge=B.c_in_n.sum(), captage=B.c_in_r.sum(), evaporation=B.c_evap.sum(), exutoire=B.c_exut.sum(),
                prelevements=B.c_prel.sum())
    coule = all(v > 0 for v in flux.values()) and livre > 0
    sols = M.bilan_sols(p)
    positifs = bool((B.nappe >= 0).all() and (B.retenue >= 0).all())
    tenue, msg = p.socle.conservation.tenue()
    b1, b2 = 0, len(B.nom) - 1
    B.nappe[b1] -= 1000.0; vu1 = abs(float(M.bilan_eau(p)[b1]) + 1000.0) <= 1e-3; B.nappe[b1] += 1000.0
    B.retenue[b2] += 250.0; vu2 = abs(float(M.bilan_eau(p)[b2]) - 250.0) <= 1e-3; B.retenue[b2] -= 250.0
    ok = pire <= 1e-3 and max(par_ile) <= 1e-3 * len(B.nom) and coule and sols <= 1e-6 and positifs and tenue and vu1 and vu2
    pen = int(B.jours_penurie.sum())
    return ok, (f"{len(B.nom)} bassins, stock {float((B.nappe + B.retenue).sum()):.3e} m3 ; pire ecart {pire:.1e} m3 "
                f"( ile {max(par_ile):.1e} ) ; flux " + ", ".join(f"{k} {v:.2e}" for k, v in flux.items())
                + f" ; sols et neige {sols:.1e} mm ; {pen} jours-bassins de penurie ; {Tt.n_seismes} seismes, {Tt.n_crues} crues, "
                f"{Tt.n_alertes} alertes incendie ; {msg} ; nappe videe a la main vue {vu1}, retenue gonflee vue {vu2}")


# ================================================================== la secheresse et les fermes du moteur
def _pleine_activite(p):
    """Routine d essai : toutes les fermes a pleine activite, pour que la production mesure le RENDEMENT et non la
    regulation des marches ( une ferme dont le marche deborde ralentit, une ferme dont le marche manque accelere )."""
    for e in p.w.entreprises.values():
        if e.type == "ferme": e.activite = 1.0


def _fermes(secheresse=False, choc=None, pont=True):
    w, p = T.monde(["territoire"])
    p.routine(6 + 10 / 60, 1, "essai", _pleine_activite)
    p.domaine("territoire").pont_e1 = pont
    villages = [e.lieu for e in w.entreprises.values() if e.type == "ferme"]
    if secheresse: M.imposer_secheresse(p, "Altis", 45)
    if choc is not None: w.chocs.append({"debut": 0, "jours": 100, "lieux": [l.id for l in villages], "facteur": choc})
    prod = lambda: sum(e.produit_du_jour["nourriture"] for e in w.entreprises.values() if e.type == "ferme")
    T.jours(w, 10); a = prod(); f = []
    for _ in range(30):
        T.jours(w, 1); f.append(np.mean([w.facteur_choc(l) for l in villages]))
    return prod() - a, float(np.mean(f))


def test_secheresse_fermes():
    """Porte : Altis, fermes a pleine activite, production des jours 10 a 40. Une secheresse du territoire ( hiver sec
    derriere elle, 45 jours sans pluie et +3 degres ) fait produire au plus 85 % du monde normal. Le monde normal a un
    rendement climatique moyen de 0,90 a 1,10. Controle positif : un choc pose a la main a 0,5 donne 45 a 55 %.
    Controle negatif : sans le pont, la meme secheresse ne change pas UNE unite de production ( le monde E1 ne voit le
    territoire que par w.chocs )."""
    n, fn = _fermes()
    s, fs = _fermes(secheresse=True)
    c, _ = _fermes(choc=0.5)
    s0, _ = _fermes(secheresse=True, pont=False)
    n0, _ = _fermes(pont=False)
    rs, rc = s / n, c / n
    ok = rs <= 0.85 and 0.45 <= rc <= 0.55 and 0.90 <= fn <= 1.10 and abs(s0 - n0) <= 1e-9 * n0
    return ok, (f"production normale {n:.0f} ( rendement climatique moyen {fn:.3f} ) ; secheresse {s:.0f} = {rs:.1%} "
                f"( rendement {fs:.3f} ) ; choc 0,5 a la main {rc:.1%} ; sans pont : secheresse {s0:.0f} contre normal {n0:.0f}")


# ================================================================== les seismes
def _aki(m): return math.log10(math.e) / (float(np.mean(m)) - M.M_MIN)


def _ks(m, b, m_max):
    x = np.sort(np.asarray(m)); n = len(x)
    F = (1 - 10 ** (-b * (x - M.M_MIN))) / (1 - 10 ** (-b * (m_max - M.M_MIN)))
    i = np.arange(1, n + 1)
    return float(max((i / n - F).max(), (F - (i - 1) / n).max()))


def test_gutenberg_richter():
    """Porte : 200 ans de sismicite d Altis par la fonction du monde ( fond et repliques ). La pente b estimee ( Aki
    1965 ) tombe a 3 ecarts-types de 0,95 ; le nombre de seismes de fond a 3 ecarts-types du taux de Poisson ; la part
    des M >= 5 et des M >= 6 a 3 ecarts-types de la loi ; le test de Kolmogorov-Smirnov accepte la loi au seuil de
    1 % ; des repliques existent. Controle positif : une region de b = 1,3 est mesuree a 1,3. Falsificateur : des
    magnitudes uniformes sont rejetees par le meme test."""
    s = M.SISMICITE["Altis"]; ans = 200
    cat = M.catalogue(s, ans * M.JOURS_AN, np.random.default_rng(3))
    m = np.array([c[1] for c in cat]); fond = sum(1 for c in cat if not c[5]); n = len(m)
    b = _aki(m); sb = b / math.sqrt(n)
    attendu = s.n4_an * ans
    def part(seuil):
        q = (10 ** (-s.b * (seuil - M.M_MIN)) - 10 ** (-s.b * (s.m_max - M.M_MIN))) / (1 - 10 ** (-s.b * (s.m_max - M.M_MIN)))
        obs = float((m >= seuil).mean())
        return obs, q, abs(obs - q) <= 3 * math.sqrt(q * (1 - q) / n)
    p5, p6 = part(5.0), part(6.0)
    ks = _ks(m, s.b, s.m_max); crit = 1.63 / math.sqrt(n)
    s13 = M.Sismicite(s.n4_an, 1.3, s.m_max, s.rayon_km)
    m13 = np.array([c[1] for c in M.catalogue(s13, ans * M.JOURS_AN, np.random.default_rng(4))])
    b13 = _aki(m13)
    uni = np.random.default_rng(5).uniform(M.M_MIN, s.m_max, n)
    ks_uni = _ks(uni, s.b, s.m_max)
    ok = (abs(b - s.b) <= 3 * sb and abs(fond - attendu) <= 3 * math.sqrt(attendu) and p5[2] and p6[2] and ks <= crit
          and n > fond and abs(b13 - 1.3) <= 3 * b13 / math.sqrt(len(m13)) and ks_uni > crit)
    return ok, (f"{n} seismes en {ans} ans dont {fond} de fond ( attendu {attendu:.0f} ) et {n - fond} repliques ; b = {b:.3f} "
                f"+/- {sb:.3f} ( loi 0,95 ) ; M>=5 {p5[0]:.4f} ( loi {p5[1]:.4f} ), M>=6 {p6[0]:.5f} ( loi {p6[1]:.5f} ) ; "
                f"KS {ks:.4f} ( seuil {crit:.4f} ) ; M>=6,8 : {int((m >= 6.8).sum())} ; controle b = 1,3 -> {b13:.3f} ; "
                f"magnitudes uniformes : KS {ks_uni:.3f}, rejetees {ks_uni > crit}")


# ================================================================== la pollution
def test_pollution():
    """Porte : Altis, 30 jours. 100 kg d hydrocarbures dans le sol d un village : il en reste 100 x 0,5^(30/180) au
    milliardieme pres ( demi-vie de 180 jours ). 10 kg de plomb dans l eau de Kavala : le plomb ne se degrade pas, l eau
    qui sort l emporte, et le bilan des polluants ferme au microgramme. Les sites du moteur E1 polluent l air de la
    centrale au-dessus du fond, pas celui d un village. Controle positif : la meme emission par vent de 2 m/s donne une
    concentration 4 fois plus forte que par 8 m/s. Falsificateur : 5 kg poses a la main dans un sol se voient."""
    w, p = T.monde(["territoire"])
    Tt = p.domaine("territoire"); Po = Tt.pollution
    village = next(l for l in Tt.parcelles.lieu_id if not any(e.lieu.id == l and e.type != "ferme" for e in w.entreprises.values()))
    kv = Tt.index_lieu[village]; x = M.SOL.index("hydrocarbures_sol")
    M.rejeter(p, village, "hydrocarbures_sol", 100.0)
    M.rejeter(p, "Kavala", "plomb", 10.0)
    T.jours(w, 30)
    reste = float(Po.sol[kv, x]); attendu = 100.0 * 0.5 ** (30 / 180)
    bil = M.bilan_pollution(p); pire = max(abs(v) for v in bil.values())
    emporte = Po.c_evacue["plomb"]
    centrale = next(e.lieu for e in w.entreprises.values() if e.type == "centrale")
    so2_c = M.concentration(p, centrale, "so2"); so2_v = M.concentration(p, village, "so2")
    fond = M.POLLUANT["so2"].fond
    calme = float(M.concentration_air(10.0, 2.0, 1000.0) / M.concentration_air(10.0, 8.0, 1000.0))
    Po.sol[kv, x] += 5.0
    vu = abs(M.bilan_pollution(p)["hydrocarbures_sol"] - 5.0) <= 1e-9
    Po.sol[kv, x] -= 5.0
    indices = M.pollution(p, centrale)
    ok = (abs(reste / attendu - 1) <= 1e-9 and pire <= 1e-9 and emporte > 0 and so2_c > fond and abs(so2_v - fond) <= 1e-12
          and abs(calme - 4.0) <= 1e-12 and vu)
    return ok, (f"sol : {reste:.4f} kg pour {attendu:.4f} attendus ; plomb emporte par l eau {emporte * 1000:.1f} g ; bilan des "
                f"polluants {pire:.1e} kg ; SO2 a la centrale {so2_c:.3f} ug/m3, au village {so2_v:.3f} ( fond {fond} ) ; indices "
                f"de la centrale air {indices[0]:.3f} eau {indices[1]:.3f} sol {indices[2]:.3f} ; vent calme x{calme:.2f} ; "
                f"5 kg a la main vus {vu}")


# ================================================================== la decision
def _eau(mode):
    w, p = T.monde(["territoire"], modes={"gerer_eau": mode})
    M.forcer_reserves(p, 0.05, "Altis")
    M.forcer_meteo(p, "Altis", 70, pluie=0.2, chaleur_c=1.5)
    T.jours(w, 70)
    return w, p


def test_gerer_eau():
    """Porte de la decision : Altis, reserves a 5 % de l exploitable et 70 jours sees ( pluie x0,2, +1,5 degre ). Le
    scenario manque vraiment d eau : sans restriction ( temoin ), au moins 10 % des jours-bassins sont en penurie. En
    mode hasard, au moins 100 decisions, au moins 100 notes rendues, et la note depend du choix ( part du choix
    >= 0,01 ) ; la conservation du socle tient. La regle, le temoin et le hasard sont compares ( sans seuil )."""
    res = {}
    for mode in ("hasard", "regle", "temoin"):
        w, p = _eau(mode)
        Tt = p.domaine("territoire"); dec = Tt.decideur; B = Tt.bassins
        notes = dec.notes_par_action()
        n_notes = sum(k for k, _ in notes.values())
        moy = sum(k * v for k, v in notes.values()) / max(1, n_notes)
        res[mode] = dict(part=dec.part_du_choix(), n=dec.n_decisions, notes=notes, n_notes=n_notes, moy=moy,
                         pen=float(B.jours_penurie.sum()) / (len(B.nom) * 70), tenue=p.socle.conservation.tenue())
    h, t = res["hasard"], res["temoin"]
    ok = t["pen"] >= 0.10 and h["n"] >= 100 and h["n_notes"] >= 100 and h["part"] >= 0.01 and h["tenue"][0]
    return ok, (f"{h['n']} decisions en hasard, {h['n_notes']} notes : "
                + ", ".join(f"{a} {m:.3f} ( {k} )" for a, (k, m) in h["notes"].items())
                + f" ; part du choix {h['part']:.3f} ; jours-bassins en penurie : hasard {h['pen']:.1%}, regle "
                f"{res['regle']['pen']:.1%}, temoin {t['pen']:.1%} ; note moyenne : hasard {h['moy']:.3f}, regle "
                f"{res['regle']['moy']:.3f}, temoin {t['moy']:.3f} ; {h['tenue'][1]}")


# ================================================================== le pays
def test_pays_vivable():
    return T.porte_commune("territoire", n_jours=12)


def test_cout():
    """Le domaine coute au plus 10 % d une journee du moteur a 10 000 habitants ( ses routines propres au plus 5 % ) ;
    l installation des six iles ( 192 annees de climat pour les normales ) en moins de 5 s."""
    def jour_moyen(avec):
        w = W.Monde(echelle=20)
        if avec: T.P.installer(w, ["territoire"])
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants)
    t_e1, n = jour_moyen(False)
    t_ter, _ = jour_moyen(True)
    w, p = T.monde(["territoire"], echelle=20); T.jours(w, 3)
    Tt = p.domaine("territoire")
    t0 = time.perf_counter()
    for _ in range(3):
        Tt.jour_fait = None; M._minuit(p); M._cloture(p, None)
    propre = (time.perf_counter() - t0) / 3
    t0 = time.perf_counter(); T.monde(["territoire"], iles=ILES); t_inst = time.perf_counter() - t0
    ok = t_ter <= 1.10 * t_e1 and propre <= 0.05 * t_e1 and t_inst <= 5.0
    return ok, (f"{n} habitants : moteur seul {t_e1:.2f} s par jour, avec le territoire {t_ter:.2f} s ( {t_ter / t_e1 - 1:+.1%} ) ; "
                f"routines propres {propre * 1000:.1f} ms par jour ; installation des six iles {t_inst:.2f} s")


# ================================================================== provoquer ( HMT-146 )
def _evts(p, type_, **k):
    return [e for e in p.socle.journal.recents if e["type"] == type_ and all(e.get(a) == b for a, b in k.items())]


def _releve(w, p, i):
    """Ce que la porte lit d un jour : le temps de l ile, ses reserves ( part de l exploitable ), son bulletin, les
    parcelles, les catastrophes nees aujourd hui."""
    Tt = p.domaine("territoire"); B, P, m = Tt.bassins, Tt.parcelles, Tt.meteo
    sb = B.ile == i
    num = float((B.nappe - B.min_n + B.retenue - B.min_r)[sb].sum()); den = float((B.cap_n - B.min_n + B.cap_r - B.min_r)[sb].sum())
    return {"jour": w.jour, "tmax": float(m.tmax[i]), "pluie": float(m.pluie[i]), "reserves": num / den,
            "secheresse": bool(Tt.en_secheresse[i]), "facteur": P.inond_facteur.copy(), "fin": P.inond_fin.copy(),
            "cat": [(c.type, c.lieu, c.gravite, c.valeur, dict(c.intensites or {})) for c in Tt.catastrophes if c.debut_j == w.jour]}


def _vivre(w, p, n, i=0):
    out = []
    for _ in range(n): T.jours(w, 1); out.append(_releve(w, p, i))
    return out


def test_provoquer():
    """Porte ( HMT-146, seuils ecrits avant le code, Plane ). Des mondes jumeaux ( Altis, graine 146 ) : l un provoque,
    l autre non. Controles positifs. Un seisme M 6,5 sous un village, ordonne au jour 0, ne tombe qu au minuit du jour 1 ;
    ses intensites sont celles de la loi du domaine recalculees ici ( Bakun et Wentworth, distance au village ) pour tous
    les lieux de l ile ; l evenement porte le numero de la provocation ; sa sequence de repliques est ouverte. Une crue
    de gravite 2 au jour 2 : la catastrophe, les parcelles de SON bassin a 0,5 jusqu au jour 9, les autres identiques au
    jumeau. Un seisme ordonne pour le jour 6 ne fait rien avant. Une secheresse de 60 jours : reserves de l ile a 10 % au
    plus de l exploitable le jour d effet, aucune pluie sur l ile 10 jours, bulletin de secheresse. Une canicule de +8 C
    sur 10 jours : tmax moyenne de la fenetre au moins 6 C au-dessus du jumeau. Chaque ordre est au journal. Falsificateurs :
    ValueError, sans rien noter ni mettre en file, pour une nature inconnue, une magnitude au-dessus du m_max de l ile, une
    gravite 4, un lieu d une autre ile, un jour passe, une ile inconnue, un parametre inconnu ; le jumeau n a ni file ni
    evenement provoque. Reprise : un instantane sans file se relit et se provoque ; une provocation en attente survit a
    l instantane ( meme monde au bit : l empreinte de la porte des domaines )."""
    import pickle
    from ..porte_domaines import empreinte
    monde = lambda: T.monde(["territoire"], graine=146)
    w0, p0 = monde()
    T0 = p0.domaine("territoire"); i = T0.iles.index("Altis")
    vil = sorted(lid for lid, k in zip(T0.parcelles.lieu_id, T0.parcelles.ile.tolist()) if k == i)
    v0 = vil[0]; b1 = int(T0.lieu_bassin[T0.index_lieu[vil[-1]]])
    jumeau = _vivre(w0, p0, 10)
    # ---- seisme, crue, echeance
    w1, p1 = monde(); T1 = p1.domaine("territoire")
    r1 = M.provoquer(p1, "seisme", "Altis", magnitude=6.5, lieu=v0, par="porte")
    r2 = M.provoquer(p1, "inondation", "Altis", jour=2, lieu=vil[-1], gravite=2, par="porte")
    r3 = M.provoquer(p1, "seisme", "Altis", jour=6, magnitude=5.0, lieu=v0, par="porte")
    attente = len(M.provocations_en_attente(p1)) == 3 and not any(c.debut_j == w1.jour for c in T1.catastrophes if c.valeur == 6.5)
    a = _vivre(w1, p1, 7)
    ev1 = _evts(p1, "seisme", provoque=r1["numero"])
    sis = [c for c in a[0]["cat"] if c[0] == "seisme" and c[3] == 6.5]
    sel = np.nonzero(T1.lieu_ile == i)[0]; k0 = T1.index_lieu[v0]
    d = np.hypot(T1.lieu_pos[sel, 0] - T1.lieu_pos[k0, 0], T1.lieu_pos[sel, 1] - T1.lieu_pos[k0, 1]) / 1000
    s = M.SISMICITE["Altis"]; h = 0.5 * (s.profondeur_km[0] + s.profondeur_km[1])
    mmi = M.intensite(6.5, np.hypot(d, h))
    loi = {T1.lieux[int(sel[a_])]: round(float(mmi[a_]), 1) for a_ in np.nonzero(mmi >= 4.0)[0].tolist()}
    seisme = (a[0]["jour"] == 1 and len(sis) == 1 and sis[0][4] == loi and sis[0][2] == round(float(mmi.max()))
              and len(ev1) >= 1 and ev1[0]["jour"] == 1 and any(q[0] == 6.5 and q[1] == 1 for q in T1.sequences[i]))
    touche = T1.parcelles.bassin == b1
    crue = (any(c[0] == "inondation" and c[1] == T1.bassins.nom[b1] and c[2] == 2 for c in a[1]["cat"])
            and bool((a[1]["facteur"][touche] <= 0.5 + 1e-12).all()) and bool((a[1]["fin"][touche] == 9).all())
            and np.array_equal(a[1]["facteur"][~touche], jumeau[1]["facteur"][~touche])
            and np.array_equal(a[1]["fin"][~touche], jumeau[1]["fin"][~touche]) and len(_evts(p1, "inondation", provoque=r2["numero"])) == 1)
    ev3 = _evts(p1, "seisme", provoque=r3["numero"])
    echeance = len(ev3) >= 1 and min(e["jour"] for e in ev3) == 6 and not M.provocations_en_attente(p1)
    journal = [e["numero"] for e in _evts(p1, "provocation")] == [1, 2, 3]
    # ---- secheresse, canicule
    w2, p2 = monde(); M.provoquer(p2, "secheresse", "Altis", jours=60); b = _vivre(w2, p2, 10)
    sech = b[0]["reserves"] <= 0.10 + 1e-9 and max(x["pluie"] for x in b) <= 1e-9 and b[0]["secheresse"]
    w3, p3 = monde(); M.provoquer(p3, "canicule", "Altis", jours=10, chaleur_c=8.0); c3 = _vivre(w3, p3, 10)
    dt = np.mean([x["tmax"] for x in c3]) - np.mean([x["tmax"] for x in jumeau])
    canicule = dt >= 6.0 and len(_evts(p3, "canicule")) == 1
    # ---- falsificateurs
    w4, p4 = T.monde(["territoire"], graine=146, iles=("Altis", "Stratis"))
    T4 = p4.domaine("territoire")
    de = lambda ile: next(l for l in T4.lieux if T4.lieu_ile[T4.index_lieu[l]] == T4.iles.index(ile))
    # ( nature, ile, parametres, ce que le refus doit dire ) : un refus pour une autre raison ne compte pas
    fautes = [("tsunami", "Altis", {}, "nature inconnue"),
              ("seisme", "Altis", {"magnitude": M.SISMICITE["Altis"].m_max + 0.1}, "magnitude"),
              ("inondation", "Altis", {"lieu": de("Altis"), "gravite": 4}, "gravite"),
              ("seisme", "Altis", {"magnitude": 5.0, "lieu": de("Stratis")}, "hors de Altis"),
              ("seisme", "Altis", {"magnitude": 5.0, "jour": w4.jour}, "au plus tot"),
              ("seisme", "Atlantis", {"magnitude": 5.0}, "ile inconnue"),
              ("seisme", "Altis", {"magnitude": 5.0, "magnitud": 5.0}, "parametres inconnus")]
    refus = 0
    for nat, ile, kw, motif in fautes:
        try: M.provoquer(p4, nat, ile, **kw)
        except ValueError as e: refus += motif in str(e)
    rien = not M.provocations_en_attente(p4) and not _evts(p4, "provocation") if "provocation" in p4.socle.journal.types else not M.provocations_en_attente(p4)
    temoin = M._file(T0) is None and not any("provoque" in e for e in p0.socle.journal.recents)
    # ---- reprise
    w5 = pickle.loads(pickle.dumps(w0)); r5 = M.provoquer(w5.pays, "seisme", "Altis", magnitude=5.5, lieu=v0)
    w6, p6 = monde(); M.provoquer(p6, "seisme", "Altis", jour=2, magnitude=6.0, lieu=v0); T.jours(w6, 1)
    w7 = pickle.loads(pickle.dumps(w6)); T.jours(w6, 2); T.jours(w7, 2)
    reprise = (r5["numero"] == 1 and empreinte(w6) == empreinte(w7)
               and len(_evts(w6.pays, "seisme", provoque=1)) >= 1 and len(_evts(w7.pays, "seisme", provoque=1)) >= 1)
    ok = attente and seisme and crue and echeance and journal and sech and canicule and refus == len(fautes) and rien and temoin and reprise
    return ok, (f"seisme M6,5 sous {v0} : attend minuit {attente}, tombe au jour {a[0]['jour']} avec les intensites de la loi "
                f"{seisme} ( {len(loi)} lieux >= IV, max {mmi.max():.2f} ) ; crue gravite 2 du bassin {T1.bassins.nom[b1]} {crue} ; "
                f"ordre pour le jour 6 {echeance} ; journal {journal} | secheresse : reserves {b[0]['reserves']:.3f}, pluie max "
                f"{max(x['pluie'] for x in b):.2f} mm, bulletin {b[0]['secheresse']} -> {sech} ; canicule +8 : tmax {dt:+.2f} C sur "
                f"10 jours -> {canicule} | falsificateurs {refus}/{len(fautes)} refuses, rien note {rien} ; jumeau sans file ni "
                f"provoque {temoin} | reprise {reprise}")


TESTS = [test_climat, test_bilan_eau, test_secheresse_fermes, test_gutenberg_richter, test_pollution, test_gerer_eau,
         test_pays_vivable, test_cout, test_provoquer]
