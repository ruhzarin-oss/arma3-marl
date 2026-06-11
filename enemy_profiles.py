"""enemy_profiles — PROFILS DE DÉFENSE partagés (mesure run_maneuver + visuel run_op_visual).
Né en visuel (07/06, demande Younes « IA hardcore ») puis promu en MESURE pour le harnais v4 :
la v3 a prouvé que sans la nage, la défense `normal` est triviale (plafond 93-100 %) — la difficulté
doit venir de la DÉFENSE (compétence + agressivité + nombre), pas de la géographie.
- mult/qrf_mult : effectifs (mêmes positions/rayons -> la géométrie de défense est conservée)
- pro : sous-compétences montées + boucle de CHASSE (un groupe qui acquiert un contact convertit
  sa patrouille en seek-and-destroy — l'ennemi statique qui attend la mort, c'est fini)."""

ENEMY_PROFILES = {
    "normal":    dict(mult=1.0, qrf_mult=1.0, pro=False),                # 28, skills base, pas de chasse -> 93% (plafond)
    "skilled":   dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=False),     # 28, SKILLS montés, PAS de chasse = candidat frontière (borne FACILE)
    "skilled_hunt": dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=True),   # 28, skills + chasse mais effectif NORMAL (isole la chasse vs les corps) = borne DURE
    "skilled_qrf": dict(mult=1.0, qrf_mult=2.5, pro=True, hunt=False),   # 28 garnison skilled + QRF MASSIVE = caractère différent (favorise vitesse de prise vs méthode) [étape 2 multi-situations]
    "skilled_react": dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=False, react=True),  # 28 skilled, défense COORDONNÉE : les patrouilles se massent sur le flanc menacé (contre l'enveloppement). Test « ennemi intelligent » 10/06
    "skilled_react_depth": dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=False, react_depth=True),  # 28 skilled, défense anti-FRONTALE : bloc central avancé quand l'attaque est frontale (punit M1), laisse les flancs (récompense M3). 2e axe matrice 10/06
    "mid_skill": dict(mult=1.25, qrf_mult=1.25, pro=False),              # 35 (sonde: PLAFOND -> effectif ≠ levier)
    "mid_bodies":dict(mult=1.5, qrf_mult=1.5, pro=False),                # 42 corps sans skills/chasse
    "pro":       dict(mult=1.5, qrf_mult=1.5, pro=True, hunt=True),      # 42, skills + chasse -> 6% (plancher)
    "hardcore":  dict(mult=2.2, qrf_mult=2.0, pro=True),    # 44 + QRF 16 = 60
    "nightmare": dict(mult=3.0, qrf_mult=3.0, pro=True),    # 60 + QRF 24 = 84
}

PRO_SKILL_SQF = (
    '{ _x setSkill ["aimingAccuracy", 0.75]; _x setSkill ["aimingSpeed", 0.9];'
    ' _x setSkill ["aimingShake", 0.9]; _x setSkill ["spotDistance", 0.95];'
    ' _x setSkill ["spotTime", 0.9]; _x setSkill ["courage", 1]; _x setSkill ["commanding", 1];'
    ' _x setSkill ["general", 1]; } forEach HMT_EN;\n')

HUNT_SQF = (
    'HMT_HUNT = true;\n'
    '[] spawn {\n'
    '  while {HMT_HUNT} do {\n'
    '    {\n'
    '      private _g = _x;\n'
    '      private _best = objNull; private _bk = 1.5;\n'
    '      { private _k = _g knowsAbout _x; if (_k > _bk) then { _bk = _k; _best = _x; }; }\n'
    '        forEach (allUnits select { side _x == west && {alive _x} && {!isPlayer _x} });\n'
    '      if (!isNull _best && {({alive _x} count units _g) > 0}) then {\n'
    '        while {count waypoints _g > 0} do { deleteWaypoint [_g, 0] };\n'
    '        private _wp = _g addWaypoint [getPos _best, 30];\n'
    '        _wp setWaypointType "SAD"; _wp setWaypointSpeed "FULL"; _g setBehaviour "COMBAT";\n'
    '      };\n'
    '    } forEach (allGroups select { side _x == east });\n'
    '    sleep 30;\n'
    '  };\n'
    '};\n')


