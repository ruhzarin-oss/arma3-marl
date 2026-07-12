"""Test de fiabilite du pont : query() corrélé doit TOUJOURS rendre 8 FPOS + un GSTAT frais (jamais None/figé)."""
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
private _ge = createGroup east; HMT_GUARDS=[];
for "_i" from 0 to 7 do { private _ang=_i*45; private _gx=HMT_CX+24*sin _ang; private _gy=HMT_CY+24*cos _ang;
  private _g=_ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"]; _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; HMT_GUARDS pushBack _g; };
private _gw = createGroup west; HMT_FR=[];
for "_i" from 0 to 7 do { private _sx=HMT_CX+((_i%2)*6-3); private _sy=HMT_CY-120-_i*6;
  private _s=_gw createUnit ["B_Soldier_F",[_sx,_sy,0],[],0,"NONE"]; _s setPosATL [_sx,_sy,0]; _s enableAI "MOVE"; _s enableAI "PATH"; HMT_FR pushBack _s; };
{ _x allowDamage false; _x setCaptive true; } forEach allPlayers;
diag_log format ["HARMATTAN_ASETUP fr=%1 guards=%2", count HMT_FR, count HMT_GUARDS];
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

MOVE = (r'''{ _x doMove [__CX__, __CY__, 0]; } forEach HMT_FR; diag_log "HARMATTAN_MOVE ordered";
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

FPOS = (r'''{ private _p=getPosATL _x; diag_log format ["HARMATTAN_FPOS %1 %2 %3", _forEachIndex, round((_p select 0)-__CX__), round((_p select 1)-__CY__)]; } forEach HMT_FR;
''').replace("__CX__", str(CX)).replace("__CY__", str(CY))

GSTAT = r'''diag_log format ["HARMATTAN_GSTAT galive=%1 alive=%2", ({alive _x} count HMT_GUARDS), ({alive _x} count HMT_FR)];'''

print("=== TEST FIABILITE PONT (query corrélé) ===", flush=True)
b.send(SETUP, wait=True, timeout=15); time.sleep(3)
b.send(MOVE, wait=True, timeout=15); time.sleep(1)
ok_fpos = ok_gstat = 0; prev_lead = None; moved = 0
for i in range(15):
    fp = b.query(FPOS, r"HARMATTAN_FPOS (\d+) (-?\d+) (-?\d+)", want=8, timeout=10)
    gs = b.query(GSTAT, r"HARMATTAN_GSTAT galive=(\d+) alive=(\d+)", want=1, timeout=10)
    pos = {int(m.group(1)): (float(m.group(2)), float(m.group(3))) for m in fp}
    lead = pos.get(0)
    g = (int(gs[0].group(1)), int(gs[0].group(2))) if gs else None
    if len(pos) >= 8: ok_fpos += 1
    if g is not None: ok_gstat += 1
    if lead and prev_lead and (abs(lead[0] - prev_lead[0]) + abs(lead[1] - prev_lead[1]) > 0.5): moved += 1
    prev_lead = lead
    print("  iter %2d | fpos=%d/8 leader=%s | gstat=%s" % (i, len(pos), ("(%.0f,%.0f)" % lead if lead else "MANQUE"), g), flush=True)
    time.sleep(1.2)
print(">>> BILAN : fpos complet %d/15 | gstat present %d/15 | leader a bouge %d fois (fraicheur)" % (ok_fpos, ok_gstat, moved), flush=True)
