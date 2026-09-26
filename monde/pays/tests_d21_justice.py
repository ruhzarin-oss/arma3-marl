"""Les portes du domaine 21 ( justice, police, criminalite, droit civil ). Seuils ecrits avant la premiere mesure.
python -m monde.pays.tests justice"""
import math, pickle, time
import numpy as np
from .. import config as C, monde as W, population as PO
from ..socle import registre as R
from . import essais as T, pays as P, d06_etat as ET, d13_immobilier as IM, d21_justice as JU

PAS_J = C.PAS_PAR_JOUR
_CACHE = {}


def _a_l_heure(w, heure):
    """Fait vivre le monde jusqu au prochain pas qui tombe a `heure`."""
    for _ in range(PAS_J + 1):
        if abs(w.heure - heure) < 1e-9: return w
        w.pas_suivant()
    raise RuntimeError("heure jamais atteinte")


def _elucidation(p, jusqu_a, types):
    """Part des affaires enregistrees ( plainte au plus tard `jusqu_a` ) qui ont un suspect."""
    S = JU._dom(p); idx = {JU.IDX[t] for t in types}
    n = e = 0
    for a in S.affaires.values():
        if a.type in idx and 0 <= a.jour_plainte <= jusqu_a:
            n += 1; e += a.etat in (JU.ELUCIDEE, JU.JUGEE, JU.ENTERREE)
    return (e / n if n else float("nan")), n


PROPRIETE = ("vol_simple", "cambriolage", "vol_violence")
PERSONNES = ("violences", "homicide")


def _campagne(police, graine=21, echelle=6, crime=40.0, jours=45, mode="regle"):
    """Un pays de 3 000 habitants ou crimes ET enqueteurs sont multiplies ( a police = crime, le rapport des enqueteurs
    aux affaires est celui du pays reel ) ; mis en cache."""
    cle = (police, graine, echelle, crime, jours, mode)
    if cle not in _CACHE:
        w, p = T.monde(["justice"], graine=graine, echelle=echelle, modes={"enquete": mode})
        JU.scenario(p, crime=crime, police=police)
        T.jours(w, jours)
        _CACHE[cle] = (w, p)
    return _CACHE[cle]


# ================================================================== les taux
def test_taux_delits():
    """3 650 nuits tirees sur la population reelle d un pays de 2 000 habitants ( `tirer_delits`, sans effet ) :
    infractions ENREGISTREES ( commises x part declaree ) pour 100 000 habitants et par an dans la bande grecque
    declaree ( JU.BANDES ) ; homicides attendus de 0,5 a 2 pour 100 000. Controle positif ( la faim ) : tous les menages
    sans repas 7 soirs sur 7 -> vols x 2,3 a x 3,2, violences x 1,3 a x 1,7 ( esperance du Poisson ), et les vols
    tires x 2,3 au moins. Dissuasion : une zone qui n a vu aucune elucidation -> x 1,9 a x 2,0 ( borne )."""
    w, p = T.monde(["justice"], graine=5, echelle=4)
    S = JU._dom(p)
    J = JU._poids(p, S)
    n = int(((w.table.vivant[:w.table.n] == 1) & (w.table.statut[:w.table.n] != PO.ABSENT)).sum())
    def compter(J, jours, graine):
        c = np.zeros(JU.NT)
        for d in range(jours):
            for t, _ in JU.tirer_delits(p, S, J, np.random.default_rng((graine, d))): c[t] += 1
        return c
    c = compter(J, 3650, 1)
    taux = {nom: c[JU.IDX[nom]] * JU.DECLAREE[JU.IDX[nom]] / n * 1e5 / 10.0 for nom in JU.BANDES}
    lam = JU.intensites(p, S, J)
    hom = lam[JU.IDX["homicide"]] * JU.JOURS_AN / n * 1e5
    f7 = p.col("menage", "faim7"); M = w.table.menages.n
    garde = f7[:M].copy(); f7[:M] = 0x7F
    Jf = JU._poids(p, S); lam_f = JU.intensites(p, S, Jf)
    cf = compter(Jf, 3650, 1)
    f7[:M] = garde
    x_vol = lam_f[JU.IDX["vol_simple"]] / lam[JU.IDX["vol_simple"]]
    x_vio = lam_f[JU.IDX["violences"]] / lam[JU.IDX["violences"]]
    x_tire = cf[JU.IDX["vol_simple"]] / max(1, c[JU.IDX["vol_simple"]])
    enr, elu = S.enr.copy(), S.elu.copy()
    S.enr[:] = 1000.0; S.elu[:] = 0.0
    lam_d = JU.intensites(p, S, JU._poids(p, S))
    S.enr[:], S.elu[:] = enr, elu
    x_dis = lam_d[JU.IDX["cambriolage"]] / lam[JU.IDX["cambriolage"]]
    ok = (all(JU.BANDES[k][0] <= v <= JU.BANDES[k][1] for k, v in taux.items()) and 0.5 <= hom <= 2.0
          and 2.3 <= x_vol <= 3.2 and 1.3 <= x_vio <= 1.7 and x_tire >= 2.3 and 1.9 <= x_dis <= 2.0)
    return ok, (f"{n} habitants, 3 650 nuits : enregistrees pour 100 000 par an " + ", ".join(
        f"{k} {v:.0f} [{JU.BANDES[k][0]:.0f} ; {JU.BANDES[k][1]:.0f}]" for k, v in taux.items())
                + f", homicides attendus {hom:.2f} ; faim 7/7 -> vols x{x_vol:.2f} ( tires x{x_tire:.2f} ), violences "
                  f"x{x_vio:.2f} ; aucune elucidation vue -> cambriolages x{x_dis:.2f}")


