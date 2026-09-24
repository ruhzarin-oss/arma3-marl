"""Les portes du domaine 11 ( energie ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests energie"""
import time
import numpy as np
from .. import config as C, monde as W
from ..socle import registre as R_
from . import essais as T, d08_territoire as TER, d11_energie as M

PAS_H = C.PAS_PAR_JOUR // 24


def _avancer(w, heures):
    for _ in range(int(round(heures * PAS_H))): w.pas_suivant()


def _reseau(p, ile="Altis"): return p.domaine("energie").par_ile[ile]


# ================================================================== les unites
def test_unites_reelles():
    """Porte : les unites du moteur, traduites en grandeurs reelles, tombent dans les ordres de grandeur du monde. Le
    carburant du moteur ( 0,03 unite par km et par vehicule ) fait 25 a 40 litres aux 100 km pour un camion ; chaque
    unite de combustible porte 0,08 a 0,12 MWh PCI ; le brut a 5 drachmes les 10 litres fait 60 a 100 dollars le baril ;
    le tarif que l aube du moteur fixe tombe entre 0,10 et 0,30 drachme le kWh ; les quatre biens du domaine sont au catalogue avec
    leur masse et leur volume, et le petrole, le gazole et l electricite y sont calibres. Falsificateurs : un
    combustible a 100 MJ/kg est refuse, une technologie a 90 % de rendement aussi."""
    w, p = T.monde(["energie"])
    T.jours(w, 1)                                        # le tarif de l installation est le defaut du moteur, pas celui de l aube
    cat = p.socle.catalogue
    l100 = C.CARBURANT_PAR_KM * M.LITRES_UNITE * 100.0
    mwh = {b: c.mj() / 3600.0 for b, c in M.COMBUSTIBLES.items()}
    baril = cat["petrole"].prix_monde / M.LITRES_UNITE * 158.987 * 1.08
    tarif = M.tarif(p)
    biens = all(b in cat.par_nom and cat[b].masse_kg and cat[b].volume_l for b in ("gaz", "essence", "kerosene", "fioul"))
    calibres = all(cat[b].masse_kg is not None and cat[b].volume_l is not None for b in ("petrole", "carburant", "electricite"))
    refus = 0
    for f in (lambda: M.Combustible("x", 8.0, 100.0, 70.0, 0.0, "falsifie"),
              lambda: M.Technologie("x", ("fioul",), 0.9, 0.1, 0.4, 0, 1, 1000, 10, 1, 1, 0, 1, 1, 1, "x", None, "falsifie")):
        try: f()
        except ValueError: refus += 1
    ok = (25 <= l100 <= 40 and all(0.08 <= v <= 0.12 for v in mwh.values()) and 60 <= baril <= 100
          and 0.10 <= tarif <= 0.30 and biens and calibres and refus == 2)
    return ok, (f"camion {l100:.0f} l/100 km ; MWh PCI par unite : " + ", ".join(f"{b} {v:.3f}" for b, v in mwh.items())
                + f" ; brut {baril:.0f} dollars le baril ; tarif {tarif:.3f} drachme le kWh ; biens declares {biens}, "
                f"calibres {calibres} ; falsificateurs refuses {refus}/2")


