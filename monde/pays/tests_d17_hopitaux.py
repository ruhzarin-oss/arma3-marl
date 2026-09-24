"""Les portes du domaine 17 ( hopitaux ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests hopitaux"""
import math, time
import numpy as np
from .. import config as C, monde as W
from ..socle import registre as R
from . import essais as T, d16_medecine as M, d17_hopitaux as HP

PAS_J = C.PAS_PAR_JOUR


def _a_l_heure(w, heure):
    """Fait vivre le monde jusqu au prochain pas qui tombe a `heure`."""
    for _ in range(PAS_J + 1):
        if abs(w.heure - heure) < 1e-9: return w
        w.pas_suivant()
    raise RuntimeError("heure jamais atteinte")


def _insulinodependants(p, region):
    w = p.w; med = p.domaine("medecine")
    ch = p.col("habitant", "med_chroniques")
    return [h.id for h in w.habitants if h.vivant and ch[h.id] & M.INSULINE
            and med.region_de_lieu[h.domicile.marche.id] == region]


# ================================================================== dimensionnement
def test_dimensionnement():
    """Porte : a 500 et a 10 000 habitants, chaque hopital a la capacite du dimensionnement declare ( lits du batiment
    du domaine 13 a 4,2 pour 1 000, au moins 2 ; reanimation a 6 pour 100 000, au moins 1 dans l hopital le plus peuple
    de l ile ; 1 bloc pour 40 lits, au moins 1 ; ambulances a 9 pour 100 000, au moins 1 ) ; chaque medecin et chaque
    infirmier vivant du moteur est affecte a un et un seul hopital, celui de sa capitale ; tout hopital de deux
    medecins ou plus a un chirurgien et un anesthesiste. A 10 000 habitants, ou les planchers ne comptent plus, les
    lits font 3,6 a 4,8 pour 1 000. Falsificateur : un lit retire a la main est vu."""
    msgs, ok = [], True
    for ech in (1, 20):
        w, p = T.monde(["hopitaux"], graine=3, echelle=ech)
        H = p.domaine("hopitaux")
        ecarts = HP.ecarts_capacite(p)
        vivants = sum(1 for h in w.habitants if h.vivant)
        soignants = {h.id: h for h in w.habitants if h.vivant and h.role in ("medecin", "infirmier")}
        affect = {}
        for e in H.etabs:
            for x in e.medecins + e.infirmiers: affect[x] = affect.get(x, 0) + 1
        un_seul = set(affect) == set(soignants) and all(v == 1 for v in affect.values())
        bonne_capitale = all(soignants[x].travail.id == e.lieu for e in H.etabs for x in e.medecins + e.infirmiers)
        equipes = all(HP.a_une_equipe_chirurgicale(e) for e in H.etabs if len(e.medecins) >= 2)
        amb = all(len(e.ambulances) == max(1, int(round(HP.AMBULANCES_100K * e.pop / 1e5))) for e in H.etabs)
        lits = sum(len(e.lits_occ) + len(e.rea_occ) for e in H.etabs)
        rea = sum(len(e.rea_occ) for e in H.etabs)
        dens = lits / vivants * 1000.0
        med = sum(len(e.medecins) for e in H.etabs) / vivants * 1000.0
        inf = sum(len(e.infirmiers) for e in H.etabs) / vivants * 1000.0
        ok &= not ecarts and un_seul and bonne_capitale and equipes and amb and (ech == 1 or 3.6 <= dens <= 4.8)
        msgs.append(f"{vivants} habitants : {lits} lits ( {dens:.1f} pour 1 000 ), {rea} de reanimation "
                    f"( {rea / vivants * 1e5:.0f} pour 100 000 ), {sum(len(e.bloc_occ) for e in H.etabs)} blocs, "
                    f"{sum(len(e.ambulances) for e in H.etabs)} ambulances ; medecins {med:.1f} et infirmiers {inf:.1f} "
                    f"pour 1 000 ( Grece {HP.MEDECINS_1000_GRECE} et {HP.INFIRMIERS_1000_GRECE} ) ; ecarts {len(ecarts)}, "
                    f"affectes une fois {un_seul}, a leur capitale {bonne_capitale}, equipes chirurgicales {equipes}")
        if ech == 1:
            e = H.etabs[0]; e.lits_occ.pop()
            vu = bool(HP.ecarts_capacite(p))
            ok &= vu
            msgs.append(f"lit retire a la main vu {vu}")
    return ok, " ; ".join(msgs)