# ================================================================== la police
def test_elucidation_et_effort():
    """Trois pays de 3 000 habitants, 45 jours, infractions x 40 ; enqueteurs x 10, x 40 ( le rapport reel ), x 60 ( au-dela,
    le moteur n a plus de policiers presents a donner a la police judiciaire : le plafond d une zone ). Affaires
    enregistrees au plus tard 15 jours avant la fin : au rapport reel, l elucidation des atteintes aux biens ( vols,
    cambriolages, vols avec violence ) de 5 % a 30 % et celle des atteintes aux personnes ( violences, homicides ) de
    45 % a 95 % ( police hellenique, ordres de grandeur ) ; l elucidation des biens MONTE avec l effort : x 60 au moins
    8 points au-dessus de x 10, et x 40 pas sous x 10 ( 2 points de bruit admis ).
    Mesure 1 ( 26/09, seuils inchanges ) : x10 13 %, x40 39 %, x160 37 % - le rendement d une journee d enquete trop
    fort ( recalibre a l elucidation grecque, q divise par 3 a 4 ) et x160 plafonne par les policiers presents
    ( remplace par x 60, sous le plafond )."""
    res = {}
    for pol in (10.0, 40.0, 60.0):
        w, p = _campagne(pol)
        res[pol] = (_elucidation(p, p.jour - 15, PROPRIETE), _elucidation(p, p.jour - 15, PERSONNES))
    (b10, n10), _ = res[10.0]; (b40, n40), (v40, m40) = res[40.0]; (b160, n160), _ = res[60.0]
    ok = (0.05 <= b40 <= 0.30 and 0.45 <= v40 <= 0.95 and b160 >= b10 + 0.08 and b40 >= b10 - 0.02)
    return ok, (f"biens elucides : x10 {b10:.0%} ( {n10} ), x40 {b40:.0%} ( {n40} ), x60 {b160:.0%} ( {n160} ) ; "
                f"personnes x40 {v40:.0%} ( {m40} )")


