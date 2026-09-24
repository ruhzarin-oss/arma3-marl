"""Les portes du domaine 2 ( banques ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests banques"""
import math, pickle, time
import numpy as np
from .. import config as C, monde as W
from ..socle import registre as R
from . import essais as T, d02_banques as M

MOTIFS_EMISSION = ("credit", "remboursement_principal", "avance_bc", "remboursement_avance_bc", "souscription_titre",
                   "remboursement_titre")


def _proche(a, b, rel=1e-9):
    return abs(a - b) <= rel * max(1.0, abs(a), abs(b))


def _secheresse(w, jours=40):
    """La secheresse de la porte du domaine 1 : les fermes des villages d Athira et de Pyrgos a 3 % de rendement."""
    villages = [l.id for l in w.carte.lieux.values() if l.type == "village" and l.marche.id in ("Athira", "Pyrgos")]
    w.chocs.append({"debut": 1, "jours": jours, "lieux": villages, "facteur": 0.03})


def _crise(p, part):
    """Une crise souveraine au jour 0 : `part` de l epargne de chaque menage habite ET toute la caisse du Tresor partent
    au service de la dette exterieure ( Chypre 2013 et Grece 2015, en plus dur ). L argent manque, la nourriture non ;
    le filet de l Etat ( subventions aux menages affames ) est vide. Motif declare par la porte, pas par le domaine."""
    w = p.w; L = p.socle.livre; dis = p.col("menage", "dissous")
    L.declarer_motif("service_dette_exterieure", "revenu_propriete", "tests_banques")
    for mg in w.menages:
        if not dis[mg.id] and mg.caisse > 0.0: L.payer_l_exterieur(mg, part * mg.caisse, "service_dette_exterieure")
    L.payer_l_exterieur(w.gouv, w.gouv.caisse, "service_dette_exterieure")


def _monde(jours, echelle=1.0, graine=C.GRAINE, modes=None, taux=None, exceptionnelle=None, secheresse=False, suivre=None,
           prelevement=None):
    """Un pays avec ses banques, vecu `jours` jours ; `exceptionnelle` : la frequence annuelle des depenses
    exceptionnelles le temps du scenario ; `prelevement` : la part de l epargne des menages prelevee au jour 0 par une crise souveraine ( _crise ) ;
    `suivre( w, p )` appele chaque soir de jour."""
    ancien = M.EXCEPTIONNELLE_AN
    if exceptionnelle is not None: M.EXCEPTIONNELLE_AN = exceptionnelle
    try:
        w, p = T.monde(["banques"], graine=graine, echelle=echelle, modes=modes)
        if taux is not None: M.fixer_taux_directeur(p, taux)
        if secheresse: _secheresse(w)
        if prelevement: _crise(p, prelevement)
        for _ in range(jours):
            T.jours(w, 1)
            if suivre is not None: suivre(w, p)
    finally:
        M.EXCEPTIONNELLE_AN = ancien
    return w, p


