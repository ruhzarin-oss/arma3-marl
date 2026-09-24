"""Les portes du domaine 10 ( industrie et extraction ). Seuils ecrits avant la premiere mesure.
python -m monde.pays.tests industrie"""
import math, time
import numpy as np
from .. import config as C, monde as W
from ..socle import objets as O
from . import essais as T, d01_population as POP, d02_banques as BQ, d10_industrie as M


def _site(p, id_):
    return p.domaine("industrie").par_entreprise[id_]


def _atelier(p, id_, nom):
    return next(a for a in _site(p, id_).ateliers if a.nom == nom)


# ================================================================== les recettes et les gisements
def test_bilan_matiere():
    """Porte : chaque recette ferme son bilan matiere ( entrees = sorties + pertes declarees, a 0,1 % ) et son bilan du
    fer ( a 0,1 % ) ; chaque gisement rend moins de produit que de minerai. Realisme ( sources de la recette ) : ciment
    0,6 a 0,95 t de CO2 par t, 3,5 GJ de lignite par t de clinker ( a 1 % ) ; four a fonte 2 000 a 2 600 kWh/t ; laitier
    de 0,3 a 1,0 t par t de fonte, 0,08 a 0,2 t par t d acier ; acier : 55 a 65 Nm3 d oxygene. Puis, dans le monde,
    20 jours : chaque gisement a donne, chaque recette placee a tourne - ou bien son cout variable depasse la valeur de
    son produit au tarif du reseau ( elle est a l arret pour cette raison, et pour elle seule ) - et l audit ( ce que
    les recettes impliquent = ce que le grand livre a vu ) tient a 1e-9 pres. Controle positif du cout : 10 jours avec
    une electricite a 0,03 drachme le kWh ( hydraulique ) : le four a fonte electrique tourne."""
    pires = []
    for r in M.RECETTES.values():
        (e, s), (fi, fo) = M.bilan_recette(r)
        pires.append((abs(e - s) / e, r.nom, "masse"))
        if fi > 0: pires.append((abs(fi - fo) / fi, r.nom, "fer"))
    pire = max(pires)
    rc, rf = M.RECETTES["ciment"], M.RECETTES["fonte_electrique"]
    co2 = rc.pertes["co2_decarbonatation"] + rc.pertes["co2_combustion"]
    gj_clinker = rc.entrees["charbon"] * M.CHARBON_PCI_MJ_KG / 0.80
    kwh_fonte = rf.entrees["electricite"] * M.KWH_PAR_UNITE_ELEC
    o2 = M.RECETTES["acier_convertisseur"].libres["oxygene"] * 1000 / 1.429      # Nm3 ( 1,429 kg par Nm3 d O2 )
    laitiers = [M.RECETTES[n].pertes["laitier"] for n in ("fonte_electrique", "fonte_bas_fourneau")]
    lait_acier = M.RECETTES["acier_convertisseur"].pertes["laitier"]
    gis = max(sum(r * M.MASSE_T[b] for b, r in M.Gisement(k, *g).rendements.items()) for k, g in M.GISEMENTS.items())
    donnees = (pire[0] <= 1e-3 and 0.6 <= co2 <= 0.95 and abs(gj_clinker / 3.5 - 1) <= 0.01 and 2000 <= kwh_fonte <= 2600
               and all(0.3 <= x <= 1.0 for x in laitiers) and 0.08 <= lait_acier <= 0.2 and 55 <= o2 <= 65 and gis < 1.0)
    w, p = T.monde(["industrie"])
    T.jours(w, 20)
    ats = [a for s in p.domaine("industrie").sites for a in s.ateliers]
    places = {}
    for a in ats:
        if a.recette is not None: places[a.recette.nom] = places.get(a.recette.nom, 0.0) + a.cumul_passes
    a_perte = sorted({a.recette.nom for a in ats if a.recette is not None and a.cumul_passes <= 0
                      and M.cout_variable(p, a) > M.valeur_directeur(p, a) and a.regime == 0.0})
    gisements = {f"{a.site.id}:{a.nom}": a.cumul_minerai for a in ats if a.gisement is not None}
    tourne = (all(v > 0 or k in a_perte for k, v in places.items()) and all(v > 0 for v in gisements.values()))
    ecart, qui = M.ecart_audit(p)
    tenue, msg = p.socle.conservation.tenue()
    w2, p2 = T.monde(["industrie"])
    p2.routine(6 + 10 / 60, 99, "porte", _electricite_hydraulique)
    T.jours(w2, 10)
    hydro = sum(a.cumul_passes for s in p2.domaine("industrie").sites for a in s.ateliers
                if a.recette is not None and a.recette.nom == "fonte_electrique")
    ok = donnees and tourne and ecart <= 1e-9 and tenue and hydro > 0 and M.ecart_audit(p2)[0] <= 1e-9
    return ok, (f"pire bilan de recette {pire[0]:.1e} ( {pire[1]}, {pire[2]} ) ; ciment {co2:.3f} t CO2/t, clinker "
                f"{gj_clinker:.2f} GJ/t ; four a fonte {kwh_fonte:.0f} kWh/t ; laitier fonte {laitiers[0]:.2f} et {laitiers[1]:.2f}, "
                f"acier {lait_acier:.3f} ; O2 {o2:.0f} Nm3/t ; gisement le plus riche {gis:.2f} t de produit par t ; 20 jours : "
                + ", ".join(f"{k} {v:.1f}" for k, v in sorted(places.items())) + f" ; a l arret parce qu a perte : {a_perte} ; "
                f"gisements tous > 0 : {all(v > 0 for v in gisements.values())} ; audit {ecart:.1e} ( {qui} ) ; {msg} ; "
                f"electricite hydraulique, 10 jours : fonte electrique {hydro:.1f} t")