def test_delais_grecs():
    """Les delais des tribunaux ( delai prevu d un dossier depose + reports attendus ) dans la bande grecque declaree
    ( JU.BANDES_DELAIS ) a l installation et apres 45 jours d un pays ordinaire de 3 000 habitants ; les dossiers
    simules deposes pendant ces 45 jours, en moyenne par file ( au moins 3 ), aussi ; le flagrant delit juge en 1 a 5
    jours ( pays a infractions x 40 ). Controle positif : la moitie des juges -> delai prevu x 1,95 a x 2,05. En regard
    ( sans seuil ) : le pays a infractions x 40, dont les tribunaux n ont que la capacite d un pays ordinaire.
    Mesure 1 ( 26/09 ) : la porte lisait le pays a infractions x 40, ou les files criminelles s engorgent ( 1 468 jours
    en 45 jours ) : c est le modele qui marche, pas la bande ; la bande se lit desormais dans le pays ordinaire."""
    w0, p0 = T.monde(["justice"], graine=21, echelle=6)
    def attendus(p):
        return {f: JU.delai_prevu(p, f) + JU.P_REPORT * JU.FILES[f][2] for f in JU.NOMS_FILES}
    d0 = attendus(p0)
    w, p = _campagne(1.0, crime=1.0)
    d1 = attendus(p)
    S = JU._dom(p)
    moy = {f: float(np.mean([x for _, x in v])) + JU.P_REPORT * JU.FILES[f][2] for f, v in S.delais.items() if len(v) >= 3}
    wc, pc = _campagne(40.0)
    Sc = JU._dom(pc)
    charge = attendus(pc)
    flag = [Sc.jugements[d.jugement].jour - d.saisine for d in Sc.dossiers.values() if d.file == "autophoro" and d.jugement >= 0]
    base = JU.delai_prevu(p0, "civil")
    JU.scenario(p0, juges=0.5)
    x = JU.delai_prevu(p0, "civil") / base
    JU.scenario(p0, juges=1.0)
    dans = lambda d: all(JU.BANDES_DELAIS[f][0] <= v <= JU.BANDES_DELAIS[f][1] for f, v in d.items())
    ok = dans(d0) and dans(d1) and dans(moy) and bool(flag) and all(1 <= j <= 5 for j in flag) and 1.95 <= x <= 2.05
    return ok, ("installation " + ", ".join(f"{f} {v:.0f}" for f, v in d0.items()) + " j ; apres 45 jours "
                + ", ".join(f"{f} {v:.0f}" for f, v in d1.items()) + " ; deposes " + ", ".join(
                    f"{f} {v:.0f} ( {len(S.delais[f])} )" for f, v in moy.items())
                + f" ; flagrant delit {min(flag) if flag else '-'} a {max(flag) if flag else '-'} j ( {len(flag)} ) ; "
                  f"moitie des juges -> x{x:.2f} ; infractions x 40 : " + ", ".join(f"{f} {v:.0f}" for f, v in charge.items()))


# ================================================================== les prisons et l argent
def _prison(graine=13):
    if ("prison", graine) not in _CACHE:
        w, p = T.monde(["justice"], graine=graine, echelle=10)
        _CACHE[("prison", graine)] = (w, p)
    return _CACHE[("prison", graine)]


def test_detenus_et_vivres():
    """5 000 habitants, 6 jours. Chaque soir, apres la paie : tout detenu vivant est ABSENT, sans emploi ( travail -1 ),
    sans heures payees, domicilie a sa prison. Vivres : achetees = mangees + stock des prisons ( 1e-9 ) ; rations
    servies + detenus affames = detenus x jours ; ce que le grand livre a vu consommer sous le motif repas_detenus =
    ce que le domaine dit avoir mange. Au moins un detenu."""
    w, p = _prison()
    S = JU._dom(p); tb = w.table
    viol = []; attendu = 0; livre_mange = 0.0; r0 = S.vivres["rations"] + S.vivres["affames"]; m0 = S.vivres["mange"]
    for _ in range(6):
        _a_l_heure(w, 19.0)
        for h in list(S.detentions):
            if not tb.vivant[h]: continue
            if tb.statut[h] != PO.ABSENT or tb.travail[h] >= 0 or tb.heures[h] > 0 or \
                    tb.domicile[h] != S.prisons[S.detentions[h].prison].lieu_n: viol.append(h)
        attendu += sum(1 for h in S.detentions if tb.vivant[h])
        _a_l_heure(w, 6.0)
        livre_mange += sum(q for n, m, b, q in (p.comptes_hier or {}).get("biens", ()) if m == "repas_detenus" and n == "consomme")
    ach, man, stock = JU.bilan_vivres(p)
    servis = S.vivres["rations"] + S.vivres["affames"] - r0
    ok = (not viol and len(S.detentions) >= 1 and abs(ach - man - stock) <= 1e-9 and servis == attendu
          and abs(livre_mange - (man - m0)) <= 1e-9 * max(1.0, man))
    return ok, (f"{len(S.detentions)} detenus, {sum(pr.places for pr in S.prisons)} places ; hors travail et hors menage : "
                f"{'oui' if not viol else f'NON {viol}'} ; vivres achetees {ach:.2f}, mangees {man:.2f}, stock {stock:.2f} ; "
                f"rations + affames {servis} pour {attendu} detenus-jours ; grand livre repas_detenus {livre_mange:.2f}")


