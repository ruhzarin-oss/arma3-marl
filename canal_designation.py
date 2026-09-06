#!/usr/bin/env python3
"""L OUIE PEUT-ELLE DESIGNER ? Criteres : CRITERES_CANAL_DESIGNATION.md, ecrits d avance.

`knowsAbout` rend `FadingSideAccuracy()` — la variable MEME que le seuil de 1,5 gouverne.
Bras A visible (controle positif) · bras B masque et bruyant (le test).
⚠️ SQF sans commentaires, et on n emet que des nombres.
"""
import sys, re, json
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
EPI = int(sys.argv[2]) if len(sys.argv) > 2 else 8
DUREE = 40
SEUIL = 1.5
SORTIE = "/home/younes/arma3-marl/canal_designation.json"
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
 'private _p = [23000,17400,0]; '
 'private _bras = __BRAS__; private _dd = __DIST__; '
 'private _gd = createGroup east; private _ga = createGroup west; '
 'private _d = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"]; '
 'private _q = [(_p select 0) + _dd, _p select 1, 0]; '
 'private _mur = objNull; '
 'if (_bras == 1) then { '
 '  _mur = createVehicle ["Land_Cargo_HQ_V1_F", [(_p select 0) + _dd / 2, _p select 1, 0], [], 0, "CAN_COLLIDE"]; '
 '}; '
 'private _a = _ga createUnit ["B_Soldier_F", _q, [], 0, "NONE"]; '
 '_d allowDamage false; _a allowDamage false; '
 '_d setSkill 0.5; _a setSkill 0.5; _d setUnitPos "UP"; _a setUnitPos "UP"; '
 '_d disableAI "PATH"; _a disableAI "PATH"; _a disableAI "AUTOTARGET"; _a disableAI "TARGET"; '
 '_d setBehaviour "COMBAT"; _d setCombatMode "RED"; '
 '_a setDir 90; '
 'sleep 3; '
 'private _t0 = time; private _kmax = 0; private _fmax = 0; private _tirs = 0; private _n = 0; '
 'while { time - _t0 < __T__ } do { '
 '  if (_bras == 1) then { _a forceWeaponFire [currentMuzzle _a, currentWeaponMode _a]; _tirs = _tirs + 1 }; '
 '  private _f = [_d, _a] call _frac; '
 '  private _k = _d knowsAbout _a; '
 '  if (_f > _fmax) then { _fmax = _f }; if (_k > _kmax) then { _kmax = _k }; '
 '  _n = _n + 1; sleep 2; '
 '}; '
 'format ["HMTCD %1 %2 %3 %4 %5 %6", _bras, _kmax, _fmax, _tirs, _n, _dd] call HMT_EMIT; '
 'deleteVehicle _a; deleteVehicle _d; if (!isNull _mur) then { deleteVehicle _mur }; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__T__", str(DUREE))

DISTANCES = [15, 25, 40, 60, 80, 100]   # la geometrie VARIE : n=8 identiques, c est n=1
res = {0: [], 1: []}
for ep in range(EPI):
    dist = DISTANCES[ep % len(DISTANCES)]
    for bras in (0, 1):
        r = b.query(EPISODE.replace("__BRAS__", str(bras)).replace("__DIST__", str(dist)),
                    r"HMTCD (\d) ([-0-9.eE+]+) ([-0-9.eE+]+) (\d+) (\d+) ([-0-9.eE+]+)", want=1, timeout=DUREE + 90)
        if not r:
            print("  bras %d episode %d : PAS DE FIN" % (bras, ep)); continue
        k, f, t, n = float(r[0].group(2)), float(r[0].group(3)), int(r[0].group(4)), int(r[0].group(5))
        res[bras].append({"kmax": k, "fmax": f, "tirs": t, "releves": n, "dist": dist})
        print("  bras %s  %3d m : knowsAbout max %.2f · fraction max %.2f · tirs %d"
              % ("A(vu)   " if bras == 0 else "B(masque)", dist, k, f, t))

print("\n  " + "=" * 66)
A, B = res[0], res[1]
kA = [e["kmax"] for e in A]
print("  BRAS A — CONTROLE POSITIF (visible) : %d episodes · knowsAbout max median %.2f"
      % (len(A), sorted(kA)[len(kA) // 2] if kA else -1))
ctrl = bool(kA) and sum(1 for k in kA if k >= SEUIL) >= max(1, int(0.5 * len(kA)))
print("    %s" % ("✔ la sonde franchit 1,5 quand on VOIT" if ctrl
                  else "⛔ elle ne franchit PAS meme a vue — rien n est lu"))
if not ctrl:
    json.dump(res, open(SORTIE, "w")); sys.exit(1)
Bv = [e for e in B if e["fmax"] == 0.0 and e["tirs"] > 0]
print("  BRAS B — episodes VALIDES (jamais vu, et bruyant) : %d / %d" % (len(Bv), len(B)))
if len(Bv) < 6:
    print("  ⛔ moins de 6 episodes valides — ON NE CONCLUT PAS.")
else:
    kB = sorted(e["kmax"] for e in Bv)
    print("  distances valides : %s" % sorted({e["dist"] for e in Bv}))
    print("  knowsAbout max : min %.2f · median %.2f · MAX %.2f" % (kB[0], kB[len(kB) // 2], kB[-1]))
    if len({e["dist"] for e in Bv}) < 3:
        print("  ⚠️ moins de 3 geometries distinctes : le resultat vaut pour une condition,")
        print("     pas pour une loi. On le dit.")
    if kB[-1] >= SEUIL:
        print("  ⛔ FALSIFIEE : l ouie seule fait franchir 1,5 (%d episodes sur %d)"
              % (sum(1 for k in kB if k >= SEUIL), len(kB)))
    elif kB[-1] == 0.0:
        print("  ⚠️ INDECIS — knowsAbout reste EXACTEMENT nul : le canal auditif n a rien")
        print("     transmis, donc le banc a teste le silence, pas le plafond.")
        print("     ⟨un zero n est pas un accord⟩")
    else:
        print("  ✔ ELLE TIENT : l ouie porte l information (max %.2f) et ne nomme JAMAIS le camp"
              % kB[-1])
json.dump(res, open(SORTIE, "w"))
print("  ecrit : %s" % SORTIE)
b.sock.close()
