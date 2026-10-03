"""03/10 ( HMT-198, chantier A2 d Arma a fond ) : LES BLINDES AU COMBAT du domaine 27. Les vehicules du domaine 25 ne
servaient qu aux patrouilles et aux convois ; une unite qui se DEFEND ( la tactique « defense » ) se bat maintenant avec
ses blindes qui sont a sa base et en service : le M113A1 de chaque groupe et le M1114 de chaque section ( une M2HB de
12,7 mm ), le Leopard 2A6HEL ( deux MG3 ). Le Parc et les munitions sont ceux du domaine 25. Idempotent.

  L EQUIPAGE  les hommes de l unite du vehicule ( le groupe pour un M113 ), conducteur et equipage d abord, puis
              fusiliers, autant que le vehicule en demande ( d25 : M113 2, M1114 2, Leopard 4 ) ; sinon le vehicule reste
              au parc. Ils passent a l element d appui ( CHOIX : les blindes font la base de feu de la defense ) ; leurs
              armes individuelles restent a l armurerie ( leur reserve est rendue ).
  LES ARMES   le tireur sert l arme de bord avec les munitions du vehicule ( d25 : 2 000 coups de 12,7 pour un M113,
              4 750 de 7,62 pour un Leopard, partages entre ses deux MG3 ), au plus ce que l armurerie a hors reserves ;
              elles sortent du grand livre comme tout tir de combat. M2HB : portee 1 500 m sur cible ponctuelle, 40 coups
              par minute en tir soutenu ( FM 3-22.65 ), M33 de 42,9 g a 887 m/s ( ~ 16 900 J ), menace perforante ; MG3
              de bord : 1 200 m sur affut ( d25 ). La portee utile suit la regle du domaine 25 ( le minimum de l arme et
              de sa visee ) : la M2HB du M113A1 et du M1114 n a que son fer ( 300 m ), la MG3 coaxiale du Leopard vise
              par le viseur du tireur ( 1 200 m ), celle du chargeur au fer. CHOIX : le canon de 120 mm ne tire pas sur des fantassins ( l armee n a
              au catalogue que l obus-fleche DM63, sans explosif ).
  LA CAISSE   un vehicule intact arrete balles d arme de poing et de fusil et eclats ( STANAG 4569 niveau 1 : 7,62 x 51
              et 5,56 a 30 m, eclats d artillerie ) ; la balle perforante ( 12,7 ) passe un blindage de niveau 1 ou 2, pas
              celui d un char ( CHOIX ) ; l equipage n est expose qu a travers la caisse ( F_CAISSE : le couvert dur ).
  L ANTICHAR  un tireur qui porte des roquettes de 84 mm ( m.h[ at ] : guerre/expedition les donne aux tireurs antichar
              de l ile attaquante ) tire une roquette par sous-pas de 30 s ( CHOIX ; 4 a 6 coups par minute au mieux,
              Saab ) sur le blinde adverse le plus proche que son camp connait, a l arret, jusqu a 1,25 fois sa portee
              ( 700 m sur cible fixe, 400 m mobile, Saab ). Touche : 0,9 a 100 m, 0,5 a la portee, 0 a 1,25 fois ( CHOIX,
              a mesurer dans Arma ) x sa competence x sa suppression x ( 1 / 1,75 s il ne voit pas ). Detruit si touche :
              0,7 pour un vehicule de niveau 3 au plus ( la charge creuse FFV551 perce plus de 400 mm d acier ; l
              aluminium du M113 en fait ~ 40 ), 0,12 pour un char ( l arc frontal du 2A6 resiste ; flancs et arriere ) -
              CHOIX. Chaque homme de l equipage est touche avec la chance 0,6 ( CHOIX ) ; les munitions de bord sont
              perdues ( perte_au_combat ) ; le vehicule sort du Parc ( detruit ) a la cloture.
Les exercices ( tir simule ) n emmenent pas de blindes : ils restent identiques au bit. BLINDES = False rend le domaine
d avant ( porte A2, B5 ).
   python patch_blindes.py racine_de_l_arbre"""
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


