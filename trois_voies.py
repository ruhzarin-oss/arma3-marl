#!/usr/bin/env python3
"""LE BRAS A TROIS VOIES SUR ARMA.

⚠️ CORRECTIF DU 04/09, impose par le pre-test : un `doMove` emis UNE SEULE FOIS est abandonne
des le premier contact en comportement COMBAT. Resultat : 8/8 assaillants vivants, 4/4
defenseurs vivants, rien en 150 s — l assaut n assaillait pas, et le controle « des morts des
deux cotes » a REFUSE la lecture (2/6). L ordre est desormais REEMIS a chaque tour de boucle,
EGALEMENT DANS LES TROIS BRAS. La metrique de prise n a PAS ete touchee : on repare
l instrument, on ne deplace pas la cible. Criteres : CRITERES_TROIS_VOIES.md, ecrits d avance.
A = frontal simple · B = fixeurs + assaut FRONTAL · C = fixeurs + debordement FLANC.
Effectif total egal (8 assaillants, 4 defenseurs), tout le reste egalise.
⚠️ SQF sans commentaires, nombres seuls, jamais de formatage `%` sur du SQF."""
import sys, re, json, math, statistics
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
EPI = int(sys.argv[2]) if len(sys.argv) > 2 else 16
DUREE = 300   # ⚠️ 220 m sous le feu, par bonds : 150 s ne suffisaient pas a arriver
SORTIE = "/home/younes/arma3-marl/trois_voies.json"
b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert (compteur %d)" % (PORT, b.counter), flush=True)

# bras : 0 = A frontal · 1 = B fixeurs + frontal · 2 = C fixeurs + flanc
EP = ('[] spawn { private _bras = __B__; HMT_TIRD = 0; '
 'private _p = [16000,16000,0]; '
 'for "_i" from 0 to 80 do { _p = [] call BIS_fnc_randomPos; '
 '  if ((getTerrainHeightASL _p) > 5) exitWith {} }; '
 'private _az = random 360; '
 'private _gd = createGroup east; private _ga = createGroup west; '
 'private _def = []; '
 'for "_i" from 0 to 3 do { '
 '  private _d = _gd createUnit ["O_Soldier_F", '
 '    [(_p select 0) + (_i - 2) * 8, (_p select 1), 0], [], 0, "NONE"]; '
 '  _d setSkill 0.5; _d allowFleeing 0; _d setUnitPos "MIDDLE"; _d disableAI "PATH"; '
 '  _d setBehaviour "COMBAT"; _d setCombatMode "RED"; '
 '  _d addEventHandler ["Fired", { HMT_TIRD = HMT_TIRD + 1 }]; '
 '  _def pushBack _d; }; '
 'private _dep = [(_p select 0) + 220 * sin _az, (_p select 1) + 220 * cos _az, 0]; '
 'private _att = []; '
 'for "_i" from 0 to 7 do { '
 '  private _a = _ga createUnit ["B_Soldier_F", '
 '    [(_dep select 0) + (_i % 4) * 6 - 9, (_dep select 1) + floor (_i / 4) * 6, 0], [], 0, "NONE"]; '
 '  _a setSkill 0.5; _a allowFleeing 0; _a setBehaviour "COMBAT"; _a setCombatMode "RED"; '
 '  _att pushBack _a; }; '
 'sleep 3; '
 '{ private _v = _x; { _v reveal [_x, 4] } forEach _def } forEach _att; '
 '{ private _v = _x; { _v reveal [_x, 4] } forEach _att } forEach _def; '
 'private _obj = [(_p select 0), (_p select 1), 0]; '
 'private _flanc = [(_p select 0) + 90 * sin (_az + 90), (_p select 1) + 90 * cos (_az + 90), 0]; '
 'if (_bras == 0) then { '
 '  { _x setSpeedMode "FULL"; _x doMove _obj } forEach _att; '
 '} else { '
 '  private _nf = 4; '
 '  for "_i" from 0 to (_nf - 1) do { private _f = _att select _i; '
 '    _f setUnitPos "DOWN"; _f disableAI "PATH"; '
 '    { _f reveal [_x, 4]; _f doTarget _x } forEach _def; }; '
 '  private _but = _obj; if (_bras == 2) then { _but = _flanc }; '
 '  for "_i" from _nf to 7 do { private _m = _att select _i; '
 '    _m setSpeedMode "FULL"; _m doMove _but; }; '
 '}; '
 'private _t0 = time; private _pris = 0; '
 'while { time - _t0 < __T__ } do { '
 '  if (_bras == 0) then { '
 '    { if (alive _x) then { _x doMove _obj } } forEach _att; '
 '  }; '
 '  if (_bras > 0) then { '
 '    for "_i" from 0 to 3 do { private _f = _att select _i; '
 '      if (alive _f) then { { if (alive _x) then { _f doTarget _x; _f doFire _x } } forEach _def } }; '
 '    private _but2 = _obj; '
 '    if ((_bras == 2) and (time - _t0 <= 45)) then { _but2 = _flanc }; '
 '    for "_i" from 4 to 7 do { private _m = _att select _i; '
 '      if (alive _m) then { _m doMove _but2 } }; '
 '  }; '
 '  { if ((alive _x) and ((_x distance2D _obj) < 15)) then { _pris = 1 } } forEach _att; '
 '  if (_pris == 1) exitWith {}; '
 '  if (({alive _x} count _att) == 0) exitWith {}; '
 '  sleep 3; }; '
 'private _dmin = 9999; '
 '{ if (alive _x) then { private _dd2 = _x distance2D _obj; '
 '  if (_dd2 < _dmin) then { _dmin = _dd2 } } } forEach _att; '
 'format ["TV %1 %2 %3 %4 %5 %6 %7", _bras, _pris, ({alive _x} count _att), '
 '  ({alive _x} count _def), HMT_TIRD, round (time - _t0), round _dmin] call HMT_EMIT; '
 '{ deleteVehicle _x } forEach (_att + _def); '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__T__", str(DUREE))

NOMS = {0: "A frontal", 1: "B fixeurs+frontal", 2: "C fixeurs+flanc"}
obs = []
for ep in range(EPI):
    for bras in (0, 1, 2):
        with b._lock:
            b.lines.clear()
        try:
            r = b.query(EP.replace("__B__", str(bras)),
                        r"TV (\d) (\d) (\d+) (\d+) (\d+) (\d+) (\d+)", want=1, timeout=DUREE + 120)
        except Exception:
            print("  ep %d %s : pont perdu" % (ep, NOMS[bras]), flush=True)
            try: b = NativeBridge(port=PORT, timeout=20)
            except Exception: break
            continue
        if not r:
            print("  ep %d %s : pas de fin" % (ep, NOMS[bras]), flush=True); continue
        pris, va, vd, tird, dur, dmin = (int(r[0].group(i)) for i in (2, 3, 4, 5, 6, 7))
        obs.append(dict(bras=bras, pris=pris, att=va, deff=vd, tird=tird, duree=dur, dmin=dmin))
        print("  ep %2d %-18s pris=%d · att %d/8 · def %d/4 · tirs %4d · %3d s · le plus proche a %4d m"
              % (ep, NOMS[bras], pris, va, vd, tird, dur, dmin), flush=True)
        json.dump(obs, open(SORTIE, "w"))

print("\n  " + "=" * 72)
vides = [o for o in obs if o["tird"] == 0]
print("  CANARI D ACTIVATION — episodes ou les defenseurs n ont PAS tire : %d / %d"
      % (len(vides), len(obs)))
val = [o for o in obs if o["tird"] > 0]
mixte = sum(1 for o in val if o["att"] < 8 and o["deff"] < 4)
print("  CONTROLE — episodes avec des morts DES DEUX cotes : %d / %d" % (mixte, len(val)))
if len(val) < 3 or mixte < len(val) / 2:
    sys.exit("  ⛔ le monde ne combat pas comme il faut — rien n est lu.")

def wil(i, n):
    if n == 0: return (float("nan"),) * 3
    p = i / n; z = 1.96; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)

