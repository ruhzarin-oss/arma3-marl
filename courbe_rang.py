#!/usr/bin/env python3
"""La courbe est-elle un MELANGE ? Test du rang sur cible INVULNERABLE.
Criteres : CRITERES_MELANGE.md, ecrits avant les chiffres.
⚠️ SQF sans commentaires, nombres seuls, jamais de formatage `%` sur du SQF."""
import sys, re, json, math, os, collections
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
BLOCS = int(sys.argv[2]) if len(sys.argv) > 2 else 14
NDUEL, DUREE = 54, 20
SORTIE = "/home/younes/arma3-marl/courbe_rang1_10_v2.json"
DIST_L = [25, 50, 75, 100, 150, 200]
POST_L = ["UP", "MIDDLE", "DOWN"]
COND = [(d, p) for p in POST_L for d in DIST_L for _ in range(3)]   # 3 duels par condition
RANG_MAX = 10
b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert (compteur %d)" % (PORT, b.counter), flush=True)

SESSION = ('[] spawn { HMT_T = 0; HMT_I = 0; private _duels = []; '
 'for "_j" from 0 to __NM1__ do { '
 '  private _p = [16000,16000,0]; '
 '  for "_i" from 0 to 60 do { _p = [] call BIS_fnc_randomPos; '
 '    if ((getTerrainHeightASL _p) > 5) exitWith {} }; '
 '  private _dd = (__DL__) select _j; private _po = (__PL__) select _j; '
 '  private _az = random 360; '
 '  private _q = [(_p select 0) + _dd * sin _az, (_p select 1) + _dd * cos _az, 0]; '
 '  private _g1 = createGroup west; private _g2 = createGroup east; '
 '  private _s = _g1 createUnit ["B_Soldier_F", _p, [], 0, "NONE"]; '
 '  private _c = _g2 createUnit ["O_Soldier_F", _q, [], 0, "NONE"]; '
 '  _s allowDamage false; _c allowDamage false; '
 '  _s setSkill 0.5; _c setSkill 0.5; _s allowFleeing 0; _c allowFleeing 0; '
 '  _s setUnitPos "UP"; _s disableAI "PATH"; _s disableAI "AUTOTARGET"; '
 '  _c setUnitPos _po; _c disableAI "PATH"; _c disableAI "AUTOTARGET"; '
 '  _c disableAI "TARGET"; _c setBehaviour "CARELESS"; '
 '  _s setVariable ["hd", _j]; _c setVariable ["hd", _j]; _c setVariable ["hs", _s]; '
 '  _s setVariable ["hr", 0]; '
 '  _s addEventHandler ["Fired", { params ["_u"]; '
 '    private _r = (_u getVariable ["hr", 0]) + 1; _u setVariable ["hr", _r]; HMT_T = HMT_T + 1; '
 '    format ["MXF %1 %2", (_u getVariable ["hd", -1]), _r] call HMT_EMIT; }]; '
 '  _c addEventHandler ["HitPart", { private _e = (_this select 0); '
 '    private _v = _e select 0; private _sh = _e select 1; private _pr = _e select 2; '
 '    if (isNull _v or isNull _sh) exitWith {}; '
 '    if (_sh != (_v getVariable ["hs", objNull])) exitWith {}; '
 '    if (_pr isEqualTo (_v getVariable ["hp", objNull])) exitWith {}; '
 '    _v setVariable ["hp", _pr]; HMT_I = HMT_I + 1; '
 '    format ["MXI %1 %2", (_v getVariable ["hd", -1]), (_sh getVariable ["hr", 0])] call HMT_EMIT; }]; '
 '  _duels pushBack [_s, _c]; '
 '}; '
 'sleep 3; '
 '{ (_x select 0) reveal [(_x select 1), 4]; (_x select 0) setBehaviour "COMBAT"; '
 '  (_x select 0) setCombatMode "RED"; } forEach _duels; '
 'private _t0 = time; '
 'while { time - _t0 < __T__ } do { '
 '  { (_x select 0) doTarget (_x select 1); (_x select 0) doFire (_x select 1); } forEach _duels; '
 '  sleep 3; }; '
 'format ["MXEND %1 %2 %3", HMT_T, HMT_I, count _duels] call HMT_EMIT; '
 '{ deleteVehicle (_x select 0); deleteVehicle (_x select 1); } forEach _duels; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__NM1__", str(NDUEL - 1)).replace("__T__", str(DUREE)).replace("__DL__", "[" + ",".join(str(d) for d, _ in COND) + "]").replace("__PL__", "[" + ",".join(chr(34) + p + chr(34) for _, p in COND) + "]")

# (bloc, duel) identifie un duel UNIQUE : les objets sont recrees a chaque bloc
tirs, imps = [], []
if os.path.exists(SORTIE):
    _p = json.load(open(SORTIE))
    tirs = [tuple(x) for x in _p["tirs"]]; imps = [tuple(x) for x in _p["imps"]]
    print("  reprise : %d balles deja acquises" % len(tirs), flush=True)
depart = max([t[0] for t in tirs], default=-1) + 1

for k in range(BLOCS):
    n0 = len(b._log_lines(400000))
    try:
        r = b.query(SESSION, r"MXEND (\d+) (\d+) (\d+)", want=1, timeout=DUREE + 120)
    except Exception:
        print("  bloc %d : pont perdu, bloc jete" % k, flush=True)
        try: b = NativeBridge(port=PORT, timeout=20)
        except Exception: break
        continue
    if not r:
        print("  bloc %d : pas de fin" % k, flush=True); continue
    nt, ni, nd = (int(r[0].group(i)) for i in (1, 2, 3))
    bid = depart + k
    for s in b._log_lines(400000)[n0:]:
        m = re.match(r"MXF (-?\d+) (\d+)$", s.strip())
        if m: tirs.append((bid, int(m.group(1)), int(m.group(2))))
        m = re.match(r"MXI (-?\d+) (\d+)$", s.strip())
        if m: imps.append((bid, int(m.group(1)), int(m.group(2))))
    print("  bloc %d/%d : %d balles · %d impacts (cumul %d)" % (k + 1, BLOCS, nt, ni, len(tirs)), flush=True)
    json.dump({"tirs": tirs, "imps": imps}, open(SORTIE, "w"))

def wil(i, n):
    if n == 0: return (float("nan"),) * 3
    p = i / n; z = 1.96; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)