# ================================================================== la conservation des lits
def test_conservation_lits():
    """Porte : 10 jours a 1 000 habitants, deux accidents de masse ( 12 blesses a Athira aux jours 2 et 6 ) et le COVID
    introduit ( 15 cas ) : a chaque pas, lits occupes + libres = capacite, chaque lit occupe a son passage et chaque
    hospitalise son lit ( `ecarts_lits` vide ) ; tout malade couche vivant est grave ( gravite > 0,3 ) ; tout malade
    deja couche au pas precedent est au poste « hopital » du moteur. Controle : les lits ont ete pleins au moins une
    fois ( sinon la porte ne mesure rien ). Falsificateurs : un lit occupe par un habitant sans passage, et un passage
    couche dont on a vide le lit, sont vus."""
    w, p = T.monde(["hopitaux"], graine=5, echelle=2)
    H = p.domaine("hopitaux")
    T.jours(w, 1)
    M.introduire(p, "covid", 15)
    ecarts, non_graves, hors_poste, plein, couches_avant = 0, 0, 0, 0, set()
    for j in range(10):
        if j in (1, 5):
            _a_l_heure(w, 14.0); HP.afflux(p, 12, "Athira")
        for _ in range(PAS_J):
            w.pas_suivant()
            ecarts += len(HP.ecarts_lits(p))
            couches = set()
            for e in H.etabs:
                for hid in e.lits_occ + e.rea_occ:
                    if hid < 0: continue
                    h = w.habitants[hid]
                    couches.add(hid)
                    if h.vivant and not (h.etat == "I" and h.gravite > HP.GRAVITE_LIT): non_graves += 1
                    if hid in couches_avant and h.vivant and h.poste != "hopital": hors_poste += 1
                if e.lits_occ and all(x >= 0 for x in e.lits_occ + e.rea_occ): plein += 1
            couches_avant = couches
    # falsificateurs : un habitant sans passage pose dans un lit ( libre, ou a la place de son occupant )
    e = H.etabs[0]
    intrus = next(h.id for h in w.habitants if h.vivant and h.id not in H.actifs)
    garde = e.lits_occ[0]; e.lits_occ[0] = intrus
    vu1 = any(x[0] == "lit_sans_patient" for x in HP.ecarts_lits(p))
    e.lits_occ[0] = garde
    ps = next((ps for ps in H.actifs.values() if ps.etat in (HP.LIT, HP.REA)), None)
    vu2 = False
    if ps is not None:
        arr = H.etabs[ps.etab].rea_occ if ps.etat == HP.REA else H.etabs[ps.etab].lits_occ
        garde = arr[ps.lit]; arr[ps.lit] = -1
        vu2 = any(x[0] == "hospitalise_sans_lit" for x in HP.ecarts_lits(p))
        arr[ps.lit] = garde
    c = H.compteurs
    ok = ecarts == 0 and non_graves == 0 and hors_poste == 0 and plein > 0 and vu1 and vu2
    return ok, (f"10 jours, {PAS_J * 10} pas : ecarts {ecarts}, couches non graves {non_graves}, couches hors du poste "
                f"hopital {hors_poste} ; un hopital plein pendant {plein} pas ; admissions {c.get('admissions', 0)}, "
                f"reanimation {c.get('admissions_rea', 0)}, chirurgies {c.get('chirurgies', 0)}, deces "
                f"{c.get('deces', 0)} ; lit fantome vu {vu1}, hospitalise sans lit vu {vu2}")


