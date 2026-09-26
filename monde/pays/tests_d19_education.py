"""Les portes du domaine 19 ( education ). Ecrites avant la premiere mesure.   python -m monde.pays.tests education"""
import datetime as dt, pickle, time
import numpy as np
from .. import config as C, monde as W, population as PO, ecole as ECOLE
from ..socle import calendrier as CAL
from . import essais as T, pays as P, d04_travail as TR, d13_immobilier as IM, d19_education as M

_CACHE = {}


def _installe():
    """Un monde de 10 000 habitants, l education et ses dependances installees : chaque porte en reprend une copie."""
    if "installe" not in _CACHE:
        w, p = T.monde(["education"], echelle=20)
        _CACHE["installe"] = pickle.dumps(w)
    w = pickle.loads(_CACHE["installe"])
    return w, w.pays


def _passe():
    """Le meme monde apres 7 jours : examens deja notes ( recensement du 15 juin ), passage du 20 juin, sorties des
    etudes a l aube du 21 ( la 7e journee commence a cette aube )."""
    if "passe" not in _CACHE:
        w, p = _installe(); T.jours(w, 7)
        _CACHE["passe"] = pickle.dumps(w)
    w = pickle.loads(_CACHE["passe"])
    return w, w.pays


def _vivants_ids(p):
    tb = p.w.table; n = tb.n
    return np.nonzero(tb.vivant[:n] == 1)[0]


# ================================================================== la loi et le calendrier
def test_lois_et_calendrier():
    """Le systeme grec : maternelle 2 ans des 4 ans, primaire 6 ans des 6 ans, gymnase 3 ans des 12 ans, lycees 3 ans
    des 15 ans, medecine 6 ans ( 18 ans d etudes ). Annee 2035-2036 : de 165 a 185 jours de cours au primaire, de 150
    a 170 au secondaire, de 115 a 155 au superieur. Aucun cours le 25 decembre, le lundi de Paques, un mardi de
    juillet ; cours un mardi d octobre ordinaire ( controle positif : le calendrier sait dire oui )."""
    cal = CAL.Calendrier()
    loi = (tuple(M.DUREE[[M.MATERNELLE, M.PRIMAIRE, M.GYMNASE, M.LYCEE_GENERAL, M.LYCEE_PRO]]) == (2, 6, 3, 3, 3)
           and tuple(M.AGE_ENTREE[[M.MATERNELLE, M.PRIMAIRE, M.GYMNASE, M.LYCEE_GENERAL]]) == (4, 6, 12, 15)
           and M.ANNEES_REQUISES["medecine"] == 12 + M.DUREE_MEDECINE and M.ANNEES_REQUISES["lycee"] == 12)
    jp, js, ju = (M.jours_de_classe_annee(cal, 2035, g) for g in (M.PRIM, M.SECOND, M.SUP))
    pq = CAL.paques_orthodoxe(2036) + dt.timedelta(days=1)
    mardi_oct = next(dt.date(2035, 10, k) for k in range(12, 20) if dt.date(2035, 10, k).weekday() == 1)
    mardi_juil = next(dt.date(2036, 7, k) for k in range(1, 8) if dt.date(2036, 7, k).weekday() == 1)
    fermes = not any(M.jour_de_classe(cal, x, g) for x in (dt.date(2035, 12, 25), pq, mardi_juil) for g in (0, 1, 2))
    ouvert = all(M.jour_de_classe(cal, mardi_oct, g) for g in (0, 1, 2))
    ok = loi and 165 <= jp <= 185 and 150 <= js <= 170 and 115 <= ju <= 155 and fermes and ouvert
    return ok, (f"loi {loi} ; jours de cours 2035-2036 : primaire {jp}, secondaire {js}, superieur {ju} ; "
                f"Noel, lundi de Paques ( {pq} ), juillet fermes : {fermes} ; mardi {mardi_oct} ouvert : {ouvert}")