T = collections.Counter(); I = collections.Counter()
for _, j, r in tirs:
    if r <= RANG_MAX: T[COND[j]] += 1
for _, j, r in imps:
    if r <= RANG_MAX: I[COND[j]] += 1
j100 = COND.index((100, "UP"))
p, lo, hi = wil(I[(100, "UP")], T[(100, "UP")])
print("\n  " + "=" * 68)
print("  CONTROLE — 100 m debout, rangs 1-%d : %.3f [%.3f ; %.3f] n=%d" % (RANG_MAX, p, lo, hi, T[(100, "UP")]))
print("  bande ecrite d avance [0,30 ; 0,41] : %s"
      % ("OK" if 0.30 <= p <= 0.41 else "HORS BANDE — instrument deplace, rien n est lu"))
print("\n  dist      debout            accroupi           couche   (rangs 1-%d)" % RANG_MAX)
for d in DIST_L:
    ligne = "  %4d m " % d
    for po in POST_L:
        n = T[(d, po)]; i = I[(d, po)]
        ligne += ("   %.3f(n=%4d)" % (i / n, n)) if n >= 300 else ("   %5s(n=%4d)" % ("-", n))
    print(ligne)
json.dump({"cond": [list(c) for c in COND], "tirs": [list(x) for x in tirs],
           "imps": [list(x) for x in imps], "rang_max": RANG_MAX}, open(SORTIE, "w"))
print("\n  ecrit : %s" % SORTIE)
b.sock.close()
