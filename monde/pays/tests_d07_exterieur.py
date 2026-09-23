"""Les portes du domaine 7 ( reste du monde ). Seuils ecrits avant la premiere mesure.   python -m monde.pays.tests exterieur"""
import math, time
import numpy as np
from .. import monde as W
from ..socle import registre as R
from . import essais as T, d01_population as POP, d07_exterieur as M

JOURS = 12


def _bop_jours(p):
    return list(p.domaine("exterieur").bop.serie)


# ================================================================== la balance des paiements
def test_balance_se_ferme():
    """12 jours : chaque soir, lignes ( biens declares, services, revenus, capital, financier, contrebande ) = variation
    des reserves + erreurs et omissions, et les erreurs et omissions tiennent au centime ( 0,01 drachme par jour et en
    cumul ). La variation des reserves est celle du compteur exterieur du grand livre. Aucune alerte de la douane. Les
    lignes ne sont pas vides : il y a eu des exportations ET des importations ( sinon la porte ne mesure rien ). Les
    reserves en euros = depart + flux exterieurs au taux du jour."""
    w, p = T.monde(["exterieur"], graine=11)
    L = p.socle.livre; e = p.domaine("exterieur")
    ext0 = e.bop.ext_prec
    T.jours(w, JOURS)
    serie = _bop_jours(p)
    pire = max(abs(s[3]) for s in serie)
    b = M.balance_des_paiements(p)
    d_ext = (L.ext["entree"] - L.ext["sortie"]) - ext0
    eu, _ = M.reserves_de_change(p)
    x, m = b["biens"][0], b["biens"][1]
    reserves_ok = abs(eu - (e.reserves0 + (e.ext_reserves - ext0) * e.taux)) <= 1e-6 * max(1.0, abs(eu)) + 1e-3
    ok = (pire <= 0.01 and abs(b["erreurs_omissions"]) <= 0.01 and abs(b["variation_reserves"] - d_ext) <= 0.01
          and not M.alertes_douane(p) and x > 0 and m > 0 and len(serie) == JOURS and reserves_ok)
    lignes = ", ".join(f"{k} {v[2]:+.0f}" for k, v in b.items() if isinstance(v, tuple))
    return ok, (f"{len(serie)} soirs, pire erreurs et omissions {pire:.2e} drachme, cumul {b['erreurs_omissions']:+.2e} ; "
                f"reserves {b['variation_reserves']:+.0f} = compteur exterieur {d_ext:+.0f} ; exportations {x:.0f}, "
                f"importations {m:.0f} ; soldes : {lignes} ; alertes {len(M.alertes_douane(p))} ; reserves en euros "
                f"{'exactes' if reserves_ok else 'FAUSSES'} ( {eu:.0f} )")


def test_sans_argent_hors_livre():
    """La porte commune passe ; et, au-dela d elle, AUCUNE famille n a d argent hors du grand livre : le reste du
    rapprochement de « gouvernement » et « marches » ( importer, exporter_or, ventes au port du moteur ) est nul a la
    tolerance, sur 12 jours ou l Etat importe et exporte son or ( actions forcees le jour 3 )."""
    ok0, msg0 = T.porte_commune("exterieur")
    w, p = T.monde(["exterieur"], graine=11)
    rap = R.Rapprochement(p.socle.registre, p.socle.livre)
    T.jours(w, 3)
    ok_i = w.gouv.appliquer({"type": "importer", "bien": "remedes", "quantite": 20}, w)[0]
    ok_x = w.gouv.appliquer({"type": "exporter_or", "quantite": 1.0}, w)[0]
    T.jours(w, JOURS - 3)
    restes = rap.restes()
    pire = max(restes, key=lambda k: abs(restes[k]))
    net = all(abs(v) <= R.tolerance(v) for v in restes.values())
    ok = ok0 and net and ok_i and ok_x
    return ok, (f"{msg0} || sans porte commune : restes du rapprochement {'tous nuls' if net else 'NON NULS'} ( pire "
                f"{pire} {restes[pire]:+.2e} ; gouvernement {restes['gouvernement']:+.2e}, marches {restes['marches']:+.2e} ) ; "
                f"import de l Etat {'fait' if ok_i else 'REFUSE'}, export d or {'fait' if ok_x else 'REFUSE'}")


