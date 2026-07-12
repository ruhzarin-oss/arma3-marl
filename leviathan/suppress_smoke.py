#!/usr/bin/env python3
"""suppress_smoke.py — SMOKE TEST de la SUPPRESSION (la porte avant tout run long).
Mini-scene : 1 tireur WEST commande (LAMBS actif) vs 1 ennemi LAMBS EAST, LOS claire, ~125 m.
Phase OFF (le tireur ne supprime pas) puis Phase ON (doSuppressiveFire). On mesure si le LAMBS se fait CLOUER :
  getSuppression monte ? il se met a couvert (unitPos DOWN) ? son tir baisse (ses munitions descendent moins vite) ?
Verdict GO/NO-GO. Leger : 1 requete/tick, pas de Qwen."""
import sys, time, ast, re
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

b = NativeBridge(port=5816)
SX, SY = 5569, 4683          # tireur WEST (LOS degagee verifiee)
EX, EY = 5569, 4738          # ennemi EAST (55 m nord, LOS claire)

SETUP = ('[] spawn { '
    'if (!isNil "HMT_SH") then { deleteVehicle HMT_SH }; if (!isNil "HMT_EN") then { deleteVehicle HMT_EN }; '
    'deleteMarker "sm_sh"; deleteMarker "sm_en"; '
    'private _gw = createGroup west; _gw createUnit ["B_soldier_F", [%d,%d,0], [], 0, "NONE"]; HMT_SH = (units _gw) select 0; '
    'HMT_SH setPosATL [%d,%d,0]; HMT_SH setSkill 0.7; HMT_SH setBehaviour "COMBAT"; HMT_SH setCombatMode "RED"; HMT_SH setUnitPos "UP"; '
    'HMT_SH disableAI "AUTOCOMBAT"; HMT_SH disableAI "AUTOTARGET"; HMT_SH disableAI "FSM"; '
    'private _ge = createGroup east; _ge createUnit ["O_Soldier_F", [%d,%d,0], [], 0, "NONE"]; HMT_EN = (units _ge) select 0; '
    'HMT_EN setPosATL [%d,%d,0]; HMT_EN setSkill 0.5; HMT_EN setBehaviour "COMBAT"; HMT_EN setCombatMode "RED"; HMT_EN setUnitPos "UP"; '
    'HMT_SH reveal [HMT_EN, 4]; HMT_EN reveal [HMT_SH, 4]; '
    'createMarker ["sm_sh", [%d,%d,0]]; "sm_sh" setMarkerType "mil_dot"; "sm_sh" setMarkerColor "ColorWEST"; "sm_sh" setMarkerText "TIREUR"; '
    'createMarker ["sm_en", [%d,%d,0]]; "sm_en" setMarkerType "mil_dot"; "sm_en" setMarkerColor "ColorEAST"; "sm_en" setMarkerText "CIBLE LAMBS"; '
    'private _los = !(terrainIntersectASL [(getPosASL HMT_SH) vectorAdd [0,0,1.5], (getPosASL HMT_EN) vectorAdd [0,0,1.5]]); '
    '(format ["HARMATTAN_SM ok los=%%1", _los]) call HMT_EMIT; };') % (SX, SY, SX, SY, EX, EY, EX, EY, SX, SY, EX, EY)

MEASURE = ('(format ["HARMATTAN_SMS sha=%1 ensup=%2 ena=%3 enpos=%4 shal=%5 enal=%6", '
    '(HMT_SH ammo currentWeapon HMT_SH), round((getSuppression HMT_EN)*100), (HMT_EN ammo currentWeapon HMT_EN), '
    'unitPos HMT_EN, alive HMT_SH, alive HMT_EN]) call HMT_EMIT;')
SUPPRESS = 'HMT_SH doSuppressiveFire (getPosATL HMT_EN); ' + MEASURE


def read(sqf, timeout=15):
    r = b.query(sqf, r"HARMATTAN_SMS sha=(\d+) ensup=(-?\d+) ena=(\d+) enpos=(\w+) shal=(\w+) enal=(\w+)", want=1, timeout=timeout)
    if not r: return None
    m = r[-1]
    return {"sha": int(m.group(1)), "ensup": max(0, int(m.group(2))), "ena": int(m.group(3)), "enpos": m.group(4), "shal": m.group(5) == "true", "enal": m.group(6) == "true"}


def main():
    rs = b.query(SETUP, r"HARMATTAN_SM ok los=(\w+)", want=1, timeout=20)
    print("=== SMOKE SUPPRESSION : tireur vs 1 LAMBS a 126m | %s ===" % (rs[-1].group(0) if rs else "?"), flush=True)
    time.sleep(4)
    off, on = [], []
    for t in range(24):
        phase = "OFF" if t < 8 else "ON "
        d = read(SUPPRESS if t >= 8 else MEASURE)
        if not d:
            time.sleep(1.3); continue
        (off if t < 8 else on).append(d)
        print("  t=%2d [%s] | tireur_muns=%2d | ENNEMI: suppr=%3d%% pos=%-6s muns=%2d | vivants sh=%s en=%s"
              % (t, phase, d["sha"], d["ensup"], d["enpos"], d["ena"], d["shal"], d["enal"]), flush=True)
        time.sleep(1.3)
    # verdict
    def ammo_drop(seq):
        return (seq[0]["ena"] - seq[-1]["ena"]) if len(seq) >= 2 else 0
    sup_off = sum(x["ensup"] for x in off) / max(1, len(off)); sup_on = sum(x["ensup"] for x in on) / max(1, len(on))
    down_on = sum(1 for x in on if x["enpos"] in ("DOWN", "MIDDLE")) / max(1, len(on))
    sh_fired = (off + on)[0]["sha"] - (off + on)[-1]["sha"] if (off + on) else 0
    print("=== VERDICT ===", flush=True)
    print("  tireur a-t-il TIRE (suppression ON) ? munitions consommees = %d" % sh_fired, flush=True)
    print("  ennemi SUPPRESSION moyenne : OFF %.0f%% -> ON %.0f%%" % (sup_off, sup_on), flush=True)
    print("  ennemi a couvert (DOWN/MIDDLE) pendant ON : %.0f%% du temps" % (100 * down_on), flush=True)
    print("  ennemi tir (munitions consommees) : OFF %d -> ON %d" % (ammo_drop(off), ammo_drop(on)), flush=True)
    bite = (sup_on > 15 and sup_on > sup_off + 5) or down_on > 0.3
    print("  >>> LA SUPPRESSION %s <<<" % ("MORD (GO)" if bite else "NE MORD PAS (NO-GO, regler CBA/LAMBS)"), flush=True)


if __name__ == "__main__":
    main()
