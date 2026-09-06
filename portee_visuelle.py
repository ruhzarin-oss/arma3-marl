#!/usr/bin/env python3
"""LA PORTEE DE DESIGNATION VISUELLE. Criteres : CRITERES_PORTEE_VISUELLE.md, ecrits d avance.
Prediction posee AVANT : d_max(f) = 123 * racine(f).
⚠️ SQF sans commentaires, nombres seuls."""
import sys, re, json, math, collections
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
REPET = int(sys.argv[2]) if len(sys.argv) > 2 else 1
DUREE = 60
SEUIL = 1.5
DISTANCES = [60, 100, 140, 180, 250, 350]
CAS = [0, 1, 2, 3]          # 0 = pleine vue · 1/2/3 = obstacle + posture UP/MIDDLE/DOWN
SORTIE = "/home/younes/arma3-marl/portee_visuelle.json"
b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert (compteur %d)" % (PORT, b.counter))

FRAC = ('private _frac = { params ["_a", "_c"]; private _o = eyePos _a; '
        'private _pi = getPosASL _c; private _oe = eyePos _c; private _n = 0; '
        '{ private _k = _x; private _pt = [(_pi select 0) + _k * ((_oe select 0) - (_pi select 0)), '
        '(_pi select 1) + _k * ((_oe select 1) - (_pi select 1)), '
        '(_pi select 2) + _k * ((_oe select 2) - (_pi select 2))]; '
        'if (([objNull, "VIEW"] checkVisibility [_o, _pt]) > 0.5) then { _n = _n + 1 }; '
        '} forEach [0.15, 0.4, 0.65, 0.9, 1]; _n / 5 }; ')

EPISODE = (
 '[] spawn { ' + FRAC +
 'private _p = [23000,17400,0]; private _dd = __D__; private _cas = __C__; '
 'private _gd = createGroup east; private _ga = createGroup west; '
 'private _d = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"]; '
 'private _q = [(_p select 0) + _dd, _p select 1, 0]; '
 'private _a = _ga createUnit ["B_Soldier_F", _q, [], 0, "NONE"]; '
 'private _mur = objNull; '
 'if (_cas > 0) then { '
 '  _mur = createVehicle ["Land_BagFence_Long_F", [(_q select 0) - 2, _q select 1, 0], [], 0, "CAN_COLLIDE"]; '
 '  _mur setDir 0; }; '
 'if (_cas == 3) then { _a setUnitPos "DOWN" } else { '
 '  if (_cas == 2) then { _a setUnitPos "MIDDLE" } else { _a setUnitPos "UP" } }; '
 '_d allowDamage false; _a allowDamage false; _d setSkill 0.5; _a setSkill 0.5; '
 '_d setUnitPos "UP"; _d disableAI "PATH"; _a disableAI "PATH"; '
 '_a disableAI "AUTOTARGET"; _a disableAI "TARGET"; _a setBehaviour "CARELESS"; '
 '_d setBehaviour "COMBAT"; _d setCombatMode "RED"; '
 'sleep 3; '
 'private _t0 = time; private _kmax = 0; private _fs = 0; private _n = 0; '
 'while { time - _t0 < __T__ } do { '
 '  private _f = [_d, _a] call _frac; private _k = _d knowsAbout _a; '
 '  if (_k > _kmax) then { _kmax = _k }; _fs = _fs + _f; _n = _n + 1; sleep 2; }; '
 'format ["HMTPV %1 %2 %3 %4 %5", _dd, _cas, _kmax, (_fs / _n), _n] call HMT_EMIT; '
 'deleteVehicle _a; deleteVehicle _d; if (!isNull _mur) then { deleteVehicle _mur }; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__T__", str(DUREE))

obs = []
for rep in range(REPET):
    for cas in CAS:
        for d in DISTANCES:
            r = b.query(EPISODE.replace("__D__", str(d)).replace("__C__", str(cas)),
                        r"HMTPV ([-0-9.eE+]+) (\d) ([-0-9.eE+]+) ([-0-9.eE+]+) (\d+)",
                        want=1, timeout=DUREE + 90)
            if not r:
                print("  cas %d %4d m : PAS DE FIN" % (cas, d)); continue
            k, f = float(r[0].group(3)), float(r[0].group(4))
            obs.append({"d": d, "cas": cas, "k": k, "f": f})
            print("  cas %d  %4d m : fraction %.2f · knowsAbout max %.2f %s"
                  % (cas, d, f, k, "DESIGNE" if k >= SEUIL else ""))
json.dump(obs, open(SORTIE, "w"))

print("\n  " + "=" * 66)
# controles
c_haut = [o for o in obs if o["cas"] == 0 and o["d"] == 60]
ok_haut = bool(c_haut) and max(o["k"] for o in c_haut) >= 3.5
print("  CONTROLE borne haute (60 m pleine vue -> 4,00) : %s"
      % ("✔" if ok_haut else "⛔ %s" % [o["k"] for o in c_haut]))
if not ok_haut:
    sys.exit("  ⛔ le controle positif tombe — rien n est lu.")

# bascule par case de fraction
CASES = [(0.05, 0.35), (0.35, 0.65), (0.65, 0.9), (0.9, 1.01)]
print("\n  case de fraction    f moy   bascule mesuree   prediction 123*rac(f)")
res = []
for lo, hi in CASES:
    sous = sorted([o for o in obs if lo <= o["f"] < hi], key=lambda o: o["d"])
    if len(sous) < 3:
        continue
    fm = sum(o["f"] for o in sous) / len(sous)
    desig = [o["d"] for o in sous if o["k"] >= SEUIL]
    non = [o["d"] for o in sous if o["k"] < SEUIL]
    if not desig:
        bas = 0.0
    elif not non:
        bas = float("inf")
    else:
        bas = (max(desig) + min([x for x in non if x > max(desig)] or [max(desig)])) / 2
    pred = 123 * math.sqrt(fm)
    res.append((fm, bas, pred))
    print("  [%.2f ; %.2f[        %.2f    %8s          %6.0f m"
          % (lo, hi, fm, ("%.0f m" % bas) if bas not in (0.0, float("inf"))
             else ("jamais" if bas == 0.0 else "> %d m" % DISTANCES[-1]), pred))

fini = [r for r in res if 0 < r[1] < float("inf")]
print("\n  cases avec bascule mesurable : %d (3 requises)" % len(fini))
if len(fini) >= 2:
    hautes = max(fini, key=lambda r: r[0]); basses = min(fini, key=lambda r: r[0])
    rap_mes = hautes[1] / basses[1]; rap_pred = math.sqrt(hautes[0] / basses[0])
    print("  FORME : rapport mesure %.2f · attendu racine(f1/f2) = %.2f" % (rap_mes, rap_pred))
b.sock.close()
