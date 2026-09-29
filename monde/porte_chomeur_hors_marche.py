"""PORTE DU CHOMEUR HORS MARCHE ET DE L ORDRE NEUTRE ( d04, 29/09, Classes diag 204 et chef de projet ; criteres ecrits
AVANT la mesure ; graines NEUVES 121, 122, 123, puis 151, 152, 153 pour le rejugement de HMT-148 ). Deux defauts du marche du travail du matin : le chomeur elu, patron ou
marchand ( HORS_MARCHE ) etait ecarte par son metier ; les candidats d un lieu etaient servis par numero d habitant ( une
file fixe ). Le monde : Stratis x 20 ( tests_d28_tourisme._ile, ou Classes l a vu ), une annee, quatre bras par graine,
chacun dans son propre arbre de code : la REGLE ( ce depot : patch_chomeur_hors_marche et patch_ordre_neutre ), SANS
HORS MARCHE ( le tronc 6b054bd et patch_ordre_neutre ), SANS ORDRE ( le tronc et patch_chomeur_hors_marche ) et le
TRONC ( information ).
Mesure. Chaque jour, les offres du matin ( d04.offres_jour ) aux CHOMEURS, relues au statut de la veille au soir ;
seulement les offres d un metier sans titre exige ( EXIGE, ou un titre donne a l embauche ), pour que tout chomeur puisse
les recevoir. Par lieu de domicile L et par jour : c_L chomeurs en age de travailler et domicilies, o_L offres a des
chomeurs de L ( au plus une par candidat et par jour ). Sous un ordre neutre, un chomeur de L en recoit une avec la
probabilite o_L / c_L ; attendu sans aucune offre : le produit des ( 1 - o_L / c_L ) de ses jours de chomage.
M1 aucun chomeur sans offre la ou des postes de son lieu se sont ouverts. Dans la regle : ( a ) parmi les chomeurs
   exposes ( au moins un jour de chomage ou des offres ont ete faites a des chomeurs de son lieu ), ceux qui ont recu au
   moins une offre sont au moins 0,8 x l attendu - 10 ( attendu : la somme des 1 - produit des ( 1 - o_L / c_L ) ) ;
   ( b ) la moitie HAUTE des numeros ( chaque jour, les chomeurs de chaque lieu ranges par numero ) recoit de 0,8 a 1,25
   fois l attendu de ses offres ( somme des o_L x h_L / c_L ), si l attendu vaut au moins 20. Controle positif : SANS
   ORDRE, la moitie haute recoit moins de 0,2 fois l attendu ( les grands numeros n en ont aucune ).
   ( Une premiere forme, « le nombre sans offre sous 1,25 x l attendu, et au-dessus de 2 x sans ordre », a ete ecartee
   avant la mesure sur une fumee de 10 jours, graine 5 : ~ 1 poste par jour pour ~ 1 000 chomeurs, l attendu sans offre
   vaut ~ 900, et aucun ordre ne peut en faire le double. )
M2 la part des marchands ( HMT-148, rejugement ) : dans la regle, les offres faites aux chomeurs marchands O, sommees sur
   les 3 graines, et leur attendu E ( somme des o_L x m_L / c_L, m_L les chomeurs marchands de L ) : | O - E | au plus
   2 x racine( E ) ( 2 ecarts-types de Poisson ), avec E au moins 50 ( sinon manque de puissance, REFUSEE comme telle ).
   Controle positif : SANS HORS MARCHE, 0 offre aux chomeurs marchands pour un attendu d au moins 20 par graine.
   ( Premier jugement, graines 121 a 123, REFUSEE et garde : M2 par graine de 0,8 a 1,25 fois l attendu, 0,66 a la graine
   121 pour 28,6 attendues ; une bande de +- 20 % y vaut ~ 1 ecart-type, le critere etait sous-dimensionne. )
M3 la conservation tient dans les quatre bras.
Information ( pas un critere ) : le chomage moyen des 20-64 ans de l annee ( statuts du domaine 4 ), regle contre tronc,
et aux jours 0, 3, 30, 90, 180, 365 ; les chomeurs marchands du jour 3 ; les embauches des marchands par metier.
   python -m monde.porte_chomeur_hors_marche [ graines ]"""