# ================================================================== les lois, sans monde
def test_tableau_amortissement():
    """10 000 drachmes a 10,15 % sur 36 mois, payees a chaque echeance : le principal amorti fait exactement le montant
    et le solde final est nul ( 1e-9 pres ), les interets font 36 mensualites moins le montant ( 1e-9 pres ) ; un pret
    a taux nul rend montant / duree. Controle positif : la mensualite croit avec le taux, decroit avec la duree.
    Falsificateur : une mensualite payee un mois en retard coute EXACTEMENT un mois d interet sur l amortissement
    retarde, et une derniere mensualite impayee laisse son principal du."""
    def derouler(P, taux, n, retard=None, derniere_impayee=False):
        m = M.mensualite(P, taux, n)
        principal, du_p, du_i, interets = P, 0.0, 0.0, []
        for k in range(n):
            i, a = M.echeance_du_mois(principal, du_p, m, taux, n - k)
            du_i += i; du_p += a
            if k == retard or (derniere_impayee and k == n - 1): continue
            interets.append(du_i); principal -= du_p; du_i = du_p = 0.0
        return m, principal, math.fsum(interets), du_p
    P, taux, n = 10000.0, 0.1015, 36
    m, reste, interets, _ = derouler(P, taux, n)
    exact = abs(reste) <= 1e-9 and _proche(interets, n * m - P)
    nul = _proche(M.mensualite(1200.0, 0.0, 12), 100.0)
    pos = (M.mensualite(1000.0, 0.12, 36) > M.mensualite(1000.0, 0.10, 36)
           and M.mensualite(1000.0, 0.10, 60) < M.mensualite(1000.0, 0.10, 36))
    k = 10
    principal = P
    for j in range(k):
        principal -= M.echeance_du_mois(principal, 0.0, m, taux, n - j)[1]
    a_k = M.echeance_du_mois(principal, 0.0, m, taux, n - k)[1]
    _, reste2, interets2, _ = derouler(P, taux, n, retard=k)
    retard_exact = abs(reste2) <= 1e-9 and _proche(interets2 - interets, a_k * taux / 12.0, 1e-6)
    _, reste3, _, du3 = derouler(P, taux, n, derniere_impayee=True)
    vu = reste3 > 0.0 and _proche(reste3, du3)
    ok = exact and nul and pos and retard_exact and vu
    return ok, (f"mensualite {m:.4f}, reste {reste:+.1e}, interets {interets:.6f} pour {n * m - P:.6f} attendus ; taux nul "
                f"{nul} ; mensualite croit avec le taux, decroit avec la duree : {pos} ; un mois de retard coute "
                f"{interets2 - interets:.6f} pour {a_k * taux / 12:.6f} attendus : {retard_exact} ; derniere impayee : reste "
                f"{reste3:.2f} du : {vu}")


def test_indice_et_taylor():
    """L indice suit les prix affiches : tous les prix x1,1 -> 110, la nourriture seule x2 -> 170 ( 1e-9 pres ). Dans un
    monde de 10 jours, l indice du matin est celui qu on recalcule a la main sur les prix affiches ( 1e-9 pres ).
    Controle positif de la regle de Taylor : une inflation de 10 % remonte le taux, d au plus 0,5 point ; une
    inflation nulle le baisse ; bornes [0 ; 25 %] tenues."""
    base = {"nourriture": 4.0, "carburant": 9.0, "remedes": 25.0, "outils": 30.0}
    ind = M.IndicePrix(M.POIDS_INDICE, base)
    tous = ind.calculer({b: 1.1 * v for b, v in base.items()})
    nour = ind.calculer(dict(base, nourriture=8.0))
    lois = abs(tous - 110.0) <= 1e-9 and abs(nour - 100.0 * (1 + M.POIDS_INDICE["nourriture"])) <= 1e-9
    w, p = _monde(10)
    d = p.domaine("banques")
    while w.minutes % 1440 != 6 * 60 + 10: w.pas_suivant()
    w.pas_suivant()                                               # la releve de 6 h 10
    pop = {k: w._pop_marche.get(k, 0) for k in w.marches}
    main = 100.0 * math.fsum(M.POIDS_INDICE[b] * sum(pop[k] * m.prix[b] for k, m in w.marches.items()) / sum(pop.values())
                             * (1 + w.gouv.tva) / d.bc.indice.base[b] for b in M.POIDS_INDICE)
    releve = _proche(d.bc.indice.valeurs[-1], main) and len(d.bc.indice.valeurs) == 11
    t = 0.0215
    haut, bas = M.regle_de_taylor(t, 0.10), M.regle_de_taylor(t, 0.0)
    bornes = M.regle_de_taylor(0.0, -0.5) == 0.0 and M.regle_de_taylor(0.25, 5.0) == 0.25
    taylor = t < haut <= t + M.PAS_TAUX_MAX + 1e-12 and bas < t and bornes
    ok = lois and releve and taylor
    return ok, (f"prix x1,1 -> {tous:.6f}, nourriture x2 -> {nour:.6f} ; indice du jour 10 {d.bc.indice.valeurs[-1]:.4f}, "
                f"recalcule {main:.4f} ( {len(d.bc.indice.valeurs)} releves ) ; Taylor : inflation 10 % -> {haut:.4f}, "
                f"0 % -> {bas:.4f}, bornes {bornes}")


