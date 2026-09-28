"""LES PORTES DE L INSTRUMENT DE RESSEMBLANCE ( monde/ressemblance.py ).   python -m monde.tests_ressemblance [ nom ... ]

Un instrument qui ne sait pas echouer ne mesure rien. Sept portes, seuils ecrits avant la premiere mesure :
  - references      : chaque indicateur a sa definition, sa source, son adresse, sa bande ( qui contient la valeur ) et
                      sa mesure ; chaque mesure a sa reference ;
  - controle positif synthetique : des mesures egales aux valeurs reelles passent TOUTES ; un indicateur deplace de
                      deux largeurs de bande ( vers le haut, puis vers le bas ) echoue, LUI SEUL ; un NonMesurable ne
                      rend non mesurable que lui ;
  - controle positif sur le vrai monde : les defauts CONNUS du monde par defaut ( ~12 % de militaires contre ~1,1 %,
                      ~1,7 personne par menage contre 2,4, aucun enfant de moins de 6 ans ) sortent hors bande, du bon
                      cote ; sinon l instrument est aveugle ;
  - falsificateurs : doubler les lits d hopital double l indicateur des lits et laisse TOUS les autres identiques au
                      bit ; tuer un habitant sur dix fait monter la mortalite d au moins une bande, du nombre exact de
                      morts, et laisse la structure par age et par sexe a moins d un quart de demi-bande ;
  - determinisme    : deux mesures du meme monde sont identiques ; deux mondes de meme graine donnent la meme mesure ;
  - lecture seule   : l empreinte du monde ( pickle et porte d identite ) est la meme avant et apres la mesure ; un
                      monde suivi et mesure chaque jour et son jumeau jamais mesure restent identiques trois jours
                      ( empreinte de monde/porte_domaines.py, resume, argent, mesure finale ) ; chaque preuve a son
                      controle positif : un milliardieme de drachme pose a la main est vu ;
  - cout            : mesurer un monde de 10 000 habitants coute moins d une seconde ;
  - non mesurable   : sans le domaine, la ligne dit « non mesurable » et pourquoi, sans exception ni zero invente."""
import hashlib, pickle, sys, time
import numpy as np
from . import config as C, ressemblance as RS, porte_domaines as PD
from .pays import essais as E, d01_population as D1

ECHELLE_REFERENCE = 20.0          # 10 000 habitants : l echelle de la mesure livree
CHAUFFE_J, SUIVI_J = 1, 2
_CACHE = {}


def monde_suivi(echelle=ECHELLE_REFERENCE, graine=C.GRAINE, domaines=None, chauffe=CHAUFFE_J, jours=SUIVI_J):
    """Un monde, sa chauffe, puis `jours` jours sous Suivi. Rend ( w, p, suivi )."""
    w, p = E.monde(domaines, graine=graine, echelle=echelle)
    E.jours(w, chauffe)
    s = RS.Suivi(w, p)
    for _ in range(jours):
        E.jours(w, 1); s.apres_jour(w, p)
    return w, p, s


def reference():
    """Le monde par defaut a 10 000 habitants, tous les domaines, construit une fois pour toutes les portes."""
    if "ref" not in _CACHE: _CACHE["ref"] = monde_suivi()
    return _CACHE["ref"]


def copie(w):
    w2 = pickle.loads(pickle.dumps(w, protocol=pickle.HIGHEST_PROTOCOL))
    return w2, w2.pays


def empreinte(w):
    return hashlib.sha256(pickle.dumps(w, protocol=pickle.HIGHEST_PROTOCOL)).hexdigest()


def _par_id(lignes): return {l["id"]: l for l in lignes}


# ================================================================== les portes
def test_references():
    refs = RS.charger()
    manque = [i for i in refs if i not in RS.MESURES]
    orphelines = [i for i in RS.MESURES if i not in refs]
    vides = [i for i, r in refs.items() if not r["source"].strip() or not r["adresse"].startswith("http")
             or len(r["justification"]) < 20 or len(r["definition"]) < 20]
    av = [i for i, r in refs.items() if r.get("a_verifier")]
    ok = not manque and not orphelines and not vides and 30 <= len(refs) <= 45
    return ok, (f"{len(refs)} indicateurs ( {len(av)} a verifier : {', '.join(av) or 'aucun'} ) ; sans mesure {manque} ; "
                f"mesures sans reference {orphelines} ; fiches incompletes {vides}")


