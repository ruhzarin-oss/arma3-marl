"""Les portes du domaine 23 ( culture, religion, loisirs, moral ). Seuils ecrits avant la premiere mesure.
python -m monde.pays.tests culture"""
import pickle, time
import numpy as np
from .. import config as C, monde as W, population as PO
from ..socle import registre as R
from . import essais as T, pays as P, d01_population as POP, d22_medias as ME, d23_culture as M

_CACHE = {}


def _monde(jours=0, echelle=5, graine=11, modes=None):
    """Un monde avec la culture et ses dependances, apres `jours` jours ; chaque porte en reprend une copie."""
    k = (jours, echelle, graine, tuple(sorted((modes or {}).items())))
    if k not in _CACHE:
        w, p = T.monde([M.DOMAINE], graine, echelle, modes=modes)
        T.jours(w, jours)
        _CACHE[k] = pickle.dumps(w)
    w = pickle.loads(_CACHE[k])
    return w, w.pays


def _jusqu_a(w, heure):
    """Avance jusqu a ce que l horloge du moteur lise `heure` ( multiple de 10 minutes ), sans jouer ce pas."""
    for _ in range(C.PAS_PAR_JOUR + 1):
        if abs(w.heure - heure) < 1e-6: return
        w.pas_suivant()
    raise RuntimeError(f"heure {heure} jamais atteinte")


def _residents(p, lieu):
    tb = p.w.table; n = tb.n
    return np.nonzero((tb.vivant[:n] == 1) & (tb.domicile[:n] == lieu))[0]


def _village_peuple(p):
    """Le lieu habite le plus peuple qui n est pas une capitale ( un village ou une ville ), et sa population."""
    d = p.domaine(M.DOMAINE); w = p.w
    caps = set(d.capitale_de.values())
    best = max((l for l in np.nonzero(d.habitable)[0].tolist() if l not in caps), key=lambda l: (len(_residents(p, l)), -l))
    return best, len(_residents(p, best))


# ================================================================== la religion
def test_religion():
    """Dix jours, 2 500 habitants. Affiliation dans les bandes grecques ( Pew 2017 : orthodoxes 90 %, sans religion 4 %,
    musulmans 2 % ) : orthodoxes 85 a 95 %, sans religion 2 a 8 %, musulmans 0,5 a 4 %. Chaque dimanche, les adultes a
    la liturgie ( realises dans le plan de l agenda ) sont 10 a 25 % des adultes ( Pew : ~17 % chaque semaine ) ; les
    dons des dimanches arrivent aux paroisses, et la paroisse a recu exactement ce que le domaine a compte. Aucun
    pratiquant sans religion. Falsificateur : un sans-religion rendu pratiquant a la main se voit."""
    w, p = _monde(10)
    d = p.domaine(M.DOMAINE); col = p.colonnes["habitant"]; tb = w.table; n = tb.n
    v = tb.vivant[:n] == 1
    c = col["cul_confession"][:n][v]
    parts = np.bincount(c[c >= 0], minlength=5) / max(1, (c >= 0).sum())
    bandes = parts[M.ORTHODOXE] >= 0.85 and parts[M.ORTHODOXE] <= 0.95 and 0.02 <= parts[M.SANS] <= 0.08 \
        and 0.005 <= parts[M.MUSULMAN] <= 0.04 and (c < 0).sum() == 0
    dim = [s for s in d.serie if s.get("semaine") == 6]
    taux = [s["culte_adultes"] / max(1, s["adultes"]) for s in dim]
    dimanches = len(dim) >= 1 and all(0.10 <= x <= 0.25 for x in taux) and all(s["dons"] > 0 for s in dim)
    recu = sum(x.dons_total for x in d.paroisses)
    exact = abs(recu - d.compte["don_religieux"]) <= 1e-6 * max(1.0, recu)
    propre = not [a for a in M.anomalies(p) if a[0] == "pratiquant_sans_religion"]
    i = int(np.nonzero(v & (col["cul_confession"][:n] == M.SANS))[0][0])
    col["agenda_pratiquant"][i] = 1
    vu = ("pratiquant_sans_religion", i) in M.anomalies(p)
    ok = bandes and dimanches and exact and propre and vu
    return ok, (f"orthodoxes {parts[0]:.1%}, musulmans {parts[1]:.1%}, catholiques {parts[2]:.1%}, autres {parts[3]:.1%}, "
                f"sans {parts[4]:.1%} ; dimanches : adultes a la liturgie {', '.join(f'{x:.1%}' for x in taux)}, dons "
                f"{', '.join(format(s['dons'], '.0f') for s in dim)} dr ; paroisses {recu:.2f} dr = compte : {exact} ; "
                f"pratiquant sans religion : aucun {propre}, pose a la main vu {vu}")


