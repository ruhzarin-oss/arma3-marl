"""Les portes du domaine 24 ( politique : partis, opinion, sondages, elections ). Seuils ecrits avant la premiere mesure.
python -m monde.pays.tests politique"""
import itertools, pickle, time
import numpy as np
from .. import config as C, monde as W
from ..socle import registre as R
from . import essais as T, pays as P, d06_etat as ET, d22_medias as ME, d24_politique as M

_CACHE = {}
UL, GN, VN, RS = 4, 1, 5, 2


def _monde(jours=0, echelle=5, graine=11, modes=None, autres=()):
    """Un monde avec la politique ( et `autres` ) apres `jours` jours ; chaque porte en reprend une copie."""
    k = (jours, echelle, graine, tuple(sorted((modes or {}).items())), tuple(autres))
    if k not in _CACHE:
        w, p = T.monde([M.DOMAINE] + list(autres), graine, echelle, modes=modes)
        T.jours(w, jours)
        _CACHE[k] = pickle.dumps(w)
    w = pickle.loads(_CACHE[k])
    return w, w.pays


def _jusqu_a(w, heure):
    for _ in range(C.PAS_PAR_JOUR + 1):
        if abs(w.heure - heure) < 1e-6: return
        w.pas_suivant()
    raise RuntimeError(f"heure {heure} jamais atteinte")


def _residents(p, lieu):
    tb = p.w.table; n = tb.n
    return np.nonzero((tb.vivant[:n] == 1) & (tb.domicile[:n] == lieu))[0]


def _lieu_peuple(p):
    """Le lieu habite le plus peuple qui n est pas la capitale."""
    d = p.domaine(M.DOMAINE)
    return max((l for l in np.nonzero(d.habitable)[0].tolist() if l != d.capitale),
               key=lambda l: (len(_residents(p, l)), -l))


def _part_gouv_lieu(p, l):
    d = p.domaine(M.DOMAINE)
    return float(d.part_lieu[d.gouv, l].sum())


def _attendu(p):
    """Les parts attendues du pays avec l etat de maintenant ( la verite d un sondage )."""
    d = p.domaine(M.DOMAINE)
    ids = M._electeurs(p)
    Tv, Pk = M._probas(d, M._entrees(p, d, ids, M._Menages(p)))
    return (Tv[:, None] * Pk).sum(0) / Tv.sum()


# ================================================================== la loi electorale
JUIN_2023 = [2115322, 930013, 617487, 401187, 243922, 231494, 193044, 165516, 128048, 189267]   # + autres listes
JUIN_LISTES = [1] * 9 + [0]
JUIN_SIEGES = [158, 47, 32, 21, 12, 12, 10, 8, 0, 0]
MAI_2023 = [2407860, 1184415, 676166, 426628, 262563, 153934, 791434]
MAI_LISTES = [1] * 6 + [0]
MAI_SIEGES = [146, 71, 41, 26, 16, 0, 0]


