"""Les portes du socle ( domaine 0 ). Ecrites AVANT la premiere mesure ; chacune a son controle positif ou son
falsificateur : une porte qui ne sait pas echouer ne prouve rien.

   python -m monde.socle.tests_socle"""
import datetime as dt, os, pickle, sys, tempfile, time
import numpy as np
from .. import monde as W, config as C
from . import biens as B, objets as O, comptes as K, registre as R, echeancier as E, journal as J
from . import hasard as H, calendrier as T, decision as D, brancher as BR


def jours(w, n):
    for _ in range(n * C.PAS_PAR_JOUR): w.pas_suivant()
    return w


# ================================================================== biens
def test_catalogue():
    """Les neuf biens du moteur, dans l ordre et aux prix de config ; les bornes refusent ce qui est faux."""
    cat = B.catalogue_du_moteur()
    memes = [b.nom for b in cat] == list(C.BIENS) and all(cat[n].prix_monde == C.PRIX_MONDE[n] for n in C.BIENS)
    ids = [b.id for b in cat] == list(range(len(C.BIENS)))
    essais = (lambda: cat.declarer("nourriture", "aliment", "x", 1.0),              # doublon
              lambda: cat.declarer("sel", "aliment", "kg", -1.0),                   # prix negatif
              lambda: cat.declarer("sel", "aliment", "kg", float("nan")),           # prix non fini
              lambda: cat.declarer("Sel", "aliment", "kg", 1.0),                    # majuscule
              lambda: cat.declarer("cafe", "boisson", "kg", 1.0),                   # famille inconnue
              lambda: cat.declarer("sel", "aliment", "kg", 1.0, masse_kg=-2.0))     # masse negative
    refus = 0
    for essai in essais:
        try: essai()
        except ValueError: refus += 1
    ok = memes and ids and refus == len(essais) and len(cat) == len(C.BIENS)
    return ok, (f"{len(cat)} biens, identifiants 0-{len(cat) - 1}, prix de config ; {refus}/{len(essais)} declarations "
                f"fausses refusees ; {len(cat.non_calibres())} biens sans masse ni volume ( a calibrer par leur domaine )")


# ================================================================== hasard
def test_hasard_par_domaine():
    """Un tirage ajoute dans un domaine ne change rien aux autres ; avec un seul flux, il les decale."""
    a = H.Hasard(7).flux("meteo").random(1000)
    h = H.Hasard(7); h.flux("banques").random(12345); h.flux("sante").integers(0, 9, 777)
    independant = np.array_equal(a, h.flux("meteo").random(1000))
    g1, g2 = np.random.default_rng(7), np.random.default_rng(7); g2.random(12345)       # un seul flux, comme Monde.rng
    commun_decale = not np.array_equal(g1.random(1000), g2.random(1000))
    h1, h2 = H.Hasard(7), H.Hasard(7); h2.flux("meteo").random(50)
    jour_stable = np.array_equal(h1.du_jour("meteo", 12).random(100), h2.du_jour("meteo", 12).random(100))
    jours_distincts = not np.array_equal(h1.du_jour("meteo", 12).random(100), h1.du_jour("meteo", 13).random(100))
    h3 = H.Hasard(7); h3.flux("meteo").random(500); snap = pickle.dumps(h3)
    repris = np.array_equal(h3.flux("meteo").random(100), pickle.loads(snap).flux("meteo").random(100))
    graines = not np.array_equal(H.Hasard(7).flux("meteo").random(100), H.Hasard(8).flux("meteo").random(100))
    ok = independant and commun_decale and jour_stable and jours_distincts and repris and graines
    return ok, (f"meteo intacte apres 13 122 tirages ailleurs : {independant} ; un flux commun decale : {commun_decale} ; "
                f"flux du jour stable : {jour_stable} ; reprise exacte : {repris}")


