"""Les portes du domaine 22 ( medias ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests medias"""
import math, pickle, time
import numpy as np
from .. import config as C, monde as W
from ..socle import registre as R
from . import essais as T, pays as P, d22_medias as M

_CACHE = {}


def _monde(echelle=5, graine=11, sans_redaction=False):
    """Un monde avec les medias et leurs dependances ; chaque porte en reprend une copie."""
    k = (echelle, graine)
    if k not in _CACHE:
        w, p = T.monde([M.DOMAINE], graine, echelle)
        _CACHE[k] = pickle.dumps(w)
    w = pickle.loads(_CACHE[k]); p = w.pays
    if sans_redaction: p.domaine(M.DOMAINE).redactions_actives = False
    return w, p


def _avancer(w, heures):
    for _ in range(int(round(heures * 60 / C.MINUTES_PAR_PAS))): w.pas_suivant()


def _jusqu_a(w, heure):
    """Avance jusqu a ce que l horloge du moteur lise `heure` ( multiple de 10 minutes )."""
    for _ in range(C.PAS_PAR_JOUR + 1):
        if abs(w.heure - heure) < 1e-6: return
        w.pas_suivant()
    raise RuntimeError(f"heure {heure} jamais atteinte")


def _habites(d, n=None):
    h = np.nonzero(d.pop > 0)[0]
    return h if n is None else h[:n]


# ================================================================== l installation
def test_equipement_et_contacts():
    """A 10 000 habitants : television 93 a 100 % des residents, internet a la maison 75 a 93 %, 80 a 115 mobiles pour
    100 residents, ligne fixe 55 a 85 % des menages, television payante 20 a 40 %, parts des operateurs a 5 points de
    leurs parts declarees. Les matrices de contact ( M, T ) sont stochastiques par ligne pour chaque lieu habite ( a
    1e-9 ). Trois familles d argent inscrites, tous les motifs declares. Falsificateur : une matrice M dont on retire
    une colonne n est plus stochastique ( le controle le voit )."""
    w, p = _monde(20)
    d = p.domaine(M.DOMAINE); tb = w.table
    cm = p.colonnes["menage"]
    ids, dom, mg = M._residents(p)
    hab = np.unique(mg)
    eq = cm["tel_equipement"][hab].astype(np.int64)
    tv = float((d.eq_tv * d.pop).sum() / d.pop.sum()); net = float((d.eq_net * d.pop).sum() / d.pop.sum())
    mob = 100.0 * cm["tel_mobiles"][hab].astype(np.int64).sum() / len(ids)
    fixe = float(((eq & M.FIXE) > 0).mean()); tvp = float(((eq & M.TV_PAYANTE) > 0).mean())
    op = np.bincount(cm["tel_operateur"][hab].astype(np.int64), minlength=3) / len(hab)
    ecart_op = max(abs(op[o.indice] - o.part_mobile) for o in d.operateurs)
    hb = d.pop > 0
    stoch = max(np.abs(d.M.sum(1)[hb] - 1).max(), np.abs(d.T.sum(1)[hb] - 1).max())
    faux = d.M.copy(); faux[:, int(np.argmax(d.pop))] = 0.0
    vu = np.abs(faux.sum(1)[hb] - 1).max() > 1e-9
    fam = all(f in p.socle.registre.familles for f in ("operateurs_telecom", "medias_prives", "audiovisuel_public"))
    motifs = all(m_ in p.socle.livre.motifs for m_, _ in M.MOTIFS)
    ok = (0.93 <= tv <= 1.0 and 0.75 <= net <= 0.93 and 80 <= mob <= 115 and 0.55 <= fixe <= 0.85 and 0.20 <= tvp <= 0.40
          and ecart_op <= 0.05 and stoch <= 1e-9 and vu and fam and motifs)
    return ok, (f"{len(ids)} residents, {len(hab)} menages : television {tv:.1%}, internet {net:.1%}, {mob:.0f} mobiles "
                f"pour 100, fixe {fixe:.1%}, television payante {tvp:.1%} ; operateurs {np.round(op, 3).tolist()} "
                f"( ecart {ecart_op:.3f} ) ; matrices stochastiques a {stoch:.1e} ( colonne retiree vue : {vu} ) ; "
                f"familles {fam}, motifs {motifs}")