def test_sieges_loi_grecque():
    """Resultats connus ( ministere de l Interieur ) : 25 juin 2023 sous la loi 4804/2021 ( ND 158, SYRIZA 47, PASOK 32,
    KKE 21, Spartiates 12, Solution grecque 12, Niki 10, Plefsi 8, MeRA25 0 a 2,46 % : prime de 50 ) ; 21 mai 2023 sous la
    loi 4406/2016 ( ND 146, SYRIZA 71, PASOK 41, KKE 26, Solution grecque 16, MeRA25 0 a 2,61 % ). Exacts au siege. Prime :
    0 a 24,99 %, 20 a 25 %, 30 a 30 %, 44 a 37,49 %, 50 a 40 % et a 45 %, 0 sous la loi 4406/2016 ; sur 200 sieges, 33 a
    40 %. Sur 300 tirages de voix au hasard ( 200 sieges ) : le total fait toujours 200, aucune liste sous 3 % ni les
    petites listes n ont de siege. Sieges du pays : 200 a 2 500 habitants, 300 pour la Grece. Coalitions : ( UL, VN ) quand
    UL 90 et VN 15 sur 200 ; ( UL, RS ) quand VN n a que 10 ; aucune quand seuls des partis incompatibles font la
    majorite ; le parti communiste n entre dans aucune."""
    s1, b1, _ = M.repartir_sieges(JUIN_2023, JUIN_LISTES, 300, "4804/2021")
    s2, b2, _ = M.repartir_sieges(MAI_2023, MAI_LISTES, 300, "4406/2016")
    juin, mai = s1.tolist() == JUIN_SIEGES and b1 == 50, s2.tolist() == MAI_SIEGES and b2 == 0
    primes = [M.prime(x) for x in (0.2499, 0.25, 0.30, 0.3749, 0.40, 0.45)]
    prime_ok = primes == [0, 20, 30, 44, 50, 50] and M.prime(0.45, "4406/2016") == 0 and M.prime(0.40, S=200) == 33
    rng = np.random.default_rng(1)
    total_ok = True
    for _ in range(300):
        v = (rng.dirichlet(np.full(7, 0.6)) * 10000).astype(np.int64)
        lst = np.array([1, 1, 1, 1, 1, 1, 0], bool)
        s, _, _ = M.repartir_sieges(v, lst, 200)
        petits = (v < 0.03 * v.sum()) | ~lst
        total_ok &= int(s.sum()) == 200 and not (s[petits] > 0).any()
    pays_ok = M.sieges_pour(2500) == 200 and M.sieges_pour(M.POPULATION_GRECE) == 300
    lr = [((1 - i) + (1 - s_) + o + m) / 4 for _, _, i, s_, o, m, *_ in M.PARTIS]
    rf = [x[8] for x in M.PARTIS]
    c1 = M.former_coalition([15, 50, 30, 0, 90, 15, 0], lr, rf, 101)
    c2 = M.former_coalition([20, 50, 30, 0, 90, 10, 0], lr, rf, 101)
    c3 = M.former_coalition([40, 80, 0, 0, 70, 10, 0], lr, rf, 101)
    c4 = M.former_coalition([60, 45, 0, 0, 0, 0, 0], lr, rf, 101)
    coal_ok = c1 == (UL, VN) and c2 == (UL, RS) and c3 is None and c4 is None
    ok = juin and mai and prime_ok and total_ok and pays_ok and coal_ok
    return ok, (f"juin 2023 {s1.tolist()} prime {b1} ( {juin} ) ; mai 2023 {s2.tolist()} ( {mai} ) ; primes {primes} "
                f"( {prime_ok} ) ; 300 tirages a 200 sieges {total_ok} ; sieges du pays {M.sieges_pour(2500)} / "
                f"{M.sieges_pour(M.POPULATION_GRECE)} ; coalitions {c1} {c2} {c3} {c4} ( {coal_ok} )")


# ================================================================== l opinion
def test_opinion_initiale():
    """Trois jours, 2 500 habitants. Les parts attendues des six listes restent a 4 points au plus de juin 2023 ( le
    calage de l installation ) ; l abstention est de 30 a 50 % ; les 17-34 ans s abstiennent d au moins 5 points de plus
    que les 55 ans et plus ; la part du sortant varie d au moins 5 points entre les lieux de 20 electeurs et plus ( la
    geographie du vote ) ; les parts font 1 ; de 35 a 55 % des electeurs sont identifies a un parti ; aucune anomalie."""
    w, p = _monde(3)
    d = p.domaine(M.DOMAINE)
    it = M.intentions(p)
    ecarts = [abs(it[x.nom] - x.cible) for x in d.partis if x.liste]
    abst = it["abstention"]
    jeunes = [M.intentions(p, groupe=g)["abstention"] for g in (0, 3, 6)]
    vieux = [M.intentions(p, groupe=g)["abstention"] for g in (2, 5, 8)]
    ins = d.inscrits.sum(0)
    aj = 1 - sum(d.attendus.sum(0)[g] for g in (0, 3, 6)) / sum(ins[g] for g in (0, 3, 6))
    av = 1 - sum(d.attendus.sum(0)[g] for g in (2, 5, 8)) / sum(ins[g] for g in (2, 5, 8))
    grands = np.nonzero(d.electeurs_l >= 20)[0]
    ul = d.part_lieu[UL, grands]
    somme = abs(sum(v for k, v in it.items() if k != "abstention") - 1.0)
    ids = M._electeurs(p)
    ident = float((p.col("habitant", "pol_ident")[ids] >= 0).mean())
    ok = (max(ecarts) <= 0.04 and 0.30 <= abst <= 0.50 and aj - av >= 0.05 and ul.max() - ul.min() >= 0.05
          and somme <= 1e-9 and 0.35 <= ident <= 0.55 and not M.anomalies(p))
    return ok, (f"parts {', '.join(f'{x.nom[:6]} {it[x.nom]:.3f}' for x in d.partis)} ; pire ecart {max(ecarts):.3f} ; "
                f"abstention {abst:.1%} ( 17-34 ans {aj:.1%}, 55 ans et plus {av:.1%} ) ; sortant par lieu de {ul.min():.3f} a "
                f"{ul.max():.3f} sur {len(grands)} lieux ; identifies {ident:.1%} ; calage {d.calibrage}")