REACTIVE_DEF_SQF = (
    'HMT_REACT = true;\n'
    '[] spawn {\n'
    '  sleep 6;\n'
    '  private _obj = [15000,16000,0];\n'
    '  private _eg = allGroups select { side _x == east };\n'
    '  private _core = objNull; private _cd = 1e9;\n'
    '  { private _d = (leader _x) distance2D _obj; if (_d < _cd) then { _cd = _d; _core = _x }; } forEach _eg;\n'
    '  private _patrols = _eg - [_core];\n'        # le noyau tient l'objectif (QRF/métrique) ; les patrouilles manoeuvrent
    '  while {HMT_REACT} do {\n'
    '    private _wW = 0; private _wE = 0;\n'
    '    {\n'
    '      private _u = _x; private _k = 0;\n'
    '      { private _kk = _x knowsAbout _u; if (_kk > _k) then { _k = _kk }; } forEach _eg;\n'
    '      if (_k > 1.0) then {\n'                 # contact suffisamment connu
    '        if (((getPosATL _u) select 0) < 15000) then { _wW = _wW + 1 } else { _wE = _wE + 1 };\n'
    '      };\n'
    '    } forEach (allUnits select { side _x == west && {alive _x} && {!isPlayer _x} });\n'
    '    if (_wW + _wE > 0) then {\n'
    '      private _rally = [14860,16000,0];\n'
    '      if (_wE > _wW) then { _rally = [15140,16000,0] };\n'   # se masser sur le flanc le plus menacé
    '      {\n'
    '        if (({alive _x} count units _x) > 0) then {\n'
    '          while {count waypoints _x > 0} do { deleteWaypoint [_x, 0] };\n'
    '          private _wp = _x addWaypoint [_rally, 20];\n'
    '          _wp setWaypointType "MOVE"; _wp setWaypointSpeed "FULL";\n'   # TENIR le flanc, pas charger : MOVE+hold (sinon la réserve épingle l\'infiltration -> standoff infini)
    '          _wp setWaypointBehaviour "COMBAT"; _wp setWaypointCombatMode "YELLOW";\n'
    '          _x setBehaviour "COMBAT"; _x setCombatMode "YELLOW";\n'
    '        };\n'
    '      } forEach _patrols;\n'
    '    };\n'
    '    sleep 15;\n'
    '  };\n'
    '};\n')


REACTIVE_DEPTH_SQF = (
    'HMT_REACT = true;\n'
    '[] spawn {\n'
    '  sleep 6;\n'
    '  private _obj = [15000,16000,0];\n'
    '  private _eg = allGroups select { side _x == east };\n'
    '  private _core = objNull; private _cd = 1e9;\n'
    '  { private _d = (leader _x) distance2D _obj; if (_d < _cd) then { _cd = _d; _core = _x }; } forEach _eg;\n'
    '  private _patrols = _eg - [_core];\n'
    '  while {HMT_REACT} do {\n'
    '    private _ctr = 0; private _lat = 0;\n'
    '    {\n'
    '      private _u = _x; private _k = 0;\n'
    '      { private _kk = _x knowsAbout _u; if (_kk > _k) then { _k = _kk }; } forEach _eg;\n'
    '      if (_k > 1.0) then {\n'
    '        if ((abs (((getPosATL _u) select 0) - 15000)) < 80) then { _ctr = _ctr + 1 } else { _lat = _lat + 1 };\n'   # contact CENTRAL vs LATÉRAL
    '      };\n'
    '    } forEach (allUnits select { side _x == west && {alive _x} && {!isPlayer _x} });\n'
    '    if (_ctr > _lat && {_ctr > 0}) then {\n'          # attaque FRONTALE -> bloc central avancé sur l'axe d'assaut ; sinon on NE commet PAS (flanc laissé à l'enveloppement)
    '      private _rally = [15000,15920,0];\n'
    '      {\n'
    '        if (({alive _x} count units _x) > 0) then {\n'
    '          while {count waypoints _x > 0} do { deleteWaypoint [_x, 0] };\n'
    '          private _wp = _x addWaypoint [_rally, 20];\n'
    '          _wp setWaypointType "MOVE"; _wp setWaypointSpeed "FULL";\n'
    '          _wp setWaypointBehaviour "COMBAT"; _wp setWaypointCombatMode "YELLOW";\n'
    '          _x setBehaviour "COMBAT"; _x setCombatMode "YELLOW";\n'
    '        };\n'
    '      } forEach _patrols;\n'
    '    };\n'
    '    sleep 15;\n'
    '  };\n'
    '};\n')