# ================================================================== la rumeur
def _t50(parts):
    """Le premier jour ( interpole ) ou la part franchit 1/2."""
    for k in range(1, len(parts)):
        if parts[k] >= 0.5 > parts[k - 1]: return (k - 1 + (0.5 - parts[k - 1]) / (parts[k] - parts[k - 1])) * M.DT
    return math.inf


def _cellule_seule(beta, N, p0, s, pas):
    """Le modele du domaine ( `diffuser` ) sur une cellule bien melangee, sans telephone ni deformation."""
    un = np.ones((1, 1)); zero = np.zeros((1, 1))
    part = np.array([[p0]]); lv = zero.copy(); rel = zero.copy(); cf = un.copy(); lc = np.zeros((1, 1), np.int32)
    out = [p0]
    rng = np.random.default_rng(0)
    for _ in range(pas):
        part, lv, rel, cf, lc, _, _ = M.diffuser(part, lv, rel, cf, lc, un, zero, np.array([s]), np.ones(1), np.zeros(1),
                                                 np.array([float(N)]), M.DT, beta, 0.0, zero, rng.random((1, 1)),
                                                 np.ones((1, 1)), np.zeros((1, 3), np.int32), 0.0, 0.0, 0.0, np.ones(1))
        out.append(float(part[0, 0]))
    return out


def _agents(N, p0, contacts_j, q, pas, graine):
    """Une population synthetique : N personnes, chacune croise au hasard Poisson( contacts x dt ) autres a chaque
    heure d eveil ; un informe transmet avec la probabilite q a chaque contact."""
    rng = np.random.default_rng(graine)
    sait = np.zeros(N, bool); sait[rng.choice(N, int(round(p0 * N)), replace=False)] = True
    out = [sait.mean()]
    for _ in range(pas):
        nc = rng.poisson(contacts_j * M.DT, N)
        tot = int(nc.sum())
        qui = np.repeat(np.arange(N), nc); avec = rng.integers(0, N, tot)
        appris = qui[sait[avec] & (rng.random(tot) < q)]
        sait[appris] = True
        out.append(sait.mean())
    return out


def test_vitesse_rumeur():
    """Vitesse DECLAREE : beta = BETA_BAO x saillance transmissions par informe et par jour. Nouvelle de saillance 0,5,
    20 000 personnes, 0,1 % d informes au depart. Le modele de cellule du domaine atteint la moitie au temps logistique
    ln( ( 1 - p0 ) / p0 ) / beta a 10 % pres ; une population synthetique d agents ( contacts de Poisson, POLYMOD ) y
    arrive a 10 % du modele ( moyenne de 5 tirages ). Falsificateur : beta divise par 2 double le temps ( rapport 1,8 a
    2,2 ) ; des agents qui parlent deux fois moins s ecartent du modele de plus de 50 %."""
    N, p0, s = 20000, 0.001, 0.5
    beta = M.BETA_BAO * s
    pas = int(30 / M.DT)
    th = math.log((1 - p0) / p0) / beta
    t_c = _t50(_cellule_seule(M.BETA_BAO, N, p0, s, pas))
    t_a = float(np.mean([_t50(_agents(N, p0, M.CONTACTS_J, M.P_PARLER * s, pas, g)) for g in range(5)]))
    t_moitie = _t50(_cellule_seule(M.BETA_BAO / 2, N, p0, s, pas))
    t_bavard = float(np.mean([_t50(_agents(N, p0, M.CONTACTS_J, M.P_PARLER * s / 2, pas, 10 + g)) for g in range(2)]))
    ok = (abs(t_c - th) / th <= 0.10 and abs(t_a - t_c) / t_c <= 0.10 and 1.8 <= t_moitie / t_c <= 2.2
          and abs(t_bavard - t_c) / t_c > 0.5)
    return ok, (f"beta {beta:.2f} par jour : moitie en {th:.2f} j ( logistique ), {t_c:.2f} j ( cellule ), {t_a:.2f} j "
                f"( agents ) ; beta / 2 : {t_moitie:.2f} j ( x{t_moitie / t_c:.2f} ) ; agents deux fois moins bavards "
                f"{t_bavard:.2f} j")