CONSTANTES = '''AGE_MAX_TIR_MIN = 2.0
# ( 03/10, HMT-198 A2 ) LES BLINDES AU COMBAT : voir la fiche de references/correctifs/patch_blindes.py ( sources et CHOIX ).
BLINDES = True
TACTIQUES_BLINDEES = ("defense",)
BORD0 = 100                                       # les armes de bord : indices BORD0 + k dans h[ arme ]
ARMES_BORD = (("m2hb", "mun_127", 1500.0, 40.0 / 60.0, 16900.0, "perforant"),
              ("mg3_bord", "mun_762", 1200.0, CADENCE_APPUI_BPS["mg3"], 3200.0, "fusil"))
ARME_BORD = {x[0]: x for x in ARMES_BORD}
IDX_BORD = {x[0]: BORD0 + k for k, x in enumerate(ARMES_BORD)}
CADENCE_APPUI_BPS.update({x[0]: x[3] for x in ARMES_BORD})
# ( arme de bord, visee ) : la portee utile est celle du domaine 25, le minimum de l arme et de sa visee ; la M2HB du M113A1
# et du M1114 n a que son fer, la MG3 coaxiale du Leopard vise par le viseur du tireur ( EMES 15 ), celle du chargeur au fer
ARMES_DE_VEHICULE = {"m113a1": (("m2hb", "fer"),), "m1114": (("m2hb", "fer"),),
                     "leopard_2a6hel": (("mg3_bord", "visee_char"), ("mg3_bord", "fer"))}
PREF_EQUIPAGE = {A.CONDUCTEUR: 0, A.EQUIPAGE: 0, A.FUSILIER: 1}
F_CAISSE = 0.05                                   # l equipage sous la caisse : le couvert dur ( F_COUVERT )
PORTEE_AT_FIXE, PORTEE_AT_MOBILE = 700.0, 400.0
D_AT_PRES, P_AT_PRES, P_AT_PORTEE = 100.0, 0.9, 0.5
P_DETRUIT_TOUCHE_LEGER, P_DETRUIT_TOUCHE_CHAR = 0.7, 0.12
P_EQUIPAGE_TOUCHE = 0.6
'''