def _electricite_hydraulique(p):
    """6 h 10 ( porte ) : apres le tarif de l aube du moteur, 0,3 drachme les 10 kWh."""
    p.w.reseau.tarif = 0.3


def _epuiser(tonnes):
    w, p = T.monde(["industrie"])
    g = M.forcer_reserve(p, "mine@Mine01", "skarn", tonnes)
    h0 = g.minerai_h()
    for _ in range(40):
        T.jours(w, 1)
        if g.epuise_j >= 0: break
    fin = g.epuise_j
    extrait = g.extrait_t
    T.jours(w, 2)
    return w, p, g, h0, fin, extrait


def test_epuisement():
    """Porte : la mine d or ( qui tourne toujours plein ) sur un gisement neuf de 120 t : il s epuise, le minerai extrait
    vaut la reserve a 1e-9 pres, plus rien n est extrait apres, l evenement est note, et le minerai par heure a la fin
    est 0,6 fois celui du debut ( decouverture de 0,2 a 1,0 ). Controle positif : 240 t durent de 1,7 a 2,3 fois plus
    longtemps ( la duree suit la reserve )."""
    w, p, g, h0, fin, extrait = _epuiser(120.0)
    h1 = g.type.materiel_t_h / (1.0 + g.decouverture())
    apres = g.extrait_t - extrait
    note = any(e["type"] == "gisement_epuise" for e in p.socle.journal.derniers("gisement_epuise"))
    w2, p2, g2, _, fin2, _ = _epuiser(240.0)
    j1, j2 = fin + 1, fin2 + 1                         # jours ( l installation tombe le jour 0 a 6 h )
    ok = (fin >= 0 and abs(extrait - 120.0) <= 1e-9 and g.reserve_t == 0.0 and apres == 0.0 and note
          and abs(h1 / h0 - 1.2 / 2.0) <= 1e-9 and fin2 >= 0 and 1.7 <= j2 / j1 <= 2.3)
    return ok, (f"120 t epuisees le jour {fin} ( extrait {extrait:.9f} t, reserve {g.reserve_t}, apres l epuisement "
                f"{apres} t, evenement note {note} ) ; minerai par heure {h0:.3f} -> {h1:.3f} t ( x{h1 / h0:.2f} ) ; 240 t : "
                f"epuisees le jour {fin2}, duree x{j2 / j1:.2f}")


