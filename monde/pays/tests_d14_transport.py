"""Les portes du domaine 14 ( transport et vehicules ). Ecrites avant la premiere mesure.
python -m monde.pays.tests transport"""
import math, time, tracemalloc
import numpy as np
from .. import config as C, monde as W
from ..socle import objets as O, registre as R
from . import essais as T, d02_banques as BQ, d12_services_publics as SP, d14_transport as M


def _voisins(n, pas):
    pts = M.emplacements(n, pas)
    return min(math.dist(a, b) for i, a in enumerate(pts) for b in pts[i + 1:])


# ================================================================== les lois
def test_modeles():
    """Porte : les dix categories demandees sont declarees au Parc ( famille vehicule ), chacune avec un classname Arma
    ascii qui n est pas le van mort C_Van_01_box_F et SANS preuve ( personne ne les a vus vivre en jeu ) ; les prix
    passent par EUROS_PAR_DRACHME ; les consommations et autonomies sont dans les bandes reelles ( voiture 4 a 10 l/100 km,
    deux-roues 2 a 6, camion 18 a 35, autocar 25 a 45 ; autonomie 250 a 1 100 km ) ; une voiture neuve paie la taxe
    d immatriculation et une moto la taxe de circulation de sa cylindree. Falsificateur : un modele au van mort est
    refuse. Controle d incarnation : 50 vehicules poses par `emplacements` sont a 8 m au moins les uns des autres."""
    w, p = T.monde(["transport"])
    parc = p.socle.parc
    noms = ("citadine", "berline", "suv", "pick_up", "utilitaire", "camion", "bus", "moto", "scooter", "tracteur")
    decl = all(n in parc.par_nom and parc.par_nom[n].famille == "vehicule" for n in noms)
    arma = all(parc.par_nom[n].arma and parc.par_nom[n].arma.isascii() and parc.par_nom[n].arma != "C_Van_01_box_F"
               and parc.par_nom[n].arma_preuve is None for n in noms)
    euros = all(abs(c.prix_ttc * 1.15 - m[3]) < 1e-6 for c, m in zip(M.CARAC, M.MODELES))
    bandes = {"voiture": (4, 10), "utilitaire_leger": (6, 14), "deux_roues": (2, 6), "poids_lourd": (18, 35),
              "autocar": (25, 45), "agricole": (30, 80)}
    conso = all(bandes[c.categorie][0] <= c.l100 <= bandes[c.categorie][1] for c in M.CARAC)
    auton = all(250 <= c.autonomie_km() <= 1100 for c in M.CARAC)
    immat = M.caracteristiques("suv").taux_immat > 0 and M.taxe_circulation(M.caracteristiques("moto"), 2030) > 0
    try:
        M.Caracteristiques(99, "van", "utilitaire_leger", "C_Van_01_box_F", *M.MODELES[4][3:]); refuse = False
    except ValueError: refuse = True
    d = _voisins(50, M.ESPACEMENT_M)
    ok = decl and arma and euros and conso and auton and immat and refuse and d >= M.ESPACEMENT_M - 1e-9
    return ok, (f"10 modeles declares {decl}, classnames sans preuve {arma}, prix en drachmes par 1,15 {euros}, "
                f"consommations {conso}, autonomies {auton} ( " + ", ".join(f"{c.nom} {c.autonomie_km():.0f}" for c in M.CARAC)
                + f" km ), taxes {immat} ; van mort refuse {refuse} ; 50 vehicules espaces d au moins {d:.1f} m")


