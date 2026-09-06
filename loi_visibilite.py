#!/usr/bin/env python3
"""P(toucher | fraction de corps visible), MESUREE sur Arma 3. Criteres : CRITERES_LOI_VISIBILITE.md

Duels simultanes, tireur ET cible invulnerables, sessions courtes repetees.
On compte les COUPS TIRES (le denominateur qui manquait) et les IMPACTS, par case de visibilite.
⚠️ SQF sans commentaires (call compile ne retire pas les //) et sans champ vide (nombres seuls).
"""
import sys, re, json, math, time, collections
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
SESSIONS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
NDUELS = int(sys.argv[3]) if len(sys.argv) > 3 else 12
DUREE = 60
DIST = 100
SORTIE = "/home/younes/arma3-marl/loi_visibilite.json"

b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert (compteur %d)" % (PORT, b.counter))

FRAC = ('private _frac = { params ["_a", "_c"]; private _o = eyePos _a; '
        'private _pi = getPosASL _c; private _oe = eyePos _c; private _n = 0; '
        '{ private _k = _x; private _pt = [(_pi select 0) + _k * ((_oe select 0) - (_pi select 0)), '
        '(_pi select 1) + _k * ((_oe select 1) - (_pi select 1)), '
        '(_pi select 2) + _k * ((_oe select 2) - (_pi select 2))]; '
        'if (([objNull, "VIEW"] checkVisibility [_o, _pt]) > 0.5) then { _n = _n + 1 }; '
        '} forEach [0.15, 0.4, 0.65, 0.9, 1]; _n / 5 }; ')

