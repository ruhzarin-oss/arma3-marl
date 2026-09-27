"""Applique la correction des prix du 27/09 a un arbre ( d03_economie.py ) : la couverture se mesure sur le stock AVANT les
courses du soir, le prix est rappele vers la parite a l import quand il la depasse ( code de la guerre des iles ), et un
bien echangeable ne descend pas sous la parite a l export ( le carburant tombait a 0,25 fois le prix mondial pendant que
le negoce l exportait ). Idempotent.
   python patch_prix.py <racine>      ( racine/monde/pays/d03_economie.py )"""
import os, re, sys
racine = sys.argv[1]
f = os.path.join(racine, "monde", "pays", "d03_economie.py")
s = open(f).read()
DEJA = "stock_soir" in s
if DEJA: print("deja corrige :", f)


def sub(a, b):
    global s
    if DEJA: return
    assert s.count(a) == 1, (f, a[:70], s.count(a)); s = s.replace(a, b)


if not DEJA and not re.search(r"^import .*\bimportlib\b", s, re.M):
    m = re.search(r"^(import|from) ", s, re.M); s = s[:m.start()] + "import importlib\n" + s[m.start():]
# 1. les constantes
sub("PARITE_EXPORT = 0.8             # le moteur exporte les surplus de nourriture a 0,8 fois le prix mondial ( monde.py, expedier )\n",
'''PARITE_EXPORT = 0.8             # le moteur exporte les surplus de nourriture a 0,8 fois le prix mondial ( monde.py, expedier )
# 27/09 ( Younes : « au plus realiste » ; inflation x2 en 30 jours mesuree par la porte de ressemblance ) :
# ( 1 ) la couverture que lit le marchand a l aube est celle du stock qu il AVAIT A OFFRIR la veille a 19 h, avant les
# courses : il se reapprovisionne chez son negociant jusqu a sa cible a 18 h 50 ( domaine 7 ), et lisait son stock a
# l aube, apres les courses - 1,3 jour pour une cible de 2, chaque jour, donc +3 % par jour jusqu au plafond ( 2,5 fois
# le prix mondial en 35 jours ) avec des greniers pleins ; ( 2 ) au-dessus de la parite a l import, la concurrence des
# importateurs rappelle le prix vers elle tant que la banque centrale fournit des devises ( loi du prix unique, guerre
# des iles, vitesse a calibrer ) ; ( 3 ) un bien echangeable ne se vend pas chez soi sous ce que le monde en donne au
# port : le carburant tombait a 0,25 fois le prix mondial pendant que le negoce exportait le stock du marche.
BETA_PARITE = 0.2
# ( 4 ) les prix sont collants ( Bils et Klenow 2004 : un prix de detail tient des mois ; l alimentaire bouge plus souvent,
# par petits pas ) : tant que la couverture reste a moins de TOLERANCE_COUVERTURE de sa cible ( en part de la cible ), le
# prix ne bouge qu au quart de la vitesse ; une rupture ( non servi ) ou un stock hors de la bande le fait bouger. Sans la bande, les fermes qui
# livrent juste ce qu on mange ( 1 a 1,8 jour a 19 h pour une cible de 2 ) faisaient monter le prix de 0,5 % par jour jusqu a
# la parite a l import, pour rien : le prix n apporte pas une ration de plus quand la recolte part deja en entier.
TOLERANCE_COUVERTURE = 0.5
LENTEUR_DANS_LA_BANDE = 0.25    # dans la bande, le prix bouge au quart de la vitesse : il redescend quand le stock est a l aise
''')
# 4 bis. la bande morte
sub('''            x = max(-1.0, min(1.0, (cible - couv) / cible))
''', '''            x = max(-1.0, min(1.0, (cible - couv) / cible))
            if abs(couv - cible) <= TOLERANCE_COUVERTURE * cible: x *= LENTEUR_DANS_LA_BANDE   # 27/09 : prix collants dans la bande
''')
# 2. l etat du marche garde le stock du soir
sub('''    __slots__ = ("id", "demande_lisse", "non_servi", "non_solvable", "couverture", "ventes_ht", "ventes_q", "ventes_jour")

    def __init__(self, id, demande0):
        self.id = id
''', '''    __slots__ = ("id", "demande_lisse", "non_servi", "non_solvable", "couverture", "ventes_ht", "ventes_q", "ventes_jour",
                 "stock_soir")

    def __init__(self, id, demande0):
        self.id = id
        self.stock_soir = None                          # { bien : stock a 19 h, avant les courses } ( 27/09 )
''')
# 3. les courses du soir notent le stock qu elles trouvent
sub('''    marches = [w.marches[k] for k in d.ids_marches]
    mi = _rang_marche_menages(w, d, n)
''', '''    marches = [w.marches[k] for k in d.ids_marches]
    for m in marches:                                   # 27/09 : ce que le marche avait a offrir, lu par _ajuster_prix a l aube
        d.marches[m.lieu.id].stock_soir = {b: m.stocks[b] for b in BIENS_PRIX}
    mi = _rang_marche_menages(w, d, n)
''')
# 4. la regle de l aube
sub('''            couv = max(0.0, m.stocks[b]) / dem
''', '''            ss = getattr(em, "stock_soir", None)         # 27/09 : le stock d hier 19 h, avant les courses ; sinon l aube
            couv = max(0.0, ss[b] if ss is not None and b in ss else m.stocks[b]) / dem
''')
sub('''            m.prix[b] = _borner(w, b, m.prix[b] * math.exp(dlog))
''', '''            par = _parite_import(p, m, b)                # 27/09 : au-dessus de la parite a l import, les importateurs ramenent le prix
            if par is not None and m.prix[b] > par: dlog += BETA_PARITE * (math.log(par) - math.log(m.prix[b]))
            x = m.prix[b] * math.exp(dlog)
            bas = _plancher_export(p, m, b)               # 27/09 : jamais sous ce que le monde en donne au port
            if bas is not None: x = max(x, bas)
            m.prix[b] = _borner(w, b, x)
''')
sub('''def _transport_unitaire(w, a, o):''', '''def _parite_import(p, m, b):
    """Le prix de detail auquel l importation d un bien devient rentable ( cout rendu, marges du negoce et du detail ) ;
    None si la banque centrale ne fournit pas de devises ou si le bien ne s importe pas ( guerre des iles, 27/09 )."""
    if not p.a("exterieur"): return None
    X = importlib.import_module(".d07_exterieur", __package__)
    if b not in X.BIENS_IMPORT: return None
    euros, _ = X.reserves_de_change(p)
    if euros <= X.PLANCHER_RESERVES: return None
    return X.prix_import(p, b) * (1.0 + X.MARGE_NEGOCE) / (1.0 - m.marge)


def _plancher_export(p, m, b):
    """Le prix de detail sous lequel le negoce exporterait le bien : ce que l etranger paie au port, moins la marge du
    negoce, sur la marge du detaillant ( loi du prix unique, 27/09 ). La nourriture garde la borne du moteur
    ( PARITE_EXPORT ) ; None sans negoce ou pour un bien qui ne s echange pas."""
    if b == "nourriture" or not p.a("exterieur"): return None
    X = importlib.import_module(".d07_exterieur", __package__)
    if b not in X.BIENS_IMPORT: return None
    return X.prix_export(p, b) * (1.0 - X.MARGE_NEGOCE) / (1.0 - m.marge)


def _transport_unitaire(w, a, o):''')
if not DEJA: open(f, "w").write(s); print("corrige :", f)

