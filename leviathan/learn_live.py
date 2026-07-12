#!/usr/bin/env python3
"""learn_live.py — 10 AGENTS APPRIS repartis AVEC LAMBS sur la vraie mission (server_fob).
Ils PERCOIVENT (10 features), la politique PARTAGEE (orchestration) choisit leur tactique, ils AGISSENT
et ENREGISTRENT leur experience (obs, action, reward partage) -> human_session_experience.jsonl, pour
affiner hors-ligne. CARTE EN COULEURS : chaque agent colore par sa TACTIQUE courante, TOI en bleu,
la masse LAMBS en gris. Reutilise HMT_ORCH_FEATS + HMT_TAC_EXEC (deja au boot)."""
import sys, time, ast, json, argparse
from collections import Counter
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import torch, torch.nn as nn

CKO = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"
EXP = "/home/younes/arma3-marl/leviathan/human_session_experience.jsonl"
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]
OBJX, OBJY = 2300, 2320          # ~320 m nord de la caserne WEST (spawn joueur) -> engagement rapide
NAG = 10; NLAMBS = 8
b = NativeBridge(port=5816)


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__(); s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU()); s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


SETUP = ('[] spawn { HMT_OBJ=[%d,%d,0]; '
  'if (!isNil "HMT_AG") then { { deleteVehicle _x } forEach HMT_AG; }; if (!isNil "HMT_LAMBS") then { { deleteVehicle _x } forEach HMT_LAMBS; }; '
  'for "_i" from 0 to 29 do { deleteMarker ("hmt_ag_"+str _i); deleteMarker ("hmt_lb_"+str _i); }; deleteMarker "hmt_you"; deleteMarker "hmt_lobj"; '
  'HMT_AG=[]; HMT_LAMBS=[]; private _ga=createGroup east; '
  'for "_i" from 0 to %d do { private _a=_i*36; private _r=12+random 14; private _px=(HMT_OBJ select 0)+_r*sin _a; private _py=(HMT_OBJ select 1)+_r*cos _a; '
  '  _ga createUnit ["O_Soldier_F",[_px,_py,0],[],0,"NONE"]; private _u=(units _ga) select (count(units _ga)-1); '
  '  _u setPosATL [_px,_py,0]; _u setSkill 0.5; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; HMT_AG pushBack _u; '
  '  private _mk=createMarker ["hmt_ag_"+str _i, getPosATL _u]; _mk setMarkerType "mil_triangle"; _mk setMarkerColor "ColorEAST"; _mk setMarkerText ("A"+str _i); _mk setMarkerSize [0.7,0.7]; }; '
  'private _gl=createGroup east; '
  'for "_i" from 0 to %d do { private _a=_i*45; private _r=28+random 12; private _px=(HMT_OBJ select 0)+_r*sin _a; private _py=(HMT_OBJ select 1)+_r*cos _a; '
  '  _gl createUnit ["O_Soldier_F",[_px,_py,0],[],0,"NONE"]; private _u=(units _gl) select (count(units _gl)-1); '
  '  _u setPosATL [_px,_py,0]; _u setSkill 0.45; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; HMT_LAMBS pushBack _u; '
  '  private _mk=createMarker ["hmt_lb_"+str _i, getPosATL _u]; _mk setMarkerType "mil_dot"; _mk setMarkerColor "ColorBlack"; _mk setMarkerText "LAMBS"; _mk setMarkerSize [0.5,0.5]; }; '
  'createMarker ["hmt_lobj", HMT_OBJ]; "hmt_lobj" setMarkerType "hd_objective"; "hmt_lobj" setMarkerColor "ColorEAST"; "hmt_lobj" setMarkerText "AGENTS APPRENANTS"; '
  'createMarker ["hmt_you", HMT_OBJ]; "hmt_you" setMarkerType "hd_flag"; "hmt_you" setMarkerColor "ColorBlue"; "hmt_you" setMarkerText "TOI"; '
  '(format ["HARMATTAN_LSETUP ag=%%1 lambs=%%2 water=%%3 pos=%%4", count HMT_AG, count HMT_LAMBS, surfaceIsWater HMT_OBJ, HMT_OBJ]) call HMT_EMIT; };') % (OBJX, OBJY, NAG - 1, NLAMBS - 1)

PERC = ('private _vs=[]; private _al=[]; '
  '{ if (alive _x) then { _vs pushBack (([_x] call HMT_ORCH_FEATS) apply {(round(_x*1000))/1000}); _al pushBack 1; } '
  '  else { _vs pushBack [0,0,0,0,0,0,0,0,0,0]; _al pushBack 0; }; } forEach HMT_AG; '
  '(format ["HARMATTAN_LOBS %1 | %2", _vs, _al]) call HMT_EMIT;')