FONCTIONS = '''

def _nom_arme(k):
    """( HMT-198 A2 ) Le nom de l arme d indice k : du domaine 25, ou de bord ( k >= BORD0 )."""
    return ARMES_BORD[k - BORD0][0] if k >= BORD0 else A.ARMES[k].nom


def _menace_energie(arme):
    """( HMT-198 A2 ) ( menace, energie a la bouche ) d une arme du domaine 25 ou de bord."""
    if arme in ARME_BORD: return ARME_BORD[arme][5], ARME_BORD[arme][4]
    a = A.ARME[arme]
    return a.menace, a.energie_j


def _arrete_par_caisse(arme, blindage):
    """( HMT-198 A2 ) La caisse d un vehicule intact arrete-t-elle ce projectile ( la roquette se juge a part ) ?"""
    if arme == "carl_gustaf_m3": return False
    return blindage >= (3 if _menace_energie(arme)[0] == "perforant" else 1)


def blesser_soldat(p, hid, zone, arme):
    """( HMT-198 A2 ) d25.blesser_soldat, et la meme loi pour une arme de bord ( la M2HB n est pas au domaine 25 )."""
    if arme in A.ARME: return A.blesser_soldat(p, hid, zone, arme)
    if not p.a("medecine"): return None, 0
    men, ej = _menace_energie(arme)
    mult = A.multiplicateur_letalite(p, hid, zone, men)
    ais = A.AIS_CONTUSION if mult <= A.SEUIL_ARRET else MED.ais_balistique(zone, ej)
    iss = MED.iss_depuis_ais({zone: ais})
    return MED.blesser(p, PO.Habitant(p.w.table, hid), "balistique", iss, "combat"), iss


def _sous_unite(U, x, u):
    while x >= 0 and x != u: x = int(U["parent"][x])
    return x == u


def _vehicules_mission(p, m, u, ids, roles, h, reserve):
    """( HMT-198 A2 ) Les blindes de l unite u qui se bat ( a sa base, en service, armes ), leurs equipages pris dans
    ids, passes a l appui ( roles ), et les munitions de bord reservees. Rend [ vehicule ]."""
    a = A._dom(p); U = a.unites; V = a.veh; E = a.eff
    if not len(ids): return []
    b = int(U["base"][u]) if int(U["base"][u]) >= 0 else int(E["base"][A._rangs(p, [m.chef])[0]])
    rg = A._rangs(p, ids); unite_h = E["unite"][rg]; spec_h = E["spec"][rg]; base_h = E["base"][rg]
    cands = []
    for k in range(V.n):
        if int(V["oid"][k]) < 0 or int(V["etat"][k]) != A.O.SERVICE or int(V["base"][k]) != b: continue
        if A.VEHICULES[int(V["modele"][k])].nom not in ARMES_DE_VEHICULE: continue
        x = int(V["unite"][k])
        if _sous_unite(U, x, int(u)): cands.append((-int(U["niveau"][x]), k))
    libres = set(range(len(ids))); out = []
    for _, k in sorted(cands):
        c = A.VEHICULES[int(V["modele"][k])]; x = int(V["unite"][k])
        pool = sorted((i for i in libres if int(spec_h[i]) in PREF_EQUIPAGE and int(base_h[i]) == b
                       and _sous_unite(U, int(unite_h[i]), x)), key=lambda i: (PREF_EQUIPAGE[int(spec_h[i])], i))
        if len(pool) < c.equipage: continue
        crew = pool[:c.equipage]; libres -= set(crew)
        out.append({"oid": int(V["oid"][k]), "modele": c.nom, "blindage": int(c.blindage), "equipage": crew,
                    "tireurs": [], "intact": True, "arretes": 0, "touches_at": 0, "perdus": 0.0})
    lid = m.base_lid
    for vi, vh in enumerate(out):
        guns = ARMES_DE_VEHICULE[vh["modele"]]; arm_v = A.VEHICULE[vh["modele"]].armement
        for j, i in enumerate(vh["equipage"]):
            if h["cal"][i] >= 0 and h["coups"][i] > 0:              # son arme individuelle reste a l armurerie
                key = (p.w.carte.par_n[int(h["base"][i])].id, int(h["cal"][i]))
                reserve[key] = max(0.0, reserve.get(key, 0.0) - float(h["coups"][i]))
            h["veh"][i] = vi; roles[i] = ROLES.index("appui")
            h["arme"][i] = -1; h["cal"][i] = -1; h["coups"][i] = 0.0
            if j >= len(guns): continue
            g = ARME_BORD[guns[j][0]]; cal = A.NOMS_MUNITIONS.index(g[1])
            dot = float(arm_v.get(g[1], 0.0)) / sum(1 for x, _ in guns if ARME_BORD[x][1] == g[1])
            stock = float(A.armurerie(p, lid).stock[a.bids[g[1]]])
            q = float(math.floor(max(0.0, min(dot, stock - reserve.get((lid, cal), 0.0)))))
            h["arme"][i] = IDX_BORD[guns[j][0]]; h["cal"][i] = cal; h["coups"][i] = q
            h["portee"][i] = g[2] if guns[j][1] == "visee_char" else min(g[2], A.OPTIQUE[guns[j][1]].portee_m)
            reserve[(lid, cal)] = reserve.get((lid, cal), 0.0) + q
            vh["tireurs"].append(int(i))
    if out: p.compter("blindes_engages", float(len(out)))
    return out


def _abriter(m, expo, debout):
    """( HMT-198 A2 ) L equipage d un vehicule intact ne s expose qu a travers la caisse."""
    for vh in m.vehicules:
        if not vh["intact"]: continue
        for i in vh["equipage"]: expo[i] *= F_CAISSE; debout[i] = 0.0


def _p_toucher_at(d, portee, tir):
    return float(np.interp(d, [D_AT_PRES, portee, 1.25 * portee], [P_AT_PRES, P_AT_PORTEE, 0.0])) * float(f_tir(tir))


def _tir_antichar(p, m, rng, dt, par, bouge):
    """( HMT-198 A2 ) Les roquettes de 84 mm sur les blindes ( voir la fiche du correctif ). Rend les roquettes tirees."""
    vehs = getattr(m, "vehicules", None)
    if not BLINDES or m.mode != "combat" or not vehs or "at" not in m.h: return 0
    h = m.h; n = 0
    for v in np.nonzero((h["at"] >= 1) & (h["actif"] == 1))[0].tolist():
        i = int(h["elt"][v]); e = m.elts[i]; c = e.cond
        if c is None or c.feu == "aucun" or (c.feu in ("tenu", "riposte") and not m.compromis[e.side]): continue
        if bouge[i] and (c.mode in ("simultane", "infiltration") or (c.mode in ("bond", "repli") and int(h["moitie"][v]) == par)):
            continue                                         # il marche, ou c est sa moitie qui court
        x0, y0 = e.x + h["dx"][v], e.y + h["dy"][v]
        cibles = []
        for vi, vh in enumerate(vehs):
            if not vh["intact"]: continue
            i0 = vh["equipage"][0]; j = int(h["elt"][i0]); t = m.elts[j]
            if t.side == e.side or _connaissance(p, e.camp, t.ent) is None: continue
            portee = PORTEE_AT_MOBILE if bouge[j] else PORTEE_AT_FIXE
            dd = math.hypot(t.x + h["dx"][i0] - x0, t.y + h["dy"][i0] - y0)
            if dd <= 1.25 * portee: cibles.append((dd, vi, j, portee))
        if not cibles: continue
        dd, vi, j, portee = min(cibles)
        pt = _p_toucher_at(dd, portee, h["tir"][v]) * (1.0 - e.supp * (1.0 - SUPP_PRECISION)) * (1.0 if j in e.vu else F_NON_VU)
        h["at"][v] -= 1.0; n += 1; e.fait_feu = True; m.roquettes[e.side] += 1
        if rng.random() >= min(0.95, pt): continue
        vh = vehs[vi]; vh["touches_at"] += 1
        if rng.random() >= (P_DETRUIT_TOUCHE_LEGER if vh["blindage"] <= 3 else P_DETRUIT_TOUCHE_CHAR): continue
        _detruire_vehicule(p, m, vh, rng)
    if n: p.compter("roquettes_tirees", float(n))
    return n


def _detruire_vehicule(p, m, vh, rng):
    """( HMT-198 A2 ) Le vehicule est detruit : son equipage touche ( 0,6 chacun ), ses munitions de bord perdues."""
    h = m.h; d = _dom(p)
    vh["intact"] = False; p.compter("blinde_detruit")
    cz = np.cumsum(P_ZONE_ABRITE)
    for i in vh["equipage"]:
        if h["actif"][i] == 1 and rng.random() < P_EQUIPAGE_TOUCHE:
            _impact(p, m, int(i), ZONES[min(4, int(np.searchsorted(cz, rng.random())))], A.IDX_ARME["carl_gustaf_m3"])
    for i in vh["tireurs"]:
        q = float(h["coups"][i])
        if h["cal"][i] >= 0 and q > 0 and int(h["side"][i]) == 0 and h["hid"][i] >= 0:
            lid = p.w.carte.par_n[int(h["base"][i])].id; c = int(h["cal"][i]); bien = A.NOMS_MUNITIONS[c]
            s = A.tirer(p, lid, bien, q, "perte_au_combat")
            d.reserve[(lid, c)] = max(0.0, d.reserve.get((lid, c), 0.0) - q)
            d.tirs[(lid, bien + ":perte")] = d.tirs.get((lid, bien + ":perte"), 0.0) + q
            d.tirs_sortis[(lid, bien + ":perte")] = d.tirs_sortis.get((lid, bien + ":perte"), 0.0) + s
            vh["perdus"] += q
        h["coups"][i] = 0.0; h["arme"][i] = -1; h["cal"][i] = -1


def _perdre_vehicules(p, m):
    """( HMT-198 A2 ) A la cloture : les vehicules detruits sortent du Parc ( d25.perdre_objet )."""
    for vh in m.vehicules:
        if vh["intact"] or vh.get("sorti"): continue
        vh["sorti"] = True
        if vh["oid"] in p.socle.parc.objets: A.perdre_objet(p, vh["oid"], "detruit"); p.compter("blinde_perdu")


def _impact(p, m, v, zone, arme_tireur):
'''

