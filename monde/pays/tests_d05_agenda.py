"""Les portes du domaine 5 ( agenda ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests agenda

Le monde part le vendredi 15 juin 2035 a 6 h : jour 0 vendredi, 1 samedi, 2 dimanche ( l epidemie du moteur commence a
Pyrgos ), 3 lundi de Pentecote ( ferie grec ), 4 mardi."""
import time
import numpy as np
from .. import config as C, monde as W
from . import essais as T, pays as P, d05_agenda as A

K = {h: (h * 60 - A.MINUTE_AUBE) // A.PAS_MIN for h in range(6, 24)}     # le pas de chaque heure pleine


def _un_jour(w, f=None):
    """Fait vivre une journee du monde ( 144 pas ) ; f( k ) apres chaque pas ( k = 0 : 6 h )."""
    for _ in range(C.PAS_PAR_JOUR):
        w.pas_suivant()
        if f is not None: f((w.pas - 1) % C.PAS_PAR_JOUR)


def _au_travail(w, horaires=None, sauf=None):
    return [h for h in w.habitants if h.vivant and h.poste == "travail"
            and (horaires is None or h.horaire in horaires) and (sauf is None or h.horaire not in sauf)]


# ================================================================== la semaine
def _semaine():
    """Vendredi, samedi, dimanche : les presences et ce que le moteur a produit ( une seule simulation pour deux portes )."""
    w, p = T.monde(["agenda"])
    prod = w.flux["produit"]
    r = {"ven": None, "sam_viol": 0, "sam_marchands": None, "dim_viol": 0, "gardes_min": 1.0}

    def vendredi(k):
        if k == K[10]:
            sem = [h for h in w.habitants if h.vivant and h.horaire in A.SEMAINE]
            r["ven"] = sum(1 for h in sem if h.poste == "travail") / len(sem)

    def samedi(k):
        r["sam_viol"] += len(_au_travail(w, A.SEMAINE))
        if k == K[12]:
            m = [h for h in w.habitants if h.vivant and h.role == "marchand"]
            r["sam_marchands"] = sum(1 for h in m if h.poste == "travail") / len(m)

    gardes = [h for h in w.habitants if h.vivant and h.horaire == "garde"]

    def dimanche(k):
        r["dim_viol"] += len(_au_travail(w, sauf=A.CONTINUS))
        r["gardes_min"] = min(r["gardes_min"], sum(1 for h in gardes if h.poste == "travail") / len(gardes))

    avant = {b: prod[b] for b in ("nourriture", "petrole", "fer")}
    ven = {}; dim = {}
    _un_jour(w, vendredi)
    for b in avant: ven[b] = prod[b] - avant[b]
    _un_jour(w, samedi)
    avant = {b: prod[b] for b in avant}
    _un_jour(w, dimanche)
    for b in avant: dim[b] = prod[b] - avant[b]
    # le moteur compte present a la ferme qui est dans le LIEU de son travail ( Monde.produire ) : a 5 h 50 lundi
    paysans = [x for x in w.habitants if x.vivant and x.role == "paysan"]
    r["chez_soi_a_la_ferme"] = sum(1 for x in paysans if x.lieu is x.travail and x.poste == "maison") / len(paysans)
    h = next(x for x in w.habitants if x.vivant and x.role == "paysan" and x.poste == "maison")
    h.lieu, h.poste = h.travail, "travail"
    r["vu"] = [x.id for x in _au_travail(w, sauf=A.CONTINUS)] == [h.id]
    return r, ven, dim


_SEMAINE = []


def _semaine_une_fois():
    if not _SEMAINE: _SEMAINE.append(_semaine())
    return _SEMAINE[0]


def test_semaine():
    """Porte : le dimanche ( jour 2 ), a chaque pas, seuls des gardes ( 3 x 8 ) sont au travail ; le samedi, aucun
    horaire jour, bureau ou ecole ne travaille et au moins 80 % des marchands tiennent le marche a midi. Controle
    positif : le vendredi a 10 h, au moins 80 % des horaires jour, bureau et ecole sont au travail. Falsificateur : un
    paysan pose a la main au travail le dimanche est compte."""
    r, _, _ = _semaine_une_fois()
    ok = r["dim_viol"] == 0 and r["sam_viol"] == 0 and r["ven"] >= 0.8 and r["sam_marchands"] >= 0.8 and r["vu"]
    return ok, (f"vendredi 10 h : {r['ven']:.0%} des horaires jour/bureau/ecole au travail ; samedi : {r['sam_viol']} "
                f"presences jour/bureau/ecole, marchands a midi {r['sam_marchands']:.0%} ; dimanche : {r['dim_viol']} "
                f"presences hors gardes, gardes presents au moins {r['gardes_min']:.0%} a chaque pas ; paysan pose a la "
                f"main vu : {r['vu']}")


def test_travail_fait():
    """Porte : le travail reellement fait suit l agenda - le dimanche, les fermes produisent au plus 1 % de la
    nourriture du vendredi, quand le puits ( gardes, 3 x 8 ) produit encore au moins 50 % de son petrole du vendredi.
    ( Ecrite avec test_semaine, avant la premiere mesure ; separee apres, pour que son echec ne cache pas l autre. )"""
    r, ven, dim = _semaine_une_fois()
    ok = dim["nourriture"] <= 0.01 * ven["nourriture"] and dim["petrole"] >= 0.5 * ven["petrole"]
    return ok, (f"produit vendredi -> dimanche : nourriture {ven['nourriture']:.0f} -> {dim['nourriture']:.0f}, petrole "
                f"{ven['petrole']:.0f} -> {dim['petrole']:.0f}, fer ( mines, domicile distinct du travail ) "
                f"{ven['fer']:.0f} -> {dim['fer']:.0f} ; {r['chez_soi_a_la_ferme']:.0%} des paysans sont chez eux DANS le "
                f"lieu de leur ferme ( village = domicile = travail ) : Monde.produire, qui compte `lieu is travail` et "
                f"non le poste, les fait travailler le dimanche. A corriger dans produire ( ou par l agriculture quand "
                f"elle reprend les fermes ) : compter `poste == travail`")


def test_ferie():
    """Porte : le lundi de Pentecote ( jour 3, ferie grec ) ressemble a un dimanche - a 10 h, le nombre d habitants au
    travail est celui du dimanche a 15 % pres ( ou 3 personnes ), et le mardi en compte au moins 3 fois plus.
    Falsificateur : dans le meme monde ou le calendrier a perdu ses feries, le lundi a 10 h compte au moins 80 % des
    presences du mardi ( le ferie oublie se voit )."""
    def compter(sans_feries):
        w, p = T.monde(["agenda"])
        if sans_feries: p.socle.calendrier._feries[2035] = {}
        n = {}
        for j in range(5):
            _un_jour(w, lambda k, j=j: n.__setitem__(j, len(_au_travail(w))) if k == K[10] else None)
        return n
    n, f = compter(False), compter(True)
    ok = abs(n[3] - n[2]) <= max(3, 0.15 * n[2]) and n[4] >= 3 * n[3] and f[3] >= 0.8 * f[4]
    return ok, (f"au travail a 10 h : vendredi {n[0]}, samedi {n[1]}, dimanche {n[2]}, lundi ferie {n[3]}, mardi {n[4]} ; "
                f"sans feries au calendrier : lundi {f[3]}, mardi {f[4]}")


# ================================================================== les contacts de la contagion
def contacts(w):
    """L instrument : ( paires, paires entre domiciles differents ) d habitants vivants presents dans le meme lieu. Ce sont
    les groupes que forme la contagion du moteur ( Monde.contagion groupe par h.lieu.id ) ; il lit la verite des
    habitants, pas le miroir de l agenda."""
    par_lieu = {}
    for h in w.habitants:
        if h.vivant and h.lieu is not None:
            d = par_lieu.setdefault(h.lieu.id, {})
            d[h.domicile.id] = d.get(h.domicile.id, 0) + 1
    paires = inter = 0
    for d in par_lieu.values():
        n = sum(d.values()); s2 = sum(v * v for v in d.values())
        paires += n * (n - 1) // 2; inter += (n * n - s2) // 2
    return paires, inter


def _journee_contacts(w):
    """Une journee, l instrument somme aux heures pleines de 8 h a 18 h ( la contagion passe a l heure pleine )."""
    tot = [0, 0]

    def f(k):
        if k in [K[h] for h in range(8, 19)]:
            a, b = contacts(w); tot[0] += a; tot[1] += b
    _un_jour(w, f)
    return tot


def test_contacts():
    """Porte : les contacts de la contagion changent avec la semaine - la part des paires de contact entre habitants de
    domiciles differents, de 8 h a 18 h, est au plus 0,6 fois celle du vendredi le dimanche. Controle negatif : le moteur
    seul ( sans agenda ) donne le meme melange le dimanche et le vendredi ( rapport 0,9 a 1,1 ). Controle positif de
    l instrument : 20 habitants de 20 domiciles et 20 lieux distincts deplaces a la main dans un lieu vide changent les
    paires et les paires entre domiciles EXACTEMENT de ce que le calcul prevoit."""
    w, p = T.monde(["agenda"])
    ven = _journee_contacts(w); sam = _journee_contacts(w); dim = _journee_contacts(w)
    s = {j: x[1] / x[0] for j, x in (("ven", ven), ("sam", sam), ("dim", dim))}
    e = W.Monde()
    e_ven = _journee_contacts(e); _journee_contacts(e); e_dim = _journee_contacts(e)
    r_e = (e_dim[1] / e_dim[0]) / (e_ven[1] / e_ven[0])
    # controle positif : un rassemblement pose a la main
    compo = {}
    for h in w.habitants:
        if h.vivant and h.lieu is not None:
            d = compo.setdefault(h.lieu.id, {}); d[h.domicile.id] = d.get(h.domicile.id, 0) + 1
    vus_d, vus_l, gens = set(), set(), []
    for h in w.habitants:
        if h.vivant and h.lieu is not None and h.domicile.id not in vus_d and h.lieu.id not in vus_l:
            gens.append(h); vus_d.add(h.domicile.id); vus_l.add(h.lieu.id)
        if len(gens) == 20: break
    cible = next(l for l in w.carte.lieux.values() if l.id not in compo)
    n = len(gens)
    d_paires = n * (n - 1) // 2 - sum(sum(compo[h.lieu.id].values()) - 1 for h in gens)
    d_inter = n * (n - 1) // 2 - sum(sum(compo[h.lieu.id].values()) - compo[h.lieu.id][h.domicile.id] for h in gens)
    a0 = contacts(w)
    for h in gens: h.lieu = cible
    a1 = contacts(w)
    exact = n == 20 and (a1[0] - a0[0], a1[1] - a0[1]) == (d_paires, d_inter)
    ok = s["dim"] <= 0.6 * s["ven"] and 0.9 <= r_e <= 1.1 and exact
    return ok, (f"paires entre domiciles differents : vendredi {s['ven']:.1%} de {ven[0]} paires-heures, samedi "
                f"{s['sam']:.1%}, dimanche {s['dim']:.1%} ( rapport {s['dim'] / s['ven']:.2f} ) ; moteur seul : "
                f"rapport {r_e:.2f} ; rassemblement pose a la main : {a1[0] - a0[0]:+d} paires, {a1[1] - a0[1]:+d} "
                f"entre domiciles, prevu {d_paires:+d} et {d_inter:+d} : {exact}")


# ================================================================== les trajets
def test_trajets():
    """Porte : le vendredi, aucun trajet du plan n a une duree que sa distance et son mode n expliquent ( a pied 2,5 a
    7 km/h, en vehicule 8 a 70 km/h de porte a porte, pas de marche de plus de 3 km, rien au-dela de 3 h ) ; dans chaque
    mode, la duree suit la distance ( correlation >= 0,9, au moins 10 trajets ) ; un trajet en vehicule d au moins 15 min
    part de son origine et s approche de sa destination a chaque minute ( position interpolee ). Falsificateur : un
    trajet en vehicule de 3 km ou plus dont la duree est multipliee par 6 a la main est vu."""
    w, p = T.monde(["agenda"])
    w.pas_suivant()
    tr = A.trajets_du_jour(p)
    mal = A.trajets_incoherents(p, tr)
    corr, nb = {}, {}
    for mode in A.MODES:
        x = np.array([(km, mn) for _, _, _, km, mn, md, c in tr if md == mode and not c])
        nb[mode] = len(x)
        corr[mode] = float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]) if len(x) >= 10 and x[:, 0].std() > 0 else float("nan")
    a = p.domaine("agenda"); pl = a.plan
    # une position qui avance
    i = next(i for i, tour, sens, km, mn, md, c in tr if tour == "travail" and sens == "aller" and md == "vehicule"
             and mn >= 15)
    d0, a0 = int(pl.tt[i, A.T_TRAVAIL, A.DEP]), int(pl.tt[i, A.T_TRAVAIL, A.ARR])
    h = w.habitants[i]
    pos = [A.position(p, i, t) for t in range(d0, a0)]
    loin = [np.hypot(q["x"] - h.travail.pos[0], q["y"] - h.travail.pos[1]) for q in pos]
    avance = (all(q["activite"] == "trajet" for q in pos) and all(b < c for b, c in zip(loin[1:], loin[:-1]))
              and np.hypot(pos[0]["x"] - h.domicile.pos[0], pos[0]["y"] - h.domicile.pos[1]) <= 1.0)
    # falsificateur
    j = next(j for j, tour, sens, km, mn, md, c in tr if tour == "travail" and sens == "aller" and md == "vehicule"
             and km >= 3)
    t0 = int(pl.tt[j, A.T_TRAVAIL, A.DEP])
    pl.tt[j, A.T_TRAVAIL, A.DEP] = int(pl.tt[j, A.T_TRAVAIL, A.ARR]) - 6 * (int(pl.tt[j, A.T_TRAVAIL, A.ARR]) - t0)
    vu = any(x[0] == j and x[1] == "travail" and x[2] == "aller" for x in A.trajets_incoherents(p))
    ok = (not mal and all(nb[m] >= 10 and corr[m] >= 0.9 for m in A.MODES) and avance and vu)
    return ok, (f"{len(tr)} trajets, {len(mal)} incoherents {mal[:3]} ; a pied {nb['marche']} ( correlation duree-distance "
                f"{corr['marche']:.3f} ), en vehicule {nb['vehicule']} ( {corr['vehicule']:.3f} ) ; position interpolee sur "
                f"{a0 - d0} min, de {loin[0]:.0f} a {loin[-1]:.0f} m de l arrivee : {avance} ; trajet allonge a la main vu : {vu}")