# ================================================================== les machines
def test_mtbf():
    """Porte : 1 500 machines de trois modeles, sans entretien, reparees a chaque panne, 4 pannes chacune, au pas du
    monde et par la loi du monde : le MTBF simule retrouve le MTBF declare a 2 % pres. Controles positifs : un MTBF
    declare deux fois plus court donne un MTBF simule de 0,48 a 0,52 fois ; une usure de vie de 0,5 le divise par
    1,5^( 1 / beta ) ( a 2 % pres ). Dans le monde ( 2 000 habitants, temoin : jamais d entretien, 30 jours, au moins 5
    pannes ) : les pannes tirees s ecartent de la somme des hasards de moins de 3 ecarts-types."""
    rng = np.random.default_rng(7)
    res = {}
    for nom in ("foreuse_jumbo", "chargeuse_souterraine", "pelle_hydraulique"):
        f = M.FIABILITE[nom]
        res[nom] = float(M.simuler_flotte(f, 1500, 4, rng).mean()) / f.mtbf_h
    f = M.FIABILITE["chargeuse_souterraine"]
    moitie = M.ModeleMachine("moitie", f.mtbf_h / 2, f.beta, f.mttr_h, f.pm_h, f.pm_duree_h)
    r_moitie = float(M.simuler_flotte(moitie, 1500, 4, rng).mean()) / f.mtbf_h
    r_use = float(M.simuler_flotte(f, 1500, 4, rng, usure=0.5).mean()) / f.mtbf_h
    attendu_use = 1.5 ** (-1.0 / f.beta)
    w, p = T.monde(["industrie"], echelle=4, modes={"entretenir_machine": "temoin"})
    T.jours(w, 30)
    st = p.domaine("industrie").stats
    z = (st["pannes"] - st["pannes_attendues"]) / math.sqrt(max(1e-9, st["pannes_attendues"]))
    ok = (all(abs(r - 1) <= 0.02 for r in res.values()) and 0.48 <= r_moitie <= 0.52 and abs(r_use / attendu_use - 1) <= 0.02
          and abs(z) <= 3.0 and st["pannes"] >= 5)
    return ok, (", ".join(f"{k} x{v:.3f}" for k, v in res.items()) + f" du MTBF declare ; MTBF divise par 2 : x{r_moitie:.3f} ; "
                f"usure 0,5 : x{r_use:.3f} pour x{attendu_use:.3f} ; monde temoin 30 jours : {st['pannes']:.0f} pannes pour "
                f"{st['pannes_attendues']:.1f} attendues ( z = {z:+.2f} )")