def test_amendes_au_tresor():
    """Huit flagrants delits de vol ( auteurs distincts, qui ont de quoi payer ) dans le pays de 5 000 habitants,
    juges sous trois jours ouvres ( 7 jours suivis ) : chaque amende payee est entree au Tresor ( le grand livre voit, sous le motif amende, les
    amendes du moteur E1 plus celles-ci, au centime ) ; le reste impaye est une creance de l Etat ; chaque peine a son
    jugement ; au moins une amende."""
    w, p = pickle.loads(pickle.dumps(_prison()))
    p = w.pays; S = JU._dom(p); tb = w.table
    _a_l_heure(w, 1.0)
    J = JU._poids(p, S)
    rng = np.random.default_rng(3)
    auteurs = [int(i) for i in J.ids if w.menages[int(tb.menage[i])].caisse > 2000.0][:40]
    auteurs = sorted(rng.choice(auteurs, 8, replace=False).tolist())
    for h in auteurs:
        v = JU._victime_menage(J, int(J.zone_h[h]), int(tb.menage[h]), rng)
        JU.deposer_plainte(p, "vol_simple", auteur=h, victime_menage=v, tort=100.0, flagrant=True)
    L = p.socle.livre
    amende_livre = 0.0; e1 = getattr(w, "amendes_totales", 0.0)
    for _ in range(7):
        _a_l_heure(w, 23 + 50 / 60)
        amende_livre += sum(s for (m, pa, re), (s, _) in L.jour_argent.items() if m == "amende" and re == "Gouvernement")
        w.pas_suivant()
    e1 = getattr(w, "amendes_totales", 0.0) - e1
    payees = sum(v[0] for v in S.amendes_de.values())
    K = p.socle.creances
    rec = 0.0; ok_cr = True
    etat = {c.id for c in ET.creances_de_l_etat(p)}
    for jid, (paye, cr) in S.amendes_de.items():
        if cr is None: continue
        if K.actives.get(cr.id) is cr: ok_cr &= cr.id in etat
        rec += S.jugements[jid].amende - paye - (cr.montant if K.actives.get(cr.id) is cr else 0.0)
    juges = [d for d in S.dossiers.values() if d.file == "autophoro" and d.jugement >= 0]
    audit = JU.audit(p)
    ok = (len(S.amendes_de) >= 1 and abs(amende_livre - e1 - payees - rec) <= 1e-6 and ok_cr
          and not audit["peine_sans_jugement"] and len(juges) == 8)
    return ok, (f"{len(juges)} flagrants delits juges, {len(S.amendes_de)} amendes : payees {payees:.2f} dr, recouvrees "
                f"ensuite {rec:.2f} ; grand livre ( motif amende vers l Etat ) {amende_livre:.2f} dont moteur E1 {e1:.2f} ; "
                f"restes en creances de l Etat : {'oui' if ok_cr else 'NON'}")


