"""TEST LIVE : LAMBS execute le bounding (capacite du mod) sur la defense de 12 (Stratis, server14).
Notre politique ne pilote PAS le bas-niveau ici : on donne a l escouade l IA LAMBS + un ordre d ASSAUT (SAD)
sur l objectif, et on mesure si LAMBS prend la position (gardes neutralises) en gardant des survivants.
=> demontre la CAPACITE (vrai feu-et-mouvement : couvert, bonds, suppression) que le mod apporte ; notre politique
   devient la couche COMMANDEMENT (quand/ou assaillir), cf le seam cerveau-tactique-abstrait."""
import os
os.environ.setdefault("HMT_MISSION", "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis")
os.environ.setdefault("HMT_LOG", "/mnt/data/harmattan-sandbox/logs/server14.out")
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
CX = 5569; CY = 4683
b = ArmaBridge()

SETUP = (r'''HMT_CX=__CX__; HMT_CY=__CY__;
if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR; };
if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS; };
if (!isNil "HMT_HOSTAGE") then { if (!isNull HMT_HOSTAGE) then { { deleteVehicle _x } forEach attachedObjects HMT_HOSTAGE; deleteVehicle HMT_HOSTAGE } };
HMT_HOSTAGE = "Land_Suitcase_F" createVehicle [HMT_CX,HMT_CY,0]; HMT_HOSTAGE setPosATL [HMT_CX,HMT_CY,0];
private _cl="Chemlight_green" createVehicle [0,0,0]; _cl attachTo [HMT_HOSTAGE,[0,0,0.4]];
private _ge = createGroup east; HMT_GUARDS=[]; private _nd=12;
for "_i" from 0 to (_nd-1) do { private _ang=_i*(360/_nd); private _r=if (_i % 2 == 0) then {20} else {38}; private _gx=HMT_CX+_r*sin _ang; private _gy=HMT_CY+_r*cos _ang;
  private _g = _ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"];
  _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; _g setSkill 0.5; HMT_GUARDS pushBack _g; };
private _gw = createGroup west; HMT_FR=[];
for "_i" from 0 to 7 do { private _sx=HMT_CX+((_i%2)*6-3); private _sy=HMT_CY-130-_i*6;
  private _s = _gw createUnit ["B_Soldier_F",[_sx,_sy,0],[],0,"NONE"];
  _s setPosATL [_sx,_sy,0]; _s allowDamage true; _s setSkill 0.55; HMT_FR pushBack _s; };
createMarker ["hmt_h",[HMT_CX,HMT_CY,0]]; "hmt_h" setMarkerType "hd_objective"; "hmt_h" setMarkerColor "ColorGreen"; "hmt_h" setMarkerText "COLIS";
{ _x allowDamage false; _x setCaptive true; if !(_x getVariable ["hmt_p",false]) then { _x setVariable ["hmt_p",true]; _x setPosATL [HMT_CX,HMT_CY-170,0]; _x setDir 0; ["LAMBS ASSAUT (Stratis). 8 bleus assaillent 12 gardes en feu-et-mouvement LAMBS."] remoteExec ["hint",_x]; }; } forEach allPlayers;
diag_log format ["HARMATTAN_ASETUP fr=%1 guards=%2", count HMT_FR, count HMT_GUARDS];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

# IA LAMBS complete + ordre ASSAUT (SAD) sur l objectif. LAMBS Danger.fsm -> bonds/couvert/suppression natifs.
ASSAULT = r'''
{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "AUTO"; } forEach HMT_FR;
private _grp = group (HMT_FR select 0);
while {count waypoints _grp > 0} do { deleteWaypoint ((waypoints _grp) select 0) };
private _wp = _grp addWaypoint [getPosATL HMT_HOSTAGE, 0];
_wp setWaypointType "SAD"; _wp setWaypointSpeed "NORMAL"; _wp setWaypointBehaviour "COMBAT"; _wp setWaypointCombatMode "RED";
_grp setCurrentWaypoint _wp;
if (!isNil "lambs_wp_fnc_taskAssault") then { [_grp, getPosATL HMT_HOSTAGE, 60] call lambs_wp_fnc_taskAssault; diag_log "HARMATTAN_LAMBS taskAssault"; };
diag_log "HARMATTAN_LAMBS_ASSAULT ordered";
'''

GSTAT = r'''diag_log format ["HARMATTAN_GSTAT galive=%1 alive=%2 dh=%3", ({alive _x} count HMT_GUARDS), ({alive _x} count HMT_FR), round (HMT_HOSTAGE distance2D (getPosATL (HMT_FR select 0)))];'''


def gstat(timeout=15):
    b.send(GSTAT, wait=True, timeout=timeout); time.sleep(0.4)
    for ln in reversed(b._log_lines()):
        m = re.search(r"HARMATTAN_GSTAT galive=(\d+) alive=(\d+) dh=(-?\d+)", ln)
        if m: return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None, None, None


print("=== LAMBS ASSAUT LIVE (Stratis, 12 gardes) : le mod execute le feu-et-mouvement ===", flush=True)
ep = 0
while True:
    ep += 1
    try:
        b.send(SETUP, wait=True, timeout=15); time.sleep(3.0)
        b.send(ASSAULT, wait=True, timeout=15); time.sleep(2.0)
        res = "timeout"; g0 = 12
        for t in range(40):
            g, a, dh = gstat(); time.sleep(2.3)
            if g is not None and t % 1 == 0:
                print("  ep%d t=%2d LAMBS-ASSAUT | gardes=%2d vivants=%d | chef->colis %dm" % (ep, t, g, a, dh), flush=True)
            if g is not None and g <= 1: res = "OBJECTIF PRIS par LAMBS (gardes neutralises)"; break
            if a is not None and a == 0: res = "escouade aneantie"; break
        print(">>> EP %d : %s (gardes restants %s, survivants %s)" % (ep, res, g, a), flush=True); time.sleep(6)
    except Exception as e:
        print("  ep%d ERREUR %s (retry)" % (ep, str(e)[:110]), flush=True); time.sleep(3)
