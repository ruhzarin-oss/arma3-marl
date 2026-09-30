"""30/09 ( session Classes, branche orphelins ) : aucun mineur seul le soir. Le jour meme ou le dernier adulte PRESENT
d un menage disparait ( mort, prison du domaine 21, voyage de l archipel ), ses mineurs rejoignent leur parente ( parent,
grand-parent, frere ou soeur majeur, oncle ou tante : AK 1510, 1589, 1592, 1463 ) sinon une famille d accueil ; une
absence les confie pour son temps. Un seul fichier : pays/d01_population.py. Ancres courtes, chacune dans la fonction
qu elle touche ; s applique a d01 du depot ( 6b054bd ) comme a celui de la reference d origine ( 5917fa8 + patch_faim ).
Si d21_justice.py est dans le meme dossier ( le depot ; pas l arbre d origine, qui n a pas de justice ), une ligne dans
d21._incarcerer confie les mineurs a l heure de l arrestation. Idempotent.   python patch_orphelins.py chemin/d01_population.py"""
import os, sys
p = sys.argv[1]; s = open(p).read()
p21 = os.path.join(os.path.dirname(p), "d21_justice.py")
if "def confier_si_seuls(p, k):" in s:
    print("deja :", p); s = None


def sub(s, a, b, n=1):
    assert s.count(a) == n, (p, a[:80], s.count(a))
    return s.replace(a, b)


def d21():
    """La ligne du domaine 21 : a l arrestation, les mineurs du menage du detenu ( 30/09, chef de projet )."""
    if not os.path.exists(p21): return
    t = open(p21).read()
    if "POP.confier_si_seuls(" in t: print("deja :", p21); return
    L = '    p.noter("incarceration", habitant=hid, prison=pr.id, titre="provisoire" if titre == PROVISOIRE else "peine", fin=int(fin))\n'
    t = sub(t, L, L + "    POP.confier_si_seuls(p, int(tb.menage[hid]))            # ( 30/09, orphelins ) ses mineurs, dans le meme pas\n")
    open(p21, "w").write(t); print("corrige :", p21)


if s is None: d21(); sys.exit(0)


# 1. la fiche : l invariant
s = sub(s, "Aucun mineur vivant\n   dans un menage sans adulte vivant ;",
        "Aucun mineur present\n   le soir sans adulte present ( 30/09 ) ;")
# 2. l etat du domaine : les enfants confies le temps d une absence
s = sub(s, '"migrations", "placements", "vivants_depart")', '"migrations", "placements", "vivants_depart", "gardes")')
s = sub(s, "        self.vivants_depart = vivants_depart\n",
        "        self.vivants_depart = vivants_depart\n"
        "        self.gardes = {}                  # enfant -> son menage, le temps de l absence d un adulte ( 30/09 )\n")
# 3. l heritage : un menage dont les adultes qui restent sont tous absents confie ses mineurs AVANT le partage
s = sub(s, "    heritiers = _heritiers(p, d, h)\n    if restants:\n",
        "    heritiers = _heritiers(p, d, h)\n"
        "    if restants and not _adultes_presents(p, mg):          # ( 30/09 ) les adultes qui restent sont absents\n"
        "        _confier(p, d, mg, p.hasard(\"population_placement\"), garde=True)\n"
        "    if restants:\n")
# 4. le placement : l ordre de la parente, oncles et tantes compris ; un parent absent ne recueille pas
s = sub(s, '    """Un mineur sans adulte : l autre parent, un grand-parent, un frere ou une soeur majeur, sinon une famille\n'
           '    d accueil de son lieu. Jamais un enfant seul dans un menage vide."""\n',
        '    """Un mineur sans adulte : l autre parent, un grand-parent, un frere ou une soeur majeur, un oncle ou une tante,\n'
        '    presents ( 30/09, voir « les orphelins » ), sinon une famille d accueil de son lieu. Jamais un enfant seul."""\n')
s = sub(s, '            if s != x.id: candidats.append((w.habitants[s], "fratrie"))\n',
        '            if s != x.id: candidats.append((w.habitants[s], "fratrie"))\n'
        '    for i in parents:                          # ( 30/09 ) les autres enfants des grands-parents : 3e degre\n'
        '        for k in ("mere", "pere"):\n'
        '            g = int(col[k][i])\n'
        '            for o in (d.enfants_de.get(g, ()) if g >= 0 else ()):\n'
        '                if o not in parents and o != x.id: candidats.append((w.habitants[o], "oncle_tante"))\n')
s = sub(s, 'and not p.col("menage", "dissous")[c.menage.id]:\n',
        'and not p.col("menage", "dissous")[c.menage.id] \\\n'
        '                and _present(p, c.id):\n')
