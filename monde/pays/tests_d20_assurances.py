"""Les portes du domaine 20 ( assurances ). Seuils ecrits avant la premiere mesure.
python -m monde.pays.tests assurances"""
import math, pickle, time
import numpy as np
from .. import config as C, monde as W
from . import essais as T, pays as P, d09_agriculture as AGR, d13_immobilier as IM, d14_transport as TR
from . import d20_assurances as AS, d21_justice as JU

PAS_J = C.PAS_PAR_JOUR
_CACHE = {}
DEPS = ["banques", "agriculture", "immobilier", "transport", "hopitaux"]


def _monde(cle, domaines, graine, echelle, jours, modes=None, avant=None):
    """Un pays mis en cache : installe, `avant( w, p )` s il est donne, puis `jours` jours."""
    if cle not in _CACHE:
        w, p = T.monde(domaines, graine=graine, echelle=echelle, modes=modes)
        if avant is not None: avant(w, p)
        T.jours(w, jours)
        _CACHE[cle] = (w, p)
    return _CACHE[cle]


def _copie(w):
    x = pickle.loads(pickle.dumps(w)); return x, x.pays


def _dans(x, b): return b[0] <= x <= b[1]


# ================================================================== les taux grecs
def test_taux_de_souscription():
    """3 000 habitants, a l installation puis apres 20 jours : vehicules assures dans [ 84 % ; 93 % ] ( 7 a 16 % de
    non-assures, EAEE ), logements de proprietaires occupants assures dans [ 10 % ; 22 % ], personnes couvertes en sante
    dans [ 8 % ; 18 % ], 100 % des fermes a ELGA ( chaque ferme a paye ou doit sa cotisation ) ; parts de marche des
    primes du portefeuille initial a 5 points de leur cible. En regard ( sans seuil ) : la penetration ( primes sur
    revenu des menages ), les primes moyennes en euros, le ratio sinistres a primes."""
    w0, p0 = T.monde(["assurances"], graine=20, echelle=6)
    t0 = AS.taux_de_souscription(p0)
    D0 = AS._dom(p0); T0 = D0.T; n = T0.n
    tot = float(T0.prime[:n].sum())
    parts = [float(T0.prime[:n][T0.assureur[:n] == a.id].sum()) / tot for a in D0.assureurs]
    ecart = max(abs(x - a.part) for x, a in zip(parts, D0.assureurs))
    w, p = _monde("base", ["assurances"], 20, 6, 20)
    t1 = AS.taux_de_souscription(p)
    D = AS._dom(p); E = D.elga; K = p.socle.creances
    fermes = p.domaine("agriculture").liste
    doit = {id(c.debiteur) for c in K.actives.values() if c.motif == "cotisation_elga"}
    cotisent = sum(1 for ex in fermes if id(ex.ferme) in doit) if E.cotisations <= 0 else len(fermes)
    ok = all(_dans(t["auto"], AS.BANDE_AUTO) and _dans(t["habitation"], AS.BANDE_HAB) and _dans(t["sante"], AS.BANDE_SANTE)
             and t["recolte"] == 1.0 for t in (t0, t1)) and ecart <= 0.05 and cotisent == len(fermes) and E.cotisations > 0
    Tn = D.T; nn = Tn.n; act = Tn.etat[:nn] == AS.ACTIF
    moy = {b: float(Tn.prime[:nn][act & (Tn.branche[:nn] == k)].mean()) * P.EUROS_PAR_DRACHME
           for k, b in enumerate(AS.BRANCHES) if (act & (Tn.branche[:nn] == k)).any()}
    acquis = sum(D.cpt[m] for m in ("prime_assurance",))
    sin = D.cpt["sinistres_ht"] + sum(d.tva for d in D.payes) + sum(d.estime for d in D.ouverts.values() if d.payeur >= 0)
    return ok, ("installation : " + ", ".join(f"{k} {t0[k]:.1%}" for k in ("auto", "habitation", "sante", "recolte"))
                + f" ; apres 20 jours : " + ", ".join(f"{k} {t1[k]:.1%}" for k in ("auto", "habitation", "sante", "recolte"))
                + f" ( {t1['vehicules']} vehicules, {t1['proprietaires']} proprietaires, {t1['personnes']} personnes, "
                  f"{t1['fermes']} fermes ; cotisations ELGA {E.cotisations:.0f} dr ) ; parts de marche a {ecart:.3f} "
                  f"de la cible ; en regard : penetration {t1['penetration']:.2%} du revenu des menages, primes moyennes "
                + ", ".join(f"{k} {v:.0f} EUR" for k, v in moy.items())
                + f", sinistres encourus sur primes encaissees en 20 jours {sin / max(acquis, 1e-9):.0%}")


