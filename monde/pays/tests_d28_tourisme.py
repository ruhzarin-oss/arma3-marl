"""Les portes du domaine 28 ( tourisme ). Seuils ecrits avant la premiere mesure ( 27/09 ).   python -m monde.pays.tests tourisme

Les portes jouent une petite Stratis ( echelle 20 : 10 000 habitants, huit lieux qui recoivent ), nee le 15 juin : la
saison est la. Le temoin sans tourisme est la meme ile, meme graine, installee sans le domaine."""
import time
import numpy as np
from .. import monde as W, population as PO, or_reel as OR
from ..socle import registre as R_
from . import essais as T, pays as P, d04_travail as TR, d07_exterieur as X, d28_tourisme as M

ILE, GRAINE, ECHELLE = "Stratis", 1, 20.0


def _ile(tourisme=True, graine=GRAINE, modes=None):
    from ..archipel import graine_ile
    from ..porte_domaines import LIVRES, LIVRES_IDENTITE
    w = W.Monde(graine=graine_ile(graine, ILE), iles=(ILE,), echelle=ECHELLE, cerveau="regles")
    P.installer(w, LIVRES if tourisme else LIVRES_IDENTITE, modes)
    OR.installer(w, w.pays)
    return w, w.pays


def _faim(w):
    from ..archipel import Ile
    return Ile(ILE, w).commande("etat")["faim"]


def _jours(w, n, chaque=None):
    out = []
    for _ in range(n):
        T.jours(w, 1)
        if chaque is not None: out.append(chaque(w))
    return out


# ================================================================== la saison
def test_saison():
    """Porte : le calendrier des arrivees. Aout au moins 5 fois janvier ; moyenne de l annee entre 0,35 et 0,55 ( iles
    grecques ) ; un risque de guerre de champ de bataille divise l occupation attendue par au moins 5. Falsificateur :
    un facteur de risque hors [0 ; 1] est refuse."""
    w, p = _ile()
    aout, janv = M.occupation_attendue(p, 8), M.occupation_attendue(p, 1)
    moy = sum(M.OCCUPATION_MOIS) / 12.0
    M.fixer_risque(p, M.RISQUE_CHAMP_DE_BATAILLE, "porte")
    guerre = M.occupation_attendue(p, 8)
    try: M.fixer_risque(p, 1.5); refuse = False
    except ValueError: refuse = True
    ok = aout >= 5 * janv and 0.35 <= moy <= 0.55 and guerre * 5 <= aout and refuse
    return ok, f"aout {aout:.2f}, janvier {janv:.2f}, moyenne {moy:.2f}, aout en guerre {guerre:.3f} ; risque 1,5 refuse : {refuse}"


# ================================================================== les recettes, la balance, les devises
def test_recettes_et_devises():
    """Porte : sept jours de juin. Nuitees servies >= 90 % de la demande ; recettes = nuitees x depense d une nuitee au
    taux du jour, jour par jour ( au millionieme ; AMENDE apres le premier essai : le test relisait le taux du
    lendemain, 1 113 534 contre 1 117 108 ) ; le grand livre a vu entrer de l exterieur, sous le motif recette_touristique, ce
    que le domaine compte ; la ligne services de la balance des paiements ( domaine 7, en monnaie de l ile ) depasse
    celle du temoin sans tourisme d au moins 80 % des recettes ( le fret des importations de l etablissement est aussi
    un service, en debit ; la fumee du 27/09 montrait 95 % ) ; les reserves de change de l ile depassent celles du temoin
    ( meme graine ) ; la conservation tient."""
    w, p = _ile(); w0, p0 = _ile(False)
    d = p.domaine("tourisme")
    _jours(w, 7); _jours(w0, 7)
    nuitees = sum(s[1] for s in d.serie); demande = sum(s[2] for s in d.serie); recettes = sum(s[3] for s in d.serie)
    attendu = sum(s[1] * s[5] for s in d.serie)
    livre = d.cumul["recettes"]
    services = sum(l.get("services", 0.0) for _, l, *_ in list(X._ext(p).bop.serie)[-7:])
    services0 = sum(l.get("services", 0.0) for _, l, *_ in list(X._ext(p0).bop.serie)[-7:])
    r, r0 = X.reserves_de_change(p)[0], X.reserves_de_change(p0)[0]
    tenue, msg = p.socle.conservation.tenue()
    ok = (demande > 0 and nuitees >= 0.9 * demande and abs(recettes - attendu) <= 1e-6 * max(1.0, attendu)
          and abs(livre - recettes) <= 1e-6 * max(1.0, recettes) and services - services0 >= 0.8 * recettes and r > r0 and tenue)
    return ok, (f"7 jours : {nuitees:.0f} nuitees servies sur {demande:.0f} demandees, recettes {recettes:.0f} ( attendu {attendu:.0f} ) ; "
                f"balance services {services:.0f} contre {services0:.0f} sans tourisme ( {(services - services0) / max(1, recettes):.0%} des recettes ) ; reserves {r:.0f} contre "
                f"{r0:.0f} ; conservation {msg}")