# 5. la famille d accueil a un adulte PRESENT ( en colonnes, et dans la version d origine gardee pour la porte )
s = sub(s, "and adultes_vivants(p, m)]", "and _adultes_presents(p, m)]", n=2)
A = "adulte = (tb.vivant[:n] == 1) & (mm >= 0) & ((p.jour"
if A in s: s = sub(s, A, "adulte = (tb.vivant[:n] == 1) & (mm >= 0) & ~_absents(tb, n) & ((p.jour")
# 5 bis. ( depot seulement ) le tirage de l accueil dans les numeros : une vue par menage candidat, a chaque placement,
# rendait l installation de la prison quadratique ( 100 000 habitants : ~3 ms par placement ). Meme tirage, meme menage.
if "    accueil = _accueil_colonnes(p, x)\n    if not accueil:" in s:
    s = sub(s, "    accueil = _accueil_colonnes(p, x)\n    if not accueil:", "    accueil = _accueil_ids(p, x)\n    if not len(accueil):")
    s = sub(s, "    m = accueil[int(rng.integers(0, len(accueil)))]\n",
            "    m = P.Menage(int(accueil[int(rng.integers(0, len(accueil)))]), w.table.menages)\n")
    s = sub(s, "def _accueil_colonnes(p, x):\n", "def _accueil_ids(p, x):\n")
    s = sub(s, "    return [P.Menage(int(k), mt) for k in ids.tolist()]\n",
            "    return ids\n\n\n"
            "def _accueil_colonnes(p, x):\n"
            '    """Les memes, en menages : la liste que compare la porte d identite du placement. `_placer` tire dans les\n'
            '    numeros ( 30/09 ) : une vue par menage candidat a chaque placement coutait ~3 ms a 100 000 habitants."""\n'
            "    return [P.Menage(int(k), p.w.table.menages) for k in _accueil_ids(p, x).tolist()]\n")