# ================================================================== le droit civil
def test_expulsions_par_le_tribunal():
    """1 000 habitants. Trois baux mis en litige a la main ( trois termes impayes, comme le domaine 13 le fait ) et le
    delai d expulsion du domaine 13 mis a zero : le lendemain matin, apres le matin du 13, les trois baux sont encore
    la ( il n expulse plus seul ). Files videes, aucun report : sous 6 jours, le tribunal a juge les trois litiges et
    les trois locataires sont expulses ( par le tribunal ), leurs arrieres sous titre executoire ; audit propre.
    Falsificateur : une expulsion appelee a la main, sans jugement, est vue."""
    w, p = T.monde(["justice"], graine=13, echelle=2)
    S = JU._dom(p); d13 = IM._dom(p); K = p.socle.creances
    _a_l_heure(w, 1.0)
    choisis = [b for b in sorted(d13.baux) if (p.jour - d13.baux[b].debut_j) % 30 < 15 and d13.baux[b].litige_j < 0][:4]
    for bid in choisis[:3]:
        bail = d13.baux[bid]
        bailleur = IM.proprietaire(p, bail.b)
        for _ in range(3): bail.impayes.append(K.constater(bailleur, bail.locataire, bail.loyer, "loyer", p.jour))
        bail.litige_j = p.jour; d13.litiges[bid] = p.jour
    d13.delai_expulsion_j = 0
    JU.vider_les_files(p); JU.scenario(p, reports=0.0, juges=1000.0)   # un tribunal sans arriere ( un dossier y pese 1/capacite )
    _a_l_heure(w, 7.0 + 10 / 60)
    encore = all(b in d13.baux for b in choisis[:3])
    en_justice = all(b in S.baux_en_justice for b in choisis[:3])
    T.jours(w, 6)
    partis = all(b not in d13.baux for b in choisis[:3])
    a = JU.audit(p)
    titres = sum(1 for e in S.titres.values() if e is not None and e[0].motif == "loyer")
    propre = JU.audit_propre(a)
    fals = pickle.loads(pickle.dumps(w)); pf = fals.pays
    autre = [b for b in sorted(IM._dom(pf).baux)][0]
    IM.expulser(pf, autre)
    vu = JU.audit(pf)["expulsion_sans_jugement"]
    ok = len(choisis) >= 3 and encore and en_justice and partis and S.expulsions_jugees == 3 and propre and vu == 1
    return ok, (f"3 baux en litige : apres le matin du 13, encore la {encore}, au tribunal {en_justice} ; apres 6 jours "
                f"expulses par jugement {S.expulsions_jugees} ( partis {partis} ), creances de loyer sous titre {titres} ; "
                f"audit {'propre' if propre else a} ; expulsion a la main vue : {vu}")


def test_interets_de_retard():
    """500 habitants, 35 jours. Une creance civile de 100 000 dr sous titre ( loyer ) sur un menage sans disponible, et une
    amende de 5 000 dr a un autre ( creance de l Etat ). Les interets courent au taux legal ( taux directeur + 8 points ) et a 0,73 % par
    mois pour l Etat, SIMPLES : chaque calcul du journal = principal restant x taux x jours / 365 ( 1e-9 ), aucun sur une
    creance d interets ; les deux creances ont porte interet ( > 0 ). Imputation ( code civil art. 423 ) : une saisie
    paie les interets du debiteur avant le principal."""
    w, p = T.monde(["justice"], graine=17, echelle=1)
    S = JU._dom(p); K = p.socle.creances; tb = w.table; M = tb.menages.n
    cm = tb.menages.caisse[:M]
    riche = int(np.argmax(cm)); pauvre = int(np.argmin(np.where(cm > 0, cm, np.inf)))
    creancier = w.menages[(riche + 1) % M]
    nv = np.bincount(tb.menage[:tb.n][(tb.vivant[:tb.n] == 1) & (tb.menage[:tb.n] >= 0)], minlength=M)
    secs = sorted((k for k in range(M) if nv[k] > 0 and k != riche), key=lambda k: (IM.disponible(p, w.menages[k]), k))
    c = K.constater(creancier, w.menages[secs[0]], 100000.0, "loyer", p.jour)
    JU.titre_executoire(p, c)
    _, cr = ET.infliger_amende(p, w.menages[secs[1]], 5000.0 + w.menages[secs[1]].caisse)
    tl, tf = JU.taux_legal(p), JU.TAUX_FISCAL_MOIS * 12
    T.jours(w, 35)
    log = S.interets_log
    exact = all(abs(x - m * t * j / 365.0) <= 1e-9 * max(1.0, x) for _, m, t, j, x in log)
    ids_interets = {i for i, e in S.titres.items() if e is not None and e[0].motif in JU.MOTIFS_INTERET} | set(S.interets_etat)
    anatocisme = [cid for cid, *_ in log if cid in ids_interets]
    civ = [e for e in log if e[0] == c.id]; fis = [e for e in log if cr is not None and e[0] == cr.id]
    taux_ok = all(abs(e[2] - tl) < 1e-12 for e in civ) and all(abs(e[2] - tf) < 1e-12 for e in fis)
    # l imputation : sur le menage le plus riche, un principal et des interets sous titre, puis une saisie
    dispo = JU._saisissable(p, w.menages[riche])
    c2 = K.constater(creancier, w.menages[riche], 4.0 * dispo, "loyer", p.jour)
    i2 = K.constater(creancier, w.menages[riche], 0.5 * dispo, "interet_moratoire", p.jour)
    JU.titre_executoire(p, c2); JU.titre_executoire(p, i2)
    I0, P0 = i2.montant, c2.montant
    JU._recouvrer(p)
    I1 = i2.montant if K.actives.get(i2.id) is i2 else 0.0; P1 = c2.montant
    paye = (I0 - I1) + (P0 - P1)
    ordre = I1 <= 1e-9 and abs(paye - dispo) <= 1e-6 * max(1.0, dispo) and abs((P0 - P1) - (dispo - I0)) <= 1e-6 * max(1.0, dispo)
    ok = exact and not anatocisme and bool(civ) and bool(fis) and taux_ok and ordre and dispo > 0
    return ok, (f"{len(log)} calculs d interets, exacts {exact}, sur une creance d interets : {len(anatocisme)} ; civil "
                f"{sum(e[4] for e in civ):.2f} dr a {tl:.2%} ( {len(civ)} calculs ), Etat {sum(e[4] for e in fis):.2f} dr a "
                f"{tf:.2%} ( {len(fis)} ) ; saisie de {paye:.2f} dr : interets {I0:.2f} -> {I1:.2f}, principal {P0:.2f} -> "
                f"{P1:.2f} ( dispo {dispo:.2f} )")