# ================================================================== scolarisation
def _mesures(p, ete):
    """Les taux de la statistique. `ete` : apres le passage de juin, un diplome du second cycle de 17 ans a fini sa
    scolarite ; la statistique ( Eurostat, sur l annee scolaire ) le compte scolarise : on le compte donc."""
    col = p.colonnes["habitant"]; tb = p.w.table
    s = M.scolarisation(p)
    ids = _vivants_ids(p)
    ages = M._ages(p, ids)
    dip = col["ed_diplomes"][ids].astype(np.int64); ins = col["ed_cycle"][ids] > 0
    if ete:
        b = (ages >= 15) & (ages < 18)
        fini = b & ~ins & ((dip & (M.BIT["lycee"] | M.BIT["epal"])) > 0)
        x, y = s[(15, 18)]
        s[(15, 18)] = (x + int(fini.sum()), y)
    j = (ages >= 18) & (ages < 25)
    sortants = j & ~ins & ((dip & (M.BIT["lycee"] | M.BIT["epal"] | M.BIT["iek"])) == 0)
    t = (ages >= 25) & (ages < 35)
    sup = t & ((dip & (M.BIT["universite"] | M.BIT["medecine"] | M.BIT["pedagogie"] | M.BIT["militaire"])) > 0)
    enf = ids[(tb.role[ids] == PO.CODE_ROLE["enfant"]) & (ages >= C.AGE_TRAVAIL)]
    hors = int((col["ed_cycle"][enf] == 0).sum())
    pas_etudiants = int(((col["ed_cycle"][enf] > 0) & (col["tr_statut"][enf] != TR.ETUDIANT)).sum())
    return s, sortants.sum() / max(1, j.sum()), sup.sum() / max(1, t.sum()), hors, pas_etudiants


def test_scolarisation():
    """Porte : taux de scolarisation dans les bandes grecques ( Eurostat, a verifier ) - 6-11 ans au moins 97 %,
    12-14 ans au moins 95 %, 15-17 ans de 85 a 98 %, 4-5 ans au moins 90 % s il y en a ; sortants precoces ( 18-24 ans,
    au plus le gymnase, hors ecole ; Grece 2023 : 3,7 % ) de 1 a 10 % ; diplomes du superieur a 25-34 ans ( ~ 44 % )
    de 35 a 55 %. A l installation ET apres le passage du 20 juin ( ou les bacheliers de 17 ans comptent scolarises,
    comme dans la statistique de l annee scolaire ). Coherence avec le domaine 4, apres l aube du 21 :
    aucun jeune de 16 ans et plus hors ecole encore enfant, tout inscrit de 16 ans et plus etudiant."""
    msgs, ok = [], True
    for nom, (w, p) in (("installation", _installe()), ("apres passage", _passe())):
        s, sortants, sup, hors, pas_etud = _mesures(p, nom == "apres passage")
        r = {k: (a / b if b else None) for k, (a, b) in s.items()}
        bon = (r[(6, 12)] >= 0.97 and r[(12, 15)] >= 0.95 and 0.85 <= r[(15, 18)] <= 0.98
               and (r[(4, 6)] is None or r[(4, 6)] >= 0.90) and 0.01 <= sortants <= 0.10 and 0.35 <= sup <= 0.55)
        if nom == "apres passage": bon = bon and hors == 0 and pas_etud == 0
        ok &= bon
        msgs.append(f"{nom} : " + ", ".join(f"{a}-{b - 1} ans {x}/{y}" + (f" ( {x / y:.1%} )" if y else "")
                                              for (a, b), (x, y) in s.items())
                    + f" ; sortants precoces {sortants:.1%} ; superieur 25-34 ans {sup:.1%} ; jeunes hors ecole encore "
                      f"enfants {hors}, inscrits non etudiants {pas_etud}")
    return ok, " || ".join(msgs)


