#!/usr/bin/env python3
"""hostage_fob.py — SAUVETAGE OTAGE en live sur server_fob (pont NATIF, fiable). Porte b1_hostage_stratis.py :
la politique d6 hostage_v1_FINAL.pt fait l'infil+recup+assaut (appris) ; FIX EXFIL = une fois l'otage pris,
le PORTEUR file droit a l'EXFIL a pleine vitesse (plancher scripte minimal). Emit via HMT_EMIT (pont natif)."""
import sys, time, ast, argparse, torch
sys.path.insert(0, "/home/younes/compose-embodiment")
from train_koth_gpu import Net
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

DEV = "cpu"; CX = 5569; CY = 4683
b = NativeBridge(port=5816)

SETUP = ('[] spawn { HMT_CX=%d; HMT_CY=%d; HMT_PICKED=0; '
  'if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR; }; '
  'if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS; }; '
  'if (!isNil "HMT_HOSTAGE") then { if (!isNull HMT_HOSTAGE) then { { deleteVehicle _x } forEach attachedObjects HMT_HOSTAGE; deleteVehicle HMT_HOSTAGE } }; '
  'deleteMarker "hmt_h"; deleteMarker "hmt_ext"; HMT_EXT = [HMT_CX, HMT_CY-140, 0]; '
  'private _ghg = createGroup west; _ghg createUnit ["B_Soldier_F",[HMT_CX,HMT_CY,0],[],0,"NONE"]; '
  'HMT_HOSTAGE = (units _ghg) select (count (units _ghg)-1); '
  'HMT_HOSTAGE setPosATL [HMT_CX,HMT_CY,0]; HMT_HOSTAGE setCaptive true; { HMT_HOSTAGE disableAI _x } forEach ["MOVE","PATH","FSM","TARGET","AUTOTARGET","AUTOCOMBAT"]; HMT_HOSTAGE setUnitPos "MIDDLE"; '
  'private _cl = "Chemlight_green" createVehicle [0,0,0]; _cl attachTo [HMT_HOSTAGE,[0,0,1.2]]; '
  'private _ge = createGroup east; HMT_GUARDS=[]; private _nd=6; '
  'for "_i" from 0 to (_nd-1) do { private _ang=_i*(360/_nd); private _gx=HMT_CX+30*sin _ang; private _gy=HMT_CY+30*cos _ang; '
  '  _ge createUnit ["O_Soldier_F",[_gx,_gy,0],[],0,"NONE"]; private _g=(units _ge) select (count (units _ge)-1); '
  '  _g setPosATL [_gx,_gy,0]; _g setBehaviour "COMBAT"; _g setCombatMode "RED"; HMT_GUARDS pushBack _g; }; '
  'private _gw = createGroup west; HMT_FR=[]; '
  'for "_i" from 0 to 8 do { private _sx=HMT_CX-30+(_i%%3)*30; private _sy=HMT_CY-120-(floor(_i/3))*12; '
  '  _gw createUnit ["B_Soldier_F",[_sx,_sy,0],[],0,"NONE"]; private _s=(units _gw) select (count (units _gw)-1); '
  '  _s setPosATL [_sx,_sy,0]; _s allowDamage true; '
  '  { _s enableAI _x } forEach ["MOVE","PATH","TARGET","AUTOTARGET"]; _s disableAI "AUTOCOMBAT"; _s disableAI "FSM"; _s setBehaviour "AWARE"; _s setSpeedMode "FULL"; _s forceSpeed -1; _s setUnitPos "AUTO"; '
  '  HMT_FR pushBack _s; }; '
  'createMarker ["hmt_h",[HMT_CX,HMT_CY,0]]; "hmt_h" setMarkerType "hd_objective"; "hmt_h" setMarkerColor "ColorGreen"; "hmt_h" setMarkerText "OTAGE"; '
  'createMarker ["hmt_ext",HMT_EXT]; "hmt_ext" setMarkerType "hd_objective"; "hmt_ext" setMarkerColor "ColorBlue"; "hmt_ext" setMarkerText "EXFIL"; '
  '(format ["HARMATTAN_SETUP fr=%%1 guards=%%2", count HMT_FR, count HMT_GUARDS]) call HMT_EMIT; };') % (CX, CY)