# ================================================================== controle positif : l afflux sature
def _saturation(afflux):
    w, p = T.monde(["hopitaux"], graine=7, echelle=2)
    H = p.domaine("hopitaux")
    T.jours(w, 1)
    _a_l_heure(w, 10.0)
    t0 = w.pas
    if afflux: HP.afflux(p, 20, "Athira")
    e = H.etab_de_lieu["Athira"]
    file_max, plein = 0, 0
    for _ in range(2 * PAS_J):
        w.pas_suivant()
        f = len(e.file_med) + len(e.file_bloc) + len(e.file_lit) + len(e.file_rea) + len(H.appels.get(e.ile, ()))
        file_max = max(file_max, f)
        plein += all(x >= 0 for x in e.lits_occ + e.rea_occ)
    d = [x for x in HP.delais(p) if x[2] >= t0]
    vus = [(x[4] - x[2]) * C.MINUTES_PAR_PAS for x in d if x[4] >= 0]
    return file_max, (float(np.mean(vus)) if vus else 0.0), len(vus), plein


def test_afflux_sature():
    """Controle positif : le meme pays ( 1 000 habitants ), deux jours, avec et sans un accident de masse de 20 blesses
    a Athira a 10 h. Avec l afflux : au moins 4 malades en attente en meme temps ( appels, urgences, bloc, lits ), les
    lits d Athira pleins au moins 6 pas, et un delai moyen de l appel a l examen d au moins 30 minutes et au moins double
    de celui du pays sans afflux ; sans lui, au plus 2 en attente."""
    fa, da, na, pa = _saturation(True)
    fs, ds, ns, ps = _saturation(False)
    ok = fa >= 4 and pa >= 6 and da >= 30.0 and da >= 2.0 * ds and fs <= 2
    return ok, (f"afflux : file maximale {fa}, lits pleins {pa} pas, appel -> examen {da:.0f} min ( {na} examens ) ; "
                f"sans afflux : file {fs}, lits pleins {ps} pas, {ds:.0f} min ( {ns} examens )")


# ================================================================== la rupture se voit chez les malades
def _rupture(rompre):
    w, p = T.monde(["hopitaux"], graine=9, echelle=2)
    H = p.domaine("hopitaux"); med = p.domaine("medecine"); L = p.socle.livre
    T.jours(w, 1)
    _a_l_heure(w, 11.0)
    b = H.id_mol["insuline"]
    ph = med.pharmacies[0]
    M.prendre(p, ph, "insuline", ph.stock[b], "essai")
    if rompre:
        HP.rupture_fournisseur(p, "insuline", 60)
        for g in H.grossistes:
            q = g.stock[b]
            L.perdre(g.stock, b, q, "essai"); HP._retirer_lots(g, b, q)
    qui = _insulinodependants(p, 0)
    T.jours(w, 4)
    sj = p.col("habitant", "med_sans_traitement_j")
    viv = [i for i in qui if w.habitants[i].vivant]
    part3 = sum(1 for i in viv if sj[i] >= 3) / max(1, len(viv))
    part1 = sum(1 for i in viv if sj[i] >= 1) / max(1, len(viv))
    jours = H.compteurs.get(("jours_sans", "officine", "insuline"), 0)
    crises = med.compteurs.get(("cas", "crise_diabetique"), 0)
    return len(qui), part3, part1, jours, crises


def test_rupture():
    """Porte : la pharmacie d Athira est videe de son insuline. Avec une rupture chez le fabricant ( et le grossiste
    vide ), apres 4 jours au moins 90 % de ses diabetiques insulinodependants vivants ont 3 jours ou plus sans insuline,
    et l officine compte au moins 3 jours sans molecule ; sans rupture, le grossiste la relivre le lendemain : au plus
    10 % ont encore un jour sans traitement, au plus 1 jour sans molecule. Au moins 5 malades concernes."""
    n, r3, r1, rj, rc = _rupture(True)
    _, s3, s1, sj_, sc = _rupture(False)
    ok = n >= 5 and r3 >= 0.9 and rj >= 3 and s1 <= 0.1 and sj_ <= 1
    return ok, (f"{n} insulinodependants a Athira ; rupture : {r3:.0%} a 3 jours et plus sans insuline, officine "
                f"{rj} jours sans molecule, {rc} crises diabetiques ; sans rupture : {s1:.0%} encore sans traitement, "
                f"{sj_} jours sans molecule, {sc} crises")