# ================================================================== places et enseignants
def test_places():
    """Porte : dans chaque zone, les places des ecoles du domaine 13 ( 8 m2 par eleve ) couvrent les eleves de la
    maternelle au lycee ; le surplus est mesure, et le ratio eleves par enseignant ( cible grecque 9 ) rapporte. Le
    compte des eleves egale le recompte des cycles. Controle positif : les ecoles de la plus grande zone rendues
    inhabitables ( dommage 4, domaine 13 ) - le manque de places se voit, egal a ses eleves."""
    w, p = _installe()
    pl = M.mesurer_places(p)
    col = p.colonnes["habitant"]; n = p.w.table.n
    recompte = int((np.isin(col["ed_cycle"][:n], M.SCOLAIRES) & (p.w.table.vivant[:n] == 1)).sum())
    total = sum(e for _, e, _ in pl.values())
    couvre = all(a >= e for a, e, _ in pl.values())
    z = max(pl, key=lambda k: pl[k][1])
    for b in IM.batiments(p, "ecole"):
        if w.carte.lieux[IM.fiche(p, b)["lieu"]].n == z: IM.endommager(p, b, 4)
    pl2 = M.mesurer_places(p)
    vu = pl2[z][0] == 0 and pl2[z][1] == pl[z][1]
    ok = couvre and total == recompte and vu
    return ok, ("; ".join(f"{p.w.carte.par_n[k].id} {a} places pour {e} eleves ( surplus {a - e} ), {ens} enseignants, "
                          f"{e / max(1, ens):.1f} eleves par enseignant" for k, (a, e, ens) in sorted(pl.items()))
                + f" ; eleves {total}, recompte {recompte} ; ecoles de {p.w.carte.par_n[z].id} detruites : "
                  f"{pl2[z][0]} places pour {pl2[z][1]} eleves, vu {vu}")


# ================================================================== competences
def _annee_cohorte(n, rythme_x, present_p, graine=3):
    """Une cohorte de primaire ( 3e annee ) vit l annee 2035-2036 jour par jour avec les fonctions du domaine."""
    rng = np.random.default_rng(graine)
    cal = CAL.Calendrier()
    apt, hab = M.tirer_aptitudes(rng, n, rng.integers(0, 3, n))
    apt = apt.astype(float); hab = hab.astype(float)
    cyc = np.full(n, M.PRIMAIRE); an = np.full(n, 3)
    comp0 = M.attendu(cyc, an - 1) * np.column_stack((apt, apt, hab))
    comp = comp0.copy()
    ja = M.jours_de_classe_annee(cal, 2035, M.PRIM)
    jours = np.full(n, ja / rythme_x)
    x = dt.date(2035, 9, 1)
    while x <= dt.date(2036, 6, 15):
        if M.jour_de_classe(cal, x, M.PRIM):
            comp = M.pas_d_ecole(comp, cyc, apt, hab, np.zeros(n), jours, rng.random(n) < present_p)
        else:
            comp = M.pas_de_vacances(comp, 365 - ja)
        x += dt.timedelta(days=1)
    return (comp - comp0)[:, 0].mean()


def test_competences():
    """Porte, sur 3 000 eleves de primaire pendant l annee 2035-2036 ( fonctions du domaine ) : avec l instruction,
    la lecture monte de 0,8 a 1,1 annee ; sans ( absents tous les jours ), elle baisse. Controle positif : un rythme
    double donne 1,8 a 2,3 fois plus. Dans le monde, 4 jours de juin apres la fin des cours ( le 15 juin, premier jour
    du monde, est le dernier jour du primaire : la mesure part du 16 ) : aucune competence ne monte ( l ete n instruit
    pas ), et les inscrits oublient un peu ( les adultes en formation continuent d apprendre : hors mesure )."""
    avec = _annee_cohorte(3000, 1.0, 1.0 - M.P_ABSENCE)
    sans = _annee_cohorte(3000, 1.0, 0.0)
    double = _annee_cohorte(3000, 2.0, 1.0 - M.P_ABSENCE)
    w, p = _installe(); T.jours(w, 1)
    col = p.colonnes["habitant"]; n = p.w.table.n
    c0 = np.column_stack([col[k][:n].copy() for k in ("ed_lecture", "ed_calcul", "ed_technique")])
    T.jours(w, 4)
    c1 = np.column_stack([col[k][:n] for k in ("ed_lecture", "ed_calcul", "ed_technique")])
    ins = col["ed_cycle"][:n] > 0                    # les eleves ; les adultes en formation, eux, sont instruits l ete
    monte = float((c1 - c0)[ins].max())
    baisse = float((c1 - c0)[ins].mean())
    ok = 0.8 <= avec <= 1.1 and sans < 0 and 1.8 <= double / avec <= 2.3 and monte <= 0 and baisse < 0
    return ok, (f"lecture en un an : instruit {avec:+.3f} annee, absent {sans:+.3f}, rythme double {double:+.3f} "
                f"( x{double / avec:.2f} ) ; monde, 4 jours de juin : plus forte hausse d un eleve {monte:+.5f}, eleves en "
                f"moyenne {baisse:+.5f} annee")