# ================================================================== calendrier
def test_calendrier():
    """Paques orthodoxe connue, 12 feries en 2035, le soleil cale sur le moteur en juin, et juste en octobre."""
    connues = [T.paques_orthodoxe(a) for a in (2024, 2025, 2026)] == [dt.date(2024, 5, 5), dt.date(2025, 4, 20), dt.date(2026, 4, 12)]
    cal = T.Calendrier()
    f = cal.feries(2035)
    feries = len(f) == 12 and f.get(dt.date(2035, 4, 30)) == "lundi_de_paques" and f.get(dt.date(2035, 3, 12)) == "lundi_pur"
    depart = cal.date(0) == dt.datetime(2035, 6, 15, 6, 0) and cal.jour_semaine(0) == 4       # un vendredi
    lj, cj = cal.soleil("Altis", dt.date(2035, 6, 15))
    cale = abs(lj - C.LEVER) <= 0.25 and abs(cj - C.COUCHER) <= 0.25
    lo, co = cal.soleil("Altis", dt.date(2035, 10, 13))            # le jour 120 du monde
    le, ce = cal.soleil("Altis", dt.date(2035, 3, 20))
    try: cal.soleil("Tanoa", dt.date(2035, 6, 15)); refuse = False
    except T.LatitudeInconnue: refuse = True
    ok = connues and feries and depart and cale and co <= 19.0 and 11.9 <= ce - le <= 12.4 and refuse
    return ok, (f"Paques 2024-26 justes : {connues} ; 15/06 : lever {lj:.2f} h coucher {cj:.2f} h ( moteur {C.LEVER} / "
                f"{C.COUCHER} ) ; 13/10 : lever {lo:.2f} h coucher {co:.2f} h, soit {(lo - C.LEVER) + (C.COUCHER - co):.1f} h "
                f"de jour en trop dans le moteur ; equinoxe {ce - le:.2f} h ; ile sans latitude refusee : {refuse}")


# ================================================================== registre et conservation sur le moteur
def test_registre_reproduit_le_moteur():
    """Porte : sur 10 jours du monde E1, le registre retrouve argent_total et biens_totaux, et la conservation du
    socle tient chaque soir."""
    w = W.Monde(); s = BR.brancher(w)
    pire_a = pire_b = pire_c = 0.0
    for _ in range(10):
        jours(w, 1)
        pire_a = max(pire_a, abs(s.registre.argent() - w.argent_total()))
        rb, wb = s.registre.biens(), w.biens_totaux()
        pire_b = max(pire_b, max(abs(rb[b] - wb[b]) for b in C.BIENS))
        d_arg, d_b, _ = s.conservation.ecarts()
        pire_c = max(pire_c, abs(d_arg), max(abs(v) for v in d_b.values()))
    ok = pire_a <= 1e-6 and pire_b <= 1e-6 and pire_c <= 1e-6
    return ok, f"10 jours : registre - moteur {pire_a:.1e} ( argent ), {pire_b:.1e} ( biens ) ; ecart de conservation {pire_c:.1e}"


def test_registre_voit_un_oubli():
    """Controle positif : un registre sans les garnisons ne voit pas le carburant qu elles brulent."""
    w = W.Monde(); s = BR.brancher(w)
    troue = R.Conservation(BR.registre_du_moteur(w, s.catalogue, sans=("garnisons",)), s.livre)
    jours(w, 3)
    _, plein, _ = s.conservation.ecarts(); _, trou, _ = troue.ecarts()
    ok = abs(plein["carburant"]) <= 1e-6 and abs(trou["carburant"]) > 1e-3
    return ok, f"carburant : registre complet {plein['carburant']:+.1e}, registre sans garnisons {trou['carburant']:+.2f}"


def test_creation_hors_source():
    """Falsificateur : 7 unites de nourriture et 3 drachmes crees a la main doivent se voir, au centime."""
    w = W.Monde(); s = BR.brancher(w); jours(w, 2)
    w.marches["Kavala"].stocks["nourriture"] += 7.0
    w.menages[0].caisse += 3.0
    d_arg, d_b, _ = s.conservation.ecarts()
    ok = abs(d_b["nourriture"] - 7.0) <= 1e-6 and abs(d_arg - 3.0) <= 1e-6
    return ok, f"vu {d_b['nourriture']:.6f} unites pour 7 creees, {d_arg:.6f} drachmes pour 3"


