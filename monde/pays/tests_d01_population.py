"""Les portes du domaine 1 ( population ). Ecrites avant la premiere mesure.   python -m monde.pays.tests population"""
import time
import numpy as np
from .. import config as C, monde as W
from . import essais as T, d01_population as M


# ================================================================== les lois, sur des cohortes synthetiques
def test_tables():
    """L esperance de vie de la table retrouve la Grece ( 79,0 / 84,1 ans, a 1,5 an pres ), la mortalite infantile est
    de 3 a 4,5 pour mille, l ISF de 1,30 a 1,40, l age moyen a la maternite de 30 a 32,5 ans. Controle positif : une
    table dont la pente de Gompertz est doublee en niveau fait perdre plus de 3 ans d esperance de vie."""
    t = M.TableDeMortalite(); f = M.TableDeFecondite()
    eh, ef = t.esperance_de_vie(M.HOMME), t.esperance_de_vie(M.FEMME)
    q0 = (t.q[M.HOMME, 0] + t.q[M.FEMME, 0]) / 2
    params = {s: dict(k, b=2 * k["b"]) for s, k in M.MORTALITE.items()}
    eh2 = M.TableDeMortalite(params).esperance_de_vie(M.HOMME)
    ok = (abs(eh - M.CIBLE_E0[M.HOMME]) <= 1.5 and abs(ef - M.CIBLE_E0[M.FEMME]) <= 1.5 and 0.003 <= q0 <= 0.0045
          and 1.30 <= f.isf() <= 1.40 and 30 <= f.age_moyen() <= 32.5 and eh - eh2 > 3)
    return ok, (f"e0 hommes {eh:.1f} ans, femmes {ef:.1f} ; q0 {q0 * 1000:.1f} pour mille ; ISF {f.isf():.2f}, age moyen a "
                f"la maternite {f.age_moyen():.1f} ; mortalite doublee au-dela de 15 ans : e0 hommes {eh2:.1f}")


def test_mortalite_cohorte():
    """200 000 personnes d ages et de sexes varies pendant un an : les deces tires tombent a 3 ecarts-types de
    l attendu. Controle positif : une table 1,5 fois plus mortelle donne 1,5 fois plus de morts ( a 5 % pres )."""
    rng = np.random.default_rng(1)
    n = 200_000
    sexe = rng.integers(0, 2, n); age = rng.integers(0, 100, n)
    def compter(table):
        vivant = np.ones(n, bool); morts = 0; attendu = 0.0
        for j in range(365):
            idx = np.nonzero(vivant)[0]
            qj = table.q_jour(sexe[idx], age[idx]); attendu += qj.sum()
            m = idx[M.tirer_deces(table, sexe[idx], age[idx], rng.random(len(idx)))]
            vivant[m] = False; morts += len(m)
        return morts, attendu
    m1, a1 = compter(M.TableDeMortalite())
    m15, _ = compter(M.TableDeMortalite(facteur=1.5))
    z = (m1 - a1) / np.sqrt(a1)
    ok = abs(z) <= 3 and abs(m15 / m1 - 1.5) <= 0.075
    return ok, f"{m1} morts pour {a1:.0f} attendus ( z = {z:+.2f} ) ; table x1,5 : {m15} morts, rapport {m15 / m1:.3f}"


def _simuler_femmes(table, n=100_000, annees=3, graine=2):
    """Des femmes d age fixe, moitie en couple, qui concoivent, perdent ou portent, accouchent, puis attendent 3 mois.
    Rend ( naissances par femme et par an, par age ; part des naissances hors couple ), mesurees apres un an de chauffe."""
    rng = np.random.default_rng(graine)
    age = rng.integers(15, 50, n); couple = rng.random(n) < 0.5
    occupee_jusqu = np.zeros(n, np.int64); naissance_le = np.full(n, -1, np.int64)
    nes = np.zeros(111); expo = np.zeros(111); hors = total = 0
    for j in range(annees * 365):
        mesure = j >= 365
        nait = np.nonzero(naissance_le == j)[0]
        if mesure:
            np.add.at(nes, age[nait], 1); total += len(nait); hors += int((~couple[nait]).sum())
            np.add.at(expo, age, 1.0 / 365)
        occupee_jusqu[nait] = j + M.POST_PARTUM_J; naissance_le[nait] = -1
        libre = np.nonzero(occupee_jusqu <= j)[0]
        k = M.facteur_couples(table, age[libre], couple[libre])
        c = libre[M.tirer_conceptions(table, age[libre], couple[libre], rng.random(len(libre)), k)]
        perdue = rng.random(len(c)) < M.FAUSSE_COUCHE
        g = np.clip(rng.normal(*M.GESTATION_J, len(c)), 196, 294).astype(np.int64)
        occupee_jusqu[c] = np.where(perdue, j + rng.integers(42, 85, len(c)), j + g + 10 ** 6)
        naissance_le[c[~perdue]] = j + g[~perdue]
    return nes / np.maximum(expo, 1e-9), hors / max(1, total), total