# ================================================================== le domaine dans le moteur
def test_bilans_et_identite():
    """Porte : 40 jours a 500 habitants, avec en plus, par l API : 40 prets sur les quatre banques ( jour 2 ), un bon du
    Tresor de 20 jours paye par la premiere banque avec toutes ses reserves et la moitie de ses depots en plus ( elle
    doit se refinancer, puis rembourser le refinancement a l echeance du titre ), une avance de
    50 000 drachmes au Tresor puis un remboursement de 20 000. Chaque soir, chaque bilan ( 4 banques, banque centrale )
    tient a une tolerance pres. Identite monetaire : variation de la monnaie des detenteurs = exterieur net + emissions
    nettes du grand livre, qui ne passent que par les six motifs du domaine ; chaque emission nette par motif egale le
    compteur du domaine ( credits crees, principal rembourse, avances, titres ) ; l encours des prets = credits -
    principal rembourse ; la conservation du socle tient ; le reglement interbancaire et le refinancement ont servi.
    Falsificateurs, chacun sur une copie : un pret dont la monnaie est ecrite a la main ( caisse += ) casse la
    conservation ET le bilan de sa banque, de son montant exact ; un pret inscrit sans monnaie ne casse pas la
    conservation ( rien n est cree ) mais casse le bilan de son montant exact."""
    w, p = T.monde(["banques"])
    d = p.domaine("banques"); L = p.socle.livre; reg = p.socle.registre
    M0, ext0 = reg.argent(), dict(L.ext)
    suivi = {"refi": 0.0, "reglements": 0.0}

    def jours(n):
        for _ in range(n):
            T.jours(w, 1)
            suivi["refi"] = max(suivi["refi"], d.banques[0].refinancement)
            suivi["reglements"] += sum(abs(b.reglement) for b in d.banques)
    jours(2)
    rng = np.random.default_rng(5)
    menages = [m for m in w.menages if not p.col("menage", "dissous")[m.id]]
    for i in rng.choice(len(menages), 40, replace=False):
        mg = menages[int(i)]
        M.preter(p, M.banque_de(p, mg), mg, float(rng.uniform(200.0, 2000.0)), "conso")
    b0 = d.banques[0]
    duree = 20
    prix = b0.reserves + 0.5 * (b0.solde_cercle - b0.caisse)
    M.souscrire_titre(p, b0, prix * (1 + 0.03 * duree / M.JOURS_AN), 0.03, duree)
    M.avance_a_l_etat(p, 50000.0)
    jours(3)
    M.rembourser_avance(p, 20000.0)
    jours(35)
    c = d.controle
    bilans = c["jours"] == 40 and c["pire_bilan"] <= 1.0 and c["pire_bc"] <= 1.0
    dM = reg.argent() - M0
    ext = (L.ext["entree"] - ext0["entree"]) - (L.ext["sortie"] - ext0["sortie"])
    em = M.emissions_par_motif(p)
    identite = set(em) <= set(MOTIFS_EMISSION) and abs(dM - ext - math.fsum(em.values())) <= R.tolerance(M0)
    cree = math.fsum(b.cree + b.cree_jour for b in d.banques)
    detruit = math.fsum(b.detruit + b.detruit_jour for b in d.banques)
    encours = math.fsum(pr.principal for pr in d.prets.values())
    compteurs = (_proche(em.get("credit", 0.0), cree) and _proche(-em.get("remboursement_principal", 0.0), detruit)
                 and _proche(em.get("avance_bc", 0.0) + em.get("remboursement_avance_bc", 0.0), d.bc.avances)
                 and _proche(em.get("souscription_titre", 0.0) + em.get("remboursement_titre", 0.0),
                             math.fsum(b.titres for b in d.banques))
                 and abs(encours - (cree - detruit)) <= 1e-6 * max(1, len(d.prets)) + R.tolerance(cree))
    tenue, msg = p.socle.conservation.tenue()
    servi = suivi["refi"] > 0.0 and suivi["reglements"] > 0.0 and b0.titres == 0.0 and b0.refinancement == 0.0
    # falsificateurs
    def copie(): x = pickle.loads(pickle.dumps(w)); return x, x.pays, x.pays.domaine("banques")
    w1, p1, d1 = copie()
    mg = next(m for m in w1.menages if not p1.col("menage", "dissous")[m.id])
    b1 = M.banque_de(p1, mg)
    pr = M.Pret(d1.prochain_pret, b1.indice, mg, "conso", 1000.0, 0.1, 36, p1.jour)
    d1.prets[pr.id] = pr; d1.prets_de.setdefault(mg, []).append(pr.id)
    mg.caisse += 1000.0
    tenue1 = p1.socle.conservation.tenue()[0]
    e1 = M.bilan(p1, b1)["ecart"]
    vu_main = not tenue1 and abs(e1 - 1000.0) <= 1e-6
    w2, p2, d2 = copie()
    mg2 = next(m for m in w2.menages if not p2.col("menage", "dissous")[m.id])
    b2 = M.banque_de(p2, mg2)
    pr2 = M.Pret(d2.prochain_pret, b2.indice, mg2, "conso", 1000.0, 0.1, 36, p2.jour)
    d2.prets[pr2.id] = pr2; d2.prets_de.setdefault(mg2, []).append(pr2.id)
    tenue2 = p2.socle.conservation.tenue()[0]
    e2 = M.bilan(p2, b2)["ecart"]
    vu_sans = tenue2 and abs(e2 - 1000.0) <= 1e-6
    ok = bilans and identite and compteurs and tenue and servi and vu_main and vu_sans
    return ok, (f"{c['jours']} soirs, pire bilan {c['pire_bilan']:.2e} tolerance, banque centrale {c['pire_bc']:.2e} ; "
                f"monnaie {dM:+,.2f} = exterieur {ext:+,.2f} + emissions "
                + ", ".join(f"{k} {v:+,.2f}" for k, v in sorted(em.items()))
                + f" : {identite} ; compteurs du domaine egaux au grand livre, encours {encours:,.2f} : {compteurs} ; {msg} ; "
                f"refinancement max {suivi['refi']:,.0f}, reglements {suivi['reglements']:,.0f} ; falsificateurs : pret "
                f"a la main ( conservation {'tenue' if tenue1 else 'ROMPUE'}, ecart {e1:+.6f} ) vu {vu_main}, pret sans "
                f"monnaie ( conservation {'tenue' if tenue2 else 'ROMPUE'}, ecart {e2:+.6f} ) vu {vu_sans}")


