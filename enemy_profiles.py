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