def test_fecondite_cohorte():
    """100 000 femmes pendant 3 ans : les naissances par age retrouvent la table ( ISF a 5 % pres, chaque groupe de 25
    a 39 ans a 8 % pres ), malgre les grossesses perdues et le temps ou une femme ne peut pas concevoir. Controle
    positif : une table doublee double les naissances ( 1,8 a 2,2 )."""
    t = M.TableDeFecondite()
    taux, hors, n1 = _simuler_femmes(t)
    isf = sum(taux[a] for a in range(15, 50))
    groupes = {a: taux[a:a + 5].mean() / M.ASFR[a] for a in (25, 30, 35)}
    _, _, n2 = _simuler_femmes(M.TableDeFecondite(facteur=2.0))
    ok = abs(isf / t.isf() - 1) <= 0.05 and all(abs(r - 1) <= 0.08 for r in groupes.values()) and 1.8 <= n2 / n1 <= 2.2
    return ok, (f"ISF mesure {isf:.3f} pour {t.isf():.3f} ; 25-39 ans : " + ", ".join(f"{a} {r:.2f}" for a, r in groupes.items())
                + f" ; naissances hors couple {hors:.0%} ; table doublee : x{n2 / n1:.2f}")


# ================================================================== le domaine dans le moteur
def test_personnes_et_familles():
    """Porte : 60 jours ( avec l epidemie du moteur ) : vivants = depart + naissances - morts, chaque mort traite une
    fois, aucune incoherence de famille, conservation tenue. Falsificateurs : un habitant retire a la main de son
    menage, un mort pose a la main sans passer par `deceder` - les deux se voient ; le second est repris le soir."""
    w, p = T.monde(["population"])
    d = p.domaine("population")
    v0 = sum(1 for h in w.habitants if h.vivant)
    T.jours(w, 60)
    v1 = sum(1 for h in w.habitants if h.vivant)
    traites = int((p.col("habitant", "deces_j")[:len(w.habitants)] >= 0).sum())
    bilan = v1 == v0 + d.naissances - d.deces and traites == d.deces
    anomalies = M.anomalies_familles(p)
    tenue, msg = p.socle.conservation.tenue()
    resume = (f"{v0} -> {v1} vivants, {d.naissances} naissances, {d.deces} morts ( {traites} traites ), "
              f"{d.unions} unions, {d.divorces} divorces, {d.placements} placements")
    h = next(x for x in w.habitants if x.vivant and len([y for y in x.menage.membres if y.vivant]) > 1
             and M.age_de(p, x) >= 30)
    h.vivant = False
    vu_mort = ("mort_non_traite", h.id) in M.anomalies_familles(p)
    T.jours(w, 1)
    repris = ("mort_non_traite", h.id) not in M.anomalies_familles(p)
    g = next(x for x in w.habitants if x.vivant)
    g.menage.membres.remove(g)
    vu_lien = ("hors_de_son_menage", g.id) in M.anomalies_familles(p)
    ok = bilan and not anomalies and tenue and vu_mort and repris and vu_lien
    return ok, (f"{resume} ; incoherences {len(anomalies)} ; {msg} ; mort a la main vu {vu_mort} puis repris {repris} ; "
                f"lien casse vu {vu_lien}")


