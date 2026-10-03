"""03/10 ( HMT-198, chantier A1-bis d Arma a fond ) : LES MORTIERS DE L ADVERSAIRE au domaine 27. Le tir indirect
( patch_tir_indirect.py, qu il suppose ) ne servait que notre camp. Une mission peut maintenant porter les mortiers de
l adversaire ( m.mortiers_adverses : ses servants parmi les hommes rouges, ses tubes, les obus qu il a apportes - pose par
guerre/expedition quand l ile attaquante emporte ses sections d appui ). Ils tirent a chaque sous-pas sur l element de
notre camp que LEUR camp connait ( domaine 26 : ce que leurs hommes ont vu ), connaissance fraiche, dans la portee, avec
les memes lois que les notres ( cadence, dispersion, rayon, eclats ) ; nos blesses suivent le chemin ordinaire
( _impact, tri, evacuation ). Les obus sont ceux que l adversaire a apportes : ils ne sortent d aucune armurerie de ce
monde ( son ile les paie a son retour ). Idempotent.
   python patch_mortiers_adverses.py racine_de_l_arbre"""
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


FONCTION = '''

def _tir_indirect_adverse(p, m, debout, rng, dt):
    """( 03/10, HMT-198 A1-bis ) Le tir des mortiers de l adversaire ( m.mortiers_adverses ) sur notre element que son
    camp connait. Rend les obus tires."""
    M = getattr(m, "mortiers_adverses", None)
    if not TIR_INDIRECT or not M or m.mode != "combat": return 0
    h = m.h
    serv = [v for v in M["servants"] if h["actif"][v] == 1]
    tubes = min(int(M["tubes"]), len(serv) // SERVANTS_PAR_TUBE)
    if tubes <= 0 or M["obus"] - M["tires"] < 1: return 0
    e0 = m.elts[int(h["elt"][serv[0]])]; x0, y0 = e0.x, e0.y
    cibles = []
    for j, t in enumerate(m.elts):
        if t.side != 0 or not len(_actifs(m, j)) or t.ent < 0: continue
        c = _connaissance(p, e0.camp, t.ent)
        if c is None or c["age_h"] * 60.0 > AGE_MAX_TIR_MIN: continue
        dd = math.hypot(c["x"] - x0, c["y"] - y0)
        if PORTEE_MIN_MORTIER <= dd <= A.ARME["mortier_81"].portee_m: cibles.append((dd, j, c))
    if not cibles: return 0
    dd, j, c = min(cibles, key=lambda x: (x[0], x[1]))
    n = int(math.floor(CADENCE_MORTIER_CPM * dt / 60.0 * tubes + rng.random()))
    n = int(min(n, math.floor(M["obus"] - M["tires"])))
    if n <= 0: return 0
    t = m.elts[j]
    sig = math.sqrt(float(c["sigma_m"]) ** 2 + (CEP_PART_PORTEE * dd / 1.1774) ** 2)
    cz = np.cumsum(P_ZONE_EXPOSE)
    for _ in range(n):
        act = _actifs(m, j)
        if not len(act): break
        ix, iy = float(c["x"]) + rng.normal(0.0, sig), float(c["y"]) + rng.normal(0.0, sig)
        r = np.hypot(t.x + h["dx"][act] - ix, t.y + h["dy"][act] - iy)
        f_eclat = (debout[act] + (1.0 - debout[act]) * F_COUCHE_ECLAT) * (F_DUR_ECLAT if t.couvert == 2 else 1.0)
        pr = P_ECLAT * np.clip(1.0 - (r / RAYON_ECLAT_M) ** 2, 0.0, 1.0) * f_eclat
        for v in act[rng.random(len(act)) < pr].tolist():
            if h["actif"][v] != 1: continue
            z = ZONES[min(4, int(np.searchsorted(cz, rng.random())))]
            _impact(p, m, int(v), z, A.IDX_ARME["mortier_81"])
    M["tires"] += n
    t.feu_recu += n / dt
    return n


def _impact(p, m, v, zone, arme_tireur):
'''

remplacer("monde/pays/d27_armee_tactique.py", [
    ('''                 "lesions_adverses", "mortiers")''', '''                 "lesions_adverses", "mortiers", "mortiers_adverses")'''),
    ("""        self.mortiers = None                           # ( 03/10, HMT-198 A1 ) les mortiers de l unite et leurs servants
""", """        self.mortiers = None                           # ( 03/10, HMT-198 A1 ) les mortiers de l unite et leurs servants
        self.mortiers_adverses = None                  # ( 03/10, HMT-198 A1-bis ) ceux de l adversaire ( guerre/expedition )
"""),
    ("""    _tir_indirect(p, m, debout, rng, dt)                       # ( 03/10, HMT-198 A1 ) les mortiers
""", """    _tir_indirect(p, m, debout, rng, dt)                       # ( 03/10, HMT-198 A1 ) les mortiers
    _tir_indirect_adverse(p, m, debout, rng, dt)               # ( 03/10, HMT-198 A1-bis ) ceux de l adversaire
"""),
    ("""

def _impact(p, m, v, zone, arme_tireur):
""", FONCTION),
])