def test_interets_et_defaut_exacts():
    """Deux prets construits de 1 000 drachmes a la grille conso, au jour 1 : l un au menage le plus riche, qui paie ;
    l autre a un menage dissous ( ni caisse ni revenu ), qui depense aussitot le pret et ne paie jamais. 126 jours. Le premier, apres ses quatre
    echeances : principal restant et interets encaisses egaux au tableau ( 1e-9 pres ), l interet passe par un motif
    revenu_propriete, jamais par l emission. Le second : impaye des la premiere echeance, un incident au fichier a 30
    jours de retard, defaut a 90 jours ( au jour 121 ), quatre mois d interet dus exactement puis plus rien, tout le
    principal exigible, provision = perte en cas de defaut x principal ( 450 ), deux incidents au fichier. Bilans
    equilibres chaque soir : la dotation est passee en fonds propres."""
    w, p = T.monde(["banques"])
    d = p.domaine("banques")
    T.jours(w, 1)
    dis = p.col("menage", "dissous")
    riche = max((m for m in w.menages if not dis[m.id]), key=lambda m: (m.caisse, -m.id))
    vide = next(m for m in w.menages if dis[m.id] and m.caisse == 0.0)
    taux = M.taux_credit(p, "conso")
    a = M.preter(p, M.banque_de(p, riche), riche, 1000.0, "conso")
    b = M.preter(p, M.banque_de(p, vide), vide, 1000.0, "conso")
    p.socle.livre.transferer(vide, w.marches[vide.domicile.marche.id], 1000.0, "depense_exceptionnelle")   # il depense tout
    g = p.jour
    retard_vu = incident_60 = None
    for _ in range(125):
        T.jours(w, 1)
        if retard_vu is None and b.retard_depuis >= 0: retard_vu = b.retard_depuis
        if incident_60 is None and b.incident: incident_60 = p.jour - 1       # pose a 18 h 10, vu au matin suivant
    # le tableau du premier
    m = M.mensualite(1000.0, taux, 36)
    principal, interets = 1000.0, []
    for k in range(4):
        i, am = M.echeance_du_mois(principal, 0.0, m, taux, 36 - k)
        interets.append(i); principal -= am
    paie = (_proche(a.principal, principal) and _proche(a.paye_interet, math.fsum(interets))
            and _proche(a.paye_principal, 1000.0 - principal) and a.retard_depuis < 0 and a.restantes == 32)
    nature = p.socle.livre.motifs["interet_pret"].nature == "revenu_propriete" and "interet_pret" not in M.emissions_par_motif(p)
    lgd = M.TYPES["conso"][2]
    defaut = (retard_vu == g + 30 and incident_60 == g + 60 and b.defaut_j == g + 120
              and _proche(b.du_interet, 4 * 1000.0 * taux / 12.0) and b.du_principal == b.principal == 1000.0
              and _proche(b.provision, lgd * 1000.0) and b.id in d.prets and b.paye_interet == 0.0
              and int(p.col("menage", "incidents")[vide.id]) == 2
              and any(e["type"] == "defaut_de_paiement" and e["pret"] == b.id for e in p.socle.journal.derniers(n=10000)))
    c = d.controle
    bilans = c["pire_bilan"] <= 1.0 and c["pire_bc"] <= 1.0
    ok = paie and nature and defaut and bilans
    return ok, (f"payeur : principal {a.principal:.9f} pour {principal:.9f}, interets {a.paye_interet:.9f} pour "
                f"{math.fsum(interets):.9f} : {paie} ; interet en revenu de la propriete, hors emission : {nature} ; "
                f"defaillant ( pret du jour {g} ) : retard au jour {retard_vu}, incident au jour {incident_60}, defaut au "
                f"jour {b.defaut_j}, interets dus {b.du_interet:.6f} pour {4 * 1000 * taux / 12:.6f}, provision "
                f"{b.provision:.2f}, incidents {int(p.col('menage', 'incidents')[vide.id])} : {defaut} ; pire bilan "
                f"{c['pire_bilan']:.2e}, banque centrale {c['pire_bc']:.2e}")


