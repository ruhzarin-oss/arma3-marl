#!/usr/bin/env python3
"""blufor_lambs.py — EXECUTEUR CORRIGE (facon LAMBS taskRush) : le moteur garde le TIR.
Mouvement par doMove (cycle facon taskRush), plus de setVelocity. Test : les coquilles AVANCENT et TUENT enfin.
On regarde 'LAMBS EAST vivants' baisser (kills) et 'coquilles' avancer/survivre. setup / run / disarm."""
import sys, time, ast, math, re, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

LOAD003 = "/home/younes/Bureau/003.ar"
NAG = 80


def loadout003():
    try: return str(ast.literal_eval(open(LOAD003).read().strip())[0]).replace("'", '"')
    except Exception: return None


def setup_sqf(sx, sy, ld):
    setl = ("{ _x setUnitLoadout %s } forEach HMT_WPILOT; " % ld) if ld else ""
    loop = ("private _try=0; while { count HMT_WPILOT < %d && _try < 500 } do { _try=_try+1; "
            "if ((count HMT_WPILOT) mod 10 == 0) then { HMT_WG = createGroup west }; "
            "private _px=%d+(random 70)-35; private _py=%d-(random 50); "
            "private _u = HMT_WG createUnit [\"B_soldier_F\",[_px,_py,0],[],0,\"NONE\"]; "
            "if (!isNull _u) then { _u allowDamage false; _u setPosATL [_px,_py,0]; _u setSkill 0.7; HMT_WPILOT pushBack _u }; }; ") % (NAG, sx, sy)
    return ("[] spawn { "
        "if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[]; "
        + loop + setl + "call HMT_WARM; { if (!isNull _x) then { _x allowDamage true } } forEach HMT_WPILOT; "
        "(format [\"HARMATTAN_WL west=%1 mode=%2 essais=%3\", count HMT_WPILOT, HMT_WAGENT_MODE, _try]) call HMT_EMIT; };")


def parse(payload):
    m = re.search(r"east=(\d+)", payload); east = int(m.group(1)) if m else -1
    left, _, right = payload.partition("|")
    shells = []
    for tok in right.strip().rstrip(";").split(";"):
        f = tok.split(",")
        if len(f) >= 4:
            try: shells.append([int(f[0]), int(f[1]), int(f[2]), int(f[3])])
            except ValueError: pass
    men = re.search(r"en=(\[.*\])", left)
    try: enemies = ast.literal_eval(men.group(1)) if men else []
    except Exception: enemies = []
    return shells, enemies, east


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["setup", "run", "disarm"])
    ap.add_argument("--fob", default="3253,2984"); ap.add_argument("--steps", type=int, default=40)
    a = ap.parse_args()
    fx, fy = [int(v) for v in a.fob.split(",")]; sx, sy = fx, fy + 200
    b = NativeBridge(port=5816)

    if a.cmd == "setup":
        b.send('call compile preprocessFileLineNumbers "blufor_coquille_lambs.sqf";'); time.sleep(0.5)
        ld = loadout003()
        r = b.query(setup_sqf(sx, sy, ld), r"HARMATTAN_WL west=(\d+) mode=(\w+) essais=(\d+)", want=1, timeout=120)
        if r:
            print("EXECUTEUR LAMBS en place : coquilles=%s/%d arme=%s (essais %s) | loadout 003=%s" % (r[-1].group(1), NAG, r[-1].group(2), r[-1].group(3), "ok" if ld else "defaut"))
        else:
            print("setup : pas de reponse")
        return

    if a.cmd == "disarm":
        b.query("call HMT_WDISARM;", r"HARMATTAN_WDISARM ok", want=1, timeout=15)
        b.send("if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[];")
        print("desarme + nettoye"); return

    # run : reveal mutuel + doMove vers le FOB (cycle facon taskRush). Le MOTEUR tire.
    b.send("private _es = allUnits select {side _x==east && alive _x}; "
           "{ private _e=_x; { _e reveal [_x,3] } forEach HMT_WPILOT } forEach _es; "
           "{ private _w=_x; { _w reveal [_x,3] } forEach _es } forEach HMT_WPILOT;")
    time.sleep(1)
    east0 = None
    print("=== ASSAUT executeur LAMBS -> FOB [%d,%d] (le moteur tire, doMove) ===" % (fx, fy), flush=True)
    for step in range(a.steps):
        r = b.query("call HMT_WREAD;", r"HARMATTAN_WRX (.+)", want=1, timeout=12)
        if not r: time.sleep(1); continue
        shells, enemies, east = parse(r[-1].group(1))
        if east0 is None: east0 = east
        # taskRush (LAMBS natif) pilote le mouvement + le feu ; on ne fait que revthe/observer
        alive = sum(1 for s in shells if len(s) >= 4 and s[3] == 1)
        pen = min((math.hypot(s[0]-fx, s[1]-fy) for s in shells if len(s) >= 4 and s[3] == 1), default=999)
        print("  [%02d] coquilles=%d/%d | ->FOB=%3.0fm | LAMBS EAST vivants=%d (depart %s) | detectes=%d"
              % (step, alive, NAG, pen, east, east0, len(enemies)), flush=True)
        if alive == 0: print("  -> escouade aneantie"); break
        if pen < 25: print("  -> FOB ATTEINT"); break
        time.sleep(1.3)
    print("=== fin run ===", flush=True)


if __name__ == "__main__":
    main()