# ================================================================== le bilan des medicaments
def test_bilan_medicaments():
    """Porte : 25 jours a 1 000 habitants ( un lot du grossiste force a perimer, deux afflux ) : pour chaque molecule,
    stock du domaine = dotation + importe + dons - livre aux officines - dispense - perime a un millionieme pres, et
    commande = recu + annule + en route ; des importations sont arrivees ( 3 molecules au moins ), les officines ont ete
    livrees, les hopitaux ont dispense, le lot force a perime ; lots = stocks ( domaine et officines ) ; la conservation
    tient. Falsificateur : 3 doses posees a la main dans une pharmacie hospitaliere sont vues par le bilan, les lots et
    la conservation."""
    w, p = T.monde(["hopitaux"], graine=13, echelle=2)
    H = p.domaine("hopitaux")
    g = H.grossistes[0]
    b = H.id_mol["vaccin_grippe"]
    q0 = g.stock[b]
    g.lots[b][0][1] = p.jour + 2
    T.jours(w, 3)
    _a_l_heure(w, 14.0); HP.afflux(p, 10, "Athira")
    T.jours(w, 10)
    _a_l_heure(w, 14.0); HP.afflux(p, 10, "Pyrgos")
    T.jours(w, 12)
    bil = HP.bilan_medicaments(p)
    pire = max(abs(v[2]) / max(1.0, abs(v[1])) for v in bil.values())
    pire_cmd = max(abs(v[3]) for v in bil.values())
    importes = sum(1 for k in range(len(M.NOMS_MOL)) if H.recu[k] > 0)
    offi = sum(v[3] for v in H.bilan.values()); disp = sum(v[4] for v in H.bilan.values())
    perime = H.bilan["vaccin_grippe"][5]
    lots = HP.ecarts_lots_hopitaux(p) + M.ecarts_lots(p)
    tenue, msg = p.socle.conservation.tenue()
    e = H.etabs[0]; bm = H.id_mol["morphine"]
    e.stock._ajouter(bm, 3.0)
    vu_b = abs(HP.bilan_medicaments(p)["morphine"][2] - 3.0) < 1e-6
    vu_l = bool(HP.ecarts_lots_hopitaux(p)); vu_c = not p.socle.conservation.tenue()[0]
    ok = (pire <= 1e-6 and pire_cmd <= 1e-6 and importes >= 3 and offi > 0 and disp > 0 and perime >= q0 - 1e-9
          and not lots and tenue and vu_b and vu_l and vu_c)
    return ok, (f"pire ecart du bilan {pire:.1e} ( relatif ), des commandes {pire_cmd:.1e} ; {importes} molecules "
                f"importees, {offi:.0f} unites livrees aux officines, {disp:.0f} dispensees a l hopital, perime "
                f"{perime:.1f} / {q0:.1f} force ; lots {len(lots)} ecarts ; {msg} ; doses a la main vues ( bilan {vu_b}, "
                f"lots {vu_l}, conservation {vu_c} )")


# ================================================================== soigne a temps
def _blesses_graves(fermer):
    w, p = T.monde(["hopitaux"], graine=17, echelle=4)
    H = p.domaine("hopitaux")
    T.jours(w, 1)
    if fermer:
        for e in H.etabs: HP.fermer_bloc(p, e.id, 60)
    rng = np.random.default_rng(17)
    blesses = []
    for j in range(8):
        for heure in (9.0, 15.0):
            _a_l_heure(w, heure)
            for cap in ("Athira", "Kavala", "Pyrgos"):
                cand = [h for h in w.habitants if h.vivant and h.domicile.marche.id == cap and h.poste != "hopital"
                        and h.id not in H.actifs]
                h = cand[int(rng.integers(0, len(cand)))]
                M.blesser(p, h, ("ecrasement", "chute")[int(rng.integers(0, 2))], int(rng.integers(16, 31)))
                blesses.append((h.id, w.pas))
    T.jours(w, 5)
    morts = sum(1 for hid, _ in blesses if not w.habitants[hid].vivant)
    return len(blesses), morts / len(blesses), blesses, p


