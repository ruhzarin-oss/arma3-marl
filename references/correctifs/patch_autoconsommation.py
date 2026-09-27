"""27/09 : l autoconsommation paysanne ( domaine 9 ) : a 19 h 40, le menage d un paysan dont le garde-manger ne tient pas
le repas du soir le prend au grenier de sa ferme. Le meme texte que le depot ( guerre-des-iles ), pose avant la decision
de vente, et sa routine posee a l installation. Idempotent.
   python patch_autoconsommation.py chemin/d09_agriculture.py"""
import sys
p = sys.argv[1]; s = open(p).read()
if "def _autoconsommation(p):" in s: print("deja :", p); sys.exit(0)
BLOC = '''# ================================================================== l autoconsommation ( 27/09, Younes : « au plus realiste » )
def _autoconsommation(p):
    """19 h 40, avant le repas de 20 h : le menage d un paysan dont le garde-manger ne tient pas le repas du soir le prend
    au grenier de sa ferme - le moulin, le pressoir et le four de la ferme, comme pour le marche. Les familles paysannes
    sont les dernieres a avoir faim ( autoconsommation : 10 a 20 % de la production des exploitations grecques ).
    ( 27/09 : sans elle, la Stratis affamee de l essai 15 mourait de faim a cote de 230 jours de vivres, ses paysans trop
    faibles pour travailler. ) Rien pour une ferme sous sequestre. Les sommes sont exactes ( math.fsum ) et l ordre est
    celui des numeros de menage : le meme texte tourne a l identique sur l ancien moteur ( correctif de reference
    patch_autoconsommation.py )."""
    w = p.w
    A = p.domaine("agriculture"); tb = w.table; n = tb.n; mt = tb.menages; M = mt.n
    st = getattr(tb, "statut", None)
    vivant = tb.vivant[:n] == 1
    if st is not None: vivant = vivant & (st[:n] != getattr(PO_MOTEUR, "ABSENT", 1))
    mm = PO_MOTEUR.menages_inscrits(tb, n)
    bouches = np.bincount(mm[vivant & (mm >= 0)], minlength=M)[:M].astype(np.float64) * C.NOURRITURE_PAR_JOUR
    code = PO_MOTEUR.CODE_ROLE["paysan"]
    for ex in A.liste:
        if ex.sequestre: continue
        ids = np.nonzero(vivant & (tb.travail[:n] == ex.lieu.n) & (tb.role[:n] == code))[0]
        if not len(ids): continue
        mids = np.unique(mm[ids]); mids = mids[mids >= 0]
        besoin = np.maximum(0.0, bouches[mids] - mt.garde_manger[mids])
        total = math.fsum(besoin.tolist())
        if total <= 1e-9: continue
        voulu = min(total, _livrable(A, ex))
        if voulu <= 1e-9: continue
        if _q(A, ex, "olives") > 0: _transformer(p, A, ex, RECETTES["presser"], _q(A, ex, "olives"))
        manque = voulu * PARTS_MAX[0] * KCAL_RATION / KCAL["farine"] - _q(A, ex, "farine")
        if manque > 0 and _q(A, ex, "cereales") > 0:
            _transformer(p, A, ex, RECETTES["moudre"], min(_q(A, ex, "cereales"), manque / RECETTES["moudre"].sorties["farine"]))
        faites, _ = _livrer_rations(p, A, ex, voulu)
        pris = min(faites, max(0.0, ex.ferme.stocks["nourriture"]))
        if pris <= 1e-9: continue
        ex.ferme.stocks["nourriture"] -= pris
        mt.garde_manger[mids] += besoin * (pris / total)
        p.compter("autoconsommation", pris)


def brancher_autoconsommation(p):
    """Pose l autoconsommation ( une fois ) : a l installation, ou sur une ile reprise d un instantane d avant."""
    J = p.socle.journal
    if "autoconsommation" not in getattr(J, "types", {}): J.declarer("autoconsommation", "agriculture", "compte")
    if not any(f is _autoconsommation for _, _, f in p.routines.get(19 * 60 + 40, ())):
        p.routine(19 + 40 / 60, 20, "agriculture", _autoconsommation)


'''
a = "# ================================================================== la decision : vendre ou stocker la recolte"
assert s.count(a) == 1, "decision de vente introuvable"
s = s.replace(a, BLOC + a)
b = '''    p.routine(20 + 10 / 60, 20, "agriculture", _soir)
'''
assert s.count(b) == 1, "routine du soir introuvable"
s = s.replace(b, b + "    brancher_autoconsommation(p)\n")
open(p, "w").write(s); print("corrige :", p)