def scaled_garrison(garrison, mult):
    """Effectifs xmult, géométrie conservée."""
    return [(x, y, max(1, round(n * mult)), rad) for (x, y, n, rad) in garrison]


def apply_profile(env, profile, garrison):
    """Prépare l'env pour un profil : renvoie la garnison échelonnée + enrobe spawn_qrf/_mech.
    À appeler AVANT env.spawn ; envoyer pro_sqf() APRÈS env.spawn si profile['pro']."""
    p = ENEMY_PROFILES[profile] if isinstance(profile, str) else profile
    g = scaled_garrison(garrison, p["mult"])
    if p["qrf_mult"] != 1.0:
        _oq, _oqm = env.spawn_qrf, env.spawn_qrf_mech
        env.spawn_qrf = lambda x, y, n, t: _oq(x, y, max(1, round(n * p["qrf_mult"])), t)
        env.spawn_qrf_mech = lambda x, y, n, t: _oqm(x, y, max(1, round(n * p["qrf_mult"])), t)
    return g, p


def metrics_dyn(env, runner, garrison):
    """Métriques P-v3b avec effectifs DYNAMIQUES (les profils cassent les tranches fixes 12/8/8)."""
    eal = env.en_alive()
    gn = garrison[0][2]; pn = sum(g[2] for g in garrison[1:])
    garr_a = int(eal[0:gn].sum()); pat_a = int(eal[gn:gn + pn].sum()); qrf_a = int(eal[gn + pn:].sum())
    qrf_live = "qrf" in runner.qrf_done
    qrf_n = max(0, eal.size - gn - pn)
    alive_tot = sum(int(env.alive(si).sum()) for si in range(env.S))
    pertes = 1 - alive_tot / sum(env.sizes)
    eff_total = gn + pn + (qrf_n if qrf_live else 0)
    reste = garr_a + pat_a + qrf_a
    ennemi_brise = (garr_a == 0) and ((1 - reste / max(eff_total, 1)) >= 0.7)
    mil = bool(ennemi_brise and pertes <= 0.5)
    return {"mil": mil, "pertes": float(pertes), "garr_pris": bool(garr_a == 0),
            "qrf_spawn": bool(qrf_live), "qrf_reste": qrf_a, "ennemis_total": int(eff_total)}


# ============================================================================
# EXTENSION DEFENSIVE (10/06) — le miroir du repertoire d attaque (DOCTRINE-REPERTOIRE.md §B)
# Patron commun : le groupe le plus proche de l objectif = noyau (tient, QRF/metrique intacte) ;
# les autres groupes manoeuvrent. Lecons reprises de REACTIVE_DEF_SQF : MOVE+hold pour bloquer
# (jamais SAD pour un bloc, sinon standoff), SAD pour frapper, sleep 8-20 s par boucle.
# ============================================================================

# D3 — RESERVE MOBILE (strike force) : force de frappe au nord, CONTRE-ATTAQUE sur le centroide
# des contacts connus. Tueuse de concentration (percee/masse). Vulnerable a la feinte.
MOBILE_DEF_SQF = (
    'HMT_DEFMOB = true;\n'
    '[] spawn {\n'
    '  sleep 6;\n'
    '  private _obj = [15000,16000,0];\n'
    '  private _eg = allGroups select { side _x == east };\n'
    '  private _core = objNull; private _cd = 1e9;\n'
    '  { private _d = (leader _x) distance2D _obj; if (_d < _cd) then { _cd = _d; _core = _x }; } forEach _eg;\n'
    '  private _strike = _eg - [_core];\n'
    '  { while {count waypoints _x > 0} do { deleteWaypoint [_x,0] };\n'
    '    private _wp = _x addWaypoint [[15000,16180,0], 20]; _wp setWaypointType "MOVE"; _wp setWaypointSpeed "FULL";\n'
    '  } forEach _strike;\n'
    '  while {HMT_DEFMOB} do {\n'
    '    private _kx = 0; private _ky = 0; private _n = 0;\n'
    '    { private _u = _x; private _k = 0;\n'
    '      { private _kk = _x knowsAbout _u; if (_kk > _k) then { _k = _kk }; } forEach _eg;\n'
    '      if (_k > 1.2) then { _kx = _kx + ((getPosATL _u) select 0); _ky = _ky + ((getPosATL _u) select 1); _n = _n + 1; };\n'
    '    } forEach (allUnits select { side _x == west && {alive _x} && {!isPlayer _x} });\n'
    '    if (_n >= 3) then {\n'
    '      private _tgt = [_kx/_n, _ky/_n, 0];\n'
    '      { if (({alive _x} count units _x) > 0) then {\n'
    '          while {count waypoints _x > 0} do { deleteWaypoint [_x,0] };\n'
    '          private _wp = _x addWaypoint [_tgt, 25]; _wp setWaypointType "SAD"; _wp setWaypointSpeed "FULL";\n'
    '          _x setBehaviour "COMBAT"; _x setCombatMode "RED"; }; } forEach _strike;\n'
    '    };\n'
    '    sleep 20;\n'
    '  };\n'
    '};\n')