def test_etat_civil():
    """Porte : l Etat compte ses inscrits a l unite, et l ecart a la verite est exactement fait des naissances non
    encore declarees moins des deces non encore declares ; au moins une naissance a attendu sa declaration ( sans
    quoi le retard n a pas ete exerce ). 2 500 habitants. Falsificateur : un habitant inscrit a la main se voit."""
    w, p = T.monde(["population"], echelle=5)
    ec = p.domaine("population").etat_civil
    col = p.colonnes["habitant"]
    retard_max = 0
    for _ in range(60):
        T.jours(w, 1)
        n = len(w.habitants)
        vivant = np.fromiter((h.vivant for h in w.habitants), bool, n)
        non_inscrits = int((vivant & (col["inscrit"][:n] == 0)).sum())
        morts_non_declares = int((~vivant & (col["inscrit"][:n] == 1) & (col["deces_declare"][:n] == 0)).sum())
        ecart = int(vivant.sum()) - ec.population_connue()
        if ecart != non_inscrits - morts_non_declares or ec.population_connue() != M.recompte_etat_civil(p): break
        retard_max = max(retard_max, non_inscrits)
    else:
        i = next(h.id for h in w.habitants if h.vivant)
        col["inscrit"][i] = 0
        vu = ec.population_connue() != M.recompte_etat_civil(p)
        return vu and retard_max >= 1, (f"60 jours au registre exact ; {ec.naissances} naissances et {ec.deces} deces declares ; jusqu a "
                    f"{retard_max} naissances en attente de declaration ; inscription faussee vue : {vu}")
    return False, f"jour {p.jour} : registre {ec.population_connue()} contre recompte {M.recompte_etat_civil(p)}"


def test_recensement():
    """Porte : le recensement donne un pays plausible - de 35 a 80 % des femmes de 25 a 64 ans en couple, de 1,8 a
    3,2 personnes par menage habite ( Grece : ~2,5 ), et aucune incoherence."""
    w, p = T.monde(["population"])
    col = p.colonnes["habitant"]
    f = [h for h in w.habitants if col["sexe"][h.id] == M.FEMME and 25 <= M.age_de(p, h) < 65]
    en_couple = sum(1 for h in f if col["conjoint"][h.id] >= 0) / max(1, len(f))
    hab = T.menages_habites(w)
    taille = sum(len([x for x in m.membres if x.vivant]) for m in hab) / len(hab)
    mineurs = [h for h in w.habitants if M.age_de(p, h) < 18]
    avec_mere = sum(1 for h in mineurs if col["mere"][h.id] >= 0) / max(1, len(mineurs))
    anomalies = M.anomalies_familles(p)
    ok = 0.35 <= en_couple <= 0.80 and 1.8 <= taille <= 3.2 and not anomalies
    return ok, (f"femmes de 25-64 ans en couple {en_couple:.0%} ; {taille:.2f} personnes par menage ( moteur E1 : "
                f"{len(w.habitants) / len(w.menages):.2f} avant fusion ) ; mineurs a mere connue {avec_mere:.0%} ; "
                f"incoherences {len(anomalies)}")


def test_heritage():
    """Porte, sur un cas construit : un parent seul meurt en laissant un mineur chez lui et un enfant majeur ailleurs -
    le mineur va chez son aine, la caisse entiere suit les deux heritiers, le menage est dissous. Puis un habitant
    seul, sans enfant ni parent connu : sa caisse va a l Etat. Conservation tenue, aucune incoherence."""
    w, p = T.monde(["population"])
    d = p.domaine("population"); col = p.colonnes["habitant"]
    def seul(m): return [x for x in m.membres if x.vivant]
    A = next(m for m in w.menages if len(seul(m)) == 1 and M.age_de(p, seul(m)[0]) >= 30)
    X = seul(A)[0]
    Z = next(h for h in w.habitants if h.vivant and h.menage is not A and M.age_de(p, h) >= 20 and len(seul(h.menage)) >= 1)
    Y = next(h for h in w.habitants if h.vivant and M.age_de(p, h) < 16 and h.menage not in (A, Z.menage)
             and len(M.adultes_vivants(p, h.menage)) >= 1)
    M.deplacer_membre(p, Y, A)
    lien = "mere" if col["sexe"][X.id] == M.FEMME else "pere"
    for e in (Y, Z): col[lien][e.id] = X.id
    d.enfants_de[X.id] = [Y.id, Z.id]
    B = Z.menage
    avant_A, avant_B = A.caisse, B.caisse
    M.deceder(p, X, "accident")
    cas1 = (Y.menage is B and abs(B.caisse - (avant_B + avant_A)) <= 1e-9 and A.caisse == 0
            and p.col("menage", "dissous")[A.id] == 1)
    D_ = next(m for m in w.menages if len(seul(m)) == 1 and M.age_de(p, seul(m)[0]) >= 30 and m is not B
              and not d.enfants_de.get(seul(m)[0].id) and col["mere"][seul(m)[0].id] < 0 and col["pere"][seul(m)[0].id] < 0)
    V = seul(D_)[0]
    avant_D, avant_G = D_.caisse, w.gouv.caisse
    M.deceder(p, V, "naturelle")
    cas2 = abs(w.gouv.caisse - (avant_G + avant_D)) <= 1e-9 and D_.caisse == 0
    tenue, msg = p.socle.conservation.tenue()
    anomalies = M.anomalies_familles(p)
    ok = cas1 and cas2 and tenue and not anomalies
    return ok, (f"parent seul : {avant_A:.0f} drachmes a ses deux enfants, le mineur place chez son aine : {cas1} ; "
                f"habitant sans heritier : {avant_D:.0f} a l Etat : {cas2} ; {msg} ; incoherences {len(anomalies)}")