# ================================================================== l argent au centime
PART_CLINIQUE = 300.0


def _accidente():
    """Accidents x 6, vols x 6 ; et, controle positif de la branche sante ( l hopital du pays facture peu : 2 passages
    en 20 jours pour 3 000 habitants ), 4 passages en clinique factures au jour 0 a des assures, 4 a des non-assures."""
    def avant(w, p):
        TR.scenario(p, accidents=6.0, corporels=3.0, vols=6.0)
        H = __import__("monde.pays.d17_hopitaux", fromlist=["x"])._dom(p)
        cm = p.colonnes["menage"]; tb = w.table; M = tb.menages.n
        for cond, k in ((cm["as_sante"][:M] >= 0, 4), (cm["as_sante"][:M] < 0, 4)):
            vus = 0
            for i in np.nonzero(cond)[0].tolist():
                hid = next((x for x in tb.menages.membres_ids(i) if tb.vivant[x]), None)
                if hid is None: continue
                H.factures.append((p.jour, hid, 0, True, PART_CLINIQUE / 0.3, PART_CLINIQUE, 0, False, "sorti"))
                vus += 1
                if vus == k: break
    return _monde("accidents", ["assurances"], 21, 6, 20, avant=avant)


def test_primes_et_sinistres_au_centime():
    """3 000 habitants, accidents x 6, vols x 6, 20 jours. Chaque contrat souscrit ou renouvele pendant la course a pour
    prime exactement son niveau fois la prime de reference, encaissee en entier ; le grand livre voit sous
    prime_assurance la somme des primes encaissees, sous taxe_primes_assurance 15 % de ce total, sous
    indemnite_assurance la somme des indemnites payees hors TVA, sous chaque motif du domaine ce que le domaine a
    paye ( 1e-6 ) ; au moins 10 sinistres payes, chacun egal a ce que le contrat et la source donnent ( 1e-6 ) ; les
    4 passages en clinique d assures rembourses a 80 % de leur participation ( 1e-9 ), ceux des non-assures non ;
    provision de chaque payeur = somme des declarations ouvertes ; audit propre ; reassurance au grand livre = ce que
    le domaine a cede et recupere."""
    w, p = _accidente()
    D = AS._dom(p); Tb = D.T; n = Tb.n
    neuf = (Tb.etat[:n] == AS.ACTIF) & (Tb.debut[:n] > D.jour_install)
    mult = np.array(AS.MULT)[np.maximum(Tb.niveau[:n], 0)]
    prix = bool(neuf.any()) and bool(np.all(np.abs(Tb.prime[:n][neuf] - mult[neuf] * Tb.ref[:n][neuf]) <= 1e-9 * Tb.prime[:n][neuf])
                                      and np.all(Tb.encaisse[:n][neuf] == Tb.prime[:n][neuf]))
    lv = AS.livre_cumule(p)
    taxe = abs(lv["taxe_primes_assurance"] - AS.TAXE[0] * lv["prime_assurance"]) <= 1e-6 * max(1.0, lv["prime_assurance"])
    ecarts = [(d.id, d.nature, d.paye, AS.recalculer(p, d)) for d in D.payes
              if abs(d.paye - AS.recalculer(p, d)) > 1e-6 * max(1.0, d.paye)]
    a = AS.audit(p)
    reas = all(abs(lv[m] - D.cpt[m]) <= 1e-6 * max(1.0, D.cpt[m]) for m in ("prime_reassurance", "indemnite_reassurance"))
    par = {}
    for d in D.payes: par[d.nature] = par.get(d.nature, 0) + 1
    sante = [d for d in D.payes if d.nature == "sante"]
    ok = (prix and taxe and len(D.payes) >= 10 and not ecarts and AS.audit_propre(a) and reas and len(sante) == 4
          and all(abs(d.paye - AS.REMB_SANTE * PART_CLINIQUE) <= 1e-9 for d in sante))
    return ok, (f"{int(neuf.sum())} contrats souscrits ou renouveles au prix cote : {prix} ; grand livre : primes "
                f"{lv['prime_assurance']:.2f} dr, taxe {lv['taxe_primes_assurance']:.2f} ( 15 % : {taxe} ), indemnites HT "
                f"{lv['indemnite_assurance']:.2f} ; {len(D.payes)} sinistres payes ( " + ", ".join(f"{k} {v}" for k, v in sorted(par.items()))
                + f" ), hors calcul : {ecarts[:3]} ; {len(D.ouverts)} ouverts ; audit {'propre' if AS.audit_propre(a) else a} ; "
                  f"reassurance cedee {D.cpt['prime_reassurance']:.2f}, recuperee {D.cpt['indemnite_reassurance']:.2f} : {reas}")