def test_griefs_crus():
    """Regle 3, controle positif. Mondes apparies apres 2 jours, dans le lieu le plus peuple hors capitale : B, une
    contamination de l eau vue de ses residents ( `constater`, temoins du lieu ) ; C, le meme fait sans temoin ni
    communique ( vrai, inconnu ). Trois jours apres : part du gouvernement dans ce lieu B - A <= -0,01 ; |C - A| <= 0,2 x
    |B - A| ; personne ne sait le fait de C. L instrument : dans B, les griefs lus en colonnes egalent, lieu par lieu, la
    somme tiree de `ME.climat` ( sujets gouvernementaux negatifs hors statistique ) a 1e-9 pres, et le lieu choque en a."""
    w0, p0 = _monde(2)
    X = _lieu_peuple(p0)
    snap = pickle.dumps(w0)
    wa, wb, wc = (pickle.loads(snap) for _ in range(3))
    ME.constater(wb.pays, "contamination_eau", X, 1.0, temoins="lieu")
    fid = ME.constater(wc.pays, "contamination_eau", X, 1.0, temoins=0, officiel=False)
    for w_ in (wa, wb, wc): T.jours(w_, 3)
    g = [_part_gouv_lieu(w_.pays, X) for w_ in (wa, wb, wc)]
    db, dc = g[1] - g[0], g[2] - g[0]
    inconnu = ME.part_nationale(wc.pays, fid) == 0.0
    pb = wb.pays; d = pb.domaine(M.DOMAINE); me = pb.domaine("medias")
    lu = M.croyances_politiques(pb)[M.GRIEFS]
    ref = np.zeros(d.L)
    for l in range(d.L):
        ref[l] = sum(i * -v for s, (i, v) in ME.climat(pb, l).items()
                     if v < 0 and me.table_sujets[s][1] and s not in M.SUJETS_STATS)
    exact = bool(np.all(np.abs(lu - ref) <= 1e-9 * np.maximum(1.0, np.abs(ref)))) and ref[X] > 0.1
    ok = db <= -0.01 and abs(dc) <= 0.2 * abs(db) and inconnu and exact
    return ok, (f"{d.lieu_ids[X]} : part du gouvernement {g[0]:.4f} ; contamination crue {db:+.4f} ; inconnue {dc:+.4f} "
                f"( sue de personne : {inconnu} ) ; griefs lus = climat {exact} ( {d.lieu_ids[X]} {ref[X]:.3f}, pire ecart "
                f"{np.abs(lu - ref).max():.1e} )")


