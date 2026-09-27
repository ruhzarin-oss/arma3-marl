"""Les portes du domaine 25 ( armee A : organisation, soldat, equipement, armes, optiques, munitions, vehicules ).
Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests armee"""
import math, pickle, time
import numpy as np
from .. import config as C, monde as W, population as PO
from ..socle import objets as O
from . import essais as T, pays as P, d01_population as POP, d04_travail as TR, d25_armee as M

_CACHE = {}


def _monde(jours=0, echelle=5, graine=11, modes=None):
    """Un monde avec l armee et ses dependances, apres `jours` jours ; chaque porte en reprend une copie."""
    k = (jours, echelle, graine, tuple(sorted((modes or {}).items())))
    if k not in _CACHE:
        w, p = T.monde([M.DOMAINE], graine, echelle, modes=modes)
        T.jours(w, jours)
        _CACHE[k] = pickle.dumps(w)
    w = pickle.loads(_CACHE[k])
    return w, w.pays


def _jusqu_a(w, heure):
    for _ in range(C.PAS_PAR_JOUR + 1):
        if abs(w.heure - heure) < 1e-6: return
        w.pas_suivant()
    raise RuntimeError(f"heure {heure} jamais atteinte")


def _militaires_du_moteur(p):
    """Ce que le recensement doit trouver : soldats et officiers vivants, en emploi, qui travaillent a une base."""
    w = p.w; tb = w.table; n = tb.n; col = p.colonnes["habitant"]
    bases = np.zeros(len(w.carte.par_n), bool); bases[[b.n for b in w.carte.de_type("base")]] = True
    tr = tb.travail[:n]; ro = tb.role[:n]
    return np.nonzero((tb.vivant[:n] == 1) & (tr >= 0) & bases[np.maximum(tr, 0)]
                      & ((ro == PO.CODE_ROLE["soldat"]) | (ro == PO.CODE_ROLE["officier"]))
                      & np.isin(col["tr_statut"][:n], TR.EN_EMPLOI))[0]


# ================================================================== l organisation
def test_effectifs_et_structure():
    """10 000 habitants, le jour de l installation. Chaque militaire present a une unite ; chaque soldat actif est dans
    un groupe ; les militaires du recensement sont exactement les soldats et officiers en emploi des bases ( plus les
    conscrits ). Pour CHAQUE unite, son effectif = ses membres directs + l effectif de ses filles, et l armee compte
    tout le monde. Doctrine : aucun groupe d infanterie de plus de 10 ; au moins 90 % des soldats d infanterie dans des
    groupes de 8 a 10 ; les equipages de char a 4 ; au plus 3 groupes par section ( 4 equipages par peloton de chars,
    doctrine ecrite dans la FICHE ), 4 sections par compagnie, 4
    compagnies ( plus l instruction ) par bataillon. Commandement : chaque unite peuplee a un chef qui en est membre ;
    la chaine d un soldat de groupe remonte en 6 niveaux jusqu a l armee ; officiers sous-lieutenant et plus, soldats
    adjudant au plus. Le dimensionnement grec ( 1,37 % d actifs ) est rapporte a cote de ce que donne le moteur."""
    w, p = _monde(0, echelle=20)
    d = p.domaine(M.DOMAINE); E = d.eff; U = d.unites
    rows = M._lignes(d)
    sans = int((E["unite"][rows] < 0).sum())
    act = rows[(E["statut"][rows] == M.ACTIF) & (E["spec"][rows] != M.OFFICIER)]
    hors_groupe = int((U["niveau"][E["unite"][act]] != M.GROUPE).sum())
    attendus = set(_militaires_du_moteur(p).tolist())
    presents = set(E["hid"][rows].tolist())
    recense = attendus == presents
    direct = np.bincount(E["unite"][rows], minlength=U.n)
    somme_ok = True
    for u in range(U.n):
        filles = [f for f in range(U.n) if U["parent"][f] == u]
        if M.effectif(p, u) != direct[u] + sum(M.effectif(p, f) for f in filles): somme_ok = False; break
    tout = M.effectif(p, d.armee_u) == len(rows)
    tailles = {u: int(direct[u]) for u in range(U.n) if U["niveau"][u] == M.GROUPE}
    inf = [t for u, t in tailles.items() if U["type"][u] == M.INFANTERIE]
    chars = [t for u, t in tailles.items() if U["type"][u] == M.CHARS]
    part_doctrine = sum(t for t in inf if 8 <= t <= 10) / max(1, sum(inf))
    def nfilles(u, niv): return sum(1 for f in range(U.n) if U["parent"][f] == u and U["niveau"][f] == niv)
    sec_ok = all(nfilles(u, M.GROUPE) <= (4 if U["type"][u] == M.CHARS else 3) for u in range(U.n)
                 if U["niveau"][u] == M.SECTION)
    comp_ok = all(nfilles(u, M.SECTION) <= 4 for u in range(U.n) if U["niveau"][u] == M.COMPAGNIE)
    bat_ok = all(sum(1 for f in range(U.n) if U["parent"][f] == u and U["niveau"][f] == M.COMPAGNIE
                     and U["type"][f] != M.INSTRUCTION) <= 4 for u in range(U.n) if U["niveau"][u] == M.BATAILLON)
    chefs_ok = all(int(U["chef"][u]) in set(M.membres(p, u).tolist()) for u in range(U.n)
                   if M.effectif(p, u) > 0 and U["type"][u] != M.INSTRUCTION)
    g0 = next(r for r in act.tolist() if U["niveau"][E["unite"][r]] == M.GROUPE)
    chaine = M.chaine_de_commandement(p, int(E["hid"][g0]))
    chaine_ok = [c[0] for c in chaine] == list(reversed(M.NIVEAUX))
    off = E["spec"][rows] == M.OFFICIER
    grades_ok = bool((E["grade"][rows][off] >= M.SOUS_LIEUTENANT).all() and (E["grade"][rows][~off] <= M.ADJUDANT).all())
    v = M.effectifs_vises(p)
    ok = (sans == 0 and hors_groupe == 0 and recense and somme_ok and tout and max(inf) <= 10 and part_doctrine >= 0.9
          and all(t == 4 for t in chars) and sec_ok and comp_ok and bat_ok and chefs_ok and chaine_ok and grades_ok)
    niv = {M.NIVEAUX[k]: int((U["niveau"][:U.n] == k).sum()) for k in range(6)}
    return ok, (f"{len(rows)} militaires ( {int(off.sum())} officiers ) pour {v['population']} habitants, "
                f"{len(rows) / v['population']:.1%} ( vise grec {v['actifs']:.0f}, 1,37 % ) ; sans unite {sans}, soldats "
                f"hors groupe {hors_groupe} ; recensement exact {recense} ; sommes par unite {somme_ok}, armee {tout} ; "
                f"unites {niv} ; groupes d infanterie {min(inf)}-{max(inf)} ( {part_doctrine:.0%} des soldats en 8-10 ), "
                f"equipages {chars} ; sections {sec_ok}, compagnies {comp_ok}, bataillons {bat_ok} ; chefs membres "
                f"{chefs_ok} ; chaine {'>'.join(c[0][:3] for c in chaine)} ; grades {grades_ok}")


