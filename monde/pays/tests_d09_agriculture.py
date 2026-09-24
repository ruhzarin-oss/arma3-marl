"""Les portes du domaine 9 ( agriculture ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests agriculture

Deux portes vivent une annee entiere ( rendements d une campagne, pays nourri ) et une cinq mois ( le temoin ). Le monde
E1 muni de l economie NE VIT PAS une annee : sans l agriculture comme avec, la raffinerie fait faillite ( 5 unites de
petrole a 5 drachmes et 8 drachmes de salaire pour 4 unites de carburant revendues 9 x 0,75 : elle perd ~7 drachmes par
heure d ouvrier ), le carburant manque aux marches vers le jour 110, plus aucun camion ne part, et la faim monte a 100 %
vers le jour 130 ( mesure du 23/09, territoire + economie seuls ). Ces portes posent donc un ECHAFAUDAGE declare : une aide
exterieure en carburant qui tient 300 unites a chaque marche ( un don : source « importe » ). Il isole l agriculture
d une faillite qui n est pas la sienne ; il ne nourrit personne."""
import math, pickle, time
import numpy as np
from .. import monde as W, config as C
from . import essais as T, d09_agriculture as M, d08_territoire as TER

JOURS_ANNEE = 372            # du 15 juin a la moisson suivante : toutes les campagnes de l annee se ferment


def _aide_carburant(w, p, plancher=300.0):
    """L echafaudage des portes longues ( voir la docstring du module )."""
    L = p.socle.livre
    for m in w.marches.values():
        q = plancher - m.stocks["carburant"]
        if q > 0: m.stocks["carburant"] += q; L.flux["importe"]["carburant"] += q


def _vivre(w, p, n, aide=True):
    faims = []
    for _ in range(n):
        if aide: _aide_carburant(w, p)
        T.jours(w, 1); faims.append(T.faim(w))
    return faims


_ANNEE = {}


def _annee():
    """Une annee du pays avec la regle ( une seule fois pour les deux portes qui la lisent )."""
    if not _ANNEE:
        w, p = T.monde(["agriculture"])
        t0 = time.perf_counter()
        faims = _vivre(w, p, JOURS_ANNEE)
        _ANNEE.update(w=w, p=p, faims=faims, t=time.perf_counter() - t0)
    return _ANNEE


def _serie(p):
    return np.array([s[:10] for s in p.domaine("agriculture").serie], float)


# ================================================================== les lois
def test_biens_et_recettes():
    """Porte : les treize biens du domaine sont au catalogue avec masse, volume, conservation ; le frais perit vite ( lait,
    poisson au plus 3 jours ; viande, legumes, fruits au plus 14 ), le stockable dure ( grain, huile au moins un an,
    feta au moins 4 mois ). Les rendements declares tombent dans les fourchettes reelles grecques ( ecrites ICI, pas lues
    dans le module : ble dur 2,5-3,0 t/ha, olives 1,8-3,2, legumes d ete 20-60, vergers 12-25, luzerne 8-16, vesce-avoine
    3-7 ). Chaque recette declaree conserve la masse ( sorties <= 1 kg ) et les calories ; la ration fait 2 500 kcal de
    parts qui somment a 1. Falsificateurs : une recette qui cree de la matiere, une qui cree des calories sont refusees."""
    w, p = T.monde(["agriculture"])
    cat = p.socle.catalogue
    manque = [b for b in M.NOMS_BIENS if b not in cat.par_nom or cat[b].masse_kg is None or cat[b].volume_l is None]
    cj = {b: cat[b].conservation_j for b in M.NOMS_BIENS if b in cat.par_nom}
    perissable = all(cj[b] <= 3 for b in ("lait", "poisson")) and all(cj[b] <= 14 for b in ("viande", "legumes", "fruits"))
    durable = cj["cereales"] >= 365 and cj["huile"] >= 365 and cj["fromage"] >= 120
    reels = {"ble": (2.5, 3.0), "olivier": (1.8, 3.2), "legumes_ete": (20.0, 60.0), "vergers": (12.0, 25.0),
             "luzerne": (8.0, 16.0), "vesce_avoine": (3.0, 7.0)}
    hors = [n for n, (a, b) in reels.items() if not a <= M.CULTURES[M.IC[n]].rendement_t_ha <= b]
    recettes = all(math.fsum(r.sorties.values()) <= 1.0 and math.fsum(q * M.KCAL[b] for b, q in r.sorties.items()) <= M.KCAL[r.entree]
                   for r in M.RECETTES.values())
    ration = abs(math.fsum(M.PARTS_RATION) - 1.0) < 1e-12 and M.KCAL_RATION == 2500.0 \
        and all(m >= n for m, n in zip(M.PARTS_MAX, M.PARTS_RATION))
    refus = 0
    for entree, sorties in (("cereales", {"farine": 0.90, "fourrage": 0.20}), ("lait", {"fromage": 0.50})):
        try: M.Recette("fausse", entree, sorties, "falsificateur")
        except ValueError: refus += 1
    ok = not manque and perissable and durable and not hors and recettes and ration and refus == 2
    return ok, (f"biens sans masse ou volume {manque} ; conservation ( jours ) " + ", ".join(f"{b} {v:g}" for b, v in cj.items())
                + f" ; rendements hors fourchette reelle {hors} ; recettes conservatives {recettes} ; ration {ration} ; "
                f"recettes fausses refusees {refus}/2")


