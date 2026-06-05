"""Exporte une politique (obs 10-D, model.pt) en SQF embarque pour le VISUEL B1 :
les agents COMBATTENT une vraie IA Arma (gunplay + manoeuvre doMove pilotee par la politique)
pour prendre l'objectif. La mission fait tourner le reseau elle-meme (pas de pont)."""
import torch, os, sys

MD = sys.argv[1] if len(sys.argv) > 1 else "/home/younes/arma3-marl/pretrain_b1.pt"
sd = torch.load(MD, map_location="cpu")

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
    _h1 pushBack (_s call HMT_TANH); } forEach HMT_W1;
  private _h2 = [];
  { private _row=_x; private _s = HMT_B2 select _forEachIndex;
    { _s = _s + (_row select _forEachIndex)*(_h1 select _forEachIndex) } forEach _row;
    _h2 pushBack (_s call HMT_TANH); } forEach HMT_W2;
  private _lg = [];
  { private _row=_x; private _s = HMT_B3 select _forEachIndex;
    { _s = _s + (_row select _forEachIndex)*(_h2 select _forEachIndex) } forEach _row;
    _lg pushBack _s; } forEach HMT_W3;
  private _best=0; private _bv=_lg select 0;
  { if (_x>_bv) then {_bv=_x; _best=_forEachIndex} } forEach _lg;
  _best
};

[] spawn {
  waitUntil { !isNull player && {alive player} && {!isNull (findDisplay 46)} };
  sleep 6;
  private _land=[[16000,16000],0,1500,18,0,0.4,0] call BIS_fnc_findSafePos;
  player setPosATL [_land#0,_land#1,0];
  sleep 2;
  { if (_x != player) then {deleteVehicle _x} } forEach allUnits;
  private _b=getPosATL player;
  HMT_BASEX=_b#0; HMT_BASEY=_b#1; HMT_S=160; HMT_TR=110; HMT_MV=22;
  HMT_OBJX=(_b#0)+160; HMT_OBJY=_b#1;
  // --- AGENTS (apprentissage) : ils TIRENT, la politique commande la manoeuvre ---
  private _gw=createGroup west; HMT_SQUAD=[]; HMT_ST=[];
  for "_a" from 0 to 3 do {
    private _sp=[(_b#0)+(_a mod 2)*6-3,(_b#1)+(floor(_a/2))*6-3,0];
    _gw createUnit ["B_Soldier_F",_sp,[],0,"FORM"];
    private _u=(units _gw) select ((count (units _gw))-1);
    _u setBehaviour "COMBAT"; _u setUnitPos "AUTO"; _u allowFleeing 0; _u setSkill 0.55;
    _u addEventHandler ["HandleDamage",{ (_this select 2) min 0.85 }];
    HMT_SQUAD pushBack _u; HMT_ST pushBack _sp;
  };
  // --- VRAIE IA ARMA : defenseurs de l'objectif ---
  private _ge=createGroup east; HMT_DEF=[];
  for "_k" from 0 to 2 do {
    _ge createUnit ["O_Soldier_F",[HMT_OBJX+(_k-1)*10,HMT_OBJY+(_k-1)*12,0],[],0,"FORM"];
    private _e=(units _ge) select ((count (units _ge))-1);
    _e setBehaviour "COMBAT"; _e setCombatMode "RED"; _e setUnitPos "AUTO"; _e setSkill 0.55;
    _e addEventHandler ["HandleDamage",{ (_this select 2) min 0.85 }];
    HMT_DEF pushBack _e;
  };
  deleteMarker "hmt_obj"; createMarker ["hmt_obj",[HMT_OBJX,HMT_OBJY]];
  "hmt_obj" setMarkerType "hd_objective"; "hmt_obj" setMarkerColor "ColorGreen"; "hmt_obj" setMarkerText "OBJECTIF";
  diag_log "HMT_POLICY_B1 demarree";
  while {true} do {
    for "_step" from 1 to 30 do {
      {
        private _u=_x;
        if (alive _u && {(getDammage _u)<0.7}) then {
          private _p=getPosATL _u;
          private _ox=((_p#0)-HMT_BASEX)/HMT_S; private _oy=((_p#1)-HMT_BASEY)/HMT_S;
          private _dgx=(HMT_OBJX-(_p#0))/HMT_S; private _dgy=(HMT_OBJY-(_p#1))/HMT_S;
          private _mdx=0; private _mdy=0; private _bd=1e18;
          { if ((_x != _u) && {alive _x} && {(getDammage _x)<0.7}) then {
              private _q=getPosATL _x; private _ex=(_q#0)-(_p#0); private _ey=(_q#1)-(_p#1);
              private _dd=_ex*_ex+_ey*_ey; if (_dd<_bd) then {_bd=_dd; _mdx=_ex/HMT_S; _mdy=_ey/HMT_S};
          } } forEach HMT_SQUAD;
          private _nox=0; private _noy=0; private _td=1e18;
          { if (alive _x && {(getDammage _x)<0.7}) then {
              private _q=getPosATL _x; private _ex=(_q#0)-(_p#0); private _ey=(_q#1)-(_p#1);
              private _dd=_ex*_ex+_ey*_ey; if (_dd<_td) then {_td=_dd; _nox=_ex/HMT_S; _noy=_ey/HMT_S};
          } } forEach HMT_DEF;
          private _tprox = if (_td>=1e18) then {0} else {(0 max (1-(sqrt _td)/HMT_TR)) min 1};
          private _act=[[_ox,_oy,_dgx,_dgy,1,_mdx,_mdy,_nox,_noy,_tprox]] call HMT_FWD;
          private _d=[[0,0],[0,1],[0,-1],[1,0],[-1,0]] select _act;
          _u doMove [(_p#0)+(_d#0)*HMT_MV,(_p#1)+(_d#1)*HMT_MV,0];
        };
      } forEach HMT_SQUAD;
      private _sec=0; { if (alive _x && {(getPosATL _x) distance2D [HMT_OBJX,HMT_OBJY,0] < 28}) then {_sec=_sec+1} } forEach HMT_SQUAD;
      if (_sec>=3) exitWith { hint "Objectif PRIS par les agents"; sleep 5; };
      sleep 3.2;
    };
    sleep 4;
    { private _u=HMT_SQUAD select _forEachIndex; _u setDamage 0; _u setPosATL (HMT_ST select _forEachIndex); doStop _u; } forEach HMT_SQUAD;
    { _x setDamage 0; _x setPosATL [HMT_OBJX+((_forEachIndex)-1)*10, HMT_OBJY+((_forEachIndex)-1)*12, 0]; } forEach HMT_DEF;
    sleep 2;
  };
};
'''

dst = "/mnt/data/harmattan-sandbox/Steam/steamapps/common/Arma 3/MPMissions/HarmattanBridge.Altis/policy.sqf"
open(dst, "w").write(weights + logic)
print("policy.sqf (B1) ecrit:", os.path.getsize(dst), "octets | source:", MD)