def test_taux_reduit_le_credit():
    """Controle positif : deux pays jumeaux ( meme graine, 1 500 habitants, 16 jours ), l un au taux directeur de 2,15 %,
    l autre a 20 %. Les memes 20 menages ( tires une fois, au jour 6 du premier pays, parmi ceux dont la paie est
    observee : un menage sans revenu ne demande pas de pret immobilier ), deux par matin des jours 6 a 15, demandent un pret
    immobilier de cinq ans de leur revenu observe par l API que prendra le domaine 13 ( demander_credit ). Au taux
    haut, la mensualite d un pret sur 25 ans est multipliee par 3,5 et la regle accorde moins : au plus 85 % des
    drachmes accordees au taux bas, sur au moins 20 demandes. Le controle n est valide que si les fonds propres des
    banques ne limitent rien au taux bas ( aucun refus reglementaire ) : le temps du scenario, les fonds propres de
    depart sont portes a 100 % des depots ( a 10 %, 8 des 20 demandes butaient sur Bale III : mesure du 23/09 ). La
    demande spontanee ( consommation, fonds de roulement ) est mesuree a cote, sans seuil."""
    res, choisis = {}, []
    for t in (0.0215, 0.20):
        ancien = M.FONDS_PROPRES_INITIAUX
        M.FONDS_PROPRES_INITIAUX = 1.0
        try: w, p = T.monde(["banques"], echelle=3)
        finally: M.FONDS_PROPRES_INITIAUX = ancien
        M.fixer_taux_directeur(p, t)
        d = p.domaine("banques")
        dis = p.col("menage", "dissous")
        inj = {"demandes": 0, "accorde": 0.0, "reglementaires": 0}
        for j in range(16):
            T.jours(w, 1)
            if not 6 <= p.jour <= 15: continue
            if not choisis:
                cands = [m.id for m in w.menages if not dis[m.id] and M._revenu_menage(p, m.id) > 0.0]
                choisis = [int(i) for i in np.random.default_rng(7).choice(cands, 20, replace=False)]
            for i in choisis[2 * (p.jour - 6): 2 * (p.jour - 6) + 2]:
                c0 = dict(d.compte)
                M.demander_credit(p, w.menages[i], 60 * M.MOIS_J * M._revenu_menage(p, i), "immo")
                inj["demandes"] += d.compte["demandes"] - c0["demandes"]
                inj["accorde"] += d.compte["montant_accorde"] - c0["montant_accorde"]
                inj["reglementaires"] += d.compte["refus_reglementaires"] - c0["refus_reglementaires"]
        res[t] = (inj, dict(d.compte))
    (ib, cb), (ih, ch) = res[0.0215], res[0.20]
    valide = ib["reglementaires"] == 0 and ib["demandes"] >= 20
    ok = valide and ih["accorde"] <= 0.85 * ib["accorde"]
    def spontane(inj, c): return c["demandes"] - inj["demandes"], c["montant_accorde"] - inj["accorde"]
    sb, sh = spontane(ib, cb), spontane(ih, ch)
    return ok, (f"prets immobiliers : taux 2,15 % : {ib['demandes']} demandes, {ib['accorde']:,.0f} drachmes accordees ; "
                f"taux 20 % : {ih['demandes']} demandes, {ih['accorde']:,.0f} drachmes "
                f"( {ih['accorde'] / max(1e-9, ib['accorde']):.0%} ) ; refus reglementaires {ib['reglementaires']} / "
                f"{ih['reglementaires']} ( valide {valide} ) ; demande spontanee : {sb[0]} demandes, {sb[1]:,.0f} drachmes "
                f"au taux bas, {sh[0]} demandes, {sh[1]:,.0f} drachmes au taux haut")