def test_socle_ne_change_pas_le_monde():
    """Porte : un monde branche est le MEME monde, au bit pres, et il passe dans l instantane."""
    a = jours(W.Monde(graine=11), 8)
    b = W.Monde(graine=11); BR.brancher(b); jours(b, 4)
    snap = pickle.dumps(b); jours(b, 4)
    c = jours(pickle.loads(snap), 4)
    meme = a.resume_jour() == b.resume_jour() == c.resume_jour() and a.argent_total() == b.argent_total() == c.argent_total()
    tenue, msg = c.socle.conservation.tenue()
    return meme and tenue, f"8 jours sans socle / avec / avec reprise a mi-course : {'identiques' if meme else 'DIFFERENTS'} ; {msg}"


def test_motifs_du_moteur():
    """Tous les paiements du moteur ont un motif declare ; un motif mal ecrit est refuse en mode strict."""
    w = W.Monde(); s = BR.brancher(w); jours(w, 10)
    compte = s.livre.cloturer_jour()
    inconnus = dict(s.livre.non_declares)
    caisse = w.gouv.caisse
    try: K.GrandLivre(s.catalogue, strict=True).transferer(w.gouv, w.menages[0], 1.0, "salaire_mal_ecrit"); refuse = False
    except K.MotifInconnu: refuse = w.gouv.caisse == caisse
    pn = compte["par_nature"]
    imp = sum(v[0] for v in compte["impayes"].values()); nimp = sum(v[1] for v in compte["impayes"].values())
    ok = not inconnus and refuse and pn.get("remuneration", 0) > 0 and pn.get("impot_production", 0) > 0
    top = ", ".join(f"{k} {v:,.0f}" for k, v in sorted(pn.items(), key=lambda kv: -kv[1]))
    return ok, (f"motifs non declares : {inconnus or 'aucun'} ; 10 jours par nature : {top} ; "
                f"impayes du moteur : {nimp} paiements, {imp:,.0f} drachmes")


# ================================================================== rapprochement
class Foyer:
    __slots__ = ("caisse", "stock")
    def __init__(self, c): self.caisse = c; self.stock = B.Stock()


class Firme(Foyer):
    __slots__ = ()


class Tresor(Foyer):
    __slots__ = ()


class MondeJouet:
    def __init__(self, rng):
        self.foyers = [Foyer(float(rng.uniform(0, 500))) for _ in range(200)]
        self.firmes = [Firme(float(rng.uniform(0, 5000))) for _ in range(20)]
        self.tresor = [Tresor(1e5)]


def _foyers(w): return w.foyers
def _firmes(w): return w.firmes
def _tresor(w): return w.tresor


def _socle_jouet(graine):
    rng = np.random.default_rng(graine)
    w = MondeJouet(rng); cat = B.catalogue_du_moteur()
    livre = K.GrandLivre(cat)
    for m, n in (("achat", "achat"), ("salaire", "remuneration"), ("impot", "impot_revenu"), ("export", "achat"), ("import", "achat")):
        livre.declarer_motif(m, n, "test")
    reg = R.Registre(w, cat)
    reg.inscrire("foyers", "menages", _foyers, "caisse", "stock", "Foyer")
    reg.inscrire("firmes", "entreprises", _firmes, "caisse", "stock", "Firme")
    reg.inscrire("tresor", "administrations", _tresor, "caisse", None, "Tresor")
    return w, rng, livre, reg


