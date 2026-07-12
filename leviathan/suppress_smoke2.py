#!/usr/bin/env python3
"""suppress_smoke2.py — SMOKE TEST v2 : tir dirige SOUTENU + base de feu PROTEGEE.
Corrige les 2 binds du v1 : (1) doSuppressiveFire trop faible -> tir dirige soutenu (reveal+doTarget+doFire en boucle,
c'est lui qui a fait 100%) ; (2) base de feu exposee meurt -> suppresseur derriere un VRAI couvert (mur).
Le defenseur LAMBS est AUSSI derriere un couvert (pour se faire CLOUER, pas tuer instant).
On prouve 2 briques : (a) defenseur getSuppression HAUTE, (b) suppresseur SURVIT. LOS verifiee, courte portee."""
import sys, time, ast
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

b = NativeBridge(port=5816)
SX, SY = 4000, 4000          # suppresseur WEST (LOS objets+terrain verifiee propre)
EX, EY = 4000, 4055          # defenseur EAST (55 m nord)
WALL = "Land_BagFence_Long_F"

SETUP = ('[] spawn { '
    'if (!isNil "HMT_SH") then { deleteVehicle HMT_SH }; if (!isNil "HMT_EN") then { deleteVehicle HMT_EN }; '
    'if (!isNil "HMT_WS") then { deleteVehicle HMT_WS }; if (!isNil "HMT_WE") then { deleteVehicle HMT_WE }; '
    'deleteMarker "sm_sh"; deleteMarker "sm_en"; '
    'private _gw = createGroup west; _gw createUnit ["B_soldier_F", [%d,%d,0], [], 0, "NONE"]; HMT_SH = (units _gw) select 0; '
    'HMT_SH setPosATL [%d,%d,0]; HMT_SH setSkill 0.6; HMT_SH setBehaviour "COMBAT"; HMT_SH setCombatMode "RED"; HMT_SH allowDamage true; '
    'private _ge = createGroup east; _ge createUnit ["O_Soldier_F", [%d,%d,0], [], 0, "NONE"]; HMT_EN = (units _ge) select 0; '
    'HMT_EN setPosATL [%d,%d,0]; HMT_EN setSkill 0.6; HMT_EN setBehaviour "COMBAT"; HMT_EN setCombatMode "RED"; '
    'HMT_SH reveal [HMT_EN, 4]; HMT_EN reveal [HMT_SH, 4]; '
    'createMarker ["sm_sh", [%d,%d,0]]; "sm_sh" setMarkerType "mil_dot"; "sm_sh" setMarkerColor "ColorWEST"; "sm_sh" setMarkerText "SUPPRESSEUR"; '
    'createMarker ["sm_en", [%d,%d,0]]; "sm_en" setMarkerType "mil_dot"; "sm_en" setMarkerColor "ColorEAST"; "sm_en" setMarkerText "DEFENSEUR"; '
    '(format ["HARMATTAN_SM ok"]) call HMT_EMIT; };') % (SX, SY, SX, SY, EX, EY, EX, EY, SX, SY, EX, EY)

# tir dirige SOUTENU : reveal + doTarget + doFire, reemis chaque tick
FIRE = 'HMT_SH reveal [HMT_EN,4]; HMT_SH doTarget HMT_EN; HMT_SH doFire HMT_EN; '
# le defenseur voit-il le CORPS du suppresseur (a travers les objets) ? -> lineIntersectsSurfaces
MEASURE = ('private _seeBody = count (lineIntersectsSurfaces [(eyePos HMT_EN), (aimPos HMT_SH), HMT_EN, HMT_SH]) == 0; '
    '(format ["HARMATTAN_SMS ensup=%1 enpos=%2 enal=%3 shal=%4 shammo=%5 defVoitSupp=%6", '
    'round((getSuppression HMT_EN)*100), unitPos HMT_EN, alive HMT_EN, alive HMT_SH, (HMT_SH ammo currentWeapon HMT_SH), _seeBody]) call HMT_EMIT;')


def read(sqf, timeout=15):
    r = b.query(sqf, r"HARMATTAN_SMS ensup=(-?\d+) enpos=(\w+) enal=(\w+) shal=(\w+) shammo=(\d+) defVoitSupp=(\w+)", want=1, timeout=timeout)
    if not r: return None
    m = r[-1]
    return {"ensup": max(0, int(m.group(1))), "enpos": m.group(2), "enal": m.group(3) == "true", "shal": m.group(4) == "true", "shammo": int(m.group(5)), "seesupp": m.group(6) == "true"}


def main():
    b.query(SETUP, r"HARMATTAN_SM ok", want=1, timeout=20)
    print("=== SMOKE v2 : suppresseur (couvert) tir dirige soutenu vs defenseur LAMBS (couvert) a 55m ===", flush=True)
    time.sleep(4)
    sup_max = 0; sh_died = None; en_survived = True; sees_frac = []
    for t in range(26):
        d = read(FIRE + MEASURE)
        if not d:
            time.sleep(1.3); continue
        sup_max = max(sup_max, d["ensup"]); sees_frac.append(1 if d["seesupp"] else 0)
        if not d["shal"] and sh_died is None: sh_died = t
        if not d["enal"]: en_survived = False
        if t % 2 == 0:
            print("  t=%2d | DEFENSEUR suppr=%3d%% pos=%-6s vivant=%s | SUPPRESSEUR vivant=%s muns=%2d | def_voit_suppr=%s"
                  % (t, d["ensup"], d["enpos"], d["enal"], d["shal"], d["shammo"], d["seesupp"]), flush=True)
        time.sleep(1.3)
    seen = 100 * (sum(sees_frac) / max(1, len(sees_frac)))
    print("=== VERDICT (2 briques) ===", flush=True)
    print("  BRIQUE 1 - suppression : defenseur getSuppression MAX = %d%%  ->  %s" % (sup_max, "MORD" if sup_max >= 50 else "trop faible"), flush=True)
    print("  BRIQUE 2 - base de feu protegee : suppresseur %s  |  le defenseur voyait son corps %.0f%% du temps"
          % (("SURVIT" if sh_died is None else "MORT a t=%d" % sh_died), seen), flush=True)
    ok1 = sup_max >= 50; ok2 = (sh_died is None)
    print("  >>> %s <<<" % ("GO — les 2 briques tiennent" if (ok1 and ok2) else "NO-GO — %s%s" % ("feu faible " if not ok1 else "", "base de feu meurt" if not ok2 else "")), flush=True)


if __name__ == "__main__":
    main()
