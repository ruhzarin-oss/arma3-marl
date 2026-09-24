"""Les portes du domaine 13 ( immobilier et construction ). Seuils ecrits avant la premiere mesure.
python -m monde.pays.tests immobilier"""
import math, time
import numpy as np
from .. import monde as W
from ..socle import objets as O, comptes as K
from . import essais as T, pays as P, d13_immobilier as M, d01_population as POP


def _audit_msg(a):
    return (f"orphelins {len(a['orphelins'])}, fantomes {len(a['fantomes'])}, ecarts de sources {a['sources']}, "
            f"Parc.verifier {a['parc']}")


# ================================================================== le logement de chaque menage, la bande grecque
def test_logement_et_proprietaires():
    """Porte : au recensement puis apres 20 jours ( 1 000 habitants ), chaque menage habite a un logement, dont il
    est l occupant, aucun logement n a plus d occupants que sa capacite ; la part des personnes logees chez leur
    menage proprietaire est dans [ 0,70 ; 0,78 ] ( Eurostat, Grece : 73,5 % ) ; la surface moyenne des residences
    principales est de 65 a 100 m2 ( ELSTAT ~ 80 ). Falsificateurs : un menage prive de son lien a la main, un
    logement retreci a 10 m2 sous une famille : les deux se voient."""
    w, p = T.monde(["immobilier"], echelle=2)
    d = p.domaine("immobilier"); B = d.B
    a0 = M.anomalies_logement(p); part0 = M.part_proprietaires(p)
    T.jours(w, 20)
    a1 = M.anomalies_logement(p); part1 = M.part_proprietaires(p)
    n = len(w.menages)
    log = p.col("menage", "im_logement")[:n]
    occ = [int(b) for b in log if b >= 0]
    surf = float(np.mean(B["surface"][occ]))
    locs = [b for b in d.baux.values()]
    effort = np.median([b.loyer / max(1e-9, M.revenu_mensuel(p, b.locataire)) for b in locs]) if locs else 0.0
    loyer_m2 = np.median([b.loyer / B["surface"][b.b] * P.EUROS_PAR_DRACHME for b in locs]) if locs else 0.0
    bande = all(M.BANDE_PROPRIETAIRES[0] <= x[0] <= M.BANDE_PROPRIETAIRES[1] for x in (part0, part1))
    ok_porte = not a0 and not a1 and bande and 65.0 <= surf <= 100.0
    # falsificateurs
    i = next(k for k in range(n) if log[k] >= 0 and M._n_vivants(w.menages[k]) >= 3)
    b = int(log[i])
    s = float(B["surface"][b]); B["surface"][b] = 10.0
    vu_surpeuple = any(x[0] == "surpeuple" and x[1] == b for x in M.anomalies_logement(p))
    B["surface"][b] = s
    j = next(k for k in range(n) if log[k] >= 0 and k != i)
    bj = int(log[j]); p.col("menage", "im_logement")[j] = -1
    vu_lien = ("sans_logement", j) in M.anomalies_logement(p)
    p.col("menage", "im_logement")[j] = bj
    ok = ok_porte and vu_surpeuple and vu_lien
    return ok, (f"anomalies au recensement {len(a0)}, a 20 jours {len(a1)} {a1[:3]} ; proprietaires ( personnes, "
                f"menages ) {part0[0]:.3f} / {part0[1]:.3f} puis {part1[0]:.3f} / {part1[1]:.3f} ; surface moyenne "
                f"{surf:.1f} m2 ; {len(locs)} baux, loyer median {loyer_m2:.2f} euros/m2/mois, effort median "
                f"{effort:.0%} ; {len(d.cherche)} menages cherchent ; surpeuplement pose vu {vu_surpeuple}, lien casse "
                f"vu {vu_lien}")