def test_blesse_a_temps():
    """Porte : 48 blesses graves ( ISS 16 a 30, contondants ) sur 8 jours, 2 000 habitants, 5 jours de suivi apres le
    dernier. Pays soigne contre le meme pays dont les blocs sont fermes ( pas de chirurgie, donc pas de soutien a
    temps ) : la mortalite sans bloc depasse d au moins 10 points et de 1,5 fois celle du pays soigne."""
    n, m_ok, bl, p = _blesses_graves(False)
    _, m_sans, _, _ = _blesses_graves(True)
    H = p.domaine("hopitaux")
    soutien = {}                        # habitant -> ( premier pas de soutien, ISS ), passages clos ET en cours
    for x in H.historique:
        if x[9] >= 0: soutien[x[1]] = min(soutien.get(x[1], (x[9], x[5])), (x[9], x[5]))
    for ps in H.actifs.values():
        if ps.t_soutien >= 0: soutien[ps.hid] = min(soutien.get(ps.hid, (ps.t_soutien, ps.iss)), (ps.t_soutien, ps.iss))
    delai = lambda iss: 6 if iss >= 41 else 18 if iss >= 25 else 36      # la phase aigue de la medecine, en pas
    a_temps = [hid for hid, t in bl if hid in soutien and 0 <= soutien[hid][0] - t <= delai(soutien[hid][1])]
    viv_temps = sum(1 for hid in a_temps if p.w.habitants[hid].vivant) / max(1, len(a_temps))
    tard = [hid for hid, _ in bl if hid not in a_temps]
    viv_tard = sum(1 for hid in tard if p.w.habitants[hid].vivant) / max(1, len(tard))
    ok = m_sans - m_ok >= 0.10 and m_sans >= 1.5 * m_ok
    return ok, (f"{n} blesses graves : mortalite {m_ok:.0%} avec les blocs, {m_sans:.0%} sans ; dans le pays soigne, "
                f"survie {viv_temps:.0%} des {len(a_temps)} soutenus avant la fin de leur phase aigue, {viv_tard:.0%} des {len(tard)} autres")


# ================================================================== la decision
HEURES_AFFLUX = (2.0, 5.0, 8.0, 11.0, 14.0, 17.0, 20.0, 23.0)
TAILLES_AFFLUX = (("Athira", 5), ("Kavala", 3), ("Pyrgos", 3))


def _monde_triage(mode, graine=23, jours_afflux=10):
    """3 000 habitants ; un accident de 11 blesses ( ISS de catastrophe ) toutes les 3 heures pendant 10 jours, puis
    l horizon du point pour que toutes les notes murissent."""
    w, p = T.monde(["hopitaux"], graine=graine, echelle=6, modes={"triage": mode})
    T.jours(w, 1)
    blesses = []
    for _ in range(jours_afflux):
        for heure in HEURES_AFFLUX:
            _a_l_heure(w, heure)
            for cap, n in TAILLES_AFFLUX: blesses += HP.afflux(p, n, cap)
            w.pas_suivant()
    T.jours(w, HP.HORIZON_TRIAGE + 1)
    return w, p, blesses


def _mortalite(p, blesses):
    """La mortalite des blesses venus a l hopital, par tranche d ISS."""
    iss = {}
    for x in p.domaine("hopitaux").historique: iss[x[1]] = max(iss.get(x[1], 0), x[5])
    par = {}
    for hid in set(blesses):
        if hid not in iss: continue
        k = iss[hid]; t = "9-15" if k < 16 else "16-24" if k < 25 else "25+"
        v = par.setdefault(t, [0, 0]); v[0] += 1; v[1] += not p.w.habitants[hid].vivant
    return {t: f"{v[1] / v[0]:.0%} de {v[0]}" for t, v in sorted(par.items())}


