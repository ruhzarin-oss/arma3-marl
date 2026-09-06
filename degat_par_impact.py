#!/usr/bin/env python3
"""`degat_par_impact` re-derive + stratification par MODE et par RANG.
Criteres : CRITERES_DEGAT_PAR_IMPACT.md, ecrits avant les chiffres.
⚠️ SQF sans commentaires, nombres seuls, jamais de formatage `%` sur du SQF.
"""
import sys, re, json, math, statistics, collections
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
BLOCS = int(sys.argv[2]) if len(sys.argv) > 2 else 14
NDUEL = 12
DUREE = 55
DIST = 100
SORTIE = "/home/younes/arma3-marl/degat_par_impact.json"
b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert (compteur %d)" % (PORT, b.counter), flush=True)

SESSION = ('[] spawn { HMT_T = 0; HMT_M = 0; '
 'private _duels = []; '
 'for "_j" from 0 to __NM1__ do { '
 '  private _p = [16000,16000,0]; '
 '  for "_i" from 0 to 60 do { _p = [] call BIS_fnc_randomPos; '
 '    if ((getTerrainHeightASL _p) > 5) exitWith {} }; '
 '  private _az = random 360; '
 '  private _q = [(_p select 0) + __D__ * sin _az, (_p select 1) + __D__ * cos _az, 0]; '
 '  private _g1 = createGroup west; private _g2 = createGroup east; '
 '  private _s = _g1 createUnit ["B_Soldier_F", _p, [], 0, "NONE"]; '
 '  private _c = _g2 createUnit ["O_Soldier_F", _q, [], 0, "NONE"]; '
 '  _s allowDamage false; '
 '  _s setSkill 0.5; _c setSkill 0.5; _s allowFleeing 0; _c allowFleeing 0; '
 '  _s setUnitPos "UP"; _s disableAI "PATH"; _s disableAI "AUTOTARGET"; '
 '  _c setUnitPos "UP"; _c disableAI "PATH"; _c disableAI "AUTOTARGET"; '
 '  _c disableAI "TARGET"; _c setBehaviour "CARELESS"; '
 '  _s setVariable ["hd", _j]; _c setVariable ["hd", _j]; _c setVariable ["hs", _s]; '
 '  _s setVariable ["hc", _c]; _s setVariable ["hr", 0]; _c setVariable ["hi", 0]; '
 '  _s addEventHandler ["Fired", { params ["_u","_arme","_muz","_mode"]; '
 '    private _r = (_u getVariable ["hr", 0]) + 1; _u setVariable ["hr", _r]; HMT_T = HMT_T + 1; '
 '    private _m = 0; if (_mode == "FullAuto") then { _m = 1 }; '
 '    if (_mode == "fullauto_medium") then { _m = 2 }; '
 '    if (_mode == "single_medium_optics1") then { _m = 3 }; '
 '    if (_mode == "single_far_optics2") then { _m = 4 }; '
 '    if (_mode == "Single") then { _m = 5 }; '
 '    format ["DFF %1 %2 %3", (_u getVariable ["hd", -1]), _r, _m] call HMT_EMIT; }]; '
 '  _c addEventHandler ["HitPart", { private _e = (_this select 0); '
 '    private _v = _e select 0; private _sh = _e select 1; private _pr = _e select 2; '
 '    if (isNull _v or isNull _sh) exitWith {}; '
 '    if (_sh != (_v getVariable ["hs", objNull])) exitWith {}; '
 '    if (_pr isEqualTo (_v getVariable ["hp", objNull])) exitWith {}; '
 '    _v setVariable ["hp", _pr]; '
 '    private _i = (_v getVariable ["hi", 0]) + 1; _v setVariable ["hi", _i]; '
 '    format ["DFI %1 %2 %3", (_v getVariable ["hd", -1]), _i, '
 '      (_sh getVariable ["hr", 0])] call HMT_EMIT; }]; '
 '  _c addEventHandler ["Killed", { params ["_v"]; HMT_M = HMT_M + 1; '
 '    format ["DFM %1 %2", (_v getVariable ["hd", -1]), (_v getVariable ["hi", 0])] call HMT_EMIT; }]; '
 '  _duels pushBack [_s, _c]; '
 '}; '
 'sleep 3; '
 '{ (_x select 0) reveal [(_x select 1), 4]; (_x select 0) setBehaviour "COMBAT"; '
 '  (_x select 0) setCombatMode "RED"; } forEach _duels; '
 'private _t0 = time; '
 'while { time - _t0 < __T__ } do { '
 '  { if (alive (_x select 1)) then { (_x select 0) doTarget (_x select 1); '
 '      (_x select 0) doFire (_x select 1); } } forEach _duels; '
 '  sleep 3; }; '
 'format ["DFEND %1 %2 %3", HMT_T, HMT_M, count _duels] call HMT_EMIT; '
 '{ deleteVehicle (_x select 0); deleteVehicle (_x select 1); } forEach _duels; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__NM1__", str(NDUEL - 1)).replace("__T__", str(DUREE)).replace("__D__", str(DIST))

MODES = {1: "FullAuto", 2: "fullauto_medium", 3: "single_medium_optics1",
         4: "single_far_optics2", 5: "Single", 0: "autre"}
# ⚠️ ON ACCUMULE, ON N ECRASE PAS. Une cible VULNERABLE meurt vite : chaque duel ne rend
# que quelques dizaines de balles, la ou une cible invulnerable en rend un millier. Une
# seule passe ne peut donc pas atteindre les 30 neutralisations exigees par le critere.
# Le critere n est pas assoupli : on lui donne le n qu il demande, en plusieurs passes.
import os
tirs, imps, morts = [], [], []
if os.path.exists(SORTIE):
    _p = json.load(open(SORTIE))
    tirs = [tuple(x) for x in _p.get("tirs", [])]
    imps = list(_p.get("imps", []))
    morts = list(_p.get("morts", []))
    print("  reprise : %d balles, %d neutralisations deja acquises" % (len(tirs), len(morts)), flush=True)
for k in range(BLOCS):
    n0 = len(b._log_lines(400000))
    try:
        r = b.query(SESSION, r"DFEND (\d+) (\d+) (\d+)", want=1, timeout=DUREE + 120)
    except Exception:
        print("  bloc %d : pont perdu, bloc jete" % k, flush=True)
        try: b = NativeBridge(port=PORT, timeout=20)
        except Exception: break
        continue
    if not r:
        print("  bloc %d : pas de fin" % k, flush=True); continue
    nt, nm, nd = (int(r[0].group(i)) for i in (1, 2, 3))
    for s in b._log_lines(400000)[n0:]:
        m = re.match(r"DFF (-?\d+) (\d+) (\d+)$", s.strip())
        if m: tirs.append((int(m.group(2)), int(m.group(3))))
        m = re.match(r"DFI (-?\d+) (\d+) (\d+)$", s.strip())
        if m: imps.append(int(m.group(3)))
        m = re.match(r"DFM (-?\d+) (\d+)$", s.strip())
        if m: morts.append(int(m.group(2)))
    print("  bloc %d/%d : %d duels · %d balles · %d neutralisations (cumul morts %d)"
          % (k + 1, BLOCS, nd, nt, nm, len(morts)), flush=True)
    json.dump({"tirs": tirs, "imps": imps, "morts": morts}, open(SORTIE, "w"))

print("\n  " + "=" * 68)
print("  CONTROLE POSITIF — des cibles tombent : %d neutralisations" % len(morts))
if len(morts) < 30:
    sys.exit("  ⛔ moins de 30 neutralisations : la mediane n est pas rendue.")
morts.sort()
med = statistics.median(morts)
print("  impacts jusqu a la neutralisation : mediane %.1f · min %d · max %d · n=%d"
      % (med, morts[0], morts[-1], len(morts)))
print("  ⭐ degat_par_impact = 0,70 / %.1f = %.4f   (en service : 0,2330 = 0,7/3,00)"
      % (med, 0.70 / med))

print("\n  STRATIFICATION PAR MODE DE TIR")
pm = collections.Counter(m for _, m in tirs)
if len(pm) <= 1:
    print("    un seul mode observe (%s) : NON RENDUE" % MODES.get(list(pm)[0] if pm else 0))
else:
    for code, n in pm.most_common():
        print("    %-22s %6d balles (%.1f %%)" % (MODES.get(code, code), n, 100 * n / len(tirs)))
    print("    -> l explication CfgWeapons devient une MESURE : les modes employes a %d m sont nommes" % DIST)

print("\n  STRATIFICATION PAR RANG DU COUP  (la cible est VULNERABLE : pas de coups tardifs artificiels)")
CASES = [(1, 10), (11, 30), (31, 80), (81, 10 ** 6)]
def wil(i, n):
    if n == 0: return (float("nan"),) * 3
    p = i / n; z = 1.96; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)