def mouvements_par_pas(w, n_pas=C.PAS_PAR_JOUR):
    """L instrument : a chaque pas, le nombre d habitants vivants qui se mettent en mouvement - leur lieu ou leur poste
    change alors qu ils n etaient pas deja en trajet. Il lit la verite des habitants ; c est ce que la bulle recoit
    comme ordres de marche au meme instant."""
    avant = {h.id: (h.lieu, h.poste) for h in w.habitants if h.vivant}
    out = []
    for _ in range(n_pas):
        w.pas_suivant()
        c = 0
        for h in w.habitants:
            if not h.vivant: continue
            v, now = avant.get(h.id), (h.lieu, h.poste)
            if v is not None and (v[0] is not now[0] or v[1] != now[1]) and v[1] != "trajet": c += 1
            avant[h.id] = now
        out.append(c)
    return out


def part_du_pic(d):
    """Les mouvements du pas le plus charge, sur ceux de l heure la plus chargee ( 6 pas consecutifs ). Un etalement
    uniforme sur l heure donne 1/6 ; tout le monde a la meme minute, 1."""
    heure = max(sum(d[i:i + 6]) for i in range(len(d) - 5))
    return max(d) / max(1, heure)


def test_departs():
    """Porte : les departs sont etales - le mardi ( jour 4 ), le pas le plus charge porte au plus 30 % des mouvements de
    l heure la plus chargee. Controle positif : le meme monde, decalages personnels mis a zero, depasse 50 % ( l instrument
    voit le pic que l etalement efface )."""
    def mesurer(sans_decalage):
        w, p = T.monde(["agenda"])
        if sans_decalage:
            for h in w.habitants: h.decalage = 0.0
        T.jours(w, 4)
        d = mouvements_par_pas(w)
        return part_du_pic(d), max(d), int(np.argmax(d)), sum(1 for h in w.habitants if h.vivant)
    r, pic, k, n = mesurer(False)
    r0, pic0, k0, _ = mesurer(True)
    ok = r <= 0.30 and r0 >= 0.50
    hh = lambda k: f"{(A.MINUTE_AUBE + 10 * k) // 60}h{(A.MINUTE_AUBE + 10 * k) % 60:02d}"
    return ok, (f"pic de {pic} mouvements a {hh(k)} ( {pic / n:.1%} des vivants ), {r:.0%} de l heure la plus chargee ; "
                f"sans decalage : {pic0} a {hh(k0)}, {r0:.0%}")