def test_controle_positif_synthetique():
    refs = RS.charger()
    exact = {i: RS.Mesure(r["valeur"], "synthetique") for i, r in refs.items()}
    tous = all(l["verdict"] == RS.DANS for l in RS.juger(refs, exact))
    bords = {i: RS.Mesure(r["bande"][k], "synthetique") for k in (0, 1) for i, r in refs.items()}
    bords_ok = all(l["verdict"] == RS.DANS for l in RS.juger(refs, bords))
    faux, vus = [], 0
    for i, r in refs.items():
        bas, haut = r["bande"]
        for signe in (+1, -1):
            v = dict(exact); v[i] = RS.Mesure(r["valeur"] + signe * 2.0 * (haut - bas), "synthetique")
            l = RS.juger(refs, v)
            hors = [x["id"] for x in l if x["verdict"] != RS.DANS]
            bon_cote = all((x["ecart"] > 1) if signe > 0 else (x["ecart"] < -1) for x in l if x["id"] == i)
            if hors != [i] or not bon_cote: faux.append((i, signe, hors))
            vus += 1
        v = dict(exact); v[i] = RS.NonMesurable("controle")
        nm = [x["id"] for x in RS.juger(refs, v) if x["verdict"] != RS.DANS]
        if nm != [i]: faux.append((i, "non_mesurable", nm))
    ok = tous and bords_ok and not faux
    return ok, (f"valeurs reelles : {'toutes dans la bande' if tous else 'ECHEC'} ; bords compris : "
                f"{'oui' if bords_ok else 'NON'} ; {vus} deplacements de deux bandes : "
                f"{vus - len([f for f in faux if f[1] != 'non_mesurable'])} n ont fait sortir que l indicateur deplace, "
                f"du bon cote ; erreurs {faux[:5]}")


def test_controle_positif_monde():
    w, p, s = reference()
    L = _par_id(RS.mesurer(w, p, suivi=s))
    attendus = (("part_militaires", +1), ("taille_menages", -1), ("part_moins_5", -1))
    res, ok = [], True
    for i, sens in attendus:
        l = L[i]
        bon = l["verdict"] == RS.HORS and l["ecart"] is not None and l["ecart"] * sens > 1
        ok &= bon
        res.append(f"{i} {RS._fmt(l['simule'])} contre {RS._fmt(l['reel'])} [{RS._fmt(l['bande'][0])} ; "
                   f"{RS._fmt(l['bande'][1])}] : {l['verdict']} ( {l['ecart']:+.1f} ){'' if bon else ' AVEUGLE'}")
    return ok, f"{w.table.n} habitants, jour {w.jour} : " + " ; ".join(res)


def test_falsificateur_lits():
    """Doubler les lits d hopital ( des lits libres ajoutes a chaque etablissement, sur une copie ) : l indicateur des
    lits double, les autres restent identiques au bit."""
    w, p, s = reference()
    avant = _par_id(RS.mesurer(w, p, suivi=s))
    w2, p2 = copie(w)
    for e in p2.domaine("hopitaux").etabs:
        e.lits_occ.extend([-1] * len(e.lits_occ)); e.rea_occ.extend([-1] * len(e.rea_occ))
    apres = _par_id(RS.mesurer(w2, p2, suivi=s))
    a, b = avant["lits_hopital"]["simule"], apres["lits_hopital"]["simule"]
    double = a is not None and b is not None and abs(b / a - 2.0) < 1e-12
    bouge = [i for i in avant if i != "lits_hopital" and (avant[i]["simule"], avant[i]["verdict"])
             != (apres[i]["simule"], apres[i]["verdict"])]
    ok = double and not bouge
    return ok, (f"lits {RS._fmt(a)} -> {RS._fmt(b)} pour 1000 ( x{b / a:.6f}, {avant['lits_hopital']['verdict']} -> "
                f"{apres['lits_hopital']['verdict']} ) ; autres indicateurs changes : {bouge or 'aucun'}")


STRUCTURE = ("part_0_14", "part_15_64", "part_65_plus", "part_moins_5", "age_median", "rapport_masculinite")


def test_falsificateur_morts():
    """Tuer un habitant vivant sur dix ( un numero sur dix, cause naturelle, sur une copie ) : la mortalite monte d au
    moins une bande et compte exactement ces morts en plus ; la structure par age et par sexe ne bouge pas de plus d un
    quart de demi-bande."""
    w, p, s = reference()
    avant = _par_id(RS.mesurer(w, p, suivi=s))
    w2, p2 = copie(w)
    ids = np.nonzero(w2.table.vivant[:w2.table.n] == 1)[0][::10].tolist()
    for i in ids: D1.deceder(p2, w2.habitants[i], "naturelle")
    apres = _par_id(RS.mesurer(w2, p2, suivi=s))
    ma, mb = avant["mortalite"], apres["mortalite"]
    compte = ma["evenements"] is not None and mb["evenements"] is not None and \
        mb["evenements"] - ma["evenements"] == len(ids)
    monte = mb["ecart"] is not None and ma["ecart"] is not None and mb["ecart"] >= ma["ecart"] + 1.0
    derive = {i: abs(apres[i]["ecart"] - avant[i]["ecart"]) for i in STRUCTURE
              if apres[i]["ecart"] is not None and avant[i]["ecart"] is not None}
    stable = all(d < 0.25 for d in derive.values()) and len(derive) == len(STRUCTURE)
    verdicts = [i for i in avant if avant[i]["verdict"] != apres[i]["verdict"]]
    ok = compte and monte and stable
    return ok, (f"{len(ids)} morts posees : mortalite {RS._fmt(ma['simule'])} -> {RS._fmt(mb['simule'])} pour 1000 "
                f"( ecart {ma['ecart']:+.1f} -> {mb['ecart']:+.1f} ; compte exact {'oui' if compte else 'NON'} ) ; "
                f"derive maximale de la structure {max(derive.values()):.3f} demi-bande ; verdicts changes : "
                f"{verdicts or 'aucun'}")