bornes = []
for lo, hi in CASES:
    nt_ = sum(1 for r, _ in tirs if lo <= r <= hi)
    ni_ = sum(1 for r in imps if lo <= r <= hi)
    if nt_ >= 100:
        p, l, h = wil(ni_, nt_)
        bornes.append((lo, hi, p, l, h, nt_))
        print("    coups %3d-%-6s %6d balles  %.3f  [%.3f ; %.3f]"
              % (lo, ("%d" % hi) if hi < 10 ** 6 else "+", nt_, p, l, h))
    else:
        print("    coups %3d-%-6s %6d balles  n<100, non rendu" % (lo, ("%d" % hi) if hi < 10 ** 6 else "+", nt_))
if len(bornes) >= 2:
    a, z = bornes[0], bornes[-1]
    disjoint = (a[4] < z[3]) or (z[4] < a[3])
    print()
    if disjoint:
        print("  ⛔ `p_touche` DEPEND DU RANG (%.3f contre %.3f, IC disjoints)." % (a[2], z[2]))
        print("     LA COURBE EST UN MELANGE et ne se transporte pas. Allumage d ÉQ. 1 SUSPENDU.")
    else:
        print("  ✔ `p_touche` ne depend pas du rang (IC recouvrants) : la courbe n est pas un melange.")
b.sock.close()