def test_conservation_machines():
    """Porte : 15 jours a la mine. Trois machines remplacees par `remplacer` : la premiere fabriquee au pays ( acier et
    pieces poses a la fonderie la plus proche, un apport paie ), la deuxieme importee ( un apport paie ), la troisieme
    non remplacee ( caisse vide, credit refuse ) ; une quatrieme usee jusqu a la corde ( usure 0,9999 ) part d elle-meme
    au rebut le soir. Chaque modele : exemplaires = sources - puits ( Parc.verifier nul partout ), conservation du socle
    tenue, audit tenu. Falsificateur : un objet efface a la main se voit ( verifier -1, conservation rompue )."""
    w, p = T.monde(["industrie"])
    D_ = p.domaine("industrie"); parc = p.socle.parc; L = p.socle.livre; cat = p.socle.catalogue
    s = _site(p, "mine@Mine01"); a = s.ateliers[0]; e = s.entreprise
    L.declarer_motif("porte_essai", "transfert_capital", "industrie")
    ordre = sorted(a.machines, key=lambda x: (parc.modeles[x.objet.modele].nom != "chargeuse_souterraine", x.objet.id))
    mod = parc.modeles[ordre[0].objet.modele]
    f = min((x for x in D_.sites if x.type == "fonderie"), key=lambda x: (x.lieu.distance(s.lieu), x.id))
    L.produire(f.stock, cat.id("acier"), M.PART_ACIER_MACHINE * mod.masse_kg / 1000.0, "porte_essai")
    L.produire(f.stock, cat.id("pieces"), M.PART_PIECES_MACHINE * mod.masse_kg / 1000.0, "porte_essai")
    avant = {m.nom: parc.nombre(m.nom) for m in parc.modeles}
    issues = []
    for k, m in enumerate(ordre[:3]):
        prix = parc.modeles[m.objet.modele].prix_monde
        if k < 2:
            L.recevoir_de_l_exterieur(e, prix, "porte_essai")
            issues.append(M.remplacer(p, m))
        else:
            L.payer_l_exterieur(e, e.caisse, "porte_essai")
            ancien = BQ.demander_credit; BQ.demander_credit = _refuser_credit
            try: issues.append(M.remplacer(p, m))
            finally: BQ.demander_credit = ancien
            L.recevoir_de_l_exterieur(e, 20000.0, "porte_essai")      # la mine repart : gazole et salaires
    quatrieme = next(m for m in a.machines if m.objet.etat == O.SERVICE)
    quatrieme.objet.usure = 0.9999
    T.jours(w, 15)
    naturel = [r for r in D_.remplacements if r[0] >= 0][3:]
    ecarts = parc.verifier()
    comptes_ok = all(v == 0 for v in ecarts.values())
    tenue, msg = p.socle.conservation.tenue()
    ecart, _ = M.ecart_audit(p)
    apres = {m.nom: parc.nombre(m.nom) for m in parc.modeles}
    victime = next(iter(parc.objets.values()))
    del parc.objets[victime.id]
    vu = parc.verifier()[parc.modeles[victime.modele].nom] == -1 and not p.socle.conservation.tenue()[0]
    parc.objets[victime.id] = victime
    ok = (issues == ["fabriquee", "importee", "non_remplacee"] and len(naturel) >= 1 and comptes_ok and tenue
          and ecart <= 1e-9 and vu and D_.stats["machines_rebut"] >= 4)
    delta = {k: apres[k] - avant[k] for k in apres if apres[k] != avant[k]}
    return ok, (f"remplacements {issues}, puis en fin de vie {[r[3] for r in naturel]} ; rebuts {D_.stats['machines_rebut']:.0f} ; "
                f"exemplaires changes {delta} ; Parc.verifier nul {comptes_ok} ; {msg} ; audit {ecart:.1e} ; objet efface "
                f"a la main vu {vu}")


def _refuser_credit(p, emprunteur, montant, type_="conso", motif="projet", duree=None): return None


# ================================================================== les accidents
def test_accidents():
    """Porte : le taux simule est celui d ESAW. ( 1 ) Loi : 10 000 000 d heures par secteur tirees par `tirer_accidents`,
    plus les pannes ( part PART_PANNES ) : non mortels a 3 ecarts-types du taux reel, mortels aussi sur 1e10 heures ;
    controle positif : un facteur 2 donne 1,8 a 2,2 fois plus. ( 2 ) Monde, facteur de risque 1 000 ( pour voir quelque
    chose en 15 jours a 2 000 habitants ) : les accidents tires s ecartent de leurs intensites de moins de 3 ecarts-types, et
    le taux attendu par heure travaillee, ramene au facteur, est de 0,86 a 1,15 fois celui d ESAW ( 0,85 vient de
    l heure travaillee ; les pannes reelles doivent en porter au moins un quinzieme de leur part ). ( 3 ) Un accident mortel passe par la population : le mort
    a la cause accident."""
    rng = np.random.default_rng(3)
    lignes, ok1 = [], True
    for sec in ("B", "C24"):
        nf, mo = M.TAUX_H[sec]
        h = 1e7
        k_nf = sum(M.tirer_accidents(rng, h / 1000, sec)[0] for _ in range(1000))
        k_nf += int(rng.poisson(nf * M.PART_PANNES * h))          # la part des pannes, tiree a son intensite
        z = (k_nf - nf * h) / math.sqrt(nf * h)
        k_m = M.tirer_accidents(rng, 1e10, sec)[1] + int(rng.poisson(mo * M.PART_PANNES * 1e10))
        zm = (k_m - mo * 1e10) / math.sqrt(mo * 1e10)
        r2 = M.tirer_accidents(rng, 1e9, sec, 2.0)[0] / M.tirer_accidents(rng, 1e9, sec, 1.0)[0]
        ok1 = ok1 and abs(z) <= 3 and abs(zm) <= 3 and 1.8 <= r2 <= 2.2
        lignes.append(f"{sec} : {k_nf} non mortels pour {nf * h:.0f} ( z {z:+.2f} ), {k_m} mortels pour {mo * 1e10:.0f} "
                      f"( z {zm:+.2f} ), facteur 2 : x{r2:.2f}")
    w, p = T.monde(["industrie"], echelle=4)
    D_ = p.domaine("industrie"); D_.facteur_risque = 1000.0
    T.jours(w, 15)
    par, (att_nf, att_m) = M.accidents(p)
    obs_nf = sum(v[1] for v in par.values()); obs_m = sum(v[2] for v in par.values())
    z_monde = (obs_nf - att_nf) / math.sqrt(max(1e-9, att_nf))
    heures = sum(v[0] for v in par.values())
    cible = sum(M.TAUX_H[k][0] * v[0] for k, v in par.items()) * 1000.0
    ok2 = abs(z_monde) <= 3 and 0.86 <= att_nf / cible <= 1.15 and obs_nf >= 10
    h = next(x for x in w.habitants if x.vivant and x.role == "mineur")
    s = _site(p, "mine@Mine01")
    v0 = sum(1 for x in w.habitants if x.vivant)
    M._accident(p, D_, s, s.ateliers[0], h, True)
    mort = (not h.vivant and POP.CAUSES[int(p.col("habitant", "cause_deces")[h.id])] == "accident"
            and sum(1 for x in w.habitants if x.vivant) == v0 - 1)
    tenue, msg = p.socle.conservation.tenue()
    ok = ok1 and ok2 and mort and tenue
    return ok, (" ; ".join(lignes) + f" ; monde x1000, 15 jours, {heures:.0f} heures : {obs_nf} non mortels pour {att_nf:.1f} "
                f"tires ( z {z_monde:+.2f} ), {obs_m} mortels pour {att_m:.2f} ; attendu / ESAW x{att_nf / cible:.3f} ; "
                f"blesses {D_.stats['blesses']:.0f} ( {D_.stats['jours_perdus']:.0f} jours perdus ) ; mort par la population "
                f"avec sa cause {mort} ; {msg}")