def _deformation(w, p, graine=3):
    d = p.domaine(M.DOMAINE)
    rng = np.random.default_rng(graine)
    hab = _habites(d)
    fids = [M.constater(p, "incendie", int(hab[k]), float(np.exp(rng.normal(1.5, 0.5))), temoins=40, s=0.9, rng=rng)
            for k in rng.choice(len(hab), 12, replace=False)]
    T.jours(w, 4)
    err, rel = [], []
    for f in fids:
        r = d.mem.par_fid.get(f)
        if r is None: continue
        c = np.nonzero(d.mem.c["part"][r, :d.L] > 0)[0]
        err.extend(np.abs(d.mem.c["lv"][r, c] - d.mem.f["lv_vrai"][r]).tolist()); rel.extend(d.mem.c["relais"][r, c].tolist())
    err, rel = np.array(err), np.array(rel)
    bas, haut = err[rel < 1.5], err[rel >= 3.0]
    rk = lambda x: np.argsort(np.argsort(x))
    rho = float(np.corrcoef(rk(rel), rk(err))[0, 1]) if len(err) > 2 else 0.0
    return (float(bas.mean()) if len(bas) else math.nan, float(haut.mean()) if len(haut) else math.nan, rho, len(err),
            len(bas), len(haut))


def test_deformation_relais():
    """Douze incendies de saillance 0,9, sans redaction, quatre jours : l erreur de valeur ( en log ) croit avec les
    relais. Erreur moyenne des croyances a 3 relais et plus au moins 0,10 au-dessus de celle a moins de 1,5 relais ;
    correlation des rangs ( relais, erreur ) >= 0,3 ; au moins 20 croyances dans chaque classe. Falsificateur : sans
    exageration ni derive ( mu = sigma = 0 ), l ecart tombe sous 0,05."""
    w, p = _monde(5, sans_redaction=True)
    b, h, rho, n, nb, nh = _deformation(w, p)
    w2, p2 = _monde(5, sans_redaction=True)
    d2 = p2.domaine(M.DOMAINE); d2.mu = d2.sigma = 0.0
    b0, h0, rho0, _, _, _ = _deformation(w2, p2)
    ok = nb >= 20 and nh >= 20 and h - b >= 0.10 and rho >= 0.3 and abs(h0 - b0) < 0.05
    return ok, (f"{n} croyances : erreur {b:.3f} a moins de 1,5 relais ( {nb} ), {h:.3f} a 3 relais et plus ( {nh} ), "
                f"rho {rho:.2f} ; sans deformation {b0:.3f} et {h0:.3f} ( ecart {h0 - b0:+.3f} )")


def test_deformation_chaine():
    """La deformation par relais sur une chaine controlee ( fonction `diffuser` du domaine ) : 8 lieux de 1 000
    habitants en ligne, chacun ne parle qu a ses voisins ( 5 % de ses contacts ), 200 nouvelles de saillance 1 nees
    au lieu 0 ( la moitie y sait, valeur vraie ), 10 jours. Plus on s eloigne, plus il y a de relais ; l erreur moyenne
    ( en log ) au lieu 7 depasse celle du lieu 1 d au moins 0,15, et croit d un lieu au suivant au moins 5 fois sur 6.
    Falsificateur : sans exageration ni derive, l erreur reste sous 0,01 partout."""
    def chaine(mu, sigma):
        L, F = 8, 200
        Mx = np.zeros((L, L))
        for i in range(L):
            for j in (i - 1, i + 1):
                if 0 <= j < L: Mx[i, j] = 0.05
            Mx[i, i] = 1.0 - Mx[i].sum()
        part = np.zeros((F, L)); part[:, 0] = 0.5
        lv = np.zeros((F, L)); rel = np.zeros((F, L)); cf = np.ones((F, L)); lc = np.zeros((F, L), np.int32)
        rng = np.random.default_rng(4)
        for _ in range(int(10 / M.DT)):
            part, lv, rel, cf, lc, _, _ = M.diffuser(part, lv, rel, cf, lc, Mx, np.zeros((L, L)), np.ones(F), np.ones(L),
                                                     np.zeros(L), np.full(L, 1000.0), M.DT, M.BETA_BAO, 0.0,
                                                     rng.standard_normal((F, L)), rng.random((F, L)), np.ones((F, L)),
                                                     np.zeros((L, 3), np.int32), mu, sigma, 0.0, np.ones(F))
        sait = part > 0
        e = np.array([np.abs(lv[sait[:, k], k]).mean() if sait[:, k].any() else np.nan for k in range(L)])
        r = np.array([rel[sait[:, k], k].mean() if sait[:, k].any() else np.nan for k in range(L)])
        return e, r
    e, r = chaine(M.MU_RELAIS, M.SIGMA_RELAIS)
    e0, _ = chaine(0.0, 0.0)
    hausses = int(np.sum(np.diff(e[1:]) > 0))
    ok = bool(np.all(np.isfinite(e))) and e[7] - e[1] >= 0.15 and hausses >= 5 and np.nanmax(e0) < 0.01
    return ok, (f"relais par lieu {np.round(r, 1).tolist()} ; erreur {np.round(e, 3).tolist()} ( {hausses} hausses sur 6 ) ; "
                f"sans deformation, erreur max {np.nanmax(e0):.4f}")