print("\n  bras                  n   prise      IC95            pertes att  pertes def")
res = {}
for bras in (0, 1, 2):
    s = [o for o in val if o["bras"] == bras]
    if len(s) < 12:
        print("  %-18s %3d   NON RENDU (moins de 12 episodes)" % (NOMS[bras], len(s))); continue
    i = sum(o["pris"] for o in s)
    p, lo, hi = wil(i, len(s))
    pa = statistics.mean(8 - o["att"] for o in s); pd = statistics.mean(4 - o["deff"] for o in s)
    res[bras] = (p, lo, hi, len(s))
    print("  %-18s %3d   %.3f    [%.3f ; %.3f]   %.1f / 8     %.1f / 4"
          % (NOMS[bras], len(s), p, lo, hi, pa, pd))

if len(res) == 3:
    A, Bb, C = res[0], res[1], res[2]
    dis = lambda x, y: (x[2] < y[1]) or (y[2] < x[1])
    print()
    if dis(C, Bb) and C[0] > Bb[0] and dis(Bb, A) and Bb[0] > A[0]:
        print("  ⭐ C > B > A : LA GEOMETRIE PAIE. Le signe gele survit sur Arma,")
        print("     et c est MA COURBE qui est suspecte.")
    elif not dis(C, Bb) and dis(Bb, A) and Bb[0] > A[0]:
        print("  ⭐ C ≈ B > A : c est LA SUPPRESSION seule qui paie.")
        print("     « Le flanc » est du folklore, et le carnet du projet est a reecrire.")
    elif not dis(A, Bb) and not dis(Bb, C):
        print("  ⚠️ A ≈ B ≈ C : le banc ne discrimine pas. On ne conclut pas.")
    else:
        print("  ⚠️ configuration non prevue par les criteres : A=%.3f B=%.3f C=%.3f"
              % (A[0], Bb[0], C[0]))
        print("     On la NOMME au lieu de la ranger dans une case ecrite d avance.")
json.dump(obs, open(SORTIE, "w"))
print("\n  ecrit : %s" % SORTIE)
b.sock.close()