# ================================================================== la campagne
def test_rendements_campagne():
    """Porte : une annee du pays ( 15 juin -> moisson suivante ), sans engrais ( pas de domaine 10 ) : pour chaque culture
    dont une campagne se ferme, le rendement recolte ( t/ha, sur la part de la fenetre vecue par le monde ) sur le
    rendement reel declare x l effet de l absence d engrais tombe dans [ 0,70 ; 1,30 ] ; la moyenne ponderee par les
    surfaces dans [ 0,85 ; 1,15 ] ; les pertes ( non recolte, retard ) sous 5 % de la recolte. Le climat de chaque
    campagne ( rendement climatique pondere ) est rapporte : il fait la difference entre une annee et la normale."""
    A = _annee()["p"].domaine("agriculture")
    agg = {}
    for (j, g, c, ha, kg, perdu, fr, clim, eng) in A.champs.campagnes:
        cu = M.CULTURES[c]
        if cu.mode == "coupes": continue
        cle = (c, j // 200)
        a = agg.setdefault(cle, [0.0, 0.0, 0.0, 0.0, 0.0])
        a[0] += ha * fr; a[1] += kg; a[2] += perdu; a[3] += clim * ha; a[4] += ha
    # la luzerne : ses six coupes d une annee ( du jour 0 au jour 365 )
    lz = M.IC["luzerne"]
    coupes = [(ha, kg, perdu) for (j, g, c, ha, kg, perdu, fr, clim, eng) in A.champs.campagnes if c == lz and j < 365]
    rapports, lignes, pertes = [], [], True
    for (c, per), (haf, kg, perdu, climh, ha) in sorted(agg.items()):
        cu = M.CULTURES[c]
        t_ha = kg / haf / 1000.0
        r = t_ha / (cu.rendement_t_ha * cu.sans_engrais)
        rapports.append((r, ha)); pertes &= perdu <= 0.05 * kg
        lignes.append(f"{cu.nom} {t_ha:.2f} t/ha ( x{r:.2f}, climat {climh / ha:.2f}, pertes {perdu / max(kg, 1e-9):.1%} )")
    if coupes:
        cu = M.CULTURES[lz]
        surf = A.champs.surface[lz].sum()
        t_ha = sum(k for _, k, _ in coupes) / surf / 1000.0
        r = t_ha / (cu.rendement_t_ha * cu.sans_engrais)
        rapports.append((r, surf)); pertes &= sum(x for _, _, x in coupes) <= 0.05 * sum(k for _, k, _ in coupes)
        lignes.append(f"luzerne {t_ha:.2f} t/ha en {len(coupes) // len(A.liste)} coupes ( x{r:.2f} )")
    moy = sum(r * h for r, h in rapports) / sum(h for _, h in rapports) if rapports else 0.0
    cultures = {M.CULTURES[c].nom for c, _ in agg} | ({"luzerne"} if coupes else set())
    ok = (len(cultures) >= 6 and all(0.70 <= r <= 1.30 for r, _ in rapports) and 0.85 <= moy <= 1.15 and pertes)
    return ok, f"{len(cultures)} cultures closes ; " + " ; ".join(lignes) + f" ; moyenne ponderee x{moy:.3f}"


def _recolte_monde(secheresse, jours=60):
    w, p = T.monde(["agriculture"])
    if secheresse: TER.imposer_secheresse(p, "Altis", jours, reserves=0.0)
    A = p.domaine("agriculture")
    fs, fi = [], []
    for _ in range(jours):
        T.jours(w, 1); fs.append(float(A.fs.mean())); fi.append(float(A.fi.mean()))
    fm = A.flux_motif
    irr = sum(fm.get(("produit", "recolte", b), 0.0) for b in ("legumes", "fruits")) \
        + fm.get(("produit", "recolte", "fourrage"), 0.0)
    olives = sum(M.rendement_attendu(p, ex.lieu, "olivier") for ex in A.liste)
    return irr, olives, float(np.mean(fs)), float(np.mean(fi))


def test_secheresse():
    """Controle positif : une secheresse du territoire ( 60 jours sans pluie, +3 degres, reserves des bassins vides,
    sols au point de fletrissement : territoire.imposer_secheresse ) des le 15 juin. Porte : la recolte irriguee des 60
    jours ( legumes, fruits, luzerne ) tombe a 85 % au plus du monde normal, et la recolte d olives attendue ( en sec,
    au climat accumule ) aussi. L instrument : dans le monde normal, le rendement climatique moyen, sec et irrigue, est
    de 0,8 a 1,2."""
    n_irr, n_ol, n_fs, n_fi = _recolte_monde(False)
    s_irr, s_ol, s_fs, s_fi = _recolte_monde(True)
    ri, ro = s_irr / n_irr, s_ol / n_ol
    ok = ri <= 0.85 and ro <= 0.85 and 0.8 <= n_fs <= 1.2 and 0.8 <= n_fi <= 1.2
    return ok, (f"recolte irriguee en 60 jours : normale {n_irr / 1000:.0f} t, secheresse {s_irr / 1000:.0f} t ( {ri:.0%} ) ; "
                f"olives attendues : normale {n_ol / 1000:.0f} t, secheresse {s_ol / 1000:.0f} t ( {ro:.0%} ) ; rendement "
                f"climatique moyen normal sec {n_fs:.2f} irrigue {n_fi:.2f}, secheresse sec {s_fs:.2f} irrigue {s_fi:.2f}")


# ================================================================== conservation, peremption
def _peremption(falsifier=False, jours=12):
    w, p = T.monde(["agriculture"])
    A = p.domaine("agriculture"); cat = p.socle.catalogue
    if falsifier: cat["lait"].conservation_j = 4.0          # une erreur posee a la main dans le catalogue
    for x in A.liste: x.sequestre = True             # rien ne perit ailleurs : le grand livre national ne voit qu elle
    ex = A.liste[0]
    frais = [b for b in M.NOMS_BIENS if M.BIENS[b][6] <= jours]
    for b in frais: M._entrer(p, A, ex, b, 100.0, "stock_initial")
    longs = {b: M._q(A, ex, b) for b in M.NOMS_BIENS if M.BIENS[b][6] > jours + 200}
    perime0 = {b: p.socle.livre.flux["perime"].get(b, 0.0) for b in frais}
    vu = {}
    for j in range(1, jours + 1):
        T.jours(w, 1)
        for b in frais:
            if b not in vu and M._q(A, ex, b) <= 1e-9: vu[b] = j
    perime = {b: p.socle.livre.flux["perime"].get(b, 0.0) - perime0[b] for b in frais}
    intacts = all(abs(M._q(A, ex, b) - q) <= 1e-9 for b, q in longs.items())
    return frais, vu, perime, intacts, p


def test_peremption():
    """Porte : dans un grenier sous sequestre ( rien n y entre ni n en sort ; les autres aussi, pour que le grand livre
    national ne voie que lui ), 100 kg de chaque bien frais poses le jour 0
    perissent EN ENTIER le jour ou leur age atteint la conservation DECLAREE dans le module ( lait et poisson 2 jours,
    olives 3, viande 4, legumes et fruits 10 ), le grand livre le voit ( flux perime = 100 kg chacun ), et le grain,
    l huile, la feta du meme grenier ne perdent rien ( controle negatif ). Falsificateur : la conservation du lait mise a
    4 jours dans le catalogue a la main - le lait perit le 4e jour, et la porte le voit."""
    frais, vu, perime, intacts, p = _peremption()
    au_jour = all(vu.get(b) == int(M.BIENS[b][6]) for b in frais)
    au_livre = all(abs(perime[b] - 100.0) <= 1e-9 for b in frais)
    _, vu_f, _, _, _ = _peremption(falsifier=True, jours=6)
    falsifie_vu = vu_f.get("lait") != int(M.BIENS["lait"][6])
    ecarts = M.ecarts_lots(p)
    ok = au_jour and au_livre and intacts and falsifie_vu and not ecarts
    return ok, ("peri le jour " + ", ".join(f"{b} {vu.get(b)} ( declare {M.BIENS[b][6]:g} )" for b in frais)
                + f" ; au grand livre 100 kg chacun {au_livre} ; stockables intacts {intacts} ; lait a 4 jours au catalogue : "
                f"peri le jour {vu_f.get('lait')}, vu {falsifie_vu} ; lots = stocks {not ecarts}")


def _flux(A):
    return dict(A.flux_motif)


def _ecarts_recettes(A, avant):
    """Mesure dans le grand livre ( flux clos par motif ), contre les recettes DECLAREES ( M.DECLAREES, figees a
    l import ) : ( ecart relatif de masse, ecart relatif de kcal ) par recette, et l ecart de la cuisine."""
    fm = A.flux_motif
    d = lambda k: fm.get(k, 0.0) - avant.get(k, 0.0)
    out = {}
    for nom, (entree, sorties, _) in M.DECLAREES.items():
        q_in = d(("consomme", nom, entree))
        m_out = math.fsum(d(("produit", nom, b)) for b in sorties)
        k_out = math.fsum(d(("produit", nom, b)) * M.BIENS[b][7] for b in sorties)
        m_att = q_in * math.fsum(sorties.values())
        k_att = q_in * math.fsum(k * M.BIENS[b][7] for b, k in sorties.items())
        out[nom] = (q_in, abs(m_out - m_att) / max(1.0, m_att), abs(k_out - k_att) / max(1.0, k_att))
    return out


def test_transformation():
    """Porte : mesures dans le grand livre ( flux par motif ), contre les recettes declarees ( M.DECLAREES, figees a
    l import ) : sur l annee du pays, chacune des quatre recettes ( moudre, presser, fromager, trier ) est exercee et
    conserve la masse et les calories a 1e-9 pres. Sur 20 jours ( du jour 1 au jour 21 ), la cuisine consomme EXACTEMENT
    2 500 kcal par ration produite ( kcal des ingredients du motif cuisiner / flux produit de nourriture ) a 1e-9 pres ;
    lots = stocks ; cheptel = depart + naissances - abattus - morts ; conservation du socle tenue. Falsificateur : le
    moulin rendu a 0,80 kg de farine au lieu de 0,78 en marche ( l objet Recette qui travaille, pas la declaration ) -
    le bilan du moulin le voit."""
    r_an = _ecarts_recettes(_annee()["p"].domaine("agriculture"), {})
    w, p = T.monde(["agriculture"])
    A = p.domaine("agriculture"); L = p.socle.livre
    T.jours(w, 1)                                   # l aube du jour 1 : le jour 0 ( et les rations de l installation ) est clos
    avant = _flux(A); nour0 = L.flux["produit"]["nourriture"]
    T.jours(w, 20)
    kcal = math.fsum((A.flux_motif.get(("consomme", "cuisiner", b), 0.0) - avant.get(("consomme", "cuisiner", b), 0.0))
                     * M.BIENS[b][7] for b in M.NOMS_BIENS)
    rations = L.flux["produit"]["nourriture"] - nour0
    cuisine = abs(kcal - 2500.0 * rations) / max(1.0, kcal)
    exercees = [n for n, v in r_an.items() if v[0] > 0]
    justes = all(v[1] <= 1e-9 and v[2] <= 1e-9 for v in r_an.values())
    tenue, msg = p.socle.conservation.tenue()
    lots, cheptel = M.ecarts_lots(p), M.bilan_cheptel(p)
    avant2 = _flux(A)
    M.RECETTES["moudre"].sorties["farine"] = 0.80
    try: T.jours(w, 3)
    finally: M.RECETTES["moudre"].sorties["farine"] = 0.78
    r2 = _ecarts_recettes(A, avant2)
    vu = r2["moudre"][0] > 0 and r2["moudre"][1] > 1e-6
    ok = (set(exercees) == set(M.DECLAREES) and justes and cuisine <= 1e-9 and tenue and not lots and abs(cheptel) <= 1e-6
          and vu)
    return ok, ("recettes sur l annee : " + ", ".join(f"{n} {v[0] / 1000:.1f} t ( masse {v[1]:.1e}, kcal {v[2]:.1e} )"
                                                      for n, v in r_an.items())
                + f" ; cuisine : {rations:.0f} rations pour {kcal / 2500:.0f} rations de kcal ( ecart {cuisine:.1e} ) ; {msg} ; "
                f"lots {len(lots)} ecarts ; cheptel {cheptel:+.1e} tete ; moulin fausse a 0,80 : ecart de masse "
                f"{r2['moudre'][1]:.1e}, vu {vu}")


# ================================================================== le travail
def _jusqu_a(w, jour, heure):
    """Fait vivre le monde jusqu au pas qui commence au jour et a l heure donnes, celui-ci compris ( ses routines ont
    tourne ) ; l heure est un multiple de 10 minutes."""
    cible = round(jour * 24 * 60 + heure * 60)
    while w.minutes <= cible: w.pas_suivant()


def test_dimanche():
    """Porte, avec l agenda : le vendredi ( jour 0 ), les paysans sont au travail dans leur ferme ( controle positif :
    presence > 0 ) ; le dimanche ( jour 2 ), la presence au poste est NULLE dans chaque ferme, les betes et l atelier sont
    tenus par une astreinte bornee a leur besoin ( astreinte <= soins + atelier, pour chaque ferme ), qui n est qu une
    petite part d une journee ( moins de 10 % des heures d un jour de travail des paysans ), et la paie voit exactement
    ces heures. Falsificateur : le meme dimanche compte avec le critere de Monde.produire ( dans le lieu de sa ferme, a
    l heure de son horaire ) - des paysans chez eux comptent au travail, et la porte le voit."""
    w, p = T.monde(["agriculture", "agenda"])
    A = p.domaine("agriculture")
    _jusqu_a(w, 0, 15 + 50 / 60)
    vendredi = sum(ex.presence_h for ex in A.liste)
    _jusqu_a(w, 2, 0.0)
    snap = pickle.dumps(w)
    _jusqu_a(w, 2, 15 + 50 / 60)
    dim = sum(ex.presence_h for ex in A.liste)
    ast = sum(ex.astreinte_h for ex in A.liste)
    borne = all(ex.astreinte_h <= ex.soins_besoin_h + ex.atelier_besoin_h + 1e-9 for ex in A.liste)
    paysans = [h for ex in A.liste for h in ex.paysans]
    paie = sum(h.heures_jour for h in paysans)
    journee = 8.0 * len(paysans)
    w2 = pickle.loads(snap); A2 = w2.pays.domaine("agriculture"); A2.critere = "lieu_e1"
    _jusqu_a(w2, 2, 15 + 50 / 60)
    faux = sum(ex.presence_h for ex in A2.liste)
    ok = vendredi > 0 and dim == 0 and 0 < ast <= 0.10 * journee and borne and abs(paie - ast) <= 1e-6 and faux > 0
    return ok, (f"vendredi {vendredi:.0f} h de presence ; dimanche {dim:.0f} h de presence, astreinte {ast:.1f} h pour "
                f"{len(paysans)} paysans ( {ast / journee:.1%} d une journee ), bornee au besoin {borne}, heures vues par la "
                f"paie {paie:.1f} ; critere de Monde.produire le meme dimanche : {faux:.0f} h ( vu : {faux > 0} )")


def test_peche_meteo():
    """Controle positif et negatif de la peche : le jour 1 ( la moisson du jour 0 est faite ), vent force a 3 m/s, chaque
    caique sort ( son usure monte de ses heures de mer ) ; vent force a 12 m/s ( force 6 ), aucun ne sort. Et au moins un
    village sur cinq a son caique ( repere cotier a moins de 2,5 km )."""
    w, p = T.monde(["agriculture"])
    A = p.domaine("agriculture")
    cotieres = [ex for ex in A.liste if ex.bateau is not None]
    _jusqu_a(w, 1, 15 + 40 / 60)
    res = []
    for vent in (3.0, 12.0):
        w2 = pickle.loads(pickle.dumps(w)); p2 = w2.pays; A2 = p2.domaine("agriculture")
        p2.domaine("territoire").meteo.vent[:] = vent
        avant = {ex.id: ex.bateau.usure for ex in A2.liste if ex.bateau is not None}
        M._journee(p2)
        res.append(sum(1 for ex in A2.liste if ex.bateau is not None and ex.bateau.usure > avant[ex.id]))
    ok = len(cotieres) >= len(A.liste) / 5 and res[0] == len(cotieres) and res[1] == 0
    return ok, (f"{len(cotieres)} villages cotiers sur {len(A.liste)} ; vent 3 m/s : {res[0]} caiques sortent ; "
                f"vent 12 m/s : {res[1]}")


# ================================================================== nourrir le pays
def test_pays_nourri():
    """Porte : une annee du pays, regle de vente, echafaudage de carburant. L agriculture nourrit toute l annee : la
    demande SOLVABLE que les marches n ont pas servie faute de stock ( economie : non_servi ) reste sous 0,5 % des
    rations vendues ; sur chaque fenetre de 30 jours, les fermes livrent au moins 95 % du besoin des regions ; le grain de
    l annee passee tient jusqu a la moisson suivante ( jamais a zero ). La faim des menages est rapportee a cote, avec sa
    part de pauvrete ( menages sans caisse ) : elle ne mesure pas l agriculture quand les marches sont pleins."""
    R = _annee(); w, p = R["w"], R["p"]
    S = _serie(p)
    rations, non_servi, vendu, besoin, grain = S[:, 1], S[:, 6], S[:, 7], S[:, 8], S[:, 9]
    part_ns = non_servi.sum() / max(1.0, non_servi.sum() + vendu[-1] - vendu[0])
    fen = [rations[k:k + 30].sum() / besoin[k:k + 30].sum() for k in range(0, len(rations) - 29, 30)]
    grain_min = float(grain.min())
    faims = np.array(R["faims"])
    pauvres = [mg for mg in T.menages_habites(w) if not w.nourri_menage.get(mg.id, True)]
    sans_caisse = sum(1 for mg in pauvres if mg.caisse < 1.0) / max(1, len(pauvres))
    ok = part_ns <= 0.005 and min(fen) >= 0.95 and grain_min > 0
    return ok, (f"{len(S)} jours en {R['t']:.0f} s : demande solvable non servie {part_ns:.2%} des ventes ; livraisons sur "
                f"30 jours de {min(fen):.0%} a {max(fen):.0%} du besoin ; grain au plus bas {grain_min / 1000:.1f} t ; faim "
                f"moyenne {faims.mean():.1%} ( 95e centile {np.percentile(faims, 95):.1%} ), dont menages sans caisse "
                f"{sans_caisse:.0%} au dernier soir")


def test_temoin_affame():
    """Porte de la decision : le temoin bete ( tout vendre au negoce chaque semaine ) laisse les marches sans stock : des
    jours 30 a 150, la demande solvable non servie depasse 5 % des rations vendues, quand la regle, sur les memes jours,
    reste sous 0,5 % ( part de la demande solvable : non servi / ( non servi + vendu ) ). ( Ecrite avec test_pays_nourri,
    separee pour que l une ne cache pas l autre. )"""
    R = _annee()
    Sr = _serie(R["p"])
    w, p = T.monde(["agriculture"], modes={"vendre_recolte": "temoin"})
    _vivre(w, p, 150)
    St = _serie(p)

    def part(S):
        """La part de la demande solvable que les marches n ont pas servie faute de stock."""
        sel = (S[:, 0] >= 30) & (S[:, 0] < 150)
        v = S[sel, 7]; ns = S[sel, 6].sum()
        return ns / max(1.0, ns + v[-1] - v[0])
    pt, pr = part(St), part(Sr)
    grain = St[(St[:, 0] >= 30) & (St[:, 0] < 150), 9]
    ok = pt >= 0.05 and pr <= 0.005
    return ok, (f"jours 30-150 : demande solvable non servie, temoin {pt:.1%}, regle {pr:.2%} ; grain du temoin au plus bas "
                f"{grain.min() / 1000:.1f} t ; faim moyenne temoin {np.mean([T.faim(w)]):.0%} au jour 150")


def test_part_du_choix():
    """Porte de la decision, en mode hasard, dans le scenario ou elle compte : la premiere decision apres la moisson
    ( jour 1, les 27 fermes le meme jour, greniers pleins et comparables ), lue sur son horizon de 14 jours, dans trois
    mondes de graines differentes ( 81 notes, ~27 par action, toutes murees le meme jour ). La note depend du choix :
    part du choix ( epsilon carre intra-jour ) >= 0,01 et p de permutation < 0,05 ; conservation tenue dans chaque monde.
    Pourquoi pas plusieurs semaines d un seul monde : au hasard, un tiers des fermes « vend tout » a chaque decision et
    garde un grenier vide jusqu a la moisson suivante ; ses notes suivantes sont faites par ce choix passe, pas par celui
    du jour ( ecarts-types de 0,8 a 1,8 contre 0,1 le premier jour, mesure du 23/09 )."""
    from ..socle import decision as D
    tout = D.Decideur(M.POINT_VENTE, "hasard")
    tenues, msgs = True, []
    for graine in (11, 12, 13):
        w, p = T.monde(["agriculture"], graine=graine, modes={"vendre_recolte": "hasard"})
        T.jours(w, 16)
        dec = p.domaine("agriculture").decideur
        for k, (n, s_, q) in dec.stats.items():
            t = tout.stats.setdefault(k, [0, 0.0, 0.0]); t[0] += n; t[1] += s_; t[2] += q
        tout.echantillon.extend(dec.echantillon)
        tout.n_decisions += dec.n_decisions
        tenue, msg = p.socle.conservation.tenue(); tenues &= tenue; msgs.append(msg)
    part = tout.part_du_choix(); pp = tout.p_permutation(); notes = tout.notes_par_action()
    n_notes = sum(n for n, _ in notes.values())
    ok = part >= 0.01 and pp < 0.05 and n_notes >= 3 * 27 and tenues
    return ok, (f"{tout.n_decisions} decisions, {n_notes} notes murees ; notes : "
                + ", ".join(f"{a} {m:+.3f} ( {n} )" for a, (n, m) in notes.items())
                + f" ; part du choix ( epsilon carre ) {part:.3f}, brute {tout.part_du_choix_brute():.3f}, p de permutation "
                f"{pp:.3f} ; conservation {'tenue' if tenues else 'ROMPUE'} ( {msgs[-1]} )")


def test_pays_vivable():
    return T.porte_commune("agriculture", n_jours=12)


def test_cout():
    """Les routines propres du domaine coutent au plus 25 % d une journee du moteur seul, a 10 000 habitants ( 2 200
    paysans ; la presence est lue 144 fois par jour sur chacun ) ; l installation ( normales du territoire comprises )
    moins de 5 s."""
    def jour_moteur():
        w = W.Monde(echelle=20); T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants)
    t_e1, n = jour_moteur()
    t0 = time.perf_counter()
    w, p = T.monde(["agriculture"], echelle=20)
    t_inst = time.perf_counter() - t0
    T.jours(w, 2)
    minutes = sorted(p.routines)
    t0 = time.perf_counter()
    for _ in range(2):
        for mn in minutes:
            for _, dom, f in p.routines[mn]:
                if dom == "agriculture":
                    if f is M._nuit: p.domaine("agriculture").jour_nuit = None
                    f(p)
    propre = (time.perf_counter() - t0) / 2
    ok = propre <= 0.25 * t_e1 and t_inst <= 5.0
    return ok, (f"{n} habitants : moteur seul {t_e1:.2f} s par jour ; routines propres de l agriculture {propre * 1000:.0f} ms "
                f"par jour ( {propre / t_e1:.0%} du moteur ) ; installation avec ses dependances {t_inst:.1f} s")


TESTS = [test_biens_et_recettes, test_peremption, test_transformation, test_dimanche, test_peche_meteo, test_secheresse,
         test_part_du_choix, test_pays_vivable, test_rendements_campagne, test_pays_nourri, test_temoin_affame, test_cout]