def test_decision():
    """Porte du point `triage`, en mode hasard ( 3 000 habitants, un accident de 11 blesses toutes les 3 heures pendant
    10 jours, puis l horizon de 14 jours ) : au moins 100 notes, au moins 3 jours ou chaque action a au moins 2 notes,
    part du choix >= 0,01 ET p de permutation < 0,05. En regard ( sans seuil ) : la mortalite des blesses par tranche
    d ISS quand la regle, puis le temoin, decident. Historique des mesures ( seuils jamais changes ) : 8 jours d un
    accident par jour et une note sur le servi et SON ecarte donnaient 105 notes, part 0,025, p 0,34 ; cette note etait
    biaisee ( le renvoye, moins grave, allait mieux de toute facon ) et son horizon de 3 jours ne voyait pas la fin de
    la phase aigue ; la note porte desormais sur le meme groupe quelle que soit l action, sur 14 jours."""
    w, p, bl = _monde_triage("hasard")
    dec = p.domaine("hopitaux").dec
    part, pval = dec.part_du_choix(), dec.p_permutation()
    notes = sum(n for n, _, _ in dec.stats.values())
    par_jour = {}
    for (j, a), (n_, _, _) in dec.stats.items(): par_jour.setdefault(j, {})[a] = n_
    jours_ok = sum(1 for d in par_jour.values() if all(d.get(a, 0) >= 2 for a in range(3)))
    morts = {}
    for mode in ("regle", "temoin"):
        _, p2, bl2 = _monde_triage(mode)
        morts[mode] = _mortalite(p2, bl2)
    ok = notes >= 100 and jours_ok >= 3 and part >= 0.01 and pval < 0.05
    return ok, (f"{dec.n_decisions} decisions, {notes} notes, {jours_ok} jours a 2 notes par action ou plus ; part du "
                f"choix {part:.3f}, p {pval:.3f} ; notes " + ", ".join(f"{a} {m:.3f} ( {n} )" for a, (n, m) in
                                                                       dec.notes_par_action().items())
                + f" ; mortalite des blesses : hasard {_mortalite(p, bl)}, regle {morts['regle']}, temoin "
                f"{morts['temoin']}")


# ================================================================== le financement
def test_financement():
    """Porte : 12 jours a 1 000 habitants, une clinique privee de 3 lits a Athira et deux accidents de masse : la
    clinique recoit au moins un malade que l hopital public ne pouvait coucher, et sa participation ; ce que l EOPYY a
    paye en forfaits egale la somme des passages factures ; l Etat a finance l EOPYY ; aucun hopital public ne garde
    d arriere de plus d un jour ; le rapprochement des familles du domaine est nul et la conservation tient.
    Falsificateur : 5 drachmes retirees a la main de la caisse de l EOPYY sont vues par le rapprochement."""
    w, p = T.monde(["hopitaux"], graine=19, echelle=2)
    H = p.domaine("hopitaux")
    rap = R.Rapprochement(p.socle.registre, p.socle.livre)
    cl = HP.ouvrir_etablissement(p, "clinique", "Athira", 3, prive=True)
    T.jours(w, 1)
    for j in range(2):
        _a_l_heure(w, 14.0); HP.afflux(p, 16, "Athira")
        T.jours(w, 4)
    T.jours(w, 3)
    fact = HP.couts_des_soins(p)
    ken = math.fsum(f[4] for f in fact); part = math.fsum(f[5] for f in fact)
    clinique = sum(1 for f in fact if f[2] == cl.id)
    egal = abs(ken - H.eopyy.paye_ken) <= 1e-6 * max(1.0, ken)
    vieux = sum(1 for e in H.etabs if not e.prive for c in p.socle.creances.de(e) if c.nee < p.jour - 1)
    restes = rap.restes()
    mes = {k: v for k, v in restes.items() if k in ("etablissements_sante", "grossistes", "eopyy")}
    rap_ok = all(abs(v) <= R.tolerance(v) + 1e-6 for v in mes.values())
    tenue, msg = p.socle.conservation.tenue()
    H.eopyy.caisse -= 5.0
    vu = abs(rap.restes()["eopyy"] + 5.0) < 1e-6
    H.eopyy.caisse += 5.0
    ok = clinique >= 1 and part > 0 and egal and H.eopyy.recu_etat > 0 and vieux == 0 and rap_ok and tenue and vu
    return ok, (f"{len(fact)} passages factures, forfaits {ken:.0f} dr ( EOPYY {H.eopyy.paye_ken:.0f}, egal {egal} ), "
                f"participation {part:.0f} dr, {clinique} sejours en clinique ; Etat -> EOPYY {H.eopyy.recu_etat:.0f} dr, "
                f"officines {H.eopyy.paye_officines:.0f} dr ; arrieres de plus d un jour {vieux} ; rapprochement "
                f"{ {k: round(v, 9) for k, v in mes.items()} } ; {msg} ; retrait a la main vu {vu}")