def test_niveau_du_moral():
    """Apres dix jours d un pays ordinaire, le moral moyen se lit comme la satisfaction de vie grecque ( Eurostat
    EU-SILC 2018 : 6,2 sur 10, a verifier ) : entre 0,55 et 0,70 ; au plus 10 % des adultes sous 0,35 ; chaque lieu
    habite a un moral collectif entre 0,4 et 0,8."""
    w, p = _monde(10)
    d = p.domaine(M.DOMAINE); tb = w.table; n = tb.n
    ids = np.nonzero((tb.vivant[:n] == 1) & (tb.age[:n] >= 18))[0]
    m = M.moral(p, ids)
    lieux = M.moral_des_lieux(p)
    habites = [x for x, (mm, r, _) in lieux.items() if r > 0]
    ok_l = all(0.4 <= lieux[x][0] <= 0.8 for x in habites)
    ok = 0.55 <= m.mean() <= 0.70 and (m < 0.35).mean() <= 0.10 and ok_l
    return ok, (f"moral moyen des adultes {m.mean():.3f} ( ecart-type {m.std():.3f} ), sous 0,35 : {(m < 0.35).mean():.1%} ; "
                f"{len(habites)} lieux habites de {min(lieux[x][0] for x in habites):.3f} a "
                f"{max(lieux[x][0] for x in habites):.3f}")


# ================================================================== les causes du moral ( controles positifs )
def test_faim_et_deuil():
    """Controle positif, mondes apparies ( meme graine, meme jour ) : dans le monde B, un adulte meurt dans 30 menages
    ( par `deceder`, mort naturelle ) et 30 autres menages ont faim cinq soirs ( faim de la semaine et rations
    manquees posees chaque soir a 22 h ). Apres 5 jours : moral des survivants endeuilles B - A <= -0,05 ; des affames
    B - A <= -0,05 ; les autres habitants ne bougent pas ( |B - A| moyen <= 0,01 ).
    26/09, premiere mesure : les 30 deces etaient des ACCIDENTS - 30 morts accidentelles le meme jour sont une nouvelle
    que tout le pays croit ( domaine 22, mort_accident : +0,79 de climat negatif a Pyrgos ) et le moral des autres
    baissait de 0,044. Le canal des croyances marchait ; le scenario ne visait que le deuil : mort naturelle depuis."""
    w0, p0 = _monde(3)
    tb = w0.table; n = tb.n
    mg, viv, Mn = M._menages_vivants(p0)
    adultes = np.bincount(mg[(tb.vivant[:n] == 1) & (mg >= 0) & (tb.age[:n] >= 25)], minlength=Mn)[:Mn]
    cands = np.nonzero((viv >= 2) & (adultes >= 1))[0]
    rng = np.random.default_rng(3)
    choisis = rng.permutation(cands)[:60]
    deuil_m, faim_m = np.sort(choisis[:30]), np.sort(choisis[30:])
    snap = pickle.dumps(w0)
    wa = pickle.loads(snap); wb = pickle.loads(snap); pb = wb.pays
    morts = []
    for k in deuil_m.tolist():
        i = int(np.nonzero((tb.menage[:n] == k) & (tb.vivant[:n] == 1) & (tb.age[:n] >= 25))[0][0])
        POP.deceder(pb, wb.habitants[i], "naturelle"); morts.append(i)
    membres_f = np.nonzero(np.isin(wb.table.menage[:n], faim_m) & (wb.table.vivant[:n] == 1))[0]
    for _ in range(5):
        for w_ in (wa, wb): _jusqu_a(w_, 22.0)
        pb.col("menage", "faim7")[faim_m] = 0x7F
        wb.table.faim[membres_f] = 3.0
        for w_ in (wa, wb): w_.pas_suivant()
    for w_ in (wa, wb): _jusqu_a(w_, 6.0)
    pa = wa.pays
    vivant = (wb.table.vivant[:n] == 1) & (wa.table.vivant[:n] == 1)
    sd = np.nonzero(np.isin(tb.menage[:n], deuil_m) & vivant)[0]
    sf = membres_f[vivant[membres_f]]
    autres = np.nonzero(vivant & ~np.isin(tb.menage[:n], choisis))[0]
    dd = M.moral(pb, sd).mean() - M.moral(pa, sd).mean()
    df = M.moral(pb, sf).mean() - M.moral(pa, sf).mean()
    da = M.moral(pb, autres).mean() - M.moral(pa, autres).mean()
    ok = dd <= -0.05 and df <= -0.05 and abs(da) <= 0.01 and not M.anomalies(pb)
    return ok, (f"{len(morts)} deces : {len(sd)} survivants endeuilles B - A {dd:+.3f} ; {len(sf)} affames B - A {df:+.3f} ; "
                f"{len(autres)} autres {da:+.4f} ; anomalies {len(M.anomalies(pb))}")


