"""03/10 ( HMT-194, etape 3b d Arma a fond ) : LES MORTS QUI PESENT. Au deces, le domaine 4 effacait la pension du defunt
( d.pensions.pop ) : aucune pension de survivant n existait, ni civile ni militaire. Ce correctif ouvre, le matin ou le
domaine voit le deces, la pension de survivant de la loi 4387/2016 art. 12 ( caisse ) ou la pension de guerre du P.D.
168/2007 ( Etat ) de la famille, et la verse chaque jour avec les autres prestations. Sans deces qui ouvre un droit,
rien ne change. Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_pension_survivant.py racine_de_l_arbre"""
import os, sys
R = sys.argv[1]


def _nouveau(a, b):
    return next((l for l in b.splitlines() if l.strip() and l not in a.splitlines()), None)


def remplacer(chemin, paires):
    f = os.path.join(R, chemin)
    if not os.path.exists(f): print("absent :", f); return
    s = open(f).read(); n = 0
    for a, b in paires:
        m = _nouveau(a, b)
        if b in s or (m is not None and m in s): continue
        if s.count(a) != 1: raise SystemExit(f"{chemin} : {s.count(a)} fois {a!r}")
        s = s.replace(a, b); n += 1
    open(f, "w").write(s); print("corrige :" if n else "deja :", f)


CONSTANTES = '''                                                      # d allocation d invalidite non contributive ( a calibrer par degre )

# ================================================================== la pension de survivant ( 03/10, HMT-194 etape 3b )
# Loi 4387/2016, art. 12, modifie par l art. 19 de la loi 4611/2019 ( circulaire e-EFKA S50/22/905880/2019 ; ministere
# du Travail, « Primary pension », et e-EFKA, « Proypotheseis aponomis », 2025 ) : au deces d un pensionne, ou d un
# assure qui remplissait les conditions d une pension ( ici : celles de la pension d invalidite du domaine, 1 500 jours ),
# la base est la pension que le defunt touchait ou a laquelle il avait droit ( ici : sa pension d invalidite,
# calculer_pension ; le taux d invalidite d un deces est a verifier ). Le conjoint survivant, quel que soit son age ( la
# loi 4611/2019 a supprime les seuils de 52 et 55 ans ), touche 70 % ; apres trois ans, 50 % s il travaille ou touche
# une pension. Marie depuis trois ans au moins, sauf deces par accident, violence ou au combat ( CHOIX : toute cause de
# ce genre ; la loi dit l accident du travail et l homicide ), ou enfant commun. Chaque enfant non marie de moins de
# 24 ans : 25 % ( 50 % orphelin de pere et de mere ). Le total ne depasse jamais la base ( reduction au prorata ). La
# pension cesse au deces du beneficiaire, au remariage du conjoint, aux 24 ans ou au mariage de l enfant. Ni le conjoint
# divorce ( pension alimentaire ), ni les veuvages d avant l installation ne sont modelises. CHOIX : un couple du
# recensement ( union_j a 0 ) compte comme marie depuis plus de trois ans - le recensement ne date pas les mariages, et
# sans cela aucun veuf n aurait de pension pendant les trois premieres annees du monde.
TAUX_CONJOINT = 0.70
TAUX_CONJOINT_REDUIT = 0.50
TROIS_ANS_J = 3 * 365
TAUX_ENFANT = 0.25
TAUX_ORPHELIN = 0.50
AGE_ENFANT_SURVIVANT = 24.0
CAUSES_SANS_DUREE_MARIAGE = ("accident", "violence", "combat")
# Code des pensions de guerre ( P.D. 168/2007, Comptabilite generale de l Etat ) : la famille d un militaire TUE AU
# COMBAT touche de l Etat une pension de guerre, sans duree de service ni de mariage ( art. 17 par. 1 a ββ ) :
#   militaire de carriere ( art. 94, A.N. 1854/1951 art. 75 par. 7 ) : base = la solde soumise a pension du grade
#   superieur ( CHOIX : la solde de son metier a la grille publique du jour - le moteur paie par metier, pas par grade ) ;
#   la veuve 7/10, + 1/10 par enfant, jusqu a la base entiere ; sans veuve, le premier enfant 7/10, + 1/10 par autre ;
#   conscrit ( art. 88 et 90 ) : 40 x 1,219 % = 48,76 % de la solde de base du capitaine, indexee ( CHOIX : la solde du
#   metier officier ), + 2 % par enfant ( art. 95 par. 2, grade d adjudant ) ; sans veuve, le premier enfant la base ;
#   non marie et sans enfant ( art. 18 et 91 ) : le pere et la mere vivants a parts egales ( art. 91 par. 5 ) - la base
#   du conscrit, ou 7/10 de celle du militaire de carriere ( CHOIX : le seul ayant droit de l art. 94 par. 2 ) ;
#   enfants ( art. 35 ) : fils non maries de moins de 18 ans, filles non mariees ;
#   quand le defunt ouvre aussi une pension de survivant, la famille touche la plus forte au jour du deces ( art. 94
#   par. 3 ; CHOIX : pas de cumul ).
GUERRE_CONSCRIT = 40 * 0.01219
GUERRE_ENFANT_CONSCRIT = 0.02
GUERRE_PREMIER = 0.70
GUERRE_SUIVANT = 0.10
AGE_FILS_GUERRE = 18.0
EVENEMENTS_HMT194 = ("reversion_ouverte", "pension_guerre_ouverte", "reversion_close")
'''