def test_migrer():
    """Porte de la decision : secheresse sur les fermes d Athira et de Pyrgos pendant 40 jours, les menages affames
    decident au hasard ( mode hasard ). La note doit dependre du choix ( part du choix >= 0,01 : partir nourrit ou
    ne nourrit pas CE menage ), des menages doivent partir, et le pays reste coherent et conserve."""
    w, p = T.monde(["population"], modes={"migrer": "hasard"})
    villages = [l.id for l in w.carte.lieux.values() if l.type == "village" and l.marche.id in ("Athira", "Pyrgos")]
    w.chocs.append({"debut": 1, "jours": 40, "lieux": villages, "facteur": 0.03})
    T.jours(w, 40)
    d = p.domaine("population"); dec = d.decideur
    part = dec.part_du_choix()
    notes = dec.notes_par_action()
    tenue, msg = p.socle.conservation.tenue()
    anomalies = M.anomalies_familles(p)
    ok = dec.n_decisions >= 20 and d.migrations >= 5 and part >= 0.01 and tenue and not anomalies
    return ok, (f"{dec.n_decisions} decisions, {d.migrations} demenagements ; notes : "
                + ", ".join(f"{a} {m:.2f} ( {n} )" for a, (n, m) in notes.items())
                + f" ; part du choix {part:.3f} ; faim finale {T.faim(w):.0%} ; {msg} ; incoherences {len(anomalies)}")


def test_pays_vivable():
    return T.porte_commune("population", n_jours=12)


def test_cout():
    """Le domaine coute au plus 25 % d une journee du moteur, a 10 000 habitants."""
    def jour_moyen(avec):
        w = W.Monde(echelle=20)
        if avec: T.P.installer(w, ["population"])
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants)
    t_e1, n = jour_moyen(False)
    t_pop, _ = jour_moyen(True)
    w, p = T.monde(["population"], echelle=20); T.jours(w, 3)
    t0 = time.perf_counter()
    for _ in range(3): M._demographie(p); M._soir(p); M._reprendre_les_morts(p); M._recueillir(p)   # ( 30/09 ) le balayage
    propre = (time.perf_counter() - t0) / 3
    ok = t_pop <= 1.25 * t_e1 and propre <= 0.25 * t_e1
    return ok, (f"{n} habitants : moteur seul {t_e1:.2f} s par jour, avec la population {t_pop:.2f} s "
                f"( {t_pop / t_e1 - 1:+.0%}, les menages fusionnes allegent les boucles du moteur ) ; routines propres du "
                f"domaine {propre * 1000:.0f} ms par jour, soit {propre / n * 1e6:.1f} us par habitant")