# ================================================================== la portee utile
def test_portee_utile():
    """La portee utile d un tireur est le MINIMUM de son arme et de son optique ( lecon d Arma, 13/09 ). Exact sur toute
    la table ( 7 armes x 6 optiques ) ; exact pour chaque militaire du monde, recalcule par un autre chemin ( les
    modeles des objets du Parc ) ; les cas payes : M4 + ACO = 400 m ( l optique limite ), G3A3 + lunette x 10 = 400 m
    ( l arme limite ), Glock + fer = 50 m. Controle positif : un fusilier G3A3 au fer ( 300 m ) passe a 400 m avec une
    lunette x 4 ; un chef HK416 + RCO ( 500 m ) tombe a 300 m quand on lui demonte l optique."""
    table = np.array([[M.portee_utile_couple(a.nom, o.nom) for o in M.OPTIQUES] for a in M.ARMES])
    exact_table = bool((table == np.minimum.outer(M.PORTEE_ARME, M.PORTEE_OPTIQUE)).all())
    w, p = _monde(0)
    d = p.domaine(M.DOMAINE); E = d.eff; parc = p.socle.parc
    rows = M._lignes(d)
    ids = E["hid"][rows]
    pu = M.portee_utile(p, ids)
    attendu = np.zeros(len(rows))
    for j, r in enumerate(rows.tolist()):
        a, o = int(E["arme"][r]), int(E["optique"][r])
        if a < 0: continue
        pa = M.ARME[parc.modeles[parc.objets[a].modele].nom].portee_m
        po = M.OPTIQUE[parc.modeles[parc.objets[o].modele].nom].portee_m if o >= 0 else M.OPTIQUE["fer"].portee_m
        attendu[j] = min(pa, po)
    exact_monde = bool((pu == attendu).all())
    payes = (M.portee_utile_couple("m4a1", "aco") == 400 and M.portee_utile_couple("g3a3", "lunette_x10") == 400
             and M.portee_utile_couple("glock17", "fer") == 50)
    fus = int(E["hid"][rows[(E["spec"][rows] == M.FUSILIER) & (E["arme_m"][rows] == M.IDX_ARME["g3a3"])][0]])
    chef = int(E["hid"][rows[E["spec"][rows] == M.CHEF][0]])
    avant = (float(M.portee_utile(p, [fus])[0]), float(M.portee_utile(p, [chef])[0]))
    apres = (M.monter_optique(p, fus, "rco_x4"), M.monter_optique(p, chef, "fer"))
    controle = avant == (300.0, 500.0) and apres == (400.0, 300.0) and not M.anomalies(p)
    vals, nb = np.unique(pu, return_counts=True)
    ok = exact_table and exact_monde and payes and controle
    return ok, (f"table exacte {exact_table} ; {len(rows)} tireurs exacts {exact_monde} ( portees "
                f"{dict(zip(vals.astype(int).tolist(), nb.tolist()))} ) ; M4+ACO, G3+x10, Glock+fer {payes} ; fusilier "
                f"{avant[0]:.0f} -> {apres[0]:.0f} m avec RCO, chef {avant[1]:.0f} -> {apres[1]:.0f} m sans optique ; "
                f"anomalies {len(M.anomalies(p))}")


