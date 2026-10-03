"""03/10 ( HMT-198, chantier A1 d Arma a fond ) : LE TIR INDIRECT des mortiers de 81 mm au domaine 27. Les mortiers
sont au domaine 25 ( arme collective des sections d appui, deux par section, 60 obus de dotation de combat chacun ) mais
restaient hors du duel ( ARMES_LOURDES : leurs servants se battaient a l arme de poing ). Une mission de COMBAT dont
l unite a des mortiers tire desormais, a chaque sous-pas, sur l element adverse CONNU du camp ( domaine 26 : la demande
de tir de l observateur ) le plus proche, a sa position crue, dans la portee du mortier ; chaque obus tombe dans la
dispersion ( incertitude de la connaissance et dispersion du tir ) et touche les hommes dans son rayon d effet selon
leur exposition ( posture, couvert, mouvement : celle du tir direct ). Chaque coup sort de l armurerie de la base
( obus_81, tir_combat, par _payer_tirs ). Interrupteur TIR_INDIRECT ; une unite sans mortier, une mission d exercice et
une unite qui rompt ne tirent pas. Idempotent.
   python patch_tir_indirect.py racine_de_l_arbre"""
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


FONCTIONS = '''

def _mortiers_mission(p, m, u, ids):
    """( 03/10, HMT-198 A1 ) Les mortiers de l unite u ( ses sections d appui, a sa base ) et leurs servants dans la
    mission ( les hommes de specialite MORTIER au domaine 25 : le mortier est une arme collective, ses servants gardent
    leur fusil ). None s il n y en a pas."""
    a = A._dom(p); U = a.unites; K = a.coll; im = A.IDX_ARME["mortier_81"]
    tubes = []
    for k in range(K.n):
        if int(K["oid"][k]) < 0 or int(K["modele"][k]) != im: continue
        x = int(K["unite"][k])
        while x >= 0 and x != int(u): x = int(U["parent"][x])
        if x == int(u): tubes.append(k)
    if not tubes: return None
    r = A._rangs(p, ids)
    serv = [v for v, rr in enumerate(r.tolist()) if int(a.eff["spec"][rr]) == A.MORTIER]   # les servants ( specialite )
    if not serv: return None
    return {"tubes": tubes, "servants": serv, "base": m.base_lid, "tires": 0.0,
            "dotation": float(A.DOTATION_COMBAT.get("mortier_81", 0)) * len(tubes)}


def _tir_indirect(p, m, debout, rng, dt):
    """( 03/10, HMT-198 A1 ) Le tir des mortiers de la mission pendant un sous-pas ( voir la fiche du correctif ). Rend
    les obus tires."""
    M = getattr(m, "mortiers", None)
    if not TIR_INDIRECT or not M or m.mode != "combat" or m.rupture: return 0
    h = m.h
    serv = [v for v in M["servants"] if h["actif"][v] == 1]
    tubes = min(len(M["tubes"]), len(serv) // SERVANTS_PAR_TUBE)
    if tubes <= 0: return 0
    e0 = m.elts[int(h["elt"][serv[0]])]; x0, y0 = e0.x, e0.y
    cal = A.NOMS_MUNITIONS.index("obus_81"); cle = (M["base"], cal)
    stock = float(A.armurerie(p, M["base"]).stock[A._dom(p).bids["obus_81"]]) - m.tirs.get(cle, 0.0) - _dom(p).reserve.get(cle, 0.0)
    cibles = []
    for j, t in enumerate(m.elts):
        if t.side != 1 or not len(_actifs(m, j)): continue
        c = _connaissance(p, S.CAMP_NATIONAL, t.ent)
        if c is None or c["age_h"] * 60.0 > AGE_MAX_TIR_MIN: continue          # une connaissance FRAICHE ( l observateur )
        dd = math.hypot(c["x"] - x0, c["y"] - y0)
        if PORTEE_MIN_MORTIER <= dd <= A.ARME["mortier_81"].portee_m: cibles.append((dd, j, c))
    if not cibles: return 0
    dd, j, c = min(cibles, key=lambda x: (x[0], x[1]))
    n = int(math.floor(CADENCE_MORTIER_CPM * dt / 60.0 * tubes + rng.random()))
    n = int(min(n, max(0.0, math.floor(stock)), max(0.0, M["dotation"] - M["tires"])))
    if n <= 0: return 0
    t = m.elts[j]; act = _actifs(m, j)
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
    m.tirs[cle] = m.tirs.get(cle, 0.0) + n; M["tires"] += n
    t.feu_recu += n / dt
    p.compter("coups_tires", float(n))
    return n


def _impact(p, m, v, zone, arme_tireur):
'''

