#!/usr/bin/env python3
"""garrison_verify — fondation CQB : garnir NDEF defenseurs DANS les batiments (buildingPos) du complexe,
puis verifier combien sont INTUABLES depuis la ligne de suppression (LOS bloquee) -> prouve qu'il faut ENTRER."""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5801
NDEF = int(sys.argv[2]) if len(sys.argv) > 2 else 10
CX, CY = 20885, 16779
APPX, APPY = CX, CY - 90          # ligne de suppression (la squad s'arrete ~83-90m au sud)
b = SocketBridge(PORT)
time.sleep(1)
# nettoie d'eventuels defenseurs precedents
b.send('if (!isNil "CQB_DEF") then { { deleteVehicle _x } forEach CQB_DEF; }; CQB_DEF=[];')
time.sleep(0.5)
# garnit NDEF defenseurs aux buildingPos de batiments enterables proches de l'objectif
b.send('private _objs = (nearestObjects [[%d,%d,0], ["House","Building"], 110]) select { count (_x buildingPos -1) > 0 };'
       ' private _g = createGroup east; CQB_DEF=[];'
       ' for "_i" from 0 to %d do {'
       '   private _bld = _objs select (_i %% (count _objs));'
       '   private _poss = _bld buildingPos -1;'
       '   private _p = _poss select (_i %% (count _poss));'
       '   private _u = _g createUnit ["O_Soldier_F", _p, [], 0, "NONE"];'
       '   _u setPosATL _p; _u setDir (random 360); _u setUnitPos "UP";'
       '   _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u setSkill 0.5;'
       '   CQB_DEF pushBack _u;'
       ' };'
       ' diag_log format ["GARR placed=%%1 enterable_blds=%%2", count CQB_DEF, count _objs];' % (CX, CY, NDEF - 1))
time.sleep(1.5)
# verifie LOS depuis la ligne de suppression : combien de defenseurs sont intuables (mur entre)
b.send('private _eye = [%d,%d,0]; _eye set [2, (getTerrainHeightASL _eye) + 1.4];'
       ' private _blocked=0; private _inb=0;'
       ' { private _q = eyePos _x;'
       '   private _hit = lineIntersectsSurfaces [_eye, _q, objNull, _x];'
       '   if (count _hit > 0) then {_blocked=_blocked+1};'
       '   if (count (nearestObjects [getPosATL _x, ["House","Building"], 4]) > 0) then {_inb=_inb+1};'
       ' } forEach CQB_DEF;'
       ' diag_log format ["LOS blocked=%%1 inbld=%%2 total=%%3", _blocked, _inb, count CQB_DEF];' % (APPX, APPY))
time.sleep(1.5)


def grab(tag):
    for ln in reversed(b._log_lines(4000)):
        m = re.search(r"%s (.+)" % tag, ln)
        if m:
            return m.group(1).strip()
    return None


print(">>> GARNISON :", grab("GARR"), flush=True)
print(">>> LOS depuis ligne de suppression (~90m sud) :", grab("LOS"), flush=True)
print("   (blocked = intuables sans entrer ; inbld = dans un batiment)", flush=True)
print("GARRISON_VERIFY DONE", flush=True)
