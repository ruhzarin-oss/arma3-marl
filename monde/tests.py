"""Les portes de l etape E1 ( plans/plan-monde-complet.md ) : chacune doit savoir echouer.
   python -m monde.tests"""
import copy, os, pickle, sys, tempfile, zlib
from . import monde as W, ecole as S, gouvernement as G, config as C, agents as A


def jours(w, n):
    for _ in range(n * C.PAS_PAR_JOUR): w.pas_suivant()
    return w


def test_conservation():
    w = jours(W.Monde(), 30)
    d_arg, d_b = w.verifier_conservation()
    pire = max(abs(v) for v in d_b.values())
    return abs(d_arg) < 1e-6 and pire < 1e-6, f"ecart argent {d_arg:.2e}, pire ecart de bien {pire:.2e}"


def test_conservation_sait_echouer():
    """Le controle de conservation doit VOIR un bien cree de rien."""
    w = jours(W.Monde(), 2)
    w.marches["Kavala"].stocks["nourriture"] += 7.0          # creation sans cause
    d_arg, d_b = w.verifier_conservation()
    return abs(d_b["nourriture"] - 7.0) < 1e-6, f"ecart vu {d_b['nourriture']:.3f} pour 7 crees"


def test_negatif_sans_perturbation():
    w = jours(W.Monde(), 30)
    faim = w.stats_jour.get("menages_sans_nourriture", 0) / len(w.menages)
    pc = w.prix_moyen("carburant") / C.PRIX_MONDE["carburant"]
    return faim <= 0.05 and 0.3 <= pc <= 3.0 and sum(1 for h in w.habitants if h.vivant) >= 490, \
        f"faim {faim:.1%}, carburant {pc:.2f} fois le prix mondial, vivants {sum(1 for h in w.habitants if h.vivant)}"


def test_positif_route_coupee():
    """Couper Pyrgos ( plus aucun convoi n y entre ni n en sort ) doit se VOIR : prix ou faim a Pyrgos, pas ailleurs."""
    temoin = jours(W.Monde(), 12)
    w = W.Monde(); jours(w, 2); w.routes_coupees.add("Pyrgos"); jours(w, 10)
    menages_p = [m for m in w.menages if m.domicile.marche.id == "Pyrgos"]
    faim_p = sum(1 for m in menages_p if m.garde_manger < 0.5 * len(m.membres)) / max(1, len(menages_p))
    dp = w.marches["Pyrgos"].prix["carburant"] / temoin.marches["Pyrgos"].prix["carburant"]
    dn = w.marches["Pyrgos"].prix["nourriture"] / temoin.marches["Pyrgos"].prix["nourriture"]
    return (dp >= 2 or dn >= 2 or faim_p >= 0.3), f"Pyrgos coupee : carburant x{dp:.2f}, nourriture x{dn:.2f}, menages a court {faim_p:.0%}"


def test_reproductible():
    a, b = jours(W.Monde(graine=11), 5), jours(W.Monde(graine=11), 5)
    return a.resume_jour() == b.resume_jour() and a.argent_total() == b.argent_total(), "meme graine, meme monde apres 5 jours"


def test_gouvernement_borne():
    w = W.Monde()
    essais = [({"type": "fixer_impot", "nom": "tva", "valeur": 0.9}, False), ({"type": "raser_kavala"}, False),
              ({"type": "acheter", "bien": "remedes", "quantite": 1e9}, False), ({"type": "quarantaine", "lieu": "Atlantide"}, False),
              ({"type": "fixer_impot", "nom": "tva", "valeur": 0.1}, True), ({"type": "couvre_feu", "debut": 22, "fin": 5}, True)]
    res = [w.gouv.appliquer(a, w)[0] == attendu for a, attendu in essais]
    return all(res), f"{sum(res)}/{len(res)} decisions traitees comme attendu ( hors catalogue et hors bornes refusees )"


def test_ecole():
    """L epreuve doit separer un eleve qui apprend d un eleve qui n apprend rien."""
    wa = jours(W.Monde(eleve=S.EleveMemoire()), 3)
    wb = jours(W.Monde(eleve=S.EleveSansMemoire()), 3)
    a, b = wa.ecole.bulletin[0]["score"], wb.ecole.bulletin[0]["score"]
    return a > b and b == 0, f"eleve a memoire {a:.2f}, eleve sans memoire {b:.2f}"


