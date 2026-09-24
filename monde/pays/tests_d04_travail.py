"""Les portes du domaine 4 ( travail et metiers ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests travail"""
import math, time
import numpy as np
from .. import config as C, monde as W
from ..socle import registre as R
from . import essais as T, d01_population as POP, d03_economie as ECO, d04_travail as M

PAS_H = C.PAS_PAR_JOUR // 24
MOTIFS_SALAIRE = ("salaire", "salaire public")
MOTIFS_COTISATION = ("cotisation_salariale", "cotisation_patronale")


def _avancer(w, heures):
    for _ in range(int(round(heures * PAS_H))): w.pas_suivant()


def _flux(L, motifs, receveur=None):
    return math.fsum(s for (m, pa, re), (s, n) in L.jour_argent.items() if m in motifs and (receveur is None or re == receveur))


def _employes(p, statuts=M.PAYES_A_L_HEURE):
    st = p.col("habitant", "tr_statut")
    return [h for h in p.w.habitants if h.vivant and h.travail is not None and st[h.id] in statuts
            and h.role not in M.POLITIQUES]


# ================================================================== les salaires
def test_bulletins_au_centime():
    """Porte : un jour de paie ( jour 2 ), chaque bulletin tient au centime - brut = net verse + cotisation salariale +
    impot retenu + cotisation syndicale, chaque ligne en centimes entiers - et l argent que le grand livre voit bouger
    pendant le pas de 18 h est celui des bulletins : nets verses aux menages, cotisations a la caisse, impot a l Etat,
    a 1e-6 drachme pres, sans arriere ce jour-la. Falsificateurs : un centime ajoute apres coup au net d un bulletin, et
    un salaire de 5 drachmes verse a la main pendant la paie, sont vus."""
    w, p = T.monde(["travail"])
    d = p.domaine("travail"); L = p.socle.livre
    d.garder_bulletins = True
    T.jours(w, 2); _avancer(w, 12)                       # le prochain pas est celui de 18 h
    avant = {k: _flux(L, m, r) for k, m, r in (("sal", MOTIFS_SALAIRE, "Menage"), ("cot", MOTIFS_COTISATION, "CaisseSecuriteSociale"),
                                              ("ir", ("impot sur le revenu",), "Gouvernement"))}
    w.pas_suivant()
    apres = {k: _flux(L, m, r) for k, m, r in (("sal", MOTIFS_SALAIRE, "Menage"), ("cot", MOTIFS_COTISATION, "CaisseSecuriteSociale"),
                                              ("ir", ("impot sur le revenu",), "Gouvernement"))}
    b = d.bulletins
    e1, e2, nb = M.verifier_bulletins(p)
    net = math.fsum(x[8] for x in b)
    cot = math.fsum((x[3] + x[4]) * x[9] for x in b)
    ir = math.fsum(x[5] * x[9] for x in b)
    ec = {"sal": apres["sal"] - avant["sal"] - net, "cot": apres["cot"] - avant["cot"] - cot, "ir": apres["ir"] - avant["ir"] - ir}
    tol = 1e-6
    tient = nb >= 50 and e1 <= 0.005 and e2 <= 1e-6 and all(abs(v) <= tol for v in ec.values()) and d.jour["arrieres_payes"] == 0.0
    brut = math.fsum(x[2] for x in b)
    # falsificateur 1 : un centime de plus sur un net
    i0 = b[0]; b[0] = i0[:7] + (i0[7] + 0.01,) + i0[8:]
    vu_centime = M.verifier_bulletins(p)[0] > 0.005
    b[0] = i0
    # falsificateur 2 : un salaire paye hors de la paie, sous le meme motif
    e = next(e for e in w.entreprises.values() if e.type != "ferme" and e.caisse > 10)
    L.transferer(e, w.menages[0], 5.0, "salaire")
    vu_main = abs(_flux(L, MOTIFS_SALAIRE, "Menage") - avant["sal"] - net) > tol
    ok = tient and vu_centime and vu_main
    return ok, (f"{nb} bulletins, brut {brut:.2f}, net verse {net:.2f} ; ecart au centime {e1:.1e}, lignes en centimes a "
                f"{e2:.1e} ; grand livre moins bulletins : salaires {ec['sal']:+.1e}, cotisations {ec['cot']:+.1e}, impot "
                f"{ec['ir']:+.1e} ; arrieres du jour {d.jour['arrieres_payes']:.2f} ; centime ajoute vu {vu_centime}, salaire "
                f"a la main vu {vu_main}")