# ================================================================== la coherence
def test_lieu_impossible():
    """Porte : pendant 3 jours, a chaque heure pleine, aucun habitant n est hors de son plan ni dans un lieu que ses
    activites n expliquent, et le miroir ( colonnes ) dit ou sont les habitants. Falsificateurs : un paysan au travail
    pose a la main sur une base militaire est vu hors plan, dans un lieu impossible, et en ecart au miroir ; un enfant
    pose en trajet a la main alors qu il dort est vu hors plan."""
    w, p = T.monde(["agenda"])
    pires = [0, 0]

    def f(k):
        if k % 6 == 0:
            pires[0] = max(pires[0], len(A.incoherences(p))); pires[1] = max(pires[1], len(A.ecarts_miroir(p)))
    for _ in range(3): _un_jour(w, f)
    while w.pas <= 4 * C.PAS_PAR_JOUR + K[10]: w.pas_suivant()      # le mardi ( jour 4 ) a 10 h
    propre = A.incoherences(p)
    h = next(x for x in w.habitants if x.vivant and x.role == "paysan" and x.poste == "travail")
    base = next(l for l in w.carte.lieux.values() if l.type == "base")
    h.lieu = base
    inc = A.incoherences(p)
    vu1 = ("lieu_impossible", h.id) in inc and ("hors_plan", h.id) in inc and h.id in A.ecarts_miroir(p)
    e = next(x for x in w.habitants if x.vivant and x.poste == "maison" and x.lieu is x.domicile)
    e.poste = "trajet"
    inc2 = A.incoherences(p)
    vu2 = ("hors_plan", e.id) in inc2 and ("lieu_impossible", e.id) not in inc2
    ok = pires == [0, 0] and not propre and vu1 and vu2
    return ok, (f"3 jours, a chaque heure : au plus {pires[0]} incoherences, {pires[1]} ecarts au miroir ; mardi 10 h : "
                f"{len(propre)} ; paysan pose sur {base.id} vu : {vu1} ; dormeur mis en trajet vu : {vu2}")


