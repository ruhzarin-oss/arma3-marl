"""29/09 ( loi d Engel hors alimentation, demande de Younes : reprise de Victoria 3 ) : au domaine 3, le reste du budget
des menages ( hors alimentation ) se partageait selon les memes parts chez tous. Desormais chaque menage le partage selon
son quintile de depense equivalente dans son ile, avec les structures d ELSTAT 2024 ( enquete sur le budget des familles,
tableaux 14 et 15 ; quintiles 2 a 4 par la courbe de Working-Leser ). La nourriture ( HMT-140, session Classes ) et les
prix ne changent pas. Le meme texte pour le depot et pour l arbre des references. A placer en fin de chaine. Chaque
remplacement deja fait est saute : idempotent.   python patch_engel.py racine_de_l_arbre   ( racine/monde/pays/d03_economie.py )"""
import os, sys

FICHE_AVANT = '''   s use. Tables eparses : proprietaires ( entreprise -> habitant ),
'''
FICHE_APRES = '''   s use. ( 29/09, loi d Engel ) Colonne eco_rang_depense : le rang de depense equivalente du menage dans son ile
   ( 0 a 1 ) ; le reste de son budget, hors alimentation, se partage selon son quintile ( ELSTAT 2024, ENGEL_PARTS ).
   Tables eparses : proprietaires ( entreprise -> habitant ),
'''

