#!/usr/bin/env python3
"""spawn_lambs_fob.py — pose un FOB ennemi LAMBS : ~50 soldats EAST (3 groupes garnison + 2 patrouilles en ronde)
autour d'un FOB (sacs + drapeau). LAMBS_Danger (serverMod) gouverne leur IA. Devient la cible de la chaine BLUFOR."""
import sys, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

b = NativeBridge(port=5816)


def build(fx, fy):
    return ('[] spawn { '
        'HMT_FX=' + str(fx) + '; HMT_FY=' + str(fy) + '; '
        'if (!isNil "HMT_LAMBS") then { { { deleteVehicle _x } forEach (units _x) } forEach HMT_LAMBS }; '
        'if (!isNil "HMT_FOBOBJ") then { { deleteVehicle _x } forEach HMT_FOBOBJ }; '
        'HMT_LAMBS=[]; HMT_FOBOBJ=[]; '
        # --- structures FOB : 4 murets de sacs + drapeau ---
        '{ private _o = createVehicle ["Land_BagFence_Long_F", _x, [], 0, "CAN_COLLIDE"]; _o setDir (random 360); HMT_FOBOBJ pushBack _o } forEach [[HMT_FX+9,HMT_FY,0],[HMT_FX-9,HMT_FY,0],[HMT_FX,HMT_FY+9,0],[HMT_FX,HMT_FY-9,0]]; '
        'private _flag = createVehicle ["Flag_Red_F", [HMT_FX,HMT_FY,0], [], 0, "CAN_COLLIDE"]; HMT_FOBOBJ pushBack _flag; '
        # --- GARNISON : 3 groupes de 10 qui tiennent le FOB (rayon 15-33 m) ---
        'for "_gi" from 0 to 4 do { private _gg = createGroup east; HMT_LAMBS pushBack _gg; '
        'for "_i" from 0 to 9 do { private _idx=_gi*10+_i; private _a=_idx*12; private _r=15+(random 18); private _p=[HMT_FX+_r*sin _a, HMT_FY+_r*cos _a, 0]; '
        'private _u=_gg createUnit ["O_Soldier_F", _p, [], 0, "NONE"]; _u setPosATL _p; _u allowDamage false; _u setSkill 0.5; _u setBehaviour "AWARE"; _u setCombatMode "YELLOW"; _u setDir _a; _u disableAI "PATH"; }; }; '
        # --- PATROUILLES : 2 groupes de 10 en ronde CYCLE autour du FOB (rayon 90 m) ---
        'for "_pg" from 0 to 2 do { private _g = createGroup east; HMT_LAMBS pushBack _g; private _b0=_pg*180; '
        'for "_j" from 0 to 9 do { private _sp=[HMT_FX+90*sin _b0+(random 14)-7, HMT_FY+90*cos _b0+(random 14)-7, 0]; '
        'private _u=_g createUnit ["O_Soldier_F", _sp, [], 0, "NONE"]; _u setPosATL _sp; _u allowDamage false; _u setSkill 0.5; }; '
        'for "_w" from 0 to 3 do { private _ang=_b0+_w*90; private _wp=_g addWaypoint [[HMT_FX+90*sin _ang, HMT_FY+90*cos _ang, 0], 0]; _wp setWaypointType "MOVE"; _wp setWaypointBehaviour "SAFE"; _wp setWaypointSpeed "LIMITED"; }; '
        'private _wc=_g addWaypoint [[HMT_FX+90*sin _b0, HMT_FY+90*cos _b0, 0], 0]; _wc setWaypointType "CYCLE"; { _x setBehaviour "SAFE" } forEach units _g; }; '
        # marqueur + reveil + reactive les degats
        'deleteMarker "lambs_fob"; createMarker ["lambs_fob", [HMT_FX,HMT_FY,0]]; "lambs_fob" setMarkerType "o_installation"; "lambs_fob" setMarkerColor "ColorEAST"; "lambs_fob" setMarkerText "FOB LAMBS"; '
        '{ { _x enableSimulation true; _x enableDynamicSimulation false; _x allowDamage true } forEach (units _x) } forEach HMT_LAMBS; '
        'private _n=0; { _n=_n+(count units _x) } forEach HMT_LAMBS; '
        '(format ["HARMATTAN_LAMBS soldats=%1 groupes=%2 structures=%3", _n, count HMT_LAMBS, count HMT_FOBOBJ]) call HMT_EMIT; '
        '};')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fob", default="3253,2984"); a = ap.parse_args()
    fx, fy = [int(v) for v in a.fob.split(",")]
    r = b.query(build(fx, fy), r"HARMATTAN_LAMBS soldats=(\d+) groupes=(\d+) structures=(\d+)", want=1, timeout=45)
    if r:
        m = r[-1]
        print("=== FOB LAMBS EN PLACE [%d,%d] ===" % (fx, fy))
        print("  soldats EAST : %s | groupes : %s (3 garnison + 2 patrouilles) | structures : %s" % (m.group(1), m.group(2), m.group(3)))
        print("  marqueur 'FOB LAMBS' sur la carte. LAMBS gouverne l'IA (patrouille + defense).")
        print("  NB : ils patrouillent/combattent VRAIMENT quand un joueur est connecte (IA inerte a 0 joueur).")
    else:
        print("pas de reponse du pont")


if __name__ == "__main__":
    main()