def test_rapprochement():
    """Porte : dans un monde qui ne paie que par le grand livre, chaque famille se rapproche au centime. Controle
    positif : 5 drachmes passees a la main d un foyer a une firme se voient dans le rapprochement, pas dans la
    conservation. Falsificateur : 4 unites posees a la main dans un stock du socle se voient. Puis le moteur E1 :
    tout l argent qui passe hors du grand livre doit etre de l argent exterieur."""
    w, rng, livre, reg = _socle_jouet(3)
    cons, rap = R.Conservation(reg, livre), R.Rapprochement(reg, livre)
    tous = w.foyers + w.firmes + w.tresor
    for _ in range(50_000):
        k = int(rng.integers(0, 8))
        f, g = w.foyers[int(rng.integers(0, 200))], w.firmes[int(rng.integers(0, 20))]
        b = int(rng.integers(0, len(C.BIENS)))
        if k == 0: livre.transferer(tous[int(rng.integers(0, len(tous)))], tous[int(rng.integers(0, len(tous)))], float(rng.uniform(0, 100)), "achat")
        elif k == 1: livre.transferer(g, f, float(rng.uniform(0, 80)), "salaire")
        elif k == 2: livre.recevoir_de_l_exterieur(g, float(rng.uniform(0, 50)), "export")
        elif k == 3: livre.payer_l_exterieur(w.tresor[0], float(rng.uniform(0, 50)), "import")
        elif k == 4: livre.produire(g.stock, b, float(rng.uniform(0, 10)), "recette")
        elif k == 5: livre.deplacer(g.stock, f.stock, b, float(rng.uniform(0, 10)), "vente")
        elif k == 6: livre.consommer(f.stock, b, float(rng.uniform(0, 5)), "repas")
        else: (livre.importer(g.stock, b, 3.0, "port") if rng.random() < 0.5 else livre.perimer(f.stock, b, 1.0, "peremption"))
    propre, msg_c = cons.tenue()
    restes = rap.restes()
    rapproche = all(abs(v) <= 1e-6 for v in restes.values())
    w.foyers[0].caisse -= 5.0; w.firmes[0].caisse += 5.0             # un paiement ecrit a la main
    restes_main = rap.restes(); d_arg_main = cons.ecarts()[0]
    vu_main = abs(restes_main["foyers"] + 5.0) <= 1e-6 and abs(restes_main["firmes"] - 5.0) <= 1e-6 and abs(d_arg_main) <= 1e-6
    w.firmes[1].stock.q[0] = w.firmes[1].stock[0] + 4.0            # une creation de bien a la main
    vu_stock = abs(cons.ecarts()[1]["nourriture"] - 4.0) <= 1e-6
    # le moteur E1
    m = W.Monde(); s = BR.brancher(m)
    ext0 = m.ext["entree"] - m.ext["sortie"]
    jours(m, 10)
    restes_e1 = s.rapprochement.restes()
    d_ext = (m.ext["entree"] - m.ext["sortie"]) - ext0
    exterieur_seul = abs(sum(restes_e1.values()) - d_ext) <= R.tolerance(d_ext)
    ok = propre and rapproche and vu_main and vu_stock and exterieur_seul
    hors = ", ".join(f"{k} {v:+,.0f}" for k, v in restes_e1.items() if abs(v) > 1e-6) or "aucune"
    return ok, (f"50 000 operations : {msg_c}, rapprochement {'au centime' if rapproche else 'FAUX'} ; 5 drachmes a la main "
                f"vues : {vu_main} ; 4 unites a la main vues : {vu_stock} ; moteur E1, 10 jours, argent hors grand livre "
                f"par famille : {hors} ( exterieur net {d_ext:+,.0f} ) : {'tout exterieur' if exterieur_seul else 'PAS SEULEMENT EXTERIEUR'}")