# 6. le balayage du soir et ses outils
BLOC = '''# ================================================================== les orphelins ( 30/09, session Classes )
# Un mineur n est jamais seul le soir. Le jour meme ou le dernier adulte PRESENT de son menage disparait - la mort
# ( `_heriter` ), la prison ( domaine 21 : le detenu reste membre de son menage, ABSENT ), le voyage de l archipel, tout
# autre chemin - il rejoint un autre menage. Le droit grec : a la mort, a l absence declaree ou a la decheance d un
# parent, la garde revient a l autre parent ; s il est empeche de fait, l autre l exerce seul ( AK 1510 ). Sans parent
# qui puisse l exercer, le mineur est mis sous tutelle ( AK 1589 ) ; le tribunal nomme de preference l un de ses plus
# proches parents ( AK 1592 ), apres les avoir entendus avec le service social ( AK 1593 ) ; la proximite se compte en
# generations ( AK 1463 : grands-parents, freres et soeurs au 2e degre, oncles et tantes au 3e ). Sans personne qui
# convienne, la tutelle va a un etablissement ou au service social ( AK 1600 ; en Grece, l EKKA et les centres de
# protection de l enfance ). Les chemins recenses le 30/09 : la mort ( deja ici ) ; la prison ( a l heure de
# l arrestation : `confier_si_seuls`, appele par le domaine 21 ) ; le voyage de l archipel ( balayage du soir, filet de
# tous les chemins ) ; l emigration, les unions, les divorces, le recensement ne laissent jamais un mineur seul
# ( `_peut_partir` ici et au domaine 7 ) ; la conscription ( domaine 25 ) et l hopital ( domaine 17 ) laissent l appele
# et le malade membres PRESENTS de leur menage : aucun menage sans adulte.
# CHOIX ( sans source, a trancher par Younes ) :
#  1. dans le 2e degre, les grands-parents avant les freres et soeurs majeurs ( la loi laisse le choix au tribunal ;
#     les grands-parents sont la parente qui recueille le plus souvent, a verifier ) ; dans un rang, la lignee de la
#     mere d abord, puis l ordre des numeros ;
#  2. qui recueille doit etre PRESENT ( un detenu, un voyageur ne recueille pas ) ; ni sa caisse ni sa faim ne sont
#     examinees ( le tribunal le ferait : AK 1593 ) ;
#  3. le foyer d accueil reste la famille tiree au hasard ( flux population_placement ) parmi les menages de son lieu qui
#     ont un adulte present ; un etablissement public ( foyer de l EKKA ) demanderait un budget au domaine 6 ;
#  4. une absence ( prison, voyage ) confie l enfant pour son temps : il rentre chez lui le soir ou un adulte y est de
#     nouveau present ( garde par la parente ). L absent garde la caisse du menage ; l enfant emporte sa part des vivres
#     ( `deplacer_membre` ) et la rapporte ; ce qu il herite pendant la garde reste au menage qui l a recueilli ( un
#     mineur n a pas de patrimoine propre dans le monde : l argent est au menage ) ; l allocation A21 le suit, elle
#     compte les membres le jour du versement. Rien n est paye a qui recueille.
def _absents(tb, n):
    """Les ABSENTS ( detenu du domaine 21, voyageur de l archipel ) parmi les n premiers habitants ; un moteur sans
    colonne statut n en a aucun."""
    st = getattr(tb, "statut", None)
    return st[:n] == P.ABSENT if st is not None else np.zeros(n, bool)


def _present(p, i):
    st = getattr(p.w.table, "statut", None)
    return st is None or st[i] != P.ABSENT


def _adultes_presents(p, mg):
    return [x for x in adultes_vivants(p, mg) if _present(p, x.id)]


def menages_sans_adulte(p):
    """L invariant des orphelins, EN COLONNES : les numeros des menages habites ( au moins un membre present ) sans aucun
    adulte present. Present : vivant, dans la liste de son menage, pas ABSENT."""
    tb = p.w.table; n = tb.n; M = tb.menages.n
    mm = P.menages_inscrits(tb, n)
    ici = (tb.vivant[:n] == 1) & (mm >= 0) & ~_absents(tb, n)
    majeur = (p.jour - p.col("habitant", "naissance_j")[:n].astype(np.int64)) >= AGE_MAJEUR * 365
    habite = np.bincount(mm[ici], minlength=M)[:M] > 0
    avec = np.bincount(mm[ici & majeur], minlength=M)[:M] > 0
    return np.nonzero(habite & ~avec)[0]


def _gardes(d):
    g = getattr(d, "gardes", None)            # un instantane d avant le 30/09 n a pas ce champ
    if g is None: g = d.gardes = {}
    return g


def _confier(p, d, mg, rng, garde):
    """Les mineurs presents de `mg` rejoignent leur parente ou un foyer ( `_placer` ), dans l ordre de la liste ; `garde` :
    l absence est temporaire, l enfant rentrera ( `_rentrer` ). Rend ceux qui sont partis."""
    g = _gardes(d); partis = []
    for x in [x for x in mg.membres if x.vivant and _present(p, x.id) and age_de(p, x) < AGE_MAJEUR]:
        _placer(p, d, x, rng)
        if int(p.w.table.menage[x.id]) == mg.id: continue          # placement impossible
        partis.append(x)
        if garde: g.setdefault(x.id, mg.id)
    return partis


def confier_si_seuls(p, k):
    """A l heure ou un domaine rend ABSENT le dernier adulte present du menage k ( l arrestation, domaine 21 ) : ses
    mineurs presents sont confies dans le meme pas, comme le soir ( `_recueillir` ). Rien si un adulte reste present."""
    if k < 0: return
    mg = p.w.menages[k]
    if _adultes_presents(p, mg): return
    _confier(p, p.domaine("population"), mg, p.hasard("population_placement"), garde=bool(adultes_vivants(p, mg)))


def _rentrer(p, d):
    """L enfant confie rentre chez lui des qu un adulte y est de nouveau present ( sortie de prison, retour de voyage ).
    La garde finit aussi a sa majorite, a sa mort, ou quand son menage est dissous."""
    g = _gardes(d)
    if not g: return
    w = p.w; dis = p.col("menage", "dissous")
    for e in sorted(g):
        m = g[e]; x = w.habitants[e]
        if not x.vivant or age_de(p, x) >= AGE_MAJEUR or dis[m]:
            del g[e]; continue
        mg = w.menages[m]
        if not _adultes_presents(p, mg): continue
        if int(w.table.menage[e]) != m:
            deplacer_membre(p, x, mg)
            p.noter("placement", enfant=e, menage=m, lien="retour")
        del g[e]


def _recueillir(p):
    """23 h 50, apres la reprise des morts : les retours, puis tout mineur present d un menage sans adulte present est
    confie le jour meme. Un menage dont un adulte vit encore ( absent ) le garde, et sa caisse ; un menage de mineurs
    seuls ( aucun chemin connu n en laisse ) les suit : sa caisse part avec eux, par tete. EN COLONNES : trois bincount
    par soir, Python ne voit que les menages trouves ; aucun tirage un soir sans orphelin."""
    d = p.domaine("population"); w = p.w
    _rentrer(p, d)
    k = menages_sans_adulte(p)
    if not len(k): return
    rng = p.hasard("population_placement")
    for m in k.tolist():
        mg = w.menages[m]
        proprietaire = bool(adultes_vivants(p, mg))
        partis = _confier(p, d, mg, rng, garde=proprietaire)
        if proprietaire or not partis or any(x.vivant for x in mg.membres): continue
        q = mg.caisse / len(partis)
        for x in partis: p.socle.livre.transferer(mg, x.menage, q, "mise_en_commun")
        _dissoudre_si_vide(p, mg)


def _reprendre_les_morts(p):'''
s = sub(s, "def _reprendre_les_morts(p):", BLOC)
s = sub(s, '    p.routine(23 + 50 / 60, 90, "population", _reprendre_les_morts)\n',
        '    p.routine(23 + 50 / 60, 90, "population", _reprendre_les_morts)\n'
        '    p.routine(23 + 50 / 60, 91, "population", _recueillir)              # ( 30/09 ) aucun mineur seul le soir\n')
# 7. la porte des familles : un mineur seul, c est un mineur PRESENT sans adulte PRESENT
s = sub(s, "        v = [x for x in m.membres if x.vivant]\n", "        v = [x for x in m.membres if x.vivant and _present(p, x.id)]\n")
open(p, "w").write(s); print("corrige :", p)
d21()