remplacer("monde/pays/d27_armee_tactique.py", [
    ("AGE_MAX_TIR_MIN = 2.0\n", CONSTANTES),
    ('''                 ("viole", np.int8, 0))''',
     '''                 ("viole", np.int8, 0), ("veh", np.int16, -1), ("at", np.float64, 0.0))    # ( HMT-198 A2 )'''),
    ('''                 "lesions_adverses", "mortiers", "mortiers_adverses")''',
     '''                 "lesions_adverses", "mortiers", "mortiers_adverses", "vehicules", "roquettes")'''),
    ("""        self.mortiers_adverses = None                  # ( 03/10, HMT-198 A1-bis ) ceux de l adversaire ( guerre/expedition )
""", """        self.mortiers_adverses = None                  # ( 03/10, HMT-198 A1-bis ) ceux de l adversaire ( guerre/expedition )
        self.vehicules = []                            # ( 03/10, HMT-198 A2 ) nos blindes engages
        self.roquettes = [0, 0]                        # ( 03/10, HMT-198 A2 ) roquettes antichar tirees par camp
"""),
    ("""    a = A.ARME[arme]
    m = 1.0
    for k in (prot, casque):
        if k >= 0 and zone in A.PROTECTIONS[k].zones: m *= A.PROTECTIONS[k].mult[a.menace]
    if m <= A.SEUIL_ARRET: return A.AIS_CONTUSION, True
    return MED.ais_balistique(zone, a.energie_j if a.energie_j > 0 else 3000.0), False
""", """    men, ej = _menace_energie(arme)                    # ( HMT-198 A2 ) une arme de bord aussi
    m = 1.0
    for k in (prot, casque):
        if k >= 0 and zone in A.PROTECTIONS[k].zones: m *= A.PROTECTIONS[k].mult[men]
    if m <= A.SEUIL_ARRET: return A.AIS_CONTUSION, True
    return MED.ais_balistique(zone, ej if ej > 0 else 3000.0), False
"""),
    ("""    h = _hommes_bleus(p, ids, roles, exo, d.reserve)
""", """    h = _hommes_bleus(p, ids, roles, exo, d.reserve)
    if mode == "combat" and BLINDES and t.nom in TACTIQUES_BLINDEES:              # ( HMT-198 A2 ) les blindes
        m.vehicules = _vehicules_mission(p, m, u, ids, roles, h, d.reserve)
"""),
    ("""        expo[sel] = ex; debout[sel] = up
    # le feu
""", """        expo[sel] = ex; debout[sel] = up
    if getattr(m, "vehicules", None): _abriter(m, expo, debout)     # ( HMT-198 A2 ) l equipage sous la caisse
    # le feu
"""),
    ("""            cad = np.array([CADENCE_APPUI_BPS.get(A.ARMES[k].nom, CADENCE_APPUI_FUSIL_BPS) if k >= 0 else 0.0""",
     """            cad = np.array([CADENCE_APPUI_BPS.get(_nom_arme(k), CADENCE_APPUI_FUSIL_BPS) if k >= 0 else 0.0"""),
    ("""    _tir_indirect_adverse(p, m, debout, rng, dt)               # ( 03/10, HMT-198 A1-bis ) ceux de l adversaire
""", """    _tir_indirect_adverse(p, m, debout, rng, dt)               # ( 03/10, HMT-198 A1-bis ) ceux de l adversaire
    _tir_antichar(p, m, rng, dt, par, bouge)                   # ( 03/10, HMT-198 A2 ) les roquettes sur les blindes
"""),
    ("""

def _impact(p, m, v, zone, arme_tireur):
""", FONCTIONS),
    ("""    h = m.h
    arme = A.ARMES[arme_tireur].nom if arme_tireur >= 0 else ARME_ADVERSE
    ais, arrete = lesion(zone, arme, int(h["prot"][v]), int(h["casque"][v]))
""", """    h = m.h
    arme = _nom_arme(arme_tireur) if arme_tireur >= 0 else ARME_ADVERSE
    vk = int(h["veh"][v]) if "veh" in h else -1                     # ( HMT-198 A2 ) sous la caisse d un blinde intact
    if vk >= 0 and m.vehicules[vk]["intact"] and _arrete_par_caisse(arme, m.vehicules[vk]["blindage"]):
        sd = int(h["side"][v]); m.n_impacts[sd] += 1; m.n_arretes[sd] += 1; m.vehicules[vk]["arretes"] += 1
        p.compter("impact"); return
    ais, arrete = lesion(zone, arme, int(h["prot"][v]), int(h["casque"][v]))
"""),
    ("""            A.blesser_soldat(p, hid, zone, arme); d.contusions.append(""",
     """            blesser_soldat(p, hid, zone, arme); d.contusions.append("""),
    ("""        if iss >= 75:
            A.blesser_soldat(p, hid, zone, arme)
""", """        if iss >= 75:
            blesser_soldat(p, hid, zone, arme)                      # ( HMT-198 A2 ) une arme de bord aussi
"""),
    ("""        ev = S.evacuer(p, hid, lieu=lieu)
        A.blesser_soldat(p, hid, zone, arme)
""", """        ev = S.evacuer(p, hid, lieu=lieu)
        blesser_soldat(p, hid, zone, arme)
"""),
    ("""              "rupture", "decision_exfiltration", "qualification_tactique", "note_exercice", "repli_impossible"):
""", """              "rupture", "decision_exfiltration", "qualification_tactique", "note_exercice", "repli_impossible",
              "blindes_engages", "roquettes_tirees", "blinde_detruit", "blinde_perdu"):     # ( HMT-198 A2 )
"""),
    ("""    if m.mode == "combat" and m.rupture: _perdre_materiel(p, m)
""", """    if m.mode == "combat" and m.rupture: _perdre_materiel(p, m)
    if m.mode == "combat" and getattr(m, "vehicules", None): _perdre_vehicules(p, m)     # ( HMT-198 A2 )
"""),
])