# ================================================================== la conservation et ses falsificateurs
def test_conservation():
    """8 jours, 2 500 habitants ( cinq jours de tir imposes a chaque compagnie : les armureries passent sous leur
    seuil et importent ). Au Parc, chaque modele du domaine est
    exact ( sources - puits ) ; le socle tient ; aucune anomalie. Munitions : pour chaque bien, ce que le grand livre a
    vu consommer = ce que le domaine a compte ( tirs declares ), et les stocks = depart + entrees - sorties. Armes et
    vehicules : autant de vivants qu au depart, plus ce qui a ete achete. Falsificateurs : une arme creee sans
    proprietaire se voit ( alors que le Parc, lui, est exact ) ; 10 cartouches retirees a la main d une armurerie se
    voient ( domaine et socle ) ; une arme dotee a deux soldats se voit."""
    w, p = _monde(0)
    d = p.domaine(M.DOMAINE); parc = p.socle.parc; L = p.socle.livre
    mes = sorted(d.idx_parc)
    n0 = {m: parc.vivants[m] for m in mes}
    imp0 = {m: parc.comptes[m]["importe"] for m in mes}
    flux0 = {b: L.flux["consomme"].get(b, 0.0) for b in M.NOMS_MUNITIONS}
    for c in M.compagnies(p): M.imposer_activite(p, c, "instruction_tir", 5)
    T.jours(w, 8)
    ecarts_parc = {parc.modeles[m].nom: v for m, v in ((m, parc.verifier()[parc.modeles[m].nom]) for m in mes) if v}
    tenue, msg = p.socle.conservation.tenue()
    anom = M.anomalies(p)
    tire = {b: L.flux["consomme"].get(b, 0.0) - flux0[b] for b in M.NOMS_MUNITIONS}
    compte = {b: math.fsum(v for (bb, m), v in d.sorties.items() if bb == b) for b in M.NOMS_MUNITIONS}
    munitions_ok = all(abs(tire[b] - compte[b]) <= 1e-9 * max(1.0, compte[b]) for b in M.NOMS_MUNITIONS)
    achetes = {m: parc.comptes[m]["importe"] - imp0[m] for m in mes}
    vivants_ok = all(parc.vivants[m] == n0[m] + achetes[m] - parc.comptes[m]["detruit"] - parc.comptes[m]["rebut"]
                     for m in mes)
    base = d.armureries[0]
    arme = parc.creer(d.mids["g3a3"], None, base.lieu, "initial", p.pas)
    vu_arme = ("arme_sans_proprietaire", arme.id) in M.anomalies(p) and not any(parc.verifier().values())
    parc.sortir(arme, "rebut")
    bid = d.bids["mun_762"]
    arm = next(a for a in d.armureries if a.stock[bid] > 10)
    arm.stock._retirer(bid, 10.0)
    vu_mun = any(a[0] == "munition_hors_consommation" and a[1][0] == "mun_762" for a in M.anomalies(p))
    vu_socle = not p.socle.conservation.tenue()[0]
    arm.stock._ajouter(bid, 10.0)
    E = d.eff; rows = M._lignes(d)
    r1, r2 = rows[E["arme"][rows] >= 0][:2].tolist()
    o2 = int(E["arme"][r2]); E["arme"][r2] = E["arme"][r1]
    vu_double = any(a[0] == "arme_doublee" for a in M.anomalies(p))
    E["arme"][r2] = o2
    rendu = not M.anomalies(p) and p.socle.conservation.tenue()[0]
    importe = sum(d.entrees.get(b, 0.0) for b in M.NOMS_MUNITIONS)
    ok = (not ecarts_parc and tenue and not anom and munitions_ok and vivants_ok and vu_arme and vu_mun and vu_socle
          and vu_double and rendu and sum(compte.values()) > 0 and importe > 0)
    return ok, (f"Parc exact {not ecarts_parc} {ecarts_parc or ''}; {msg} ; anomalies {len(anom)} {anom[:3]} ; tire "
                f"{ {b: round(v) for b, v in compte.items() if v} } = grand livre {munitions_ok}, importe {importe:.0f} "
                f"pour {d.depenses['munitions']:.0f} dr ; vivants = depart + "
                f"achats {vivants_ok} ( achats {sum(achetes.values())} ) ; arme sans proprietaire vue {vu_arme} ; 10 "
                f"cartouches retirees a la main vues domaine {vu_mun} socle {vu_socle} ; arme doublee vue {vu_double} ; "
                f"remis : propre {rendu}")