def test_situation_propre():
    """Controle positif sur la situation de l electeur : dans le monde B, 30 menages ont faim chaque soir pendant 3 jours
    ( faim de la semaine posee a 22 h ). Au matin : probabilite de choisir le gouvernement de leurs electeurs B - A <=
    -0,03 ; celle des autres electeurs ne bouge pas ( |B - A| moyen <= 0,005 )."""
    w0, p0 = _monde(2)
    tb = w0.table; n = tb.n
    ids = M._electeurs(p0)
    mg = tb.menage[ids].astype(np.int64)
    cands = np.unique(mg[mg >= 0])
    choisis = np.sort(np.random.default_rng(3).permutation(cands)[:30])
    snap = pickle.dumps(w0)
    wa, wb = pickle.loads(snap), pickle.loads(snap); pb = wb.pays
    for _ in range(3):
        for w_ in (wa, wb): _jusqu_a(w_, 22.0)
        pb.col("menage", "faim7")[choisis] = 0x7F
        for w_ in (wa, wb): w_.pas_suivant()
    for w_ in (wa, wb): _jusqu_a(w_, 6.0)
    pa = wa.pays
    ids = M._electeurs(pa)
    ids = ids[np.isin(ids, M._electeurs(pb))]
    touche = np.isin(wb.table.menage[ids], choisis)
    da = pa.domaine(M.DOMAINE)
    _, Pa = M.probabilites(pa, ids); _, Pb = M.probabilites(pb, ids)
    ga, gb = Pa[:, da.gouv].sum(1), Pb[:, pb.domaine(M.DOMAINE).gouv].sum(1)
    dt, do = float((gb - ga)[touche].mean()), float((gb - ga)[~touche].mean())
    ok = dt <= -0.03 and abs(do) <= 0.005
    return ok, f"{int(touche.sum())} electeurs affames : gouvernement B - A {dt:+.4f} ; {int((~touche).sum())} autres {do:+.5f}"


# ================================================================== les sondages
def test_sondage_erreur():
    """Trois jours, 2 500 habitants. 300 sondages du meme pays ( graines distinctes ) : l ecart-type de l estimation du
    premier parti est entre 0,8 x l ecart-type du tirage sans remise ( correction de population finie ) et 1,2 x celui
    du tirage avec remise, pour les repondants qui votent ; la marge publiee a 95 % couvre la verite ( parts attendues
    de tout le pays ) dans 90 a 99 % des sondages ; le biais moyen est sous 3 erreurs types. Publication : quatre jours
    apres le premier sondage publie, le fait `sondage` est cru dans la capitale par 10 % au moins."""
    w, p = _monde(3)
    d = p.domaine(M.DOMAINE)
    vrai = _attendu(p)
    k = int(np.argmax(vrai))
    est, marge, nv = [], [], []
    for i in range(300):
        s = M.sonder(p, rng=np.random.default_rng(1000 + i))
        est.append(s["parts"][k]); marge.append(s["marges"][k]); nv.append(s["votants"])
    est, marge = np.array(est), np.array(marge)
    n, N, nvm = s["n"], s["N"], float(np.mean(nv))
    sd_srs = np.sqrt(vrai[k] * (1 - vrai[k]) / nvm)
    fpc = np.sqrt((N - n) / (N - 1))
    sd = float(est.std(ddof=1))
    couvre = float((np.abs(est - vrai[k]) <= marge).mean())
    biais = abs(est.mean() - vrai[k])
    ok_err = 0.8 * sd_srs * fpc <= sd <= 1.2 * sd_srs and 0.90 <= couvre <= 0.99 and biais <= 3 * sd / np.sqrt(300)
    w2, p2 = _monde(0)
    d2 = p2.domaine(M.DOMAINE)
    T.jours(w2, 8)
    sus = ME.croyance(p2, d2.capitale, "sondage")
    part = max((e["part"] for e in sus), default=0.0)
    publie = len(d2.sondages) >= 1 and part >= 0.10
    ok = ok_err and publie
    return ok, (f"{d.partis[k].nom} vrai {vrai[k]:.4f} ; 300 sondages de {n} sur {N} ( {nvm:.0f} votants ) : ecart-type "
                f"{sd:.4f} dans [ {0.8 * sd_srs * fpc:.4f} ; {1.2 * sd_srs:.4f} ] ; couverture {couvre:.1%} ; biais "
                f"{biais:.4f} ; {len(d2.sondages)} sondages publies, le plus su cru par {part:.0%} de la capitale")