def test_caisse_securite_sociale():
    """Porte : sur 20 jours, la variation de la caisse = cotisations recues + financement de l Etat - prestations
    versees - reserves placees, a la tolerance du registre ; le grand livre en dit autant ( rapprochement de la famille
    securite_sociale nul ) ; la caisse a recu des cotisations, verse des pensions et des indemnites, et l Etat a verse au
    moins la part nationale des pensions. Falsificateur : 100 drachmes retirees a la main de la caisse sont vues des
    deux cotes."""
    w, p = T.monde(["travail"])
    d = p.domaine("travail"); L = p.socle.livre
    rap = R.Rapprochement(p.socle.registre, L)
    c0 = d.caisse.caisse
    nat_j = math.fsum(pn.nationale_par_jour() for pn in d.pensions.values())
    T.jours(w, 20)
    recu, verse = math.fsum(d.caisse.recu.values()), math.fsum(d.caisse.verse.values())
    var = d.caisse.caisse - c0
    ecart = var - (recu - verse - d.placements)
    tol = R.tolerance(abs(var), recu + verse)
    reste = rap.restes()["securite_sociale"]
    cot = sum(v for k, v in d.caisse.recu.items() if k.startswith("cotisation"))
    fin = d.caisse.recu.get("financement_etat_securite_sociale", 0.0)
    pen = d.caisse.verse.get("pension_vieillesse", 0.0) + d.caisse.verse.get("pension_invalidite", 0.0)
    ind = d.caisse.verse.get("indemnite_chomage", 0.0)
    tient = abs(ecart) <= tol and abs(reste) <= tol and cot > 0 and pen > 0 and ind > 0 and fin >= 0.95 * 20 * nat_j
    d.caisse.caisse -= 100.0
    vu = (abs(rap.restes()["securite_sociale"] + 100.0) <= 1e-6
          and abs(d.caisse.caisse - c0 - (recu - verse - d.placements) + 100.0) <= 1e-6)
    ok = tient and vu
    return ok, (f"20 jours : cotisations {cot:.0f}, Etat {fin:.0f} ( part nationale attendue {20 * nat_j:.0f} ), pensions "
                f"{pen:.0f}, indemnites {ind:.0f}, placements {d.placements:.0f} ; caisse {var:.2f}, ecart {ecart:+.1e}, "
                f"rapprochement {reste:+.1e} ( tolerance {tol:.1e} ) ; 100 drachmes a la main vues {vu}")


# ================================================================== l emploi
def test_emploi_20_64():
    """Porte : le taux d emploi des 20-64 ans, standardise sur une population a moitie feminine, est dans la bande de
    62,6 % ( Eurostat 2021 ) a 5 points pres, au recensement ET apres 30 jours ; au recensement, hommes a 72,6 % et
    femmes a 52,4 % a 7 points pres. Le taux brut et la part des hommes ( domaine 1 ) sont rapportes. Controle positif :
    sans le recensement des inactifs ( le moteur ), le taux standardise depasse 95 %."""
    M.RECENSER_INACTIFS = False
    try: w0, p0 = T.monde(["travail"])
    finally: M.RECENSER_INACTIFS = True
    moteur = M.mesurer_emploi(p0)
    w, p = T.monde(["travail"])
    m0 = M.mesurer_emploi(p)
    T.jours(w, 30)
    m30 = M.mesurer_emploi(p)
    bande = (M.CIBLE_EMPLOI_20_64 - 0.05, M.CIBLE_EMPLOI_20_64 + 0.05)
    dans = [bande[0] <= m["taux_standardise"] <= bande[1] for m in (m0, m30)]
    sexes = abs(m0["taux_hommes"] - 0.726) <= 0.07 and abs(m0["taux_femmes"] - 0.524) <= 0.07
    positif = moteur["taux_standardise"] > 0.95
    ok = all(dans) and sexes and positif
    return ok, (f"recensement : standardise {m0['taux_standardise']:.1%} ( hommes {m0['taux_hommes']:.1%}, femmes "
                f"{m0['taux_femmes']:.1%} ), brut {m0['taux_emploi']:.1%} avec {m0['part_hommes']:.0%} d hommes, chomage "
                f"{m0['taux_chomage']:.1%} ; jour 30 : standardise {m30['taux_standardise']:.1%}, brut {m30['taux_emploi']:.1%}, "
                f"chomage {m30['taux_chomage']:.1%} ; bande {bande[0]:.1%}-{bande[1]:.1%} ; moteur sans inactifs "
                f"{moteur['taux_standardise']:.1%} ; statuts jour 30 {m30['statuts']}")


