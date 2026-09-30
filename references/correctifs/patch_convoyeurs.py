"""29/09 ( HMT-140, cause 5 ) : les convoyeurs au reel - 4,4 pour 1 000 habitants ( Eurostat, fret routier H49.4 ), au
moins un par marche ; les autres vont aux metiers ouverts par le remplissage vers la structure reelle de
population.effectifs. La taille du pays ne change pas. Idempotent.
La regle suit celui qui porte le fret ( arbitrage du chef de projet, 29/09 ) : `generer( ..., fret= )`. « d15 » : le
domaine 15 porte le fret ( le monde complet ) - les convoyeurs au reel ; « e1 » ( defaut ) : les convois du moteur,
mecanisme d essai des mondes sans domaine 15 - les convoyeurs d E1, au bit. Le temoin et l archive des references sont
des mondes « e1 » : ils ne recoivent que les outils de l etape ( le remplissage, que l industrie au reel reprend ). Ancres propres : ni le corps de `effectifs`, ni les
lignes des effectifs d un metier ; l etape s ajoute A LA FIN ( elle enveloppe la fonction des effectifs deja posee ) et
se compose donc avec les autres correctifs de la generation, dans n importe quel ordre.
  - un depot d aujourd hui ( `def effectifs` ) : l etape `convoyeurs_au_reel`, `effectifs` qui l appelle en dernier si
    fret="d15", `generer` et `generer_reel` qui prennent `fret` et le passent ; ancres : la ligne `def generer(`, le
    renvoi au mode grec et l appel des effectifs de `generer`, la ligne `def generer_reel(` et ses deux appels des
    effectifs ;
  - un arbre d origine ou l ancien moteur temoin ( la boucle des effectifs d E1, corrigee par patch_patrons ) : un monde
    « e1 » ; seulement les outils de l etape ( patch_industrie les reprend ) ; ancre : la ligne `def generer(`. Les
    postes liberes vont a l agriculture et au commerce ( la cible annuelle de population.ACCUEIL, recopiee a
    l identique ) : ni hotellerie ni convoyeur n en naissent.
   python patch_convoyeurs.py <racine>      ( racine/monde/... pour un depot, racine/... pour le temoin )"""
import os, sys
racine = sys.argv[1]
base = os.path.join(racine, "monde") if os.path.exists(os.path.join(racine, "monde", "population.py")) else racine
fp = os.path.join(base, "population.py")
s = open(fp).read()
if "def convoyeurs_au_reel(" in s: print("deja :", fp); sys.exit(0)


def sub(t, a, b, f):
    assert t.count(a) == 1, (f, a[:70], t.count(a))
    return t.replace(a, b)