# ================================================================== la conservation des batiments
def test_conservation_batiments():
    """Porte : 15 jours avec un seisme d intensite 8,5 sur une capitale ( des batiments detruits, des abris tires de la
    reserve ou importes ) : Parc.verifier nul pour chaque modele, les comptes du Parc egaux aux naissances et aux
    sorties faites par le domaine, individus du Parc = individus de la table, conservation du socle tenue.
    Falsificateurs : une maison creee a la main par Parc.creer ( source fabrique, sans chantier ) et une maison sortie
    a la main par Parc.sortir : Parc.verifier reste nul ( les comptes sont coherents ), l audit du domaine voit les deux."""
    w, p = T.monde(["immobilier"])
    d = p.domaine("immobilier"); parc = p.socle.parc
    T.jours(w, 5)
    cap = sorted(w.marches)[0]
    res = M.appliquer_seisme(p, {cap: 8.5})
    T.jours(w, 10)
    a = M.audit_batiments(p)
    tenue, msg = p.socle.conservation.tenue()
    detruits = sum(d.sortis[n]["detruit"] for n in M.NOMS_MODELES)
    ok_porte = M.audit_propre(a) and tenue and detruits >= 1
    mg = next(m for m in w.menages if M._n_vivants(m) > 0)
    faux = parc.creer(d.modele_parc["maison"], mg, mg.domicile.id, "fabrique", p.pas)
    a1 = M.audit_batiments(p)
    verif1 = {n: v for n, v in parc.verifier().items() if n in M.NOMS_MODELES and v}
    vu_creation = faux.id in a1["orphelins"] and ("maison", "fabrique") in a1["sources"] and not verif1
    parc.sortir(faux, "detruit")
    B = d.B
    b = next(int(x) for x in np.nonzero((B["vivant"][:B.n] == 1) & (B["modele"][:B.n] == d.idx_modele["maison"])
                                         & (B["occupant"][:B.n] < 0))[0])
    parc.sortir(M._objet(p, d, b), "detruit")
    a2 = M.audit_batiments(p)
    vu_sortie = int(B["oid"][b]) in a2["fantomes"]
    ok = ok_porte and vu_creation and vu_sortie
    return ok, (f"seisme 8,5 a {cap} : {res.get(cap)} ( batiments, touches, inhabitables, detruits ) ; detruits au Parc "
                f"{detruits}, abris donnes {d.stats['abris_donnes']:.0f} dont importes {d.stats['abris_importes']:.0f} ; "
                f"audit : {_audit_msg(a)} ; {msg} ; creation hors chantier vue {vu_creation} ( Parc.verifier muet : "
                f"{not verif1} ), sortie hors puits du domaine vue {vu_sortie}")