SESSION = (
 '[] spawn { HMT_TIRS = 0; HMT_IMP = 0; HMT_BRUT = 0; ' + FRAC +
 'HMT_FRAC = _frac; '
 'private _duels = []; private _duels_murs = []; '
 'for "_j" from 0 to __ND__ do { '
 '  private _p = [16000,16000,0]; '
 '  for "_i" from 0 to 60 do { _p = [] call BIS_fnc_randomPos; '
 '    if ((getTerrainHeightASL _p) > 5) exitWith {} }; '
 '  private _az = random 360; '
 '  private _q = [(_p select 0) + __D__ * sin _az, (_p select 1) + __D__ * cos _az, 0]; '
 '  private _g1 = createGroup west; private _g2 = createGroup east; '
 '  private _s = _g1 createUnit ["B_Soldier_F", _p, [], 0, "NONE"]; '
 '  private _c = _g2 createUnit ["O_Soldier_F", _q, [], 0, "NONE"]; '
 '  _s allowDamage false; _c allowDamage false; '
 '  _s setSkill 0.5; _c setSkill 0.5; _s allowFleeing 0; _c allowFleeing 0; '
 '  _s setUnitPos "UP"; _s disableAI "PATH"; _s disableAI "AUTOTARGET"; '
 '  _c disableAI "PATH"; _c disableAI "AUTOTARGET"; _c disableAI "TARGET"; '
 '  _c setBehaviour "CARELESS"; '
 '  private _cas = _j % 4; '
 '  if (_cas > 0) then { '
 '    private _mp = [(_q select 0) + 2 * sin (_az + 180), (_q select 1) + 2 * cos (_az + 180), 0]; '
 '    private _mur = createVehicle ["Land_BagFence_Long_F", _mp, [], 0, "CAN_COLLIDE"]; '
 '    _mur setDir (_az + 90); _duels_murs pushBack _mur; }; '
 '  if (_cas == 0) then { _c setUnitPos "UP" }; '
 '  if (_cas == 1) then { _c setUnitPos "UP" }; '
 '  if (_cas == 2) then { _c setUnitPos "MIDDLE" }; '
 '  if (_cas == 3) then { _c setUnitPos "DOWN" }; '
 '  _s setVariable ["hd", _j]; _c setVariable ["hd", _j]; _c setVariable ["hs", _s]; '
 '  _s addEventHandler ["Fired", { params ["_u"]; '
 '    HMT_BRUT = HMT_BRUT + 1; '
 '    private _t = _u getVariable ["hc", objNull]; if (isNull _t) exitWith {}; '
 '    private _f = [_u, _t] call HMT_FRAC; HMT_TIRS = HMT_TIRS + 1; '
 '    format ["HMTF %1 %2", (_u getVariable ["hd", -1]), _f] call HMT_EMIT; }]; '
 '  _c addEventHandler ["HitPart", { private _e = (_this select 0); '
 '    private _v = _e select 0; private _sh = _e select 1; '
 '    if (!isNull _v && {!isNull _sh} && {_v != _sh}) then { HMT_IMP = HMT_IMP + 1; '
 '    format ["HMTI %1", (_v getVariable ["hd", -1])] call HMT_EMIT; }; }]; '
 '  _s setVariable ["hc", _c]; '
 '  _duels pushBack [_s, _c, _g1, _g2]; '
 '}; '
 'sleep 3; '
 '{ (_x select 0) reveal [(_x select 1), 4]; (_x select 0) setBehaviour "COMBAT"; '
 '  (_x select 0) setCombatMode "RED"; (_x select 0) doTarget (_x select 1); } forEach _duels; '
 'private _t0 = time; '
 'while { time - _t0 < __T__ } do { '
 '  { (_x select 0) doTarget (_x select 1); (_x select 0) doFire (_x select 1); } forEach _duels; '
 '  sleep 3; }; '
 'format ["HMTSESS %1 %2 %3 %4", HMT_TIRS, HMT_IMP, count _duels, HMT_BRUT] call HMT_EMIT; '
 '{ deleteVehicle (_x select 0); deleteVehicle (_x select 1); } forEach _duels; '
 '{ deleteVehicle _x } forEach _duels_murs; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__ND__", str(NDUELS - 1)).replace("__D__", str(DIST)).replace("__T__", str(DUREE))

tirs, imps = [], []
for k in range(SESSIONS):
    n0 = len(b._log_lines(200000))
    r = b.query(SESSION, r"HMTSESS (\d+) (\d+) (\d+) (\d+)", want=1, timeout=DUREE + 120)
    if not r:
        print("  session %d : PAS DE FIN — on s arrete" % k); break
    nt, ni, nd, nb = (int(r[0].group(i)) for i in (1, 2, 3, 4))
    for s in b._log_lines(200000)[n0:]:
        m = re.match(r"HMTF (-?\d+) ([-0-9.eE+]+)", s.strip())
        if m: tirs.append((int(m.group(1)), float(m.group(2))))
        m = re.match(r"HMTI (-?\d+)$", s.strip())
        if m: imps.append(int(m.group(1)))
    print("  session %d : %d duels · %d coups BRUTS · %d coups mesures · %d impacts"
          % (k, nd, nb, nt, ni))
    if nb > 0 and nt == 0:
        print("    ⛔ ils tirent mais la sonde de fraction echoue — instrument, pas monde")

print("\n  " + "=" * 66)
if len(tirs) < 200:
    print("  ⛔ %d coups tires (< 200 requis) — ON NE CONCLUT PAS." % len(tirs))
    json.dump({"tirs": tirs, "imps": imps}, open(SORTIE, "w")); sys.exit(1)

# fraction MOYENNE par duel (le duel est la condition ; la cible ne bouge pas)
par_duel_f = collections.defaultdict(list)
for d, f in tirs: par_duel_f[d].append(f)
n_tirs = collections.Counter(d for d, _ in tirs)
n_imps = collections.Counter(imps)
CASES = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.01)]
print("  %d coups tires · %d impacts · %d duels" % (len(tirs), len(imps), len(n_tirs)))
print("\n  case de visibilite      coups   impacts   P(toucher)")
pts = []
for lo, hi in CASES:
    ds = [d for d in n_tirs if lo <= (sum(par_duel_f[d]) / len(par_duel_f[d])) < hi]
    t = sum(n_tirs[d] for d in ds); i = sum(n_imps.get(d, 0) for d in ds)
    if t:
        p = i / t
        fm = sum(sum(par_duel_f[d]) / len(par_duel_f[d]) for d in ds) / len(ds)
        print("  [%.1f ; %.1f[            %5d    %5d     %.3f" % (lo, hi, t, i, p))
        pts.append((fm, p, t))
    else:
        print("  [%.1f ; %.1f[            %5d        -        -" % (lo, hi, t))

peuplees = [q for q in pts if q[2] >= 30]
print("\n  cases peuplees (>= 30 coups) : %d  (3 requis)" % len(peuplees))
plein = [q for q in pts if q[0] > 0.8]
print("  CONTROLE POSITIF — case pleinement visible a %d m : %s (bande certifiee 0,15-0,50)"
      % (DIST, ("%.3f" % plein[0][1]) if plein else "ABSENTE"))
ok = bool(plein) and 0.15 <= plein[0][1] <= 0.50 and len(peuplees) >= 3
if not ok:
    print("  ⛔ le banc ne remplit pas ses conditions — AUCUN EXPOSANT N EST LU.")
else:
    xs = [(math.log(f), math.log(p)) for f, p, _ in peuplees if f > 0 and p > 0]
    n = len(xs); mx = sum(x for x, _ in xs) / n; my = sum(y for _, y in xs) / n
    num = sum((x - mx) * (y - my) for x, y in xs); den = sum((x - mx) ** 2 for x, _ in xs)
    a = num / den if den else float("nan")
    print("  ⭐ EXPOSANT MESURE : a = %.2f   (RV1 postulait 2)" % a)
    print("     %s" % ("RV1 tient, `visible**2` devient MESURE"
                       if 1.5 <= a <= 2.5 else "RV1 ne tient pas : on remplace par %.2f" % a))
json.dump({"tirs": tirs, "imps": imps, "dist": DIST}, open(SORTIE, "w"))
print("  ecrit : %s" % SORTIE)
b.sock.close()
