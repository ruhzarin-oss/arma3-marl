"""PORTE DE LA FAMINE DE L ARMEE ( HMT-147, 29/09, chef de projet ; criteres ecrits AVANT la mesure, dans Plane puis ici ;
graines NEUVES 141, 142, 143 ). Le monde E1 d Altis x 20 ( 28 domaines ; le monde nait le 15 juin ), une annee, deux bras
par graine, chacun dans son propre arbre de code : la REGLE ( ce depot : la pension militaire au plan de departs,
l ordinaire de caserne des appeles ) et le TEMOIN ( c460323, la 1re partie de la branche, identique au tronc dans le E1 ).
Une mort de faim : cause_deces = faim ( domaine 1 ). Militaire : appele ou de carriere la veille de sa mort, parti au
plan de departs, ou de metier soldat ou officier.
F1 les morts de faim militaires, sommees sur les 3 graines, valent au plus le tiers de celles du temoin ; sans hausse
   ailleurs : les autres morts de faim de la regle restent sous 1,2 x celles du temoin + 3.
F2 aucun appele ne meurt de faim dans la regle ; controle positif : le temoin en a au moins un sur les 3 graines ( sinon
   la porte manque de puissance, REFUSEE comme telle ).
F3 parmi les partants du plan de departs qui remplissent ( b ) 60 ans et 25 ans de service ou ( c ) 40 ans de service,
   au moins 95 % ont une pension dans la regle ; controle positif : 0 % dans le temoin ( avec au moins un tel partant ).
G  la garde budgetaire : la conservation tient dans les deux bras ; aucune pension due et impayee a la fin de l annee
   dans la regle ( creances de prestations sur la caisse de securite sociale ).
Information ( pas un critere ) : les morts de faim d hiver ( jours 170 a 290 ) par categorie ; le cout de l ordinaire ;
les pensionnes ; la caisse et la dette de l Etat, regle contre temoin.
   python -m monde.porte_famine_armee [ graines ]"""
import sys, os, json, time, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
GRAINES = (141, 142, 143)
JOURS = 365
HIVER = (170, 290)
TEMOIN = "c460323"
PY = sys.executable


