#!/usr/bin/env python3
"""La courbe est-elle un MELANGE ? Test du rang sur cible INVULNERABLE.
Criteres : CRITERES_MELANGE.md, ecrits avant les chiffres.
⚠️ SQF sans commentaires, nombres seuls, jamais de formatage `%` sur du SQF."""
import sys, re, json, math, os, collections
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
BLOCS = int(sys.argv[2]) if len(sys.argv) > 2 else 14
NDUEL, DUREE, DIST = 18, 55, 100
SORTIE = "/home/younes/arma3-marl/test_melange.json"
b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert (compteur %d)" % (PORT, b.counter), flush=True)

SESSION = ('[] spawn { HMT_T = 0; HMT_I = 0; private _duels = []; '
 'for "_j" from 0 to __NM1__ do { '
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
 '  _c setUnitPos "UP"; _c disableAI "PATH"; _c disableAI "AUTOTARGET"; '
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
).replace("__NM1__", str(NDUEL - 1)).replace("__T__", str(DUREE)).replace("__D__", str(DIST))

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

print("\n  " + "=" * 68)
p, lo, hi = wil(len(imps), len(tirs))
print("  CONTROLE POSITIF — 100 m debout : %.3f [%.3f ; %.3f] n=%d" % (p, lo, hi, len(tirs)))
ok = not (hi < 0.335 or lo > 0.435)
print("  contre 0,402 [0,371;0,435] et 0,383 [0,335;0,434] : %s"
      % ("✔ l instrument n a pas bouge" if ok else "⛔ INSTRUMENT DEPLACE — rien n est lu"))
if not ok:
    sys.exit(1)

CASES = [(1, 10), (11, 30), (31, 80)]
print("\n  LECTURE 1 — ENTRE DUELS (celle qui a declenche la suspension)")
for lo_, hi_ in CASES:
    n = sum(1 for _, _, r in tirs if lo_ <= r <= hi_)
    i = sum(1 for _, _, r in imps if lo_ <= r <= hi_)
    pp, l, h = wil(i, n)
    print("    coups %3d-%-3d %6d balles  %s" % (lo_, hi_, n,
          ("%.3f [%.3f ; %.3f]" % (pp, l, h)) if n >= 100 else "n<100, non rendu"))

print("\n  LECTURE 2 — DANS LE DUEL (composition identique par construction)")
rmax = collections.defaultdict(int)
for d_, j, r in tirs: rmax[(d_, j)] = max(rmax[(d_, j)], r)
longs = {k for k, v in rmax.items() if v >= 31}
print("    duels atteignant le rang 31 : %d" % len(longs))
if len(longs) < 10:
    print("    ⛔ moins de 10 duels : le banc ne discrimine pas.")
    print("    LA SUSPENSION RESTE — un doute ne se resout pas en faveur de ce qu on veut.")
else:
    res = []
    for lo_, hi_ in [(1, 10), (31, 80)]:
        n = sum(1 for d_, j, r in tirs if (d_, j) in longs and lo_ <= r <= hi_)
        i = sum(1 for d_, j, r in imps if (d_, j) in longs and lo_ <= r <= hi_)
        pp, l, h = wil(i, n)
        res.append((n, pp, l, h))
        print("    coups %3d-%-3d %6d balles  %s" % (lo_, hi_, n,
              ("%.3f [%.3f ; %.3f]" % (pp, l, h)) if n >= 100 else "n<100, non rendu"))
    if min(res[0][0], res[1][0]) < 100:
        print("\n    ⛔ moins de 100 balles dans une case : LA SUSPENSION RESTE.")
    else:
        disj = (res[0][3] < res[1][2]) or (res[1][3] < res[0][2])
        print()
        if disj:
            print("  ⛔ LA DECROISSANCE PERSISTE DANS LE DUEL : elle est REELLE.")
            print("     La courbe EST un melange, elle ne se transporte pas. ÉQ. 1 reste SUSPENDU.")
        else:
            print("  ✔ LA DECROISSANCE DISPARAIT DANS LE DUEL : c etait un biais de COMPOSITION")
            print("     du banc a cible vulnerable. La courbe n est PAS un melange.")
            print("     SUSPENSION LEVEE, et le banc `degat_par_impact` est marque comme portant ce biais.")
b.sock.close()