def test_flux_energie():
    """Avec le domaine 11 : ses importations de combustible et ses exportations petrolieres ( ses propres motifs ) passent
    par la douane et la balance SANS doublon. 6 jours. Seuils : il y en a eu ; pour chacun de ses motifs, la valeur declaree
    = le paiement vu, au centime ( un paiement pour deux biens est reparti, pas compte deux fois ) ; erreurs et omissions
    nulles au centime ; aucune alerte ; porte de conservation tenue."""
    w, p = T.monde(["exterieur", "energie"], graine=11)
    T.jours(w, 6)
    e = p.domaine("exterieur")
    au = e.douane.autres
    motifs = sorted(au)
    ecart = max((abs(v - x) for v, x in au.values()), default=math.inf)
    eo = max(abs(s[3]) for s in e.bop.serie)
    tenue = p.socle.conservation.tenue()[0]
    ok = len(motifs) >= 2 and ecart <= 0.01 and eo <= 0.01 and not M.alertes_douane(p) and tenue
    return ok, (f"motifs du domaine 11 declares : {', '.join(f'{m} {au[m][0]:.0f} ( paye {au[m][1]:.0f} )' for m in motifs)} ; "
                f"pire ecart declare / paye {ecart:.2e} ; erreurs et omissions {eo:.2e} ; alertes {len(M.alertes_douane(p))} ; "
                f"conservation {'tenue' if tenue else 'ROMPUE'}")


# ================================================================== les prix
def _jumeaux(action, jours_avant=1, jours_apres=30, graine=11):
    out = []
    for avec in (False, True):
        w, p = T.monde(["exterieur"], graine=graine)
        T.jours(w, jours_avant)
        if avec: action(p)
        serie = []
        for _ in range(jours_apres):
            T.jours(w, 1)
            serie.append({b: sum(m.prix[b] for m in w.marches.values()) / len(w.marches) for b in M.BIENS_IMPORT})
        out.append((w, p, serie))
    return out


def _choc_energie(p): M.choc(p, 1.6, famille="energie")
def _choc_manufactures(p): M.choc(p, 1.6, famille="produit_fini")


def test_choc_petrolier():
    """Controle positif : un choc de +60 % sur l energie ( 2022 ) le jour 1. Seuils : la parite a l import du gazole
    monte d au moins 50 % ( le prix du port que lisent le negoce et le domaine 11 ) ; les exportations d energie ( gazole
    et brut ) montent d au moins 30 % ; le prix interieur du gazole, moyen des jours 20 a 30, est au moins 1,15 fois celui
    du jumeau sans choc. Temoin : sans choc, la parite ne bouge que du hasard des prix mondiaux."""
    (w0, p0, s0), (w1, p1, s1) = _jumeaux(_choc_energie)
    par = M.prix_import(p1, "carburant") / M.prix_import(p0, "carburant")
    def ex(p): return sum(v for (sens, b), v in p.domaine("exterieur").douane.cumul_v.items()
                          if sens == "export" and b in ("carburant", "petrole"))
    rx = ex(p1) / max(1e-9, ex(p0))
    dom = np.mean([s["carburant"] for s in s1[19:]]) / np.mean([s["carburant"] for s in s0[19:]])
    ok = par >= 1.5 and rx >= 1.3 and dom >= 1.15
    return ok, (f"parite a l import du gazole x {par:.2f} ; exportations d energie x {rx:.2f} ( {ex(p0):.0f} -> {ex(p1):.0f} "
                f"drachmes ) ; prix interieur du gazole ( jours 20-30 ) x {dom:.3f} ; faim {T.faim(w1):.1%} contre "
                f"{T.faim(w0):.1%}")


def test_choc_importe():
    """Controle positif du canal de l import : +60 % sur les produits manufactures le jour 1 ; le pays importe ses outils.
    Seuil : le prix interieur des outils, moyen des jours 20 a 30, au moins 1,15 fois celui du jumeau sans choc."""
    (w0, p0, s0), (w1, p1, s1) = _jumeaux(_choc_manufactures)
    dom = np.mean([s["outils"] for s in s1[19:]]) / np.mean([s["outils"] for s in s0[19:]])
    def im(p): return p.domaine("exterieur").douane.cumul_q.get(("import", "outils"), 0.0)
    ok = dom >= 1.15
    return ok, (f"prix interieur des outils ( jours 20-30 ) x {dom:.3f} ; outils importes {im(p0):.0f} -> {im(p1):.0f} unites ; "
                f"parite a l import x {M.prix_import(p1, 'outils') / M.prix_import(p0, 'outils'):.2f}")