def test_inactifs_changent():
    """Mesure de ce que les inactifs changent : deux mondes de meme graine, 30 jours, avec et sans le recensement des
    inactifs. Porte : les deux restent vivables ( au plus 5 % de menages sans repas chaque soir ), le monde avec
    inactifs produit au moins 85 % de la nourriture de l autre ( le moteur tournait avec un tiers de capacite
    oisive ), et son sous-emploi ( heures que les entreprises n ouvrent pas ) est plus bas. Rapportes : production
    d outils, menages sans revenu du travail, caisse de l Etat, salaires verses."""
    res = {}
    for avec in (False, True):
        M.RECENSER_INACTIFS = avec
        try: w, p = T.monde(["travail"])
        finally: M.RECENSER_INACTIFS = True
        L = p.socle.livre
        n0 = L.flux["produit"]["nourriture"]; o0 = L.flux["produit"]["outils"]
        faim = 0.0; sous = []
        for _ in range(30):
            T.jours(w, 1)
            faim = max(faim, T.faim(w)); sous.append(ECO.chomage(p)["sous_emploi"])
        d = p.domaine("travail")
        n = len(w.habitants)
        net = p.col("habitant", "tr_net_jour")[:n]
        par_menage = np.bincount([h.menage.id for h in w.habitants if h.vivant],
                                 weights=[float(net[h.id]) for h in w.habitants if h.vivant], minlength=len(w.menages))
        habites = [m.id for m in T.menages_habites(w)]
        res[avec] = {"nourriture": L.flux["produit"]["nourriture"] - n0, "outils": L.flux["produit"]["outils"] - o0,
                     "faim": faim, "sous_emploi": float(np.mean(sous)), "sans_revenu": float(np.mean(par_menage[habites] <= 0.0)),
                     "etat": w.gouv.caisse, "salaires": d.cumul.get("net_paye", 0.0), "chomage": M.mesurer_emploi(p)["taux_chomage"]}
    a, s = res[True], res[False]
    ok = a["faim"] <= 0.05 and s["faim"] <= 0.05 and a["nourriture"] >= 0.85 * s["nourriture"] and a["sous_emploi"] < s["sous_emploi"]
    f = lambda r: (f"nourriture {r['nourriture']:.0f}, outils {r['outils']:.1f}, sous-emploi {r['sous_emploi']:.0%}, faim max "
                   f"{r['faim']:.1%}, menages sans revenu du jour {r['sans_revenu']:.0%}, nets verses {r['salaires']:.0f}, "
                   f"Etat {r['etat']:.0f}, chomage {r['chomage']:.1%}")
    return ok, f"sans inactifs : {f(s)} ; avec : {f(a)}"