def test_non_assure_et_falsificateurs():
    """Le pays accidente apres 20 jours. Un sinistre d un menage sans la garantie ( dommages, vol, logement, sa propre
    responsabilite civile ) n est jamais paye a ce menage ( au moins 3 tels sinistres ). Puis, chacun sur une copie :
    une indemnite versee a la main sans declaration, une declaration ouverte sans contrat, une provision gonflee, un
    pointeur de menage vers le contrat d un autre - chacun est vu par l audit."""
    w, p = _accidente()
    D = AS._dom(p)
    GAR = {"dommages": AS.DOMMAGES, "vol": AS.VOL, "corporel": AS.RC, "incendie": AS.INCENDIE, "seisme": AS.SEISME,
           "sante": AS.HOSPI}
    payes = {(d.jour, d.benef, d.garantie, d.objet) for d in D.payes if d.assure == d.benef}
    viole = [nc for nc in D.non_couverts if (nc[0], nc[1], GAR[nc[2]], nc[4]) in payes]
    a0 = AS.audit(p)
    x, px = _copie(w); Dx = AS._dom(px)
    A = Dx.assureurs[0]
    px.socle.livre.transferer(A, x.menages[0], 1000.0, "indemnite_assurance")
    v1 = bool(AS.audit(px)["livre"])
    x, px = _copie(w); Dx = AS._dom(px)
    d = AS.Declaration(Dx.prochain, AS.AUTO, "vol", 0, px.jour); Dx.prochain += 1
    d.benef = 0; d.garantie = AS.VOL; d.echeance_j = px.jour + 5
    AS._ouvrir(px, Dx, d, 5000.0)
    v2 = d.id in AS.audit(px)["sans_contrat"]
    x, px = _copie(w); Dx = AS._dom(px)
    Dx.assureurs[1].psap += 50.0
    v3 = bool(AS.audit(px)["provision"])
    x, px = _copie(w); Dx = AS._dom(px); cm = px.colonnes["menage"]
    M = x.table.menages.n
    i = int(np.nonzero(cm["as_hab"][:M] >= 0)[0][0]); j = int(np.nonzero(cm["as_hab"][:M] >= 0)[0][1])
    cm["as_hab"][i] = cm["as_hab"][j]
    v4 = bool(AS.audit(px)["pointeur"])
    ok = len(D.non_couverts) >= 3 and not viole and AS.audit_propre(a0) and v1 and v2 and v3 and v4
    par = {}
    for nc in D.non_couverts: par[nc[2]] = par.get(nc[2], 0) + 1
    return ok, (f"{len(D.non_couverts)} sinistres sans garantie ( " + ", ".join(f"{k} {v}" for k, v in sorted(par.items()))
                + f" ), payes quand meme : {len(viole)} ; audit {'propre' if AS.audit_propre(a0) else a0} ; indemnite sans "
                  f"declaration vue {v1} ; declaration sans contrat vue {v2} ; provision gonflee vue {v3} ; pointeur vers "
                  f"le contrat d un autre vu {v4}")