CLASSE = '''

class Reversion:
    """( 03/10, HMT-194 3b ) Une pension de survivant ( caisse ) ou de guerre ( Etat ) : son beneficiaire, le defunt, la
    nature ( survivant, guerre ), la qualite ( conjoint, enfant, orphelin, parent ), la base mensuelle du defunt et sa
    part nationale ( survivant ; la pension de guerre se recalcule chaque jour sur la grille ), le metier du defunt et
    s il etait conscrit ( guerre ), le jour du deces."""
    __slots__ = ("hid", "defunt", "nature", "qualite", "base", "nationale", "role", "conscrit", "jour")

    def __init__(self, hid, defunt, nature, qualite, base, nationale, role, conscrit, jour):
        if nature not in ("survivant", "guerre") or qualite not in ("conjoint", "enfant", "orphelin", "parent"):
            raise ValueError(f"reversion invalide : {nature!r}, {qualite!r}")
        if not base >= 0.0 or not 0.0 <= nationale <= base + TOL: raise ValueError("base de reversion invalide")
        self.hid, self.defunt, self.nature, self.qualite = int(hid), int(defunt), nature, qualite
        self.base, self.nationale, self.role, self.conscrit, self.jour = float(base), float(nationale), role, bool(conscrit), int(jour)


def _age_j(p, i):
    return (p.jour - int(p.col("habitant", "naissance_j")[i])) / JOURS_AN


def _enfant_ayant_droit(p, k, nature):
    """Un enfant garde son droit : vivant, non marie, de moins de 24 ans ( survivant ) ; fils de moins de 18 ans ou fille
    ( guerre, art. 35 )."""
    col = p.colonnes["habitant"]
    if not p.w.table.vivant[k] or int(col["conjoint"][k]) >= 0: return False
    if nature == "guerre": return int(col["sexe"][k]) == POP.FEMME or _age_j(p, k) < AGE_FILS_GUERRE
    return _age_j(p, k) < AGE_ENFANT_SURVIVANT


def _famille_du_defunt(p, i):
    """( conjoint ou -1, enfants vivants, parents vivants ) au deces de i : le defunt garde son lien de conjoint
    ( domaine 1 ), le conjoint a ete rendu veuf."""
    col = p.colonnes["habitant"]; tb = p.w.table
    c = int(col["conjoint"][i])
    conj = c if c >= 0 and tb.vivant[c] and int(col["conjoint"][c]) < 0 else -1
    enf = sorted(int(k) for k in p.domaine("population").enfants_de.get(i, ()) if tb.vivant[int(k)])
    par = [int(col[k][i]) for k in ("pere", "mere") if col[k][i] >= 0 and tb.vivant[int(col[k][i])]]
    return conj, enf, par


def _orphelin(p, i, k):
    """L enfant k du defunt i a-t-il perdu son autre parent ?"""
    col = p.colonnes["habitant"]
    autre = int(col["mere"][k]) if int(col["pere"][k]) == i else int(col["pere"][k])
    return autre < 0 or not p.w.table.vivant[autre]


def _enfant_commun(p, i, c):
    col = p.colonnes["habitant"]
    return any({int(col["pere"][k]), int(col["mere"][k])} == {i, c} for k in p.domaine("population").enfants_de.get(i, ()))


def _conscrit(p, i):
    """Le defunt etait-il appele ( domaine 25 ; sa ligne garde le numero de l habitant apres son depart ) ?"""
    if not p.a("armee"): return False
    from . import d25_armee as A
    E = A._dom(p).eff; r = int(p.col("habitant", "ar_rang")[i])
    if r < 0:
        rr = np.nonzero(E["hid"][:E.n] == i)[0]
        if not len(rr): return False
        r = int(rr[-1])
    return bool(E["conscrit"][r])


def _montants(p, d, rs):
    """[ ( reversion, mensuel ) ] d une famille ( un defunt, une nature ), aux taux et a la grille du jour."""
    if not rs: return []
    r0 = rs[0]; col = p.colonnes["habitant"]
    if r0.nature == "survivant":
        t = []
        for r in rs:
            if r.qualite == "conjoint":
                actif = int(col["tr_statut"][r.hid]) in EN_EMPLOI or r.hid in d.pensions
                t.append(TAUX_CONJOINT if p.jour - r.jour < TROIS_ANS_J or not actif else TAUX_CONJOINT_REDUIT)
            else: t.append(TAUX_ORPHELIN if r.qualite == "orphelin" else TAUX_ENFANT)
        k = min(1.0, 1.0 / math.fsum(t))
        return [(r, r.base * x * k) for r, x in zip(rs, t)]
    from . import d25_armee as A
    if r0.conscrit: S, premier, suivant, plafond = A.solde_annuelle(p, "officier") / 12.0, GUERRE_CONSCRIT, GUERRE_ENFANT_CONSCRIT, math.inf
    else: S, premier, suivant, plafond = A.solde_annuelle(p, r0.role) / 12.0, GUERRE_PREMIER, GUERRE_SUIVANT, 1.0
    par = [r for r in rs if r.qualite == "parent"]
    if par: t = [premier / len(par) if r.qualite == "parent" else 0.0 for r in rs]
    else:
        tete = next((r for r in rs if r.qualite == "conjoint"), rs[0])
        t = [premier if r is tete else suivant for r in rs]
    k = min(1.0, plafond / math.fsum(t)) if math.fsum(t) > 0 else 1.0
    return [(r, S * x * k) for r, x in zip(rs, t)]


def _ouvrir_reversions(p, d, i):
    """Au deces de i, vu le matin : la pension de survivant ( caisse ) ou de guerre ( Etat ) de sa famille, la plus
    forte au jour du deces quand il ouvre les deux. Rend le nombre de pensions ouvertes."""
    col = p.colonnes["habitant"]; tb = p.w.table
    cause = POP.CAUSES[int(col["cause_deces"][i])] if "cause_deces" in col else "inconnue"
    conj, enf, par = _famille_du_defunt(p, i)
    pn = d.pensions.get(i)
    if pn is not None: base, nat = pn.mensuelle, pn.nationale
    else:
        base, nat, _, _ = calculer_pension(float(col["tr_jours_cotises"][i]), float(col["tr_assiette"][i]), _age_j(p, i),
                                           invalidite=True)
    ls = []
    if base > 0.0:
        union = int(col["union_j"][i])
        if conj >= 0 and (union <= 0 or p.jour - union >= TROIS_ANS_J or cause in CAUSES_SANS_DUREE_MARIAGE
                          or _enfant_commun(p, i, conj)):
            ls.append((conj, "conjoint"))
        ls += [(k, "orphelin" if _orphelin(p, i, k) else "enfant") for k in enf if _enfant_ayant_droit(p, k, "survivant")]
    role = _role_de(tb, i); lg = []; conscrit = False
    if cause == "combat" and role in ("soldat", "officier"):
        conscrit = _conscrit(p, i)
        lg = ([(conj, "conjoint")] if conj >= 0 else []) + [(k, "enfant") for k in enf if _enfant_ayant_droit(p, k, "guerre")]
        if not lg: lg = [(k, "parent") for k in par]
    rs = [Reversion(k, i, "survivant", q, base, nat, role, False, p.jour) for k, q in ls]
    rg = [Reversion(k, i, "guerre", q, 0.0, 0.0, role, conscrit, p.jour) for k, q in lg]
    if rs and rg:
        if math.fsum(m for _, m in _montants(p, d, rg)) >= math.fsum(m for _, m in _montants(p, d, rs)): rs = []
        else: rg = []
    if getattr(d, "reversions", None) is None: d.reversions = []
    d.reversions.extend(rs + rg)
    for r in rs + rg: p.compter("pension_guerre_ouverte" if r.nature == "guerre" else "reversion_ouverte")
    return len(rs) + len(rg)


def _reversions_du_jour(p, d):
    """Les pensions de survivant et de guerre du jour : d abord celles qui cessent ( deces, remariage, age, mariage ),
    puis les montants par famille. Rend ( [ ( beneficiaire, par jour, part nationale par jour ) ] de la caisse,
    [ ( beneficiaire, par jour ) ] de l Etat )."""
    rs = getattr(d, "reversions", None)
    if not rs: return [], []
    col = p.colonnes["habitant"]; tb = p.w.table
    garder = []
    for r in rs:
        ok = bool(tb.vivant[r.hid])
        if ok and r.qualite == "conjoint": ok = int(col["conjoint"][r.hid]) < 0
        elif ok and r.qualite in ("enfant", "orphelin"): ok = _enfant_ayant_droit(p, r.hid, r.nature)
        if ok: garder.append(r)
        else: p.compter("reversion_close")
    d.reversions = garder
    fam = {}
    for r in garder: fam.setdefault((r.defunt, r.nature), []).append(r)
    surv, guerre = [], []
    for cle in sorted(fam):
        for r, m in _montants(p, d, fam[cle]):
            j = m * 12.0 / JOURS_AN
            if r.nature == "survivant": surv.append((r.hid, j, j * (r.nationale / r.base if r.base > 0 else 0.0)))
            else: guerre.append((r.hid, j))
    return surv, guerre


class Indemnite:
'''