# ================================================================== les falsificateurs
def test_falsificateurs():
    """Sur le pays de 5 000 habitants apres 6 jours : l audit est propre ; puis, chacun sur une copie : un habitant
    enferme a la main sans jugement, une amende executee sans jugement, un detenu remis au travail - chacun est vu."""
    w, p = _prison()
    if p.jour < 3: T.jours(w, 6)
    a0 = JU.audit(p)
    def copie():
        x = pickle.loads(pickle.dumps(w)); return x, x.pays, JU._dom(x.pays)
    x, px, S = copie(); tb = x.table
    libre = int(np.nonzero((tb.vivant[:tb.n] == 1) & (px.col("habitant", "ju_detenu")[:tb.n] == 0))[0][0])
    S.detentions[libre] = JU.Detention(libre, 0, px.jour, px.jour + 30, JU.PEINE, -1, int(tb.menage[libre]), -1, 0)
    px.col("habitant", "ju_detenu")[libre] = JU.PEINE
    tb.statut[libre] = PO.ABSENT; tb.domicile[libre] = S.prisons[0].lieu_n
    v1 = libre in JU.audit(px)["detenu_sans_titre"]
    x, px, S = copie()
    S.peines.append((-7, 3, "amende", 50.0))
    v2 = bool(JU.audit(px)["peine_sans_jugement"])
    x, px, S = copie(); tb = x.table
    det = sorted(h for h in S.detentions if tb.vivant[h])
    v3 = False
    if det:
        tb.travail[det[0]] = x.carte.capitales[0].n
        v3 = det[0] in JU.audit(px)["detenu_au_travail"]
    ok = JU.audit_propre(a0) and v1 and v2 and v3
    return ok, (f"audit {'propre' if JU.audit_propre(a0) else a0} ; enferme sans jugement vu {v1} ; amende sans jugement "
                f"vue {v2} ; detenu au travail vu {v3}")