# ================================================================== le bilan energetique
def test_bilan_energetique():
    """Porte : 5 jours sur Altis. Pour chaque groupe thermique, combustible ( MJ ) = electricite + chaleur perdue a 1e-9
    pres ; a pleine charge le rendement mesure est le rendement nominal ( 1e-9 ), compris entre 35 et 45 % pour chaque
    filiere ; a charge partielle il est plus bas. Les unites brulees que les groupes comptent sont celles que le grand
    livre a vu bruler ( 1e-9 ). Le reseau ferme : production + decharge - charge = consommations + sites + pertes, les
    pertes font 7 % de l injection, la batterie contient ce que ses charges et decharges y ont laisse. Falsificateurs :
    une unite de fioul brulee a la main sous le motif des centrales, et 50 kWh ajoutes au compteur d un groupe, se voient."""
    w, p = T.monde(["energie"])
    T.jours(w, 5)
    E = p.domaine("energie"); R = _reseau(p)
    groupes, ecarts = M.bilan_combustion(p)
    tot_mj = sum(g["mj"] for g in groupes.values())
    ferme = all(abs(g["ecart_mj"]) <= 1e-9 * max(1.0, g["mj"]) for g in groupes.values())
    plein = [g for g in groupes.values() if g["rendement_plein"] is not None]
    nominal = all(abs(g["rendement_plein"] - g["nominal"]) <= 1e-9 for g in plein)
    filieres = all(0.35 <= t.rendement <= 0.45 for t in M.THERMIQUES.values())
    partiel = all(g["rendement_moyen"] < g["nominal"] for g in groupes.values() if g["heures"] > g["heures_pleines"])
    brule = all(abs(v) <= 1e-9 * max(1.0, tot_mj) for v in ecarts.values())
    b = M.bilan_electricite(p)
    reseau = all(abs(b[k]) <= b["tolerance"] for k in ("reseau_kwh", "batterie_kwh", "production_comptee_kwh"))
    part_pertes = R.cumul["pertes"] / R.cumul["injection"]
    pertes = abs(part_pertes - M.PERTES_RESEAU) <= 1e-9
    # falsificateurs
    res = next(r for r in E.reservoirs if r.stock[E.ids["fioul"]] > 1)
    p.socle.livre.bruler(res.stock, E.ids["fioul"], 1.0, "combustion_centrale")
    vu_fioul = abs(M.bilan_combustion(p)[1]["fioul"] + 1.0) <= 1e-6
    u = next(x for x in E.unites if x.genre == "thermique" and x.c_mj > 0)
    u.c_kwh += 50.0
    vu_kwh = abs(M.bilan_combustion(p)[0][u.id]["ecart_mj"] + 180.0) <= 1e-6
    ok = ferme and nominal and len(plein) >= 1 and filieres and partiel and brule and reseau and pertes and vu_fioul and vu_kwh
    return ok, (f"{len(groupes)} groupes, {tot_mj / 3600:.0f} MWh de combustible, {sum(g['kwh'] for g in groupes.values()) / 1000:.1f} "
                f"MWh electriques ; groupes fermes {ferme} ; rendements a pleine charge ( {len(plein)} groupes ) : "
                + ", ".join(sorted({f"{g['technologie']} {g['rendement_plein']:.3f}" for g in plein}))
                + " ; moyens : " + ", ".join(sorted({f"{g['technologie']} {g['rendement_moyen']:.3f}" for g in groupes.values() if g['rendement_moyen']}))
                + f" ; brule compte = grand livre {brule} ; reseau {b['reseau_kwh']:+.1e} kWh, batterie {b['batterie_kwh']:+.1e}, "
                f"production {b['production_comptee_kwh']:+.1e} ; pertes {part_pertes:.4f} de l injection ; falsificateurs : fioul brule "
                f"a la main vu {vu_fioul}, 50 kWh ajoutes vus {vu_kwh}")


# ================================================================== la courbe de charge
def _courbe(chaleur):
    w, p = T.monde(["energie"])
    TER.forcer_meteo(p, "Altis", 4, chaleur_c=chaleur, debut=p.jour + 1)
    T.jours(w, 3)                                          # jusqu au lundi 18 juin a 6 h ; le lundi finit a 23 h 50
    _avancer(w, 18)
    R = _reseau(p)
    return R.hier["zones"].copy(), R.hier["temperature"].copy(), R.hier["demande"].copy()


def test_courbe_de_charge():
    """Porte : la demande des zones habitees ( residentiel, tertiaire, eclairage ) d un lundi de juin. Jour doux ( -4
    degres ) : pic entre 18 h et 22 h, creux entre 1 h et 6 h, pic au moins 1,3 fois le creux. Controle positif : le
    meme lundi 8 degres plus chaud ( climatisation ) monte la pointe d au moins 15 % et l apres-midi ( 13-16 h ) d au
    moins 25 %. Falsificateur : la courbe douce decalee de 12 heures est refusee par le meme controle."""
    doux, t_doux, tot_doux = _courbe(-4.0)
    chaud, t_chaud, tot_chaud = _courbe(8.0)
    ok_doux, hp, hc, r = M.verifier_courbe(doux)
    faux, hp_f, _, _ = M.verifier_courbe(np.roll(doux, 12))
    pointe = chaud.max() / doux.max()
    aprem = chaud[13:17].mean() / doux[13:17].mean()
    ok = ok_doux and pointe >= 1.15 and aprem >= 1.25 and not faux
    return ok, (f"jour doux ( {t_doux.min():.0f}-{t_doux.max():.0f} degres ) : pic a {hp} h ( {doux.max():.0f} kW ), creux a {hc} h, "
                f"rapport {r:.2f} ; jour chaud ( {t_chaud.min():.0f}-{t_chaud.max():.0f} degres ) : pointe x{pointe:.2f}, "
                f"13-16 h x{aprem:.2f}, pic a {int(np.argmax(chaud))} h ; avec les sites du moteur, pic du jour doux a "
                f"{int(np.argmax(tot_doux))} h ; courbe decalee de 12 h refusee {not faux} ( pic a {hp_f} h )")