def test_jamais_antidatee():
    """Apres quatre jours du scenario de publication ( nouvelles vraies et fausses, redactions, dementis ) : aucune
    croyance datee avant son fait, aucune part hors de [0 ; 1], aucune cellule qui sait sans date, sur au moins 300
    croyances. Falsificateur : une croyance antidatee d une demi-journee a la main est vue, et elle seule."""
    dec, p = M.scenario_publication(jours=4, mode="regle", par_jour=10)
    d = p.domaine(M.DOMAINE); mem = d.mem
    a0 = M.anomalies(p)
    idx = mem.actifs()
    n = int((mem.c["part"][idx] > 0).sum())
    r = int(idx[np.argmax((mem.c["part"][idx] > 0).sum(1))]); c = int(np.nonzero(mem.c["part"][r] > 0)[0][0])
    mem.c["appris"][r, c] = mem.f["t"][r] - 0.5
    a1 = M.anomalies(p)
    vu = a1 == [("antidatee", int(mem.f["fid"][r]), c)]
    ok = not a0 and n >= 300 and vu
    return ok, f"{n} croyances, {len(a0)} anomalie(s) ; croyance antidatee a la main : {a1[:2]} ( vue seule : {vu} )"


def test_individus_et_groupes():
    """Individus ( `sait` ) : sur les lieux ou la part est entre 0,1 et 0,9 ( au moins 500 residents ), la part des
    residents qui savent est a 0,03 de la part attendue ; relever la part de 0,1 ne fait oublier personne ( monotone ).
    Un observer ne lit pas la verite : `croyance` sans ses champs. Groupes : un camp inscrit sur les deux plus grands
    lieux apprend en un jour un incendie vu chez lui, jamais avant le fait ; falsificateur : un camp isole, sans media,
    n en sait rien ; un rapport a lieu faux lui fait croire ce lieu ( erreur de position > 0 km ). Un monde avec ses
    groupes passe l instantane a l identique."""
    w, p = _monde(20, sans_redaction=True)
    d = p.domaine(M.DOMAINE)
    hab = np.argsort(-d.pop, kind="stable")[:2]
    A, B = int(hab[0]), int(hab[1])
    M.inscrire_groupe(p, "camp_bleu", {d.lieu_ids[A]: 1.0, d.lieu_ids[B]: 1.0}, taille=200)
    M.inscrire_groupe(p, "camp_isole", None, taille=50, suit_medias=False)
    fid = M.constater(p, "incendie", A, 3.0, s=0.8)
    T.jours(w, 1)
    ids, dom, mg = M._residents(p)
    r = d.mem.par_fid[fid]; part = d.mem.c["part"][r, :d.L].copy()
    sel = (part[dom] > 0.1) & (part[dom] < 0.9)
    s0 = M.sait(p, ids[sel], fid)
    ecart = abs(float(s0.mean()) - float(part[dom[sel]].mean())) if sel.any() else 1.0
    d.mem.c["part"][r, :d.L] = np.minimum(1.0, part + 0.1)
    s1 = M.sait(p, ids[sel], fid); mono = not (s0 & ~s1).any()
    d.mem.c["part"][r, :d.L] = part
    cg = M.croyance(p, "camp_bleu", "incendie")
    appris_ok = bool(cg) and cg[0]["appris"] >= M.fait(p, fid)["t"]
    iso0 = M.croyance(p, "camp_isole", "incendie")
    M.informer(p, "camp_isole", fid, part=1.0, lieu=d.lieu_ids[B])
    e = M.croyance(p, "camp_isole", "incendie", avec_erreur=True)
    err_ok = bool(e) and e[0]["lieu"] == d.lieu_ids[B] and e[0]["erreur_lieu_km"] > 0
    cache = not (set(M.croyance(p, d.lieu_ids[A], "incendie")[0]) & {"vrai", "erreur_valeur", "erreur_lieu_km"})
    snap = pickle.loads(pickle.dumps(w))
    identique = M.croyance(snap.pays, "camp_bleu") == M.croyance(p, "camp_bleu")
    ok = (int(sel.sum()) >= 500 and ecart <= 0.03 and mono and cache and appris_ok and not iso0 and err_ok and identique)
    return ok, (f"{int(sel.sum())} residents a part partielle : savent {float(s0.mean()) if sel.any() else 0:.3f} pour "
                f"{float(part[dom[sel]].mean()) if sel.any() else 0:.3f} attendus ( ecart {ecart:.3f} ), monotone {mono} ; "
                f"verite cachee a l observer {cache} ; camp_bleu part {cg[0]['part'] if cg else 0:.2f} ( date ok {appris_ok} ), "
                f"camp isole {len(iso0)} croyance(s) avant rapport, apres : lieu {e[0]['lieu'] if e else None} a "
                f"{e[0]['erreur_lieu_km'] if e else 0:.1f} km ; instantane identique {identique}")