remplacer("monde/pays/d04_travail.py", [
    ("""                                                      # d allocation d invalidite non contributive ( a calibrer par degre )
""", CONSTANTES),
    ("""

class Indemnite:
""", CLASSE),
    ('''"hors_paie", "placements", "marge_veille")''', '''"hors_paie", "placements", "marge_veille", "reversions")'''),
    ("""        self.placements = 0.0       # reserves de la caisse pretees a l Etat ( encours )
""", """        self.placements = 0.0       # reserves de la caisse pretees a l Etat ( encours )
        self.reversions = []        # ( 03/10, HMT-194 3b ) les pensions de survivant et de guerre en cours
"""),
    ("""            if st[i] != HORS:
                st[i] = HORS; _fermer_contrat(col, i); d.pensions.pop(i, None); d.indemnites.pop(i, None)
""", """            if st[i] != HORS:
                _ouvrir_reversions(p, d, i)                # ( 03/10, HMT-194 3b ) avant que sa pension ne tombe
                st[i] = HORS; _fermer_contrat(col, i); d.pensions.pop(i, None); d.indemnites.pop(i, None)
"""),
    ("""    for i, ind in d.indemnites.items():
        if not 0 <= i < n: raise IndexError(i)
""", """    surv, guerre = _reversions_du_jour(p, d)               # ( 03/10, HMT-194 3b ) survivants ( caisse ), guerre ( Etat )
    for i, m, nj in surv:
        dues.append((i, m, "pension_survivant")); nat += nj
    for i, ind in d.indemnites.items():
        if not 0 <= i < n: raise IndexError(i)
"""),
    ("""    besoin = nat + max(0.0, total + arr - c.caisse - nat)
""", """    besoin = nat + max(0.0, total + arr - c.caisse - nat) + math.fsum(m for _, m in guerre)   # ( HMT-194 3b ) la guerre
"""),
    ('''            agg["indemnites" if mot == "indemnite_chomage" else "pensions"] += x
            agg["prestations_dues"] += du
        col["tr_net_jour"][i] += x
''', '''            agg["indemnites" if mot == "indemnite_chomage" else "pensions"] += x
            agg["prestations_dues"] += du
        col["tr_net_jour"][i] += x
    for i, m in guerre:                                          # ( 03/10, HMT-194 3b ) la pension de guerre : l Etat paie
        x, du = _payer(p, g, _menage_de(tb, i), m, "pension")
        agg["pensions"] += x; agg["prestations_dues"] += du
        col["tr_net_jour"][i] += x
'''),
    ('''("pension_invalidite", "prestation"), ("indemnite_chomage", "prestation"),''',
     '''("pension_invalidite", "prestation"), ("pension_survivant", "prestation"), ("indemnite_chomage", "prestation"),'''),
    ('''"indemnite_ouverte", "accident_travail", "heures_non_travaillees", "arrieres_salaire") + EVENEMENTS_HMT126:''',
     '''"indemnite_ouverte", "accident_travail", "heures_non_travaillees", "arrieres_salaire") + EVENEMENTS_HMT126 + EVENEMENTS_HMT194:'''),
    ("""   commerciale ), Pension, Indemnite, Greve,""",
     """   commerciale ), Pension, Reversion ( pension de survivant ou de guerre, HMT-194 3b ), Indemnite, Greve,"""),
    ("""6. Portes : tests_d04_travail.py.""",
     """6. Portes : tests_d04_travail.py ; pensions de survivant et de guerre : guerre/porte_pension_survivant.py ( HMT-194 3b )."""),
])