def test_fete_controle_positif():
    """Controle positif : dans le monde B, la fete du saint patron du lieu le plus peuple hors capitale est posee au
    jour qui commence. Au soir : au moins 30 % de ses residents de 6 ans et plus sont au panigyri ( realise dans le
    plan ), sa paroisse en recoit la recette, le journal note le panigyri ; le moral des participants B - A >= +0,03 ;
    les residents des autres lieux ne bougent pas ( |B - A| moyen <= 0,005 )."""
    w0, p0 = _monde(3)
    X, pop = _village_peuple(p0)
    snap = pickle.dumps(w0)
    wa = pickle.loads(snap); wb = pickle.loads(snap); pb = wb.pays; db = pb.domaine(M.DOMAINE)
    date = pb.socle.calendrier.date(wb.pas).date()
    db.fete_mois[X], db.fete_jour[X] = date.month, date.day
    par = db.paroisses[int(db.paroisse_de[X])]
    avant = par.panigyri_total
    for w_ in (wa, wb): T.jours(w_, 1)
    pa = wa.pays
    part = pb.domaine(M.DOMAINE).panigyri_ids
    res = _residents(pb, X); res6 = res[wb.table.age[res] >= 6]
    realises = part[np.isin(part, M._realises(pb.domaine("agenda").plan, M.AG.T_LOISIR_SOIR))]
    taux = len(realises) / max(1, len(res6))
    dm = M.moral(pb, realises).mean() - M.moral(pa, realises).mean() if len(realises) else 0.0
    tb = wb.table; n = tb.n
    autres = np.nonzero((tb.vivant[:n] == 1) & (tb.domicile[:n] != X) & (wa.table.vivant[:n] == 1))[0]
    da = M.moral(pb, autres).mean() - M.moral(pa, autres).mean()
    journal = any(e["type"] == "panigyri" and e["lieu"] == db.lieu_ids[X] for e in pb.socle.journal.derniers(n=500))
    recette = par.panigyri_total - avant
    ok = taux >= 0.30 and recette > 0 and journal and dm >= 0.03 and abs(da) <= 0.005
    return ok, (f"{db.lieu_ids[X]} ( {pop} residents ), fete de {par.saint} posee : {len(realises)} au panigyri, "
                f"{taux:.0%} des 6 ans et plus ; recette de la paroisse {recette:.0f} dr ; journal {journal} ; moral des "
                f"participants B - A {dm:+.3f} ; autres lieux {da:+.5f}")


def test_catastrophe_crue():
    """Regle 3 : le moral suit ce qui est CRU, jamais la verite cachee. Mondes apparies apres 2 jours, dans le lieu le
    plus peuple hors capitale : B, un seisme destructeur vu de ses residents ( `constater`, 60 batiments ) ; C, le meme
    fait sans aucun temoin ni communique ( vrai, inconnu ). Trois jours apres : moral collectif B - A <= -0,01 ;
    |C - A| <= 0,2 x |B - A|, et personne ne sait le fait de C."""
    w0, p0 = _monde(2)
    X, pop = _village_peuple(p0)
    snap = pickle.dumps(w0)
    mondes = [pickle.loads(snap) for _ in range(3)]
    wa, wb, wc = mondes
    ME.constater(wb.pays, "degats_seisme", X, 60.0)
    fid_c = ME.constater(wc.pays, "degats_seisme", X, 60.0, temoins=0, officiel=False)
    for w_ in mondes: T.jours(w_, 3)
    m = [M.moral_collectif(w_.pays, X) for w_ in mondes]
    db, dc = m[1] - m[0], m[2] - m[0]
    inconnu = ME.part_nationale(wc.pays, fid_c) == 0.0
    ok = db <= -0.01 and abs(dc) <= 0.2 * abs(db) and inconnu
    return ok, (f"{p0.domaine(M.DOMAINE).lieu_ids[X]} ( {pop} residents ) : moral {m[0]:.4f} ; seisme cru {db:+.4f} ; "
                f"seisme inconnu {dc:+.4f} ( su de personne : {inconnu} )")


