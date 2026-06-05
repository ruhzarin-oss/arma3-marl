"""Exporte la politique entrainee (model.pt) en SQF embarque : la mission Arma
fait tourner le mini-reseau elle-meme (pilotage live des agents, sans pont)."""
import torch, os, glob

runs = sorted(glob.glob(os.path.expanduser("~/Bureau/Harmattan-entrainements/run_arma_*")), key=os.path.getmtime)
md = os.path.join(runs[-1], "model.pt")
sd = torch.load(md, map_location="cpu")

def vec(v): return "[" + ",".join("%.6g" % float(x) for x in v) + "]"
def matr(m): return "[" + ",".join(vec(r) for r in m) + "]"

W1 = sd["actor.0.weight"].tolist(); B1 = sd["actor.0.bias"].tolist()
W2 = sd["actor.2.weight"].tolist(); B2 = sd["actor.2.bias"].tolist()
W3 = sd["actor.4.weight"].tolist(); B3 = sd["actor.4.bias"].tolist()
print("formes:", len(W1), "x", len(W1[0]), "|", len(W2), "x", len(W2[0]), "|", len(W3), "x", len(W3[0]))

weights = ("HMT_W1=%s;\nHMT_B1=%s;\nHMT_W2=%s;\nHMT_B2=%s;\nHMT_W3=%s;\nHMT_B3=%s;\n"
           % (matr(W1), vec(B1), matr(W2), vec(B2), matr(W3), vec(B3)))

logic = r'''
HMT_TANH = { private _z = ((2*_this) max (-30)) min 30; private _e = exp _z; (_e-1)/(_e+1) };
HMT_FWD = {
  params ["_obs"];
  private _h1 = [];
  { private _row=_x; private _s = HMT_B1 select _forEachIndex;
    { _s = _s + (_row select _forEachIndex)*(_obs select _forEachIndex) } forEach _row;
    _h1 pushBack (_s call HMT_TANH);
  } forEach HMT_W1;
  private _h2 = [];
  { private _row=_x; private _s = HMT_B2 select _forEachIndex;
    { _s = _s + (_row select _forEachIndex)*(_h1 select _forEachIndex) } forEach _row;
    _h2 pushBack (_s call HMT_TANH);
  } forEach HMT_W2;
  private _lg = [];
  { private _row=_x; private _s = HMT_B3 select _forEachIndex;
    { _s = _s + (_row select _forEachIndex)*(_h2 select _forEachIndex) } forEach _row;
    _lg pushBack _s;
  } forEach HMT_W3;
  private _best=0; private _bv=_lg select 0;
  { if (_x>_bv) then {_bv=_x; _best=_forEachIndex} } forEach _lg;
  _best
};

[] spawn {
  waitUntil { !isNull player && {alive player} && {!isNull (findDisplay 46)} };
  sleep 6;
  private _land=[[16000,16000],0,1200,15,0,0.35,0] call BIS_fnc_findSafePos;
  player setPosATL [_land#0,_land#1,0];
  sleep 2;
  { if (_x != player) then {deleteVehicle _x} } forEach allUnits;
  private _b=getPosATL player;
  HMT_BASEX=_b#0; HMT_BASEY=_b#1; HMT_S=110; HMT_OBJX=(_b#0)+110; HMT_OBJY=_b#1;
  private _gw=createGroup west; HMT_SQUAD=[]; HMT_START=[];
  for "_a" from 0 to 3 do {
    private _sp=[(_b#0)+(_a mod 2)*5-2,(_b#1)+(floor(_a/2))*5-2,0];
    _gw createUnit ["B_Soldier_F",_sp,[],0,"NONE"];
    private _u=(units _gw) select ((count (units _gw))-1);
    _u disableAI "AUTOTARGET"; _u setBehaviour "AWARE"; _u setUnitPos "UP"; _u allowFleeing 0;
    _u addEventHandler ["HandleDamage",{ (_this select 2) min 0.85 }];
    HMT_SQUAD pushBack _u; HMT_START pushBack _sp;
  };
  private _ge=createGroup east; HMT_OPF=[];
  for "_k" from 0 to 1 do {
    _ge createUnit ["O_Soldier_F",[(_b#0)+55+_k*6,(_b#1),0],[],0,"NONE"];
    private _e=(units _ge) select ((count (units _ge))-1);
    _e setBehaviour "COMBAT"; _e disableAI "MOVE"; _e setUnitPos "UP"; _e setSkill 0.4;
    HMT_OPF pushBack _e;
  };
  deleteMarker "hmt_obj";
  createMarker ["hmt_obj",[HMT_OBJX,HMT_OBJY]];
  "hmt_obj" setMarkerType "hd_objective"; "hmt_obj" setMarkerColor "ColorGreen"; "hmt_obj" setMarkerText "OBJECTIF";
  diag_log "HMT_POLICY demarree";
  while {true} do {
    for "_step" from 1 to 26 do {
      private _secn=0;
      {
        private _u=_x;
        if (alive _u && {(getDammage _u)<0.7}) then {
          private _p=getPosATL _u;
          private _ox=((_p#0)-HMT_BASEX)/HMT_S; private _oy=((_p#1)-HMT_BASEY)/HMT_S;
          private _dgx=(HMT_OBJX-(_p#0))/HMT_S; private _dgy=(HMT_OBJY-(_p#1))/HMT_S;
          private _mdx=0; private _mdy=0; private _bd=1e18;
          { if ((_x != _u) && {alive _x}) then {
              private _q=getPosATL _x; private _ex=(_q#0)-(_p#0); private _ey=(_q#1)-(_p#1);
              private _dd=_ex*_ex+_ey*_ey; if (_dd<_bd) then {_bd=_dd; _mdx=_ex/HMT_S; _mdy=_ey/HMT_S};
          } } forEach HMT_SQUAD;
          private _obs=[_ox,_oy,_dgx,_dgy,1,_mdx,_mdy];
          private _act=[_obs] call HMT_FWD;
          private _d=[[0,0],[0,1],[0,-1],[1,0],[-1,0]] select _act;
          _u doMove [(_p#0)+(_d#0)*15,(_p#1)+(_d#1)*15,0];
          if ((_p distance2D [HMT_OBJX,HMT_OBJY,0]) < 26) then {_secn=_secn+1};
        };
      } forEach HMT_SQUAD;
      if (_secn >= 3) exitWith { hint "Objectif securise par la politique"; };
      sleep 3.5;
    };
    sleep 4;
    { private _u=HMT_SQUAD select _forEachIndex; _u setDamage 0; _u setPosATL (HMT_START select _forEachIndex); } forEach HMT_SQUAD;
    { _x setDamage 0 } forEach HMT_OPF;
    sleep 2;
  };
};
'''

dst = "/mnt/data/harmattan-sandbox/Steam/steamapps/common/Arma 3/MPMissions/HarmattanBridge.Altis/policy.sqf"
open(dst, "w").write(weights + logic)
print("policy.sqf ecrit:", os.path.getsize(dst), "octets ->", dst)
print("source modele:", md)