# ================================================================== les greves
def test_greve():
    """Controle positif : une greve de 2 jours a la mine arrete SA production ( zero unite produite pendant la greve )
    pendant que les autres entreprises produisent ; aucun greviste n a de bulletin ; la production reprend apres, les
    grevistes retrouvent leur horaire ; les salaires perdus sont comptes. Controle de la regle : des arrieres de salaire
    poses a la main ( 4 jours de paie, en creances ) font debrayer un etablissement syndique au matin suivant."""
    w, p = T.monde(["travail"])
    d = p.domaine("travail"); d.garder_bulletins = True
    T.jours(w, 3)
    e = next(x for x in w.entreprises.values() if x.type == "mine")
    gv = M.declencher_greve(p, e.lieu.id, e.role, 2, "essai")
    grevistes = set(gv.horaires) if gv else set()
    avant = sum(e.produit_du_jour.values())
    autres0 = sum(sum(x.produit_du_jour.values()) for x in w.entreprises.values() if x is not e)
    bulletins = 0
    for _ in range(2):
        T.jours(w, 1)
        bulletins += sum(1 for b in d.bulletins if b[0] in grevistes)
    pendant = sum(e.produit_du_jour.values()) - avant
    autres = sum(sum(x.produit_du_jour.values()) for x in w.entreprises.values() if x is not e) - autres0
    T.jours(w, 2)
    apres = sum(e.produit_du_jour.values()) - avant - pendant
    rendus = all(w.habitants[i].horaire is not None for i in grevistes if w.habitants[i].travail is e.lieu)
    fini = gv is not None and gv.fin >= 0 and (e.lieu.id, e.role) not in d.en_greve
    controle = gv is not None and len(grevistes) >= 3 and pendant == 0.0 and autres > 0 and bulletins == 0 and apres > 0 \
        and rendus and fini and gv.salaires_perdus > 0
    # la regle : des arrieres poses a la main
    cible = next(x for x in w.entreprises.values() if x.type == "fonderie")
    gens = [h for h in M._membres(p, cible.lieu.id, cible.role)]
    col = p.colonnes["habitant"]
    col["tr_syndique"][gens[0].id] = 1
    paie = math.fsum(M._net_jour(p, float(col["tr_taux"][h.id]), float(col["tr_heures_prevues"][h.id]), h.role) for h in gens)
    for h in gens: p.socle.creances.constater(h.menage, cible, 4.0 * paie / len(gens), "salaire", p.jour)
    tresor = p.socle.livre.transferer(cible, w.gouv, cible.caisse, "amende")      # la fonderie ne peut plus payer
    _avancer(w, 24)
    regle = (cible.lieu.id, cible.role) in d.en_greve and d.en_greve[(cible.lieu.id, cible.role)].motif == "arrieres"
    ok = controle and regle
    return ok, (f"mine : {len(grevistes)} grevistes, production pendant la greve {pendant:.2f} ( avant {avant:.1f} ), autres "
                f"entreprises {autres:.1f}, bulletins de grevistes {bulletins}, apres la greve {apres:.1f}, horaires rendus "
                f"{rendus}, salaires perdus {gv.salaires_perdus if gv else 0:.0f} ; arrieres de 4 jours poses a la fonderie "
                f"( caisse videe de {tresor:.0f} ) : greve declenchee {regle}")


# ================================================================== la retraite
def test_retraite():
    """Porte : un salarie qui atteint 62 ans avec 12 000 jours d assurance ( 40 ans ) part le matin meme ( decision du
    domaine, le domaine 1 ne met a la retraite qu a 65 ans ) avec la pension du bareme grec calculee a la main : taux
    contributif 50,01 %, pension nationale pleine, sans penalite ; un salarie qui atteint 65 ans avec 30 ans est mis a
    la retraite par le domaine 1 et recoit 12 % de moins ( 24 mois x 1/200 ) ; un salarie de 61,5 ans a 12 500 jours
    reste. Le lendemain soir, la caisse verse a chacun sa pension du jour ( mensuelle x 12 / 365 )."""
    w, p = T.monde(["travail"])
    d = p.domaine("travail"); col = p.colonnes["habitant"]
    T.jours(w, 1); _avancer(w, 13)                       # 19 h : la paie du jour est faite
    A, B, C_ = [h for h in _employes(p, (M.SALARIE, M.FONCTIONNAIRE)) if 30 <= POP.age_de(p, h) < 60
                and h.horaire in ("jour", "bureau", "ecole") and h.role != "convoyeur"][:3]      # rien a payer la nuit
    nj = col["naissance_j"]
    nj[A.id] = p.jour + 1 - 62 * 365; nj[B.id] = p.jour + 1 - 65 * 365; nj[C_.id] = p.jour - int(61.5 * 365)
    for h, jours in ((A, 12000.0), (B, 9000.0), (C_, 12500.0)):
        col["tr_jours_cotises"][h.id] = jours; col["tr_assiette"][h.id] = jours / 25.0 * 1500.0
    _avancer(w, 11 + 1 / 3)                               # le lendemain, 6 h 20
    nat = 413.76 / 1.15
    taux40 = (15 * 0.77 + 3 * 0.84 + 3 * 0.90 + 3 * 0.96 + 3 * 1.03 + 3 * 1.21 + 3 * 1.98 + 3 * 2.50 + 4 * 2.55) / 100
    taux30 = (15 * 0.77 + 3 * 0.84 + 3 * 0.90 + 3 * 0.96 + 3 * 1.03 + 3 * 1.21) / 100
    attendu_a = nat + 1500.0 * taux40
    attendu_b = (nat + 1500.0 * taux30) * (1.0 - 24 / 200)
    pa, pb = d.pensions.get(A.id), d.pensions.get(B.id)
    liquidees = (pa is not None and pb is not None and abs(pa.mensuelle - attendu_a) <= 1e-9 and abs(pb.mensuelle - attendu_b) <= 1e-9
                 and pa.jour == p.jour and pb.jour == p.jour and pa.penalite == 0.0 and abs(pb.penalite - 0.12) <= 1e-12)
    etats = (A.role == B.role == "retraite" and A.travail is None and col["tr_statut"][A.id] == M.RETRAITE
             and C_.role != "retraite" and C_.id not in d.pensions)
    _avancer(w, 12)                                      # 18 h 20 : la paie est passee
    verse = all(abs(float(col["tr_net_jour"][h.id]) - d.pensions[h.id].par_jour()) <= 1e-9 for h in (A, B))
    ok = abs(taux40 - 0.5001) <= 1e-12 and liquidees and etats and verse
    return ok, (f"40 ans a 62 ans : {pa.mensuelle if pa else 0:.2f} drachmes par mois ( attendu {attendu_a:.2f}, taux "
                f"{taux40:.2%} ) ; 30 ans a 65 ans : {pb.mensuelle if pb else 0:.2f} ( attendu {attendu_b:.2f}, penalite "
                f"{pb.penalite if pb else 0:.0%} ) ; 61,5 ans reste en poste {etats} ; pension du jour versee {verse}")