remplacer("monde/pays/d27_armee_tactique.py", [
    ("""MORAL_ADVERSE = 0.5
""", """MORAL_ADVERSE = 0.5
# ( 03/10, HMT-198 A1 ) LE TIR INDIRECT des mortiers de 81 mm ( arme collective du domaine 25 ) : cadence soutenue 16 coups
# par minute et par tube, 33 au plus ( M252 : GlobalSecurity, Wikipedia ) - CHOIX : la soutenue ; portee 80 m a la portee
# du domaine 25 ( 5 650 m ) ; rayon d effet 35 m ( « effective kill radius » des obus M821 et M889, Wikipedia ) ;
# dispersion CEP = 1,9 % de la distance ( CHOIX par analogie : 136 m a la portee maximale d un obus de 120 mm sans conduite
# de tir moderne, euro-sd, 2020 ) ; touche dans le rayon avec la chance P_ECLAT x ( 1 - ( r / R )^2 ) x la posture
# ( couche x F_COUCHE_ECLAT ) x le couvert ( dur x F_DUR_ECLAT ; la vegetation n arrete pas un eclat ) - CHOIX, a mesurer
# dans Arma ( B_Mortar_01_F ) ; on ne tire que sur une connaissance FRAICHE ( AGE_MAX_TIR_MIN : l observateur suit la
# cible ; 03/10, une sonde a montre qu une salve sur une position perimee ne touchait rien ) ; deux servants par tube au
# moins ( CHOIX ; cinq au M252 ).
TIR_INDIRECT = True
CADENCE_MORTIER_CPM = 16.0
PORTEE_MIN_MORTIER = 80.0
RAYON_ECLAT_M = 35.0
CEP_PART_PORTEE = 0.019
P_ECLAT = 0.5
SERVANTS_PAR_TUBE = 2
F_COUCHE_ECLAT = 0.3
F_DUR_ECLAT = 0.1
AGE_MAX_TIR_MIN = 2.0
"""),
    ('''                 "lesions_adverses")''', '''                 "lesions_adverses", "mortiers")'''),
    ("""        self.lesions_adverses = []                     # ( 03/10, HMT-197 4b ) ( homme, zone, arme, AIS, arretee )
""", """        self.lesions_adverses = []                     # ( 03/10, HMT-197 4b ) ( homme, zone, arme, AIS, arretee )
        self.mortiers = None                           # ( 03/10, HMT-198 A1 ) les mortiers de l unite et leurs servants
"""),
    ("""    m.h = h
    m.cibles = [e.ent for e in m.elts if e.side == 1]
""", """    m.h = h
    m.cibles = [e.ent for e in m.elts if e.side == 1]
    if mode == "combat" and TIR_INDIRECT: m.mortiers = _mortiers_mission(p, m, u, ids)     # ( HMT-198 A1 )
"""),
    ("""    # les impacts : chacun sur un homme actif de l element cible, au prorata de son exposition
""", """    _tir_indirect(p, m, debout, rng, dt)                       # ( 03/10, HMT-198 A1 ) les mortiers
    # les impacts : chacun sur un homme actif de l element cible, au prorata de son exposition
"""),
    ("""

def _impact(p, m, v, zone, arme_tireur):
""", FONCTIONS),
])