def test_faim_tue():
    """La faim tue au rythme du reel ( SEUILS_FAIM, 27/09 ). Cohortes : un adulte qui ne mange plus meurt entre 45 et
    80 jours ( 10 % avant le jour 58, la moitie vers 63, 90 % avant 80 ) ; un enfant de 3 ans avant 50 jours ( mediane ) ;
    a demi-ration pendant 24 semaines ( Keys 1950 ), moins de 2 % meurent. Dans le monde : des adultes au deficit de 40
    rations meurent a l aube, cause « faim » au journal et dans la colonne ; sans deficit, aucune mort de faim."""
    rng = np.random.default_rng(3)
    def cohorte(age, ration, jours, n=20000):
        faim = np.zeros(n); mort = np.full(n, -1)
        for j in range(1, jours + 1):
            vivant = mort < 0
            faim[vivant] += max(0.0, (1.0 - ration) - C.FAIM_ADAPTATION)
            idx = np.nonzero(vivant)[0]
            r = M.risque_faim(faim[idx], np.full(idx.size, age))
            mort[idx[rng.random(idx.size) < r]] = j
        return mort
    a = cohorte(35, 0.0, 120); e = cohorte(3, 0.0, 120); k = cohorte(30, 0.5, 168)
    q10, q50, q90 = np.percentile(a[a > 0], [10, 50, 90])
    me = np.median(e[e > 0]); pk = (k > 0).mean()
    cohortes = bool((a > 0).all()) and 45 <= q10 <= 58 and 55 <= q50 <= 70 and q90 <= 80 and me < 50 and pk < 0.02
    # dans le monde
    r = T.monde(["population"], graine=5); w = r[0] if isinstance(r, tuple) else r; p = w.pays
    T.jours(w, 1)
    t = w.table; n = t.n
    ad = np.nonzero((t.vivant[:n] == 1) & (t.age[:n] >= 20) & (t.age[:n] < 60))[0]
    def morts_de_faim(): return [x for x in p.socle.journal.recents if x["type"] == "deces" and x.get("cause") == "faim"]
    T.jours(w, 1); temoin = len(morts_de_faim())
    t.faim[ad] = 40.0; T.jours(w, 1); mf = morts_de_faim()
    col = p.col("habitant", "cause_deces")
    colonne = all(col[x["habitant"]] == M.CAUSES.index("faim") for x in mf)
    attendu = M.PENTE_FAIM * ((40.0 - 26.0) / 20.0) ** 2 * len(ad)
    monde_ok = temoin == 0 and 0.5 * attendu <= len(mf) <= 1.5 * attendu and colonne and len(mf) > 0
    return cohortes and monde_ok, (f"jeune total, adulte : 10 % morts au jour {q10:.0f}, 50 % au jour {q50:.0f}, 90 % au jour "
        f"{q90:.0f} ; enfant de 3 ans : mediane jour {me:.0f} ; demi-ration 24 semaines : {pk:.1%} de morts ; monde : {len(ad)} "
        f"adultes a 40 rations de deficit -> {len(mf)} morts de faim ( attendu ~{attendu:.0f} ), temoin {temoin}, colonne : {colonne}")


def test_placement_en_colonnes():
    """HMT-130 : la recherche des familles d accueil d un orphelin en colonnes ( `_accueil_colonnes` ) rend exactement la liste
    de la recherche d origine ( `_accueil_reference`, une vue par menage ), dans le meme ordre, pour tous les mineurs des
    menages frappes par une vague de morts ( 3 % des adultes de 25 a 60 ans d un pays de 4 000 habitants ) ; puis la vague
    elle-meme laisse les familles coherentes. Controle positif : une reference alteree ( un menage de plus ) est vue."""
    w, p = T.monde(["population"], echelle=8.0); T.jours(w, 2)
    tb = w.table; n = tb.n; col = p.colonnes["habitant"]
    age = (p.jour - col["naissance_j"][:n]) / 365.0
    adultes = np.nonzero((tb.vivant[:n] == 1) & (age >= 25) & (age < 60))[0]
    rng = np.random.default_rng(1); cibles = np.sort(rng.choice(adultes, size=max(1, int(0.03 * adultes.size)), replace=False))
    mm = M.P.menages_inscrits(tb, n)
    mineurs = np.nonzero((tb.vivant[:n] == 1) & (age < 18) & np.isin(mm, mm[cibles]))[0].tolist()
    ecarts = compares = 0
    for i in mineurs:
        x = w.habitants[i]
        a = [m.id for m in M._accueil_colonnes(p, x)]; b = [m.id for m in M._accueil_reference(p, x)]
        compares += 1; ecarts += a != b
    x0 = w.habitants[mineurs[0]] if mineurs else None
    altere = x0 is not None and [m.id for m in M._accueil_colonnes(p, x0)] != [m.id for m in M._accueil_reference(p, x0)] + [0]
    t0 = time.perf_counter()
    for i in cibles.tolist(): M.deceder(p, w.habitants[i], "maladie")
    dt = time.perf_counter() - t0
    anomalies = M.anomalies_familles(p)
    ok = compares >= 10 and ecarts == 0 and altere and not anomalies
    return ok, (f"{compares} orphelins compares, {ecarts} ecart(s) de familles d accueil ; reference alteree vue : {altere} ; "
                f"{cibles.size} adultes morts d un coup en {dt:.2f} s, {p.domaine('population').placements} placements, "
                f"anomalies {len(anomalies)}")