# ================================================================== le choc et la reassurance
def _seisme(graine=22):
    if ("seisme", graine) not in _CACHE:
        w, p = T.monde(["assurances", "justice"], graine=graine, echelle=6)
        AS.scenario(p, fraude=5.0)
        T.jours(w, 2)
        x, px = _copie(w)
        lieu = _ville(x)
        IM.appliquer_seisme(px, {lieu: 8.5})
        T.jours(w, 17); T.jours(x, 17)
        _CACHE[("seisme", graine)] = (w, p, x, px, lieu)
    return _CACHE[("seisme", graine)]


def test_choc_seisme_et_reassurance():
    """3 000 habitants avec la justice, fraude x 5 ; au jour 2, une copie subit un seisme d intensite 8,5 sur sa ville la
    plus peuplee ; 17 jours. Chaque sinistre habitation paye vaut ce que le contrat et le dommage donnent ( somme
    assuree, franchise de 2 % en seisme ; 1e-6 ). Controle positif : au moins 10 sinistres seisme declares dans la copie, au moins 10 fois
    ceux du pays temoin. La reassurance joue : le grand livre voit recuperer ( indemnite_reassurance ) exactement la
    quote-part et l excedent des sinistres habitation payes ( 1e-6 ), au moins la quote-part de 50 % ; l excedent de
    sinistre a joue pour au moins un assureur. Un non-assure n est pas indemnise : au moins 10 logements de proprietaires
    sans garantie seisme endommages, aucun paye. Chaque fraude soupconnee est une affaire de la justice ( fraude_assurance )
    et chaque vraie fraude detectee designe l assure ; audits propres."""
    w, p, x, px, lieu = _seisme()
    D, Dx = AS._dom(p), AS._dom(px)
    def seis(D_): return [d for d in list(D_.payes) + list(D_.ouverts.values()) if d.nature == "seisme"]
    s0, s1 = seis(D), seis(Dx)
    hab = [d for d in Dx.payes if d.nature in ("seisme", "incendie")]
    attendu = math.fsum(d.recupere for d in list(Dx.payes) + list(Dx.ouverts.values()))
    parts = [d.id for d in hab if abs(d.recupere - d.paye * (d.part_qp + d.part_xl)) > 1e-6 * max(1.0, d.paye)]
    lv = AS.livre_cumule(px)
    rec = lv["indemnite_reassurance"]
    qp = math.fsum(d.paye * d.part_qp for d in hab)
    xl = any(d.part_xl > 0 for d in s1)
    nc = {(j, i, b) for j, i, nat, _, b in Dx.non_couverts if nat == "seisme"}
    payes = {(d.jour, d.benef, d.objet) for d in Dx.payes if d.nature == "seisme"}
    aff = JU.affaires(px, type_="fraude_assurance")
    signal = Dx.stats["fraudes_vraies"] + Dx.stats["fausses_alertes"]
    calc = [d.id for d in hab if abs(d.paye - AS.recalculer(px, d)) > 1e-6 * max(1.0, d.paye)]
    ok = (not calc and not parts and len(s1) >= 10 and len(s1) >= 10 * len(s0) and abs(rec - attendu) <= 1e-6 * max(1.0, attendu) and rec >= qp - 1e-6
          and qp > 0 and xl and len(nc) >= 10 and not (nc & payes) and len(aff) == signal
          and AS.audit_propre(AS.audit(p)) and AS.audit_propre(AS.audit(px)))
    brut = math.fsum(d.paye for d in hab)
    return ok, (f"seisme 8,5 a {lieu} : sinistres seisme {len(s1)} ( temoin {len(s0)} ), payes {sum(1 for d in s1 if d.etat == AS.PAYE)}, "
                f"habitation payee {brut:.0f} dr, reassurance recuperee {rec:.0f} dr ( attendu {attendu:.0f}, dont quote-part "
                f"{qp:.0f} ; parts hors calcul {len(parts)} ), excedent de sinistre {'joue' if xl else 'NON'} ; {len(nc)} proprietaires sans garantie seisme "
                f"endommages, payes {len(nc & payes)} ; fraudes signalees {signal} ( vraies {Dx.stats['fraudes_vraies']} ), "
                f"affaires de justice {len(aff)} ; hors calcul {len(calc)} ; audits {'propres' if AS.audit_propre(AS.audit(p)) and AS.audit_propre(AS.audit(px)) else 'NON'}")