# ================================================================== l emploi du temps
def test_emploi_du_temps():
    """Porte : le vendredi, chaque menage dont un adulte sort a au plus un acheteur, les courses sont finies avant 19 h,
    il y a des courses au marche ET a l epicerie du village, au plus 5 % des menages habites sans acheteur, et personne au
    culte ; le dimanche, aucune course, et de 5 a 30 % des adultes libres au culte ; la part des 6 ans et plus qui ont un
    loisir le samedi est au moins 1,5 fois celle du mardi. Controle positif : 5 ecoliers rajeunis a la main a 4 ans
    restent a la maison le mardi a 10 h, quand au moins 80 % des autres ecoliers sont en classe."""
    w, p = T.monde(["agenda"])
    a = p.domaine("agenda")
    res = {}

    def releve(j):
        pl = a.plan; t = A.tours_du_jour(p)
        age = (p.jour - p.col("habitant", "naissance_j")[:pl.n]) / 365.0
        libre = ~pl.hors & ~pl.hopital
        six = libre & (age >= 6); adultes = libre & (age >= 18)
        loisir = np.zeros(pl.n, bool); loisir[t["loisir_jour"]] = True; loisir[t["loisir_soir"]] = True
        culte = np.zeros(pl.n, bool); culte[t["culte"]] = True
        ach = t["courses"]
        mg = [w.habitants[i].menage.id for i in ach]
        fin = pl.tt[ach, A.T_COURSES, A.FIN].astype(int) if ach else np.zeros(0)
        res[j] = dict(loisir=(loisir & six).sum() / six.sum(), culte=(culte & adultes).sum() / adultes.sum(),
                      courses=len(ach), un_par_menage=len(set(mg)) == len(mg), avant_19h=bool((fin <= A.FIN_COURSES).all()),
                      marche=pl.stats["courses_marche"], village=pl.stats["courses_village"],
                      sans=pl.stats["sans_acheteur"] / max(1, len(T.menages_habites(w))))
    for j in range(5):
        w.pas_suivant(); releve(j)
        if j == 3:              # la veille du mardi : 5 ecoliers rajeunis
            petits = [h for h in w.habitants if h.vivant and h.horaire == "ecole" and h.role == "enfant"][:5]
            for h in petits: p.col("habitant", "naissance_j")[h.id] = p.jour - 4 * 365
        if j == 4:
            while w.pas <= 4 * C.PAS_PAR_JOUR + K[10]: w.pas_suivant()
            ecoliers = [h for h in w.habitants if h.vivant and h.horaire == "ecole" and h.role == "enfant" and h not in petits]
            en_classe = sum(1 for h in ecoliers if h.poste == "travail") / len(ecoliers)
            petits_maison = all(h.poste == "maison" for h in petits)
        else:
            for _ in range(C.PAS_PAR_JOUR - 1): w.pas_suivant()
    v, d = res[0], res[2]
    ok = (v["un_par_menage"] and v["avant_19h"] and v["marche"] > 0 and v["village"] > 0 and v["sans"] <= 0.05
          and v["culte"] == 0 and d["courses"] == 0 and 0.05 <= d["culte"] <= 0.30
          and res[1]["loisir"] >= 1.5 * res[4]["loisir"] and petits_maison and en_classe >= 0.8)
    return ok, (f"vendredi : {v['courses']} acheteurs ( {v['marche']} au marche, {v['village']} a l epicerie ), un par "
                f"menage {v['un_par_menage']}, avant 19 h {v['avant_19h']}, menages sans acheteur {v['sans']:.1%} ; culte : "
                f"vendredi {v['culte']:.0%}, dimanche {d['culte']:.1%} des adultes ; courses le dimanche {d['courses']} ; "
                f"loisirs ( 6 ans et plus ) : " + ", ".join(f"{n} {res[j]['loisir']:.0%}" for j, n in
                                                         ((0, "ven"), (1, "sam"), (2, "dim"), (3, "lun ferie"), (4, "mar")))
                + f" ; 5 enfants de 4 ans a la maison le mardi : {petits_maison}, ecoliers en classe {en_classe:.0%}")


