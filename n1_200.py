#!/usr/bin/env python3
"""N1 — LE NIVEAU DE LA COURBE, REMESURE A `HitPart`. Criteres : CRITERES_N1_NIVEAU.md.

⛔ CORRECTIF DU 04/09, IMPOSE PAR LA DONNEE. La premiere passe a rendu 2 164 impacts pour
1 759 balles a 25 m couche — un taux de 1,23, IMPOSSIBLE. « Un impact par appel de
l ecouteur » ne suffit donc pas : le moteur appelle `HitPart` PLUSIEURS FOIS pour un MEME
projectile. On deduplique desormais par IDENTITE DU PROJECTILE (`_e select 2`), pas par
appel. C est la troisieme fois que ce projet paie le meme mode d echec, a un cran plus fin
chaque fois : `HandleDamage` 1,9 appel par balle, puis les parties du corps, puis les appels
repetes pour un projectile.

18 conditions (6 distances x 3 postures), terrain nu, skill 0,5, plein jour.
SEUL LE CAPTEUR CHANGE. Quatre gardes, toutes deja payees par le projet :
  1. compter les BALLES TIREES (`Fired`) autant que les impacts ;
  2. UN impact par PROJECTILE (`_this select 0`, jamais `forEach _this`) ;
  3. n accepter un impact que si sa SOURCE est le tireur APPARIE ;
  4. tireurs ET cibles invulnerables.
⚠️ SQF sans commentaires (call compile ne retire pas les //), nombres seuls.
"""
import sys, re, json, math, time, collections
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
BLOCS = int(sys.argv[2]) if len(sys.argv) > 2 else 12
NDUEL = 18                      # une condition par duel : 6 distances x 3 postures
DUREE = 55                      # bloc court : l IA cesse d engager une cible qui ne tombe pas
DIST = [25, 50, 75, 100, 150, 200]
POST = ["UP", "MIDDLE", "DOWN"]
BANDE = (0.45, 0.66)            # bande du controle positif, ecrite d avance
SORTIE = "/home/younes/arma3-marl/courbe_toucher_hitpart_200.json"

b = NativeBridge(port=PORT, timeout=20)
print("  pont %d ouvert (compteur %d)" % (PORT, b.counter), flush=True)

COND = [(200, p) for p in POST for _ in range(6)]   # 18 duels TOUS a 200 m, 6 par posture
assert len(COND) == NDUEL

SESSION = (
 '[] spawn { HMT_T = 0; HMT_I = 0; '
 'private _duels = []; private _D = __DL__; private _P = __PL__; '
 'for "_j" from 0 to __NM1__ do { '
 '  private _dd = _D select _j; private _po = _P select _j; '
 '  private _p = [16000,16000,0]; '
 '  for "_i" from 0 to 60 do { _p = [] call BIS_fnc_randomPos; '
 '    if ((getTerrainHeightASL _p) > 5) exitWith {} }; '
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
 '  _s setVariable ["hc", _c]; '
 '  _s addEventHandler ["Fired", { params ["_u"]; HMT_T = HMT_T + 1; '
 '    format ["N1F %1", (_u getVariable ["hd", -1])] call HMT_EMIT; }]; '
 '  _c addEventHandler ["HitPart", { private _e = (_this select 0); '
 '    private _v = _e select 0; private _sh = _e select 1; private _pr = _e select 2; '
 '    if (isNull _v or isNull _sh) exitWith {}; '
 '    if (_sh != (_v getVariable ["hs", objNull])) exitWith {}; '
 '    if (_pr isEqualTo (_v getVariable ["hp", objNull])) exitWith {}; '
 '    _v setVariable ["hp", _pr]; '
 '    HMT_I = HMT_I + 1; '
 '    format ["N1I %1", (_v getVariable ["hd", -1])] call HMT_EMIT; }]; '
 '  _duels pushBack [_s, _c]; '
 '}; '
 'sleep 3; '
 '{ (_x select 0) reveal [(_x select 1), 4]; (_x select 0) setBehaviour "COMBAT"; '
 '  (_x select 0) setCombatMode "RED"; } forEach _duels; '
 'private _t0 = time; '
 'while { time - _t0 < __T__ } do { '
 '  { (_x select 0) doTarget (_x select 1); (_x select 0) doFire (_x select 1); } forEach _duels; '
 '  sleep 3; }; '
 'format ["N1END %1 %2 %3", HMT_T, HMT_I, count _duels] call HMT_EMIT; '
 '{ deleteVehicle (_x select 0); deleteVehicle (_x select 1); } forEach _duels; '
 '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; };'
).replace("__NM1__", str(NDUEL - 1)).replace("__T__", str(DUREE)) \
 .replace("__DL__", "[" + ",".join(str(d) for d, _ in COND) + "]") \
 .replace("__PL__", "[" + ",".join('"%s"' % p for _, p in COND) + "]")

tirs = collections.Counter(); imps = collections.Counter()
for k in range(BLOCS):
    n0 = len(b._log_lines(400000))
    try:
        r = b.query(SESSION, r"N1END (\d+) (\d+) (\d+)", want=1, timeout=DUREE + 120)
    except Exception as e:
        print("  bloc %d : PONT %s — bloc jete, on continue" % (k, type(e).__name__), flush=True)
        try:
            b = NativeBridge(port=PORT, timeout=20)
            print("    pont repris (compteur %d)" % b.counter, flush=True)
        except Exception:
            print("    pont IRRECUPERABLE — arret"); break
        continue
    if not r:
        print("  bloc %d : pas de fin — jete" % k, flush=True); continue
    nt, ni, nd = (int(r[0].group(i)) for i in (1, 2, 3))
    for s in b._log_lines(400000)[n0:]:
        m = re.match(r"N1F (-?\d+)$", s.strip())
        if m: tirs[int(m.group(1))] += 1
        m = re.match(r"N1I (-?\d+)$", s.strip())
        if m: imps[int(m.group(1))] += 1
    print("  bloc %d/%d : %d duels · %d balles · %d impacts (cumul %d balles)"
          % (k + 1, BLOCS, nd, nt, ni, sum(tirs.values())), flush=True)
    json.dump({"cond": COND, "tirs": dict(tirs), "imps": dict(imps)}, open(SORTIE, "w"))

def wilson(i, n):
    if n == 0: return (0.0, 0.0, 0.0)
    p = i / n
    if p > 1.0:
        return (p, float("nan"), float("nan"))   # impossible : le capteur sur-compte
    z = 1.96; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))

print("\n  " + "=" * 70)
i100 = 0
p, lo, hi = wilson(imps.get(i100, 0), tirs.get(i100, 0))
print("  (session dediee au 200 m ; le controle 100 m ne s applique pas) %.3f [%.3f;%.3f] n=%d"
      % (p, lo, hi, tirs.get(i100, 0)))
print("  cumul par posture a 200 m :")
for po in POST:
    js = [k for k, (d, q) in enumerate(COND) if q == po]
    nn = sum(tirs.get(k, 0) for k in js); ii = sum(imps.get(k, 0) for k in js)
    pp, lo2, hi2 = wilson(ii, nn)
    print("    %-8s %5d balles %5d impacts  %.3f [%.3f ; %.3f]  %s"
          % (po, nn, ii, pp, lo2, hi2, "RENDU" if nn >= 300 else "NON RENDU (n<300)"))
b.sock.close()