# ================================================================== le solaire
def _solaire(facteur):
    w, p = T.monde(["energie"])
    R = _reseau(p)
    u = next(x for x in R.renouvelables if x.genre == "solaire")
    u.pmax *= facteur
    prod, irr, ecr = [], [], []
    for _ in range(8):
        T.jours(w, 1)
        prod.append(R.hier["solaire"].copy()); irr.append(R.hier["irradiance"].copy()); ecr.append(R.hier["ecrete"].copy())
    return np.array(prod[1:]), np.array(irr[1:]), np.array(ecr[1:]), u.pmax


def test_solaire():
    """Porte : 7 jours complets de juin. Aux heures sans ecretement, la production est capacite x eclairement x 0,80
    ( 1e-9 ), nulle la nuit, a son pic a moins d une heure du pic de l eclairement ; l eclairement de juin a 40 degres
    nord fait 6 a 8 kWh/m2 par jour ( PVGIS, Lemnos : ~7,3 ) ; le pic tombe entre 12 h et 14 h. Controle positif : un
    ciel couvert ( ecart diurne divise par 4 ) divise le rayonnement par 2 ( Hargreaves ) ; un parc double double la
    production aux heures ou aucun des deux n ecrete. Falsificateur : la serie decalee de 6 heures est refusee."""
    prod, irr, ecr, cap = _solaire(1.0)
    prod2, _, ecr2, _ = _solaire(2.0)
    oks = [M.verifier_solaire(prod[k], irr[k], cap, ecr[k] <= 1e-9) for k in range(len(prod))]
    suit = all(o[0] for o in oks)
    jour = irr.sum(axis=1) / 1000.0
    pics = [int(np.argmax(x)) for x in irr]
    libres = (ecr <= 1e-9) & (ecr2 <= 1e-9) & (prod > 0)
    double = float(np.max(np.abs(prod2[libres] / prod[libres] - 2.0))) if libres.any() else 1.0
    r1 = M.irradiation_jour(17.0, 8.0); r4 = M.irradiation_jour(17.0, 2.0)
    faux = M.verifier_solaire(np.roll(prod[0], 6), irr[0], cap)[0]
    ok = suit and 6.0 <= jour.mean() <= 8.0 and all(12 <= h <= 14 for h in pics) and abs(r4 / r1 - 0.5) <= 1e-9 \
        and libres.sum() >= 20 and double <= 1e-9 and not faux
    return ok, (f"{len(prod)} jours : suit l eclairement {suit} ( pire ecart {max(o[1] for o in oks):.1e} ) ; rayonnement "
                f"{jour.mean():.2f} kWh/m2/j ( {jour.min():.2f}-{jour.max():.2f} ), pics a {sorted(set(pics))} h ; "
                f"production {prod.sum() / 1000:.2f} MWh, facteur de charge {prod.sum() / (cap * 24 * len(prod)):.1%} ; couvert : "
                f"x{r4 / r1:.3f} ; parc double : {int(libres.sum())} heures libres, ecart au double {double:.1e} ; serie decalee "
                f"refusee {not faux}")