def _ville(x):
    pop = {}
    tb = x.table; M = tb.menages.n
    for k in tb.menages.domicile[:M].tolist(): pop[k] = pop.get(k, 0) + 1
    return x.carte.par_n[max((k for k in pop if x.carte.par_n[k].type in ("capitale", "ville")), key=lambda k: (pop[k], k))].id


def test_faillite():
    """Le pays accidente apres 20 jours ( copie ) : le reassureur de l assureur qui a le plus de sinistres ouverts fait
    defaut ( ses traites tombent ). Son SCR reprend tout le risque de seisme, ses fonds propres passent sous le MCR : le
    soir meme il est liquide - plus aucun contrat actif, caisse, provision et obligations a zero ; ses sinistres ouverts
    ( au moins un ) sont repris par le fonds de garantie, dont la provision reste egale a ses declarations ouvertes et
    qui recoit ses actifs ; 3 jours apres, au moins la moitie des vehicules qu il assurait sont assures ailleurs ; aucun
    autre assureur n est liquide ; audit propre. Controle : dans le pays reassure du seisme ( porte precedente ), aucun
    assureur n est tombe."""
    w0, p0 = _accidente()
    w, p = _copie(w0)
    D = AS._dom(p)
    ouverts = {}
    for d in D.ouverts.values():
        if d.payeur >= 0: ouverts[d.payeur] = ouverts.get(d.payeur, 0) + 1
    A = D.assureurs[max(ouverts, key=lambda a: (ouverts[a], -a))] if ouverts else D.assureurs[0]
    n_ouv = ouverts.get(A.id, 0); psap_a, oblig_a, oblig_f0 = A.psap, A.oblig, D.fonds.oblig
    Tb = D.T; n = Tb.n
    siens = [(int(Tb.menage[r]), int(Tb.slot[r])) for r in np.nonzero((Tb.etat[:n] == AS.ACTIF) & (Tb.assureur[:n] == A.id)
                                                                         & (Tb.branche[:n] == AS.AUTO))[0].tolist()]
    AS.retirer_reassurance(p, A.id)
    T.jours(w, 1)
    liquide = not A.vivant and A.faillite_j >= 0
    actifs = int(((Tb.etat[:Tb.n] == AS.ACTIF) & (Tb.assureur[:Tb.n] == A.id)).sum())
    transferes = sum(1 for d in D.ouverts.values() if d.payeur == AS.FONDS and not d.tiers_non_assure)
    pv = AS.provisions(p)[AS.FONDS]
    lv = AS.livre_cumule(p)
    T.jours(w, 3)
    cm = p.colonnes["menage"]
    encore = [(i, k) for i, k in siens if cm[f"vh_m{k}"][i] >= 0]
    repris = sum(1 for i, k in encore if cm[f"as_auto{k}"][i] >= 0)
    seul = sum(1 for a in D.assureurs if not a.vivant) == 1
    a_ = AS.audit(p)
    _, _, _, px, _ = _seisme()
    controle = all(a.vivant for a in AS._dom(px).assureurs)
    ok = (liquide and actifs == 0 and A.caisse == 0.0 and A.psap == 0.0 and A.oblig == 0.0 and n_ouv >= 1
          and transferes >= 1 and abs(pv[0] - pv[1]) <= 1e-6 * max(1.0, pv[1]) and lv["liquidation_assureur"] > 0
          and abs(D.fonds.oblig - oblig_f0 - oblig_a) <= 1e-6 * max(1.0, oblig_a)
          and repris >= 0.5 * len(encore) and len(encore) > 10 and seul and AS.audit_propre(a_) and controle)
    return ok, (f"{A.nom} ( {n_ouv} sinistres ouverts, provision {psap_a:.0f} dr, obligations {oblig_a:.0f} ) sans reassurance : "
                f"ratio {A.ratio:.2f}, liquide {liquide} au jour {A.faillite_j}, contrats actifs ensuite {actifs}, caisse "
                f"{A.caisse:.2f}, provision {A.psap:.2f}, obligations {A.oblig:.2f} ; fonds de garantie : liquidation recue "
                f"{lv['liquidation_assureur']:.0f} dr, obligations {oblig_f0:.0f} -> {D.fonds.oblig:.0f}, sinistres repris "
                f"encore ouverts {transferes}, provision {pv[0]:.0f} = ouvertes {pv[1]:.0f} ; vehicules qu il assurait : "
                f"{repris} / {len(encore)} assures ailleurs apres 3 jours ; seul liquide {seul} ; audit "
                f"{'propre' if AS.audit_propre(a_) else a_} ; pays reassure du seisme : aucun liquide {controle}")