# ------------------------------------------------------------------ l etape, commune aux deux formes
REGLE = '''

# ================================================================== les convoyeurs au reel ( 29/09, HMT-140 cause 5 )
# Le monde E1 donne 25 convoyeurs pour 500 habitants ( config.ROLES ), 50 pour 1 000 : a 10 000 habitants, Altis lance
# 56 convois de 4,7 km par jour, 51 heures de conduite, et laisse ~ 350 de ses ~ 440 convoyeurs sans travail des le jour
# 5 ( mesure du 29/09, tronc 72f0873 ). Le reel : le fret routier et le demenagement ( NACE H49.4 ) emploient 45 591
# personnes en Grece en 2024 ( Eurostat sbs_sc_ovw ; 37 183 en 2019, sbs_na_1a_se_r2 ) pour 10 375 764 habitants
# ( demo_pjan ) : 4,4 pour 1 000 habitants, 1,07 % de l emploi. Au moins un convoyeur par marche : sans chauffeur a sa
# capitale, aucun convoi n y part. Les autres sont verses aux metiers ouverts par le meme remplissage vers la structure
# reelle ANNUELLE que les bras de l industrie ( population.ACCUEIL : agriculture et commerce ; ni l hotellerie,
# saisonniere, que le domaine 28 embauche a la saison, ni les convoyeurs, qui ne se recreent pas ).
#   https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sbs_sc_ovw?geo=EL&nace_r2=H494&indic_sbs=EMP_NR&size_emp=TOTAL
CONVOYEURS_POUR_MILLE = 1000.0 * 45591 / 10375764
# ( 30/09 ) 4,4 pour 1 000 est un ratio d EMPLOI ( H49.4 : personnes occupees ) : il vaut pour les convoyeurs AU TRAVAIL
# apres le recensement du domaine 4, qui ne laisse a leur poste qu une partie des nes ( monde E1, graine 71, 10 000
# habitants, tronc e8f1ee8 : 363 convoyeurs au travail sur 500 nes ). Au mode par defaut, les nes sont la cible divisee
# par cette survie ; une population copiee sur le reel ( `habitants` donne ) nait avec son statut : nes = cible.
SURVIE_RECENSEMENT = 363 / 500
ACCUEIL_CONVOYEURS = {"paysan": 467.8, "marchand": 712.9}   # = population.ACCUEIL ( porte ) : Grece, lfsa_egan2 2024


def _metier_ouvert(carte, role):
    types = TRAVAIL[role][0]
    return not types or types == ("gouvernement",) or bool(carte.de_type(*types))


def _remplir_vers(c, w, total):
    """Le remplissage vers les parts w sans aller contre ( le meme que population._vers_le_reel )."""
    c = np.asarray(c, np.float64); w = np.asarray(w, np.float64)
    haut_ = total > c.sum()
    f = (lambda l: np.maximum(c, l * w)) if haut_ else (lambda l: np.minimum(c, l * w))
    lo, hi = 0.0, 1.0
    while f(hi).sum() < total: hi *= 2.0
    for _ in range(200):
        mi = 0.5 * (lo + hi)
        if f(mi).sum() < total: lo = mi
        else: hi = mi
    return f(hi)


def _parts_entieres(total, poids):
    """Le partage entier de total au prorata de poids, plus forts restes ( le meme que population._quotas )."""
    poids = np.asarray(poids, np.float64)
    if total <= 0 or poids.sum() <= 0: return np.zeros(len(poids), np.int64)
    x = total * poids / poids.sum()
    q = np.floor(x).astype(np.int64)
    reste = int(total) - int(q.sum())
    if reste > 0: q[np.argsort(-(x - q), kind="stable")[:reste]] += 1
    return q


def convoyeurs_au_reel(carte, eff, entiers=True, habitants=None):
    """L etape de fin des effectifs : les convoyeurs ramenes a CONVOYEURS_POUR_MILLE des habitants EN EMPLOI ( monde E1 :
    somme des effectifs, et les nes divises par SURVIE_RECENSEMENT ; `habitants` pour une population copiee sur un pays
    reel, sans correction ), au moins un par capitale, jamais plus qu avant ; le surplus aux autres metiers ouverts, vers
    la structure reelle. La somme ne change pas."""
    if "convoyeur" not in eff or eff["convoyeur"] <= 0: return eff
    eff = dict(eff)
    n = float(sum(eff.values())) if habitants is None else float(habitants)
    vise = CONVOYEURS_POUR_MILLE * n / 1000.0 / (SURVIE_RECENSEMENT if habitants is None else 1.0)
    vise = max(vise, float(len(carte.capitales)))
    k = min(eff["convoyeur"], max(1, int(round(vise))) if entiers else vise)
    surplus = eff["convoyeur"] - k
    ouverts = [r for r in ACCUEIL_CONVOYEURS if r != "convoyeur" and r in eff and _metier_ouvert(carte, r)]
    if surplus <= 0 or not ouverts: return eff
    eff["convoyeur"] = k
    c = [float(eff[r]) for r in ouverts]
    d = _remplir_vers(c, [ACCUEIL_CONVOYEURS[r] for r in ouverts], sum(c) + surplus) - np.asarray(c)
    if entiers: d = _parts_entieres(int(surplus), np.maximum(d, 0.0))
    for r, x in zip(ouverts, d.tolist()): eff[r] += int(x) if entiers else x
    return eff
'''