STEP = ('HMT_LTAC=[%s]; '
  '{ private _u=_x; private _i=_forEachIndex; private _mk="hmt_ag_"+str _i; '
  '  if (alive _u) then { private _t=HMT_LTAC select _i; [_u,_t] call HMT_TAC_EXEC; '
  '    _mk setMarkerColor (["ColorRed","ColorOrange","ColorGreen","ColorWhite","ColorYellow"] select _t); '
  '    _mk setMarkerText (["TIR","GREN","FLANC","FUMI","SUPPR"] select _t); _mk setMarkerPos (getPosATL _u); } '
  '  else { _mk setMarkerColor "ColorBlack"; _mk setMarkerText "KO"; }; } forEach HMT_AG; '
  '{ private _i=_forEachIndex; if (alive _x) then { ("hmt_lb_"+str _i) setMarkerPos (getPosATL _x); } else { ("hmt_lb_"+str _i) setMarkerColor "ColorBlack"; }; } forEach HMT_LAMBS; '
  'private _pl=allPlayers; if (count _pl>0) then { "hmt_you" setMarkerPos (getPosATL (_pl select 0)); }; '
  'private _nw={alive _x && side _x==west && (_x distance HMT_OBJ)<320} count allUnits; '
  'private _dmg=0; private _na=0; { if (alive _x) then {_na=_na+1;_dmg=_dmg+(damage _x);}; } forEach HMT_AG; '
  '(format ["HARMATTAN_LREW nw=%%1 dmg=%%2 na=%%3", _nw, round(_dmg*100), _na]) call HMT_EMIT;')


def perc(timeout=10):
    r = b.query(PERC, r"HARMATTAN_LOBS (\[.*\]) \| (\[.*\])", want=1, timeout=timeout)
    if not r: return None, None
    try:
        return ast.literal_eval(r[-1].group(1)), ast.literal_eval(r[-1].group(2))
    except Exception:
        return None, None


def step(tacs, timeout=10):
    sqf = STEP % ",".join(str(int(t)) for t in tacs)
    r = b.query(sqf, r"HARMATTAN_LREW nw=(\d+) dmg=(\d+) na=(\d+)", want=1, timeout=timeout)
    if not r: return None
    m = r[-1]; return {"nw": int(m.group(1)), "dmg": int(m.group(2)) / 100.0, "na": int(m.group(3))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ticks", type=int, default=100000)
    a = ap.parse_args()
    net = OrchNet(); net.load_state_dict(torch.load(CKO, map_location="cpu")); net.eval()
    r = b.query(SETUP, r"HARMATTAN_LSETUP ag=(\d+) lambs=(\d+) water=(\w+) pos=(\[.*\])", want=1, timeout=20)
    if r:
        m = r[-1]; print("[learn] setup : %s agents appris + %s LAMBS | water=%s | obj=%s" % (m.group(1), m.group(2), m.group(3), m.group(4)), flush=True)
    print("=== AGENTS APPRENANTS EN LIGNE (obs->politique partagee->action->enregistrement) ===", flush=True)
    print("=== couleurs : TIR=rouge GRENADE=orange FLANC=vert FUMI=blanc SUPPR=jaune | TOI=bleu | LAMBS=noir ===", flush=True)
    time.sleep(3)
    fexp = open(EXP, "a")
    prev_nw = None; prev_dmg = 0.0; nrec = 0
    for tick in range(a.ticks):
        vs, al = perc()
        if not vs:
            time.sleep(1.0); continue
        with torch.no_grad():
            tacs = net(torch.tensor(vs, dtype=torch.float32))[0].argmax(1).tolist()
        st = step(tacs)
        if st:
            nw, dmg = st["nw"], st["dmg"]
            if prev_nw is None: prev_nw = nw
            rew = 1.0 * (prev_nw - nw) - 2.0 * (dmg - prev_dmg) - 0.01     # reward PARTAGE (equipe) : ennemis tombes - degats subis
            for i in range(len(vs)):
                if al[i]:
                    fexp.write(json.dumps({"t": tick, "ag": i, "obs": vs[i], "act": tacs[i], "r": round(rew, 3), "nalive": st["na"]}) + "\n"); nrec += 1
            fexp.flush(); prev_nw, prev_dmg = nw, dmg
            if tick % 4 == 0:
                dist = Counter(TAC[t] for i, t in enumerate(tacs) if al[i])
                print("  [%04d] agents=%d/%d | west_pres=%d | r=%+.2f | tactiques=%s | exp=%d" % (tick, st["na"], NAG, nw, rew, dict(dist), nrec), flush=True)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