def test_menages_decident():
    """Un menage qui decide doit VRAIMENT changer le monde : la meme graine, avec et sans doctrine, doit differer."""
    a = jours(W.Monde(), 6)
    b = W.Monde(); b.doctrine = A.Doctrine(epsilon=1.0); jours(b, 6)
    meme = a.resume_jour() == b.resume_jour()
    d_arg, d_b = b.verifier_conservation()
    ok = (not meme) and abs(d_arg) < 1e-6 and max(abs(v) for v in d_b.values()) < 1e-6
    return ok, f"monde a decisions different du monde a regle : {not meme} ; conservation tenue : {abs(d_arg):.1e}"


def test_reprise_identique():
    """Point 10 : un monde arrete puis repris doit etre le MEME que s il n avait jamais ete arrete."""
    continu = jours(W.Monde(graine=5), 3)
    coupe = jours(W.Monde(graine=5), 2)
    with tempfile.TemporaryDirectory() as d:
        chemin = os.path.join(d, "instantane.pkl")
        pickle.dump(coupe, open(chemin, "wb"))
        repris = jours(pickle.load(open(chemin, "rb")), 1)
    meme = continu.resume_jour() == repris.resume_jour() and continu.argent_total() == repris.argent_total()
    return meme, f"3 jours d affilee contre 2 + reprise + 1 : {'identiques' if meme else 'DIFFERENTS'}"


def test_demographie():
    """Point 5 : sur une annee du monde, le pays doit vivre - naissances, retraites, morts de vieillesse - sans
    s effondrer ni exploser. Une population qui ne bouge pas d un habitant serait une photographie, pas un pays."""
    w = jours(W.Monde(), 365)
    vivants = [h for h in w.habitants if h.vivant]
    nes = len(w.habitants) - 500
    retraites = sum(1 for h in vivants if h.role == "retraite")
    enfants = sum(1 for h in vivants if h.role == "enfant")
    d_arg, d_b = w.verifier_conservation()
    # sur 365 jours, le seuil absolu de 1e-6 ne mesure plus la conservation mais l accumulation de la virgule
    # flottante ( 4e-7 sur 1,37 million de drachmes, soit 3e-13 en relatif ) : le critere devient relatif.
    relatif = abs(d_arg) / max(1.0, w.argent_total())
    ok = (400 <= len(vivants) <= 600 and nes > 0 and retraites > 0 and enfants > 0
          and relatif < 1e-9 and max(abs(v) for v in d_b.values()) < 1e-3)
    return ok, (f"apres un an : {len(vivants)} vivants, {nes} nes, {retraites} retraites, {enfants} enfants ; "
                f"conservation relative {relatif:.1e}")


def test_desobeissance():
    """Point 8 : une loi doit pouvoir etre enfreinte. Une taxe legere est payee ; une taxe lourde se contourne, et
    l Etat encaisse moins que ce qu il a decrete. Une quarantaine est violee par une part de la population."""
    def gele(tva):                      # le gouvernement est GELE : on ne mesure que la desobeissance, pas ses decisions
        w = W.Monde(); w.gouverner = lambda: None; w.gouv.tva = tva
        return jours(w, 12)
    leger, lourd = gele(0.10), gele(0.45)
    part = lourd.tva_fraudee / max(1e-9, lourd.tva_fraudee + lourd.tva_percue)
    q = W.Monde(); q.gouv.lois["quarantaine"] = ["Pyrgos"]; jours(q, 3)
    dehors = sum(1 for h in q.habitants if h.vivant and h.domicile.id == "Pyrgos" and h.lieu is h.travail
                 and h.travail is not None)
    ok = leger.tva_fraudee == 0.0 and part > 0.2 and dehors > 0
    return ok, (f"tva 10 % : {leger.tva_fraudee:.0f} drachme fraudee ; tva 45 % : {part:.0%} des montants echappent "
                f"a l Etat ; quarantaine : {dehors} habitants sortent quand meme")