def test_sans_devises():
    """Porte : la vraie crise de Stratis. Les reserves de change de l ile portees a -50 millions d euros : la banque
    centrale ne fournit plus de devises ; l etablissement ne peut plus importer la nourriture de ses visiteurs, les repas
    importes manquent ( repas_touristes_manquants > 0 ) et les nuitees servies tombent sous la moitie de celles
    du jumeau aux reserves intactes ( controle ). La conservation tient."""
    w, p = _ile(); w2, p2 = _ile()
    X.reserves_de_change(p); X._ext(p).reserves_euros = -5e7
    d, d2 = p.domaine("tourisme"), p2.domaine("tourisme")
    _jours(w, 4); _jours(w2, 4)
    n, n2 = sum(s[1] for s in d.serie), sum(s[1] for s in d2.serie)
    manquants = d.cumul["repas_manquants"]
    tenue, msg = p.socle.conservation.tenue()
    ok = manquants > 0 and n < 0.5 * n2 and n2 > 0 and tenue
    return ok, f"4 jours sans devises : {n:.0f} nuitees servies contre {n2:.0f} ; repas importes manquants {manquants:.0f} ; conservation {msg}"


# ================================================================== l emploi
def test_emplois():
    """Porte : le personnel. Apres deux jours, les etablissements emploient au moins 90 % de leur personnel vise ; au
    moins 80 % des embauches etaient chomeurs ou hors emploi la veille ( le tourisme cree des emplois, il ne vide pas les
    fermes ) ; chacun est paye par son etablissement ( bulletins du domaine 4 ; le premier essai a ECHOUE ici : 0
    bulletin - le domaine ne creditait pas les heures pointees, 587 employes travaillaient sans etre payes ). Controle : un etablissement dont l ile
    est interdite aux voyageurs ( risque 0 ) n embauche personne."""
    w, p = _ile(); w0, p0 = _ile()
    M.fixer_risque(p0, 0.0, "porte")
    tb = w.table; col = p.colonnes["habitant"]; n = tb.n
    st0 = col["tr_statut"][:n].copy()
    p.domaine("travail").garder_bulletins = True
    _jours(w, 2); _jours(w0, 2)
    d = p.domaine("tourisme")
    ids = np.concatenate([M._personnel_ids(p, e) for e in d.etablissements])
    vise = sum(e.vise for e in d.etablissements)
    sans = float(np.isin(st0[ids], (TR.CHOMEUR, TR.HORS, TR.DECOURAGE, TR.AU_FOYER)).mean()) if len(ids) else 0.0
    payeurs = {e.id for e in d.etablissements}
    bul = [b for b in p.domaine("travail").bulletins if int(b[0]) in set(ids.tolist())]
    payes = {b[1] for b in bul}
    ids0 = sum(len(M._personnel_ids(p0, e)) for e in p0.domaine("tourisme").etablissements)
    ok = vise > 0 and len(ids) >= 0.9 * vise and sans >= 0.8 and bul and payes <= payeurs and ids0 == 0
    return ok, (f"personnel {len(ids)} pour {vise} vises ; {sans:.0%} etaient sans emploi ; {len(bul)} bulletins, payeurs {sorted(payes)[:3]} ; "
                f"ile interdite : {ids0} employes")