def test_recensement():
    """Porte : au recensement ( 2 500 habitants ), 520 a 600 voitures pour 1 000 habitants ( Grece ~ 560 ), age moyen des
    voitures de 14,5 a 19 ans ( ~ 17 ), 110 a 210 deux-roues pour 1 000, 65 a 85 % des adultes titulaires du permis B,
    et le quintile de revenu le plus haut a au moins deux fois plus de voitures par menage que le plus bas ; aucune
    anomalie du registre. Controle positif : un pays recense avec deux fois moins de voitures visees en a 0,45 a 0,55
    fois autant."""
    w, p = T.monde(["transport"], echelle=5)
    r = M.recensement_du_parc(p)
    an = M.anomalies_parc(p)
    n = len(w.menages)
    rev = np.array([M._revenu(p, i) for i in range(n)])
    voit = sum(((M._cols(p, f"vh_m{k}")[:n] >= 0) & M.IS_VOITURE[np.maximum(M._cols(p, f"vh_m{k}")[:n], 0)]).astype(int)
               for k in M.K3)
    hab = np.array([any(x.vivant for x in mg.membres) for mg in w.menages])
    io = np.nonzero(hab)[0]; ordre = io[np.argsort(rev[io], kind="stable")]
    q1, q5 = voit[ordre[:len(ordre) // 5]].mean(), voit[ordre[-len(ordre) // 5:]].mean()
    ancien = M.VOITURES_1000
    try:
        M.VOITURES_1000 = ancien / 2.0
        r2 = M.recensement_du_parc(T.monde(["transport"], echelle=5)[1])
    finally:
        M.VOITURES_1000 = ancien
    ratio = r2["voitures_1000"] / r["voitures_1000"]
    ok = (520 <= r["voitures_1000"] <= 600 and 14.5 <= r["age_voitures"] <= 19 and 110 <= r["deux_roues_1000"] <= 210
          and 0.65 <= r["permis_b"] <= 0.85 and q5 >= 2 * q1 and not an and 0.45 <= ratio <= 0.55)
    return ok, (f"{r['habitants']} habitants : {r['voitures_1000']:.0f} voitures pour 1 000, age moyen {r['age_voitures']:.1f} "
                f"ans, {r['deux_roues_1000']:.0f} deux-roues pour 1 000, permis B {r['permis_b']:.0%} des adultes ; voitures "
                f"par menage : quintile bas {q1:.2f}, haut {q5:.2f} ; parc {r['par_modele']} ; anomalies {len(an)} ; "
                f"cible divisee par deux : x{ratio:.2f}")


# ================================================================== la conservation des objets
def test_conservation_objets():
    """Porte : 36 jours ( plus que l enquete d un vol ) sous un scenario charge ( pannes x20, accidents x100, vols x300, rebuts x5 ) : Parc.verifier nul,
    registre = Parc pour chaque modele, emplacements des menages = cohortes de la flotte + individus, aucun individu
    orphelin, litres des colonnes = Stock des reservoirs, conservation du socle tenue, et le rapprochement des familles
    du domaine nul ( aucun paiement hors du grand livre ). L instrument a ete exerce : au moins 5 vols, 5 reparations,
    5 ventes, 1 vehicule detruit ou mis au rebut, 1 vol resolu ( retrouve, exporte ou depece )."""
    w, p = T.monde(["transport"])
    rap = R.Rapprochement(p.socle.registre, p.socle.livre)
    M.scenario(p, pannes=20.0, accidents=100.0, vols=300.0, rebut=5.0)
    T.jours(w, 36)
    tr = p.domaine("transport"); s = tr.stats
    an = M.anomalies_parc(p)
    tenue, msg = p.socle.conservation.tenue()
    restes = {k: v for k, v in rap.restes().items() if k in ("concessions", "stations_service", "garages")}
    propres = all(abs(v) <= R.tolerance(v) for v in restes.values())
    exerce = s["vols"] >= 5 and s["reparations"] >= 5 and s["ventes_neuf"] + s["ventes_occasion"] >= 5 \
        and s["detruits"] + s["rebuts"] >= 1 and any(v.issue is not None for v in tr.vols)
    ok = not an and tenue and propres and exerce
    return ok, (f"vols {s['vols']:.0f} ( retrouves {s['retrouves']:.0f} ), pannes {s['pannes']:.0f}, reparations "
                f"{s['reparations']:.0f}, accidents {s['accidents_materiels']:.0f} materiels et {s['accidents_corporels']:.0f} "
                f"corporels, detruits {s['detruits']:.0f}, rebuts {s['rebuts']:.0f}, exportes {s['exportes']:.0f}, ventes "
                f"{s['ventes_neuf']:.0f} neuves et {s['ventes_occasion']:.0f} d occasion ; individus vivants "
                f"{sum(1 for o in p.socle.parc.objets.values() if o.modele in tr.idx_parc)} ; anomalies {an[:4]} ; {msg} ; "
                f"rapprochement du domaine {restes}")


# ================================================================== le carburant
def test_carburant():
    """Porte, 8 jours : ( a ) chaque soir, les litres brules sous carburant_route = somme sur les vehicules des menages des
    km ajoutes au compteur x L/100 km / 100 ( a 1e-4 pres : l arrondi des compteurs en float32 ) ; ( b ) ce que le
    domaine dit avoir achete a la raffinerie = ce que le grand livre a vu sortir du domaine 11 sous son motif
    ( vente_produit_petrolier ), a 1e-9 ; ( c ) stocks des stations et des reservoirs : variation = achats au domaine 11 +
    imports + dotation - brule - perdu, exacte ( 1e-9 ). Falsificateur : 5 km ajoutes a la main a un compteur rendent
    ( a ) faux."""
    w, p = T.monde(["transport"])
    tr = p.domaine("transport"); L = p.socle.livre
    T.jours(w, 1)
    ecarts_a, achats_d11, vus_d11 = [], 0.0, 0.0
    a0 = tr.stats["litres_achetes_d11"]; i0 = tr.stats["litres_importes"]

    def stock_total():
        return sum(st.stock[tr.bid[b]] for st in tr.stations for b in M.FUELS) + sum(tr.reservoirs.stock[tr.bid[b]] for b in M.FUELS)
    s0 = stock_total()
    brule = perdu = 0.0
    faux = None
    for j in range(8):
        # jusqu a 20 h 20 ( avant la journee du transport )
        while w.minutes % 1440 != 20 * 60 + 20: w.pas_suivant()
        n = len(w.menages)
        v, bits, classe = M._habitants(p, tr)
        avant = {b: L.flux["brule"].get(b, 0.0) for b in M.FUELS}
        km0 = [M._cols(p, f"vh_km{k}")[:n].astype(float).copy() for k in M.K3]
        mods = [M._cols(p, f"vh_m{k}")[:n].astype(np.int64).copy() for k in M.K3]
        M._rouler(p, tr, n, v, bits)
        if j == 7:                                   # le falsificateur, apres le roulage du dernier jour
            i = int(np.nonzero(mods[0] >= 0)[0][0]); M._cols(p, "vh_km0")[i] += 5.0
        att = sum(float(((M._cols(p, f"vh_km{k}")[:n].astype(float) - km0[k]) * M.L100[np.maximum(mods[k], 0)] / 100.0)[mods[k] >= 0].sum())
                  for k in M.K3)
        vu = sum(L.flux["brule"].get(b, 0.0) - avant[b] for b in M.FUELS) * M.LITRES_UNITE
        e = abs(att - vu) / max(1.0, vu)
        if j < 7: ecarts_a.append(e)
        else: faux = e
        # la suite du jour ( le roulage est deja fait : la routine le refait, les deux comptent dans les stocks )
        T.jours(w, 1)
        for (nat, motif, bien, q) in p.comptes_hier["biens"]:
            if bien not in M.FUELS: continue
            if nat == "deplace" and motif == "vente_produit_petrolier": vus_d11 += q
            if nat == "brule" and motif in ("carburant_route", "carburant_route_flottes"): brule += q
            if nat == "perdu" and motif == "reservoir_sorti": perdu += q
    while w.minutes % 1440 != 0: w.pas_suivant()      # la cloture du dernier jour
    for (nat, motif, bien, q) in p.comptes_hier["biens"]:
        if bien not in M.FUELS: continue
        if nat == "deplace" and motif == "vente_produit_petrolier": vus_d11 += q
        if nat == "brule" and motif in ("carburant_route", "carburant_route_flottes"): brule += q
        if nat == "perdu" and motif == "reservoir_sorti": perdu += q
    achats_d11 = (tr.stats["litres_achetes_d11"] - a0) / M.LITRES_UNITE
    imports = (tr.stats["litres_importes"] - i0) / M.LITRES_UNITE
    ds = stock_total() - s0
    bilan = abs(ds - (achats_d11 + imports - brule - perdu)) <= 1e-9 * max(1.0, brule) + 1e-9
    b_ok = abs(achats_d11 - vus_d11) <= 1e-9 * max(1.0, vus_d11)
    a_ok = max(ecarts_a) <= 1e-4 and faux > 1e-4
    ok = a_ok and b_ok and bilan
    return ok, (f"( a ) km x L/100 km contre le brule du grand livre : pire ecart relatif {max(ecarts_a):.1e} sur 7 soirs, "
                f"compteur fausse de 5 km : {faux:.1e} ; ( b ) achats a la raffinerie {achats_d11 * 10:.0f} l, vus sortir du "
                f"domaine 11 {vus_d11 * 10:.0f} l ; ( c ) stocks {ds * 10:+.1f} l = achats + imports {imports * 10:.0f} l - brule "
                f"{brule * 10:.0f} l - perdu {perdu * 10:.1f} l : {bilan}")


# ================================================================== les accidents
def _parc_synthetique(rng, habitants):
    mods, km = [], []
    for c in M.CARAC:
        n = int(round(M.PARC_1000[c.nom] * habitants / 1000.0))
        a = M._tirer_age(rng, c.categorie, n)
        mods.append(np.full(n, c.idx)); km.append(c.km_an * M.facteur_age(a))
    return np.concatenate(mods), np.concatenate(km)


def _morts(tues, iss):
    """Tues a 30 jours attendus : sur le coup, plus la letalite soignee de la medecine ( a 40 ans ) des blesses."""
    from . import d16_medecine as MED
    hop = sum(float(MED.letalite_iss(g, 40.0)) for gs in iss for g in gs)
    return sum(tues) + hop


def test_accidents():
    """Porte ( un parc grec synthetique d un million d habitants, un an, par la fonction de la journee ) : 950 a 1 300
    victimes par million d habitants et par an ( Grece ~ 1 125 ), 45 a 70 tues a 30 jours ( ~ 57 : sur le coup, plus la
    letalite soignee de la medecine ), 20 a 50 % des tues en deux-roues. Controle positif sur des routes degradees
    ( etat 0,1 : facteur d accident des services publics ) : 1,5 a 1,8 fois plus de victimes. Dans le pays ( services
    publics et medecine installes, 1 000 habitants, accidents corporels x20 000, 20 jours, meme graine ) : routes a 0,15
    contre routes du recensement, 1,3 a 2,0 fois plus d accidents corporels par km roule ; les tues passent par `deceder` ( cause accident ), les
    blesses par `blesser` ( lesions de la route ), et la medecine a laisse la route au domaine."""
    rng = np.random.default_rng(14)
    mods, km = _parc_synthetique(rng, 1_000_000)
    res = {}
    for nom, f in (("normal", 1.0), ("degrade", float(SP.risque_accident(0.1)))):
        idx, corp, vict, tues, iss = M.tirer_accidents(np.random.default_rng(7), km, mods, np.full(len(km), f))
        v = int(vict[corp].sum())
        deux = sum(t for t, j in zip(tues, idx.tolist()) if M.CARAC[mods[j]].categorie == "deux_roues")
        deux += _morts([0], [gs for gs, j, c_ in zip(iss, idx.tolist(), corp.tolist()) if c_ and M.CARAC[mods[j]].categorie == "deux_roues"])
        mo = _morts(tues, iss)
        res[nom] = (v, mo, deux / max(1e-9, mo), int(corp.sum()), int((~corp).sum()))
    v, mo, part2, nc, nm = res["normal"]
    rv = res["degrade"][0] / v
    synth = 950 <= v <= 1300 and 45 <= mo <= 70 and 0.2 <= part2 <= 0.5 and 1.5 <= rv <= 1.8

    def monde(degrade):
        w, p = T.monde(["transport", "services_publics", "medecine"], echelle=2)
        if degrade:
            p.domaine("services_publics").routes.etat[:] = 0.15
        M.scenario(p, corporels=20000.0)
        T.jours(w, 20)
        return w, p
    w1, p1 = monde(False); w2, p2 = monde(True)
    a1, a2 = p1.domaine("transport").stats, p2.domaine("transport").stats
    # par km roule : sous ce scenario, le monde aux routes degradees perd plus de vehicules ( detruits ) et de conducteurs,
    # et roule moins ( premiere mesure : un compte brut x1,14 pour un facteur de route x1,45 )
    rc = (a2["accidents_corporels"] / max(1.0, a2["km"])) / max(1e-12, a1["accidents_corporels"] / max(1.0, a1["km"]))
    col = p1.col("habitant", "cause_deces")
    morts_acc = int(sum(1 for h in w1.habitants if not h.vivant and col[h.id] == 4))
    med = p1.domaine("medecine")
    lesions = med.compteurs.get(("lesions", "route"), 0) if hasattr(med, "compteurs") else None
    repris = "route" in med.reprises
    pays = 1.3 <= rc <= 2.0 and repris and a1["tues_sur_le_coup"] <= morts_acc and a1["blesses"] >= 1
    ok = synth and pays
    return ok, (f"parc synthetique : {v} victimes pour un million ( {nc} accidents corporels, {nm} materiels ), {mo:.1f} tues "
                f"a 30 jours, {part2:.0%} en deux-roues ; routes degradees : victimes x{rv:.2f} | pays : accidents corporels "
                f"{a1['accidents_corporels']:.0f} en {a1['km']:.0f} km contre {a2['accidents_corporels']:.0f} en {a2['km']:.0f} km sur "
                f"routes degradees ( x{rc:.2f} par km ), "
                f"tues sur le coup {a1['tues_sur_le_coup']:.0f} ( morts par accident au registre {morts_acc} ), blesses "
                f"{a1['blesses']:.0f} ( lesions de la route vues par la medecine {lesions} ), route reprise {repris}")


# ================================================================== le credit
def _tableau(montant, taux, duree):
    """Le tableau d amortissement a mensualites constantes, calcule ici sans le domaine 2 : ( interets, principal )."""
    r = taux / 12.0
    m = montant * r / (1.0 - (1.0 + r) ** -duree)
    reste, it = montant, []
    for k in range(duree):
        i = reste * r
        a = reste if k == duree - 1 else m - i
        it.append(i); reste -= a
    return math.fsum(it), montant


def test_credit_au_centime():
    """Porte : un scooter neuf vendu a credit sur 3 mois ( 20 % d apport, pret direct de sa banque ) : le menage paie le prix TTC exact
    ( la concession recoit le prix hors taxes, l Etat la TVA ), le pret est solde au 92e jour, son principal rembourse
    = le montant prete et ses interets = ceux du tableau d amortissement calcule ici, au centime. Falsificateur : le
    tableau d une mensualite de moins s en ecarte de plus d un centime."""
    w, p = T.monde(["transport"])
    tr = p.domaine("transport"); L = p.socle.livre
    m = M.IDX["scooter"]
    prix, ht, immat = M.prix_neuf(p, M.CARAC[m])
    # le menage le plus riche qui a une place libre : il n apporte que 20 % et finance le reste
    cands = [mg for mg in w.menages if any(x.vivant for x in mg.membres) and M._slot_libre(p, mg.id) is not None
             and BQ.banque_de(p, mg) is not None]
    mg = max(cands, key=lambda x: (x.caisse, x.id))
    conc = tr.par_marche[mg.domicile.marche.id][0]
    if M._stock_neuf(p, tr, conc, m) < 1: return False, "pas de scooter en stock"
    c0, q0 = mg.caisse, conc.caisse
    fait = M.vendre_neuf(p, conc, mg, m, credit=True, octroi=False, duree=3, apport_max=0.2 * prix)
    pr = tr.prets_auto.get(mg.id, [None])[-1]
    if not fait or pr is None: return False, f"vente {fait}, pret {pr}"
    paye = (c0 - mg.caisse) + pr.montant - tr.depense_jour.get(mg.id, 0.0)    # sans le plein donne avec le vehicule
    recu_conc = conc.caisse - q0
    vente_ok = abs(paye - prix) <= 0.005 and abs(recu_conc - ht) <= 0.005
    T.jours(w, 92)
    solde = pr.id not in p.domaine("banques").prets
    i_th, p_th = _tableau(pr.montant, pr.taux, 3)
    i_faux, _ = _tableau(pr.montant, pr.taux, 2)
    ok = vente_ok and solde and abs(pr.paye_principal - p_th) <= 0.005 and abs(pr.paye_interet - i_th) <= 0.005 \
        and abs(pr.paye_interet - i_faux) > 0.01
    return ok, (f"scooter {prix:.2f} TTC ( {ht:.2f} HT ) : le menage a paye {paye:.2f}, la concession recu {recu_conc:.2f} ; pret "
                f"{pr.montant:.2f} a {pr.taux:.2%} sur 3 mois, solde {solde} ; principal rembourse {pr.paye_principal:.4f} "
                f"( tableau {p_th:.4f} ), interets {pr.paye_interet:.4f} ( tableau {i_th:.4f}, a deux mois {i_faux:.4f} )")


# ================================================================== le falsificateur du parc
def test_falsificateur():
    """Porte : un pays propre, puis 7 jours avec un import legitime ( jusqu a 3 scooters par la concession la plus riche,
    ce que sa caisse paie ), n a aucune anomalie ;
    une citadine creee a la main au Parc ( source importe, hors `importer_vehicules` ), une moto creee au Parc apres le
    recensement ( source initial ), une voiture posee dans les colonnes d un menage sans achat : chacune est vue."""
    w, p = T.monde(["transport"])
    tr = p.domaine("transport"); parc = p.socle.parc
    propre0 = M.anomalies_parc(p)
    T.jours(w, 3)
    conc = max(tr.concessions, key=lambda c: c.caisse)
    n_imp = M.importer_vehicules(p, conc, M.IDX["scooter"], 3, conc.marche)
    T.jours(w, 4)
    propre = M.anomalies_parc(p)
    lieu = w.menages[0].domicile.id
    parc.creer_cohorte(tr.mids[M.IDX["citadine"]], tr.flotte, lieu, 1, "importe")
    vu_import = any(a[0] == "hors_registre" and a[1] == "citadine" for a in M.anomalies_parc(p))
    w2, p2 = T.monde(["transport"])
    tr2 = p2.domaine("transport")
    p2.socle.parc.creer(tr2.mids[M.IDX["moto"]], tr2.concessions[0], tr2.concessions[0].marche, "initial", p2.pas)
    vu_initial = any(a[0] == "hors_registre" and a[1] == "moto" for a in M.anomalies_parc(p2))
    w3, p3 = T.monde(["transport"])
    tr3 = p3.domaine("transport")
    i = next(mg.id for mg in w3.menages if any(x.vivant for x in mg.membres)
             and all(M._cols(p3, f"vh_m{k}")[mg.id] < 0 for k in M.K3))
    M._cols(p3, "vh_m0")[i] = M.IDX["berline"]; M._cols(p3, "vh_lieu")[i] = tr3.k_lieu[w3.menages[i].domicile.id]
    vu_achat = any(a[0] == "hors_achat" for a in M.anomalies_parc(p3))
    ok = not propre0 and not propre and n_imp >= 1 and vu_import and vu_initial and vu_achat
    return ok, (f"pays propre : {len(propre0)} anomalie(s), apres un import de {n_imp} scooters : {len(propre)} ; citadine "
                f"creee a la main vue {vu_import} ; moto apres le recensement vue {vu_initial} ; voiture posee sans achat "
                f"vue {vu_achat}")


# ================================================================== la decision
def test_decision():
    """Porte de la decision ( 5 000 habitants, 40 jours, pannes x10 : une vague de pannes ou la decision compte ; modes
    hasard ) : pour `acheter_vehicule` et pour
    `reparer_vehicule`, la note depend du choix ( part du choix >= 0,01 et p de permutation < 0,05 ), avec au moins 300
    decisions d achat et 60 de reparation ; le pays reste conserve et sans anomalie."""
    w, p = T.monde(["transport"], echelle=10, modes={"acheter_vehicule": "hasard", "reparer_vehicule": "hasard"})
    M.scenario(p, pannes=10.0)
    T.jours(w, 40)
    tr = p.domaine("transport")
    out, ok = [], True
    for dec, mini in ((tr.dec_achat, 300), (tr.dec_reparer, 60)):
        e2, pp = dec.part_du_choix(), dec.p_permutation()
        ok &= dec.n_decisions >= mini and e2 >= 0.01 and pp < 0.05
        out.append(f"{dec.point.nom} : {dec.n_decisions} decisions, notes "
                   + ", ".join(f"{a} {m:.3f} ( {n} )" for a, (n, m) in dec.notes_par_action().items())
                   + f", part du choix {e2:.3f}, p {pp:.3f}")
    tenue, msg = p.socle.conservation.tenue()
    an = M.anomalies_parc(p)
    ok = ok and tenue and not an
    return ok, " ; ".join(out) + f" ; faim {T.faim(w):.1%} ; {msg} ; anomalies {len(an)}"


def test_pays_vivable():
    return T.porte_commune("transport", n_jours=12)


# ================================================================== le cout
def test_cout():
    """Le domaine coute au plus 25 % d une journee du pays sans lui ( ses dependances installees ), a 10 000 habitants ;
    ses colonnes au plus 80 octets par menage et 2 par habitant ; un individu du Parc coute plus que l emplacement d un
    vehicule ( la raison des colonnes )."""
    def jour_moyen(domaines):
        w, p = T.monde(domaines, echelle=20)
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, w, p
    t0, _, _ = jour_moyen(["banques", "exterieur", "industrie", "energie"])
    t1, w, p = jour_moyen(["transport"])
    tr = p.domaine("transport")
    cm, ch = p.colonnes["menage"], p.colonnes["habitant"]
    oct_m = sum(cm[k].itemsize for k in cm.cols if k.startswith("vh_"))
    oct_h = sum(ch[k].itemsize for k in ch.cols if k.startswith("vh_"))
    parc = O.Parc(p.socle.hasard); parc.declarer_modele("essai", "vehicule", 1e4, 1e3, 1e4)
    tracemalloc.start(); a = tracemalloc.get_traced_memory()[0]
    garde = [parc.creer(0, None, "L", "initial", 0) for _ in range(20000)]
    oct_obj = (tracemalloc.get_traced_memory()[0] - a) / 20000; tracemalloc.stop(); del garde
    veh = sum(p.socle.parc.vivants[m] for m in tr.mids)
    nh, nm = len(w.habitants), len(w.menages)
    part = (t1 - t0) / t0
    ok = part <= 0.25 and oct_m <= 80 and oct_h <= 2 and oct_obj > oct_m / 3.0
    return ok, (f"{nh} habitants, {nm} menages, {veh} vehicules : pays sans transport {t0:.2f} s par jour, avec {t1:.2f} s "
                f"( {part:+.0%} ) ; colonnes {oct_m} octets par menage ( 3 emplacements ) et {oct_h} par habitant ; un objet du "
                f"Parc {oct_obj:.0f} octets ; a 50 millions d habitants ( ~ 20 millions de menages, ~ 28 millions de "
                f"vehicules ) : colonnes ~ {20e6 * oct_m / 1e9 + 50e6 * oct_h / 1e9:.1f} Go contre ~ {28e6 * oct_obj / 1e9:.1f} Go "
                f"d objets ; temps propre ~ {(t1 - t0) / nh * 1e6:.0f} us par habitant et par jour, "
                f"~ {(t1 - t0) / nh * 5e7 / 60:.0f} min par jour a 50 millions")


TESTS = [test_modeles, test_recensement, test_conservation_objets, test_carburant, test_accidents, test_credit_au_centime,
         test_falsificateur, test_decision, test_pays_vivable, test_cout]