# ================================================================== les seismes
def test_seisme():
    """Controle positif sur 20 000 batiments de beton arme des annees 1960-1984 ( V = 0,62 ) : la part en etat D3 ou
    plus croit strictement avec l intensite de V a IX ; sous 0,5 % a V ; de 5 a 20 % a VIII ( EMS-98, classe C :
    « quelques » D3 ) et de 20 a 60 % a IX ( « beaucoup » ) ; a VIII, la maconnerie d avant 1959 est plus touchee
    que le beton post-2000. Porte dans le monde ( 1 000 habitants ) : un seisme d intensite 9 sur une capitale touche
    des batiments de ce lieu et d aucun autre, chaque menage reste loge le jour meme, les sinistres ont un chantier
    ouvert, l audit et la conservation tiennent. Temoin negatif : intensite 3, aucun dommage."""
    rng = np.random.default_rng(7)
    n = 20000
    parts = [float((M.tirer_dommages(np.full(n, I), np.full(n, 0.62), rng) >= 3).mean()) for I in (5, 6, 7, 8, 9)]
    pierre = float(M.tirer_dommages(np.full(n, 8.0), np.full(n, 0.74), rng).mean())
    moderne = float(M.tirer_dommages(np.full(n, 8.0), np.full(n, 0.36), rng).mean())
    loi = (all(a < b for a, b in zip(parts, parts[1:])) and parts[0] < 0.005 and 0.05 <= parts[3] <= 0.20
           and 0.20 <= parts[4] <= 0.60 and pierre > moderne)
    w, p = T.monde(["immobilier"], echelle=2)
    d = p.domaine("immobilier"); B = d.B
    T.jours(w, 2)
    cap = sorted(w.marches)[0]; kc = d.k_lieu[cap]
    avant = B["dommage"][:B.n].copy()
    rien = M.appliquer_seisme(p, {cap: 3.0})
    calme = int((B["dommage"][:B.n] != avant).sum()) == 0
    ch0 = len(d.chantiers)
    res = M.appliquer_seisme(p, {cap: 9.0})
    n2 = B.n
    change = np.nonzero(B["dommage"][:n2] > np.concatenate((avant, np.zeros(n2 - len(avant), np.int8))))[0]
    ailleurs = int(sum(1 for b in change.tolist() if B["lieu"][b] != kc))
    anomalies = M.anomalies_logement(p)
    ouverts = len(d.chantiers) - ch0
    T.jours(w, 2)
    a = M.audit_batiments(p)
    tenue, msg = p.socle.conservation.tenue()
    lieu = res[cap]
    ok = (loi and calme and lieu[1] >= 5 and ailleurs == 0 and not anomalies and ouverts >= 1 and M.audit_propre(a)
          and tenue)
    return ok, (f"part D3+ de V a IX : " + ", ".join(f"{x:.4f}" for x in parts) + f" ; a VIII degat moyen pierre "
                f"{pierre:.2f}, beton post-2000 {moderne:.2f} ; intensite 3 : dommages {not calme} ; intensite 9 a {cap} : "
                f"{lieu} ( batiments, touches, inhabitables, detruits ), ailleurs {ailleurs}, chantiers ouverts {ouverts}, "
                f"anomalies de logement {len(anomalies)} ; audit {M.audit_propre(a)} ; {msg}")