# D4 — DEFENSE ELASTIQUE : lignes successives (objectif -> 16150 -> 16270) ; on recule sous pression,
# l attaquant s etire. Contre-indication doctrinale : marteau-enclume (le repli meurt sur le bloc).
ELASTIC_DEF_SQF = (
    'HMT_ELAS = true;\n'
    '[] spawn {\n'
    '  sleep 6;\n'
    '  private _tot = {alive _x} count HMT_EN;\n'
    '  private _l2 = false; private _l3 = false;\n'
    '  while {HMT_ELAS} do {\n'
    '    private _al = {alive _x} count HMT_EN;\n'
    '    if (!_l2 && _al < _tot * 0.7) then { _l2 = true;\n'
    '      { if (((leader _x) distance2D [15000,16000,0]) < 160) then {\n'
    '          while {count waypoints _x > 0} do { deleteWaypoint [_x,0] };\n'
    '          private _wp = _x addWaypoint [[15000,16150,0], 25]; _wp setWaypointType "MOVE"; _wp setWaypointSpeed "FULL";\n'
    '          _wp setWaypointBehaviour "COMBAT"; }; } forEach (allGroups select { side _x == east }); };\n'
    '    if (!_l3 && _al < _tot * 0.4) then { _l3 = true;\n'
    '      { while {count waypoints _x > 0} do { deleteWaypoint [_x,0] };\n'
    '        private _wp = _x addWaypoint [[15010,16270,0], 25]; _wp setWaypointType "MOVE"; _wp setWaypointSpeed "FULL";\n'
    '      } forEach (allGroups select { side _x == east }); };\n'
    '    sleep 10;\n'
    '  };\n'
    '};\n')

# D5 — HERISSON (reduit) : TOUT le monde rentre au complexe, perimetre dense, pas d ecran.
# Tueuse d infiltration/raid/tournant (rien dehors a contourner). Vulnerable a l appui-feu + convergence.
HERISSON_DEF_SQF = (
    '[] spawn {\n'
    '  sleep 4;\n'
    '  { private _g = _x;\n'
    '    while {count waypoints _g > 0} do { deleteWaypoint [_g,0] };\n'
    '    private _wp = _g addWaypoint [[15000,16000,0], 15];\n'
    '    _wp setWaypointType "MOVE"; _wp setWaypointSpeed "FULL";\n'
    '    _g setBehaviour "COMBAT"; _g setCombatMode "RED";\n'
    '  } forEach (allGroups select { side _x == east });\n'
    '  sleep 30;\n'
    '  { _x setUnitPos "MIDDLE"; } forEach (allUnits select { side _x == east && {alive _x} });\n'
    '};\n')