PERC = ('HMT_S=140; private _all=[]; '
  '{ private _u=_x; private _p=getPosATL _u; private _ax=(_p select 0)-HMT_CX; private _ay=(_p select 1)-HMT_CY; '
  '  private _hp=getPosATL HMT_HOSTAGE; private _hx=(_hp select 0)-HMT_CX; private _hy=(_hp select 1)-HMT_CY; '
  '  private _dhx=_hx-_ax; private _dhy=_hy-_ay; private _dh=sqrt(_dhx*_dhx+_dhy*_dhy)+0.001; '
  '  private _ex=(HMT_EXT select 0)-HMT_CX-_ax; private _ey=(HMT_EXT select 1)-HMT_CY-_ay; private _de=sqrt(_ex*_ex+_ey*_ey)+0.001; '
  '  private _ng=objNull; private _ndd=1e9; { if (alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_ndd) then {_ndd=_d;_ng=_x}; }; } forEach HMT_GUARDS; '
  '  private _gdx=0; private _gdy=0; private _gd=1; private _los=0; '
  '  if (!isNull _ng) then { private _q=getPosATL _ng; _gdx=((_q select 0)-HMT_CX)-_ax; _gdy=((_q select 1)-HMT_CY)-_ay; _gd=sqrt(_gdx*_gdx+_gdy*_gdy)+0.001; '
  '     private _gp=getPosASL _ng; private _aps=getPosASL _u; _los=if (terrainIntersectASL [[(_aps select 0),(_aps select 1),(_aps select 2)+0.9],[(_gp select 0),(_gp select 1),(_gp select 2)+0.9]]) then {0} else {1}; }; '
  '  private _nt=objNull; private _td=1e9; { if (_x!=_u && alive _x) then { private _q=getPosATL _x; private _ddx=((_q select 0)-HMT_CX)-_ax; private _ddy=((_q select 1)-HMT_CY)-_ay; private _d=_ddx*_ddx+_ddy*_ddy; if (_d<_td) then {_td=_d;_nt=_x}; }; } forEach HMT_FR; '
  '  private _tdx=0; private _tdy=0; private _tdist=1; '
  '  if (!isNull _nt) then { private _q=getPosATL _nt; _tdx=((_q select 0)-HMT_CX)-_ax; _tdy=((_q select 1)-HMT_CY)-_ay; _tdist=sqrt(_tdx*_tdx+_tdy*_tdy)+0.001; }; '
  '  private _th0=if (!isNull _ng) then { _gdy atan2 _gdx } else {0}; private _shell=[]; '
  '  for "_k" from 0 to 11 do { private _ang=_th0+_k*30; private _ddx=cos _ang; private _ddy=sin _ang; private _sv=1; '
  '     for "_s" from 1 to 20 do { private _r=_s/20*60; private _qx=(_p select 0)+_r*_ddx; private _qy=(_p select 1)+_r*_ddy; '
  '        if (count (nearestObjects [[_qx,_qy,(_p select 2)],["House","Wall","Rock"],3])>0) exitWith {_sv=_s/20}; }; '
  '     _shell pushBack _sv; }; '
  '  private _dmg=damage _u; private _pk=if (isNil "HMT_PICKED") then {0} else {HMT_PICKED}; '
  '  private _o=_shell+[_dmg,_dhx/_dh,_dhy/_dh,(_dh/HMT_S) min 2,_ex/_de,_ey/_de,(_de/HMT_S) min 2,_gdx/_gd,_gdy/_gd,(_gd/HMT_S) min 2,_los,_tdx/_tdist,_tdy/_tdist,(_tdist/HMT_S) min 2,_pk,damage HMT_HOSTAGE,_dmg]; '
  '  _all pushBack _o; } forEach HMT_FR; '
  '(format ["HARMATTAN_AOBS %1", _all]) call HMT_EMIT;')