def test_creances():
    """Un salaire qu on ne peut payer devient une dette nommee ; elle se regle plus tard sous son motif d origine,
    ou s abandonne ; l argent se conserve de bout en bout."""
    cat = B.catalogue_du_moteur(); livre = K.GrandLivre(cat)
    livre.declarer_motif("salaire", "remuneration", "test"); livre.declarer_motif("export", "achat", "test")
    cr = K.Creances()
    patron, ouvrier = Firme(30.0), Foyer(0.0)
    paye, c = livre.payer_ou_devoir(patron, ouvrier, 100.0, "salaire", cr, jour=3)
    dette = paye == 30.0 and c is not None and c.montant == 70.0 and livre.impayes["salaire"][0] == 70.0
    livre.recevoir_de_l_exterieur(patron, 50.0, "export")
    regle = cr.regler(c, livre) == 50.0 and c.montant == 20.0 and cr.de(patron) == [c]
    perdu = cr.abandonner(c, "faillite") == 20.0 and cr.abandonnees["faillite"] == 20.0 and not cr.actives and not cr.de(patron)
    conserve = patron.caisse + ouvrier.caisse == 30.0 + 50.0 and ouvrier.caisse == 80.0
    salaires = sum(s for m, p, r, s, n in livre.cloturer_jour()["argent"] if m == "salaire")
    ok = dette and regle and perdu and conserve and salaires == 80.0
    return ok, f"70 de salaire impaye devenu dette, 50 regles plus tard comme salaire, 20 abandonnes a la faillite ; salaires comptes {salaires:.0f}"