# D6 — APPAT (retraite feinte) : la garnison ABANDONNE l objectif vers les surplombs nord ;
# quand >=3 attaquants occupent le complexe -> contre-assaut convergent (la nasse). Tueuse de raid/masse.
APPAT_DEF_SQF = (
    'HMT_APPAT = true;\n'
    '[] spawn {\n'
    '  sleep 6;\n'
    '  private _obj = [15000,16000,0];\n'
    '  private _eg = allGroups select { side _x == east };\n'
    '  private _out = false; private _fired = false;\n'
    '  while {HMT_APPAT && !_fired} do {\n'
    '    if (!_out) then {\n'
    '      private _seen = 0;\n'
    '      { private _u = _x; private _k = 0;\n'
    '        { private _kk = _x knowsAbout _u; if (_kk > _k) then { _k = _kk }; } forEach _eg;\n'
    '        if (_k > 1.0) then { _seen = _seen + 1; };\n'
    '      } forEach (allUnits select { side _x == west && {alive _x} && {!isPlayer _x} });\n'
    '      if (_seen >= 2) then { _out = true;\n'
    '        private _i = 0;\n'
    '        { while {count waypoints _x > 0} do { deleteWaypoint [_x,0] };\n'
    '          private _p = [[14870,16180,0],[15130,16200,0]] select (_i mod 2); _i = _i + 1;\n'
    '          private _wp = _x addWaypoint [_p, 20]; _wp setWaypointType "MOVE"; _wp setWaypointSpeed "FULL";\n'
    '          _wp setWaypointBehaviour "COMBAT"; _x setCombatMode "YELLOW";\n'
    '        } forEach _eg; };\n'
    '    } else {\n'
    '      private _in = { side _x == west && {alive _x} && {_x distance2D _obj < 70} } count allUnits;\n'
    '      if (_in >= 3) then { _fired = true;\n'
    '        { while {count waypoints _x > 0} do { deleteWaypoint [_x,0] };\n'
    '          private _wp = _x addWaypoint [_obj, 25]; _wp setWaypointType "SAD"; _wp setWaypointSpeed "FULL";\n'
    '          _x setBehaviour "COMBAT"; _x setCombatMode "RED";\n'
    '        } forEach _eg; };\n'
    '    };\n'
    '    sleep 10;\n'
    '  };\n'
    '};\n')

# D7 — SORTIE PREVENTIVE (spoiling attack) : au premier contact, les patrouilles ATTAQUENT les zones
# de rassemblement sud (crete d appui + base assaut). Tueuse de mises en place lentes. Le noyau tient.
SORTIE_DEF_SQF = (
    'HMT_SORTIE = true;\n'
    '[] spawn {\n'
    '  sleep 6;\n'
    '  private _eg = allGroups select { side _x == east };\n'
    '  private _core = objNull; private _cd = 1e9;\n'
    '  { private _d = (leader _x) distance2D [15000,16000,0]; if (_d < _cd) then { _cd = _d; _core = _x }; } forEach _eg;\n'
    '  private _raiders = _eg - [_core];\n'
    '  private _done = false;\n'
    '  while {HMT_SORTIE && !_done} do {\n'
    '    private _seen = 0;\n'
    '    { private _u = _x; private _k = 0;\n'
    '      { private _kk = _x knowsAbout _u; if (_kk > _k) then { _k = _kk }; } forEach _eg;\n'
    '      if (_k > 0.8) then { _seen = _seen + 1; };\n'
    '    } forEach (allUnits select { side _x == west && {alive _x} && {!isPlayer _x} });\n'
    '    if (_seen >= 1) then { _done = true;\n'
    '      private _i = 0;\n'
    '      { if (({alive _x} count units _x) > 0) then {\n'
    '          while {count waypoints _x > 0} do { deleteWaypoint [_x,0] };\n'
    '          private _p = [[14880,15860,0],[15120,15830,0]] select (_i mod 2); _i = _i + 1;\n'
    '          private _wp = _x addWaypoint [_p, 25]; _wp setWaypointType "SAD"; _wp setWaypointSpeed "FULL";\n'
    '          _x setBehaviour "COMBAT"; _x setCombatMode "RED"; }; } forEach _raiders; };\n'
    '    sleep 8;\n'
    '  };\n'
    '};\n')

DEFENSE_SQF = {"mobile": MOBILE_DEF_SQF, "elastic": ELASTIC_DEF_SQF, "herisson": HERISSON_DEF_SQF,
               "appat": APPAT_DEF_SQF, "sortie": SORTIE_DEF_SQF}

ENEMY_PROFILES.update({
    "skilled_mobile":   dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=False, def_sqf="mobile"),    # D3 reserve mobile
    "skilled_elastic":  dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=False, def_sqf="elastic"),   # D4 elastique
    "skilled_herisson": dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=False, def_sqf="herisson"),  # D5 herisson
    "skilled_appat":    dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=False, def_sqf="appat"),     # D6 appat
    "skilled_sortie":   dict(mult=1.0, qrf_mult=1.0, pro=True, hunt=False, def_sqf="sortie"),    # D7 sortie preventive
})