def test_faim_des_habitants():
    """Porte : les visiteurs ne prennent pas la nourriture des habitants. Sept jours : chaque jour, la faim de l ile
    avec tourisme <= celle du temoin sans tourisme + 1 point. Falsificateur ( la lecon payee du 27/09 ) : le meme
    personnel a l horaire du marche ( 8 h - 19 h, celui des commerces ) empeche ses menages de faire leurs courses -
    un jour au moins, la faim depasse celle du temoin de plus d un point."""
    w, p = _ile(); w0, p0 = _ile(False)
    f = _jours(w, 7, _faim); f0 = _jours(w0, 7, _faim)
    vieux = PO.TRAVAIL[M.METIER]
    PO.TRAVAIL[M.METIER] = (vieux[0], "marche")
    try:
        wf, pf = _ile(); ff = _jours(wf, 7, _faim)
    finally: PO.TRAVAIL[M.METIER] = vieux
    ok = all(a <= b + 0.01 for a, b in zip(f, f0)) and any(a > b + 0.01 for a, b in zip(ff, f0))
    return ok, (f"faim avec tourisme {[round(x, 3) for x in f]} ; temoin {[round(x, 3) for x in f0]} ; "
                f"falsificateur ( horaire du marche ) {[round(x, 3) for x in ff]}")


# ================================================================== la guerre
def test_guerre_et_occupation():
    """Porte : l avis aux voyageurs et l occupation. Sept jours au risque du champ de bataille : les recettes tombent
    sous 20 % de celles de la paix ( meme graine ). Un lieu mis en quarantaine ( une zone occupee ) : son
    etablissement ne sert plus aucune nuitee, les autres servent ( controle )."""
    w, p = _ile(); w0, p0 = _ile()
    M.fixer_risque(p, M.RISQUE_CHAMP_DE_BATAILLE, "porte")
    _jours(w, 7); _jours(w0, 7)
    r = sum(s[3] for s in p.domaine("tourisme").serie); r0 = sum(s[3] for s in p0.domaine("tourisme").serie)
    w2, p2 = _ile()
    d2 = p2.domaine("tourisme")
    cible = max(d2.etablissements, key=lambda e: e.lits)
    w2.gouv.lois.setdefault("quarantaine", []).append(cible.lieu.id)
    _jours(w2, 3)
    autres = sum(e.nuitees_total for e in d2.etablissements if e is not cible)
    ok = r0 > 0 and r <= 0.2 * r0 and cible.nuitees_total == 0 and autres > 0
    return ok, (f"recettes 7 jours : guerre {r:.0f}, paix {r0:.0f} ( {r / max(1, r0):.0%} ) ; lieu occupe {cible.lieu.id} : "
                f"{cible.nuitees_total:.0f} nuitees, les autres {autres:.0f}")


# ================================================================== la decision
def test_part_du_choix():
    """Porte de la decision effectif_saison, en mode hasard, 8 semaines : au moins 48 decisions notees ; part du choix
    ( epsilon carre a jour egal ) >= 0,01 et p de permutation < 0,05. La regle et le temoin ouvrent en juin ( plein )."""
    w, p = _ile(modes={"effectif_saison": "hasard"})
    _jours(w, 56)
    dec = p.domaine("tourisme").decideur
    n_notes = sum(k for k, _ in dec.notes_par_action().values())
    part, perm = dec.part_du_choix(), dec.p_permutation()
    wr, pr = _ile(); _jours(wr, 1)
    ouvert = all(e.vise > 0 for e in pr.domaine("tourisme").etablissements)
    ok = dec.n_decisions >= 48 and part >= 0.01 and perm < 0.05 and ouvert
    return ok, (f"{dec.n_decisions} decisions, {n_notes} notes : " + ", ".join(f"{a} {m:+.3f} ( {k} )" for a, (k, m) in dec.notes_par_action().items())
                + f" ; part du choix {part:.3f}, p de permutation {perm:.3f} ; regle ouverte en juin : {ouvert}")


# ================================================================== le cout
def test_cout():
    """Porte : le jour touristique coute moins de 5 % d une journee du pays a 10 000 habitants."""
    w, p = _ile()
    _jours(w, 1)
    t0 = time.perf_counter(); T.jours(w, 1); jour = time.perf_counter() - t0
    t1 = time.perf_counter()
    for _ in range(5): M._jour(p)
    tour = (time.perf_counter() - t1) / 5
    ok = tour <= 0.05 * jour
    return ok, f"jour du pays {jour:.2f} s, jour touristique {tour * 1000:.1f} ms ( {tour / jour:.1%} )"


def test_porte_commune():
    """La porte de tout domaine ( Altis, 500 habitants, 12 jours ) : conservation, argent hors livre exterieur
    seulement, pays vivable, reprise et jumeau identiques."""
    return T.porte_commune("tourisme")


TESTS = [test_saison, test_recettes_et_devises, test_sans_devises, test_emplois, test_faim_des_habitants,
         test_guerre_et_occupation, test_part_du_choix, test_cout, test_porte_commune]