BLOC_AVANT = '''                  "alimentation": (0.0, ()), "equipement": (0.0, ())}
'''
BLOC_APRES = '''                  "alimentation": (0.0, ()), "equipement": (0.0, ())}

# ( 29/09, a la demande de Younes : reprise de Victoria 3, la consommation par niveau de richesse ) LA LOI D ENGEL HORS
# ALIMENTATION. Jusqu ici le reste du budget ( ce qui n est pas la nourriture ) se partageait selon les memes parts
# ( PARTS_HORS_ALIM ) chez tous les menages. ELSTAT, enquete sur le budget des familles 2024 ( communique du 25/09/2025 ),
# tableau 15 : les 20 % de la population a la plus faible depense equivalente ( quintile 1 ) et les 20 % a la plus forte
# ( quintile 5 ) ne partagent pas leur budget de la meme facon ( % ) :
#               alim  alc-tab  habill  logement  equip  sante  transp  comm  loisirs  educ  restau  divers
#   quintile 1  33,5    2,3     3,1     22,4     3,7    6,7     6,9    7,7    1,2     1,1    5,6    1,5 + 4,4
#   quintile 5  12,7    3,9     5,1     12,0     5,0   10,1    17,0    3,5    6,7     3,5   13,0    2,7 + 4,8
# ( divers = assurances et services financiers + soins personnels, protection sociale et divers : les 13 postes de 2024,
# COICOP 2018, ramenes aux 12 divisions du moteur ). Entre les deux, la courbe d Engel de Working ( 1943 ) et Leser
# ( 1963 ) : la part est lineaire en log de la depense, w( x ) = w1 + ( w5 - w1 ) x ( ln x - ln x1 ) / ( ln x5 - ln x1 ),
# aux depenses equivalentes medianes des quintiles ( tableau 14 : 411,60 ; 644,16 ; 856,85 ; 1 138,24 ; 2 337,23 euros
# par mois ). Controle sur le reel ( calcule avant la porte ) : la moyenne des cinq quintiles ponderee par leur depense
# rend la structure d ensemble du tableau 1 a 1,35 point pres ( restauration 10,5 contre 11,8 ; logement 15,6 contre
# 14,4 ; alimentation 19,9 contre 20,7 ; transport 13,5 contre 13,3 ).
# L alimentation n est pas ici : sa part suit le besoin et la qualite ( HMT-140 point 7, session Classes ). Les parts de
# chaque quintile sont renormalisees HORS alimentation ( ENGEL_PARTS, 5 x K, alimentation 0 ) : le quintile 1 met 33,6 %
# de son reste dans le logement et 1,8 % dans les loisirs, le quintile 5 13,7 % et 7,7 %.
# Le quintile d un menage : son RANG dans la distribution de sa consommation voulue ( repartir_budget ) par unite de
# consommation ( echelle OCDE modifiee d ELSTAT ), ponderee par les personnes presentes, sur les menages habites de son
# ile, chaque soir ( les ex aequo au meme rang ). Par le rang et non par le niveau : un menage des 20 % les moins
# depensiers de son ile partage son budget comme les 20 % les moins depensiers de Grece, et l inegalite du monde ( S80/S20
# de 12,6 contre 5,68 ) ne deforme pas les parts ; elle pese sur l ensemble par les montants. Par quintile et non en
# continu : ELSTAT ne publie que des quintiles, une courbe continue entre leurs centres serait une hypothese de plus.
# Ce que ca change dans le monde : ce que le domaine 3 achete lui-meme ( carburant, remedes, biens et services marchands :
# habillement, boissons et tabac, restauration, divers ) suit le quintile ; ce qu un autre domaine sert ( loyers,
# factures, ecole, loisirs ) reste a ce domaine, mais la part qui lui est reservee change ce qui reste pour le reste. Les
# durables gardent leur cible ( equipement_vise, que le credit lit aussi ) : leur part hors alimentation va de 5,6 a 5,7 %
# entre les quintiles extremes.
ENGEL_Q1 = np.array([33.5, 2.3, 3.1, 22.4, 3.7, 6.7, 6.9, 7.7, 1.2, 1.1, 5.6, 1.5 + 4.4]) / 100.0
ENGEL_Q5 = np.array([12.7, 3.9, 5.1, 12.0, 5.0, 10.1, 17.0, 3.5, 6.7, 3.5, 13.0, 2.7 + 4.8]) / 100.0
ENGEL_ENSEMBLE = np.array([20.7, 3.4, 5.0, 14.4, 4.3, 7.8, 13.3, 4.8, 4.0, 3.5, 11.8, 2.2 + 4.9]) / 100.0   # tableau 1
ENGEL_DEPENSES = np.array([411.60, 644.16, 856.85, 1138.24, 2337.23])   # tableau 14 : euros par mois, par adulte-equivalent
ENGEL_LAMBDA = (np.log(ENGEL_DEPENSES) - math.log(ENGEL_DEPENSES[0])) / math.log(ENGEL_DEPENSES[4] / ENGEL_DEPENSES[0])
ENGEL_ELSTAT = ENGEL_Q1[None, :] + ENGEL_LAMBDA[:, None] * (ENGEL_Q5 - ENGEL_Q1)[None, :]   # 5 x K : le budget entier
ENGEL_PARTS = ENGEL_ELSTAT.copy(); ENGEL_PARTS[:, I_ALIM] = 0.0
ENGEL_PARTS /= ENGEL_PARTS.sum(axis=1, keepdims=True)                                      # 5 x K : le reste
AGE_ADULTE_UC_ENGEL = 16.0      # l echelle d ELSTAT : 0,5 a partir de 16 ans, 0,3 en dessous ( comme HMT-140 )


def rang_pondere(x, poids):
    """( Engel, fonction pure ) Le rang de chaque valeur de `x` dans sa distribution ponderee par `poids`, entre 0 et 1 :
    le milieu de son poids dans le cumul ; des ex aequo partagent le milieu de leur groupe."""
    x = np.asarray(x, dtype=float); pw = np.asarray(poids, dtype=float)
    tot = float(pw.sum())
    if not len(x) or tot <= 0.0: return np.full(len(x), 0.5)
    o = np.argsort(x, kind="stable"); xs = x[o]; cw = np.cumsum(pw[o])
    deb = np.flatnonzero(np.r_[True, xs[1:] != xs[:-1]])
    fin = np.r_[deb[1:], len(xs)] - 1
    avant = np.where(deb > 0, cw[deb - 1], 0.0)
    r = np.empty(len(x))
    r[o] = np.repeat((avant + cw[fin]) / (2.0 * tot), fin - deb + 1)
    return r


def quintile_de_rang(rang):
    """( Engel, fonction pure ) Le quintile ( 0 a 4 ) d un rang entre 0 et 1."""
    return np.minimum(4, np.floor(np.asarray(rang, dtype=float) * 5.0).astype(np.int64))


def partager_le_reste(M, parts):
    """( Engel, fonction pure ) Le budget voulu `M` ( n x K, repartir_budget ) dont le reste, hors alimentation, est
    repartage selon `parts` ( n x K, alimentation 0, lignes de somme 1 ) : la nourriture et le total ne changent pas."""
    M = np.asarray(M, dtype=float)
    reste = M.sum(axis=1) - M[:, I_ALIM]
    out = reste[:, None] * np.asarray(parts, dtype=float)
    out[:, I_ALIM] = M[:, I_ALIM]
    return out


def _uc_engel(p, n):
    """Les unites de consommation de chaque menage ( echelle OCDE modifiee d ELSTAT : 1 le premier adulte, 0,5 chaque autre
    personne de 16 ans et plus, 0,3 chaque enfant ; les presents seulement ; sans adulte present, le premier enfant
    compte 1 ; un menage vide, 0 ). COPIE PROVISOIRE de unites_de_consommation ( session Classes, HMT-140, branche
    revenu-nourriture ) : a remplacer par elle a la fusion, pour classer les menages avec la meme mesure."""
    tb = p.w.table; nh = tb.n
    mid = np.where((tb.vivant[:nh] == 1) & (tb.statut[:nh] != PO.ABSENT), tb.menage[:nh], -1).astype(np.int64)
    ok = (mid >= 0) & (mid < n)
    if "naissance_j" in p.colonnes["habitant"]:
        age = (p.jour - p.col("habitant", "naissance_j")[:nh].astype(np.float64)) / JOURS_AN
    else: age = tb.age[:nh].astype(np.float64)
    ad = np.bincount(mid[ok & (age >= AGE_ADULTE_UC_ENGEL)], minlength=n)[:n].astype(np.float64)
    en = np.bincount(mid[ok & (age < AGE_ADULTE_UC_ENGEL)], minlength=n)[:n].astype(np.float64)
    return np.where(ad > 0, 1.0 + 0.5 * (ad - 1.0) + 0.3 * en, np.where(en > 0, 1.0 + 0.3 * (en - 1.0), 0.0))


def _colonne_rang(p, n):
    """La colonne eco_rang_depense ( posee aussi sur un monde installe avant elle : instantane relu )."""
    cm = p.colonnes["menage"]
    if "eco_rang_depense" not in cm: cm.ajouter("eco_rang_depense", np.float64, 0.5)
    cm.assurer(n)
    return cm["eco_rang_depense"]


def parts_des_menages(p, n, ok, v, rev, caisse, tampon):
    """( Engel ) Les parts du reste de chaque menage ( n x K ) : le rang de sa consommation voulue par unite de
    consommation parmi les menages habites ( `ok`, `v` personnes presentes ), son quintile, ENGEL_PARTS de ce quintile.
    Le rang est ecrit dans eco_rang_depense ( 0,5 pour un menage inhabite )."""
    uc = _uc_engel(p, n)
    cv = repartir_budget(rev, caisse, tampon, np.zeros(n))[0]
    sel = np.asarray(ok) & (uc > 0.0)
    r = np.full(n, 0.5)
    if sel.any(): r[sel] = rang_pondere(cv[sel] / uc[sel], np.asarray(v, dtype=float)[sel])
    _colonne_rang(p, n)[:n] = r
    return ENGEL_PARTS[quintile_de_rang(r)]


'''