def test_publication_accelere():
    """Controle positif : une greve de 50 personnes dans un village ( saillance ~ 0,39 ), sans redaction. La meme,
    publiee a midi par la chaine a la plus forte audience : un jour plus tard, au moins 15 % du pays la sait, au moins
    deux fois plus et 10 points de plus que sans publication."""
    w, p = _monde(5, sans_redaction=True)
    d = p.domaine(M.DOMAINE)
    _jusqu_a(w, 12.0)
    village = next(k for k in _habites(d) if w.carte.par_n[k].type == "village")
    fid = M.constater(p, "greve", int(village), 50.0, temoins=30)
    snap = pickle.dumps(w)
    wa = pickle.loads(snap); pa = wa.pays
    top = max(d.medias, key=lambda m: m.base).nom
    M.publier(pa, fid, top, immediat=True)
    _avancer(wa, 24)
    wb = pickle.loads(snap); pb = wb.pays
    _avancer(wb, 24)
    a, b = M.part_nationale(pa, fid), M.part_nationale(pb, fid)
    ok = a >= 0.15 and a >= 2 * b and a - b >= 0.10
    return ok, f"greve a {w.carte.par_n[int(village)].id} : publiee par {top} {a:.1%} du pays un jour plus tard, sans publication {b:.1%}"


def test_credibilite_fausse_nouvelle():
    """Une fausse nouvelle publiee par un site, puis dementie : sa credibilite baisse d au moins 5 % ; celle d un media
    qui ne l a pas publiee ne bouge pas ; la confiance de ceux qui y croyaient baisse de moitie au moins. Controle : une
    nouvelle vraie publiee ne fait pas baisser la credibilite."""
    w, p = _monde(5, sans_redaction=True)
    d = p.domaine(M.DOMAINE)
    _jusqu_a(w, 12.0)
    lieu = int(_habites(d)[0])
    faux = M.fabriquer_rumeur(p, "penurie", lieu, 30.0, personnes=20)
    vrai = M.constater(p, "incendie", lieu, 2.0)
    c0 = {m.nom: m.cred for m in d.medias}
    M.publier(p, faux, "site_3", immediat=True); M.publier(p, vrai, "site_1", immediat=True)
    c1 = {m.nom: m.cred for m in d.medias}
    r = d.mem.par_fid[faux]
    conf0 = float(d.mem.c["conf"][r, lieu])
    M.dementir(p, faux)
    c2 = {m.nom: m.cred for m in d.medias}
    conf1 = float(d.mem.c["conf"][r, lieu])
    ok = (c2["site_3"] <= 0.95 * c1["site_3"] and c2["tv_1"] == c0["tv_1"] and c1["site_1"] >= c0["site_1"]
          and c2["site_1"] == c1["site_1"] and conf1 <= 0.5 * conf0)
    return ok, (f"site_3 {c0['site_3']:.3f} -> {c1['site_3']:.3f} publiee -> {c2['site_3']:.3f} dementie ; tv_1 "
                f"{c0['tv_1']:.3f} -> {c2['tv_1']:.3f} ; site_1 ( une vraie ) {c0['site_1']:.4f} -> {c2['site_1']:.4f} ; "
                f"confiance au lieu {conf0:.2f} -> {conf1:.2f}")