def test_devaluation():
    """Une devaluation de 20 % le jour 2 : la parite a l import de chaque bien importable est multipliee par 1 / 0,8 =
    1,25 ( a 1e-9 : fob, fret et droit sont proportionnels ) ; une importation de l Etat le jour 3 coute 1,25 fois plus
    par unite ; la parite a l import = ( FOB + fret ) x ( 1 + droit de douane du domaine 6 ). Temoin : le jumeau sans
    devaluation."""
    res = []
    for dev in (False, True):
        w, p = T.monde(["exterieur"], graine=11)
        T.jours(w, 2)
        if dev: M.devaluer(p, 0.2)
        par = {b: M.prix_import(p, b) for b in M.BIENS_IMPORT}
        w.importer("remedes", 10.0)
        d = [x for x in p.domaine("exterieur").douane.jour if x[1] == "import_etat"][-1]
        res.append((par, d[4] / d[3], p))
    (a, ua, p0), (b, ub, p1) = res
    pire = max(abs(b[k] / a[k] - 1.25) for k in a)
    fob, fret = M.prix_port(p0, "nourriture"), M.fret_unitaire(p0, "nourriture")
    formule = abs(M.prix_import(p0, "nourriture") - (fob + fret) * 1.10) <= 1e-9
    ok = pire <= 1e-9 and abs(ub / ua - 1.25) <= 1e-9 and formule
    return ok, (f"parites a l import x 1,25 a {pire:.1e} pres ; importation de l Etat : {ua:.3f} -> {ub:.3f} drachmes par "
                f"unite ( x {ub / ua:.4f} ) ; nourriture : ( FOB {fob:.3f} + fret {fret:.3f} ) x 1,10 "
                f"{'= parite' if formule else 'DIFFERENT de la parite'}")


# ================================================================== les migrations
def test_migrations():
    """Taux multiplies par 100 ( controle positif : un flux mesurable sur 500 habitants ; x 25 n en attendait que 8,7,
    sous le minimum de 20 ecrit ci-dessous ), 20 jours. Seuils : les
    departs tires tombent a 3 ecarts-types de la somme des hasards declares ( Poisson ), et au moins 20 sont attendus ;
    les menages immigres aussi ; aucun emigre compte comme mort ; vivants = depart + naissances - deces + immigres -
    emigres ; aucune anomalie de famille ( domaine 1 ) ; etat civil recompte ; l epargne des emigres est sortie par le
    compte de capital, celle des immigres y est entree. Temoin : a taux x 1, moins de 5 departs attendus."""
    w, p = T.monde(["exterieur"], graine=13)
    e = p.domaine("exterieur"); e.facteur_migration = 100.0
    T.jours(w, 20)
    d = p.domaine("population"); col = p.colonnes["habitant"]
    z_e = (e.departs - e.attendu_emigration) / math.sqrt(max(1e-9, e.attendu_emigration))
    z_i = (e.menages_immigres - e.attendu_immigration) / math.sqrt(max(1e-9, e.attendu_immigration))
    n = len(w.habitants)
    emig = [i for i in range(n) if col["ext_emigre_j"][i] >= 0]
    morts = sum(1 for h in w.habitants if not h.vivant and col["ext_emigre_j"][h.id] < 0 and col["deces_j"][h.id] >= 0)
    faux_morts = sum(1 for i in emig if w.habitants[i].vivant)
    viv, att = M.bilan_population(p)
    anom = POP.anomalies_familles(p)
    ec = POP.recompte_etat_civil(p) == d.etat_civil.inscrits_vivants
    b = M.balance_des_paiements(p)["capital"]
    capital = b[1] >= e.epargne_sortie - 0.01 and b[0] >= e.epargne_entree - 0.01 and e.epargne_sortie > 0
    w2, p2 = T.monde(["exterieur"], graine=13); T.jours(w2, 20)
    temoin = p2.domaine("exterieur").attendu_emigration
    ok = (abs(z_e) <= 3 and abs(z_i) <= 3 and e.attendu_emigration >= 20 and morts == d.deces - e.deces0
          and faux_morts == 0 and viv == att and not anom and ec and capital and temoin < 5)
    return ok, (f"departs {e.departs} pour {e.attendu_emigration:.1f} attendus ( z {z_e:+.2f} ), {e.n_emigres} emigres avec "
                f"les accompagnants ; menages immigres {e.menages_immigres} pour {e.attendu_immigration:.1f} ( z {z_i:+.2f} ), "
                f"{e.n_immigres} personnes ; deces {d.deces - e.deces0} = morts {morts} ; vivants {viv} = attendus {att} ; "
                f"anomalies {len(anom)} ; etat civil {'recompte' if ec else 'FAUX'} ; epargne sortie {e.epargne_sortie:.0f}, "
                f"entree {e.epargne_entree:.0f} ( capital : credit {b[0]:.0f}, debit {b[1]:.0f} ) ; temoin x1 : "
                f"{temoin:.2f} departs attendus")