import sys, os, json, time, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor
GRAINES = (151, 152, 153)          # HMT-148 ( le premier jugement : 121, 122, 123 )
JOURS = 365
POINTS = (0, 3, 30, 90, 180, 365)
TRONC = "6b054bd"
BRAS = {"regle": None, "sans_hors_marche": ("patch_ordre_neutre.py",), "sans_ordre": ("patch_chomeur_hors_marche.py",),
        "tronc": ()}
PY = sys.executable


def _jouer(graine):
    """Un bras ( le code est celui du PYTHONPATH ). Rend le dictionnaire des mesures."""
    import math, collections
    import numpy as np
    from monde import config as C, population as PO
    from monde.pays import tests_d28_tourisme as T, d04_travail as TR, d01_population as POP
    t0 = time.time()
    w, p = T._ile(graine=graine)
    tb = w.table; col = p.colonnes["habitant"]; d = p.domaine("travail"); nl = len(w.carte.par_n)
    MARCHAND = PO.CODE_ROLE["marchand"]
    libre = {r for r in PO.CODE_ROLE if TR.EXIGE.get(r) is None or TR.EXIGE.get(r) in TR.FORMEES_A_L_EMBAUCHE}
    cap = tb.n + 100000
    lp = np.zeros(cap); expose = np.zeros(cap, bool); offert = np.zeros(cap, bool)
    cho_v = np.zeros(cap, bool); lieu_v = np.full(cap, -1, np.int64); mar_v = np.zeros(cap, bool); haut_v = np.zeros(cap, bool)
    serie, taux = {}, []; om = 0; em = 0.0; oh = 0; eh = 0.0; o_tot = 0; emb_m = collections.Counter(); marchands_j3 = None
    om_lieu = np.zeros(nl); em_lieu = np.zeros(nl); roles_m = collections.Counter()          # le detail, pour la sonde

    def mesurer():
        n = tb.n; v = tb.vivant[:n] == 1
        age = (p.jour - col["naissance_j"][:n]) / POP.JOURS_AN
        st = col["tr_statut"][:n]; cho = st == TR.CHOMEUR; emp = np.isin(st, TR.EN_EMPLOI)
        m = v & (age >= 20) & (age < 65)
        t = float(cho[m].sum() / max(1, cho[m].sum() + emp[m].sum()))
        ids = np.nonzero(v & cho & (age >= C.AGE_TRAVAIL) & (age < TR.AGE_LEGAL) & (tb.domicile[:n] >= 0))[0]
        return t, ids[ids < cap]

    def veille(ids):
        cho_v[:] = False; mar_v[:] = False; haut_v[:] = False; lieu_v[:] = -1
        cho_v[ids] = True; lieu_v[ids] = tb.domicile[ids]; mar_v[ids[tb.role[ids] == MARCHAND]] = True
        if len(ids):                                            # la moitie haute des numeros de chaque lieu
            o = np.argsort(lieu_v[ids], kind="stable"); l = lieu_v[ids][o]
            debut = np.r_[0, np.nonzero(np.diff(l))[0] + 1]; taille = np.diff(np.r_[debut, len(l)])
            pos = np.arange(len(l)) - np.repeat(debut, taille)
            haut_v[ids[o][pos >= np.repeat(taille, taille) / 2.0]] = True

    t, ids = mesurer(); serie[0] = round(t, 4); veille(ids); ids_v = ids
    j0 = int(w.jour); vu = j0
    while int(w.jour) < j0 + JOURS:
        w.pas_suivant()
        if int(w.jour) == vu: continue
        vu = int(w.jour); fini = vu - j0
        o_l = np.zeros(nl); om_l = 0
        for (i, k, a) in list(getattr(d, "offres_jour", ()) or ()):         # les offres du matin, au statut de la veille
            if i >= cap or not cho_v[i] or k[1] not in libre: continue
            o_l[lieu_v[i]] += 1; offert[i] = True; o_tot += 1
            if haut_v[i]: oh += 1
            if mar_v[i]:
                om += 1; om_lieu[lieu_v[i]] += 1; roles_m[k[1]] += 1
                if a == 1: emb_m[k[1]] += 1
        if len(ids_v):
            c_l = np.bincount(lieu_v[ids_v], minlength=nl).astype(float)
            m_l = np.bincount(lieu_v[ids_v[mar_v[ids_v]]], minlength=nl).astype(float)
            q = np.divide(o_l, c_l, out=np.zeros(nl), where=c_l > 0)
            e_l = o_l * np.divide(m_l, c_l, out=np.zeros(nl), where=c_l > 0); em += float(e_l.sum()); em_lieu += e_l
            h_l = np.bincount(lieu_v[ids_v[haut_v[ids_v]]], minlength=nl).astype(float)
            eh += float((o_l * np.divide(h_l, c_l, out=np.zeros(nl), where=c_l > 0)).sum())
            qi = q[lieu_v[ids_v]]; ex = qi > 0
            with np.errstate(divide="ignore"): lp[ids_v[ex]] += np.log(np.clip(1.0 - qi[ex], 0.0, 1.0))
            expose[ids_v[ex]] = True
        t, ids = mesurer(); taux.append(t); veille(ids); ids_v = ids
        if fini in POINTS: serie[fini] = round(t, 4)
        if fini == 3: marchands_j3 = int(mar_v.sum())
    return {"graine": graine, "serie": serie, "chomage_moyen": round(float(np.mean(taux)), 5),
            "exposes": int(expose.sum()), "offerts": int((expose & offert).sum()),
            "offerts_attendu": round(float((1.0 - np.exp(lp[expose])).sum()), 1), "offres_haut": oh, "offres_haut_attendu": round(eh, 1),
            "offres_chomeurs": o_tot, "offres_marchands": om, "offres_marchands_attendu": round(em, 1),
            "marchands_j3": marchands_j3, "embauches_marchands": dict(emb_m), "roles_offerts_marchands": dict(roles_m),
            "marchands_par_lieu": {w.carte.par_n[k].id: (int(om_lieu[k]), round(float(em_lieu[k]), 1)) for k in range(nl) if em_lieu[k] >= 1.0 or om_lieu[k] > 0},
            "conservation": bool(p.socle.conservation.tenue()[0]), "secondes": round(time.time() - t0)}