# ================================================================== ELGA
def test_elga_grele():
    """1 000 habitants ( 27 fermes quel que soit le pays ). Au jour 3, une copie subit la grele sur le ble de 9 fermes
    ( 60 % de la recolte sur pied detruite : recolte attendue et climat de la campagne x 0,4 ). Au jour 32, le ble est
    moissonne ( fenetre des jours 165 a 195 de l an ) : ELGA a declare un sinistre pour chacune des 9 fermes, de montant
    80 % de la valeur climatique perdue au prix de reference de l annee ( 1e-9 ) ; le temoin en a moins ; la provision d ELGA = ses declarations non
    payees ; aucune perte de gestion ( non recolte ) n est indemnisee sans perte de climat."""
    w, p = T.monde(["assurances"], graine=24, echelle=2)
    T.jours(w, 3)
    x, px = _copie(w)
    A = px.domaine("agriculture"); ch = A.champs
    c = [k for k, cu in enumerate(AGR.CULTURES) if cu.nom == "ble"][0]
    greles = [g for g in range(len(A.liste)) if ch.ouvert[c, g]][:9]
    for g in greles:
        ch.attendu[c, g] *= 0.4; ch.climat[c, g] *= 0.4
    T.jours(w, 29); T.jours(x, 29)
    def elga(p_):
        D_ = AS._dom(p_)
        return [d for d in list(D_.payes) + list(D_.ouverts.values()) if d.nature == "recolte"]
    e0, e1 = elga(p), elga(px)
    cps = ch.campagnes
    faux = []
    for d in e1:
        jour, g, cc, ha, kg, perdu, fr, clim, eng = cps[d.source]
        b = px.socle.catalogue[AGR.CULTURES[cc].bien]
        v = AS.COUV_ELGA * (kg + perdu) * (1 - clim) / max(clim, 0.05) / b.masse_kg * AS._dom(px).prix_elga[AGR.CULTURES[cc].bien]
        if abs(d.vrai - v) > 1e-9 * max(1.0, v) or clim >= 1.0 - AS.SEUIL_ELGA: faux.append(d.id)
    touchees = {d.ferme for d in e1 if cps[d.source][2] == c}
    pv = AS.provisions(px)[AS.ELGA_P]
    ok = len(greles) == 9 and set(greles) <= touchees and len(e0) < len(e1) and not faux and abs(pv[0] - pv[1]) <= 1e-6 * max(1.0, pv[1])
    return ok, (f"grele sur {len(greles)} fermes : ELGA {len(e1)} sinistres ( temoin {len(e0)} ), fermes grelees indemnisees "
                f"{len(set(greles) & touchees)} / {len(greles)}, montant hors calcul {len(faux)}, provisionne "
                f"{math.fsum(d.estime for d in e1):.0f} dr ; provision ELGA {pv[0]:.2f} = ouvertes {pv[1]:.2f} ; cotisations "
                f"{AS._dom(px).elga.cotisations:.0f} dr")