# ================================================================== echeancier
def test_echeancier():
    """Porte : un million d echeances sur un an, servies par sauts irreguliers : chacune une fois, a son pas, dans
    l ordre ; les annulees jamais ; une reprise d instantane sert exactement le reste. Falsificateurs : une echeance
    dans le passe est refusee ; un seau perdu se voit au recompte."""
    rng = H.Hasard(3).flux("test_echeancier")
    ech = E.Echeancier(); noms = ("terme", "pret", "peine")
    for t in noms: ech.declarer(t)
    n, fin = 1_000_000, 365 * C.PAS_PAR_JOUR
    pas, types = rng.integers(0, fin, n), rng.integers(0, 3, n)
    t0 = time.perf_counter()
    tickets = [ech.poser(int(p), noms[k], i) for i, (p, k) in enumerate(zip(pas.tolist(), types.tolist()))]
    annules = rng.choice(n, n // 10, replace=False)
    for i in annules.tolist(): ech.annuler(tickets[i], int(pas[i]))
    servies, p, mal_places, snap = [], -1, 0, None
    while p < fin - 1:
        q = min(fin - 1, p + int(rng.integers(1, 300)))
        for t, type_, cle, d in ech.servir(q):
            mal_places += not p < pas[cle] <= q
            servies.append(cle)
        p = q
        if snap is None and p > fin // 2: snap = (pickle.dumps(ech), len(servies))
    ns = (time.perf_counter() - t0) / n * 1e9
    arr = np.array(servies); pp = pas[arr]
    ordre = bool(np.all((pp[1:] > pp[:-1]) | ((pp[1:] == pp[:-1]) & (arr[1:] > arr[:-1]))))
    attendues = np.setdiff1d(np.arange(n), annules)
    completes = len(servies) == len(attendues) and np.array_equal(np.sort(arr), attendues)
    reprise = [e[2] for e in pickle.loads(snap[0]).servir(fin - 1)] == servies[snap[1]:]
    try: ech.poser(0, "terme", 0); passe_refusee = False
    except E.EcheancePassee: passe_refusee = True
    intact = pickle.loads(snap[0]).ecart()
    abime = pickle.loads(snap[0]); perdu = len(abime.seaux.pop(next(k for k, v in abime.seaux.items() if v)))
    ok = (completes and ordre and mal_places == 0 and reprise and passe_refusee and ech.ecart() == 0 and intact == 0
          and abime.ecart() == perdu)
    return ok, (f"{len(servies):,} servies sur {n:,} posees ( {len(annules):,} annulees ), ordre {ordre}, mal placees "
                f"{mal_places}, reprise exacte {reprise}, passe refuse {passe_refusee} ; instantane intact : ecart {intact}, "
                f"seau de {perdu} perdu : ecart {abime.ecart()} ; {ns:.0f} ns par echeance ( pose, annulations, service )")


# ================================================================== objets
def _tirer(ids, rng):
    i = int(rng.integers(0, len(ids)))
    return i, ids[i]


def _oter(ids, i):
    ids[i] = ids[-1]; ids.pop()


def _jouer_parc(graine, n_ops=20_000):
    h = H.Hasard(graine); parc = O.Parc(h)
    for nom, fam in (("berline", "vehicule"), ("camion", "vehicule"), ("fusil", "arme")):
        parc.declarer_modele(nom, fam, prix_monde=1000.0, masse_kg=100.0, vie_h=5000.0)
    rng = h.flux("test_objets")
    ids = []
    for k in range(n_ops):
        op, m, p = int(rng.integers(0, 10)), int(rng.integers(0, 3)), int(rng.integers(0, 20))
        lieu = f"L{int(rng.integers(0, 5))}"
        cohortes = list(parc.cohortes.values())
        if op == 0: ids.append(parc.creer(m, p, lieu, O.SOURCES[int(rng.integers(0, 3))], k, float(rng.random())).id)
        elif op == 1: parc.creer_cohorte(m, p, lieu, int(rng.integers(1, 20)), O.SOURCES[int(rng.integers(0, 3))], float(rng.random()))
        elif op == 2 and ids:
            i, oid = _tirer(ids, rng); parc.sortir(parc.objets[oid], O.PUITS[int(rng.integers(0, 3))]); _oter(ids, i)
        elif op == 3 and cohortes:
            parc.sortir_de_cohorte(cohortes[int(rng.integers(0, len(cohortes)))], int(rng.integers(1, 6)), O.PUITS[int(rng.integers(0, 3))])
        elif op == 4 and ids:
            i, oid = _tirer(ids, rng); parc.ceder(parc.objets[oid], p, ("vente", "vol", "heritage")[int(rng.integers(0, 3))])
        elif op == 5 and cohortes:
            c = cohortes[int(rng.integers(0, len(cohortes)))]
            parc.ceder_de_cohorte(c, int(rng.integers(1, c.nombre + 1)), p, "vente")
        elif op == 6 and cohortes: ids.append(parc.materialiser(cohortes[int(rng.integers(0, len(cohortes)))], k).id)
        elif op == 7 and ids:
            i, oid = _tirer(ids, rng); o = parc.objets[oid]
            if o.etat == O.SERVICE: parc.fondre(o); _oter(ids, i)
        elif op == 8 and ids:
            i, oid = _tirer(ids, rng); o = parc.objets[oid]
            if parc.user(o, float(rng.uniform(0, 500))) > 0.9: parc.mettre_en_etat(o, O.PANNE)
        elif op == 9:
            if ids and rng.random() < 0.5:
                i, oid = _tirer(ids, rng); parc.mettre_en_etat(parc.objets[oid], O.SERVICE)
            elif cohortes:
                c = cohortes[int(rng.integers(0, len(cohortes)))]; parc.deplacer_de_cohorte(c, int(rng.integers(1, c.nombre + 1)), lieu)
    signature = (sorted((o.id, o.modele, o.proprietaire, o.lieu, o.usure, o.etat) for o in parc.objets.values()),
                 sorted((c.modele, c.proprietaire, c.lieu, c.nombre, c.usure) for c in parc.cohortes.values()),
                 parc.comptes, sorted(parc.cessions.items()))
    return parc, signature


def test_objets():
    """Porte : 20 000 operations au hasard ( sources, puits, cessions, materialisations, refontes, usure ) laissent
    chaque modele conserve a l exemplaire pres, et se rejouent a l identique. Falsificateur : un objet pose a la main
    dans le parc se voit."""
    parc, sig = _jouer_parc(5)
    conserve = all(v == 0 for v in parc.verifier().values()) and parc.vivants == parc.recompter()
    rejoue = _jouer_parc(5)[1] == sig and _jouer_parc(6)[1] != sig
    parc2 = O.Parc(H.Hasard(1)); parc2.declarer_modele("berline", "vehicule", 1000.0, 100.0, 5000.0)
    c = parc2.creer_cohorte("berline", "p", "L", 100, "initial", 0.4)
    tires = [parc2.materialiser(c, 0).usure for _ in range(30)]
    usure_conservee = abs(sum(tires) + c.nombre * c.usure - 40.0) <= 1e-9
    parc.objets[10 ** 9] = O.Objet(10 ** 9, 0, 0, "L0", 0.0, O.SERVICE, 0)
    vu = parc.verifier()["berline"] == 1
    ok = conserve and rejoue and usure_conservee and vu
    return ok, (f"{len(parc.objets) - 1} individus, {len(parc.cohortes)} cohortes, {sum(parc.recompter()) - 1} exemplaires : "
                f"conserves {conserve}, rejoues {rejoue}, usure totale conservee a la materialisation {usure_conservee}, "
                f"objet pose a la main vu {vu}")


# ================================================================== decision
SEUIL_JOUET = 0.5 / 1.2          # investir rapporte 1,2 x terrain - 0,3 ; attendre 0,2 : investir si terrain > 0,417


def _obs_jouet(ctx): return (ctx,)
def _regle_jouet(x, ctx): return 1 if x[0] > 0.5 else 0
def _temoin_jouet(x, ctx, rng): return 0          # le temoin bete : toujours attendre


def _point_jouet(horizon):
    return D.PointDeDecision(
        "jouet_investir", "socle", traits=(("terrain", "la qualite de son propre terrain, qu il connait"),),
        actions=("attendre", "investir"), observer=_obs_jouet, regle=_regle_jouet, temoin=_temoin_jouet,
        note="ce que CE choix rapporte a celui qui l a fait", horizon_j=horizon)


def _jouer_jouet(dec, terrains, n_jours, rng, nationale=False):
    """Attendre rapporte 0,2 le lendemain. Investir coute 0,3 le lendemain et rapporte 1,2 x terrain trois jours
    apres. Rend ( part des choix optimaux, gain moyen par agent et par jour )."""
    n = len(terrains); dus = [dict() for _ in range(n)]; gain = 0.0; justes = 0
    for j in range(n_jours):
        if j > 0:
            r = np.array([dus[i].pop(j, 0.0) for i in range(n)]) + rng.normal(0.0, 0.3, n)
            gain += float(r.sum())
            v = np.full(n, r.mean()) if nationale else r
            for i in range(n): dec.noter(i, float(v[i]), j)
        for i in range(n):
            s = float(terrains[i]); a = dec.decider(i, s)
            justes += a == (1 if s > SEUIL_JOUET else 0)
            d = dus[i]
            if a == 1: d[j + 1] = d.get(j + 1, 0.0) - 0.3; d[j + 3] = d.get(j + 3, 0.0) + 1.2 * s
            else: d[j + 1] = d.get(j + 1, 0.0) + 0.2
    return justes / (n * n_jours), gain / (n * (n_jours - 1))


def _former_jouet(horizon, nationale=False):
    dec = D.Decideur(_point_jouet(horizon), "appris", graine=1, epsilon=0.1, alpha=0.05)
    _jouer_jouet(dec, np.random.default_rng(10).random(300), 60, np.random.default_rng(11), nationale)
    return dec


def _examiner(dec_ou_mode, horizon, doctrine=None):
    dec = D.Decideur(_point_jouet(horizon), dec_ou_mode, doctrine=doctrine, graine=2)
    return _jouer_jouet(dec, np.random.default_rng(20).random(300), 20, np.random.default_rng(21))


def test_decision_horizon():
    """Porte : avec une note lue sur trois jours, l agent apprend a investir quand son terrain le vaut ( >= 80 % de
    choix optimaux sur des agents jamais vus ) et bat le temoin bete et le hasard. Controle positif : la meme note
    lue le lendemain seulement apprend a ne jamais investir ( <= 60 % ). Instrument : une note nationale ne varie
    pas avec le choix ( part du choix nulle ), une note individuelle si. Falsificateurs : traits hors bornes, action
    hors catalogue, refuses."""
    forme3 = _former_jouet(3)
    j3, g3 = _examiner("fige", 3, forme3.doctrine)
    jt, gt = _examiner("temoin", 3); jh, gh = _examiner("hasard", 3); jr, gr = _examiner("regle", 3)
    j1, g1 = _examiner("fige", 1, _former_jouet(1).doctrine)
    part_indiv = forme3.part_du_choix()
    part_nat = _former_jouet(3, nationale=True).part_du_choix()
    refus = 0
    for obs, regle in ((lambda c: (1.3,), _regle_jouet), (lambda c: (float("nan"),), _regle_jouet),
                       (lambda c: (0.5, 0.5), _regle_jouet), (_obs_jouet, lambda x, c: 2)):
        p = D.PointDeDecision("faux", "socle", (("t", "test"),), ("a", "b"), obs, regle, _temoin_jouet, "test")
        try: D.Decideur(p, "regle").decider(0, 0.5)
        except (D.TraitHorsBornes, D.ActionHorsCatalogue): refus += 1
    ok = (j3 >= 0.80 and g3 > gt + 0.05 and g3 > gh + 0.05 and j1 <= 0.60 and part_indiv >= 0.01 and part_nat <= 1e-9
          and refus == 4)
    return ok, (f"horizon 3 : {j3:.0%} de choix optimaux, gain {g3:.3f}/jour ( temoin {gt:.3f}, hasard {gh:.3f}, regle "
                f"{gr:.3f} ) ; horizon 1 : {j1:.0%}, gain {g1:.3f} ; part du choix : note individuelle {part_indiv:.3f}, "
                f"nationale {part_nat:.1e} ; {refus}/4 erreurs d observateur ou d action refusees")


# ================================================================== journal
def test_journal():
    """Un million d evenements comptes tiennent dans deux nombres ; les individuels dans une file bornee ; le fichier
    recoit une ligne par evenement individuel et un bilan par jour. Types non declares et champs manquants refuses."""
    with tempfile.TemporaryDirectory() as d:
        chemin = os.path.join(d, "journal.jsonl")
        jl = J.Journal(fichier=chemin, recents_max=1000)
        jl.declarer("naissance", "demographie", "individuel", ("mere", "enfant"))
        jl.declarer("achat", "economie", "compte")
        for _ in range(1_000_000): jl.compter("achat", 2.0)
        for i in range(5000): jl.noter(1, 8.0, "naissance", mere=i, enfant=i + 1)
        bornee = len(jl.recents) == 1000
        refus = 0
        for essai in (lambda: jl.compter("vente"), lambda: jl.noter(1, 8.0, "naissance", mere=1),
                      lambda: jl.noter(1, 8.0, "achat")):
            try: essai()
            except (J.TypeInconnu, ValueError): refus += 1
        bilan = jl.cloturer_jour(1)
        exact = bilan["comptes"]["achat"] == (1_000_000, 2_000_000.0) and bilan["individuels"]["naissance"] == 5000
        lignes = sum(1 for _ in open(chemin))
    ok = bornee and exact and refus == 3 and lignes == 5001 and not jl.comptes
    return ok, f"1 000 000 achats comptes exactement : {exact} ; file bornee a 1000 : {bornee} ; {lignes} lignes ecrites ; {refus}/3 refus"


TESTS = [test_catalogue, test_hasard_par_domaine, test_calendrier, test_registre_reproduit_le_moteur,
         test_registre_voit_un_oubli, test_creation_hors_source, test_socle_ne_change_pas_le_monde,
         test_motifs_du_moteur, test_rapprochement, test_creances, test_echeancier, test_objets,
         test_decision_horizon, test_journal]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t0 = time.perf_counter()
        r, msg = t()
        ok += r
        print(f"{'PASSE' if r else 'ECHOUE':7s} {t.__name__:34s} ({time.perf_counter() - t0:5.1f} s) {msg}", flush=True)
    print(f"{ok} / {len(TESTS)} portes du socle")
    sys.exit(0 if ok == len(TESTS) else 1)