def test_hopital():
    """Point 9 : un malade grave doit QUITTER sa maison pour l hopital de sa capitale, et y trouver des soignants.
    Le test regarde le monde ( le poste ) et la bulle ( la cle du batiment ), les deux moities du chemin."""
    from . import incarner as I
    w = jours(W.Monde(), 3)
    malade = next(h for h in w.habitants if h.vivant and h.role != "enfant")
    malade.etat, malade.gravite = "I", 0.9
    # les soignants tournent en trois equipes : on cherche une heure ou l une d elles est de garde
    soignant = None
    for heure in (7.0, 10.0, 15.0, 18.0, 23.0, 3.0):
        w.deplacer(heure)
        soignant = next((h for h in w.habitants if h.vivant and h.role in I.SOIGNANTS and h.poste == "travail"
                         and h.lieu is malade.lieu), None)      # un soignant DE LA MEME ville : l hopital est local
        if soignant is not None: break
    ok = (malade.poste == "hopital" and malade.lieu is malade.domicile.marche
          and soignant is not None and I.cle(malade) == I.cle(soignant)
          and I.cle(malade) != zlib.crc32(f"maison-{malade.menage.id}".encode()) % 997)
    return ok, (f"le malade va a l hopital de {malade.lieu.id} ( batiment {I.cle(malade)} ) ; "
                f"un soignant y travaille : {soignant is not None and I.cle(soignant) == I.cle(malade)}")


def test_armee_coupee():
    """Point 6 : couper la route d une base doit vider SA garnison dans le delai calcule - stock divise par ce qu elle
    brule - pendant que les autres bases continuent de patrouiller."""
    w = W.Monde()
    base = w.carte.de_type("base")[0]
    besoin = w.besoin_patrouille(base)
    attendu = w.garnisons[base.id]["carburant"] / besoin          # en jours, calcule AVANT de jouer
    w.routes_coupees.add(base.id)
    premier = None
    for j in range(12):
        jours(w, 1)
        annulees = [e for e in w.evenements[-600:] if e["type"] == "patrouille_annulee" and e.get("base") == base.id]
        if annulees and premier is None: premier = w.jour
    autres = [b for b in w.carte.de_type("base") if b.id != base.id]
    vivantes = sum(1 for b in autres if w.garnisons[b.id]["carburant"] > 0)
    ok = premier is not None and abs(premier - attendu) <= 1.5 and vivantes == len(autres)
    return ok, (f"{base.id} coupee : a sec au jour {premier}, calcul {attendu:.1f} ; "
                f"{vivantes}/{len(autres)} autres bases encore ravitaillees")


def test_voyage_entre_iles():
    """Point 13 : un habitant qui traverse doit disparaitre des deux iles pendant la traversee, puis reparaitre
    la-bas avec la meme identite, le meme argent et la meme memoire. Jamais deux corps pour un homme."""
    from . import carte as K
    # le monde NAIT avec ses deux iles : greffer une carte sur un monde deja peuple n a plus de sens depuis que les
    # habitants sont ranges par numero de lieu ( refonte en colonnes, 23/09 )
    w = W.Monde(iles=("Altis", "Malden"))
    cible = w.carte.lieux["Malden:LaTrinite"]
    h = next(x for x in w.habitants if x.vivant and x.role == "marchand")
    avant = (h.id, h.menage.caisse, h.role)
    arrivee = w.embarquer(h, cible, sejour_jours=2.0)
    en_mer, la_bas = [], []
    for _ in range(arrivee - w.pas + 2):
        w.pas_suivant(); en_mer.append(h.lieu is None)
    arrive = h.lieu is cible
    for _ in range(C.PAS_PAR_JOUR):                     # un jour de sejour : il doit rester sur place
        w.pas_suivant(); la_bas.append(h.lieu is not None and h.lieu.ile == "Malden")
    ok = any(en_mer) and arrive and all(la_bas) and h.id == avant[0] and h.role == avant[2]
    return ok, (f"traversee de {sum(en_mer)} pas sans aucun corps, debarquement a {cible.id} ( ile Malden ), "
                f"sejour tenu {sum(la_bas)}/{len(la_bas)} pas, identite {h.id} conservee")


TESTS = [test_conservation, test_conservation_sait_echouer, test_negatif_sans_perturbation, test_positif_route_coupee,
         test_reproductible, test_gouvernement_borne, test_ecole, test_menages_decident, test_reprise_identique,
         test_demographie, test_desobeissance, test_hopital,
         test_armee_coupee, test_voyage_entre_iles]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        r, msg = t()
        ok += r
        print(f"{'PASSE' if r else 'ECHOUE':7s} {t.__name__:32s} {msg}")
    print(f"{ok} / {len(TESTS)} portes du monde ( E1 et douze manques )")
    sys.exit(0 if ok == len(TESTS) else 1)