# ================================================================== l election et le gouvernement
def _elire(w, p, dans_j):
    j = M.convoquer(p, dans_j)
    T.jours(w, j - p.jour + 2)
    return j


def test_alternance_et_bornes():
    """Mondes apparies apres 2 jours, elections anticipees convoquees a 7 jours. Dans B, la gauche radicale gagne 2 points
    d utilite ( un effet pose a la main : le controle positif de la chaine vote -> sieges -> gouvernement -> lois ). Le
    scrutin tombe un dimanche, la participation est de 45 a 75 %. B : la gauche radicale arrive en tete et gouverne, sans
    le sortant ; ses lois vont vers son programme par rapport a A ( TVA normale, IR de la derniere tranche, facteur des
    salaires publics plus hauts ) ; toutes les lois sont dans les bornes du domaine 6 ; aucune action d investiture
    refusee, au moins 5 acceptees. A : le sortant reste chef du gouvernement. Bornes : les 16 programmes extremes ont des
    cibles dans les bornes ; une TVA de 40 % est refusee par le domaine 6 ; un programme hors [0 ; 1] est refuse a la
    construction. Regle du matin : un programme social subventionne quand la faim se publie, le sortant non."""
    w0, p0 = _monde(2)
    snap = pickle.dumps(w0)
    wa, wb = pickle.loads(snap), pickle.loads(snap)
    pa, pb = wa.pays, wb.pays
    pb.domaine(M.DOMAINE).constante[GN] += 2.0
    ja = _elire(wa, pa, 7); jb = _elire(wb, pb, 7)
    da, db = pa.domaine(M.DOMAINE), pb.domaine(M.DOMAINE)
    sa, sb = da.scrutins[-1], db.scrutins[-1]
    wd = (pb.socle.calendrier.jour_semaine(wb.pas) + (sb.jour - pb.jour)) % 7
    part = sb.votants.sum() / sb.inscrits.sum()
    eb, ea = M.executif(pb), M.executif(pa)
    la, lb = M.lois_en_vigueur(pa), M.lois_en_vigueur(pb)
    fb = pb.domaine("etat").fisc
    bornes = (0.15 <= lb["tva_normale"] <= 0.27 and lb["tva_reduite"] <= lb["tva_normale"] and lb["ir_avant"] <= lb["ir_haut"]
              <= 0.55 and 0.10 <= lb["is"] <= 0.35 and 0.5 <= lb["salaires"] <= 2.0 and 0.0 <= lb["controle"] <= 1.0
              and all(fb.taux_ir[j] <= fb.taux_ir[j + 1] for j in range(len(fb.taux_ir) - 1)))
    inv = [a for a in db.actions if a[1] == "investiture"]
    acc = sum(1 for a in inv if a[3])
    sens = lb["tva_normale"] > la["tva_normale"] and lb["ir_haut"] > la["ir_haut"] and lb["salaires"] > la["salaires"]
    alternance = sb.premier == GN and eb["chef"] == "gauche_nouvelle" and "union_liberale" not in eb["partis"]
    stable = ea["chef"] == "union_liberale"
    ref = db.programme_ref
    extremes = True
    for prog in itertools.product((0.0, 1.0), repeat=4):
        c = M.cibles_du_programme(prog, ref, db.lois_ref, lb)
        extremes &= (0.15 <= c["tva_normale"] <= 0.27 and c["ir_haut"] <= 0.55 and 0.10 <= c["is"] <= 0.35
                     and 0.5 <= c["salaires"] <= 2.0 and 0.0 <= c["controle"] <= 1.0 and c["defense"] >= 0)
    refuse, _ = ET.appliquer(pb, {"type": "fixer_tva", "categorie": "normale", "valeur": 0.40})
    try: M.Executif((0,), (1.2, 0.5, 0.5, 0.5), 0, "x", {}, 0); construit = True
    except ValueError: construit = False
    pub = {"enquete": {"faim_menages": 100.0}}
    regle = (len(M.regle_du_gouvernement(pub, db.partis[GN].axes, 2500)) == 1
             and not M.regle_du_gouvernement(pub, db.partis[UL].axes, 2500))
    ok = (wd == 6 and 0.45 <= part <= 0.75 and alternance and stable and sens and bornes and not db.refus and acc >= 5
          and extremes and not refuse and not construit and regle)
    return ok, (f"scrutin le jour {sb.jour} ( dimanche {wd == 6} ), participation {part:.1%} ; B : voix {sb.voix_nat.tolist()}, "
                f"sieges {sb.sieges.tolist()}, gouvernement {eb['partis']} ; A : {sa.sieges.tolist()}, {ea['partis']} ; lois "
                f"B / A : TVA {lb['tva_normale']:.3f} / {la['tva_normale']:.3f}, IR {lb['ir_haut']:.3f} / {la['ir_haut']:.3f}, "
                f"IS {lb['is']:.3f}, salaires {lb['salaires']:.3f} / {la['salaires']:.3f}, controle {lb['controle']:.2f} ; "
                f"bornes {bornes}, {acc} actions acceptees, refus {len(db.refus)} ; extremes {extremes} ; TVA 40 % refusee "
                f"{not refuse} ; programme 1,2 refuse {not construit} ; regle du matin {regle}")