def _arbre(depot, nom, patchs):
    """L arbre de code d un bras : le depot ( la regle ), ou le tronc extrait et ses correctifs du depot."""
    if patchs is None: return depot
    t = os.path.join(tempfile.gettempdir(), f"porte_chomeur_{TRONC}_{nom}")
    if not os.path.isdir(os.path.join(t, "monde")):
        os.makedirs(t, exist_ok=True)
        a = subprocess.run(["git", "-C", depot, "archive", TRONC, "monde", "guerre"], check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", t], input=a, check=True)
        for x in patchs: subprocess.run([PY, os.path.join(depot, "references", "correctifs", x), t], check=True, capture_output=True)
    return t


def _bras(args):
    graine, nom, arbre, script = args
    env = dict(os.environ, PYTHONPATH=arbre, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    r = subprocess.run([PY, script, "--jouer", str(graine)], env=env, capture_output=True, text=True, cwd=arbre)
    lignes = [l for l in r.stdout.splitlines() if l.startswith("{")]
    if r.returncode or not lignes: raise RuntimeError(f"bras {graine} {nom} : {r.stderr[-2000:]}")
    x = json.loads(lignes[-1]); x["bras"] = nom
    return x


def main():
    graines = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else list(GRAINES)
    t0 = time.time(); ok = {}
    depot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(tempfile.mkdtemp(prefix="porte_chomeur_"), "porte_chomeur_hors_marche.py")
    with open(os.path.abspath(__file__)) as f, open(script, "w") as g: g.write(f.read())      # le meme script partout
    arbres = {nom: _arbre(depot, nom, patchs) for nom, patchs in BRAS.items()}
    with ThreadPoolExecutor(2) as ex: rs = list(ex.map(_bras, [(g, nom, arbres[nom], script) for g in graines for nom in BRAS]))
    for r in rs: print("  ", r, flush=True)
    for g in graines:
        X = {r["bras"]: r for r in rs if r["graine"] == g}; R, SH, SO, TT = X["regle"], X["sans_hors_marche"], X["sans_ordre"], X["tronc"]
        ok[f"M1a graine {g} : regle, {R['offerts']} chomeurs exposes ont recu une offre sur {R['exposes']} ( attendu {R['offerts_attendu']}, au moins 0,8 x - 10 )"] = (
            R["offerts"] >= 0.8 * R["offerts_attendu"] - 10)
        for nom, B in (("regle", R), ("sans ordre", SO)):
            if B["offres_haut_attendu"] < 20:
                print(f"   M1b graine {g} {nom} : sans objet, {B['offres_haut_attendu']} offres attendues a la moitie haute", flush=True); continue
            x = B["offres_haut"] / B["offres_haut_attendu"]
            if B is R:
                ok[f"M1b graine {g} : regle, la moitie haute des numeros {B['offres_haut']} offres pour {B['offres_haut_attendu']} attendues ( {x:.2f} ; 0,8 a 1,25 )"] = 0.8 <= x <= 1.25
            else:
                ok[f"M1b graine {g} : controle positif, sans ordre, la moitie haute {B['offres_haut']} offres pour {B['offres_haut_attendu']} attendues ( {x:.2f} ; moins de 0,2 )"] = x < 0.2
        ok[f"M2 graine {g} : controle positif, sans hors marche {SH['offres_marchands']} offres aux marchands pour {SH['offres_marchands_attendu']} attendues ( 0, attendu au moins 20 )"] = (
            SH["offres_marchands"] == 0 and SH["offres_marchands_attendu"] >= 20)
        ok[f"M3 graine {g} : conservation dans les quatre bras"] = all(X[b]["conservation"] for b in BRAS)
        print(f"   information graine {g} : chomage moyen des 20-64 ans regle {R['chomage_moyen']:.2%}, tronc {TT['chomage_moyen']:.2%}, sans hors marche {SH['chomage_moyen']:.2%}, "
              f"sans ordre {SO['chomage_moyen']:.2%} ; serie regle {R['serie']} tronc {TT['serie']} ; marchands chomeurs au jour 3 {R['marchands_j3']} ; "
              f"leurs embauches {R['embauches_marchands']}", flush=True)
    Rs = [r for r in rs if r["bras"] == "regle"]
    O = sum(r["offres_marchands"] for r in Rs); Em = sum(r["offres_marchands_attendu"] for r in Rs)
    ok[f"M2 somme des graines : regle, {O} offres aux chomeurs marchands pour {Em:.1f} attendues ( | O - E | au plus 2 x racine( E ) = {2 * Em ** 0.5:.1f} ; E au moins 50 )"] = (
        Em >= 50 and abs(O - Em) <= 2 * Em ** 0.5)
    for r in Rs: print(f"   information graine {r['graine']} : marchands par lieu ( offerts, attendus ) {r['marchands_par_lieu']} ; metiers offerts {r['roles_offerts_marchands']}", flush=True)
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DU CHOMEUR HORS MARCHE ET DE L ORDRE NEUTRE : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--jouer":
        print(json.dumps(_jouer(int(sys.argv[2]))), flush=True); sys.exit(0)
    sys.exit(main())