# ------------------------------------------------------------------ d07 : le grossiste garnit le marche pour les jours fermes
f7 = os.path.join(racine, "monde", "pays", "d07_exterieur.py")
s7 = open(f7).read()
if "fermes = 1.0 + EC._jours_sans_marche(p)" in s7: print("deja corrige :", f7)
else:
    def sub7(a, b):
        global s7
        assert s7.count(a) == 1, (f7, a[:70], s7.count(a)); s7 = s7.replace(a, b)
    sub7('''            dem = _demande(p, neg.marche_id, nom)
            while lots:
                lot = lots[0]
                besoin = _cible(nom) * dem - m.stocks[nom]
''', '''            dem = _demande(p, neg.marche_id, nom)
            # 27/09 : la veille d une fermeture ( samedi, veille de ferie ), le marche se garnit aussi pour les jours fermes,
            # et un bien essentiel est rachete meme a perte s il manque pour ces jours-la. Sans cela, chaque samedi soir
            # manquait ( les fermes ne livrent pas le samedi, les menages achetent deux jours ) : une rupture par semaine, et
            # le prix de la nourriture montait d un cran a chaque fois, sans jamais redescendre.
            fermes = 1.0 + EC._jours_sans_marche(p)
            while lots:
                lot = lots[0]
                besoin = (_cible(nom) + fermes - 1.0) * dem - m.stocks[nom]
''')
    sub7('''                urgence = nom in ESSENTIELS and m.stocks[nom] < URGENCE_J * dem
''', '''                urgence = nom in ESSENTIELS and m.stocks[nom] < URGENCE_J * fermes * dem
''')
    open(f7, "w").write(s7); print("corrige :", f7)