def test_falsificateur_scrutin():
    """Falsificateur. Un scrutin anticipe ( 3 jours ) : aucune anomalie, les signatures de la colonne font les votants.
    Un bulletin ajoute a la main dans un bureau se voit ( vote sans electeur ) ; un siege passe d une liste a une liste
    sans voix se voit ( siege sans vote ) ; une signature effacee se voit ( emargement ) ; tout remis, plus rien."""
    w, p = _monde(1)
    _elire(w, p, 3)
    d = p.domaine(M.DOMAINE); s = d.scrutins[-1]
    propre = not M.anomalies(p)
    l = int(np.argmax(s.votants)); k = int(np.argmax(s.voix_nat))
    s.voix[l, k] += 1
    vu_vote = any(a[0] == "vote_sans_electeur" and a[2] == d.lieu_ids[l] for a in M.anomalies(p))
    s.voix[l, k] -= 1
    s.sieges[k] -= 1; s.sieges[M._indice(d, "divers")] += 1
    vu_siege = any(a[0] == "siege_sans_vote" for a in M.anomalies(p))
    s.sieges[k] += 1; s.sieges[M._indice(d, "divers")] -= 1
    em = p.col("habitant", "pol_emarge")
    i = int(np.nonzero(em[:w.table.n] == s.numero)[0][0])
    em[i] = 0
    vu_em = any(a[0] == "emargement" for a in M.anomalies(p))
    em[i] = s.numero
    rendu = not M.anomalies(p)
    ok = propre and vu_vote and vu_siege and vu_em and rendu
    return ok, (f"scrutin {s.numero} : {int(s.votants.sum())} votants sur {int(s.inscrits.sum())} inscrits, {int(s.blancs.sum())} "
                f"blancs et nuls, sieges {s.sieges.tolist()} ; propre {propre} ; bulletin ajoute vu {vu_vote} ; siege deplace vu "
                f"{vu_siege} ; signature effacee vue {vu_em} ; remis propre {rendu}")


