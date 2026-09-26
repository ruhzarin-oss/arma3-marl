"""Les portes du domaine 26 ( armee B : logistique militaire, renseignement, commandement ).
Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests armee_soutien"""
import math, pickle, time
import numpy as np
from .. import config as C, monde as W
from . import essais as T, pays as P, d15_logistique as LG, d17_hopitaux as HM, d22_medias as MED, d25_armee as A
from . import d26_armee_soutien as M

_CACHE = {}


def _monde(jours=0, echelle=5, graine=11, modes=None):
    """Un monde avec le domaine et ses dependances, apres `jours` jours ; chaque porte en reprend une copie."""
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


def _pas(w, n):
    for _ in range(int(n)): w.pas_suivant()


def _lid(p, b): return p.w.carte.par_n[b].id


def _hq_et_isolee(p):
    """La base de l etat-major de brigade, et la base la plus loin d elle par la route."""
    d = p.domaine(M.DOMAINE); w = p.w
    dep = next(x for x in d.depots if x.niveau == "brigade")
    hq = w.carte.lieux[dep.lieu]
    autres = [b for b in d.bases if b != dep.base]
    x = max(autres, key=lambda b: (w.carte.km_route(hq, w.carte.par_n[b]), b))
    return dep, x


# ================================================================== le grand livre du perimetre militaire
class _Sonde:
    """Autour d une fonction : la variation du perimetre militaire ( M.perimetre ) doit etre exactement la variation des
    flux comptes par le domaine ( M.flux_nets ), plus ce qui entre de l exterieur pendant l appel ( `externe` ). Garde
    le pire ecart par bien."""
    __slots__ = ("f", "p", "externe", "pire", "appels")

    def __init__(self, f, p, externe=None): self.f, self.p, self.externe, self.pire, self.appels = f, p, externe, {}, 0

    def __call__(self, *a):
        p = self.p
        per0, fl0 = M.perimetre(p), M.flux_nets(p)
        ext = self.externe(p) if self.externe is not None else {}
        r = self.f(*a)
        per1, fl1 = M.perimetre(p), M.flux_nets(p)
        self.appels += 1
        for b in per1:
            e = (per1[b] - per0.get(b, 0.0)) - (fl1.get(b, 0.0) - fl0.get(b, 0.0)) - ext.get(b, 0.0)
            tol = 1e-9 * max(1.0, abs(per1[b]))
            if abs(e) > tol and abs(e) > abs(self.pire.get(b, 0.0)): self.pire[b] = e
        return r


def _commandes_armee_arrivant(p):
    """Ce que le moteur fait entrer au stock public de l armee pendant ses arrivees : les commandes publiques ( le
    gouvernement du moteur commande du gazole pour l armee ), qui viennent d un marche, hors du perimetre."""
    out = {}
    for c in p.w.convois:
        if c.motif == "commande_armee" and c.arrivee <= p.w.pas:
            for b, q in c.cargaison.items(): out[b] = out.get(b, 0.0) + q
    return out


def _sonder(p):
    """Pose une sonde sur chaque routine et chaque gestionnaire d echeance du domaine, et sur les arrivees de convois
    ( ou passent ses recepteurs ). Rend les sondes."""
    sondes = []
    for minute, lst in p.routines.items():
        for i, (o, dom, f) in enumerate(lst):
            if dom == M.DOMAINE:
                s = _Sonde(f, p); lst[i] = (o, dom, s); sondes.append(s)
    for t in ("armee_soutien_ordre", "armee_soutien_plan"):
        s = _Sonde(p.gestionnaires[t], p); p.gestionnaires[t] = s; sondes.append(s)
    s = _Sonde(p.w.arrivees, p, _commandes_armee_arrivant); p.w.arrivees = s; sondes.append(s)
    return sondes