# ================================================================== le bilan matiere d un chantier
def test_chantier_bilan_matiere():
    """Porte ( avec le domaine 4 pour les ouvriers, 1 000 habitants ) : une maison endommagee ( D2 ) est reparee -
    permis ( droits payes a l Etat ), materiaux livres par l industrie ( importes s il ne les livre pas ), ouvriers embauches par le marche du travail et
    payes par l entreprise de BTP. A la fin, pour chaque materiau : livre = consomme + reste au centieme de
    kilogramme pres, consomme = besoin ( 1e-9 relatif ), heures >= heures requises, degats effaces, devis paye par le
    maitre ou du en creance, conservation tenue. Falsificateur : 100 kg de ciment retires a la main du stock d un
    second chantier : son bilan le voit."""
    w, p = T.monde(["immobilier", "travail"], echelle=2)
    d = p.domaine("immobilier"); B = d.B; L = p.socle.livre; cat = p.socle.catalogue
    d.delai_permis_j = 0
    T.jours(w, 1)
    g0 = w.gouv.caisse
    cands = [int(b) for b in np.nonzero((B["vivant"][:B.n] == 1) & (B["modele"][:B.n] == d.idx_modele["maison"])
                                        & (B["occupant"][:B.n] >= 0))[0]]
    ch = None
    for b in cands:
        prop = M.proprietaire(p, b)
        if type(prop).__name__ == "Menage" and prop.caisse > 3000:
            M.endommager(p, b, 2, "essai")
            ch = d.chantiers.get(int(B["chantier"][b]))
            if ch is not None: break
    if ch is None: return False, "aucun chantier n a pu s ouvrir"
    for _ in range(60):
        T.jours(w, 1)
        if ch.etat == "termine": break
    bilan = {x: ch.livre[x] - ch.consomme[x] - ch.reste[x] - ch.stock[cat.id(x)] for x in ch.besoins}
    importe = {x: round(v, 3) for x, v in ch.importe.items() if v > 0}
    besoin = {x: abs(ch.consomme[x] - ch.besoins[x]) / ch.besoins[x] for x in ch.besoins}
    creances = sum(c.montant for c in p.socle.creances.de(ch.maitre) if c.motif == "travaux")
    paye_ok = abs(ch.paye + creances - ch.devis) <= 0.01
    tenue, msg = p.socle.conservation.tenue()
    fini = ch.etat == "termine"
    ok_porte = (fini and all(abs(v) <= 1e-5 for v in bilan.values()) and all(v <= 1e-9 for v in besoin.values())
                and ch.heures >= ch.heures_req - 1e-9 and B["dommage"][ch.b] == 0 and paye_ok and tenue)
    # falsificateur sur un second chantier
    b2 = next(b for b in cands if b != ch.b and B["chantier"][b] < 0 and type(M.proprietaire(p, b)).__name__ == "Menage"
              and M.proprietaire(p, b).caisse > 3000)
    M.endommager(p, b2, 3, "essai")
    ch2 = d.chantiers.get(int(B["chantier"][b2]))
    vu = False
    if ch2 is not None:
        for _ in range(8):
            T.jours(w, 1)
            if ch2.stock[cat.id("ciment")] > 0.2: break
        if ch2.stock[cat.id("ciment")] > 0.1:
            ch2.stock._retirer(cat.id("ciment"), 0.1)
            vu = abs(ch2.livre["ciment"] - ch2.consomme["ciment"] - ch2.reste["ciment"] - ch2.stock[cat.id("ciment")]) > 1e-3
    ok = ok_porte and vu
    return ok, (f"chantier {ch.id} ( renovation, {ch.surface:.0f} m2, devis {ch.devis:.0f} ) {'termine' if fini else 'NON TERMINE'} "
                f"en {ch.fin_j - ch.debut_j if fini else -1} jours, {ch.heures:.0f} h pour {ch.heures_req:.0f} requises ; "
                f"livre / consomme / reste ( t ) : " + ", ".join(f"{x} {ch.livre[x]:.3f}/{ch.consomme[x]:.3f}/{ch.reste[x]:.3f}"
                                                                   for x in sorted(ch.besoins))
                + f" ; dont importe {importe} ; pire bilan {max(abs(v) for v in bilan.values()):.1e} t ; devis paye {ch.paye:.2f} + du {creances:.2f} ; "
                f"BTP : materiaux {ch.btp.materiaux:.0f}, fournitures {ch.btp.fournitures:.0f}, encaisse {ch.btp.encaisse:.0f} ; {msg} ; ciment retire a la main vu {vu}")