# ================================================================== le soldat : controles positifs
def test_instruction_et_repos():
    """Controle positif, mondes apparies apres 2 jours, la compagnie la plus nombreuse : A au repos, B au tir, C a la
    marche, 3 jours imposes. Ecart du tir moyen B - A >= +0,03 ; de l endurance C - A >= +0,03 ; de la fatigue A - B
    <= -0,10 et A - C <= -0,10 ; B a consomme des munitions a sa base, A non ; les autres compagnies ne bougent pas
    ( ecart max <= 1e-12 )."""
    w0, p0 = _monde(2)
    d0 = p0.domaine(M.DOMAINE)
    X = max(M.compagnies(p0), key=lambda c: (M.effectif(p0, c), -c))
    snap = pickle.dumps(w0)
    mondes = [pickle.loads(snap) for _ in range(3)]
    for w_, a in zip(mondes, ("repos", "instruction_tir", "marche")):
        M.imposer_activite(w_.pays, X, a, 3)
    base = w0.carte.par_n[int(d0.unites["base"][X])].id
    conso0 = [sum(v for (b, m), v in w_.pays.domaine(M.DOMAINE).sorties.items() if m == "tir_instruction") for w_ in mondes]
    for w_ in mondes: T.jours(w_, 3)
    def moy(w_, k, c):
        pp = w_.pays; ids = M.membres(pp, c, actifs_seulement=True)
        return float(M.competences(pp, ids)[k].mean())
    tir = [moy(w_, "tir", X) for w_ in mondes]
    end = [moy(w_, "endurance", X) for w_ in mondes]
    fat = [moy(w_, "fatigue", X) for w_ in mondes]
    conso = [sum(v for (b, m), v in w_.pays.domaine(M.DOMAINE).sorties.items() if m == "tir_instruction") - c0
             for w_, c0 in zip(mondes, conso0)]
    autres = [c for c in M.compagnies(p0) if c != X and M.effectif(p0, c) > 0]
    ecart = max(abs(moy(mondes[k], q, c) - moy(mondes[0], q, c)) for c in autres for k in (1, 2)
                for q in ("tir", "endurance", "fatigue"))
    arm_a = mondes[0].pays.domaine(M.DOMAINE); arm_b = mondes[1].pays.domaine(M.DOMAINE)
    ok = (tir[1] - tir[0] >= 0.03 and end[2] - end[0] >= 0.03 and fat[0] - fat[1] <= -0.10 and fat[0] - fat[2] <= -0.10
          and conso[1] > conso[0] and ecart <= 1e-12)
    return ok, (f"compagnie {X} ( {M.effectif(p0, X)} hommes, {base} ) : tir repos/tir/marche "
                f"{tir[0]:.3f}/{tir[1]:.3f}/{tir[2]:.3f}, endurance {end[0]:.3f}/{end[1]:.3f}/{end[2]:.3f}, fatigue "
                f"{fat[0]:.3f}/{fat[1]:.3f}/{fat[2]:.3f} ; munitions de tir du pays {conso[0]:.0f}/{conso[1]:.0f}/"
                f"{conso[2]:.0f} ; autres compagnies ecart max {ecart:.1e}")