def test_conservation():
    """Grand livre des munitions, du carburant et des vivres entre les depots et les garnisons. 2 500 habitants, 7 jours :
    deux jours de paix, puis quatre garnisons au combat ( dont l etat-major ) et une en alerte. Sonde autour de chaque
    routine et echeance du domaine et des arrivees de convois : la variation du perimetre militaire ( depots,
    armureries, garnisons, stock public de l armee, convois militaires et lots ) = les flux comptes par le domaine, au
    milliardieme pres, pour CHAQUE bien et CHAQUE appel. La conservation du socle tient ; les anomalies des domaines 25
    ( munition_hors_consommation ), 15 ( transit ) et 26 sont vides. L instrument voit des flux : au moins 5
    livraisons militaires, une consommation de campagne de gazole, de munitions et de vivres. Falsificateurs : 5 unites
    de gazole posees a la main dans une garnison pendant un appel sonde sont vues ( ecart 5 ) ; 100 cartouches deplacees
    d un depot a une armurerie sans le dire au domaine 25 sont vues par ses anomalies."""
    w, p = _monde(1)
    d = p.domaine(M.DOMAINE)
    sondes = _sonder(p)
    T.jours(w, 2)
    dep, x = _hq_et_isolee(p)
    for b in d.bases[:4] if dep.base in d.bases[:4] else [dep.base] + d.bases[:3]:
        M.poser_posture(p, _lid(p, b), "combat")
    M.poser_posture(p, _lid(p, d.bases[-1]), "alerte")
    T.jours(w, 4)
    pire = {}
    for s in sondes:
        for b, e in s.pire.items():
            if abs(e) > abs(pire.get(b, 0.0)): pire[b] = e
    appels = sum(s.appels for s in sondes)
    tenue, msg = p.socle.conservation.tenue()
    an26, an25, an15 = M.anomalies(p), A.anomalies(p), LG.anomalies_transit(p)
    fl = d.flux
    conso = {c: math.fsum(q for (b, s, m), q in fl.items() if s == "sortie" and m in ("consommation_campagne", "tir_combat")
                          and (b == "carburant" if c == 0 else b == M.RATION if c == 2 else b in A.NOMS_MUNITIONS))
             for c in range(3)}
    livrees = sum(1 for e in p.socle.journal.recents if e["type"] == "convoi_militaire")
    # falsificateur 1 : du gazole pose a la main pendant un appel sonde
    lid = _lid(p, d.bases[0])
    def tricher(): w.garnisons[lid]["carburant"] += 5.0
    s = _Sonde(tricher, p); s()
    vu_triche = abs(s.pire.get("carburant", 0.0) - 5.0) < 1e-6
    # falsificateur 2 : des cartouches livrees a une armurerie sans le dire au domaine 25
    arm = A.armurerie(p, lid)
    q = p.socle.livre.deplacer(dep.stock, arm.stock, d.ids["mun_762"], 100.0, "livraison_militaire")
    vu_25 = any(t == "munition_hors_consommation" and x_[0] == "mun_762" for t, x_ in A.anomalies(p))
    ok = (not pire and tenue and not an26 and not an25 and not an15 and livrees >= 5 and min(conso.values()) > 0
          and vu_triche and vu_25 and q == 100.0)
    return ok, (f"{appels} appels sondes, pire ecart {pire or 'aucun'} ; conservation {msg} ; anomalies 26 {an26[:2]} 25 "
                f"{an25[:2]} 15 {an15[:2]} ; {livrees} convois militaires ; consommation gazole {conso[0]:.0f} u, munitions "
                f"{conso[1]:.0f} coups, rations {conso[2]:.0f} ; falsificateurs : gazole a la main {'VU' if vu_triche else 'NON VU'}"
                f" ( ecart {s.pire.get('carburant', 0.0):+.2f} ), cartouches hors domaine 25 {'VUES' if vu_25 else 'NON VUES'}")


# ================================================================== le controle positif : la base isolee
def _rupture_predite(s0, besoins, rotation=0.0):
    """Le premier jour ( relatif ) ou le stock ne couvre plus le besoin, sans aucune livraison : la consommation de midi,
    puis la rotation du soir ( une fraction du stock )."""
    s = s0
    for t, q in enumerate(besoins):
        if s < q * (1 - 1e-9): return t
        s = max(0.0, s - q)
        s -= s * rotation
    return None


def test_isolement():
    """Controle positif. MONDE ( 2 500 habitants ) : toutes les garnisons au combat pendant 5 jours ; la route de la base
    la plus eloignee de l etat-major de brigade est coupee ( Monde.routes_coupees ) et ses compagnies au repos ( ni
    patrouille ni tir du domaine 25 ). Son premier jour de rupture en gazole et en vivres est PREDIT des stocks du
    moment de la coupure, des besoins du jour et de la rotation des rations, sans aucune livraison : il doit etre
    observe exactement ce jour-la ( 0 jour d ecart ), et la base ne recoit rien ; chaque autre garnison recoit au moins
    un convoi et a moins de jours de rupture en vivres que l isolee. SCENARIO ( la mer ) : mer fermee tout le long, les
    garnisons des autres iles rompent chacune au jour predit par leur stock initial ( 0 ecart sur toutes, toutes
    classes ) ; mer ouverte, elles ont au moins deux fois moins de ruptures."""
    w, p = _monde(1)
    d = p.domaine(M.DOMAINE)
    _jusqu_a(w, 6.5)
    dep, x = _hq_et_isolee(p)
    jours = 5
    for b in d.bases: M.poser_posture(p, _lid(p, b), "combat", jours + 1)
    w.routes_coupees.add(_lid(p, x))
    for c in A.compagnies(p):
        if int(A._dom(p).unites["base"][c]) == x: A.imposer_activite(p, c, "repos", jours + 1)
    j0 = p.jour
    s0 = None; besoins_c, besoins_v = [], []
    for t in range(jours):
        _jusqu_a(w, 11 + 50 / 60)
        nc, _, nv = d.besoins[x]
        if s0 is None:
            sc, _, sv = M._stocks_base(p, d, x); s0 = (sc, sv)
        besoins_c.append(nc); besoins_v.append(nv)
        _jusqu_a(w, 6.5)
    pred_c = _rupture_predite(s0[0], besoins_c)
    pred_v = _rupture_predite(s0[1], besoins_v, 1.0 / M.CONSERVATION_RATION_J)
    rupt = [(j - j0, b, c) for j, b, c in d.ruptures]
    obs_c = min((t for t, b, c in rupt if b == x and c == M.CARB), default=None)
    obs_v = min((t for t, b, c in rupt if b == x and c == M.VIV), default=None)
    livre_x = x in d.livraisons
    rv = {b: sum(1 for t, bb, c in rupt if bb == b and c == M.VIV) for b in d.bases}
    recus = {b: sum(1 for e in p.socle.journal.recents if e["type"] == "convoi_militaire" and e["vers"] == _lid(p, b)
                    and e["jour"] >= j0) for b in d.bases}
    autres = [b for b in d.bases if b != x]
    monde_ok = (pred_c == obs_c and pred_v == obs_v and obs_c is not None and obs_v is not None and not livre_x
                and all(recus[b] >= 1 for b in autres) and all(rv[b] < rv[x] for b in autres))
    # la mer, dans le scenario
    dec_f, sf = M.scenario_ravitaillement(n_brigades=4, garnisons=10, jours=12, mode="regle", mer_fermee=(0, 99),
                                          p_coupure=0.0, serie=True)
    dec_o, so = M.scenario_ravitaillement(n_brigades=4, garnisons=10, jours=12, mode="regle", mer_fermee=None,
                                          p_coupure=0.0, serie=True)
    ecarts = 0; n_iles = 0
    for i in np.nonzero(sf["ile"])[0].tolist():
        n_iles += 1
        for c in range(3):
            q = sf["besoin"][i, c] * sf["intensite"][i]
            pred = _rupture_predite(sf["stock0"][i, c], [q] * 12)
            obs = next((s["jour"] for s in sf["serie"] if s["manque"][i, c]), None)
            ecarts += pred != obs
    rf = sum(int(s["ruptures"][sf["ile"]].sum()) for s in sf["serie"])
    ro = sum(int(s["ruptures"][so["ile"]].sum()) for s in so["serie"])
    mer_ok = ecarts == 0 and n_iles > 0 and ro * 2 <= rf
    ok = monde_ok and mer_ok
    return ok, (f"monde : base isolee {_lid(p, x)} ( depot {dep.lieu} ) ; rupture gazole predite j+{pred_c} observee "
                f"j+{obs_c}, vivres predite j+{pred_v} observee j+{obs_v} ; livree apres coupure {livre_x} ; convois recus "
                f"{ {_lid(p, b): n for b, n in recus.items()} } ; jours de rupture en vivres "
                f"{ {_lid(p, b): n for b, n in rv.items()} } ; scenario : {n_iles} garnisons d ile, {ecarts} ecart(s) au jour "
                f"predit, mer fermee {rf} ruptures contre {ro} mer ouverte")