# ================================================================== la rentree et les cours prives
def test_rentree_et_cours_prives():
    """Porte : un jour de cours impose dans le monde fait monter les presents et baisser les absents. A la rentree,
    60 a 95 % des lyceens de terminale generale prennent des cours prives ( KANEP-GSEE : ~ 80 %, a verifier ) ; le
    ministere demande dans chaque zone ses enseignants au ratio de 9 eleves. La facture d un mois passe du menage au
    marche de sa zone au centime, conservation tenue ; controle positif : douze factures de suite sans revenu, des
    menages ne peuvent plus payer et retirent leurs enfants."""
    w, p = _installe()
    d = p.domaine("education"); col = p.colonnes["habitant"]; tb = p.w.table; n = tb.n
    ins = np.nonzero((col["ed_cycle"][:n] > 0) & (tb.vivant[:n] == 1))[0]
    c0 = M.competences(p, ins); a0 = col["ed_absences"][ins].copy()
    M._ecole(p, forcer=(True, True, True))
    dc = (M.competences(p, ins) - c0).sum(axis=1); absent = col["ed_absences"][ins] > a0
    monte, baisse = float(dc[~absent].mean()), float(dc[absent].mean()) if absent.any() else 0.0
    M.rentree(p)
    g3 = ins[(col["ed_cycle"][ins] == M.LYCEE_GENERAL) & (col["ed_annee"][ins] == 3)]
    part = float(col["ed_frontistirio"][g3].mean())
    po = p.domaine("travail").postes_ouverts
    postes = all(po.get((p.w.carte.par_n[z].id, "enseignant")) == int(np.ceil(e / M.RATIO_CIBLE))
                 for z, (_, e, _) in M.places(p).items())
    nm = tb.menages.n
    m0 = np.cumsum(tb.menages.caisse[:nm])[-1]; k0 = np.cumsum([m.caisse for m in p.w.marches.values()])[-1]
    M._facturer_frontistiria(p, d, n)
    paye = d.paye_front
    m1 = np.cumsum(tb.menages.caisse[:nm])[-1]; k1 = np.cumsum([m.caisse for m in p.w.marches.values()])[-1]
    au_centime = abs((m0 - m1) - paye) < 0.01 and abs((k1 - k0) - paye) < 0.01
    inscrits = int(col["ed_frontistirio"][:n].sum())
    for _ in range(12): M._facturer_frontistiria(p, d, n)
    restent = int(col["ed_frontistirio"][:n].sum())
    tenue, msg = p.socle.conservation.tenue()
    ok = (monte > 0 and baisse < 0 and 0.60 <= part <= 0.95 and postes and au_centime and paye > 0 and tenue
          and restent < inscrits)
    return ok, (f"jour de cours : presents {monte:+.4f}, absents {baisse:+.4f} annee ( somme des trois competences ) ; "
                f"cours prives en terminale generale {part:.0%} ( {len(g3)} eleves ) ; postes d enseignants demandes au "
                f"ratio {postes} ( " + ", ".join(f"{p.w.carte.par_n[z].id} {po.get((p.w.carte.par_n[z].id, 'enseignant'))}"
                                               for z in sorted(M.places(p))) + f" ) ; un mois facture {paye:.0f} "
                f"drachmes, menages -{m0 - m1:.2f}, marches +{k1 - k0:.2f}, au centime {au_centime} ; inscrits aux cours "
                f"{inscrits}, apres douze factures sans revenu {restent} ; {msg}")