# ================================================================== la decision
def _malades_dehors(mode, jours=10):
    """Les malades visibles ( I ) hors de chez eux et hors de l hopital, aux heures pleines de 8 h a 18 h, des jours 4 a 13."""
    w, p = T.monde(["agenda"], modes={"sortir": mode})
    T.jours(w, 4)
    r = [0, 0]

    def f(k):
        if k in [K[h] for h in range(8, 19)]:
            for h in w.habitants:
                if h.vivant and h.etat == "I":
                    r[1] += 1
                    if h.poste not in ("maison", "hopital"): r[0] += 1
    for _ in range(jours): _un_jour(w, f)
    return r


def test_sortir():
    """Porte de la decision : 18 jours avec l epidemie du moteur, chaque adulte decide au hasard ( mode hasard ) chaque
    matin. La note doit dependre du choix ( part du choix >= 0,01 ), au moins 2 000 decisions, les deux actions notees,
    la conservation tenue et aucune incoherence. Regle contre temoin : avec la regle, aucun malade visible hors de chez
    lui ( hors hopital ) ; avec le temoin ( toujours sortir ), au moins un ( controle positif de ce compte )."""
    w, p = T.monde(["agenda"], modes={"sortir": "hasard"})
    T.jours(w, 18)
    dec = p.domaine("agenda").decideur
    part = dec.part_du_choix(); notes = dec.notes_par_action()
    tenue, msg = p.socle.conservation.tenue()
    inc = A.incoherences(p)
    regle, temoin = _malades_dehors("regle"), _malades_dehors("temoin")
    ok = (dec.n_decisions >= 2000 and part >= 0.01 and len(notes) == 2 and tenue and not inc
          and regle[0] == 0 and temoin[0] >= 1)
    return ok, (f"{dec.n_decisions} decisions ; notes : " + ", ".join(f"{a} {m:.3f} ( {n} )" for a, (n, m) in notes.items())
                + f" ; part du choix {part:.3f} ; faim finale {T.faim(w):.0%} ; {msg} ; incoherences {len(inc)} ; malades "
                  f"visibles dehors ( sur malades-heures ) : regle {regle[0]}/{regle[1]}, temoin {temoin[0]}/{temoin[1]}")