# ================================================================== le commandement
def test_transmission():
    """Un ordre arrive avec le delai calcule. 2 500 habitants, 10 h. Du bataillon de la base isolee a sa brigade, sans
    friction : par RADIO, recu 1 pas ( 10 min ) apres son emission ; radios coupees, par TELEPHONE, 2 pas ; radios coupees
    et reseau civil en panne, par ESTAFETTE, au delai recalcule ici ( 15 min + 1,3 x distance a 45 km/h, au pas
    superieur ), strictement plus lent que la radio ; brouillage d un autre camp sur la base : plus de radio. Avec
    frictions, 400 ordres radio : part mal comprise dans [ 1 % ; 10 % ] ( P_MAL 4 %, plus la fatigue ), part retardee
    dans [ 1 % ; 12 % ] ( 5 % ), aucun recu avant son emission, aucun perdu par radio. Un plan de 3 etapes ( emises a
    +2, +6, +12 pas, echeances +4, +8, +14 ) : les trois recues a temps. Un ordre de mouvement pose la destination
    AVANT la marche ; arrivee sans ordre TENIR, l unite compte des heures de dislocation, pas avec."""
    w, p = _monde(1)
    d = p.domaine(M.DOMAINE)
    _jusqu_a(w, 10.0)
    dep, x = _hq_et_isolee(p)
    bat, brig = d.bataillon_de[x], dep.brigade
    def envoyer(contenu="tenir", **kw):
        k = M.emettre_ordre(p, bat, brig, contenu, a=1.0, frictions=False, **kw)
        t0 = w.pas
        for _ in range(60):
            if d.ordres["etat"][k] == M.RECU: break
            w.pas_suivant()
        o = M.ordre(p, k)
        return o["moyen"], (o["recu"] - t0) if o["recu"] is not None else None, o
    m1, d1, _ = envoyer()
    M.couper_radios(p, bat); M.couper_radios(p, brig)
    m2, d2, _ = envoyer()
    R = p.domaine("medias").reseau
    R.panne_fin[:] = 1e9; R.ok[:] = False
    x0, y0, _ = M.position(p, 0, bat); x1, y1, _ = M.position(p, 0, brig)
    km = math.hypot(x1 - x0, y1 - y0) / 1000.0
    attendu = max(1, math.ceil((M.PREPARATION_ESTAFETTE_MIN + 1.3 * km / 45.0 * 60.0) / 10.0 - 1e-9))
    m3, d3, _ = envoyer()
    R.panne_fin[:] = -1.0; R.ok[:] = True
    M.couper_radios(p, bat, coupe=False); M.couper_radios(p, brig, coupe=False)
    M.poser_camp(p, "rouge", taille=10)
    M.brouiller(p, "rouge", *M.position(p, 0, bat)[:2], 5.0, 24)
    m4, d4, _ = envoyer()
    d.brouillages.clear()
    # frictions
    ks = [M.emettre_ordre(p, bat, brig, "tenir", a=1.0) for _ in range(400)]
    T.jours(w, 1)
    Od = d.ordres
    mal = float(np.mean([Od["compris"][k] == 0 for k in ks])); ret = float(np.mean([Od["retard"][k] > 0 for k in ks]))
    avant = sum(1 for k in ks if 0 <= Od["t_recu"][k] < Od["t_emis"][k]); perdus = sum(1 for k in ks if Od["etat"][k] == M.PERDU)
    nonrecus = sum(1 for k in ks if Od["etat"][k] != M.RECU)
    # un plan
    t = w.pas
    pl = M.poser_plan(p, brig, [(bat, "tenir", (2.0,), t + 2, t + 4), (bat, "tenir", (2.0,), t + 6, t + 8),
                                (bat, "tenir", (2.0,), t + 12, t + 14)])
    _pas(w, 20)
    ep = M.etat_plan(p, pl)
    plan_ok = len(ep) == 3 and all(e["a_temps"] for e in ep)
    # le mouvement et la dislocation
    comp = next(c for c in A.compagnies(p) if int(A._dom(p).unites["base"][c]) == x)
    xc, yc, _ = M.position(p, 0, comp)
    k = M.emettre_ordre(p, bat, comp, "mouvement", a=xc + 800.0, b=yc, frictions=False)
    _pas(w, 2 * C.PAS_PAR_JOUR // 24 + 12)
    seq = d.ordres_arma[-1][3] if d.ordres_arma else []
    h_sans = d.sans_ordre_h.get((0, comp), 0)
    M.tenir(p, bat, comp, 48)
    _pas(w, 2)
    h0 = d.sans_ordre_h.get((0, comp), 0)
    _pas(w, 18)
    h1 = d.sans_ordre_h.get((0, comp), 0)
    mouv_ok = bool(seq) and seq[0][0] == "setDestination" and h_sans > 0 and h1 == h0 == 0
    ok = (m1 == "radio" and d1 == 1 and m2 == "telephone" and d2 == 2 and m3 == "estafette" and d3 == attendu
          and d3 > d1 and m4 != "radio" and 0.01 <= mal <= 0.10 and 0.01 <= ret <= 0.12 and avant == 0 and perdus == 0
          and nonrecus == 0 and plan_ok and mouv_ok)
    return ok, (f"radio {m1} {d1} pas ; sans radio {m2} {d2} pas ; sans radio ni reseau {m3} {d3} pas pour {attendu} "
                f"attendus ( {km:.1f} km ) ; brouille : {m4} ; 400 ordres radio : mal compris {mal:.1%}, retardes {ret:.1%}, "
                f"recus avant emission {avant}, perdus {perdus}, non recus {nonrecus} ; plan {[(e['recu'], e['echeance']) for e in ep]} ; "
                f"mouvement : {seq[:1]}, dislocation sans ordre {h_sans} h, avec TENIR {h0} puis {h1} h")


# ================================================================== le renseignement
def _guetteurs(p, x):
    comp = next(c for c in A.compagnies(p) if int(A._dom(p).unites["base"][c]) == x)
    return comp, A.membres(p, comp, actifs_seulement=True)


def test_connaissance_de_camp():
    """La connaissance est de camp. 2 500 habitants, 10 h ( jour ). Un camp rouge et un camp vert poses ; une compagnie
    a sa base : UN seul soldat regarde vers l est, les autres vers l ouest. Trois entites rouges : a 150 m a l est
    ( devant le guetteur ), a 50 m au nord ( sur son flanc ), a 900 m a l est ( trop loin ). La premiere est connue du
    camp national ( source observation, observateur = ce soldat, et la cellule du camp au domaine 22 croit le fait,
    source renseignement ) ; les deux autres ne le sont PAS : `connaissance` rend None ( une absence, pas un zero ).
    Individuelle : ce soldat l a vue, aucun autre. Le vert n en sait rien, ni au domaine 26 ni dans sa cellule, meme un
    jour plus tard ( la rumeur ne sort pas d un etat-major ). La meme scene de nuit : rien n est connu a 150 m."""
    w, p = _monde(1)
    d = p.domaine(M.DOMAINE)
    _jusqu_a(w, 10.0)
    dep, x = _hq_et_isolee(p)
    lieu = w.carte.par_n[x]
    M.poser_camp(p, "rouge", {lieu.id: 1.0}, 30)
    M.poser_camp(p, "vert", {lieu.id: 1.0}, 30)
    comp, ids = _guetteurs(p, x)
    x0, y0 = lieu.pos
    ile = w.carte.iles.index(lieu.ile)
    e1 = M.poser_entite(p, "rouge", x0 + 150.0, y0, ile)
    e2 = M.poser_entite(p, "rouge", x0, y0 + 50.0, ile)
    e3 = M.poser_entite(p, "rouge", x0 + 900.0, y0, ile)
    ig = int(np.argmax(A.perception(p, ids)[1]))              # le meilleur guetteur de la compagnie regarde l est
    regards = np.full(len(ids), math.pi); regards[ig] = 0.0
    vus = M.observer(p, M.CAMP_NATIONAL, ids, np.tile([x0, y0], (len(ids), 1)), regards)
    c1, c2, c3 = (M.connaissance(p, M.CAMP_NATIONAL, e) for e in (e1, e2, e3))
    guetteur = int(ids[ig])
    indiv = M.a_vu(p, guetteur); autres = [h for h in ids.tolist() if h != guetteur and M.a_vu(p, h)]
    r = d.conn_idx.get((0, e1)); fid = int(d.conn["fait"][r]) if r is not None else -1
    nat22 = [e for e in MED.croyance(p, M.CAMP_NATIONAL, M.SUJET_PRESENCE) if e["fait"] == fid]
    T.jours(w, 1)
    vert26 = M.connaissance(p, "vert", e1)
    vert22 = [e for e in MED.croyance(p, "vert", M.SUJET_PRESENCE) if e["fait"] == fid]
    # la nuit
    w2, p2 = _monde(1)
    _jusqu_a(w2, 2.0)
    M.poser_camp(p2, "rouge", {lieu.id: 1.0}, 30)
    _, ids2 = _guetteurs(p2, x)
    en = M.poser_entite(p2, "rouge", x0 + 150.0, y0, ile)
    M.observer(p2, M.CAMP_NATIONAL, ids2, np.tile([x0, y0], (len(ids2), 1)), np.zeros(len(ids2)))
    nuit = M.connaissance(p2, M.CAMP_NATIONAL, en)
    portee_jour = float(A.perception(p, ids[ig:ig + 1])[1][0])
    ok = (c1 is not None and c1["source"] == "observation" and c1["observateur"] == guetteur and c2 is None and c3 is None
          and len(indiv) == 1 and indiv[0][1] == e1 and not autres and len(nat22) == 1 and nat22[0]["source"] == "renseignement"
          and vert26 is None and not vert22 and nuit is None and len(vus) == 1)
    return ok, (f"guetteur a {portee_jour:.0f} m de jour ; a 150 m devant : {'connue' if c1 else 'INCONNUE'} "
                f"( {c1['source'] if c1 else '-'}, erreur {M.erreur_position(p, 0, e1) if c1 else float('nan'):.1f} m ) ; flanc 50 m : "
                f"{c2} ; 900 m : {c3} ; vue par {len(indiv)} guetteur, {len(autres)} autre(s) ; cellule nationale : {len(nat22)} "
                f"croyance ( {nat22[0]['source'] if nat22 else '-'} ) ; camp vert : {vert26}, {len(vert22)} croyance ; de nuit a 150 m : {nuit}")


def test_erreur_position():
    """L erreur de position croit avec la distance. Un guetteur qui regarde la cible ( portee forcee a 1 km : on mesure
    la loi d erreur, pas la portee ), 80 observations a chacune des distances 25, 50, 100, 150, 200 et 250 m : l erreur
    moyenne croit a chaque pas ( 5 hausses sur 5 ) et celle de 250 m vaut au moins 3 fois celle de 25 m. Avec l age :
    deux heures plus tard, le rayon d incertitude d une cible qui marche a depasse l erreur a l observation d au moins
    5 km ( 1,4 m/s x 2 h ). La cellule du camp au domaine 22 porte une erreur de lieu en km, lisible par `croyance`
    avec_erreur."""
    w, p = _monde(1)
    _jusqu_a(w, 10.0)
    dep, x = _hq_et_isolee(p)
    lieu = w.carte.par_n[x]; x0, y0 = lieu.pos; ile = w.carte.iles.index(lieu.ile)
    M.poser_camp(p, "rouge", taille=10, visible=False)
    _, ids = _guetteurs(p, x)
    g = ids[:1]
    e = M.poser_entite(p, "rouge", x0 + 25.0, y0, ile)
    moy = []
    for dist in (25.0, 50.0, 100.0, 150.0, 200.0, 250.0):
        err = []
        for k in range(80):
            ang = 2.0 * math.pi * k / 80.0
            M.deplacer_entite(p, e, x0 + dist * math.cos(ang), y0 + dist * math.sin(ang))
            M.observer(p, M.CAMP_NATIONAL, g, [[x0, y0]], [ang], portees=[1000.0])
            err.append(M.erreur_position(p, M.CAMP_NATIONAL, e))
        moy.append(float(np.mean(err)))
    hausses = sum(1 for a, b in zip(moy, moy[1:]) if b > a)
    c0 = M.connaissance(p, M.CAMP_NATIONAL, e)
    _pas(w, 12)
    c2 = M.connaissance(p, M.CAMP_NATIONAL, e)
    cr = [z for z in MED.croyance(p, M.CAMP_NATIONAL, M.SUJET_PRESENCE, avec_erreur=True)]
    ok = hausses == 5 and moy[-1] >= 3 * moy[0] and c2["rayon_m"] - c0["rayon_m"] >= 5000.0 and len(cr) >= 1
    return ok, (f"erreur moyenne ( m ) a 25/50/100/150/200/250 m : {[round(v, 1) for v in moy]} ; {hausses} hausses sur 5 ; "
                f"rayon {c0['rayon_m']:.0f} m puis {c2['rayon_m']:.0f} m deux heures plus tard ; domaine 22 : erreur de lieu "
                f"{cr[0]['erreur_lieu_km'] if cr else None} km")


def test_falsificateur():
    """Les anomalies voient ce qu on pose a la main, et rien dans un monde sain. 2 500 habitants apres 2 jours, un camp
    rouge observe et des ordres recus : aucune anomalie. Puis, chacune sur une copie : une croyance du camp national
    sans source ( croyance_sans_source ), une observation sans guetteur ( observation_sans_guetteur ), un ordre recu un
    pas avant son emission ( ordre_recu_avant_emission ) : chacune vue, et seulement elle."""
    w, p = _monde(2)
    d = p.domaine(M.DOMAINE)
    _jusqu_a(w, 10.0)
    dep, x = _hq_et_isolee(p)
    lieu = w.carte.par_n[x]; x0, y0 = lieu.pos; ile = w.carte.iles.index(lieu.ile)
    M.poser_camp(p, "rouge", taille=10)
    _, ids = _guetteurs(p, x)
    e = M.poser_entite(p, "rouge", x0 + 60.0, y0, ile)
    M.observer(p, M.CAMP_NATIONAL, ids, np.tile([x0, y0], (len(ids), 1)), np.zeros(len(ids)))
    k = M.emettre_ordre(p, d.bataillon_de[x], dep.brigade, "tenir", a=1.0, frictions=False)
    _pas(w, 3)
    sain = M.anomalies(p)
    snap = pickle.dumps(w)
    def essai(poser, attendu):
        w2 = pickle.loads(snap); p2 = w2.pays; d2 = p2.domaine(M.DOMAINE)
        poser(p2, d2)
        an = M.anomalies(p2)
        return [t for t, _ in an] == [attendu], an
    def sans_source(p2, d2):
        r = d2.conn.ajouter(); d2.conn_idx[(0, 99999)] = r
        d2.conn["camp"][r] = 0; d2.conn["cible"][r] = 99999; d2.conn["t"][r] = p2.w.pas; d2.conn["actif"][r] = 1
        d2.conn["source"][r] = M.AUCUNE
    def sans_guetteur(p2, d2):
        r = d2.conn_idx[(0, e)]; d2.conn["observateur"][r] = -1
    def recu_avant(p2, d2):
        d2.ordres["t_recu"][k] = d2.ordres["t_emis"][k] - 1
    r1, a1 = essai(sans_source, "croyance_sans_source")
    r2, a2 = essai(sans_guetteur, "observation_sans_guetteur")
    r3, a3 = essai(recu_avant, "ordre_recu_avant_emission")
    ok = not sain and r1 and r2 and r3 and M.connaissance(p, 0, e) is not None
    return ok, (f"monde sain : {len(sain)} anomalie(s) ; sans source : {a1} ; sans guetteur : {a2} ; recu avant emission : {a3}")


# ================================================================== la decision
def test_decision():
    """Porte de decision : 120 garnisons ( 12 brigades ), 21 jours de crise, mer fermee du jour 4 au jour 14, routes
    coupees au hasard, chaque S4 decide au hasard ( scenario_ravitaillement ). Part du choix >= 0,01 et p de permutation
    < 0,05, avec au moins 5 notes par action et par jour sur 5 jours au moins. Regle ( la plus faible autonomie d abord )
    et temoin ( tout a parts egales ) : notes moyennes rapportees. Dans le monde ( 2 500 habitants, 6 jours ), la regle
    decide chaque matin pour chaque garnison."""
    dec = M.scenario_ravitaillement(mode="hasard")
    e2, pp = dec.part_du_choix(), dec.p_permutation()
    par_jour = {}
    for (j, a), (nb, s, q) in dec.stats.items(): par_jour.setdefault(j, []).append(nb)
    jours_ok = sum(1 for v in par_jour.values() if len(v) == len(M.ACTIONS) and min(v) >= 5)
    def moy(dc):
        na = dc.notes_par_action()
        return sum(k * m for k, m in na.values()) / max(1, sum(k for k, _ in na.values()))
    regle = M.scenario_ravitaillement(mode="regle")
    temoin = M.scenario_ravitaillement(mode="temoin")
    w, p = _monde(6)
    dm = p.domaine(M.DOMAINE).decideur
    monde_ok = dm.n_decisions >= 6 * len(p.domaine(M.DOMAINE).bases)
    ok = e2 >= 0.01 and pp < 0.05 and jours_ok >= 5 and monde_ok
    na = {k: (nb, round(v, 3)) for k, (nb, v) in dec.notes_par_action().items()}
    return ok, (f"hasard : {dec.n_decisions} decisions, part du choix {e2:.3f}, p {pp:.3f}, {jours_ok} jours a 5 notes par "
                f"action ; notes {na} ; moyennes regle {moy(regle):.3f}, temoin {moy(temoin):.3f}, hasard {moy(dec):.3f} ; "
                f"monde : {dm.n_decisions} decisions de la regle, notes {dm.notes_par_action()}")


# ================================================================== l API du domaine 27 et la sante
def test_api_27():
    """L API du domaine 27 sur 2 500 habitants. EVACUATION : un soldat de la base isolee, par helicoptere, arrive au pas
    calcule ( 15 min + aller-retour a 180 km/h + 10 min ) et le kerosene du vol est brule au depot national ; les
    helicopteres occupes, un second part en ambulance, plus lentement. INTERCEPTION : une station d ecoute rouge pres
    de la base ( 3 km ) localise le bataillon qui emet a la radio ( source radio, erreur sous 4 ecarts-types de la
    goniometrie : 5 m + 5 % de la distance ). PATROUILLE :
    une compagnie qui marche vers une entite rouge la trouve ( source patrouille ). POPULATION : une entite rouge posee
    dans un village fait une nouvelle presence_militaire ; en un jour, le camp national en a un contact non identifie
    ( source population ou medias ). Le pont : chaque convoi militaire a une destination et un point de depart propre,
    jamais deux au meme point, et les departs d une meme origine etales ( jamais le meme pas ). `requisitionner_vivres`
    sans agriculture ne fait rien."""
    w, p = _monde(1)
    d = p.domaine(M.DOMAINE); a = A._dom(p)
    _jusqu_a(w, 10.0)
    dep, x = _hq_et_isolee(p)
    lieu = w.carte.par_n[x]; x0, y0 = lieu.pos; ile = w.carte.iles.index(lieu.ile)
    E = a.eff; rows = A._lignes_actives(a)
    hs = E["hid"][rows[E["base"][rows] == x]].tolist()[:2 + M.HELICOS_PAR_BRIGADE]
    kero0 = d.national.stock[d.ids["kerosene"]]
    hop = w.carte.lieux[d.hopital.lieu]
    km = lieu.distance(hop) / 1000.0
    ev = [M.evacuer(p, h) for h in hs]
    attendu = max(1, math.ceil((15.0 + 2.0 * km / 180.0 * 60.0 + 10.0) / 10.0 - 1e-9))
    kero = kero0 - d.national.stock[d.ids["kerosene"]]
    kero_att = M.HELICOS_PAR_BRIGADE * 2.0 * km / 180.0 * 32.0
    moyens = [e["moyen"] if e else None for e in ev]
    etat0 = HM.etat_patient(p, w.habitants[hs[0]])
    _pas(w, attendu)
    etat1 = HM.etat_patient(p, w.habitants[hs[0]])
    evac_ok = (moyens[:M.HELICOS_PAR_BRIGADE] == ["helicoptere"] * M.HELICOS_PAR_BRIGADE and moyens[-1] == "ambulance"
               and ev[0]["pas"] == attendu and ev[-1]["minutes"] > ev[0]["minutes"] and abs(kero - kero_att) < 1e-6
               and etat0 is not None and etat0["etat"] == "transport" and etat1 is not None and etat1["etat"] != "transport")
    # interception
    M.poser_camp(p, "rouge", {lieu.id: 1.0}, 30)
    M.poser_ecoute(p, "rouge", x0 + 3000.0, y0, 20.0, ile)
    bat = d.bataillon_de[x]
    M.emettre_ordre(p, bat, dep.brigade, "tenir", a=1.0, frictions=False)
    ci = M.connaissance(p, "rouge", M.cible_unite(bat))
    xb, yb, _ = M.position(p, 0, bat)
    err_i = math.hypot(ci["x"] - xb, ci["y"] - yb) if ci else None
    inter_ok = ci is not None and ci["source"] == "radio" and err_i < 4.0 * (M.SIGMA0_M + M.K_GONIO * 3000.0)
    # patrouille
    comp, _ = _guetteurs(p, x)
    ep = M.poser_entite(p, "rouge", x0 + 400.0, y0 + 20.0, ile)
    trouve = M.patrouille(p, comp, [(x0, y0), (x0 + 200.0, y0), (x0 + 350.0, y0)])
    cp = M.connaissance(p, M.CAMP_NATIONAL, ep)
    patr_ok = cp is not None and cp["source"] == "patrouille" and any(t[0] == ep for t in trouve)
    # la population
    village = next(l for l in w.carte.par_n if l.type == "village" and l.ile == lieu.ile)
    M.poser_entite(p, "rouge", village.pos[0] + 100.0, village.pos[1], w.carte.iles.index(village.ile), taille=12)
    T.jours(w, 1)
    pop = [v for v in M.connaissances(p, M.CAMP_NATIONAL).values() if v["source"] in ("population", "medias")]
    # le pont
    M.poser_posture(p, lieu.id, "combat", 2)
    for b in d.bases: M.poser_posture(p, _lid(p, b), "combat", 2)
    T.jours(w, 1)
    _jusqu_a(w, 7.0)
    br = None
    for _ in range(18):
        w.pas_suivant()
        br = M.a_incarner(p)
        if br["convois"]: break
    departs = [c["depart"] for c in br["convois"]]
    par_origine = {}
    for c in br["convois"]: par_origine.setdefault(c["origine"], []).append(c["depart_pas"])
    etales = all(len(set(v)) == len(v) for v in par_origine.values())
    pont_ok = bool(departs) and len(set(departs)) == len(departs) and etales and all(
        c["ordres"][0][0] == "setDestination" for c in br["convois"])
    req = M.requisitionner_vivres(p, dep.k, 1e6)
    ok = evac_ok and inter_ok and patr_ok and len(pop) >= 1 and pont_ok and req == 0.0
    return ok, (f"evacuation {moyens} en {[e['pas'] if e else None for e in ev]} pas ( attendu {attendu}, {km:.1f} km ), "
                f"kerosene brule {kero:.1f} pour {kero_att:.1f}, patient {etat0['etat'] if etat0 else None} puis "
                f"{etat1['etat'] if etat1 else None} ; interception : {ci['source'] if ci else None} a {err_i if err_i is None else round(err_i)} m ; "
                f"patrouille : {cp['source'] if cp else None} ; contacts par la population {len(pop)} ; pont : {len(departs)} convoi(s), "
                f"departs distincts {len(set(departs)) == len(departs)} ; requisition sans agriculture {req}")


def test_requisition():
    """Vivres de crise par l agriculture. 2 500 habitants AVEC l agriculture ( domaine 9 ), toutes les garnisons au combat
    5 jours, la base isolee coupee de la route ( comme test_isolement ). On requisitionne dans les fermes de son ile 3
    jours-homme de vivres par militaire de la garnison : elle en recoit au moins 99 % ( si les greniers les ont ), l Etat
    verse une indemnite aux fermes, et sa premiere rupture en vivres, predite au jour j+2 sans requisition, n arrive
    plus dans les 5 jours ; celle du gazole reste au jour predit ( temoin ). La conservation du socle tient."""
    w, p = T.monde([M.DOMAINE, "agriculture"], 11, 5)
    T.jours(w, 1)
    d = p.domaine(M.DOMAINE)
    _jusqu_a(w, 6.5)
    dep, x = _hq_et_isolee(p)
    jours = 5
    for b in d.bases: M.poser_posture(p, _lid(p, b), "combat", jours + 1)
    w.routes_coupees.add(_lid(p, x))
    for c in A.compagnies(p):
        if int(A._dom(p).unites["base"][c]) == x: A.imposer_activite(p, c, "repos", jours + 1)
    nv = d.besoins[x][2]
    sv0 = M._stocks_base(p, d, x)[2]
    sans = _rupture_predite(sv0, [nv] * jours, 1.0 / M.CONSERVATION_RATION_J)
    ind0 = p.socle.livre.jour_argent.copy()
    obtenu = M.requisitionner_vivres(p, _lid(p, x), 3.0 * nv * M.KCAL_RATION)
    ind = math.fsum(s_ for (m, _, _), (s_, n) in p.socle.livre.jour_argent.items() if m == "indemnite_requisition")
    sv1 = M._stocks_base(p, d, x)[2]
    j0 = p.jour
    s0c = None; bc = []
    for t in range(jours):
        _jusqu_a(w, 11 + 50 / 60)
        if s0c is None: s0c = M._stocks_base(p, d, x)[0]
        bc.append(d.besoins[x][0])
        _jusqu_a(w, 6.5)
    pred_c = _rupture_predite(s0c, bc)
    obs_c = min((j - j0 for j, b, c in d.ruptures if b == x and c == M.CARB), default=None)
    obs_v = min((j - j0 for j, b, c in d.ruptures if b == x and c == M.VIV), default=None)
    tenue, msg = p.socle.conservation.tenue()
    ok = (obtenu >= 0.99 * 3.0 * nv and abs((sv1 - sv0) - obtenu) < 1e-6 * max(1.0, obtenu) and ind > 0 and sans == 2
          and obs_v is None and obs_c == pred_c and tenue)
    return ok, (f"{_lid(p, x)} : {nv:.0f} militaires, vivres {sv0:.1f} jours-homme, rupture predite sans requisition j+{sans} ; "
                f"requisition de {3.0 * nv:.0f} jours-homme : {obtenu:.1f} obtenus, garnison {sv1:.1f}, indemnite {ind:.1f} dr ; "
                f"rupture en vivres observee {obs_v} ; gazole predite j+{pred_c} observee j+{obs_c} ; conservation {msg}")


def test_pays_vivable():
    """La porte commune : conservation, argent hors livre exterieur seulement, pays vivable, reprise et jumeau."""
    return T.porte_commune(M.DOMAINE)


class _Chrono:
    __slots__ = ("f", "t")

    def __init__(self, f): self.f, self.t = f, 0.0

    def __call__(self, *a):
        t0 = time.perf_counter(); r = self.f(*a); self.t += time.perf_counter() - t0
        return r


def test_cout():
    """Coeur Rust. A 10 000 habitants, les routines du domaine ( ses echeances et ses recepteurs de convois compris )
    coutent au plus 25 % d une journee du moteur seul, une journee de paix et une journee ou deux garnisons sont au
    combat. Installer le domaine a 100 000 habitants ( ses dependances deja la ) coute au plus 15 fois l installation
    a 10 000 ( lineaire : ~ x10 )."""
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
    for t in ("armee_soutien_ordre", "armee_soutien_plan"):
        c = _Chrono(p.gestionnaires[t]); p.gestionnaires[t] = c; chronos.append(c)
    lg = LG._lg(p)
    for k in ("convoi:" + M.MOTIF_CONVOI, M.RECEPTEUR):
        c = _Chrono(lg.recepteurs[k]); lg.recepteurs[k] = c; chronos.append(c)
    d = p.domaine(M.DOMAINE)
    T.jours(w, 1)
    M.poser_posture(p, _lid(p, d.bases[0]), "combat"); M.poser_posture(p, _lid(p, d.bases[-1]), "combat")
    T.jours(w, 1)
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


TESTS = [test_conservation, test_isolement, test_transmission, test_connaissance_de_camp, test_erreur_position,
         test_falsificateur, test_decision, test_api_27, test_requisition, test_pays_vivable, test_cout]