# ================================================================== le falsificateur
def test_bien_hors_recette():
    """Falsificateur : apres 5 jours l audit tient ; ( 1 ) 5 t d acier produites par le grand livre sous le motif de
    production du domaine mais hors de toute recette : la conservation du socle ne voit rien ( la source est declaree ),
    l audit voit 5 t d acier ; ( 2 ) 3 t de ciment ajoutees a un stock sans le grand livre : la conservation les voit ;
    ( 3 ) 2 outils ajoutes au stock du moteur d une fonderie : la conservation les voit. Chaque erreur est retiree apres."""
    w, p = T.monde(["industrie"])
    T.jours(w, 5)
    L = p.socle.livre; cat = p.socle.catalogue
    avant, _ = M.ecart_audit(p)
    s = _site(p, "fonderie@factory04")
    L.produire(s.stock, cat.id("acier"), 5.0, M.MOTIF_PRODUCTION)
    a = M.audit(p)[("produit", "acier")]
    vu1 = abs((a[1] - a[0]) - 5.0) <= 1e-9 and p.socle.conservation.tenue()[0]
    L.declarer_motif("porte_retrait", "transfert_capital", "industrie")
    L.consommer(s.stock, cat.id("acier"), 5.0, "porte_retrait")
    q = _site(p, "carriere@quarry01")
    q.stock._ajouter(cat.id("ciment"), 3.0)
    d_b = p.socle.conservation.ecarts()[1]
    vu2 = abs(d_b["ciment"] - 3.0) <= 1e-9
    q.stock._retirer(cat.id("ciment"), 3.0)
    s.entreprise.stocks["outils"] += 2.0
    vu3 = abs(p.socle.conservation.ecarts()[1]["outils"] - 2.0) <= 1e-9
    s.entreprise.stocks["outils"] -= 2.0
    tenue, msg = p.socle.conservation.tenue()
    ok = avant <= 1e-9 and vu1 and vu2 and vu3 and tenue
    return ok, (f"audit avant {avant:.1e} ; acier hors recette sous le motif du domaine : ecart de l audit "
                f"{a[1] - a[0]:+.3f} t, conservation muette {vu1} ; ciment hors grand livre vu {vu2} ; outils hors grand livre "
                f"vus {vu3} ; apres retrait {msg}")