# ================================================================== heures payees = heures travaillees
def test_heures_payees_travaillees():
    """Porte : 3 jours ordinaires, aucune heure payee sans pointage ( convoyeurs compris : leur aller-retour est
    credite au depart ). Falsificateur : 8 heures creditees a la main a 17 h a un inactif, a un salarie deja rentre chez
    lui et a un salarie encore au travail sont vues a la paie du soir, et aucune autre."""
    w, p = T.monde(["travail"])
    d = p.domaine("travail"); col = p.colonnes["habitant"]
    T.jours(w, 3)
    avant = len(M.anomalies_heures(p))
    propre = avant == 0
    _avancer(w, 11)                                      # 17 h
    st = col["tr_statut"]
    x = next(h for h in w.habitants if h.vivant and st[h.id] in (M.AU_FOYER, M.CHOMEUR, M.DECOURAGE))
    y = next(h for h in _employes(p) if h.poste == "maison" and h.role != "convoyeur")
    z = next(h for h in _employes(p) if h.poste == "travail" and h.heures_jour >= 4.0 and h.role != "convoyeur")
    for h in (x, y, z): h.heures_jour += 8.0
    jour = p.jour
    _avancer(w, 1 + 1 / 6)
    vus = {a[1] for a in M.anomalies_heures(p, jour)}
    ok = propre and vus == {x.id, y.id, z.id}
    return ok, (f"3 jours ordinaires : {avant} anomalie(s) ; faux credits a un "
                f"{M.STATUTS[int(st[x.id])]}, a un {y.role} chez lui, a un {z.role} au travail : vus {sorted(vus)} pour "
                f"{sorted((x.id, y.id, z.id))}")


# ================================================================== la decision
def test_accepter_emploi():
    """Porte de la decision : la raffinerie ferme ( liquidee au jour 1 ), des postes s ouvrent dans les fonderies, les
    mines et les carrieres ; 1 500 habitants ; les candidats decident au hasard ( mode hasard ). La note doit dependre
    du choix : part du choix ( epsilon carre intra-jour, corrige des petits groupes ) >= 0,01 ET le hasard permute a jour
    egal ne fait pas aussi bien ( p < 0,05, 200 permutations ) ; au moins 100 decisions, et au moins 5 jours ou chaque
    action a recu au moins 2 notes ( sinon epsilon carre n a rien a comparer ) ; conservation tenue. Rapportes : notes
    par action, eta carre brut, et la regle et le temoin dans le meme scenario."""
    out = {}
    for mode in ("hasard", "regle", "temoin"):
        w, p = T.monde(["travail"], echelle=3, modes={"accepter_emploi": mode})
        d = p.domaine("travail")
        T.jours(w, 1)
        raf = next(e for e in w.entreprises.values() if e.type == "raffinerie")
        ECO.liquider(p, raf)
        for e in sorted(w.entreprises.values(), key=lambda e: e.id):
            if e.type in ("fonderie", "mine", "carriere", "pharmacie"):
                M.ouvrir_postes(p, e.lieu.id, e.role, M._effectif(p, e.lieu.id, e.role) + 12)
        T.jours(w, 20)
        dec = d.decideur
        par_jour = {}
        for (j, a), s in dec.stats.items(): par_jour.setdefault(j, {})[a] = s[0]
        jours2 = sum(1 for v in par_jour.values() if len(v) == 2 and min(v.values()) >= 2)
        out[mode] = (dec.n_decisions, dec.part_du_choix(), dec.notes_par_action(), jours2, p.socle.conservation.tenue(),
                     M.mesurer_emploi(p)["taux_chomage"], dec.p_permutation() if mode == "hasard" else 1.0,
                     dec.part_du_choix_brute())
    n, part, notes, jours2, (tenue, msg), _, p_perm, brute = out["hasard"]
    ok = n >= 100 and part >= 0.01 and p_perm < 0.05 and jours2 >= 5 and tenue
    txt = lambda o: ", ".join(f"{a} {m:.3f} ( {k} )" for a, (k, m) in o[2].items())
    return ok, (f"hasard : {n} decisions, {jours2} jours ou chaque action a 2 notes et plus, part du choix {part:.3f} "
                f"( eta carre brut {brute:.3f} ), p permutation {p_perm:.4f}, notes {txt(out['hasard'])}, "
                f"chomage final {out['hasard'][5]:.1%} ; regle : {out['regle'][0]} decisions, notes {txt(out['regle'])}, chomage "
                f"{out['regle'][5]:.1%} ; temoin : notes {txt(out['temoin'])}, chomage {out['temoin'][5]:.1%} ; {msg}")