# ================================================================== la decision
def test_decision():
    """Le point `enquete`, en mode hasard : 10 000 habitants, 30 jours, infractions x 60, enqueteurs x 20 ( la penurie :
    le choix compte ). Au moins 150 notes et 3 jours ou chaque critere a 2 notes ; part du choix >= 0,01 ET p de
    permutation < 0,05. En regard ( sans seuil ) : la note moyenne sous la regle et sous le temoin."""
    w, p = _campagne(20.0, graine=29, echelle=20, crime=60.0, jours=30, mode="hasard")
    dec = JU._dom(p).decideur
    part, pval = dec.part_du_choix(), dec.p_permutation()
    notes = sum(n for n, _, _ in dec.stats.values())
    par_jour = {}
    for (j, a), (n_, _, _) in dec.stats.items(): par_jour.setdefault(j, {})[a] = n_
    jours_ok = sum(1 for d in par_jour.values() if all(d.get(a, 0) >= 2 for a in range(len(JU.CRITERES))))
    moy = {}
    for m in ("regle", "temoin"):
        dm = JU._dom(_campagne(20.0, graine=29, echelle=20, crime=60.0, jours=30, mode=m)[1]).decideur
        n_ = sum(n for n, _, _ in dm.stats.values()); s_ = sum(s for _, s, _ in dm.stats.values())
        moy[m] = s_ / n_ if n_ else float("nan")
    ok = notes >= 150 and jours_ok >= 3 and part >= 0.01 and pval < 0.05
    return ok, (f"{dec.n_decisions} decisions, {notes} notes, {jours_ok} jours a 2 notes par critere ; part du choix "
                f"{part:.3f}, p {pval:.3f} ; notes " + ", ".join(f"{a} {m:.3f} ( {n} )" for a, (n, m) in dec.notes_par_action().items())
                + f" ; note moyenne sous la regle {moy['regle']:.3f}, sous le temoin {moy['temoin']:.3f}")


def test_pays_vivable():
    return T.porte_commune("justice", n_jours=12)


# ================================================================== le cout
def test_cout():
    """A 10 000 habitants, coeur Rust : les routines propres du domaine ( une journee, appelees une a une ) coutent au plus
    25 % d une journee du moteur seul. Installer le domaine sur ses dependances deja installees coute a 100 000 habitants
    au plus 20 fois ce qu il coute a 10 000 ( lineaire : ~ 10 ; quadratique : ~ 100 )."""
    w0 = W.Monde(echelle=20)
    T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    inst = {}
    for ech in (20, 200):
        w = W.Monde(echelle=ech)
        P.installer(w, ["immobilier"])
        t0 = time.perf_counter(); P.installer(w, ["justice"]); inst[ech] = time.perf_counter() - t0
        if ech == 20: w20 = w
    p = w20.pays; S = JU._dom(p)
    T.jours(w20, 1)
    routines = (JU._delits, JU._prisons_matin, JU._interets, JU._doter, JU._baux, JU._enquetes, JU._fraudes_fiscales,
                JU._tribunaux, JU._radiations_avant, JU._radiations_apres, JU._recouvrer_etat, JU._recouvrer,
                JU._vivres_achat, JU._vivres_repas, JU._contrebande, JU._du_soir, JU._paie, JU._noter_enquetes)
    t0 = time.perf_counter()
    for _ in range(3):
        for f in routines: f(p)
        JU._cloture(p, None)
    propre = (time.perf_counter() - t0) / 3
    ratio = inst[200] / inst[20]
    ok = propre <= 0.25 * t_e1 and ratio <= 20.0
    return ok, (f"coeur Rust {'present' if W.COEUR is not None else 'ABSENT'} ; {len(w20.habitants)} habitants, "
                f"{len(S.detentions)} detenus, {len(S.affaires)} affaires : moteur seul {t_e1:.2f} s par jour, routines "
                f"propres {propre * 1000:.1f} ms ( {propre / t_e1:.1%} ) ; installation {inst[20]:.3f} s a 10 000, "
                f"{inst[200]:.3f} s a 100 000 ( x{ratio:.1f} )")


TESTS = [test_taux_delits, test_elucidation_et_effort, test_delais_grecs, test_detenus_et_vivres, test_amendes_au_tresor,
         test_expulsions_par_le_tribunal, test_interets_de_retard, test_falsificateurs, test_decision, test_pays_vivable,
         test_cout]