# ================================================================== la decision
def _entretien(mode, jours=45):
    w, p = T.monde(["industrie"], modes={"entretenir_machine": mode})
    T.jours(w, jours)
    D_ = p.domaine("industrie"); dec = D_.decideur
    notes = dec.notes_par_action()
    n = sum(k for k, _ in notes.values())
    return dict(dec=dec, notes=notes, n=n, moy=sum(k * v for k, v in notes.values()) / max(1, n),
                pannes=D_.stats["pannes"], entretiens=D_.stats["entretiens"], tenue=p.socle.conservation.tenue(), jours=jours)


def test_part_du_choix():
    """Porte de la decision : 45 jours, chaque machine en service d un atelier qui tourne decide chaque matin, au hasard :
    au moins 20 decisions par jour et 200 notes murees ( horizon 30 jours ), la note depend du choix
    ( part_du_choix >= 0,01, epsilon carre a jour egal ) et le hasard permute a jour egal ne fait pas aussi bien
    ( p_permutation < 0,05 ) ; conservation tenue. La regle et le temoin sont compares ( sans seuil )."""
    r = {m: _entretien(m) for m in ("hasard", "regle", "temoin")}
    h = r["hasard"]; dec = h["dec"]
    part, pp = dec.part_du_choix(), dec.p_permutation()
    ok = dec.n_decisions >= 20 * h["jours"] and h["n"] >= 200 and part >= 0.01 and pp < 0.05 and h["tenue"][0]
    return ok, (f"{dec.n_decisions} decisions, {h['n']} notes : " + ", ".join(f"{a} {m:.3f} ( {k} )" for a, (k, m) in h["notes"].items())
                + f" ; part du choix {part:.3f} ( brute {dec.part_du_choix_brute():.3f} ), p permutation {pp:.3f} ; note "
                f"moyenne : hasard {h['moy']:.3f}, regle {r['regle']['moy']:.3f}, temoin {r['temoin']['moy']:.3f} ; pannes : "
                f"hasard {h['pannes']:.0f}, regle {r['regle']['pannes']:.0f}, temoin {r['temoin']['pannes']:.0f} ; entretiens : "
                f"{h['entretiens']:.0f}, {r['regle']['entretiens']:.0f}, {r['temoin']['entretiens']:.0f} ; {h['tenue'][1]}")


# ================================================================== le pays
def test_pays_vivable():
    return T.porte_commune("industrie", n_jours=12)


class _Chrono:
    __slots__ = ("f", "t")

    def __init__(self, f): self.f, self.t = f, 0.0

    def __call__(self, p):
        t0 = time.perf_counter(); self.f(p); self.t += time.perf_counter() - t0


def test_cout():
    """Les routines propres du domaine coutent au plus 15 % d une journee du moteur seul, a 10 000 habitants ( mesurees
    en vrai sur deux jours, chaque routine chronometree )."""
    def jour_moyen():
        w = W.Monde(echelle=20)
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants)
    t_e1, n = jour_moyen()
    w, p = T.monde(["industrie"], echelle=20)
    T.jours(w, 1)
    chronos = []
    for minute, lst in p.routines.items():
        for k, (o, dom, f) in enumerate(lst):
            if dom == "industrie":
                c = _Chrono(f); lst[k] = (o, dom, c); chronos.append(c)
    t0 = time.perf_counter(); T.jours(w, 2); t_pays = (time.perf_counter() - t0) / 2
    propre = sum(c.t for c in chronos) / 2
    machines = len(p.domaine("industrie").machines)
    ok = propre <= 0.15 * t_e1
    return ok, (f"{n} habitants, {machines} machines : moteur seul {t_e1:.2f} s par jour, pays avec l industrie et ses "
                f"dependances {t_pays:.2f} s ; routines propres du domaine {propre * 1000:.0f} ms par jour ( {propre / t_e1:.1%} "
                f"du moteur )")


TESTS = [test_bilan_matiere, test_epuisement, test_mtbf, test_conservation_machines, test_accidents, test_bien_hors_recette,
         test_part_du_choix, test_pays_vivable, test_cout]