# ================================================================== la conscription
def test_conscription():
    """10 000 habitants, 12 jours. Chaque incorpore est un homme de 19 a 28 ans sans formation militaire ; aucune femme,
    aucun moins de 19 ans parmi les conscrits. Controle positif ( monde B, apres 2 jours ) : trois hommes civils hors etudes et sans
    formation a qui l on donne 19 ans sont appeles ( incorpores ou exemptes ) au matin qui suit ; trois femmes au meme
    age, un homme de 19 ans etudiant ( sursis ) et un de 18 ans ne le sont pas. Liberation : un
    conscrit dont les 12 mois sont poses a aujourd hui quitte les effectifs le lendemain, garde sa formation militaire et
    revient au marche du travail ( chomeur, sans indemnite ). Les lits des casernes ne sont jamais depasses par les
    conscrits."""
    w0, p0 = _monde(2, echelle=20)
    snap = pickle.dumps(w0)
    wa = pickle.loads(snap); wb = pickle.loads(snap); pb = wb.pays; db = pb.domaine(M.DOMAINE)
    tb = wb.table; n = tb.n; col = pb.colonnes["habitant"]
    age = (pb.jour - col["naissance_j"][:n]) / POP.JOURS_AN
    viv = tb.vivant[:n] == 1
    civils = viv & (col["ar_rang"][:n] < 0) & (col["ar_appel"][:n] == M.PAS_APPEL) \
        & ((col["tr_qualifs"][:n] & TR.BIT["formation_militaire"]) == 0) & (tb.statut[:n] != PO.ABSENT)
    # des adultes civils sans formation militaire, hors etudes ( le domaine 4 remet a l etude un « enfant » de 16 a 19
    # ans chaque matin et donne la formation a 85 % des hommes qui sortent des etudes : un adulte ne bouge pas )
    adultes = np.nonzero(civils & (age >= 30) & (age < 45) & (col["tr_statut"][:n] != TR.ETUDIANT)
                         & ~np.isin(tb.role[:n], [PO.CODE_ROLE[r] for r in M.ROLES_NON_APPELES + ("enfant",)]))[0]
    hommes = adultes[col["sexe"][adultes] == POP.HOMME]; femmes = adultes[col["sexe"][adultes] == POP.FEMME]
    h_ok, f_ok, h18 = hommes[:3], femmes[:3], hommes[3:4]
    # le sursitaire : un vrai etudiant ( role enfant, statut etudiant ), a qui l on donne 19 ans et des etudes longues
    etudiant = np.nonzero(civils & (age >= 16) & (col["sexe"][:n] == POP.HOMME) & (col["tr_statut"][:n] == TR.ETUDIANT)
                          & (tb.role[:n] == PO.CODE_ROLE["enfant"]))[0][:1]
    for i in np.concatenate([h_ok, f_ok, etudiant]).tolist(): col["naissance_j"][i] = pb.jour - int(19.01 * POP.JOURS_AN)
    col["naissance_j"][h18] = pb.jour - int(18.2 * POP.JOURS_AN)
    col["tr_fin_etudes"][etudiant] = pb.jour + 1000
    E = db.eff; rows = M._lignes(db)
    cons = rows[E["conscrit"][rows] == 1]
    libere = int(E["hid"][cons[0]]) if len(cons) else -1
    if libere >= 0: E["fin_j"][cons[0]] = pb.jour
    _jusqu_a(wb, 7.0)
    appeles = all(col["ar_appel"][i] in (M.APPELE, M.EXEMPTE) for i in h_ok.tolist())
    pas_appeles = all(col["ar_appel"][i] == M.PAS_APPEL for i in np.concatenate([f_ok, etudiant, h18]).tolist())
    lib_ok = (libere >= 0 and col["ar_rang"][libere] < 0 and (col["tr_qualifs"][libere] & TR.BIT["formation_militaire"]) > 0
              and col["tr_statut"][libere] == TR.CHOMEUR and libere not in pb.domaine("travail").indemnites)
    T.jours(wa, 10)
    pa = wa.pays; da = pa.domaine(M.DOMAINE); ca = pa.colonnes["habitant"]; ta = wa.table
    E = da.eff; rows = M._lignes(da); cons = rows[E["conscrit"][rows] == 1]
    h = E["hid"][cons]
    ages_c = np.array([a for (_, _, _, a) in da.incorpores])
    sexes_ok = bool((ca["sexe"][h] == POP.HOMME).all()) and all(ca["sexe"][i] == POP.HOMME for _, i, _, _ in da.incorpores)
    ages_ok = len(ages_c) > 0 and bool(((ages_c >= M.AGE_APPEL) & (ages_c < M.AGE_MAX_SURSIS)).all())
    libres = M._lits_libres(pa, da)
    lits_ok = all(v >= 0 for v in libres.values())
    en_service, instr, exemptes, inc, lib = M.conscrits(pa)
    ok = appeles and pas_appeles and len(etudiant) == 1 and lib_ok and sexes_ok and ages_ok and lits_ok
    return ok, (f"12 jours : {inc} incorpores ( ages {ages_c.min() if len(ages_c) else 0:.1f}-"
                f"{ages_c.max() if len(ages_c) else 0:.1f} ), {en_service} conscrits en service dont {instr} en instruction, "
                f"{exemptes} exemptes, {lib} liberes ; hommes seulement {sexes_ok}, 19-28 ans {ages_ok} ; controle : 3 "
                f"hommes de 19 ans appeles {appeles}, femmes, etudiant et 18 ans non {pas_appeles} ; liberation {lib_ok} ; "
                f"lits {lits_ok} ; vise grec {pa.domaine(M.DOMAINE).vise.get('conscrits', 0):.0f} conscrits")