# ================================================================== diplome -> qualification
def test_diplome_donne_la_qualification():
    """Porte : un etudiant en 6e annee de medecine qui reussit recoit au passage du 20 juin le diplome de medecine et la
    qualification diplome_medecine du domaine 4, et a l aube suivante le domaine 4 le fait sortir des etudes vers le
    metier de medecin. Chaque diplome du superieur delivre au passage porte sa qualification ( aucun manque ), et aucune
    incoherence de titres n apparait."""
    w, p = _installe()
    col = p.colonnes["habitant"]; tb = p.w.table; n = tb.n
    cand = np.nonzero((tb.vivant[:n] == 1) & (tb.role[:n] == PO.CODE_ROLE["enfant"]) & (col["ed_annees"][:n] >= 12)
                      & (M._ages(p, np.arange(n)) >= 22))[0]
    i = int(cand[0])
    col["ed_cycle"][i] = M.UNIVERSITE; col["ed_annee"][i] = 6; col["ed_filiere"][i] = M.MEDECINE
    col["ed_annees"][i] = 17; col["ed_resultat"][i] = 1
    T.jours(w, 7)
    h = PO.Habitant(tb, i)
    a_dip = "medecine" in M.diplomes(p, h)
    a_q = "diplome_medecine" in TR.qualifications(p, h)
    sorti = int(col["tr_statut"][i]) != TR.ETUDIANT and h.role == "medecin"
    evs = [e for e in p.socle.journal.recents if e["type"] == "diplome_superieur"]
    manque = 0
    for e in evs:
        cy, fil = e["diplome"].split(":")
        x = PO.Habitant(tb, e["habitant"])
        attendu = {"medecine": "diplome_medecine", "soins": "diplome_infirmier", "pedagogie": "diplome_enseignant"}.get(fil) \
            if cy in ("universite", "iek") else {"ecole_militaire": "ecole_officiers", "ecole_police": "ecole_police"}.get(cy)
        if attendu and attendu not in TR.qualifications(p, x): manque += 1
    an = M.anomalies(p)
    ok = a_dip and a_q and sorti and manque == 0 and not an and len(evs) >= 10
    return ok, (f"etudiant {i} : diplome de medecine {a_dip}, qualification {a_q}, sorti des etudes medecin {sorti} "
                f"( role {h.role}, statut {TR.STATUTS[int(col['tr_statut'][i])]} ) ; {len(evs)} diplomes du superieur "
                f"au passage, {manque} sans leur qualification ; incoherences {len(an)}")


# ================================================================== examens
def test_examens():
    """Porte : au passage du 20 juin ( monde de 10 000 habitants ), les admis aux panhelleniques font de 55 a 85 % des
    candidats ( ~ 70 % en Grece depuis la note minimale de 2021, a verifier ), l apolytirio du gymnase est obtenu par
    95 a 99,5 % des eleves de 3e annee, le primaire est reussi par 99 % au moins. Les memes bandes sur 20 000 lyceens
    de terminale synthetiques ( fonctions du domaine ). Controle positif : des competences a 80 % font perdre au moins
    20 points d admission."""
    w, p = _passe()
    d = p.domaine("education")
    st = d.stats_passage[2034]
    adm = d.admis / max(1, d.candidats)
    gym = st["diplomes_gymnase"] / max(1, st["inscrits_gymnase_3"])
    prim = st["reussites_primaire"] / max(1, st["inscrits_primaire"])
    rng = np.random.default_rng(5)
    nn = 20000
    apt, hab = M.tirer_aptitudes(rng, nn, rng.integers(0, 3, nn))
    cyc = np.full(nn, M.LYCEE_GENERAL); an = np.full(nn, 3)
    comp = M.attendu(cyc, an) * np.column_stack((apt, apt, hab)).astype(float) * (1 + 0.1 * rng.standard_normal((nn, 3)))
    z = rng.standard_normal(nn)
    synth = float((M.noter_examen(comp, cyc, an, z) >= M.EBE).mean())
    faible = float((M.noter_examen(0.8 * comp, cyc, an, z) >= M.EBE).mean())
    ok = (0.55 <= adm <= 0.85 and 0.95 <= gym <= 0.995 and prim >= 0.99 and 0.55 <= synth <= 0.85
          and synth - faible >= 0.20)
    return ok, (f"monde : {d.admis}/{d.candidats} admis ( {adm:.1%} ), gymnase {st['diplomes_gymnase']}/"
                f"{st['inscrits_gymnase_3']} ( {gym:.1%} ), primaire {prim:.1%}, redoublements {d.redoublements}, "
                f"decrochages {d.decrochages}, orientations general/pro/arret {d.orientations} ; synthetiques : admis "
                f"{synth:.1%}, a 80 % des competences {faible:.1%}")