# ================================================================== le chomage
def test_indemnite_chomage():
    """Porte : un salarie licencie apres plus de 14 mois de contrat ouvre 12 mois d indemnite, apres 6 jours de carence,
    a 55 % du salaire minimum journalier de l ouvrier sur 25 jours ( + 10 % par mineur a charge ) ; une demission et un
    contrat de moins de 125 jours n ouvrent rien ; le premier jour du, la caisse verse ( s il n a pas retrouve
    d emploi : sinon l indemnite est close )."""
    w, p = T.monde(["travail"])
    d = p.domaine("travail"); col = p.colonnes["habitant"]
    T.jours(w, 2)
    cands = [h for h in _employes(p, (M.SALARIE,)) if col["tr_contrat"][h.id] == M.CDI
             and col["tr_debut_j"][h.id] <= p.jour - 430]
    A, B = cands[0], cands[1]
    C_ = next(h for h in w.habitants if h.vivant and col["tr_statut"][h.id] == M.CHOMEUR and h.id not in (A.id, B.id))
    e = next(x for x in w.entreprises.values() if x.type == "fonderie")
    M.embaucher_contrat(p, C_, e, "ouvrier", M.CDI)
    ia = M.rompre_contrat(p, A, "economique")
    ib = M.rompre_contrat(p, B, "demission", involontaire=False)
    ic = M.rompre_contrat(p, C_, "economique")
    attendu = 0.55 * 37.07 / 1.15 * 25 * 12 / 365 * (1 + 0.10 * M._a_charge(p, A))
    ouverte = (ia is not None and abs(ia.jour - attendu) <= 1e-9 and ia.debut == p.jour + 6
               and ia.fin == ia.debut + 12 * 30 - 1 and ib is None and ic is None)
    T.jours(w, 6); _avancer(w, 12 + 1 / 6)                 # le 6e jour, apres la paie
    if col["tr_statut"][A.id] == M.CHOMEUR:
        verse = abs(float(col["tr_net_jour"][A.id]) - attendu) <= 1e-9 and d.caisse.verse.get("indemnite_chomage", 0) > 0
        etat = "verse"
    else:
        verse = A.id not in d.indemnites; etat = "reembauche, indemnite close"
    ok = ouverte and verse
    return ok, (f"licencie apres plus de 14 mois : {ia.jour if ia else 0:.3f} drachmes par jour ( attendu {attendu:.3f} ) du jour {ia.debut if ia else -1} au "
                f"{ia.fin if ia else -1} ; demission {ib} ; contrat d un jour {ic} ; jour {p.jour} : {etat} {verse}")