# ================================================================== le falsificateur
def test_falsificateur():
    """Trois mondes de meme graine. Intact : aucune alerte, erreurs et omissions nulles. Un import de 100 rations SANS
    paiement ( livre.importer sous le motif du negoce, le jour 2 ) : la douane le voit, 100 unites non declarees. Une
    vente au port ecrite a la main comme le moteur le faisait ( caisse += 1000, ext += 1000, le jour 2 ) : les erreurs et
    omissions du soir valent 1000."""
    out = []
    for cas in ("intact", "import", "main"):
        w, p = T.monde(["exterieur"], graine=11)
        T.jours(w, 2)
        if cas == "import":
            p.socle.livre.importer(M.StockE1(w.publics["reserve"], p.socle.catalogue), p.socle.catalogue.id("nourriture"),
                                   100.0, "import_biens")
        elif cas == "main":
            w.gouv.caisse += 1000.0; w.ext["entree"] += 1000.0
        T.jours(w, 1)
        out.append((M.alertes_douane(p), p.domaine("exterieur").bop.serie[-1][3], M.balance_des_paiements(p)["erreurs_omissions"]))
    (a0, eo0, c0), (a1, eo1, c1), (a2, eo2, c2) = out
    vu_import = any(x[1] == "non_declare" and x[3] == "nourriture" and abs(x[4] - 100.0) <= 1e-6 for x in a1)
    ok = not a0 and abs(c0) <= 0.01 and vu_import and abs(eo2 - 1000.0) <= 0.01
    return ok, (f"intact : {len(a0)} alerte, erreurs et omissions {c0:+.2e} ; import sans paiement : "
                f"{'VU' if vu_import else 'PAS VU'} ( {a1[:1]} ) ; vente a la main : erreurs et omissions du soir {eo2:+.2f}")


# ================================================================== la decision
def test_decision_importer():
    """Mode hasard, 16 jours ( 63 decisions par jour ) : la part du choix ( epsilon carre intra-jour ) >= 0,01 ET le
    hasard permute fait moins bien ( p < 0,05 ). Mesures : la regle et le temoin ( expedier sans condition ) sur le meme
    monde - la note moyenne de chacun."""
    w, p = T.monde(["exterieur"], graine=11, modes={"importer": "hasard"})
    T.jours(w, 16)
    d = p.domaine("exterieur").decideur
    eps, pp = d.part_du_choix(), d.p_permutation()
    moy = {}
    for mode in ("regle", "temoin"):
        w2, p2 = T.monde(["exterieur"], graine=11, modes={"importer": mode}); T.jours(w2, 16)
        na = p2.domaine("exterieur").decideur.notes_par_action()
        tot = sum(n for n, _ in na.values())
        moy[mode] = (sum(n * m for n, m in na.values()) / max(1, tot), T.faim(w2))
    ok = eps >= 0.01 and pp < 0.05
    notes = ", ".join(f"{a} {m:+.4f} ( {n} )" for a, (n, m) in d.notes_par_action().items())
    return ok, (f"epsilon carre {eps:.3f}, p {pp:.3f} ; au hasard : {notes} ; regle {moy['regle'][0]:+.4f} ( faim "
                f"{moy['regle'][1]:.1%} ), temoin {moy['temoin'][0]:+.4f} ( faim {moy['temoin'][1]:.1%} )")


# ================================================================== le cout
def test_cout():
    """Les routines propres du domaine ( chronometrees ) coutent au plus 10 % d une journee du moteur seul, a 10 000
    habitants."""
    w0 = W.Monde(echelle=20)
    T.jours(w0, 1)
    t0 = time.perf_counter(); T.jours(w0, 2); t_e1 = (time.perf_counter() - t0) / 2
    w, p = T.monde(["exterieur"], echelle=20)
    T.jours(w, 1)
    e = p.domaine("exterieur"); e.chrono.clear()
    t0 = time.perf_counter(); T.jours(w, 2); t_pays = (time.perf_counter() - t0) / 2
    propre = sum(e.chrono.values()) / 2
    detail = ", ".join(f"{k} {v / 2 * 1000:.0f}" for k, v in sorted(e.chrono.items(), key=lambda kv: -kv[1]))
    ok = propre <= 0.10 * t_e1
    return ok, (f"{len(w.habitants)} habitants : moteur seul {t_e1:.2f} s par jour, pays avec l exterieur et ses dependances "
                f"{t_pays:.2f} s ; routines propres {propre * 1000:.0f} ms par jour ( {propre / t_e1:.1%} ; {detail} ms ), "
                f"{propre / len(w.habitants) * 1e6:.1f} us par habitant")


TESTS = [test_balance_se_ferme, test_sans_argent_hors_livre, test_flux_energie, test_choc_petrolier, test_choc_importe, test_devaluation,
         test_migrations, test_falsificateur, test_decision_importer, test_cout]