SLOTS_AVANT = '''                 "exceptionnelle", "recalibrage", "faillites", "part_bien")
'''
SLOTS_APRES = '''                 "exceptionnelle", "recalibrage", "faillites", "part_bien", "budget_rang")
'''

INIT_AVANT = '''        self.part_bien = None
'''
INIT_APRES = '''        self.part_bien = None
        self.budget_rang = np.zeros((5, K))   # ( Engel ) quintile de rang de depense x division : drachmes voulues, cumul
'''

ACHATS_AVANT = '''    M[~ok] = 0.0
'''
ACHATS_APRES = '''    # ( 29/09, loi d Engel ) le reste du budget, hors alimentation, se partage selon le quintile de depense du menage
    M = partager_le_reste(M, parts_des_menages(p, n, ok, v, rev, caisse_engel, tampon))
    M[~ok] = 0.0
'''

QUINTILES_AVANT = '''        for qn in range(5): d.budget[qn] += M[io[quint == qn]].sum(axis=0)
'''
QUINTILES_APRES = '''        for qn in range(5): d.budget[qn] += M[io[quint == qn]].sum(axis=0)
        # ( Engel ) et par quintile de rang de depense ( eco_rang_depense ), celui qui partage le reste
        br = getattr(d, "budget_rang", None)
        if br is None: br = d.budget_rang = np.zeros((5, K))       # un monde installe avant ( instantane relu )
        qr = quintile_de_rang(p.col("menage", "eco_rang_depense")[:n][io])
        for qn in range(5): br[qn] += M[io[qr == qn]].sum(axis=0)
'''

