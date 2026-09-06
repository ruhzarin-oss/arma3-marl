#!/usr/bin/env python3
"""`movement` conditionne-t-il la detection ? Criteres : CRITERES_MOUVEMENT.md, ecrits d avance.
⚠️ SQF sans commentaires, nombres seuls."""
import sys, re, json, statistics
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
REPET = int(sys.argv[2]) if len(sys.argv) > 2 else 3
DUREE = 90
DISTANCES = [60, 150, 250, 350]
SORTIE = "/home/younes/arma3-marl/mouvement_detection.json"
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
 'private _p = [23000,17400,0]; private _dd = __D__; private _mob = __M__; '
 'private _gd = createGroup east; private _ga = createGroup west; '
 'private _d = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"]; '
 'private _q = [(_p select 0) + _dd, _p select 1, 0]; '
 'private _a = _ga createUnit ["B_Soldier_F", _q, [], 0, "NONE"]; '
 '_d allowDamage false; _a allowDamage false; _d setSkill 0.5; _a setSkill 0.5; '
 '_d setUnitPos "UP"; _a setUnitPos "UP"; _d disableAI "PATH"; '
 '_a disableAI "AUTOTARGET"; _a disableAI "TARGET"; _a setBehaviour "CARELESS"; '
 '_d setBehaviour "COMBAT"; _d setCombatMode "RED"; '
 'if (_mob == 0) then { _a disableAI "PATH" } else { _a setSpeedMode "FULL" }; '
 'sleep 3; '
 'private _t0 = time; private _kmax = 0; private _t05 = -1; private _t15 = -1; '
 'private _fs = 0; private _n = 0; private _sens = 1; '
 'while { time - _t0 < __T__ } do { '
 '  if (_mob == 1) then { '
 '    _a doMove [(_q select 0), (_q select 1) + 30 * _sens, 0]; _sens = -1 * _sens; }; '
 '  private _f = [_d, _a] call _frac; private _k = _d knowsAbout _a; '
 '  if (_k > _kmax) then { _kmax = _k }; '
 '  if (_t05 < 0 && {_k >= 0.5}) then { _t05 = time - _t0 }; '
 '  if (_t15 < 0 && {_k >= 1.5}) then { _t15 = time - _t0 }; '
 '  _fs = _fs + _f; _n = _n + 1; sleep 3; }; '
 'format ["HMTMV %1 %2 %3 %4 %5 %6", _dd, _mob, _kmax, _t05, _t15, (_fs / _n)] call HMT_EMIT; '
 'deleteVehicle _a; deleteVehicle _d; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__T__", str(DUREE))

obs = []
for rep in range(REPET):
    for d in DISTANCES:
        for mob in (0, 1):
            r = b.query(EPISODE.replace("__D__", str(d)).replace("__M__", str(mob)),
                        r"HMTMV ([-0-9.eE+]+) (\d) ([-0-9.eE+]+) ([-0-9.eE+]+) ([-0-9.eE+]+) ([-0-9.eE+]+)",
                        want=1, timeout=DUREE + 90)
            if not r:
                print("  %4d m %s : PAS DE FIN" % (d, "mobile" if mob else "immobile")); continue
            k, t05, t15, f = (float(r[0].group(i)) for i in (3, 4, 5, 6))
            obs.append({"d": d, "mob": mob, "k": k, "t05": t05, "t15": t15, "f": f})
            print("  %4d m %-8s : fraction %.2f · kmax %.2f · t(0,5) %s · t(1,5) %s"
                  % (d, "MOBILE" if mob else "immobile", f, k,
                     ("%.0f s" % t05) if t05 >= 0 else "jamais",
                     ("%.0f s" % t15) if t15 >= 0 else "jamais"))
json.dump(obs, open(SORTIE, "w"))

print("\n  " + "=" * 66)
c60 = [o for o in obs if o["d"] == 60]
ok = bool(c60) and all(o["k"] >= 3.5 for o in c60)
print("  CONTROLE POSITIF (60 m, les deux bras a 4,00) : %s"
      % ("✔" if ok else "⛔ %s" % [(o["mob"], o["k"]) for o in c60]))
if not ok:
    sys.exit("  ⛔ rien n est lu.")
print("\n  distance   immobile t(0,5)   mobile t(0,5)   rapport   kmax imm / mob")
for d in DISTANCES:
    I = [o for o in obs if o["d"] == d and o["mob"] == 0]
    M = [o for o in obs if o["d"] == d and o["mob"] == 1]
    if not I or not M: continue
    def med(v, c):
        x = [o[c] for o in v if o[c] >= 0]
        return statistics.median(x) if x else None
    ti, tm = med(I, "t05"), med(M, "t05")
    rap = ("%.2f" % (ti / tm)) if (ti and tm and tm > 0) else ("jamais/%.0f" % tm if tm else "-")
    print("  %4d m       %-14s   %-13s   %-8s  %.2f / %.2f"
          % (d, ("%.0f s" % ti) if ti else "jamais", ("%.0f s" % tm) if tm else "jamais",
             rap, statistics.median([o["k"] for o in I]), statistics.median([o["k"] for o in M])))
loin = [d for d in DISTANCES if d > 60]
rr = []
for d in loin:
    I = [o["t05"] for o in obs if o["d"] == d and o["mob"] == 0 and o["t05"] >= 0]
    M = [o["t05"] for o in obs if o["d"] == d and o["mob"] == 1 and o["t05"] >= 0]
    if I and M: rr.append(statistics.median(I) / statistics.median(M))
print()
if not rr:
    print("  ⚠️ INDECIS : pas de bascule comparable dans les deux bras.")
elif statistics.median(rr) < 1.5:
    print("  ⛔ `movement` REFUTE : l immobile est detecte aussi vite (rapport median %.2f < 1,5)."
          % statistics.median(rr))
    print("     -> ON NE MET PAS ce terme dans le gymnase. Il aurait paye l immobilite dans un")
    print("        monde ou figer un homme coute deja ⟨doctrine 91,0 contre 35,0⟩.")
else:
    print("  ✔ `movement` CONFIRME : rapport median %.2f (>= 1,5)." % statistics.median(rr))
    print("     ⚠️ A brancher SOUS SURVEILLANCE de la doctrine 91/35 et du bond +15 ⟨Fable⟩.")
b.sock.close()