# ================================================================== carrieres, qualifications, syndicats
def test_carrieres():
    """Porte : 13 a 27 % de syndiques parmi les salaries au recensement ( OCDE 13,4 % en 2020, demande 20 % ) ; chaque
    metier qui exige un titre n est exerce que par un titulaire, au recensement et apres 30 jours ; un fonctionnaire qui
    franchit 2 ans d anciennete passe a l echelon suivant, son taux multiplie par ( 1 + 3,5 % x e ) / ( 1 + 3,5 % x
    ( e - 1 ) ) ; un salarie du prive de 2 ans n en franchit aucun. Rapportes : promotions sur 30 jours, grille."""
    w, p = T.monde(["travail"])
    d = p.domaine("travail"); col = p.colonnes["habitant"]
    synd = M.mesurer_emploi(p)["syndiques"]

    def titres_tenus():
        return all(M.peut_exercer(p, h, h.role) for h in w.habitants if h.vivant and h.travail is not None
                   and h.role in M.EXIGE and h.role != "enfant")
    t0 = titres_tenus()
    pub = next(h for h in _employes(p, (M.FONCTIONNAIRE,)) if 0 < col["tr_echelon"][h.id] < 18)
    pri = next(h for h in _employes(p, (M.SALARIE,)) if col["tr_echelon"][h.id] == 0)
    e0 = int(col["tr_echelon"][pub.id])
    col["tr_carriere_j"][pub.id] = p.jour + 1 - int(math.ceil((e0 + 1) * 2 * 365))
    col["tr_carriere_j"][pri.id] = p.jour - 2 * 365
    t_pub, t_pri = float(col["tr_taux"][pub.id]), float(col["tr_taux"][pri.id])
    T.jours(w, 2)
    e1 = int(col["tr_echelon"][pub.id])
    f = (1 + 0.035 * e1) / (1 + 0.035 * e0)
    promu = e1 == e0 + 1 and abs(float(col["tr_taux"][pub.id]) - t_pub * f) <= 1e-9 * t_pub
    reste = int(col["tr_echelon"][pri.id]) == 0 and float(col["tr_taux"][pri.id]) == t_pri
    T.jours(w, 28)
    t30 = titres_tenus()
    ok = 0.13 <= synd <= 0.27 and t0 and t30 and promu and reste
    return ok, (f"syndiques {synd:.1%} ; titres tenus au recensement {t0}, a 30 jours {t30} ; fonctionnaire echelon {e0} -> "
                f"{e1}, taux x{float(col['tr_taux'][pub.id]) / t_pub:.4f} ( attendu x{f:.4f} ) ; prive de 2 ans inchange {reste} ; "
                f"SMIC {M.SMIC_HORAIRE:.2f} drachmes de l heure, indemnite {M.INDEMNITE_JOUR:.2f} par jour")


# ================================================================== le pays et le cout
def test_pays_vivable():
    return T.porte_commune("travail", n_jours=12)


def test_cout():
    """Les routines propres du domaine coutent au plus 25 % d une journee du moteur seul, a 10 000 habitants ; le pays
    avec le travail au plus 1,5 fois le pays sans ( population, banques, economie )."""
    def jour_moyen(doms):
        w = W.Monde(echelle=20)
        if doms: T.P.installer(w, doms)
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants)
    t_e1, n = jour_moyen(None)
    t_eco, _ = jour_moyen(["economie"])
    t_tr, _ = jour_moyen(["travail"])
    w, p = T.monde(["travail"], echelle=20); T.jours(w, 3)
    t0 = time.perf_counter()
    for _ in range(3):
        M._carrieres(p); M._marche_du_travail(p); M._greves(p)
        for _ in range(C.PAS_PAR_JOUR - 1): M._pointer(p)
        M._paie(p); M._noter_offres(p); M._bilan_du_jour(p)
    propre = (time.perf_counter() - t0) / 3
    ok = propre <= 0.25 * t_e1 and t_tr <= 1.5 * t_eco
    return ok, (f"{n} habitants : moteur seul {t_e1:.2f} s par jour, avec l economie {t_eco:.2f} s, avec le travail {t_tr:.2f} s ; "
                f"routines propres {propre * 1000:.0f} ms par jour ( {propre / t_e1:.0%} du moteur ), {propre / n * 1e6:.1f} us "
                f"par habitant : ~ {propre / n * 1e6:.0f} s par jour a 1 million, {propre / n * 5e7 / 60:.0f} min a 50 millions")


TESTS = [test_bulletins_au_centime, test_caisse_securite_sociale, test_emploi_20_64, test_inactifs_changent, test_greve,
         test_retraite, test_heures_payees_travaillees, test_accepter_emploi, test_indemnite_chomage, test_carrieres,
         test_pays_vivable, test_cout]