# ================================================================== les orphelins ( 30/09, session Classes )
def _foyer(p, w, pris):
    """Un menage construit : un adulte X de 30 ans ou plus, seul, et un mineur Y de moins de 16 ans venu d un menage qui
    garde un adulte ; X est le parent de Y et n a aucune autre parente connue. `pris` : les menages deja pris."""
    d = p.domaine("population"); col = p.colonnes["habitant"]
    def seuls(m): return [x for x in m.membres if x.vivant]
    A = next(m for m in w.menages if m.id not in pris and len(seuls(m)) == 1 and M.age_de(p, seuls(m)[0]) >= 30
             and w.table.statut[seuls(m)[0].id] != M.P.ABSENT)
    X = seuls(A)[0]
    Y = next(h for h in w.habitants if h.vivant and M.age_de(p, h) < 16 and h.menage.id not in pris and h.menage.id != A.id
             and len(M.adultes_vivants(p, h.menage)) >= 1)
    pris.update((A.id, Y.menage.id))
    M.deplacer_membre(p, Y, A)
    for k in ("mere", "pere"): col[k][X.id] = col[k][Y.id] = -1
    col["mere" if col["sexe"][X.id] == M.FEMME else "pere"][Y.id] = X.id
    d.enfants_de[X.id] = [Y.id]
    return A, X, Y


def _ailleurs(p, w, pris, age_min):
    """Un adulte present d un menage qui n est pas encore pris ( la parente qu on pose a la main )."""
    h = next(h for h in w.habitants if h.vivant and M.age_de(p, h) >= age_min and h.menage.id not in pris
             and w.table.statut[h.id] != M.P.ABSENT)
    pris.add(h.menage.id)
    return h


def _grand_mere(p, X, G, U):
    """G devient le parent de X et de U : pour l enfant de X, une grand-mere et un oncle ( ou une tante )."""
    col = p.colonnes["habitant"]; d = p.domaine("population")
    k = "mere" if col["sexe"][G.id] == M.FEMME else "pere"
    col[k][X.id] = G.id; col[k][U.id] = G.id
    d.enfants_de[G.id] = [X.id, U.id]


def _lien(p, y):
    ev = [x for x in p.socle.journal.recents if x["type"] == "placement" and x.get("enfant") == y.id]
    return ev[-1]["lien"] if ev else None