# ================================================================== falsificateurs
def test_falsificateurs():
    """Porte : le monde installe n a aucune incoherence de titres. Falsificateurs : une qualification de medecin posee
    a la main sur un adulte sans diplome est vue ; un diplome universitaire pose a la main sur un eleve de primaire
    est vu ; `delivrer` refuse un diplome a qui n a pas la scolarite."""
    w, p = _installe()
    col = p.colonnes["habitant"]; tb = p.w.table; n = tb.n
    propre = M.anomalies(p)
    ids = _vivants_ids(p)
    ages = M._ages(p, ids)
    a = int(ids[(ages >= 30) & ((col["ed_diplomes"][ids] & M.BIT["medecine"]) == 0)][0])
    TR.qualifier(p, PO.Habitant(tb, a), "diplome_medecine")
    vu1 = ("qualification_sans_diplome", a, "diplome_medecine") in M.anomalies(p)
    e = int(ids[col["ed_cycle"][ids] == M.PRIMAIRE][0])
    col["ed_diplomes"][e] |= M.BIT["universite"]
    vu2 = ("diplome_sans_scolarite", e, "universite") in M.anomalies(p)
    e2 = int(ids[col["ed_cycle"][ids] == M.PRIMAIRE][1])
    try: M.delivrer(p, e2, "medecine"); refuse = False
    except ValueError: refuse = True
    ok = not propre and vu1 and vu2 and refuse
    return ok, (f"incoherences a l installation {len(propre)} ; qualification sans diplome vue {vu1} ; diplome sans "
                f"scolarite vu {vu2} ; delivrer sans scolarite refuse {refuse}")


# ================================================================== la decision
def test_orientation():
    """Porte de la decision : 1 600 fins de gymnase dans 4 etablissements ( scenario du domaine, 365 jours de note ),
    orientation au hasard : la note depend du choix ( epsilon carre >= 0,01 ) et le hasard permute ne fait pas aussi
    bien ( p < 0,05 ), avec au moins 1 000 notes. Rapporte la regle et le temoin sur les memes eleves, et le nombre
    de decisions prises dans le monde au passage du 20 juin."""
    dec = M.scenario_orientation(1600, 4, 7, "hasard")
    part = dec.part_du_choix(); pp = dec.p_permutation()
    notes = dec.notes_par_action()
    nb = sum(k for k, _ in notes.values())
    moy = {}
    for mode in ("regle", "temoin"):
        d2 = M.scenario_orientation(1600, 4, 7, mode)
        tot = sum(k * m for k, m in d2.notes_par_action().values()); cnt = sum(k for k, _ in d2.notes_par_action().values())
        moy[mode] = tot / max(1, cnt)
    w, p = _passe()
    dm = p.domaine("education").decideur
    ok = part >= 0.01 and pp < 0.05 and nb >= 1000
    return ok, (f"{dec.n_decisions} decisions, {nb} notes ; " + ", ".join(f"{a} {m:.3f} ( {k} )" for a, (k, m) in notes.items())
                + f" ; part du choix {part:.3f}, p {pp:.3f} ; note moyenne regle {moy['regle']:.3f}, temoin ( toujours "
                  f"general ) {moy['temoin']:.3f} ; monde : {dm.n_decisions} orientations au passage")