BUDGET_AVANT = '''            "elstat": dict(zip(NOMS_CATEGORIES, PARTS.tolist()))}
'''
BUDGET_APRES = '''            "elstat": dict(zip(NOMS_CATEGORIES, PARTS.tolist())),
            # ( Engel ) les parts du budget voulu par quintile de rang de depense ( 5 x K ), et celles d ELSTAT 2024
            "parts_par_quintile_rang": _parts_des_lignes(getattr(p.domaine("economie"), "budget_rang", None)),
            "engel_elstat": ENGEL_ELSTAT.tolist()}


def _parts_des_lignes(B):
    """( Engel ) Chaque ligne d un tableau de drachmes rapportee a sa somme ( [] sans tableau )."""
    if B is None: return []
    return (B / np.maximum(1e-12, B.sum(axis=1, keepdims=True))).tolist()
'''

CAISSE_AVANT = '''    _assurer_hmt126(p)
    gm = w.table.menages.garde_manger[:n].copy()
'''
CAISSE_APRES = '''    _assurer_hmt126(p)
    caisse_engel = caisse          # ( Engel ) la caisse d avant la nourriture : le rang se mesure comme la qualite ( HMT-140 )
    gm = w.table.menages.garde_manger[:n].copy()
'''

REMPLACEMENTS = ((FICHE_AVANT, FICHE_APRES), (BLOC_AVANT, BLOC_APRES), (SLOTS_AVANT, SLOTS_APRES),
                 (INIT_AVANT, INIT_APRES), (CAISSE_AVANT, CAISSE_APRES), (ACHATS_AVANT, ACHATS_APRES), (QUINTILES_AVANT, QUINTILES_APRES),
                 (BUDGET_AVANT, BUDGET_APRES))


def appliquer(chemin):
    s = open(chemin, encoding="utf-8").read()
    for avant, apres in REMPLACEMENTS:
        if apres in s: continue                      # deja fait
        if s.count(avant) != 1: raise SystemExit(f"{chemin} : ancre introuvable ou multiple : {avant[:70]!r}")
        s = s.replace(avant, apres, 1)
    open(chemin, "w", encoding="utf-8").write(s)
    print(f"loi d Engel hors alimentation : {chemin}")


if __name__ == "__main__":
    appliquer(os.path.join(sys.argv[1], "monde", "pays", "d03_economie.py"))