def test_rumeur_fausse():
    """Regle 3, l autre face : une rumeur FAUSSE que le lieu croit pese sur son moral. Mondes apparies apres 2 jours ;
    dans le monde D, une rumeur d incendie que 80 % du lieu le plus peuple hors capitale croit ( `fabriquer_rumeur` ).
    Trois jours apres : moral collectif D - A <= -0,01. ( Ecrite avec test_catastrophe_crue, avant la premiere mesure ;
    separee apres elle pour que chaque porte dise une seule chose. )"""
    w0, p0 = _monde(2)
    X, pop = _village_peuple(p0)
    snap = pickle.dumps(w0)
    wa, wd = pickle.loads(snap), pickle.loads(snap)
    fid = ME.fabriquer_rumeur(wd.pays, "incendie", X, 5.0, personnes=max(1, int(0.8 * pop)))
    suivi = []
    for _ in range(3):
        T.jours(wa, 1); T.jours(wd, 1)
        f = ME.fait(wd.pays, fid)
        suivi.append(f"{M.moral_collectif(wd.pays, X) - M.moral_collectif(wa.pays, X):+.4f}"
                     + (" ( dementie )" if f and f["dementi"] else ""))
    dd = M.moral_collectif(wd.pays, X) - M.moral_collectif(wa.pays, X)
    ok = dd <= -0.01
    return ok, f"{p0.domaine(M.DOMAINE).lieu_ids[X]} : rumeur fausse crue, moral D - A jour par jour {', '.join(suivi)}"


# ================================================================== l argent
def test_argent_au_centime():
    """Huit jours, 2 500 habitants. Les trois familles du domaine se rapprochent du grand livre ( reste nul ) ; pour
    chaque motif du domaine, ce que le domaine a compte = ce que le grand livre a vu, au centime ; la TVA de chaque
    etablissement ( reversee + due ) = taux / ( 1 + taux ) de ce qu il a encaisse ( 1e-9 relatif ) ; la conservation
    tient ; les sorties payees font de 3 a 20 % du revenu des menages ( ELSTAT 2023 : loisirs 4,4 % et
    restauration 11,4 % de la consommation ). Falsificateur : 5 drachmes retirees a la main d une paroisse se voient."""
    w, p = _monde(0)
    d = p.domaine(M.DOMAINE); L = p.socle.livre
    rap = R.Rapprochement(p.socle.registre, L)
    rev = 0.0
    for _ in range(8):
        T.jours(w, 1); rev += float(np.maximum(0.0, p.col("menage", "eco_revenu")[:w.table.menages.n]).sum())
    fams = ("paroisses", "etablissements_loisir", "associations_loisir")
    restes = rap.restes()
    rap_ok = all(abs(restes[f]) <= R.tolerance(restes[f]) + 1e-9 for f in fams)
    motifs = [m for m, _ in M.MOTIFS] + ["tva"]
    ecarts = {m: d.compte.get(m, 0.0) - d.livre_motifs.get(m, 0.0) for m in motifs}
    centime = all(abs(x) <= 0.005 for x in ecarts.values())
    tva_ok = all(abs(e.tva_versee + e.tva_due - e.recettes_ttc * e.tva / (1 + e.tva)) <= 1e-9 * max(1.0, e.recettes_ttc)
                 for e in d.etablissements)
    dep = sum(s["depense"] for s in d.serie)
    part = dep / max(rev, 1e-9)
    tenue, msg = p.socle.conservation.tenue()
    x = next(x for x in d.paroisses if x.caisse > 5)
    x.caisse -= 5.0
    vu = abs(rap.restes()["paroisses"] + 5.0) <= 1e-6
    ok = rap_ok and centime and tva_ok and 0.03 <= part <= 0.20 and tenue and vu
    pire = max(ecarts, key=lambda m: abs(ecarts[m]))
    return ok, (f"restes {', '.join(f'{f} {restes[f]:+.1e}' for f in fams)} ; {len(motifs)} motifs au centime {centime} "
                f"( pire {pire} {ecarts[pire]:+.1e} ) ; TVA exacte {tva_ok} ; sorties {dep:.0f} dr pour {rev:.0f} dr de "
                f"revenu ( {part:.1%} ) ; dons {d.compte['don_religieux']:.0f}, entraide {d.compte['aide_paroissiale']:.0f}, "
                f"proprietaires {d.compte['revenu_exploitant_loisirs']:.0f} dr ; {msg} ; paroisse videe a la main vue {vu}")