# ================================================================== loyers et impayes au centime
def test_loyers_au_centime():
    """Porte : un bail dont le loyer est porte a trois mois de revenu du locataire ( un loyer insoutenable ) ; il paie
    ce qu il peut sans toucher a sa reserve de nourriture. Sur 100 jours, pour ce bail : loyers echus = payes +
    impayes ( creances du socle, motif loyer, creancier le bailleur, debiteur le locataire ) au centime ; au troisieme
    terme impaye le litige s ouvre, puis l expulsion ( delai mis a zero ) le reloge ( un logement ou un abri ), le
    depot compensant ses arrieres. Pour tout le pays : le grand livre a vu, sous le motif loyer, exactement ce que le
    domaine a encaisse ( au centime ). Falsificateur : 10 drachmes de loyer comptees sans passer par le grand livre."""
    w, p = T.monde(["immobilier"])
    d = p.domaine("immobilier"); Kc = p.socle.creances
    d.delai_expulsion_j = 0
    enc0 = d.stats["loyers_encaisses"]
    livre = [0.0]
    bail = next(b for b in sorted(d.baux.values(), key=lambda x: x.id) if M._n_vivants(b.locataire) >= 1)
    loc = bail.locataire; bailleur = M.proprietaire(p, bail.b)
    bail.loyer = round(max(bail.loyer, 3.0 * M.revenu_mensuel(p, loc)), 2)
    du0, paye0 = bail.du, bail.paye
    expulsions0 = d.stats["expulsions"]
    litige = -1; fin = None
    for j in range(100):
        T.jours(w, 1)
        for m, pa, re, s, _ in p.comptes_hier["argent"]:
            if m == "loyer": livre[0] += s
        if bail.litige_j >= 0 and litige < 0: litige = bail.litige_j
        if bail.id not in d.baux and fin is None: fin = p.jour
    termes = int(round((bail.du - du0) / bail.loyer))
    impayes = sum(c.montant for c in bail.impayes if Kc.actives.get(c.id) is c)
    creances_ok = bool(bail.impayes) and all(c.creancier is bailleur and c.debiteur is loc and c.motif == "loyer"
                                             for c in bail.impayes)
    ecart_bail = (bail.du - du0) - (bail.paye - paye0) - impayes      # le depot qui regle des arrieres compte dans paye
    ecart_pays = livre[0] - (d.stats["loyers_encaisses"] - enc0)
    expulse = any(e["bail"] == bail.id for e in p.socle.journal.derniers("expulsion", 1000))
    reloge = p.col("menage", "im_logement")[loc.id] >= 0 or M._n_vivants(loc) == 0
    ok_porte = (abs(ecart_bail) <= 0.005 and abs(ecart_pays) <= 0.005 and impayes > 0 and creances_ok and litige >= 0
                and expulse and reloge and termes >= MIN_TERMES)
    d.stats["loyers_encaisses"] += 10.0
    vu = abs(livre[0] - (d.stats["loyers_encaisses"] - enc0)) > 0.005
    d.stats["loyers_encaisses"] -= 10.0
    ok = ok_porte and vu
    return ok, (f"bail {bail.id} porte a {bail.loyer:.2f} par mois : {termes} termes echus, du {bail.du - du0:.2f}, paye "
                f"{bail.paye - paye0:.2f}, impayes {impayes:.2f} ( ecart {ecart_bail:+.4f} ) ; litige le jour {litige}, "
                f"expulsion notee {expulse} le jour {fin}, reloge {bool(reloge)} ( statut "
                f"{int(p.col('menage', 'im_statut')[loc.id])} ) ; expulsions du pays {d.stats['expulsions'] - expulsions0:.0f} ; "
                f"pays : grand livre {livre[0]:.2f}, domaine {d.stats['loyers_encaisses'] - enc0:.2f} ( ecart "
                f"{ecart_pays:+.4f} ) ; loyer compte hors grand livre vu {vu}")


MIN_TERMES = 3


# ================================================================== la decision
def _jeunes(p, w):
    out = []
    for mg in w.menages:
        v = [h for h in mg.membres if h.vivant]
        if len(v) < 2: continue
        for h in v:
            a = POP.age_de(p, h)
            if 18 <= a < 40 and h.role not in ("enfant", "retraite") and any(POP.age_de(p, x) >= a + 15 for x in v if x is not h):
                out.append(h)
    return out


def _scenario_loyer(mode, echelle, par_jour, jours=65, graine=None):
    """Un marche detendu ( 25 % de logements vides offerts, comme dans les regions grecques ou le parc vide depasse
    30 % ) et une vague de decohabitation : chaque jour pendant 35 jours, des jeunes adultes qui vivaient chez un aine
    fondent leur menage ( domaine 1 ) et cherchent un logement dans leur zone."""
    vac = M.TAUX_VACANTS
    M.TAUX_VACANTS = 0.25
    try:
        kw = {} if graine is None else {"graine": graine}
        w, p = T.monde(["immobilier"], echelle=echelle, modes={"fixer_loyer": mode}, **kw)
    finally:
        M.TAUX_VACANTS = vac
    rng = np.random.default_rng(5)
    for j in range(jours):
        if j < 35:
            js = _jeunes(p, w); rng.shuffle(js)
            for h in js[:par_jour]:
                mg = POP.nouveau_menage(p, h.menage.domicile); POP.deplacer_membre(p, h, mg)
        T.jours(w, 1)
    return w, p