if "def effectifs(" in s:
    # --- un depot d aujourd hui : l etape enveloppe `effectifs`, placee avant `generer` ( ni `_lieux_ponderes`, que le bras
    #     de la raffinerie reecrit, ni le corps d `effectifs`, que touchent la politique par ile et la raffinerie )
    ancre = "\n\ndef generer(carte, rng, echelle=1.0, table=None, demographie=None):"
    neuve = "\n\ndef generer(carte, rng, echelle=1.0, table=None, demographie=None, fret=\"e1\"):"
    s = sub(s, ancre, REGLE + '''

_effectifs_avant_convoyeurs = effectifs
FRETS = ("e1", "d15")      # qui porte le fret : les convois du moteur ( E1 ), ou le domaine 15


def effectifs(carte, echelle, entiers=True, emploi_civil_par_habitant=None, fret="e1"):
    """Les effectifs de la generation ( la fonction d avant ), puis, si le domaine 15 porte le fret ( fret="d15", le
    monde complet ), les convoyeurs au reel en derniere etape. fret="e1" ( defaut ) : les convoyeurs d E1, au bit - les
    convois du moteur, mecanisme d essai des mondes sans domaine 15, prennent leurs chauffeurs a la capitale du marche qui
    paie et en demandent bien plus que le reel ( 29/09 : avec 3 chauffeurs a 500 habitants, 12 514 convois refuses en
    40 jours et le marche de la mine sans gazole 20 jours ). Pour une population copiee sur un pays reel,
    `emploi_civil_par_habitant` donne sa taille ( generer_reel : les postes civils sur l emploi civil par habitant ) :
    c est sur elle que se comptent les 4,4 pour 1 000."""
    if fret not in FRETS: raise ValueError(f"fret inconnu {fret!r} : {FRETS}")
    eff = _effectifs_avant_convoyeurs(carte, echelle, entiers)
    if fret == "e1": return eff
    hab = None
    if emploi_civil_par_habitant is not None:
        civils = sum(v for r, v in eff.items() if r not in ("enfant", "retraite", "soldat", "officier"))
        hab = int(round(civils / emploi_civil_par_habitant))
    return convoyeurs_au_reel(carte, eff, entiers, hab)''' + neuve, fp)
    s = sub(s, "    if demographie is not None: return generer_reel(carte, rng, echelle, table, demographie)\n",
            "    if demographie is not None: return generer_reel(carte, rng, echelle, table, demographie, fret)\n", fp)
    s = sub(s, "    eff = effectifs(carte, echelle)\n    for role, (n, classe, _) in C.ROLES.items():\n",
            "    eff = effectifs(carte, echelle, fret=fret)\n    for role, (n, classe, _) in C.ROLES.items():\n", fp)
    s = sub(s, "def generer_reel(carte, rng, echelle, table, demographie):\n",
            "def generer_reel(carte, rng, echelle, table, demographie, fret=\"e1\"):\n", fp)
    s = sub(s, '''    eff = effectifs(carte, echelle)
    postes = []
''', '''    eff = effectifs(carte, echelle, emploi_civil_par_habitant=R.emploi_par_habitant() - R.PART_MILITAIRES, fret=fret)
    postes = []
''', fp)
    s = sub(s, "    unite = effectifs(carte, 1.0, entiers=False)\n", "    unite = effectifs(carte, 1.0, entiers=False, fret=fret)\n", fp)
    open(fp, "w").write(s); print("corrige :", fp)
    sys.exit(0)

# --- un arbre d origine ou le temoin : la boucle d E1 corrigee par patch_patrons
assert "_effectif_patrons" in s, (fp, "patch_patrons doit passer avant")
if "import numpy as np" not in s:
    s = sub(s, "from . import config as C\n", "import numpy as np\nfrom . import config as C\n", fp)
s = sub(s, "\n\ndef generer(carte, rng, echelle=1.0", REGLE + '''
# le temoin et l archive des references sont des mondes « e1 » ( les convois du moteur ) : les convoyeurs d E1 ; la
# regle au reel n y est pas appliquee, seuls ses outils servent ( patch_industrie )


def generer(carte, rng, echelle=1.0''', fp)
open(fp, "w").write(s); print("corrige :", fp)