# ================================================================== les patrouilles ( methode reprise du moteur )
def test_patrouilles():
    """Controle positif, mondes apparies apres 2 jours : A, toutes les compagnies patrouillent un jour ; B, toutes au
    repos. A : au moins 80 % des 12 patrouilles tenues, et le carburant note par le moteur = km x consommation du
    vehicule parti ( M1114 : 21,4 l aux 100 km ), a 1e-9 pres ; B : 0 patrouille, toutes annulees pour
    « aucune_troupe ». Les compteurs du moteur ( patrouilles_jour ) disent la meme chose que le domaine."""
    w0, p0 = _monde(2)
    snap = pickle.dumps(w0)
    wa, wb = pickle.loads(snap), pickle.loads(snap)
    for w_, a in ((wa, "patrouille"), (wb, "repos")):
        for c in M.compagnies(w_.pays): M.imposer_activite(w_.pays, c, a, 1)
    jour = wa.jour
    _jusqu_a(wa, 21.0); _jusqu_a(wb, 21.0)
    ev_a = [e for e in wa.evenements if e["jour"] == jour and e["type"] in ("patrouille", "patrouille_annulee")]
    ev_b = [e for e in wb.evenements if e["jour"] == jour and e["type"] in ("patrouille", "patrouille_annulee")]
    faites = [e for e in ev_a if e["type"] == "patrouille"]
    pa = wa.pays; da = pa.domaine(M.DOMAINE)
    carb_ok = True
    for e in faites:
        km, _ = M._km_patrouille(pa, wa.carte.lieux[e["base"]].n)
        att = [round(km * v.unites_par_km, 2) for v in M.VEHICULES]
        if e["carburant"] not in att: carb_ok = False
    compteurs = sum(f for f, a in wa.patrouilles_jour.values()) == len(faites)
    b_ok = (not [e for e in ev_b if e["type"] == "patrouille"]
            and all(e.get("cause") == "aucune_troupe" for e in ev_b) and len(ev_b) == 2 * len(wb.carte.de_type("base")))
    tot = 2 * len(wa.carte.de_type("base"))
    ok = len(faites) >= 0.8 * tot and carb_ok and compteurs and b_ok
    causes = sorted({e.get("cause") for e in ev_a if e["type"] == "patrouille_annulee"})
    return ok, (f"A : {len(faites)}/{tot} patrouilles ( annulees : {causes} ), carburant = km x consommation {carb_ok}, "
                f"compteurs du moteur {compteurs} ; B : {len(ev_b)} annulees, aucune troupe {b_ok}")


# ================================================================== la decision
def test_decision():
    """Porte de decision : 60 compagnies, 21 jours, chaque commandant decide au hasard ( scenario_compagnies ). Part du
    choix >= 0,01 et p de permutation < 0,05, avec au moins 5 notes par action et par jour sur 5 jours au moins. Regle
    et temoin ( toujours le tir ) : notes moyennes rapportees ; dans le monde ( 2 500 habitants, 6 jours ), la regle
    decide chaque jour pour chaque compagnie."""
    dec = M.scenario_compagnies(n=60, jours=21, mode="hasard")
    e2, pp = dec.part_du_choix(), dec.p_permutation()
    par_jour = {}
    for (j, a), (nb, s, q) in dec.stats.items(): par_jour.setdefault(j, []).append(nb)
    jours_ok = sum(1 for v in par_jour.values() if len(v) == len(M.ACTIONS) and min(v) >= 5)
    def moy(dc):
        na = dc.notes_par_action()
        return sum(k * m for k, m in na.values()) / max(1, sum(k for k, _ in na.values()))
    regle = M.scenario_compagnies(n=60, jours=21, mode="regle")
    temoin = M.scenario_compagnies(n=60, jours=21, mode="temoin")
    w, p = _monde(6)
    dm = p.domaine(M.DOMAINE).decideur
    tenues = getattr(w, "patrouilles_faites", 0) / max(1, getattr(w, "patrouilles_faites", 0) + getattr(w, "patrouilles_annulees", 0))
    monde_ok = dm.n_decisions >= 6 * len(M.compagnies(p))
    ok = e2 >= 0.01 and pp < 0.05 and jours_ok >= 5 and monde_ok
    na = {k: (nb, round(v, 3)) for k, (nb, v) in dec.notes_par_action().items()}
    nm = {k: (nb, round(v, 3)) for k, (nb, v) in dm.notes_par_action().items()}
    return ok, (f"hasard : {dec.n_decisions} decisions, part du choix {e2:.3f}, p {pp:.3f}, {jours_ok} jours a 5 notes "
                f"par action ; notes {na} ; moyennes regle {moy(regle):.3f}, temoin {moy(temoin):.3f}, hasard "
                f"{moy(dec):.3f} ; monde : {dm.n_decisions} decisions de la regle, notes {nm}, patrouilles tenues {tenues:.0%}")