def test_panne_coupe_telecom():
    """Avec l energie : la ligne d un lieu habite est coupee. Une heure apres, le reseau tient encore ( batteries des
    relais ) ; cinq heures apres, il est coupe ( journal : panne_telecom de ce lieu ), les sites n y portent plus et le
    telephone n y relaie plus ; un lieu non coupe garde son reseau. Controle : avant la coupure, le reseau marche ; deux
    jours apres, il est retabli."""
    from . import d11_energie as EN
    w, p = T.monde([M.DOMAINE, "energie"], 11, 5)
    d = p.domaine(M.DOMAINE)
    T.jours(w, 1); _jusqu_a(w, 10.0)
    E = p.domaine("energie")
    cand = [k for k in _habites(d) if w.carte.par_n[k].id in E.par_ile[w.carte.par_n[k].ile].par_lieu]
    lieu = d.lieu_ids[int(cand[0])]; autre = d.lieu_ids[int(cand[-1])]
    avant = M.telecom_ok(p, lieu)
    EN.couper_ligne(p, lieu, 1.0, "porte")
    _avancer(w, 1); une = M.telecom_ok(p, lieu)
    _avancer(w, 4); cinq = M.telecom_ok(p, lieu); autre_ok = M.telecom_ok(p, autre)
    k = d.n_du_lieu[lieu]
    site = next(m for m in d.medias if m.genre == "site")
    portee_site = float((site.portee * M._disponible(d, site))[k]); tel = float((d.eq_tel * d.reseau.ok)[k])
    note = any(e["type"] == "panne_telecom" and e["lieu"] == lieu for e in p.socle.journal.derniers(n=2000))
    _avancer(w, 48); apres = M.telecom_ok(p, lieu)
    ok = avant and une and not cinq and autre_ok and portee_site == 0.0 and tel == 0.0 and note and apres
    return ok, (f"{lieu} : avant {avant}, +1 h {une}, +5 h {cinq} ( {autre} : {autre_ok} ) ; portee du site {portee_site}, "
                f"relais telephonique {tel} ; journal {note} ; +2 j {apres}")


# ================================================================== la decision
def test_decision():
    """Scenario : 12 nouvelles par jour ( 35 % fausses ), 10 jours, 12 medias. En mode hasard, part du choix >= 0,01 et
    p de permutation < 0,05, avec au moins 5 notes par action et par jour sur 5 jours au moins. Regle, temoin ( tout
    publier ) et hasard : notes moyennes rapportees ( pas un seuil )."""
    dec, _ = M.scenario_publication(jours=10, mode="hasard")
    e2, pp = dec.part_du_choix(), dec.p_permutation()
    par_jour = {}
    for (j, a), (n, s, q) in dec.stats.items(): par_jour.setdefault(j, []).append(n)
    jours_ok = sum(1 for v in par_jour.values() if len(v) == 3 and min(v) >= 5)
    moy = lambda dc: sum(n * m for n, m in dc.notes_par_action().values()) / max(1, sum(n for n, _ in dc.notes_par_action().values()))
    regle, _ = M.scenario_publication(jours=10, mode="regle")
    temoin, _ = M.scenario_publication(jours=10, mode="temoin")
    ok = e2 >= 0.01 and pp < 0.05 and jours_ok >= 5
    na = {k: (n, round(v, 3)) for k, (n, v) in dec.notes_par_action().items()}
    return ok, (f"hasard : part du choix {e2:.3f}, p {pp:.3f}, {jours_ok} jours a 5 notes par action ; notes {na} ; "
                f"moyennes regle {moy(regle):.3f} {regle.notes_par_action()} , temoin {moy(temoin):.3f}, hasard {moy(dec):.3f}")