def test_emigre_n_est_pas_mort():
    """Faire emigrer des adultes ( un sur vingt parmi ceux qui laissent un autre adulte au menage, par le domaine 7, sur
    une copie ) : la mortalite ne bouge pas, au deces pres. Controle positif : le compte brut des dates de deces, lui,
    monte d autant ( le domaine 7 pose deces_j au jour de la sortie ) - c est ce qui doublait la mortalite du pays grec
    le 27/09 ( 16 emigres sur 27 « deces » en 35 jours )."""
    from .pays import d07_exterieur as D7
    w, p, s = reference()
    avant = _par_id(RS.mesurer(w, p, suivi=s))
    w2, p2 = copie(w)
    tb = w2.table; n = tb.n
    gens = [w2.habitants[i] for i in np.nonzero(tb.vivant[:n] == 1)[0].tolist()
            if D1.age_de(p2, w2.habitants[i]) >= D1.AGE_MAJEUR]
    gens = [h for h in gens if h.menage is not None and len(D1.adultes_vivants(p2, h.menage)) >= 2][::20]
    dj = p2.col("habitant", "deces_j")
    brut0 = int((dj >= s.depuis_jour).sum()) if hasattr(s, "depuis_jour") else int((dj >= 0).sum())
    partis = 0
    for h in gens:
        if h.vivant and len(D1.adultes_vivants(p2, h.menage)) >= 2: D7.emigrer(p2, [h]); partis += 1
    brut1 = int((dj >= s.depuis_jour).sum()) if hasattr(s, "depuis_jour") else int((dj >= 0).sum())
    apres = _par_id(RS.mesurer(w2, p2, suivi=s))
    ma, mb = avant["mortalite"], apres["mortalite"]
    meme = ma["evenements"] == mb["evenements"]
    vu = brut1 - brut0 == partis and partis > 0
    return meme and vu, (f"{partis} emigres poses : deces comptes {ma['evenements']} -> {mb['evenements']} "
                         f"( identiques {'oui' if meme else 'NON'} ) ; controle positif : dates de deces brutes "
                         f"+{brut1 - brut0} ( {'vu' if vu else 'NON VU'} )")


def test_determinisme():
    w, p, s = reference()
    a, b = RS.mesurer(w, p, suivi=s), RS.mesurer(w, p, suivi=s)
    meme = repr(a) == repr(b)
    x = monde_suivi(echelle=2.0, graine=5)
    y = monde_suivi(echelle=2.0, graine=5)
    jumeaux = repr(RS.mesurer(x[0], x[1], suivi=x[2])) == repr(RS.mesurer(y[0], y[1], suivi=y[2]))
    return meme and jumeaux, (f"deux mesures du meme monde {'identiques' if meme else 'DIFFERENTES'} ; deux mondes de "
                              f"graine 5 ( 1 000 habitants ) {'identiques' if jumeaux else 'DIFFERENTS'}")