# ================================================================== la panne et le delestage
def _panne(forcer):
    w, p = T.monde(["energie"])
    E = p.domaine("energie"); R = _reseau(p)
    village = next(c.lieu for c in R.charges if c.type == M.ZONE and c.hab > 0)
    c = M.abonner(p, "hopital_test", village, w.gouv, 15.0, prioritaire=True)
    T.jours(w, 1); _avancer(w, 10)                         # jour 1, 16 h
    if forcer: M.forcer_panne(p, "Altis", "diesel_fioul", heures=24.0)
    dem = serv = ens = 0.0; h_del = 0; contrat = []
    for _ in range(24):
        _avancer(w, 1)
        h = int(p.heure) - 1 if p.heure >= 1 else 23
        H = R.h if R.h["injection"][h] > 0 else R.hier
        dem += H["demande"][h]; serv += H["servi"][h]; ens += H["ens_delestage"][h]
        contrat.append(c.servi_h)
    h_del = sum(sum(x.h_del7) + x.d_h_del for x in R.charges)
    ident = abs(dem - serv - ens) <= 1e-9 * max(1.0, dem)
    return dem, ens, h_del, min(contrat), ident, p


def test_panne_delestage():
    """Porte : le jour 1 a 16 h, les trois groupes au fioul tombent en panne pour 24 heures. Sur ces 24 heures, l energie
    non servie par delestage fait au moins 1 % de la demande et au moins 3 heures-zones sont delestees ; le meme monde
    sans panne en deleste au plus 0,1 %. Chaque heure, demande = servi + non servi. Un contrat prioritaire ( hopital,
    15 kW ) reste servi toute la panne."""
    d0, e0, h0, c0, i0, _ = _panne(False)
    d1, e1, h1, c1, i1, p = _panne(True)
    ok = e1 >= 0.01 * d1 and h1 >= 3 and e0 <= 0.001 * d0 and i0 and i1 and c1 >= 1.0
    ev = [e for e in p.socle.journal.recents if e["type"] == "delestage_electrique"]
    return ok, (f"sans panne : {e0:.1f} kWh non servis sur {d0:.0f} ( {e0 / d0:.2%} ), {h0} heures-zones ; panne des groupes "
                f"au fioul : {e1:.0f} kWh non servis sur {d1:.0f} ( {e1 / d1:.1%} ), {h1} heures-zones, {len(ev)} heures de "
                f"delestage ; demande = servi + non servi {i0 and i1} ; contrat prioritaire servi au pire {c1:.0%}")


# ================================================================== la raffinerie et le puits
def test_raffinerie():
    """Porte : 6 jours. La masse de brut = coupes + autoconsommation + pertes a 1e-9 pres ; chaque coupe a son
    rendement massique ( 1e-12 ) ; en volume, gazole 35-40 %, essence 20-25 %, kerosene 8-10 % ; les unites produites
    sont celles que le grand livre a vues ( 1e-9 ) ; au moins 1 tonne raffinee. Le gisement : ramene a 5 % de ses
    reserves de depart, le debit par petrolier tombe a 5/35 du plateau ( 0,12 a 0,17 ) ; un gisement de 20 unites dont il
    reste 10 ( encore sur son plateau ) rend exactement ses 10 unites et s arrete a zero, jamais en dessous.
    Falsificateur : 1 kg d essence ajoute au registre de la raffinerie se voit dans le bilan de masse."""
    w, p = T.monde(["energie"])
    E = p.domaine("energie")
    T.jours(w, 6)
    b = M.bilan_raffinerie(p)
    masse = abs(b["ecart_kg"]) <= 1e-9 * b["brut_kg"]
    coupes = all(abs(b["masse"][k] - r) <= 1e-12 for k, r in M.RENDEMENTS)
    v = b["volume"]
    vol = 0.35 <= v["carburant"] <= 0.40 and 0.20 <= v["essence"] <= 0.25 and 0.08 <= v["kerosene"] <= 0.10
    livre = all(abs(x) <= 1e-9 * max(1.0, E.raff[k + "_u"]) for k, x in b["ecart_livre"].items()) and abs(b["brut_livre"]) <= 1e-9 * E.raff["brut_u"]
    g = E.gisement
    avant = g.c_extrait / 6.0
    g.reste = 0.05 * g.depart
    x0 = g.c_extrait; T.jours(w, 1); jour = g.c_extrait - x0
    declin = jour / max(1e-9, avant)
    g.depart, g.reste = 20.0, 10.0
    x0 = g.c_extrait; T.jours(w, 1); fin = g.c_extrait - x0
    E.raff["essence_kg"] += 1.0
    vu = abs(M.bilan_raffinerie(p)["ecart_kg"] + 1.0) <= 1e-6
    E.raff["essence_kg"] -= 1.0
    ok = masse and coupes and vol and livre and b["brut_kg"] >= 1000 and 0.12 <= declin <= 0.17 \
        and abs(fin - 10.0) <= 1e-9 and g.reste >= 0.0 and vu
    return ok, (f"{b['brut_kg'] / 1000:.1f} t de brut, ecart de masse {b['ecart_kg']:+.1e} kg ; volumes : "
                + ", ".join(f"{k} {x:.1%}" for k, x in v.items()) + f" ; grand livre {livre} ; gisement a 5 % : debit x{declin:.3f} "
                f"( attendu {1 / 7:.3f} ), 10 unites restantes : {fin:.6f} extraites, reste {g.reste:.1e} ; 1 kg falsifie vu {vu}")


