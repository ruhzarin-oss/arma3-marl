#!/usr/bin/env python3
"""duel_5v3.py — diagnostic combat elementaire. 5 coquilles WEST (003, corps LAMBS enableAI ALL) vs 3 LAMBS EAST,
60m, terrain decouvert, LOS claire, zone nettoyee. Question : une coquille sait-elle TUER ?"""
import sys, time, ast
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

CX, CY = 5569, 4704          # centre (zone LOS-claire validee)
WX, WY = 5569, 4683          # WEST (5)
EX, EY = 5569, 4725          # EAST (3), ~42m nord (LOS franche)
LOAD003 = "/home/younes/Bureau/003.ar"
b = NativeBridge(port=5816)
try: L = str(ast.literal_eval(open(LOAD003).read().strip())[0]).replace("'", '"')
except Exception: L = None
setl = ("{ _x setUnitLoadout %s } forEach HMT_DW; " % L) if L else ""

SETUP = ("[] spawn { "
    "{ deleteVehicle _x } forEach (nearestObjects [[%d,%d,0],[\"Man\"],350] select { side _x != west }); " % (CX, CY) +
    "if (!isNil \"HMT_DW\") then { {deleteVehicle _x} forEach HMT_DW }; if (!isNil \"HMT_DE\") then { {deleteVehicle _x} forEach HMT_DE }; "
    "private _gw=createGroup west; HMT_DW=[]; for \"_i\" from 0 to 4 do { private _u=_gw createUnit [\"B_soldier_F\",[%d+(_i*4)-8,%d,0],[],0,\"NONE\"]; _u setPosATL [%d+(_i*4)-8,%d,0]; _u allowDamage false; _u setSkill 0.7; _u enableAI \"ALL\"; _u setBehaviour \"AWARE\"; _u setCombatMode \"RED\"; HMT_DW pushBack _u; }; " % (WX, WY, WX, WY) +
    setl +
    "private _ge=createGroup east; HMT_DE=[]; for \"_i\" from 0 to 2 do { private _u=_ge createUnit [\"O_Soldier_F\",[%d+(_i*4)-4,%d,0],[],0,\"NONE\"]; _u setPosATL [%d+(_i*4)-4,%d,0]; _u setSkill 0.7; _u setBehaviour \"AWARE\"; _u setCombatMode \"RED\"; HMT_DE pushBack _u; }; " % (EX, EY, EX, EY) +
    "{ _x allowDamage true } forEach HMT_DW; "
    "{ _x enableSimulation true; _x enableDynamicSimulation false } forEach (HMT_DW+HMT_DE); "
    "{ private _u=_x; { _u reveal [_x,4] } forEach HMT_DE } forEach HMT_DW; { private _u=_x; { _u reveal [_x,4] } forEach HMT_DW } forEach HMT_DE; "
    "(format [\"HARMATTAN_DUEL w=%1 e=%2\", count HMT_DW, count HMT_DE]) call HMT_EMIT; };")

MEASURE = "(format [\"HARMATTAN_DM w=%1 e=%2 wammo=%3 players=%4\", {alive _x} count HMT_DW, {alive _x} count HMT_DE, (HMT_DW#0) ammo primaryWeapon (HMT_DW#0), count allPlayers]) call HMT_EMIT;"

r = b.query(SETUP, r"HARMATTAN_DUEL w=(\d+) e=(\d+)", want=1, timeout=20)
print("=== DUEL : 5 coquilles WEST (003) vs 3 LAMBS EAST | 60m decouvert ===")
print("  place : WEST=%s EAST=%s" % (r[-1].group(1), r[-1].group(2)) if r else "?")
time.sleep(3)
for t in range(22):
    rr = b.query(MEASURE, r"HARMATTAN_DM w=(\d+) e=(\d+) wammo=(\d+) players=(\d+)", want=1, timeout=12)
    if not rr: time.sleep(1.3); continue
    m = rr[-1]; w = int(m.group(1)); e = int(m.group(2)); wammo = int(m.group(3)); pl = int(m.group(4))
    print("  t=%2d | WEST vivantes=%d/5 (muns coquille#0=%d) | EAST vivants=%d/3 | joueurs=%d" % (t, w, wammo, e, pl))
    if e == 0: print("  >>> les coquilles NETTOYENT les 3 LAMBS -> le corps SAIT tuer."); break
    if w == 0: print("  >>> les 5 coquilles MORTES sans finir -> corps trop faible."); break
    time.sleep(1.3)
print("=== fin duel ===")