# ================================================================== le falsificateur du moral
def test_moral_hors_causes():
    """Falsificateur : apres trois jours, aucune anomalie ; un moral individuel releve de 0,1 a la main ( hors de ses
    causes ) se voit, un moral de lieu faux se voit, et un moral remis a sa valeur ne se voit plus."""
    w, p = _monde(3)
    d = p.domaine(M.DOMAINE); col = p.colonnes["habitant"]; tb = w.table; n = tb.n
    avant = M.anomalies(p)
    i = int(np.nonzero((tb.vivant[:n] == 1) & (col["cul_moral"][:n] < 0.8))[0][0])
    v0 = col["cul_moral"][i]
    col["cul_moral"][i] = v0 + np.float32(0.1)
    vu_i = ("moral_hors_causes", i) in M.anomalies(p)
    col["cul_moral"][i] = v0
    rendu = not M.anomalies(p)
    X, _ = _village_peuple(p)
    d.moral_lieu[X] += 0.01
    vu_l = ("moral_de_lieu", d.lieu_ids[X]) in M.anomalies(p)
    ok = not avant and vu_i and rendu and vu_l
    return ok, (f"anomalies d un monde sain {len(avant)} ; moral de l habitant {i} releve de 0,1 vu {vu_i}, remis : "
                f"propre {rendu} ; moral de {d.lieu_ids[X]} fausse vu {vu_l}")