def test_octroi_part_du_choix():
    """Porte de la decision, dans un scenario ou le choix change l issue de CE menage : l argent manque, pas la
    nourriture. 1 500 habitants ; au jour 0, une crise souveraine envoie 97 % de l epargne des menages et toute la caisse
    du Tresor au service de la dette exterieure ( _crise ) : plus de filet de l Etat. Un menage sur cinq gagne a la paie
    moins que sa nourriture ( mesure du 23/09 ) : a court, il demande de quoi manger 30 jours. Accorde, il mange puis
    doit rembourser ; refuse, il a faim. La banque decide au
    hasard ( mode hasard ) pendant 130 jours. Au moins 150 decisions, au moins 60 notes murees ( 120 jours ) ; la note
    depend du choix : part du choix ( epsilon carre intra-jour ) >= 0,01 ET p de permutation < 0,05. Instrument : pour
    chaque action, la note moyenne du decideur egale part banque + poids x part emprunteur ( 1e-9 pres ), la part banque
    d un refus est nulle, et le volet emprunteur a servi ( une note de refus non nulle ). La monnaie se conserve.
    ( Mesures precedentes, epsilon carre 0,000 les deux fois : pays sans secheresse, 200 jours, 1 000 habitants, 131
    notes murees, 1,5 par jour pour 3 actions - un pret de depense exceptionnelle ne change presque rien ; prelevement
    de 97 % verse au Tresor, 687 notes murees - le Tresor enrichi subventionne les affames, faim finale 1 %, et la
    plupart des demandeurs se refont a la paie du lendemain. )"""
    w, p = _monde(130, echelle=3, modes={"octroi_credit": "hasard"}, prelevement=0.97)
    d = p.domaine("banques"); dec = d.decideur
    part, perm, brute = dec.part_du_choix(), dec.p_permutation(), dec.part_du_choix_brute()
    notes = dec.notes_par_action()
    murees = sum(n for n, _ in notes.values())
    jours_notes = len({j for (j, a) in dec.stats})
    comp = {dec.point.actions[a]: (n, sb / n, sm / n) for a, (n, sb, sm) in sorted(d.composantes.items())}
    somme = all(a in comp and comp[a][0] == n and _proche(m, comp[a][1] + M.POIDS_MENAGE * comp[a][2])
                for a, (n, m) in notes.items())
    refus = [st for (j, a), st in dec.stats.items() if a == 0]
    refus_banque_nulle = "refuser" in comp and comp["refuser"][1] == 0.0
    refus_non_nul = any(st[2] > 0.0 for st in refus)
    cons = p.socle.conservation
    tenue, msg = cons.tenue()
    argent = abs(cons.ecarts()[0]) <= R.tolerance(cons.argent0, cons.volumes()[0])
    ok = (dec.n_decisions >= 150 and murees >= 60 and part >= 0.01 and perm < 0.05 and somme and refus_banque_nulle
          and refus_non_nul and argent)
    return ok, (f"{dec.n_decisions} decisions, {murees} notes murees sur {jours_notes} jours : "
                + ", ".join(f"{a} {m:+.4f} ( {n} ; banque {comp[a][1]:+.4f}, emprunteur {comp[a][2]:+.4f} )"
                            for a, (n, m) in notes.items() if a in comp)
                + f" ; part du choix {part:.3f} ( brute {brute:.3f} ), p de permutation {perm:.3f} ; note = banque + "
                f"emprunteur : {somme} ; refus : part banque nulle {refus_banque_nulle}, une note non nulle {refus_non_nul} ; "
                f"faim finale {T.faim(w):.0%} ; monnaie conservee {argent} ; {msg}")