# ================================================================== le pays
def test_pays_vivable():
    return T.porte_commune("agenda", n_jours=12)


def test_cout():
    """Le domaine coute au plus 25 % d une journee du moteur ( avec la population ), a 10 000 habitants, sur les jours 0
    a 4 ( ouvre, samedi, dimanche, ferie, ouvre ; decisions d epidemie a partir du jour 2 ). Mesures entrelacees, le
    minimum de deux essais par configuration ( la station est partagee )."""
    def mesurer(domaines):
        w = W.Monde(echelle=20); P.installer(w, domaines)
        t0 = time.perf_counter(); T.jours(w, 5)
        return (time.perf_counter() - t0) / 5, w
    t_pop, t_ag = [], []
    for _ in range(2):
        t_pop.append(mesurer(["population"])[0])
        t, w = mesurer(["agenda"]); t_ag.append(t)
    p = w.pays
    horloge = w.deplacer
    cumul = [0.0]

    def chrono(heure=None):
        t0 = time.perf_counter(); horloge(heure); cumul[0] += time.perf_counter() - t0
    w.deplacer = chrono
    T.jours(w, 1)
    w.deplacer = horloge
    t_pop, t_ag = min(t_pop), min(t_ag)
    n = len(w.habitants)
    ok = t_ag <= 1.25 * t_pop
    return ok, (f"{n} habitants : moteur et population {t_pop:.2f} s par jour, avec l agenda {t_ag:.2f} s "
                f"( {t_ag / t_pop - 1:+.0%} ) ; l agenda seul ( plan, pas, decisions ) {cumul[0]:.2f} s par jour, "
                f"{cumul[0] / n * 1e6:.1f} us par habitant, contre 1,04 s pour Monde.deplacer mesure le 23/09")


TESTS = [test_semaine, test_travail_fait, test_ferie, test_contacts, test_trajets, test_departs, test_lieu_impossible,
         test_emploi_du_temps, test_sortir, test_pays_vivable, test_cout]
