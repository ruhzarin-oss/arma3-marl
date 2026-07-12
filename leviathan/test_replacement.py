#!/usr/bin/env python3
"""Valide EN LIVE le placement co-evolue : spawn menace -> replacement 2-clusters -> les defenseurs bougent."""
import sys, time, math
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import torch
CKV = "/home/younes/compose-embodiment/coevo_live.pt"; REAL_R = 42.0; FX, FY = 4279, 3856
b = NativeBridge(port=5816)
dmu = torch.load(CKV, map_location="cpu")["defender"]["mu"].view(2, 2).tanh().tolist()
b.query("[] spawn { HMT_TESTW=createGroup west; for \"_i\" from 0 to 4 do { HMT_TESTW createUnit [\"B_Soldier_F\",[%d,%d,0],[],5,\"FORM\"]; }; (format [\"HARMATTAN_SPAWN %%1\", count units HMT_TESTW]) call HMT_EMIT; };" % (FX, FY - 220), r"HARMATTAN_SPAWN (\d+)", want=1, timeout=15)
time.sleep(5)
rb = b.query("private _w=allUnits select {side _x==west && alive _x && _x distance [%d,%d,0]<450}; if (count _w==0) then {(format [\"HARMATTAN_BRG %%1\",-999]) call HMT_EMIT} else {private _sx=0;private _sy=0;{private _p=getPosATL _x;_sx=_sx+(_p select 0);_sy=_sy+(_p select 1)} forEach _w;_sx=_sx/(count _w);_sy=_sy/(count _w);(format [\"HARMATTAN_BRG %%1\",(_sx-%d) atan2 (_sy-%d)]) call HMT_EMIT};" % (FX, FY, FX, FY), r"HARMATTAN_BRG (-?[0-9.]+)", want=1, timeout=10)
brg = float(rb[-1].group(1)) if rb else -999.0
print("bearing menace = %.0f deg (attendu ~180 = sud)" % brg)
th = math.radians(brg); cls = []
for c in dmu:
    ox, oy = c[0] * REAL_R, c[1] * REAL_R
    ex = ox * math.cos(th) + oy * math.sin(th); ny = -ox * math.sin(th) + oy * math.cos(th)
    cls.append((FX + ex, FY + ny))
print("clusters monde =", [(round(x), round(y)) for x, y in cls])
def meandist():
    r = b.query("private _e=(allUnits select {side _x==east && alive _x && _x distance [%d,%d,0]<160}); private _s=0; { private _p=getPosATL _x; _s=_s+ ((_p distance2D [%.1f,%.1f]) min (_p distance2D [%.1f,%.1f])); } forEach _e; (format [\"HARMATTAN_MD %%1 %%2\", round(_s/((count _e) max 1)), count _e]) call HMT_EMIT;" % (FX, FY, cls[0][0], cls[0][1], cls[1][0], cls[1][1]), r"HARMATTAN_MD (\d+) (\d+)", want=1, timeout=10)
    return (int(r[-1].group(1)), int(r[-1].group(2))) if r else (None, None)
d0, n0 = meandist()
b.send("private _e=(allUnits select {side _x==east && alive _x && _x distance [%d,%d,0]<120}); { private _t=if ((_forEachIndex mod 2)==0) then {[%.1f,%.1f,0]} else {[%.1f,%.1f,0]}; _x setUnitPos \"AUTO\"; _x doMove _t; } forEach _e;" % (FX, FY, cls[0][0], cls[0][1], cls[1][0], cls[1][1]))
print("AVANT replacement : %s defenseurs, dist moyenne aux clusters = %sm" % (n0, d0))
time.sleep(25)
d1, n1 = meandist()
print("APRES 25s        : dist moyenne aux clusters = %sm" % d1)
verdict = "SE SONT RAPPROCHES du placement appris (OK)" if (d0 and d1 and d1 < d0 - 2) else "n ont pas converge"
print("=> les defenseurs %s" % verdict)
b.send("if (!isNil \"HMT_TESTW\") then { { deleteVehicle _x } forEach (units HMT_TESTW); HMT_TESTW=grpNull; };")
print("probe menace nettoye")