# ================================================================== la decision
def test_decision():
    """Le point `tarifer`, en mode hasard : 3 000 habitants, tous les contrats renouveles dans les 10 premiers jours
    ( renouvellements groupes ), 42 jours. Au moins 300 notes et 3 jours ou chaque action a 2 notes ; part du choix
    >= 0,01 ET p de permutation < 0,05. En regard ( sans seuil ) : la note moyenne sous la regle et sous le temoin
    ( prime unique ), et la couverture auto qu elles laissent."""
    def avant(w, p): AS.forcer_echeances(p, 1.0, 10, np.random.default_rng(1))
    res = {}
    for m in ("hasard", "regle", "temoin"):
        w, p = _monde(("decision", m), ["assurances"], 25, 6, 42, modes={"tarifer": m}, avant=avant)
        res[m] = (p, AS._dom(p).decideur)
    dec = res["hasard"][1]
    part, pval = dec.part_du_choix(), dec.p_permutation()
    notes = sum(n for n, _, _ in dec.stats.values())
    par_jour = {}
    for (j, a), (n_, _, _) in dec.stats.items(): par_jour.setdefault(j, {})[a] = n_
    jours_ok = sum(1 for d in par_jour.values() if all(d.get(a, 0) >= 2 for a in range(len(AS.ACTIONS))))
    moy = {}
    for m in ("regle", "temoin"):
        dm = res[m][1]
        n_ = sum(n for n, _, _ in dm.stats.values()); s_ = sum(s for _, s, _ in dm.stats.values())
        moy[m] = (s_ / n_ if n_ else float("nan"), AS.taux_de_souscription(res[m][0])["auto"])
    ok = notes >= 300 and jours_ok >= 3 and part >= 0.01 and pval < 0.05
    return ok, (f"{dec.n_decisions} decisions, {notes} notes, {jours_ok} jours a 2 notes par action ; part du choix "
                f"{part:.3f}, p {pval:.3f} ; notes " + ", ".join(f"{a} {x:.2f} ( {n} )" for a, (n, x) in dec.notes_par_action().items())
                + f" ; regle : note {moy['regle'][0]:.3f}, auto assuree {moy['regle'][1]:.1%} ; temoin : note "
                  f"{moy['temoin'][0]:.3f}, auto assuree {moy['temoin'][1]:.1%}")


def test_pays_vivable():
    return T.porte_commune("assurances", n_jours=12)


# ================================================================== le cout
def test_cout():
    """A 10 000 habitants, coeur Rust : les routines propres du domaine ( une journee, appelees une a une, apres un jour
    de vie ) coutent au plus 25 % d une journee du moteur seul. Installer le domaine sur ses dependances deja installees
    coute a 100 000 habitants au plus 20 fois ce qu il coute a 10 000 ( lineaire : ~ 10 ; quadratique : ~ 100 )."""
    w0 = W.Monde(echelle=20)
    T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    inst = {}
    for ech in (20, 200):
        w = W.Monde(echelle=ech)
        P.installer(w, DEPS)
        t0 = time.perf_counter(); P.installer(w, ["assurances"]); inst[ech] = time.perf_counter() - t0
        if ech == 20: w20 = w
        else: n200 = AS._dom(w.pays).T.n
    p = w20.pays; D = AS._dom(p)
    T.jours(w20, 1)
    t0 = time.perf_counter()
    for _ in range(3):
        for f in (AS._matin, AS._souscrire, AS._placements, AS._elga_cotisations): f(p)
        AS._cloture(p, {"argent": []})
    propre = (time.perf_counter() - t0) / 3
    ratio = inst[200] / inst[20]
    ok = propre <= 0.25 * t_e1 and ratio <= 20.0
    return ok, (f"coeur Rust {'present' if W.COEUR is not None else 'ABSENT'} ; {len(w20.habitants)} habitants, {D.T.n} "
                f"contrats : moteur seul {t_e1:.2f} s par jour, routines propres {propre * 1000:.1f} ms ( {propre / t_e1:.1%} ) ; "
                f"installation {inst[20]:.3f} s a 10 000, {inst[200]:.3f} s a 100 000 ( {n200} contrats, x{ratio:.1f} )")


TESTS = [test_taux_de_souscription, test_primes_et_sinistres_au_centime, test_non_assure_et_falsificateurs,
         test_choc_seisme_et_reassurance, test_faillite, test_elga_grele, test_decision, test_pays_vivable, test_cout]