ACT_TPL = ('HMT_ACT = [%s]; '
  '{ private _i=_forEachIndex; private _a=HMT_ACT select _i; private _p=getPosATL _x; '
  '  if (_a < 8) then { private _ang=_a*45; _x doMove [(_p select 0)+40*sin _ang, (_p select 1)+40*cos _ang, 0]; } else { _x doMove (getPosATL _x); }; } forEach HMT_FR; '
  'private _car=objNull; private _cd=1e9; { if (alive _x) then { private _d=_x distance2D HMT_HOSTAGE; if (_d<_cd) then {_cd=_d;_car=_x}; }; } forEach HMT_FR; '
  'if (HMT_PICKED==0 && !isNull _car && _cd<50) then { _car setSpeedMode "FULL"; _car forceSpeed -1; _car doMove (getPosATL HMT_HOSTAGE); }; '
  'if (_cd < 25) then { HMT_PICKED=1; }; '
  'if (HMT_PICKED==1 && !isNull _car) then { HMT_HOSTAGE setPosATL (getPosATL _car); '
  '  { _x setSpeedMode "FULL"; _x forceSpeed -1; _x doMove [(HMT_EXT select 0),(HMT_EXT select 1),0]; } forEach (HMT_FR select {alive _x}); }; '
  'private _dex=HMT_HOSTAGE distance2D [(HMT_EXT select 0),(HMT_EXT select 1),0]; '
  'private _succ=if (HMT_PICKED==1 && _dex<25) then {1} else {0}; '
  '(format ["HARMATTAN_STATUS picked=%%1 succ=%%2 dh=%%3 dex=%%4 alive=%%5", HMT_PICKED, _succ, round _cd, round _dex, ({alive _x} count HMT_FR)]) call HMT_EMIT;')

SMOKE = '"SmokeShellGreen" createVehicle (getPosATL HMT_HOSTAGE);'


def read_aobs(timeout=12):
    r = b.query(PERC, r"HARMATTAN_AOBS (\[.*\])", want=1, timeout=timeout)
    if not r: return None
    try: arr = ast.literal_eval(r[-1].group(1))
    except Exception: return None
    return torch.tensor(arr, dtype=torch.float32) if arr else None


def send_act(acts, timeout=12):
    sqf = ACT_TPL % ",".join(str(int(a)) for a in acts)
    r = b.query(sqf, r"HARMATTAN_STATUS picked=(\d+) succ=(\d+) dh=(-?\d+) dex=(-?\d+) alive=(\d+)", want=1, timeout=timeout)
    if not r: return None
    m = r[-1]
    return {"picked": int(m.group(1)), "succ": int(m.group(2)), "dh": int(m.group(3)), "dex": int(m.group(4)), "alive": int(m.group(5))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--eps", type=int, default=5); ap.add_argument("--ticks", type=int, default=120)
    a = ap.parse_args()
    net = Net(29, 10, 512, 3).to(DEV); net.load_state_dict(torch.load("/home/younes/compose-embodiment/hostage_v1_FINAL.pt", map_location=DEV)); net.eval()
    print("=== SAUVETAGE OTAGE (server_fob, pont natif, FIX EXFIL) ===", flush=True)
    won = 0
    for ep in range(1, a.eps + 1):
        b.query(SETUP, r"HARMATTAN_SETUP fr=(\d+)", want=1, timeout=20); time.sleep(3.0)
        res = "timeout"; best = 999
        for t in range(a.ticks):
            obs = read_aobs()
            if obs is None: time.sleep(1.0); continue
            with torch.no_grad(): act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
            st = send_act(act.tolist())
            if st:
                best = min(best, st["dex"])
                if t % 6 == 0: print("  ep %d t=%2d %s" % (ep, t, st), flush=True)
                if st["succ"]: res = "OTAGE EXFILTRE t=%d" % t; won += 1; b.send(SMOKE); break
                if st["alive"] == 0: res = "escouade aneantie"; break
            time.sleep(2.3)
        print(">>> EP %d : %s (dex min=%dm)" % (ep, res, best), flush=True)
        time.sleep(3.0)
    print("=== BILAN : %d/%d otages exfiltres ===" % (won, a.eps), flush=True)
    b.send('if (!isNil "HMT_FR") then { { deleteVehicle _x } forEach HMT_FR }; if (!isNil "HMT_GUARDS") then { { deleteVehicle _x } forEach HMT_GUARDS }; if (!isNil "HMT_HOSTAGE") then { deleteVehicle HMT_HOSTAGE }; deleteMarker "hmt_h"; deleteMarker "hmt_ext";')


if __name__ == "__main__":
    main()
