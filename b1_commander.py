"""ARCHITECTURE COMMANDANT — incrément 1 : le SEAM (notre couche decide, LAMBS execute le corps).
Le commandant scinde l escouade en 2 elements : BASE DE FEU (cloue l objectif) + MANOEUVRE (contourne puis assaut).
Decision reelle : quel cote flanquer (le plus faible en gardes). Ordres traduits en taches LAMBS (le mod fait le
feu-et-mouvement : couvert, bonds, suppression). Stratis, server14+LAMBS. Mesure : objectif pris ? survivants ?
Incrément 2 (apres) : remplacer l heuristique par une politique RL apprise (le commandant appris)."""
import os
os.environ.setdefault("HMT_MISSION", "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanBridge14.Stratis")
os.environ.setdefault("HMT_LOG", "/mnt/data/harmattan-sandbox/logs/server14.out")
import sys, time, re, math
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge
CX = 5569; CY = 4683; NG = 8                       # 8 gardes (anneau) — gagnable par feu+manoeuvre
b = ArmaBridge()

SETUP = (r'''HMT_CX=__CX__; HMT_CY=__CY__; HMT_NG=__NG__;
if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR; };
if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS; };
if (!isNil "HMT_HOSTAGE") then { if (!isNull HMT_HOSTAGE) then { { deleteVehicle _x } forEach attachedObjects HMT_HOSTAGE; deleteVehicle HMT_HOSTAGE } };
HMT_HOSTAGE = "Land_Suitcase_F" createVehicle [HMT_CX,HMT_CY,0]; HMT_HOSTAGE setPosATL [HMT_CX,HMT_CY,0];
private _cl="Chemlight_green" createVehicle [0,0,0]; _cl attachTo [HMT_HOSTAGE,[0,0,0.4]];
private _ge = createGroup east; HMT_GUARDS=[];
for "_i" from 0 to (HMT_NG-1) do { private _ang=_i*(360/HMT_NG); private _r=24; private _gx=HMT_CX+_r*sin _ang; private _gy=HMT_CY+_r*cos _ang;
  private _g = _ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"];
  _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; _g setSkill 0.5; HMT_GUARDS pushBack _g; };
HMT_GA = createGroup west; HMT_GB = createGroup west; HMT_FR=[];        // GA=base de feu, GB=manoeuvre
for "_i" from 0 to 7 do { private _sx=HMT_CX+((_i%2)*6-3); private _sy=HMT_CY-120-_i*6;
  private _grp=if (_i<4) then {HMT_GA} else {HMT_GB};
  private _s = _grp createUnit ["B_Soldier_F",[_sx,_sy,0],[],0,"NONE"];
  _s setPosATL [_sx,_sy,0]; _s allowDamage true; _s setSkill 0.55; HMT_FR pushBack _s; };
createMarker ["hmt_h",[HMT_CX,HMT_CY,0]]; "hmt_h" setMarkerType "hd_objective"; "hmt_h" setMarkerColor "ColorGreen"; "hmt_h" setMarkerText "COLIS";
{ _x allowDamage false; _x setCaptive true; if !(_x getVariable ["hmt_p",false]) then { _x setVariable ["hmt_p",true]; _x setPosATL [HMT_CX,HMT_CY-150,0]; _x setDir 0; ["COMMANDANT (Stratis). Base de feu + element de manoeuvre qui contourne. LAMBS execute."] remoteExec ["hint",_x]; }; } forEach allPlayers;
diag_log format ["HARMATTAN_ASETUP fr=%1 guards=%2 ga=%3 gb=%4", count HMT_FR, count HMT_GUARDS, count units HMT_GA, count units HMT_GB];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY)).replace("__NG__", str(NG))

GPOS = (r'''HMT_CX=__CX__; HMT_CY=__CY__;
{ if (alive _x) then { private _q=getPosATL _x; diag_log format ["HARMATTAN_GUARD %1 %2 %3", _forEachIndex, (_q select 0)-HMT_CX, (_q select 1)-HMT_CY]; }; } forEach HMT_GUARDS;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

# ORDRE COMMANDANT : base de feu (GA) cloue l objectif ; manoeuvre (GB) contourne cote __SIDE__ puis assaut. LAMBS execute.
ORDER = (r'''HMT_CX=__CX__; HMT_CY=__CY__; private _side=__SIDE__;
// --- BASE DE FEU : tient un standoff et supprime l objectif ---
HMT_GA setBehaviour "COMBAT"; HMT_GA setCombatMode "RED"; { deleteWaypoint _x } forEach waypoints HMT_GA;
{ _x enableAI "ALL"; _x setUnitPos "MIDDLE"; _x doWatch HMT_HOSTAGE; } forEach units HMT_GA;
private _bp=[HMT_CX - _side*15, HMT_CY-95, 0]; private _wA=HMT_GA addWaypoint [_bp,0]; _wA setWaypointType "HOLD"; _wA setWaypointBehaviour "COMBAT"; _wA setWaypointCombatMode "RED"; HMT_GA setCurrentWaypoint _wA;
// --- MANOEUVRE : contourne cote _side puis SAD sur l objectif (LAMBS enrichit le bond/couvert) ---
HMT_GB setBehaviour "COMBAT"; HMT_GB setCombatMode "RED"; { deleteWaypoint _x } forEach waypoints HMT_GB;
{ _x enableAI "ALL"; _x setUnitPos "AUTO"; } forEach units HMT_GB;
private _fp=[HMT_CX + _side*75, HMT_CY-30, 0];
private _w1=HMT_GB addWaypoint [_fp,0]; _w1 setWaypointType "MOVE"; _w1 setWaypointSpeed "FULL"; _w1 setWaypointBehaviour "AWARE"; _w1 setWaypointCombatMode "YELLOW";
private _w2=HMT_GB addWaypoint [getPosATL HMT_HOSTAGE,0]; _w2 setWaypointType "SAD"; _w2 setWaypointBehaviour "COMBAT"; _w2 setWaypointCombatMode "RED";
HMT_GB setCurrentWaypoint _w1;
diag_log format ["HARMATTAN_CMD ordered side=%1 (1=droite,-1=gauche)", _side];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

# une fois l objectif degage : tout le monde converge + secure
ASSAULT_ALL = r'''{ deleteWaypoint _x } forEach (waypoints HMT_GA + waypoints HMT_GB);
{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; } forEach HMT_FR;
{ private _g=_x; private _w=_g addWaypoint [getPosATL HMT_HOSTAGE, 0]; _w setWaypointType "SAD"; _w setWaypointBehaviour "COMBAT"; _w setWaypointCombatMode "RED"; _g setCurrentWaypoint _w; } forEach [HMT_GA, HMT_GB];
diag_log "HARMATTAN_CMD assault_all";'''

GSTAT = r'''private _dmin=9999; { if (alive _x) then { private _d=_x distance2D HMT_HOSTAGE; if (_d<_dmin) then {_dmin=_d}; }; } forEach HMT_FR;
diag_log format ["HARMATTAN_GSTAT galive=%1 alive=%2 ga=%3 gb=%4 dh=%5", ({alive _x} count HMT_GUARDS), ({alive _x} count HMT_FR), ({alive _x} count units HMT_GA), ({alive _x} count units HMT_GB), round _dmin];'''


def read_guards(timeout=15):
    ms = b.query(GPOS, r"HARMATTAN_GUARD (\d+) (-?[\d.]+) (-?[\d.]+)", want=NG, timeout=timeout)
    g = {int(m.group(1)): [float(m.group(2)), float(m.group(3))] for m in ms}
    return list(g.values())


def gstat(timeout=15):
    ms = b.query(GSTAT, r"HARMATTAN_GSTAT galive=(\d+) alive=(\d+) ga=(\d+) gb=(\d+) dh=(-?\d+)", want=1, timeout=timeout)
    if not ms: return None
    m = ms[-1]
    return {"g": int(m.group(1)), "a": int(m.group(2)), "ga": int(m.group(3)), "gb": int(m.group(4)), "dh": int(m.group(5))}


def decide_side(guards):
    """COMMANDANT : flanquer le cote le plus FAIBLE (moins de gardes a l est qu a l ouest -> on prend l est)."""
    east = sum(1 for x, y in guards if x > 3); west = sum(1 for x, y in guards if x < -3)
    return 1 if east <= west else -1            # +1 = droite/est, -1 = gauche/ouest


print("=== COMMANDANT (incrément 1) : base de feu + manoeuvre, LAMBS execute. Stratis 8 gardes ===", flush=True)
ep = 0
while True:
    ep += 1
    try:
        b.send(SETUP, wait=True, timeout=15); time.sleep(3.0)
        guards = read_guards()
        side = decide_side(guards) if guards else 1
        print("  ep%d COMMANDANT : flanc %s (gardes lus=%d)" % (ep, "DROITE/est" if side > 0 else "GAUCHE/ouest", len(guards)), flush=True)
        b.send(ORDER.replace("__SIDE__", str(side)), wait=True, timeout=15); time.sleep(2.0)
        res = "timeout"; assault_sent = False
        for t in range(65):                                            # +de temps : l'assaut fermait la distance (97->44m) mais expirait
            st = gstat(); time.sleep(2.3)
            if st is None: continue
            if not assault_sent and (st["g"] <= NG // 2 or t >= 14):       # suppression+flanc etablis -> ASSAUT decisif
                b.send(ASSAULT_ALL, wait=True, timeout=12); assault_sent = True
                print("  ep%d t=%2d >> ASSAUT GENERAL (gardes=%d, t=%d)" % (ep, t, st["g"], t), flush=True)
            if t % 1 == 0: print("  ep%d t=%2d | gardes=%d | base_feu=%d manoeuvre=%d | +proche->colis %dm%s" % (ep, t, st["g"], st["ga"], st["gb"], st["dh"], "  [assaut]" if assault_sent else ""), flush=True)
            if st["dh"] < 14: res = "OBJECTIF ATTEINT — colis securise par la manoeuvre (commandant -> LAMBS)"; break  # mission = atteindre le colis (pas annihiler)
            if st["g"] == 0: res = "DEFENSE ANEANTIE (bonus)"; break
            if st["a"] == 0: res = "escouade aneantie"; break
        print(">>> EP %d : %s (gardes %s, survivants %s)" % (ep, res, st["g"] if st else "?", st["a"] if st else "?"), flush=True); time.sleep(6)
    except Exception as e:
        print("  ep%d ERREUR %s (retry)" % (ep, str(e)[:110]), flush=True); time.sleep(3)