def test_decision_loyer():
    """Porte de la decision : 1 500 habitants, marche detendu et vague de decohabitation, les bailleurs fixent le loyer
    de leurs logements vides AU HASARD. La note ( loyer percu sans impaye sur le loyer de reference, plus le menage
    loge, moins sa faim, sur 30 jours ) doit dependre du choix : part du choix ( epsilon carre ) >= 0,01 ET p de
    permutation < 0,05, avec au moins 300 notes. Le pays reste coherent ( logement, audit, conservation ). Mesures
    ( sans seuil ) : la note moyenne de la regle et du temoin dans le meme scenario a 1 000 habitants."""
    w, p = _scenario_loyer("hasard", 3, 6)
    d = p.domaine("immobilier"); dec = d.decideur
    part, pp = dec.part_du_choix(), dec.p_permutation()
    notes = dec.notes_par_action()
    nb = sum(n for n, _ in notes.values())
    jours = {}
    for (j, a), (n, s, q) in dec.stats.items(): jours.setdefault(j, 0); jours[j] += n
    an = M.anomalies_logement(p); a = M.audit_batiments(p)
    tenue, msg = p.socle.conservation.tenue()
    ok = part >= 0.01 and pp < 0.05 and nb >= 300 and not an and M.audit_propre(a) and tenue
    moy = {}
    for mode in ("regle", "temoin"):
        w2, p2 = _scenario_loyer(mode, 2, 4)
        dd = p2.domaine("immobilier").decideur.notes_par_action()
        tot = sum(n for n, _ in dd.values())
        moy[mode] = (sum(n * m for n, m in dd.values()) / tot if tot else 0.0, tot)
    return ok, (f"{dec.n_decisions} decisions, {nb} notes sur {len(jours)} jours ; notes : "
                + ", ".join(f"{k} {m:.3f} ( {n} )" for k, (n, m) in notes.items())
                + f" ; part du choix {part:.4f} ( brute {dec.part_du_choix_brute():.3f} ), p permutation {pp:.3f} ; "
                f"baux signes {d.stats['baux_signes']:.0f}, abris {d.stats['abris_donnes']:.0f} ; a 1 000 habitants, note "
                f"moyenne regle {moy['regle'][0]:.3f} ( {moy['regle'][1]} ), temoin {moy['temoin'][0]:.3f} "
                f"( {moy['temoin'][1]} ) ; anomalies {len(an)} ; audit {M.audit_propre(a)} ; {msg}")


# ================================================================== la porte commune et le cout
def test_pays_vivable():
    return T.porte_commune("immobilier", n_jours=12)


def test_cout():
    """Le domaine coute au plus 10 % d une journee du moteur a 10 000 habitants ( routines propres ), et le pays avec
    lui au plus 15 % de plus que le pays de ses seules dependances."""
    deps = ["banques", "etat", "territoire", "industrie"]
    def jour_moyen(doms):
        w = W.Monde(echelle=20)
        if doms: P.installer(w, doms)
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, w
    t_e1, w0 = jour_moyen(None)
    t_dep, _ = jour_moyen(deps)
    t_imm, w = jour_moyen(deps + ["immobilier"])
    p = w.pays
    t0 = time.perf_counter()
    for _ in range(3):
        M._seismes(p); M._matin(p); M._marche(p); M._materiaux(p); M._travail(p); M._soir(p); M._nuit(p)
    propre = (time.perf_counter() - t0) / 3
    d = p.domaine("immobilier")
    ok = propre <= 0.10 * t_e1 and t_imm <= 1.15 * t_dep
    return ok, (f"{len(w.habitants)} habitants, {d.B.n} batiments, {len(d.baux)} baux : moteur seul {t_e1:.2f} s par jour, "
                f"dependances {t_dep:.2f} s, avec l immobilier {t_imm:.2f} s ( {t_imm / t_dep - 1:+.1%} ) ; routines "
                f"propres {propre * 1000:.0f} ms par jour ( {propre / t_e1:.1%} du moteur, {propre / len(w.habitants) * 1e6:.1f} "
                f"us par habitant )")


TESTS = [test_logement_et_proprietaires, test_conservation_batiments, test_seisme, test_chantier_bilan_matiere,
         test_loyers_au_centime, test_decision_loyer, test_pays_vivable, test_cout]