def test_api_26_27():
    """L API des domaines 26 et 27, sur 2 500 habitants apres 2 jours ( et la medecine pour les blessures ). Tirer 100
    coups au combat : le stock baisse de 100, le grand livre et le domaine le comptent, aucune anomalie. Transferer 50
    coups d une armurerie a une autre : le total ne bouge pas. Detruire l arme d un soldat : le Parc la compte au puits
    detruit, reste exact, le soldat n a plus d arme ( portee 0 ). Protections : plaque III sur le thorax contre un fusil
    = 0,15, casque sur la tete contre un fusil = 1, rien sur un membre = 1. La detection d une unite est celle de son
    meilleur guetteur ( connaissance de camp ). Un tir de G3 au thorax d un soldat a plaque III ne laisse qu une
    contusion ( ISS <= 1 ) ; au membre, sans protection, une lesion d ISS >= 9.
    26/09, premiere mesure : la porte disait « ne le blesse pas » et l API passait 3 100 J x 0,15 = 465 J au bareme du
    domaine 16 ( AIS 3 au thorax, ISS 9 ). Les deux etaient faux : une plaque qui arrete la balle laisse une contusion
    derriere le blindage, pas rien et pas une plaie ; l API la modele desormais ( AIS 1 ) et la porte le dit."""
    w, p = T.monde([M.DOMAINE, "medecine"], 11, 5)
    T.jours(w, 2)
    d = p.domaine(M.DOMAINE); parc = p.socle.parc; L = p.socle.livre
    b0, b1 = d.armureries[0].lieu, d.armureries[1].lieu
    s0 = M.stocks_munitions(p, b0)[b0]["mun_762"]; f0 = L.flux["consomme"].get("mun_762", 0.0)
    q = M.tirer(p, b0, "mun_762", 100.0)
    tir_ok = (q == 100.0 and M.stocks_munitions(p, b0)[b0]["mun_762"] == s0 - 100.0
              and abs(L.flux["consomme"]["mun_762"] - f0 - 100.0) < 1e-9 and d.sorties[("mun_762", "tir_combat")] == 100.0)
    tot = sum(v["mun_556"] for v in M.stocks_munitions(p).values())
    tr = M.transferer_munitions(p, b0, b1, "mun_556", 50.0)
    transfert_ok = tr == 50.0 and sum(v["mun_556"] for v in M.stocks_munitions(p).values()) == tot
    E = d.eff; rows = M._lignes(d)
    r = int(rows[(E["spec"][rows] == M.FUSILIER) & (E["arme"][rows] >= 0)][0]); hid = int(E["hid"][r])
    oid = int(E["arme"][r]); m = parc.objets[oid].modele; det0 = parc.comptes[m]["detruit"]
    M.perdre_objet(p, oid)
    perte_ok = (parc.comptes[m]["detruit"] == det0 + 1 and not any(parc.verifier().values())
                and float(M.portee_utile(p, [hid])[0]) == 0.0)
    g = next(int(E["hid"][x]) for x in rows.tolist() if E["protection"][x] == M.IDX_PROTECTION["plaque_iii"])
    mult_ok = (M.multiplicateur_letalite(p, g, "thorax", "fusil") == 0.15
               and M.multiplicateur_letalite(p, g, "tete", "fusil") == 1.0
               and M.multiplicateur_letalite(p, g, "membre", "fusil") == 1.0)
    u = next(c for c in M.compagnies(p) if M.effectif(p, c) > 0)
    ids = M.membres(p, u, actifs_seulement=True)
    det = M.detection_unite(p, u); det_ok = det == float(M.perception(p, ids)[1].max()) and det > 0
    nuit_ok = M.detection_unite(p, u, nuit=True) < det
    prot = M.blesser_soldat(p, g, "thorax", "g3a3")
    nu = M.blesser_soldat(p, g, "membre", "g3a3")
    bless_ok = prot[1] <= 1 and nu[0] is not None and nu[1] >= 9
    radios, portee = M.radios(p, d.armee_u)
    anom = M.anomalies(p)
    ok = tir_ok and transfert_ok and perte_ok and mult_ok and det_ok and nuit_ok and bless_ok and not anom and portee > 0
    return ok, (f"tirer {tir_ok} ; transferer {transfert_ok} ; arme detruite {perte_ok} ; multiplicateurs {mult_ok} ; "
                f"detection de l unite {u} {det:.0f} m de jour ( meilleur guetteur {det_ok} ), de nuit "
                f"{M.detection_unite(p, u, nuit=True):.0f} m ; ISS sous plaque {prot[1]}, au membre {nu[1]} ; radios "
                f"{radios} ( portee {portee:.0f} km ) ; anomalies {len(anom)} ; chaine du soldat "
                f"{[c[0] for c in M.chaine_de_commandement(p, hid)]} ; grade {M.grade(p, hid)} ; {M.classname(p, hid)}")


def test_pays_vivable():
    return T.porte_commune(M.DOMAINE)


# ================================================================== le cout
class _Chrono:
    __slots__ = ("f", "t")

    def __init__(self, f): self.f, self.t = f, 0.0

    def __call__(self, *a):
        t0 = time.perf_counter(); self.f(*a); self.t += time.perf_counter() - t0