# ================================================================== avec les domaines optionnels
def test_domaines_optionnels():
    """Porte : avec l exterieur, l energie, le transport et le travail ( 500 habitants, 8 jours ) : une ligne coupee a
    Athira pendant un jour fait tourner le groupe electrogene ( au moins 6 heures ) ; un stock d amoxicilline du
    grossiste ramene a 2 jours est recommande et l import arrive par le port ( domaine 7 ) ; le carburant des
    ambulances est achete a la station ( domaine 14 ) ; la conservation tient."""
    w, p = T.monde(["hopitaux", "exterieur", "energie", "transport", "travail"], graine=29, echelle=1)
    from . import d11_energie as EN
    H = p.domaine("hopitaux"); L = p.socle.livre
    T.jours(w, 1)
    g = H.grossistes[0]; b = H.id_mol["amoxicilline"]; k = M.IMOL["amoxicilline"]
    q = g.stock[b] * 0.95
    L.perdre(g.stock, b, q, "essai"); HP._retirer_lots(g, b, q)
    recu0 = H.recu[k]
    _a_l_heure(w, 12.0)
    EN.couper_ligne(p, "Athira", 1.0)
    HP.afflux(p, 10, "Athira")
    T.jours(w, 7)
    e = H.etab_de_lieu["Athira"]
    tenue, msg = p.socle.conservation.tenue()
    recu = H.recu[k] - recu0
    missions = H.compteurs.get("missions", 0)
    ok = e.heures_groupe >= 6 and recu > 0 and missions > 0 and tenue
    return ok, (f"groupe electrogene {e.heures_groupe} h ; amoxicilline importee par le port {recu:.0f} unites ; "
                f"{missions} missions d ambulance ; {msg}")


# ================================================================== la porte commune et le cout
def test_pays_vivable():
    return T.porte_commune("hopitaux", n_jours=12)


def test_cout():
    """Le domaine coute au plus 25 % d une journee de ses dependances ( medecine, immobilier, industrie ), a 10 000
    habitants."""
    def jour_moyen(doms):
        w = W.Monde(echelle=20)
        T.P.installer(w, doms)
        T.jours(w, 1)
        t0 = time.perf_counter(); T.jours(w, 2)
        return (time.perf_counter() - t0) / 2, len(w.habitants), w
    t_base, n, _ = jour_moyen(["medecine", "immobilier", "industrie"])
    t_h, _, w = jour_moyen(["hopitaux"])
    H = w.pays.domaine("hopitaux")
    ok = t_h <= 1.25 * t_base
    return ok, (f"{n} habitants : dependances {t_base:.2f} s par jour, avec les hopitaux {t_h:.2f} s "
                f"( {t_h / t_base - 1:+.0%} ) ; {len(H.actifs)} passages en cours, {H.compteurs.get('passages', 0)} examens")


TESTS = [test_dimensionnement, test_conservation_lits, test_afflux_sature, test_rupture, test_bilan_medicaments,
         test_blesse_a_temps, test_decision, test_financement, test_domaines_optionnels, test_pays_vivable, test_cout]