# ================================================================== l argent
def test_financement_au_centime():
    """Trente et un jours, 2 500 habitants, elections convoquees a 20 jours ( supplement electoral, tournees, scrutin ).
    La famille des partis se rapproche du grand livre ( reste nul ) ; pour chaque motif du domaine, ce que le domaine a
    compte = ce que le grand livre a vu, au centime ; chaque versement public est exactement la cle des voix fois le
    total ( 1e-9 relatif ), la cle faisant 90 % ( ou 100 % avec des listes de 1,5 % sans siege ) ; il y a eu un versement
    mensuel et un supplement electoral, des depenses de campagne et des cotisations ; la conservation tient.
    Falsificateur : 5 drachmes retirees a la main d un parti se voient."""
    w, p = _monde(0)
    d = p.domaine(M.DOMAINE); L = p.socle.livre
    rap = R.Rapprochement(p.socle.registre, L)
    n0 = len(d.financements)
    M.convoquer(p, 20)
    T.jours(w, 31)
    restes = rap.restes()
    rap_ok = abs(restes["partis_politiques"]) <= R.tolerance(restes["partis_politiques"]) + 1e-9
    ecarts = {m: d.compte.get(m, 0.0) - d.livre_motifs.get(m, 0.0) for m, _ in M.MOTIFS}
    centime = all(abs(x) <= 0.005 for x in ecarts.values())
    cle_ok = True
    for jour, quoi, total, verse, parts in list(d.financements)[n0:]:
        s_ = sum(parts.values())
        cle_ok &= abs(sum(verse.values()) - s_) <= 1e-9 * max(1.0, s_)
        cle_ok &= all(abs(verse.get(k, 0.0) - v) <= 1e-9 * max(1.0, v) for k, v in parts.items())
        f = s_ / total if total > 0 else 0.0
        cle_ok &= abs(f - 0.9) <= 1e-9 or abs(f - 1.0) <= 1e-9
    quoi = [x[1] for x in list(d.financements)[n0:]]
    tenue, msg = p.socle.conservation.tenue()
    x = max(d.partis, key=lambda y: y.caisse)
    x.caisse -= 5.0
    vu = abs(rap.restes()["partis_politiques"] + 5.0) <= 1e-6
    ok = (rap_ok and centime and cle_ok and "mensuel" in quoi and "supplement_electoral" in quoi
          and d.compte["campagne_electorale"] > 0 and d.compte["cotisation_parti"] > 0 and tenue and vu)
    pire = max(ecarts, key=lambda m: abs(ecarts[m]))
    return ok, (f"reste {restes['partis_politiques']:+.1e} ; motifs au centime {centime} ( pire {pire} {ecarts[pire]:+.1e} ) ; "
                f"versements {quoi} exacts {cle_ok} ; public {d.compte['financement_partis']:.0f} dr, cotisations "
                f"{d.compte['cotisation_parti']:.0f}, campagne {d.compte['campagne_electorale']:.0f} ; {msg} ; parti vide a la "
                f"main vu {vu}")


# ================================================================== la contestation
def test_contestation():
    """Controle positif, avec le domaine 4. Mondes apparies apres 2 jours ; dans B, chaque lieu habite voit une
    contamination de l eau, une penurie de medicaments et une restriction d eau ( temoins du lieu ). En trois jours : B a au
    moins 3 manifestations et 10 manifestants, et une greve generale politique ( greve_debut, motif politique, domaine
    4 ) ; A n a ni manifestation ni greve politique."""
    w0, p0 = _monde(2, autres=("travail",))
    snap = pickle.dumps(w0)
    wa, wb = pickle.loads(snap), pickle.loads(snap)
    pb = wb.pays; d0 = pb.domaine(M.DOMAINE)
    for l in np.nonzero(d0.habitable & (d0.electeurs_l > 0))[0].tolist():
        for sujet in ("contamination_eau", "penurie_medicaments", "restriction_eau"):
            ME.constater(pb, sujet, l, 1.0, temoins="lieu")
    for w_ in (wa, wb): T.jours(w_, 3)
    def compte(w_):
        d = w_.pays.domaine(M.DOMAINE)
        m = [x for x in d.manifs if x[0] >= 2]
        g = [e for e in w_.pays.socle.journal.derniers("greve_debut", n=1000) if e.get("motif") == "politique"]
        return len(m), sum(x[2] for x in m), len(g), float(d.griefs[d.electeurs_l > 0].mean())
    ma, pa_, ga, gra = compte(wa); mb, pb_, gb, grb = compte(wb)
    ok = mb >= 3 and pb_ >= 10 and gb >= 1 and ma == 0 and ga == 0
    return ok, (f"B : {mb} manifestations, {pb_} manifestants, {gb} greves politiques, griefs moyens {grb:.3f} ; A : {ma}, "
                f"{pa_}, {ga}, griefs {gra:.3f}")