def test_loi_de_programmation():
    """L armee du budget ( 27/09, « l Etat doit pouvoir construire une armee avec un budget, comme toute nation » ).
    2 500 habitants. LOI : les soldes de la defense valent PART_PERSONNEL_DEFENSE de PART_DEFENSE_DEPENSES des depenses
    publiques votees ( au centime pres ), et l effectif de carriere paye est ( soldes - appeles x solde d appele ) / cout
    moyen. APPELE : un incorpore porte la solde de service ( SOLDE_CONSCRIT_HORAIRE, sous le SMIC ). DEPARTS : le 1er
    juillet ( jour 16 ), le monde E1 a plus de militaires de carriere que la loi n en paie : il en part au moins un et au
    plus 2 % ( arrondi ), les plus ages d abord. CONTROLES POSITIFS : une part doublee paie plus du double de carriere ;
    une part de 50 % paie tout le monde, et personne ne part."""
    w, p = _monde(0)
    d = M._dom(p); b = p.domaine("etat").budget
    autres = math.fsum(v for (l, _), v in b.credits.items() if l != "defense")
    s = M.PART_DEFENSE_DEPENSES
    ok_credits = abs(b.credits[("defense", "personnel")] - M.PART_PERSONNEL_DEFENSE * s / (1.0 - s) * autres) < 1e-6 * max(1.0, autres)
    v = M.effectifs_vises(p)
    moy = (1 - M.PART_OFFICIERS) * M.solde_annuelle(p, "soldat") + M.PART_OFFICIERS * M.solde_annuelle(p, "officier")
    attendu = max(0.0, (d.loi["personnel_an"] - v["conscrits"] * M.solde_conscrit(p)) / moy)
    ok_paye = v["budget"] and abs(v["carriere"] - attendu) < 1e-6
    # controle positif : la meme loi a part double
    try:
        M.PART_DEFENSE_DEPENSES = 2.0 * s; d.loi_vue = None; M._loi_de_programmation(p, d)
        double = M.effectifs_vises(p)["carriere"]
    finally:
        M.PART_DEFENSE_DEPENSES = s; d.loi_vue = None; M._loi_de_programmation(p, d)
    ok_double = double > 2.0 * v["carriere"]
    # l appele et le plan de departs
    E = d.eff
    car0 = int((E["conscrit"][M._lignes(d)] == 0).sum())
    T.jours(w, 17)
    rows = M._lignes(d)
    appeles = E["hid"][rows[E["conscrit"][rows] == 1]]
    ok_solde = len(appeles) > 0 and bool(np.all(np.abs(p.col("habitant", "tr_taux")[appeles] - M.SOLDE_CONSCRIT_HORAIRE) < 1e-12))
    ok_departs = 1 <= d.departs <= max(1, int(M.DEPARTS_MAX_MOIS * car0))
    # controle positif : une part de 50 % paie tout le monde, personne ne part
    w2, p2 = _monde(0)
    d2 = M._dom(p2)
    try:
        M.PART_DEFENSE_DEPENSES = 0.5; d2.loi_vue = None; M._loi_de_programmation(p2, d2)
        T.jours(w2, 17)
        riche = d2.departs
    finally:
        M.PART_DEFENSE_DEPENSES = s
    ok = ok_credits and ok_paye and ok_double and ok_solde and ok_departs and riche == 0
    return ok, (f"credits de soldes {b.credits[('defense', 'personnel')]:.0f} pour {M.PART_PERSONNEL_DEFENSE:.2f} x {s:.3f} des depenses : "
                f"{ok_credits} ; carriere payee {v['carriere']:.1f} ( calcul {attendu:.1f} ), a part double {double:.1f} ; "
                f"{len(appeles)} appeles a la solde de service {ok_solde} ; departs au 1er juillet {d.departs} sur {car0} de carriere "
                f"( au plus {max(1, int(M.DEPARTS_MAX_MOIS * car0))} ) ; a 50 % : {riche} depart")


def test_cout():
    """Coeur Rust. A 10 000 habitants, les routines du domaine ( et les patrouilles et le ravitaillement repris au
    moteur ) coutent au plus 25 % d une journee du moteur seul. Installer l armee a 100 000 habitants ( ses dependances
    deja la ) coute au plus 15 fois l installation a 10 000 ( lineaire : ~ x10 )."""
    coeur = W.COEUR is not None
    w0 = W.Monde(echelle=20); T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    w, p = T.monde([M.DOMAINE], 11, 20)
    T.jours(w, 1)
    chronos = []
    for minute, lst in p.routines.items():
        for i, (o, dom, f) in enumerate(lst):
            if dom == M.DOMAINE:
                c = _Chrono(f); lst[i] = (o, dom, c); chronos.append(c)
    for nom in ("patrouilles", "ravitailler_bases"):
        c = _Chrono(getattr(w, nom)); setattr(w, nom, c); chronos.append(c)
    T.jours(w, 2)
    propre = sum(c.t for c in chronos) / 2
    deps = sorted(set(P.fermeture([M.DOMAINE])) - {M.DOMAINE}, key=P.RANG.get)
    def installation(ech):
        wx = W.Monde(echelle=ech); P.installer(wx, deps)
        t = time.perf_counter(); P.installer(wx, [M.DOMAINE]); return time.perf_counter() - t, wx.table.n
    t10, n10 = installation(20); t100, n100 = installation(200)
    ok = coeur and propre <= 0.25 * t_e1 and t100 <= 15 * t10
    return ok, (f"coeur Rust {coeur} ; {w.table.n} habitants : moteur seul {t_e1:.2f} s par jour ; routines propres "
                f"{propre * 1000:.0f} ms, {propre / t_e1:.1%} ; installation {n10} habitants {t10:.3f} s, {n100} habitants "
                f"{t100:.3f} s ( x{t100 / t10:.1f} )")


TESTS = [test_loi_de_programmation, test_effectifs_et_structure, test_portee_utile, test_conservation, test_instruction_et_repos,
         test_conscription, test_patrouilles, test_decision, test_api_26_27, test_pays_vivable, test_cout]