# ================================================================== la formation des adultes
def test_formation():
    """Porte du cycle instruction -> exercice -> debrief -> qualification : 2 000 habitants, 30 chomeurs sans permis
    inscrits le 15 juin a un programme de permis court declare par l API des domaines 25 et 27 ( 8 jours
    d instruction, 5 d exercice, 1 de debrief ; le programme DYPA de 28 jours ne finit pas avant la fermeture d aout
    avec l epidemie du moteur ), vivent 45 jours. Ceux qui reussissent l epreuve ont le diplome et la
    qualification permis_poids_lourd du domaine 4 ; ceux qui echouent ne l ont pas ; de 40 a 95 % de reussite ; l Etat
    a verse des allocations. Controle positif : 10 autres, qui n apprennent pas ( habilete 0,05 ), reussissent a 20 %
    au plus. L ecole du moteur etendue : un eleve sans memoire n obtient pas le diplome civique."""
    w, p = T.monde(["education"], echelle=4)
    col = p.colonnes["habitant"]; tb = p.w.table; n = tb.n
    ch = np.nonzero((tb.vivant[:n] == 1) & (col["tr_statut"][:n] == TR.CHOMEUR)
                    & ((col["tr_qualifs"][:n] & TR.BIT["permis_poids_lourd"]) == 0))[0][:40]
    normaux, lents = ch[:30].tolist(), ch[30:40].tolist()
    for i in lents: col["ed_habilete"][i] = 0.05
    M.declarer_programme(p, "essai_permis", "tests", 8, 5, 1, 2, 0.5, "poids_lourd", M.SEUIL_PERMIS,
                         allocation=M.ALLOCATION_FORMATION_J)
    for i in normaux + lents: M.inscrire_formation(p, PO.Habitant(tb, i), "essai_permis")
    T.jours(w, 45)
    def bilan(ids):
        fini = [i for i in ids if i not in p.domaine("education").stagiaires and tb.vivant[i]]
        q = [i for i in fini if col["tr_qualifs"][i] & TR.BIT["permis_poids_lourd"]]
        d_ = [i for i in fini if col["ed_diplomes"][i] & M.BIT["poids_lourd"]]
        return fini, q, d_
    f1, q1, d1 = bilan(normaux); f2, q2, d2 = bilan(lents)
    coherent = set(q1) == set(d1) and set(q2) == set(d2)
    t1 = len(q1) / max(1, len(f1)); t2 = len(q2) / max(1, len(f2))
    dm = p.domaine("education")
    paye = dm.qualifies + dm.echoues
    s_temoin, dlv = M.former_agent(p, int(normaux[0]), ECOLE.EleveSansMemoire(), jours=3)
    s_mem, dlv_mem = M.former_agent(p, int(normaux[1]), ECOLE.EleveMemoire(), jours=3)
    ok = (len(f1) >= 25 and coherent and 0.40 <= t1 <= 0.95 and t2 <= 0.20 and paye >= 35 and dm.allocations > 0
          and not dlv)
    return ok, (f"formes {len(f1)}/30 : {len(q1)} qualifies ( {t1:.0%} ), diplome = qualification {coherent} ; sans "
                f"apprentissage {len(q2)}/{len(f2)} ( {t2:.0%} ) ; epreuves passees {paye} ; allocations "
                f"{dm.allocations:.0f} drachmes ; ecole du moteur : eleve sans "
                f"memoire {s_temoin:.2f} ( diplome {dlv} ), eleve a memoire {s_mem:.2f} ( diplome {dlv_mem} )")


# ================================================================== la porte commune et le cout
def test_pays_vivable():
    return T.porte_commune("education", n_jours=12)


def test_cout():
    """Le domaine coute au plus 25 % d une journee du moteur ( coeur Rust ), a 10 000 habitants, un jour de cours
    ordinaire ( impose : le monde commence en juin ) ; examens, passage et rentree ( une fois par an ) au plus une
    journee du moteur. Installer l education a 100 000 habitants coute au plus 15 fois l installation a 10 000."""
    coeur = W.COEUR is not None
    w0 = W.Monde(echelle=20); T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    w, p = _installe(); T.jours(w, 1)
    t0 = time.perf_counter()
    for _ in range(3):
        M._inscrire_formations(p); M._ecole(p, forcer=(True, True, True)); M._formations(p); M._noter(p); M._nuit(p)
    propre = (time.perf_counter() - t0) / 3
    t0 = time.perf_counter(); M.examiner(p); M.passer(p); M.rentree(p); annuel = time.perf_counter() - t0
    def installation(ech):
        wx = W.Monde(echelle=ech); P.installer(wx, ["travail", "immobilier", "etat"])
        t = time.perf_counter(); P.installer(wx, ["education"]); return time.perf_counter() - t, wx.table.n
    t10, n10 = installation(20); t100, n100 = installation(200)
    ok = coeur and propre <= 0.25 * t_e1 and annuel <= t_e1 and t100 <= 15 * t10
    return ok, (f"coeur Rust {coeur} ; {p.w.table.n} habitants : moteur seul {t_e1:.2f} s par jour ; routines propres "
                f"( jour de cours ) {propre * 1000:.0f} ms, {propre / t_e1:.1%} ; examens, passage et rentree {annuel * 1000:.0f} ms ; "
                f"installation {n10} habitants {t10:.2f} s, {n100} habitants {t100:.2f} s ( x{t100 / t10:.1f} )")


TESTS = [test_lois_et_calendrier, test_scolarisation, test_places, test_competences, test_rentree_et_cours_prives,
         test_diplome_donne_la_qualification,
         test_examens, test_falsificateurs, test_orientation, test_formation, test_pays_vivable, test_cout]