# ================================================================== l argent
def test_facturation_et_argent():
    """Trois jours a 2 500 habitants : chaque jour, entre 1/60 et 1/15 des menages habites recoit sa facture ; la TVA
    reversee par les operateurs est exactement 24/124 de ce qu ils ont encaisse ( a 1e-9 relatif ) ; les trois
    familles du domaine se rapprochent du grand livre ( reste nul ) ; la publicite et la dotation publique coulent ;
    aucun abonnement n est suspendu avant deux mois de retard."""
    w, p = _monde(5)
    d = p.domaine(M.DOMAINE)
    rap = R.Rapprochement(p.socle.registre, p.socle.livre)
    par_jour = []
    for _ in range(3):
        T.jours(w, 1); par_jour.append(d.compte.get("factures", 0))
    ids, dom, mg = M._residents(p)
    nm = len(np.unique(mg))
    recu = sum(o.recu_total for o in d.operateurs); tva = sum(o.tva_total for o in d.operateurs)
    tva_ok = recu > 0 and abs(tva - recu * 0.24 / 1.24) <= 1e-9 * recu
    restes = rap.restes()
    fams = ("operateurs_telecom", "medias_prives", "audiovisuel_public")
    rap_ok = all(abs(restes[f]) <= R.tolerance(restes[f]) + 1e-9 for f in fams)
    pub = sum(m.recettes_pub for m in d.medias); etat = sum(m.recettes_etat for m in d.medias)
    freq_ok = all(nm / 60 <= x <= nm / 15 for x in par_jour)
    ok = tva_ok and rap_ok and pub > 0 and etat > 0 and freq_ok and d.suspendus == 0
    return ok, (f"{nm} menages habites, factures par jour {par_jour} ; encaisse {recu:.0f} dr, TVA {tva:.2f} dr "
                f"( exacte : {tva_ok} ) ; restes {', '.join(f'{f} {restes[f]:+.1e}' for f in fams)} ; "
                f"publicite {pub:.0f} dr, Etat {etat:.0f} dr ; suspendus {d.suspendus}")


def test_porte_commune():
    return T.porte_commune(M.DOMAINE)


# ================================================================== le cout
class _Chrono:
    __slots__ = ("f", "t")

    def __init__(self, f): self.f, self.t = f, 0.0

    def __call__(self, p):
        t0 = time.perf_counter(); self.f(p); self.t += time.perf_counter() - t0


def test_cout():
    """Coeur Rust. A 10 000 habitants, avec 40 nouvelles vivantes : les routines du domaine coutent au plus 25 % d une
    journee du moteur seul. Installer les medias a 100 000 habitants coute au plus 15 fois l installation a 10 000."""
    coeur = W.COEUR is not None
    w0 = W.Monde(echelle=20); T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    w, p = _monde(20)
    d = p.domaine(M.DOMAINE)
    rng = np.random.default_rng(1)
    hab = _habites(d)
    for k in range(40):
        l = int(hab[rng.integers(len(hab))])
        if k % 3: M.constater(p, "incendie", l, 2.0, rng=rng)
        else: M.fabriquer_rumeur(p, "penurie", l, 10.0, rng=rng)
    chronos = []
    for minute, lst in p.routines.items():
        for i, (o, dom, f) in enumerate(lst):
            if dom == M.DOMAINE:
                c = _Chrono(f); lst[i] = (o, dom, c); chronos.append(c)
    T.jours(w, 2)
    propre = sum(c.t for c in chronos) / 2
    def installation(ech):
        wx = W.Monde(echelle=ech); P.installer(wx, ["etat"])
        t = time.perf_counter(); P.installer(wx, [M.DOMAINE]); return time.perf_counter() - t, wx.table.n
    t10, n10 = installation(20); t100, n100 = installation(200)
    ok = coeur and propre <= 0.25 * t_e1 and t100 <= 15 * t10
    return ok, (f"coeur Rust {coeur} ; {w.table.n} habitants, {len(d.mem.actifs())} faits vivants : moteur seul "
                f"{t_e1:.2f} s par jour ; routines propres {propre * 1000:.0f} ms, {propre / t_e1:.1%} ; installation "
                f"{n10} habitants {t10:.2f} s, {n100} habitants {t100:.2f} s ( x{t100 / t10:.1f} )")


TESTS = [test_equipement_et_contacts, test_vitesse_rumeur, test_deformation_relais, test_deformation_chaine,
         test_jamais_antidatee,
         test_individus_et_groupes, test_publication_accelere, test_credibilite_fausse_nouvelle, test_panne_coupe_telecom, test_decision,
         test_facturation_et_argent, test_porte_commune, test_cout]