def test_orphelins_controles():
    """Portes des orphelins ( 30/09, critere ecrit avant le code ), sur des menages construits d un adulte X et de son
    enfant Y. P2, la mort de X : le jour meme, Y est chez sa grand-mere presente ( lien grand_parent ), chez son oncle
    si la grand-mere est absente ( oncle_tante ), sinon dans une famille d accueil de son lieu avec un adulte present ;
    la caisse du menage suit Y ( seul heritier ), le menage est dissous. P3, l absence de X ( comme la prison du domaine
    21 ) : le soir meme Y est chez sa grand-mere, le menage de X reste ; X revenu, Y rentre le soir meme. P4
    falsificateur : sans le balayage du soir, P3 laisse Y seul, et l invariant ( menages_sans_adulte ) comme la porte des
    familles le voient a minuit. P5 : conservation tenue, aucune incoherence de famille, invariant nul chaque soir."""
    w, p = T.monde(["population"]); T.jours(w, 1)
    d = p.domaine("population"); tb = w.table; dis = p.col("menage", "dissous")
    pris = set(); res = {}
    # P2 a : grand-mere presente
    A, X, Y = _foyer(p, w, pris); G = _ailleurs(p, w, pris, 45); U = _ailleurs(p, w, pris, 20); _grand_mere(p, X, G, U)
    B = G.menage; a0, b0 = A.caisse, B.caisse
    M.deceder(p, X, "accident")
    res["grand_parent"] = (int(tb.menage[Y.id]) == B.id and _lien(p, Y) == "grand_parent" and abs(B.caisse - (a0 + b0)) <= 1e-6
                           and A.caisse == 0 and dis[A.id] == 1)
    # P2 b : grand-mere absente ( detenue ), l oncle ou la tante
    A, X, Y = _foyer(p, w, pris); G = _ailleurs(p, w, pris, 45); U = _ailleurs(p, w, pris, 20); _grand_mere(p, X, G, U)
    tb.statut[G.id] = M.P.ABSENT
    M.deceder(p, X, "accident")
    res["oncle_tante"] = int(tb.menage[Y.id]) == int(tb.menage[U.id]) and _lien(p, Y) == "oncle_tante"
    tb.statut[G.id] = M.P.RESIDENT
    # P2 c : aucune parente, une famille d accueil de son lieu, avec un adulte present
    A, X, Y = _foyer(p, w, pris); lieu = int(tb.menages.domicile[A.id]); a0 = A.caisse
    M.deceder(p, X, "accident")
    F = Y.menage
    res["accueil"] = (_lien(p, Y) == "accueil" and F.id != A.id and bool(M._adultes_presents(p, F))
                      and int(tb.menages.domicile[F.id]) == lieu and A.caisse == 0 and dis[A.id] == 1)
    # P3 : l absence de X, puis son retour
    A, X, Y = _foyer(p, w, pris); G = _ailleurs(p, w, pris, 45); U = _ailleurs(p, w, pris, 20); _grand_mere(p, X, G, U)
    tb.statut[X.id] = M.P.ABSENT                             # 6 h : le monde nait a l aube ( config.DATE_DEPART )
    seuls = [len(M.menages_sans_adulte(p))]
    T.jours(w, 0.75); seuls.append(len(M.menages_sans_adulte(p)))           # minuit : la fin du jour
    garde = (int(tb.menage[Y.id]) == int(tb.menage[G.id]) and dis[A.id] == 0 and d.gardes.get(Y.id) == A.id)
    tb.statut[X.id] = M.P.RESIDENT
    T.jours(w, 1); seuls.append(len(M.menages_sans_adulte(p)))
    res["absence_et_retour"] = garde and int(tb.menage[Y.id]) == A.id and Y.id not in d.gardes and _lien(p, Y) == "retour"
    tenue, msg = p.socle.conservation.tenue()
    anomalies = M.anomalies_familles(p)
    # P4 : le falsificateur, sans le balayage du soir
    w2, p2 = T.monde(["population"]); T.jours(w2, 1)
    for lst in p2.routines.values(): lst[:] = [r for r in lst if r[2] is not M._recueillir]
    pris2 = set(); A2, X2, Y2 = _foyer(p2, w2, pris2)
    G2 = _ailleurs(p2, w2, pris2, 45); U2 = _ailleurs(p2, w2, pris2, 20); _grand_mere(p2, X2, G2, U2)
    w2.table.statut[X2.id] = M.P.ABSENT
    T.jours(w2, 0.75)
    vu = A2.id in M.menages_sans_adulte(p2).tolist() and ("mineurs_seuls", A2.id) in M.anomalies_familles(p2)
    ok = all(res.values()) and seuls == [1, 0, 0] and tenue and not anomalies and vu
    return ok, (" ; ".join(f"{k} {v}" for k, v in res.items()) + f" ; menages sans adulte ( absence posee, soir, retour ) "
                f"{seuls} ; {msg} ; incoherences {len(anomalies)} ; sans le balayage, le menage seul est vu : {vu}")


def _sans_appel(p, k):
    """Le falsificateur : l appel du domaine 21 a l arrestation ( `confier_si_seuls` ) neutralise."""
    return None