def _jouer(graine):
    """Un bras ( le code est celui du PYTHONPATH ). Rend le dictionnaire des mesures."""
    import numpy as np, collections
    from monde import population as PO
    from monde.pays import pays as P, essais as E, d25_armee as A, d04_travail as TR, d01_population as D1, d06_etat as ET
    t0 = time.time()
    partants = {}                                              # habitant -> ( jour, droit ( b ) ou ( c ), pension )

    def droit(p, i):
        col = p.colonnes["habitant"]; ans = float(col["tr_jours_cotises"][i]) / TR.JOURS_ASSURANCE_AN
        age = (p.jour - int(col["naissance_j"][i])) / D1.JOURS_AN
        return (ans >= 25.0 and age >= 60.0) or ans >= 40.0
    rompre0, retraite0 = TR.rompre_contrat, TR.prendre_retraite

    def rompre(p, h, motif="economique", involontaire=True):
        if motif == "reduction_effectifs": partants[h.id] = (p.jour, droit(p, h.id), False)
        return rompre0(p, h, motif, involontaire)

    def retraite(p, h, *a, **k):
        if a[:1] == (False,) or k.get("penalite") is False: partants[h.id] = (p.jour, droit(p, h.id), None)
        pn = retraite0(p, h, *a, **k)
        if h.id in partants and partants[h.id][2] is None: partants[h.id] = (partants[h.id][0], partants[h.id][1], pn is not None)
        return pn
    TR.rompre_contrat, TR.prendre_retraite = rompre, retraite
    w, _ = E.monde([nom for nom, mod, _ in P.DOMAINES], graine=graine, echelle=20.0); p = w.pays
    tb = w.table; col = p.colonnes["habitant"]; d = A._dom(p); T = p.domaine("travail")
    FAIM = D1.CAUSES.index("faim"); MIL = (PO.CODE_ROLE["soldat"], PO.CODE_ROLE["officier"])
    vus = set(); morts = collections.Counter(); hiver = collections.Counter()
    caisse0, dette0 = float(w.gouv.caisse), float(ET.dette_brute(p))

    def effectifs():
        rows = A._lignes(d); E_ = d.eff
        return set(E_["hid"][rows[E_["conscrit"][rows] == 1]].tolist()), set(E_["hid"][rows[E_["conscrit"][rows] == 0]].tolist())
    cons, car = effectifs()
    j0 = int(w.jour); vu = j0
    while int(w.jour) < j0 + JOURS:
        w.pas_suivant()
        if int(w.jour) == vu: continue
        vu = int(w.jour); fini = vu - j0; n = tb.n
        mf = np.nonzero((col["cause_deces"][:n] == FAIM) & (col["deces_j"][:n] >= 0))[0]
        for i in mf.tolist():
            if i in vus: continue
            vus.add(i)
            cat = ("appele" if i in cons else "carriere" if i in car else "ancien" if i in partants
                   else "militaire" if int(tb.role[i]) in MIL else "autre")
            morts[cat] += 1
            if HIVER[0] <= fini <= HIVER[1]: hiver[cat] += 1
        cons, car = effectifs()
    K = p.socle.creances
    arr = float(sum(cr.montant for cr in K.de(T.caisse)))
    ayants = [v for v in partants.values() if v[1]]
    return {"graine": graine, "morts": dict(morts), "hiver": dict(hiver),
            "militaires": sum(morts[c] for c in ("appele", "carriere", "ancien", "militaire")), "autres": morts["autre"],
            "appeles": morts["appele"], "partants": len(partants), "ayants_droit": len(ayants),
            "ayants_droit_pensionnes": sum(1 for v in ayants if v[2]), "pensionnes": int(getattr(d, "pensionnes", 0) or 0),
            "ordinaire": round(float(d.depenses.get("ordinaire", 0.0)), 2), "arrieres_caisse": round(arr, 2),
            "caisse_etat": round(float(w.gouv.caisse) - caisse0, 2), "dette_etat": round(float(ET.dette_brute(p)) - dette0, 2),
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def _arbre(depot, regle):
    if regle: return depot
    t = os.path.join(tempfile.gettempdir(), f"porte_famine_armee_{TEMOIN}")
    if not os.path.isdir(os.path.join(t, "monde")):
        os.makedirs(t, exist_ok=True)
        a = subprocess.run(["git", "-C", depot, "archive", TEMOIN, "monde", "guerre"], check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", t], input=a, check=True)
    return t


def _bras(args):
    graine, regle, arbre, script = args
    env = dict(os.environ, PYTHONPATH=arbre, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    r = subprocess.run([PY, script, "--jouer", str(graine)], env=env, capture_output=True, text=True, cwd=arbre)
    lignes = [l for l in r.stdout.splitlines() if l.startswith("{")]
    if r.returncode or not lignes: raise RuntimeError(f"bras {graine} {'regle' if regle else 'temoin'} : {r.stderr[-2000:]}")
    x = json.loads(lignes[-1]); x["regle"] = regle
    return x


def main():
    graines = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else list(GRAINES)
    t0 = time.time(); ok = {}
    depot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(tempfile.mkdtemp(prefix="porte_famine_armee_"), "porte_famine_armee.py")
    with open(os.path.abspath(__file__)) as f, open(script, "w") as g: g.write(f.read())
    arbres = {r: _arbre(depot, r) for r in (True, False)}
    with ThreadPoolExecutor(2) as ex: rs = list(ex.map(_bras, [(g, r, arbres[r], script) for g in graines for r in (True, False)]))
    for r in rs: print("  ", r, flush=True)
    R = [r for r in rs if r["regle"]]; T = [r for r in rs if not r["regle"]]
    s = lambda X, k: sum(x[k] for x in X)
    ok[f"F1 morts de faim militaires : regle {s(R, 'militaires')}, temoin {s(T, 'militaires')} ( au plus le tiers )"] = s(R, "militaires") <= s(T, "militaires") / 3.0
    ok[f"F1 sans hausse ailleurs : autres morts de faim, regle {s(R, 'autres')}, temoin {s(T, 'autres')} ( au plus 1,2 x + 3 )"] = s(R, "autres") <= 1.2 * s(T, "autres") + 3
    ok[f"F2 appeles morts de faim : regle {s(R, 'appeles')} ( 0 ) ; controle positif, temoin {s(T, 'appeles')} ( au moins 1 )"] = s(R, "appeles") == 0 and s(T, "appeles") >= 1
    ar, ap = s(R, "ayants_droit"), s(R, "ayants_droit_pensionnes"); at, atp = s(T, "ayants_droit"), s(T, "ayants_droit_pensionnes")
    ok[f"F3 partants ayants droit pensionnes : regle {ap} sur {ar} ( au moins 95 % ) ; controle positif, temoin {atp} sur {at} ( 0 % )"] = (
        ar > 0 and ap >= 0.95 * ar and at > 0 and atp == 0)
    ok[f"G conservation dans les deux bras ; arrieres de prestations en fin d annee, regle {[x['arrieres_caisse'] for x in R]} ( 0 )"] = (
        all(x["conservation"] for x in rs) and all(x["arrieres_caisse"] <= 0.01 for x in R))
    for g in graines:
        a = next(x for x in R if x["graine"] == g); b = next(x for x in T if x["graine"] == g)
        print(f"   information graine {g} : morts de faim regle {a['morts']} ( hiver {a['hiver']} ), temoin {b['morts']} ( hiver {b['hiver']} ) ; "
              f"pensionnes {a['pensionnes']}, ordinaire {a['ordinaire']} ; caisse de l Etat regle {a['caisse_etat']} temoin {b['caisse_etat']} ; "
              f"dette regle {a['dette_etat']} temoin {b['dette_etat']}", flush=True)
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DE LA FAMINE DE L ARMEE : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--jouer":
        print(json.dumps(_jouer(int(sys.argv[2]))), flush=True); sys.exit(0)
    sys.exit(main())
