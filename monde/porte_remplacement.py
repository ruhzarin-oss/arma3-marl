"""PORTE DU REMPLACEMENT ( HMT-161, 30/09, Classes et chef de projet ; criteres ecrits AVANT la mesure, dans Plane puis
ici ; graines NEUVES 171, 172, 173 ). Le monde de Classes ( diag6.py : W.Monde( graine, echelle 20, fret d15 ), puis
P.installer( w, None ) ), une annee, deux bras par graine, chacun dans son propre arbre de code : la REGLE ( ce depot :
patch_remplacement ) et le TEMOIN ( le tronc bce9f31 ). Un espion sur d04.embaucher_contrat releve chaque depart d un
salarie EN DISPONIBILITE vers un autre emploi : son poste ( lieu, metier ), le besoin de l employeur ( _besoin ), la
cible avant et apres, puis l effectif du poste les 30 jours qui suivent.
R1 le poste garde : parmi ces departs dont l employeur a encore besoin, aucune baisse de la cible dans la regle ; controle
   positif : dans le temoin, la cible baisse pour au moins 90 % d entre eux.
R2 le poste pourvu : dans la regle, au moins 50 % de ces postes gardes retrouvent leur effectif d avant le depart dans les
   30 jours ; au moins 20 tels departs sur les 3 graines ( sinon manque de puissance, REFUSEE comme telle ).
R3 les chauffeurs : les convoyeurs salaries au travail au jour 40, sommes sur les graines, font au moins 0,9 x ceux du
   jour 1 dans la regle ; controle positif : moins de 0,85 x dans le temoin.
R4 sans hausse ailleurs : le chomage moyen des 20-64 ans ( statuts du domaine 4 ) de la regle ne depasse pas celui du
   temoin de plus de 0,25 point, graine par graine ; la moyenne annuelle des salaries en disponibilite de la regle reste
   sous 1,25 x celle du temoin + 10 ; la conservation tient dans les deux bras.
Information ( pas un critere ) : les departs par metier, les convoyeurs au jour 365.
   python -m monde.porte_remplacement [ graines ]"""
import sys, os, json, time, subprocess, tempfile, inspect
from concurrent.futures import ThreadPoolExecutor
GRAINES = (171, 172, 173)
JOURS = 365
SUIVI_J = 30
TEMOIN = "bce9f31"
PY = sys.executable