# ================================================================== la decision
def test_decision():
    """Porte de decision : 12 jours de campagne ( elections a 25 jours ), 2 500 habitants, chaque liste choisit ses tournees
    au hasard. Part du choix >= 0,01 et p de permutation < 0,05, avec au moins 5 notes par action et par jour sur 5 jours
    au moins. Regle et temoin ( rien ) : notes moyennes rapportees."""
    dec, _ = M.scenario_campagne(jours=12, mode="hasard")
    e2, pp = dec.part_du_choix(), dec.p_permutation()
    par_jour = {}
    for (j, a), (nb, s, q) in dec.stats.items(): par_jour.setdefault(j, []).append(nb)
    jours_ok = sum(1 for v in par_jour.values() if len(v) == len(M.THEMES) and min(v) >= 5)
    def moy(dc):
        na = dc.notes_par_action()
        return sum(k * m for k, m in na.values()) / max(1, sum(k for k, _ in na.values()))
    regle, _ = M.scenario_campagne(jours=12, mode="regle")
    temoin, _ = M.scenario_campagne(jours=12, mode="temoin")
    ok = e2 >= 0.01 and pp < 0.05 and jours_ok >= 5
    na = {k: (nb, round(v, 3)) for k, (nb, v) in dec.notes_par_action().items()}
    nr = {k: (nb, round(v, 3)) for k, (nb, v) in regle.notes_par_action().items()}
    return ok, (f"hasard : {dec.n_decisions} decisions, part du choix {e2:.3f}, p {pp:.3f}, {jours_ok} jours a 5 notes par "
                f"action ; notes {na} ; moyennes regle {moy(regle):.3f} {nr}, temoin {moy(temoin):.3f}, hasard {moy(dec):.3f}")


def test_pays_vivable():
    return T.porte_commune(M.DOMAINE)


# ================================================================== le cout
class _Chrono:
    __slots__ = ("f", "t")

    def __init__(self, f): self.f, self.t = f, 0.0

    def __call__(self, p):
        t0 = time.perf_counter(); self.f(p); self.t += time.perf_counter() - t0


def test_cout():
    """Coeur Rust. A 10 000 habitants, les routines du domaine coutent au plus 25 % d une journee du moteur seul.
    Installer la politique a 100 000 habitants coute au plus 15 fois l installation a 10 000 ( lineaire : ~ x10 )."""
    coeur = W.COEUR is not None
    w0 = W.Monde(echelle=20); T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    w, p = T.monde([M.DOMAINE], 11, 20)
    T.jours(w, 1)
    chronos = []
    for minute, lst in p.routines.items():
        for i, (o, dom, f) in enumerate(lst):
            if dom == M.DOMAINE:
                c = _Chrono(f); lst[i] = (o, dom, c); chronos.append(c)
    T.jours(w, 2)
    propre = sum(c.t for c in chronos) / 2
    def installation(ech):
        wx = W.Monde(echelle=ech); P.installer(wx, ["etat", "medias", "culture"])
        t = time.perf_counter(); P.installer(wx, [M.DOMAINE]); return time.perf_counter() - t, wx.table.n
    t10, n10 = installation(20); t100, n100 = installation(200)
    ok = coeur and propre <= 0.25 * t_e1 and t100 <= 15 * t10
    return ok, (f"coeur Rust {coeur} ; {w.table.n} habitants : moteur seul {t_e1:.2f} s par jour ; routines propres "
                f"{propre * 1000:.0f} ms, {propre / t_e1:.1%} ; installation {n10} habitants {t10:.3f} s, {n100} habitants "
                f"{t100:.3f} s ( x{t100 / t10:.1f} )")


TESTS = [test_sieges_loi_grecque, test_opinion_initiale, test_griefs_crus, test_situation_propre, test_sondage_erreur,
         test_alternance_et_bornes, test_falsificateur_scrutin, test_financement_au_centime, test_contestation,
         test_decision, test_pays_vivable, test_cout]
