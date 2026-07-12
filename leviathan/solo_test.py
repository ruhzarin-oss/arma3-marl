#!/usr/bin/env python3
"""solo_test.py — UN agent BLUFOR seul (loadout 003) dans 3 scenarios, pour voir comment il se debrouille
et OU il echoue (= liste d'ameliorations). Corps LAMBS (mouvement+reflexe) + tactique apprise (orchestration)
en surcouche. LEGER (1 agent, 2 requetes/tick) donc stable. Enregistre son etat tick par tick :
  solo_<scenario>.jsonl : {t, alive, x, y, dobj (dist objectif), ka (knowsAbout max ennemi->agent), neast, tac}
Scenarios : assaut (prendre un point tenu) / patrouille (traverser vivant) / reco (observer sans etre vu)."""
import sys, time, ast, json, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import torch, torch.nn as nn

CKO = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]
INNER = str(ast.literal_eval(open("/home/younes/Bureau/003.ar").read().strip())[0]).replace("'", '"')

# (start agent, objectif, [positions EAST], but)   -- zone caserne sud Stratis (terre)
SCEN = {
    "assaut":     ([2300, 2100], [2300, 2440], [[2300, 2440], [2288, 2450], [2312, 2448], [2300, 2428]], "prendre l'objectif (dist<30m)"),
    "patrouille": ([2300, 2100], [2620, 2360], [[2410, 2200], [2500, 2290], [2540, 2340]], "atteindre le point loin VIVANT"),
    "reco":       ([2300, 2100], [2470, 2440], [[2470, 2440], [2482, 2432], [2458, 2450]], "observer a <150m SANS etre detecte (ka<1.5)"),
}


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__(); s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU()); s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--scenario", required=True, choices=list(SCEN)); ap.add_argument("--ticks", type=int, default=60)
    a = ap.parse_args()
    ag, obj, easts, but = SCEN[a.scenario]
    net = OrchNet(); net.load_state_dict(torch.load(CKO, map_location="cpu")); net.eval()
    b = NativeBridge(port=5816)

    east_sqf = "[" + ",".join("[%d,%d,0]" % (p[0], p[1]) for p in easts) + "]"
    setup = ('[] spawn { if (!isNil "HMT_SOLO") then {deleteVehicle HMT_SOLO}; if (!isNil "HMT_EAST") then {{deleteVehicle _x} forEach HMT_EAST}; '
        'for "_i" from 0 to 11 do {deleteMarker ("hmt_e_"+str _i)}; deleteMarker "hmt_solo"; deleteMarker "hmt_sobj"; '
        'HMT_OBJ=[%d,%d,0]; HMT_L003=%s; '
        'private _gw=createGroup west; _gw createUnit ["B_soldier_F",[%d,%d,0],[],0,"NONE"]; HMT_SOLO=(units _gw) select ((count units _gw)-1); '
        'HMT_SOLO setPosATL [%d,%d,0]; HMT_SOLO setSkill 0.6; HMT_SOLO setBehaviour "AWARE"; HMT_SOLO setCombatMode "YELLOW"; HMT_SOLO allowDamage true; HMT_SOLO setUnitLoadout HMT_L003; '
        'private _wp=_gw addWaypoint [HMT_OBJ,0]; _wp setWaypointType "MOVE"; _wp setWaypointBehaviour "AWARE"; _wp setWaypointCombatMode "YELLOW"; _wp setWaypointSpeed "NORMAL"; '
        'private _ge=createGroup east; HMT_EAST=[]; { private _p=_x; _ge createUnit ["O_Soldier_F",_p,[],0,"NONE"]; private _u=(units _ge) select ((count units _ge)-1); _u setPosATL _p; _u setSkill 0.5; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; HMT_EAST pushBack _u; } forEach %s; '
        'createMarker ["hmt_solo", getPosATL HMT_SOLO]; "hmt_solo" setMarkerType "mil_triangle"; "hmt_solo" setMarkerColor "ColorWEST"; "hmt_solo" setMarkerText "AGENT"; '
        'createMarker ["hmt_sobj", HMT_OBJ]; "hmt_sobj" setMarkerType "hd_objective"; "hmt_sobj" setMarkerColor "ColorYellow"; "hmt_sobj" setMarkerText "OBJ"; '
        '{ private _m=createMarker ["hmt_e_"+str _forEachIndex, getPosATL _x]; _m setMarkerType "mil_dot"; _m setMarkerColor "ColorEAST"; } forEach HMT_EAST; '
        '(format ["HARMATTAN_SOLO ok east=%%1 water=%%2", count HMT_EAST, surfaceIsWater HMT_OBJ]) call HMT_EMIT; };') % (obj[0], obj[1], INNER, ag[0], ag[1], ag[0], ag[1], east_sqf)

    sense = ('if (alive HMT_SOLO) then { (format ["HARMATTAN_SOLOF %1 1", ([HMT_SOLO] call HMT_ORCH_FEATS) apply {(round(_x*1000))/1000}]) call HMT_EMIT } '
             'else { (format ["HARMATTAN_SOLOF %1 0", [0,0,0,0,0,0,0,0,0,0]]) call HMT_EMIT };')
    act_tpl = ('private _t=%d; if (alive HMT_SOLO) then { [HMT_SOLO,_t] call HMT_TAC_EXEC; "hmt_solo" setMarkerPos (getPosATL HMT_SOLO) }; '
        '{ ("hmt_e_"+str _forEachIndex) setMarkerPos (getPosATL _x) } forEach HMT_EAST; '
        'private _p=getPosATL HMT_SOLO; private _do=_p distance2D [(HMT_OBJ select 0),(HMT_OBJ select 1)]; '
        'private _ka=0; { _ka=_ka max (_x knowsAbout HMT_SOLO) } forEach (HMT_EAST select {alive _x}); '
        '(format ["HARMATTAN_SOLOST al=%%1 do=%%2 ka=%%3 ne=%%4 x=%%5 y=%%6", (alive HMT_SOLO), round _do, round(_ka*100)/100, ({alive _x} count HMT_EAST), round(_p select 0), round(_p select 1)]) call HMT_EMIT;')

    r = b.query(setup, r"HARMATTAN_SOLO ok east=(\d+) water=(\w+)", want=1, timeout=20)
    print("=== SOLO [%s] : %s | %s ===" % (a.scenario.upper(), but, r[-1].group(0) if r else "?"), flush=True)
    time.sleep(4)
    f = open("/home/younes/arma3-marl/leviathan/solo_%s.jsonl" % a.scenario, "w")
    res = "timeout"; detected_at = None; tmin_obj = 9999
    for t in range(a.ticks):
        rf = b.query(sense, r"HARMATTAN_SOLOF (\[.*\]) (\d)", want=1, timeout=20)
        if not rf:
            time.sleep(1.5); continue
        feats = ast.literal_eval(rf[-1].group(1)); alive = int(rf[-1].group(2))
        with torch.no_grad():
            tac = net(torch.tensor([feats], dtype=torch.float32))[0].argmax(1).item()
        rs = b.query(act_tpl % tac, r"HARMATTAN_SOLOST al=(\w+) do=(\d+) ka=([\d.]+) ne=(\d+) x=(-?\d+) y=(-?\d+)", want=1, timeout=20)
        if not rs:
            time.sleep(1.5); continue
        m = rs[-1]; al = (m.group(1) == "true"); dobj = int(m.group(2)); ka = float(m.group(3)); ne = int(m.group(4)); x = int(m.group(5)); y = int(m.group(6))
        tmin_obj = min(tmin_obj, dobj)
        if ka >= 1.5 and detected_at is None: detected_at = t
        f.write(json.dumps({"t": t, "alive": al, "x": x, "y": y, "dobj": dobj, "ka": ka, "neast": ne, "tac": tac}) + "\n"); f.flush()
        if t % 3 == 0:
            print("  t=%2d | vivant=%s | ->obj=%3dm | detecte(ka)=%.1f | east=%d | %s" % (t, al, dobj, ka, ne, TAC[tac]), flush=True)
        # verdicts
        if not al: res = "MORT a t=%d (->obj %dm, detecte t=%s)" % (t, dobj, detected_at); break
        if a.scenario in ("assaut", "patrouille") and dobj < 30: res = "OBJECTIF ATTEINT t=%d (detecte t=%s)" % (t, detected_at); break
        if a.scenario == "reco" and dobj < 150 and ka < 1.5: res = "OBSERVE NON DETECTE t=%d (->obj %dm)" % (t, dobj); break
        if a.scenario == "reco" and ka >= 1.5: res = "DETECTE (echec reco) t=%d (->obj %dm)" % (t, dobj); break
        time.sleep(1.5)
    print(">>> [%s] VERDICT : %s | dist mini objectif=%dm | premiere detection=t%s" % (a.scenario.upper(), res, tmin_obj, detected_at), flush=True)
    print(">>> log : solo_%s.jsonl" % a.scenario, flush=True)


if __name__ == "__main__":
    main()