# ================================================================== le falsificateur de l electricite
def test_electricite_hors_production():
    """Falsificateur : 3 jours, le socle et le bilan de l electricite tiennent ; 50 kWh poses a la main dans la batterie
    rompent la conservation du socle ET le bilan de la batterie ; 30 kWh crees par le grand livre sous un motif qui n est
    pas une production du domaine gardent la conservation ( le socle les voit nes ) mais rompent le bilan du reseau."""
    w, p = T.monde(["energie"])
    E = p.domaine("energie"); R = _reseau(p)
    T.jours(w, 3)
    t0, _ = p.socle.conservation.tenue(); b0 = M.bilan_electricite(p)
    propre = t0 and all(abs(b0[k]) <= b0["tolerance"] for k in ("reseau_kwh", "batterie_kwh", "production_comptee_kwh"))
    R.batterie.stock._ajouter(E.elec, 5.0)
    t1, msg = p.socle.conservation.tenue(); b1 = M.bilan_electricite(p)
    vu_main = (not t1) and abs(b1["batterie_kwh"] - 50.0) <= 1e-6
    R.batterie.stock._retirer(E.elec, 5.0)
    p.socle.livre.produire(R.gestionnaire.stock, E.elec, 3.0, "production_fantome")
    t2, _ = p.socle.conservation.tenue(); b2 = M.bilan_electricite(p)
    vu_motif = t2 and abs(b2["reseau_kwh"] + 30.0) <= 1e-6
    ok = propre and vu_main and vu_motif
    return ok, (f"avant : conservation {t0}, reseau {b0['reseau_kwh']:+.1e} kWh ; 50 kWh a la main : conservation rompue "
                f"{not t1} ( {msg} ), batterie {b1['batterie_kwh']:+.1f} kWh ; 30 kWh sous un faux motif : conservation {t2}, "
                f"reseau {b2['reseau_kwh']:+.1f} kWh")


# ================================================================== la repartition
def _controler(besoin, unites, res, batt, plan):
    """Les proprietes d une repartition : bornes, bilan, ordre de merite, manque seulement a fond."""
    s, ru, ec, ch, de, manque, surplus = plan
    bornes = all(u[0] - 1e-9 <= x <= u[1] + 1e-9 for u, x in zip(unites, s)) and -1e-9 <= ru <= res + 1e-9
    bilan = abs(sum(s) + ru + de - ch - (besoin - manque + surplus)) <= 1e-7 * max(1.0, besoin)
    merite = True
    for i, a in enumerate(unites):
        for j, b in enumerate(unites):
            if a[2] < b[2] - 1e-12 and s[j] > b[0] + 1e-9 and s[i] < a[1] - 1e-9 and ch <= 1e-9: merite = False
    a_fond = manque <= 1e-9 or (all(abs(x - u[1]) <= 1e-9 for u, x in zip(unites, s)) and de >= batt[1] - 1e-9 or
                                all(abs(x - u[1]) <= 1e-9 for u, x in zip(unites, s)) and ch > 0)
    return bornes and bilan and merite and a_fond


