#!/usr/bin/env python3
"""POINT 2 — le conflit `R_VUE_NULLE` : 0,00 a 100 m (30/07) contre 3,99 a 250 m (03/09).

Ni la posture (les deux « debout ») ni la fenetre (les deux jusqu a 60 s) ne separent les
deux bancs. Reste UNE variable : le comportement de l attaquant.
  · banc du 30/07 : `setBehaviour COMBAT` + `setCombatMode RED`  -> il se met a couvert
  · banc du 03/09 : `setBehaviour CARELESS`                      -> il reste plante debout
Et nous savons depuis ce soir qu un homme COUCHE devient invisible passe ~120 m.

FALSIFICATEUR ECRIT D AVANCE : si les deux bras rendent le MEME `knowsAbout` a 100 m, le
comportement n explique rien et le conflit est reel -> il faudra un ABBA sur le meme banc.
CONTROLE POSITIF : a 30 m, les DEUX bras doivent monter a 4,00 (cas connu massif, mesure le
30/07 avec le controle positif de l epoque). S il tombe, rien n est lu.
On releve aussi la POSTURE reelle de l attaquant : c est l explication candidate, elle doit
etre visible dans la donnee, pas supposee.
"""
import sys, re, json
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
DUREE = 60
b = NativeBridge(port=PORT, timeout=20)

EP = (
 '[] spawn { private _p = [23000,17400,0]; private _dd = __D__; private _cm = __C__; '
 'private _gd = createGroup east; private _ga = createGroup west; '
 'private _d = _gd createUnit ["O_Soldier_F", _p, [], 0, "NONE"]; '
 'private _a = _ga createUnit ["B_Soldier_F", [(_p select 0) + _dd, _p select 1, 0], [], 0, "NONE"]; '
 '_d allowDamage false; _a allowDamage false; _d setSkill 0.7; _a setSkill 0.7; '
 '_d setBehaviour "COMBAT"; _d setCombatMode "RED"; _d disableAI "PATH"; '
 '_a setUnitPos "UP"; '
 'if (_cm == 1) then { _a setBehaviour "COMBAT"; _a setCombatMode "RED" } '
 'else { _a setBehaviour "CARELESS"; _a disableAI "AUTOTARGET"; _a disableAI "TARGET"; '
 '_a disableAI "PATH" }; '
 'sleep 3; '
 'private _t0 = time; private _kmax = 0; private _bas = 0; private _n = 0; private _dep = 0; '
 'private _p0 = getPosATL _a; '
 'while { time - _t0 < __T__ } do { '
 '  private _k = _d knowsAbout _a; if (_k > _kmax) then { _kmax = _k }; '
 '  if ((animationState _a) find "lying" >= 0 or (animationState _a) find "pron" >= 0 '
 '    or (animationState _a) find "Dead" >= 0) then { _bas = _bas + 1 }; '
 '  _n = _n + 1; sleep 2; }; '
 '_dep = _a distance2D _p0; '
 'format ["HMTRV %1 %2 %3 %4 %5", _dd, _cm, _kmax, (_bas / _n), _dep] call HMT_EMIT; '
 'deleteVehicle _a; deleteVehicle _d; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__T__", str(DUREE))

obs = []
for d in (30, 60, 100, 150, 250):
    for cm in (0, 1):
        r = b.query(EP.replace("__D__", str(d)).replace("__C__", str(cm)),
                    r"HMTRV ([-0-9.eE+]+) (\d) ([-0-9.eE+]+) ([-0-9.eE+]+) ([-0-9.eE+]+)",
                    want=1, timeout=DUREE + 90)
        if not r:
            print("  %4d m %s : PAS DE FIN" % (d, cm)); continue
        k, bas, dep = (float(r[0].group(i)) for i in (3, 4, 5))
        obs.append({"d": d, "cm": cm, "k": k, "bas": bas, "dep": dep})
        print("  %4d m  %-8s : knowsAbout max %.2f · part du temps AU SOL %.0f %% · deplacement %.0f m"
              % (d, "COMBAT" if cm else "CARELESS", k, 100 * bas, dep))
json.dump(obs, open("/home/younes/arma3-marl/conflit_rvue.json", "w"))

print("\n  " + "=" * 66)
c30 = [o for o in obs if o["d"] == 30]
ok = len(c30) == 2 and all(o["k"] >= 3.5 for o in c30)
print("  CONTROLE POSITIF (30 m, les deux bras a 4,00) : %s" % ("✔" if ok else "⛔ %s" % [o["k"] for o in c30]))
if not ok:
    sys.exit("  ⛔ rien n est lu.")
print("\n  distance   CARELESS   COMBAT   ecart")
for d in (30, 60, 100, 150, 250):
    A = [o for o in obs if o["d"] == d and o["cm"] == 0]
    B = [o for o in obs if o["d"] == d and o["cm"] == 1]
    if A and B:
        print("  %4d m       %.2f      %.2f     %+.2f" % (d, A[0]["k"], B[0]["k"], B[0]["k"] - A[0]["k"]))
c100 = {o["cm"]: o for o in obs if o["d"] == 100}
if 0 in c100 and 1 in c100:
    ec = abs(c100[0]["k"] - c100[1]["k"])
    print()
    if ec < 0.5:
        print("  ⛔ LE COMPORTEMENT N EXPLIQUE RIEN (ecart %.2f a 100 m) : le conflit est REEL," % ec)
        print("     il faut un ABBA sur le meme banc.")
    else:
        print("  ✔ LE COMPORTEMENT EXPLIQUE LE CONFLIT : ecart %.2f a 100 m." % ec)
        print("     COMBAT au sol %.0f %% du temps contre %.0f %% en CARELESS."
              % (100 * c100[1]["bas"], 100 * c100[0]["bas"]))
        print("     Les deux mesures sont JUSTES, chacune dans SON regime — comme le 62 %.")
b.sock.close()