def _jouer(graine):
    """Un bras ( le code est celui du PYTHONPATH ). Rend le dictionnaire des mesures."""
    import numpy as np, collections
    from monde import monde as W, population as PO
    from monde.pays import pays as P, d04_travail as TR, d01_population as D1
    t0 = time.time()
    departs = []                                   # [ jour, cle, besoin, cible avant, cible apres, effectif avant, pourvu ]
    emb0 = TR.embaucher_contrat

    def emb(p, h, *a, **k):
        d = p.domaine("travail"); col = p.colonnes["habitant"]
        x = None
        if h.travail is not None and "tr_dispo_j" in col and col["tr_dispo_j"][h.id] >= 0:
            cle = (h.travail.id, h.role)
            x = [p.jour, cle, bool(TR._besoin(p, d, *cle)), d.cible.get(cle, 0), None, TR._effectifs(p).get(cle, 0), False]
        r = emb0(p, h, *a, **k)
        if x is not None: x[4] = d.cible.get(x[1], 0); departs.append(x)
        return r
    TR.embaucher_contrat = emb
    kw = {"fret": "d15"} if "fret" in inspect.signature(W.Monde.__init__).parameters else {}
    w = W.Monde(graine=graine, echelle=20.0, **kw); p = P.installer(w, None)
    tb = w.table; col = p.colonnes["habitant"]; CV = PO.CODE_ROLE["convoyeur"]

    def convoyeurs():
        n = tb.n
        return int(((tb.role[:n] == CV) & (tb.vivant[:n] == 1) & (tb.travail[:n] >= 0) & (col["tr_statut"][:n] == TR.SALARIE)).sum())

    def chomage():
        n = tb.n; v = tb.vivant[:n] == 1
        age = (p.jour - col["naissance_j"][:n]) / D1.JOURS_AN
        st = col["tr_statut"][:n]; cho = st == TR.CHOMEUR; emp = np.isin(st, TR.EN_EMPLOI); m = v & (age >= 20) & (age < 65)
        dispo = int((v & (col["tr_dispo_j"][:n] >= 0)).sum()) if "tr_dispo_j" in col else 0
        return float(cho[m].sum() / max(1, cho[m].sum() + emp[m].sum())), dispo
    conv = {}; taux, dispos = [], []
    j0 = int(w.jour); vu = j0
    while int(w.jour) < j0 + JOURS:
        w.pas_suivant()
        if int(w.jour) == vu: continue
        vu = int(w.jour); fini = vu - j0
        if fini in (1, 40, JOURS): conv[fini] = convoyeurs()
        t, dp = chomage(); taux.append(t); dispos.append(dp)
        ouverts = [x for x in departs if not x[6] and p.jour - x[0] <= SUIVI_J]
        if ouverts:
            eff = TR._effectifs(p)
            for x in ouverts:
                if eff.get(x[1], 0) >= x[5]: x[6] = True
    B = [x for x in departs if x[2]]
    return {"graine": graine, "departs": len(departs), "departs_besoin": len(B),
            "cible_baissee": sum(1 for x in B if x[4] < x[3]), "gardes": sum(1 for x in B if x[4] >= x[3]),
            "gardes_pourvus": sum(1 for x in B if x[4] >= x[3] and x[6]),
            "par_metier": dict(collections.Counter(x[1][1] for x in departs)), "convoyeurs": conv,
            "chomage_moyen": round(float(np.mean(taux)), 5), "dispo_moyen": round(float(np.mean(dispos)), 1),
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def _arbre(depot, regle):
    if regle: return depot
    t = os.path.join(tempfile.gettempdir(), f"porte_remplacement_{TEMOIN}")
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
    script = os.path.join(tempfile.mkdtemp(prefix="porte_remplacement_"), "porte_remplacement.py")
    with open(os.path.abspath(__file__)) as f, open(script, "w") as g: g.write(f.read())
    arbres = {r: _arbre(depot, r) for r in (True, False)}
    with ThreadPoolExecutor(2) as ex: rs = list(ex.map(_bras, [(g, r, arbres[r], script) for g in graines for r in (True, False)]))
    for r in rs: print("  ", r, flush=True)
    R = [r for r in rs if r["regle"]]; T = [r for r in rs if not r["regle"]]
    s = lambda X, k: sum(x[k] for x in X)
    ok[f"R1 regle : {s(R, 'cible_baissee')} cibles baissees sur {s(R, 'departs_besoin')} departs en disponibilite dont l employeur a besoin ( 0 )"] = s(R, "cible_baissee") == 0
    ok[f"R1 controle positif, temoin : {s(T, 'cible_baissee')} cibles baissees sur {s(T, 'departs_besoin')} ( au moins 90 % )"] = (
        s(T, "departs_besoin") > 0 and s(T, "cible_baissee") >= 0.9 * s(T, "departs_besoin"))
    ok[f"R2 regle : {s(R, 'gardes_pourvus')} postes gardes pourvus en 30 jours sur {s(R, 'gardes')} ( au moins 50 %, au moins 20 departs )"] = (
        s(R, "gardes") >= 20 and s(R, "gardes_pourvus") >= 0.5 * s(R, "gardes"))
    c1r = sum(x["convoyeurs"].get("1", 0) for x in R); c40r = sum(x["convoyeurs"].get("40", 0) for x in R)
    c1t = sum(x["convoyeurs"].get("1", 0) for x in T); c40t = sum(x["convoyeurs"].get("40", 0) for x in T)
    ok[f"R3 regle : convoyeurs {c1r} au jour 1, {c40r} au jour 40 ( au moins 0,9 x )"] = c1r > 0 and c40r >= 0.9 * c1r
    ok[f"R3 controle positif, temoin : {c1t} au jour 1, {c40t} au jour 40 ( moins de 0,85 x )"] = c1t > 0 and c40t < 0.85 * c1t
    for g in graines:
        a = next(x for x in R if x["graine"] == g); b = next(x for x in T if x["graine"] == g)
        ok[f"R4 graine {g} : chomage moyen des 20-64 ans regle {a['chomage_moyen']:.2%}, temoin {b['chomage_moyen']:.2%} ( au plus + 0,25 point ) ; "
           f"disponibilites {a['dispo_moyen']} contre {b['dispo_moyen']} ( au plus 1,25 x + 10 ) ; conservation"] = (
            a["chomage_moyen"] <= b["chomage_moyen"] + 0.0025 and a["dispo_moyen"] <= 1.25 * b["dispo_moyen"] + 10
            and a["conservation"] and b["conservation"])
        print(f"   information graine {g} : departs par metier regle {a['par_metier']} temoin {b['par_metier']} ; convoyeurs regle {a['convoyeurs']} temoin {b['convoyeurs']}", flush=True)
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DU REMPLACEMENT : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--jouer":
        print(json.dumps(_jouer(int(sys.argv[2]))), flush=True); sys.exit(0)
    sys.exit(main())