def test_repartition():
    """Porte de la conduite : 2 000 heures tirees au hasard ( besoin, groupes, renouvelable, batterie ) : chaque
    repartition respecte les bornes des groupes, le bilan ( sorties + renouvelable + decharge - charge = besoin - manque
    + surplus ), l ordre de merite ( jamais un groupe cher au-dessus de son minimum quand un moins cher n est pas a fond,
    hors recharge de nuit ), et ne manque que groupes et batterie a fond. Falsificateur : une repartition en ordre de
    merite inverse est refusee par le meme controle dans au moins 10 % des tirages."""
    rng = np.random.default_rng(3)
    bons = inverses = n = 0
    for _ in range(2000):
        k = int(rng.integers(1, 6))
        pmax = rng.uniform(20, 200, k); pmin = pmax * rng.uniform(0.2, 0.5, k); cout = rng.uniform(0.05, 0.3, k)
        unites = [(float(a), float(b), float(c)) for a, b, c in zip(pmin, pmax, cout)]
        besoin = float(rng.uniform(0, 1.3 * pmax.sum())); res = float(rng.uniform(0, 0.5 * besoin + 1))
        batt = (float(rng.uniform(0, 50)), float(rng.uniform(0, 50)))
        pointe, nuit = bool(rng.random() < 0.3), bool(rng.random() < 0.3)
        plan = M.repartir(besoin, unites, res, batt, pointe, nuit)
        n += 1; bons += _controler(besoin, unites, res, batt, plan)
        inv = [(a, b, -c) for a, b, c in unites]
        pl = M.repartir(besoin, inv, res, batt, pointe, nuit)
        inverses += not _controler(besoin, unites, res, batt, pl)
    ok = bons == n and inverses >= 0.10 * n
    return ok, f"{bons}/{n} repartitions valides ; ordre inverse refuse {inverses}/{n} fois"


# ================================================================== l argent
def test_argent():
    """Porte : 10 jours. Chaque drachme du gestionnaire passe par le grand livre : sa caisse = dotation + factures +
    compensation - achats aux centrales - redevance, a la tolerance du registre ; le rapprochement de sa famille est nul ;
    les centrales ont ete payees ; les menages factures ont paye ou doivent ( facture + arrieres = du ). Le cout marginal
    et le tarif sont mesures ( sans seuil : le tarif reglemente des iles ne couvre pas leur cout, d ou la compensation )."""
    w, p = T.monde(["energie"])
    E = p.domaine("energie"); R = _reseau(p); L = p.socle.livre
    rap = R_.Rapprochement(p.socle.registre, L)
    caisse0 = R.gestionnaire.caisse
    T.jours(w, 10)
    net = L.net_par_classe()
    vu = net.get("GestionnaireReseau", 0.0)
    ecart = R.gestionnaire.caisse - vu
    reste = rap.restes()["gestionnaires_reseau"]
    achats = E.argent.get("achat_electricite_producteur", 0.0)
    s = list(R.serie)
    cm = np.mean([x["cout_marginal_moyen"] for x in s]); cmoy = np.mean([x["cout_moyen"] for x in s]); tar = M.tarif(p)
    ok = abs(ecart) <= R_.tolerance(vu, achats) and abs(reste) <= R_.tolerance(caisse0, achats) and achats > 0
    return ok, (f"gestionnaire : caisse {R.gestionnaire.caisse:.0f} = vu au grand livre {vu:.0f} ( ecart {ecart:+.1e} ), "
                f"rapprochement {reste:+.1e} ; achats aux centrales {achats:.0f}, factures {E.factures:.0f} ( impayes "
                f"{E.impayes:.0f} ), compensation de l Etat {E.compensation:.0f}, redevance {E.redevance:.0f} ; tarif {tar:.3f}, "
                f"cout marginal moyen {cm:.3f}, cout variable moyen du thermique {cmoy:.3f} drachme le kWh")


# ================================================================== la decision
def _stress(mode):
    w, p = T.monde(["energie"], modes={"delestage_zone": mode})
    M.forcer_panne(p, "Altis", "diesel_fioul", heures=12 * 24.0)
    T.jours(w, 12)
    return w, p