# ================================================================== la decision
def test_decision():
    """Porte de decision : 21 jours, 2 500 habitants, chaque menage decide sa semaine au hasard. Part du choix >= 0,01
    et p de permutation < 0,05, avec au moins 5 notes par action et par jour sur 5 jours au moins. La regle vectorisee
    est la regle ( 4 000 traits tires au hasard ). Regle et temoin ( toujours rester ) : notes moyennes rapportees."""
    dec, _ = M.scenario_loisirs(jours=21, mode="hasard")
    e2, pp = dec.part_du_choix(), dec.p_permutation()
    par_jour = {}
    for (j, a), (nb, s, q) in dec.stats.items(): par_jour.setdefault(j, []).append(nb)
    jours_ok = sum(1 for v in par_jour.values() if len(v) == len(M.ACTIONS) and min(v) >= 5)
    X = np.random.default_rng(0).random((4000, len(M.POINT_LOISIRS.traits)))
    X[:, 1] = np.where(X[:, 1] < 0.7, 0.0, X[:, 1]); X[:, 4] = np.round(X[:, 4]); X[:, 5] = (X[:, 5] < 0.1)
    meme = (M._regle_vect(X) == np.array([M._regle_loisirs(x, None) for x in X])).all()
    def moy(dc):
        na = dc.notes_par_action()
        return sum(k * m for k, m in na.values()) / max(1, sum(k for k, _ in na.values()))
    regle, _ = M.scenario_loisirs(jours=21, mode="regle")
    temoin, _ = M.scenario_loisirs(jours=21, mode="temoin")
    ok = e2 >= 0.01 and pp < 0.05 and jours_ok >= 5 and meme
    na = {k: (nb, round(v, 3)) for k, (nb, v) in dec.notes_par_action().items()}
    nr = {k: (nb, round(v, 3)) for k, (nb, v) in regle.notes_par_action().items()}
    return ok, (f"hasard : {dec.n_decisions} decisions, part du choix {e2:.3f}, p {pp:.3f}, {jours_ok} jours a 5 notes par "
                f"action ; notes {na} ; regle vectorisee = regle {meme} ; moyennes regle {moy(regle):.3f} {nr}, temoin "
                f"{moy(temoin):.3f}, hasard {moy(dec):.3f}")


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
    Installer la culture a 100 000 habitants coute au plus 15 fois l installation a 10 000 ( lineaire : ~ x10 )."""
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
        wx = W.Monde(echelle=ech); P.installer(wx, ["medias", "agenda"])
        t = time.perf_counter(); P.installer(wx, [M.DOMAINE]); return time.perf_counter() - t, wx.table.n
    t10, n10 = installation(20); t100, n100 = installation(200)
    ok = coeur and propre <= 0.25 * t_e1 and t100 <= 15 * t10
    return ok, (f"coeur Rust {coeur} ; {w.table.n} habitants : moteur seul {t_e1:.2f} s par jour ; routines propres "
                f"{propre * 1000:.0f} ms, {propre / t_e1:.1%} ; installation {n10} habitants {t10:.3f} s, {n100} habitants "
                f"{t100:.3f} s ( x{t100 / t10:.1f} )")


def test_sortie_sans_revenu():
    """Porte ( HMT-126 e, seuils ecrits avant la mesure ) - controle positif : le plancher de la culture vaut 90 jours de
    nourriture pour un menage sans revenu ; une sortie de 5 drachmes au cafe, payee par le chemin des sorties
    ( _payer_par_couple, reserve max( 7 jours, plancher ) ), n est pas payee par un menage sans revenu qui a 30 jours de
    nourriture en caisse. Falsificateur : un menage au revenu suffisant, avec la meme caisse, la paie ; son plancher reste
    nul au-dela de ses 7 jours propres."""
    w, p = _monde(1)
    d = M._dom(p); cm = p.colonnes["menage"]; tb = w.table
    mg, viv, Mn = M._menages_vivants(p)
    cout = M._cout_jour(p, Mn, viv)
    ids = [k for k in range(Mn) if viv[k] > 0]
    A, B = ids[0], ids[1]
    EC = __import__(__package__ + ".d03_economie", fromlist=["x"]); EC.revenu_recent(p, len(w.menages))
    for k, r in ((A, 0.0), (B, 10.0 * cout[B])): cm["eco_revenu_30"][k] = r; cm["eco_revenu_30_n"][k] = 30
    pl = M._plancher(p, cout)
    caisse = tb.menages.caisse[:Mn]
    L = p.socle.livre
    for k in (A, B):
        m = w.menages[k]; x = 30.0 * cout[k]
        if m.caisse > x: L.transferer(m, w.gouv, m.caisse - x, "amende")
        else: L.recevoir_de_l_exterieur(m, x - m.caisse, "epargne_initiale")
    et = next(i for i, e in enumerate(d.etablissements) if e is not None)
    reserve = np.maximum(M.RESERVE_SORTIE_J * cout, pl)
    ca, cb = float(caisse[A]), float(caisse[B])
    tot, par = M._payer_par_couple(p, d, np.array([A, B]), np.array([et, et]), np.array([5.0, 5.0]), d.etablissements,
                                   M._motif_etablissement, reserve, caisse, M._encaisser_sortie)
    valeurs = abs(pl[A] - 90.0 * cout[A]) <= 1e-9 * pl[A] and pl[B] <= M.RESERVE_SORTIE_J * cout[B] + 1e-9
    a_ok = float(caisse[A]) == ca and A not in par
    b_ok = abs(cb - float(caisse[B]) - 5.0) <= 1e-9
    tenue, msg = p.socle.conservation.tenue()
    ok = valeurs and a_ok and b_ok and tenue
    return ok, (f"plancher sans revenu {pl[A] / cout[A]:.0f} jours, avec revenu {pl[B] / cout[B]:.0f} jours ; sortie de 5 avec 30 jours "
                f"en caisse : sans revenu payee {ca - float(caisse[A]):.2f}, avec revenu {cb - float(caisse[B]):.2f} ; {msg}")


TESTS = [test_religion, test_niveau_du_moral, test_faim_et_deuil, test_fete_controle_positif, test_catastrophe_crue,
         test_rumeur_fausse,
         test_argent_au_centime, test_moral_hors_causes, test_decision, test_pays_vivable, test_cout, test_sortie_sans_revenu]