def test_orphelins_invariant():
    """Porte des orphelins ( 30/09, amendee par le chef de projet : A TOUTE HEURE ) : Altis, tous les domaines livres ( la
    prison du domaine 21 comprise ), echelle 20, graine du test, 40 jours : aucun menage habite sans adulte present juste
    apres l installation ni apres AUCUN pas de 10 minutes ; conservation tenue. Falsificateur : sans l appel du domaine
    21 ( `confier_si_seuls` neutralise ), les enfants des detenus de l installation sont seuls des la premiere mesure
    ( 4 a la graine du test ), jusqu au balayage de 23 h 50."""
    from ..porte_domaines import LIVRES
    w, p = T.monde(LIVRES, echelle=20.0)
    d = p.domaine("population")
    vus = [len(M.menages_sans_adulte(p))]
    for _ in range(40 * C.PAS_PAR_JOUR):
        w.pas_suivant(); vus.append(len(M.menages_sans_adulte(p)))
    tenue, msg = p.socle.conservation.tenue()
    orig = M.confier_si_seuls; M.confier_si_seuls = _sans_appel
    try:
        w2, p2 = T.monde(LIVRES, echelle=20.0)
        seuls = [len(M.menages_sans_adulte(p2))]
        for _ in range(C.PAS_PAR_JOUR):
            w2.pas_suivant(); seuls.append(len(M.menages_sans_adulte(p2)))
    finally:
        M.confier_si_seuls = orig
    ok = max(vus) == 0 and tenue and seuls[0] >= 1
    return ok, (f"{w.table.n} habitants, {len(vus)} mesures ( l installation, puis chaque pas de 40 jours ) : au plus "
                f"{max(vus)} menage sans adulte ; {d.placements} placements, {len(d.gardes)} enfants confies le temps d une "
                f"absence ; {msg} ; sans l appel du domaine 21 : {seuls[0]} menage(s) sans adulte a l installation, vus "
                f"{sum(1 for x in seuls if x)} mesures sur {len(seuls)} du premier jour")


def test_orphelins_arrestation():
    """Porte de l arrestation ( 30/09, amendement du chef de projet, critere ecrit avant ) : a 0 h 30, l heure des delits,
    le domaine 21 incarcere ( `_incarcerer` ) le seul adulte X d un menage construit, X et son enfant Y, une grand-mere
    presente ailleurs. P7 : dans le MEME pas, Y est chez sa grand-mere, confie le temps de l absence, et l invariant ne
    voit pas le menage ; conservation tenue. P8 falsificateur : sans l appel ( `confier_si_seuls` neutralise ), Y est vu
    seul a l arrestation puis apres chaque pas jusqu a 23 h 50 ( 141 mesures ), et c est le balayage du soir qui le
    confie a minuit."""
    from . import d21_justice as J
    def poser(w, p):
        while w.minutes % (24 * 60) != 30: w.pas_suivant()          # le monde nait a 6 h : jusqu a 0 h 30
        pris = set(); A, X, Y = _foyer(p, w, pris)
        G = _ailleurs(p, w, pris, 45); U = _ailleurs(p, w, pris, 20); _grand_mere(p, X, G, U)
        J._incarcerer(p, J._dom(p), X.id, J.PROVISOIRE, -1, p.jour + 5)
        return A, Y, G
    w, p = T.monde(["justice"])
    A, Y, G = poser(w, p); tb = w.table
    meme_pas = (int(tb.menage[Y.id]) == int(tb.menage[G.id]) and _lien(p, Y) == "grand_parent"
                and A.id not in M.menages_sans_adulte(p).tolist() and p.domaine("population").gardes.get(Y.id) == A.id)
    tenue, msg = p.socle.conservation.tenue()
    orig = M.confier_si_seuls; M.confier_si_seuls = _sans_appel
    try:
        w2, p2 = T.monde(["justice"])
        A2, Y2, G2 = poser(w2, p2)
        vu = [A2.id in M.menages_sans_adulte(p2).tolist()]
        while vu[-1] and len(vu) <= C.PAS_PAR_JOUR:
            w2.pas_suivant(); vu.append(A2.id in M.menages_sans_adulte(p2).tolist())
        minuit = w2.minutes % (24 * 60) == 0
        confie = int(w2.table.menage[Y2.id]) == int(w2.table.menage[G2.id])
    finally:
        M.confier_si_seuls = orig
    ok = meme_pas and tenue and sum(vu) == 141 and not vu[-1] and minuit and confie
    return ok, (f"arrestation a 0 h 30 : confie dans le meme pas chez sa grand-mere {meme_pas} ; {msg} ; sans l appel : "
                f"vu seul {sum(vu)} mesures, confie a minuit par le balayage {minuit and confie}")


TESTS = [test_tables, test_mortalite_cohorte, test_fecondite_cohorte, test_recensement, test_personnes_et_familles,
         test_etat_civil, test_heritage, test_migrer, test_pays_vivable, test_cout, test_faim_tue, test_placement_en_colonnes,
         test_orphelins_controles, test_orphelins_invariant, test_orphelins_arrestation]