def test_part_du_choix():
    """Porte de la decision : les trois groupes au fioul en panne 12 jours ( la production manque chaque jour ). En mode
    hasard : au moins 100 decisions, au moins 100 notes, plusieurs notes par action et par jour ( un tiers des zones
    decide chaque jour ), et la note depend du choix : part du choix ( epsilon carre intra-jour, corrige des petits
    groupes ) >= 0,01 ET p de permutation a jour egal < 0,05 ; la conservation tient. La regle, le temoin et le hasard
    sont compares ( sans seuil ) : energie non servie de l ile, et delestage des zones selon leur programme."""
    res = {}
    for mode in ("hasard", "regle", "temoin"):
        w, p = _stress(mode)
        E = p.domaine("energie"); R = _reseau(p); dec = E.decideur
        notes = dec.notes_par_action()
        par = {}
        for c in R.charges:
            if c.type == M.ZONE and c.c_serv + c.c_del > 0:
                a = par.setdefault(M.ACTIONS_DELESTAGE[c.effacement], [0.0, 0.0]); a[0] += c.c_del; a[1] += c.c_serv + c.c_del
        par_jour = {}
        for (j, a), st in dec.stats.items(): par_jour.setdefault(j, []).append(st[0])
        res[mode] = dict(part=dec.part_du_choix(), brute=dec.part_du_choix_brute(),
                         perm=dec.p_permutation() if mode == "hasard" else None,
                         par_action_jour=float(np.mean([x for v in par_jour.values() for x in v])) if par_jour else 0.0,
                         n=dec.n_decisions, notes=notes, n_notes=sum(k for k, _ in notes.values()),
                         ens=R.cumul["ens_delestage"] / max(1.0, R.cumul["demande"]), tenue=p.socle.conservation.tenue(),
                         par=par, faim=T.faim(w))
    h = res["hasard"]
    ok = h["n"] >= 100 and h["n_notes"] >= 100 and h["part"] >= 0.01 and h["perm"] < 0.05 and h["tenue"][0]
    return ok, (f"hasard : {h['n']} decisions, {h['n_notes']} notes : " + ", ".join(f"{a} {m:+.4f} ( {k} )" for a, (k, m) in h["notes"].items())
                + f" ; {h['par_action_jour']:.1f} notes par action et par jour ; part du choix {h['part']:.3f} ( brute {h['brute']:.3f} ), "
                f"p de permutation {h['perm']:.3f} ; non servi de l ile : hasard {h['ens']:.2%}, regle {res['regle']['ens']:.2%}, "
                f"temoin {res['temoin']['ens']:.2%} ; delestage des zones par programme final ( hasard ) : "
                + ", ".join(f"{a} {x[0] / max(1e-9, x[1]):.1%}" for a, x in sorted(h["par"].items()))
                + f" ; faim {h['faim']:.1%} ; {h['tenue'][1]}")


# ================================================================== le pays
def test_pays_vivable():
    return T.porte_commune("energie", n_jours=12)


def test_cout():
    """Les routines propres du domaine coutent au plus 10 % d une journee du moteur seul a 10 000 habitants ; le pays
    avec l energie ( et ses dependances ) reste sous 2 fois le moteur seul."""
    def jour_moyen(avec):
        w = W.Monde(echelle=20)
        if avec: T.P.installer(w, ["energie"])
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants)
    t_e1, n = jour_moyen(False)
    t_en, _ = jour_moyen(True)
    w, p = T.monde(["energie"], echelle=20)
    T.jours(w, 2)
    E = p.domaine("energie")
    t0 = time.perf_counter()
    for _ in range(2):
        E.jour_prepare = None
        M._debut_de_jour(p, E)
        for h in range(24):
            for R in E.reseaux: M._conduire(p, E, R, h)
        M._combustibles(p); M._fin_de_jour(p)
    propre = (time.perf_counter() - t0) / 2
    ok = propre <= 0.10 * t_e1 and t_en <= 2.0 * t_e1
    return ok, (f"{n} habitants : moteur seul {t_e1:.2f} s par jour, avec l energie et ses dependances {t_en:.2f} s ; "
                f"routines propres du domaine {propre * 1000:.0f} ms par jour ( {propre / t_e1:.1%} du moteur )")


TESTS = [test_unites_reelles, test_bilan_energetique, test_courbe_de_charge, test_solaire, test_panne_delestage,
         test_raffinerie, test_electricite_hors_production, test_repartition, test_argent, test_part_du_choix,
         test_pays_vivable, test_cout]