def test_lecture_seule():
    """Deux preuves, chacune avec son controle positif. 1. Le meme monde : l empreinte complete ( pickle, et
    l empreinte de la porte d identite des domaines ) est la meme avant et apres deux mesures ; une ecriture d un
    milliardieme de drachme la change. 2. Deux jumeaux de meme graine, l un suivi et mesure chaque jour, l autre
    jamais : meme empreinte de la porte d identite, meme resume, meme argent, meme mesure finale apres trois jours ; un
    milliardieme de drachme pose dans l un les separe. ( Le pickle de deux mondes construits a part n est pas le meme
    octet a octet, meme sans mesure : la comparaison des jumeaux passe par l empreinte de monde/porte_domaines.py. )"""
    w, p, s = reference()
    e0, d0 = empreinte(w), PD.empreinte(w)
    RS.mesurer(w, p, suivi=s); RS.tableau_markdown(RS.mesurer(w, p, suivi=s))
    meme = empreinte(w) == e0 and PD.empreinte(w) == d0
    w2, _ = copie(w)
    e2 = empreinte(w2); w2.table.menages.caisse[3] += 1e-9
    vu1 = empreinte(w2) != e2
    def jumeaux(saboter):
        a = E.monde(None, graine=7, echelle=2.0); b = E.monde(None, graine=7, echelle=2.0)
        sa, sb = RS.Suivi(*a), RS.Suivi(*b)
        for j in range(3):
            if saboter and j == 1: b[0].table.menages.caisse[3] += 1e-9
            E.jours(a[0], 1); sa.apres_jour(*a); RS.mesurer(a[0], a[1], suivi=sa)
            E.jours(b[0], 1); sb.apres_jour(*b)
        ecarts = [k for k, v in PD.empreinte(a[0]).items() if PD.empreinte(b[0]).get(k) != v]
        pareil = not ecarts and a[0].resume_jour() == b[0].resume_jour() and \
            a[0].argent_total() == b[0].argent_total() and \
            repr(RS.mesurer(a[0], a[1], suivi=sa)) == repr(RS.mesurer(b[0], b[1], suivi=sb))
        return pareil, ecarts
    suite, ecarts = jumeaux(False)
    separes, ecarts_sab = jumeaux(True)
    vu2 = not separes
    ok = meme and vu1 and suite and vu2
    return ok, (f"meme monde avant et apres mesure : {'identique' if meme else 'CHANGE'} ( controle : un milliardieme "
                f"de drachme {'vu' if vu1 else 'NON VU'} ) ; jumeaux mesure / jamais mesure, 3 jours : "
                f"{'identiques' if suite else f'DIFFERENTS {ecarts[:6]}'} ( controle : un milliardieme de drachme "
                f"{'vu, ' + str(len(ecarts_sab)) + ' empreintes changees' if vu2 else 'NON VU'} )")


def test_cout():
    w, p, s = reference()
    refs = RS.charger()
    t = []
    for _ in range(3):
        t0 = time.perf_counter(); RS.mesurer(w, p, suivi=s, refs=refs); t.append(time.perf_counter() - t0)
    return min(t) < 1.0, f"{w.table.n} habitants : mesure en {1000 * min(t):.0f} ms ( meilleure de 3 ; pire {1000 * max(t):.0f} ms ) ; seuil 1 000 ms"


def test_non_mesurable():
    x = monde_suivi(echelle=1.0, graine=3, domaines=["population"], chauffe=1, jours=1)
    L = _par_id(RS.mesurer(x[0], x[1], suivi=x[2]))
    lits = L["lits_hopital"]
    ok1 = lits["verdict"] == RS.NON_MESURABLE and "hopitaux" in lits["detail"] and lits["simule"] is None
    ok2 = L["part_0_14"]["verdict"] != RS.NON_MESURABLE and L["rapport_masculinite"]["verdict"] != RS.NON_MESURABLE
    y = monde_suivi(echelle=1.0, graine=3, domaines=[], chauffe=0, jours=1)
    M = _par_id(RS.mesurer(y[0], y[1], suivi=y[2]))
    ok3 = M["rapport_masculinite"]["verdict"] == RS.NON_MESURABLE and M["part_65_plus"]["verdict"] != RS.NON_MESURABLE
    nm1 = sum(1 for l in L.values() if l["verdict"] == RS.NON_MESURABLE)
    nm2 = sum(1 for l in M.values() if l["verdict"] == RS.NON_MESURABLE)
    return ok1 and ok2 and ok3, (f"population seule : {nm1} non mesurables, lits « {lits['detail']} » ; sans domaine : "
                                 f"{nm2} non mesurables, age mesure par le moteur ( 65+ = "
                                 f"{RS._fmt(M['part_65_plus']['simule'])} % ), sexe « "
                                 f"{M['rapport_masculinite']['detail']} »")


TESTS = [test_references, test_controle_positif_synthetique, test_controle_positif_monde, test_falsificateur_lits,
         test_falsificateur_morts, test_emigre_n_est_pas_mort, test_determinisme, test_lecture_seule, test_cout, test_non_mesurable]


def main(noms):
    tests = [t for t in TESTS if not noms or t.__name__ in noms or t.__name__[5:] in noms]
    passees = 0
    for t in tests:
        t0 = time.perf_counter()
        try: r, msg = t()
        except Exception as e:
            import traceback; traceback.print_exc()
            r, msg = False, f"EXCEPTION {type(e).__name__} : {e}"
        passees += bool(r)
        print(f"{'PASSE' if r else 'ECHOUE':7s} {t.__name__:36s} ({time.perf_counter() - t0:5.1f} s) {msg}", flush=True)
    print(f"{passees} / {len(tests)} portes de l instrument")
    return passees == len(tests)


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