def test_pays_vivable():
    return T.porte_commune("banques", n_jours=12)


def test_cout():
    """Le domaine ajoute au plus 20 % a une journee du moteur avec la population, a 10 000 habitants, et ses routines
    propres coutent au plus 10 % de cette journee."""
    def jour_moyen(domaines):
        w = W.Monde(echelle=20)
        T.P.installer(w, domaines)
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, w
    t_pop, _ = jour_moyen(["population"])
    t_bq, w = jour_moyen(["banques"])
    p = w.pays
    t0 = time.perf_counter()
    for _ in range(3):
        M._matin(p); M._guichet(p); M._avant_paie(p); M._apres_paie(p); M._recouvrer(p); M._soir(p)
    propre = (time.perf_counter() - t0) / 3
    n = len(w.habitants)
    ok = t_bq <= 1.20 * t_pop and propre <= 0.10 * t_pop
    return ok, (f"{n} habitants : moteur et population {t_pop:.2f} s par jour, avec les banques {t_bq:.2f} s "
                f"( {t_bq / t_pop - 1:+.0%} ) ; routines propres du domaine {propre * 1000:.0f} ms par jour, soit "
                f"{propre / n * 1e6:.1f} us par habitant")


TESTS = [test_tableau_amortissement, test_indice_et_taylor, test_bilans_et_identite, test_interets_et_defaut_exacts,
         test_taux_reduit_le_credit, test_octroi_part_du_choix, test_pays_vivable, test_cout]
