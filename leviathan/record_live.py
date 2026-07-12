#!/usr/bin/env python3
"""record_live.py — SESSION ENREGISTREE pour AAR. 10 agents appris + LAMBS + officier Qwen, et on capte TOUT :
  - flux ETAT   (session_state.jsonl)  : par tick/unite = features + position + cap + vitesse + posture + degats + tactique + logits + valeur
  - flux EVENTS (session_events.jsonl) : tirs / touches / morts (EventHandlers Arma : Fired/Hit/EntityKilled)
  - flux QWEN   (session_qwen.jsonl)   : SITREP + prompt + sortie brute + ordres parses + RAG + latence
Carte couleur (agent=tactique, TOI=bleu, LAMBS=noir). Reutilise HMT_ORCH_FEATS / HMT_TAC_EXEC / HMT_SITREP."""
import sys, time, ast, json, re, argparse, threading
from collections import Counter
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import OfficerState, FOBS
from officer_memory import OfficerMemory, embed_theatre
from officer import OfficerLoop, make_apply, format_retrieved, SYSTEM
import requests
import torch, torch.nn as nn

CKO = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"
DIR = "/home/younes/arma3-marl/leviathan"
F_STATE = DIR + "/session_state.jsonl"; F_EV = DIR + "/session_events.jsonl"; F_QWEN = DIR + "/session_qwen.jsonl"
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]
OBJX, OBJY = 2300, 2320; NAG = 10; NLAMBS = 8
b = NativeBridge(port=5816)

try:                                                  # loadout SF de Younes (003.ar) -> appliqué au spawn + respawn
    _raw = open("/home/younes/Bureau/003.ar").read().strip()
    LOADOUT003 = str(ast.literal_eval(_raw)[0]).replace("'", '"')
except Exception as _e:
    LOADOUT003 = None


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__(); s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU()); s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def qwen_recorded(prompt, sit, model="qwen2.5:14b", url="http://localhost:11434/v1/chat/completions"):
    """Comme qwen_ollama mais renvoie AUSSI le texte brut du LLM (pour l'AAR)."""
    r = requests.post(url, json={"model": model, "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                                 "temperature": 0.2, "response_format": {"type": "json_object"}}, timeout=120)
    txt = r.json()["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S); parsed = json.loads(m.group(0)) if m else {"appreciation": txt[:200], "ordres": []}
    return parsed, txt


# ---- SQF : spawn agents+LAMBS+markers + EventHandlers (Fired/Hit) + mission EntityKilled ----
SETUP = ('[] spawn { HMT_OBJ=[%d,%d,0]; HMT_EVENTS=[]; '
  'if (!isNil "HMT_AG") then { { deleteVehicle _x } forEach HMT_AG }; if (!isNil "HMT_LAMBS") then { { deleteVehicle _x } forEach HMT_LAMBS }; '
  'for "_i" from 0 to 29 do { deleteMarker ("hmt_ag_"+str _i); deleteMarker ("hmt_lb_"+str _i) }; deleteMarker "hmt_you"; deleteMarker "hmt_lobj"; '
  'if (isNil "HMT_KEH") then { HMT_KEH = addMissionEventHandler ["EntityKilled", { params ["_k","_kl"]; if (!isNil "HMT_EVENTS") then { HMT_EVENTS pushBack ["KILL", netId _k, (if (isNull _kl) then {"?"} else {netId _kl}), (if (isNull _kl) then {-1} else {round (_k distance _kl)})] } }] }; '
  'HMT_ADDEH = { params ["_u"]; _u addEventHandler ["Fired", { HMT_EVENTS pushBack ["FIRE", netId (_this select 0), (_this select 1)] }]; _u addEventHandler ["Hit", { HMT_EVENTS pushBack ["HIT", netId (_this select 0), (if (isNull (_this select 1)) then {"?"} else {netId (_this select 1)}), round ((_this select 2)*100)] }]; _u setVariable ["HMT_EH",1] }; '
  'HMT_AG=[]; HMT_LAMBS=[]; private _ga=createGroup east; '
  'for "_i" from 0 to %d do { private _a=_i*36; private _r=12+random 14; private _px=(HMT_OBJ select 0)+_r*sin _a; private _py=(HMT_OBJ select 1)+_r*cos _a; '
  '  _ga createUnit ["O_Soldier_F",[_px,_py,0],[],0,"NONE"]; private _u=(units _ga) select (count(units _ga)-1); _u setPosATL [_px,_py,0]; _u setSkill 0.5; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; [_u] call HMT_ADDEH; HMT_AG pushBack _u; '
  '  private _mk=createMarker ["hmt_ag_"+str _i, getPosATL _u]; _mk setMarkerType "mil_triangle"; _mk setMarkerColor "ColorEAST"; _mk setMarkerText ("A"+str _i); _mk setMarkerSize [0.7,0.7] }; '
  'private _gl=createGroup east; '
  'for "_i" from 0 to %d do { private _a=_i*45; private _r=28+random 12; private _px=(HMT_OBJ select 0)+_r*sin _a; private _py=(HMT_OBJ select 1)+_r*cos _a; '
  '  _gl createUnit ["O_Soldier_F",[_px,_py,0],[],0,"NONE"]; private _u=(units _gl) select (count(units _gl)-1); _u setPosATL [_px,_py,0]; _u setSkill 0.45; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; [_u] call HMT_ADDEH; HMT_LAMBS pushBack _u; '
  '  private _mk=createMarker ["hmt_lb_"+str _i, getPosATL _u]; _mk setMarkerType "mil_dot"; _mk setMarkerColor "ColorBlack"; _mk setMarkerText "LAMBS"; _mk setMarkerSize [0.5,0.5] }; '
  'createMarker ["hmt_lobj", HMT_OBJ]; "hmt_lobj" setMarkerType "hd_objective"; "hmt_lobj" setMarkerColor "ColorEAST"; "hmt_lobj" setMarkerText "AGENTS APPRENANTS"; '
  'createMarker ["hmt_you", HMT_OBJ]; "hmt_you" setMarkerType "hd_flag"; "hmt_you" setMarkerColor "ColorBlue"; "hmt_you" setMarkerText "TOI"; '
  '(format ["HARMATTAN_LSETUP ag=%%1 lambs=%%2 water=%%3", count HMT_AG, count HMT_LAMBS, surfaceIsWater HMT_OBJ]) call HMT_EMIT; };') % (OBJX, OBJY, NAG - 1, NLAMBS - 1)

# ---- SENSE agents : features(10) + [x,y,z,dir,vx,vy,stance,dmg100,alive] ----
SENSE_AG = ('private _o=[]; '
  '{ if (alive _x) then { private _p=getPosATL _x; private _v=velocity _x; private _st=switch (stance _x) do {case "CROUCH":{1};case "PRONE":{2};default{0}}; '
  '    _o pushBack (([_x] call HMT_ORCH_FEATS) apply {(round(_x*1000))/1000}) + [round(_p#0),round(_p#1),round((_p#2)*10)/10,round(direction _x),round((_v#0)*10)/10,round((_v#1)*10)/10,_st,round((damage _x)*100),1]; } '
  '  else { _o pushBack [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,round((damage _x)*100),0]; }; } forEach HMT_AG; '
  '(format ["HARMATTAN_AG %1", _o]) call HMT_EMIT;')

# ---- SENSE env : LAMBS [x,y,dir,dmg,alive] + joueurs [x,y,z,dir] (+ pose les EH sur les joueurs) ----
SENSE_ENV = ('{ if (isNil {_x getVariable "HMT_EH"}) then { [_x] call HMT_ADDEH }; if (!isNil "HMT_L003" && {isNil {_x getVariable "HMT_L003_done"}}) then { _x setVariable ["HMT_L003_done",1]; [_x, HMT_L003] remoteExecCall ["setUnitLoadout", _x] } } forEach allPlayers; '
  'private _m=[]; { if (alive _x) then { private _p=getPosATL _x; _m pushBack [round(_p#0),round(_p#1),round(direction _x),round((damage _x)*100),1] } else { _m pushBack [0,0,0,round((damage _x)*100),0] } } forEach HMT_LAMBS; '
  'private _pl=[]; { private _p=getPosATL _x; _pl pushBack [round(_p#0),round(_p#1),round((_p#2)*10)/10,round(direction _x)] } forEach allPlayers; '
  '(format ["HARMATTAN_ENV %1 | %2", _m, _pl]) call HMT_EMIT;')

# ---- drain EVENTS ----
DRAIN = ('private _e = if (isNil "HMT_EVENTS") then {[]} else {+HMT_EVENTS}; HMT_EVENTS=[]; (format ["HARMATTAN_EV %1", _e]) call HMT_EMIT;')

# ---- ACT : dispatch tactiques + markers + reward inputs ----
ACT = ('HMT_LTAC=[%s]; '
  '{ private _u=_x; private _i=_forEachIndex; private _mk="hmt_ag_"+str _i; '
  '  if (alive _u) then { private _t=HMT_LTAC select _i; [_u,_t] call HMT_TAC_EXEC; _mk setMarkerColor (["ColorRed","ColorOrange","ColorGreen","ColorWhite","ColorYellow"] select _t); _mk setMarkerText (["TIR","GREN","FLANC","FUMI","SUPPR"] select _t); _mk setMarkerPos (getPosATL _u); } '
  '  else { _mk setMarkerColor "ColorBlack"; _mk setMarkerText "KO"; }; } forEach HMT_AG; '
  '{ private _i=_forEachIndex; if (alive _x) then { ("hmt_lb_"+str _i) setMarkerPos (getPosATL _x) } else { ("hmt_lb_"+str _i) setMarkerColor "ColorBlack" } } forEach HMT_LAMBS; '
  'private _pl=allPlayers; if (count _pl>0) then { "hmt_you" setMarkerPos (getPosATL (_pl select 0)) }; '
  'private _nw={alive _x && side _x==west && (_x distance HMT_OBJ)<320} count allUnits; '
  'private _dmg=0; private _na=0; { if (alive _x) then {_na=_na+1;_dmg=_dmg+(damage _x)} } forEach HMT_AG; '
  '(format ["HARMATTAN_LREW nw=%%1 dmg=%%2 na=%%3", _nw, round(_dmg*100), _na]) call HMT_EMIT;')


def q1(sqf, tag, timeout=25):
    r = b.query(sqf, tag + r" (\[.*\])", want=1, timeout=timeout)
    if not r: return None
    try: return ast.literal_eval(r[-1].group(1))
    except Exception: return None


def read_sit(st, tick):
    r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=25)
    return st.parse(r[-1].group(1).rstrip('"').strip(), tick) if r else None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ticks", type=int, default=100000); a = ap.parse_args()
    net = OrchNet(); net.load_state_dict(torch.load(CKO, map_location="cpu")); net.eval()
    st = OfficerState(bridge=b)
    b.send('if (isNil "HMT_TARGET") then { HMT_TARGET = HMT_TARGETS apply {_x select 1}; };')
    b.send("HMT_FOB_ANCHORS = [" + ",".join("[%d,%d]" % (f[1], f[2]) for f in FOBS) + "];")
    mem = OfficerMemory("/home/younes/arma3-marl/leviathan/leviathan_officer.db")

    class Stub:
        focus = None
    drv = Stub(); apply_fn = make_apply(drv)
    fs = open(F_STATE, "a"); fe = open(F_EV, "a"); fq = open(F_QWEN, "a")
    r = b.query(SETUP, r"HARMATTAN_LSETUP ag=(\d+) lambs=(\d+) water=(\w+)", want=1, timeout=20)
    print("[record] setup %s | 3 flux -> session_{state,events,qwen}.jsonl" % (r[-1].group(0) if r else "?"), flush=True)
    if LOADOUT003:                                    # loadout 003 : global + réapplication au respawn (le spawn est géré dans SENSE_ENV)
        b.send('HMT_L003 = %s; if (isNil "HMT_L003_EH") then { HMT_L003_EH = addMissionEventHandler ["EntityRespawned", { params ["_n"]; if (isPlayer _n && {!isNil "HMT_L003"}) then { [_n, HMT_L003] remoteExecCall ["setUnitLoadout", _n] } }] };' % LOADOUT003)
        print("[record] loadout 003 (SF HK416) chargé -> spawn + respawn", flush=True)
    else:
        print("[record] pas de loadout 003 (003.ar absent)", flush=True)
    print("=== SESSION ENREGISTREE (etat + events + Qwen) — couleurs: TIR=r GREN=o FLANC=v FUMI=b SUPPR=j | TOI=bleu | LAMBS=noir ===", flush=True)
    time.sleep(3)
    nS = nE = 0; nQ = [0]; qbusy = [False]

    def qwen_worker(prompt, sit, passe, tick, thr):     # le LLM (lent) tourne ICI, hors de la boucle d'enregistrement ; QUE du HTTP + fichier, pas de pont
        try:
            t0 = time.time(); orders, raw = qwen_recorded(prompt, sit); lat = round(time.time() - t0, 2)
            apply_fn(orders)
            fq.write(json.dumps({"t": tick, "menaces": thr, "focus": drv.focus, "sitrep": OfficerState.to_text(sit),
                                 "prompt": prompt, "raw": raw, "ordres": orders, "rag": passe, "latence_s": lat}) + "\n"); fq.flush(); nQ[0] += 1
            print("  [%04d] QWEN focus=%s menaces=%s lat=%ss" % (tick, drv.focus, thr or "-", lat), flush=True)
        except Exception as e:
            print("  [%04d] qwen err: %s" % (tick, str(e)[:60]), flush=True)
        finally:
            qbusy[0] = False

    for tick in range(a.ticks):
        # --- QWEN (tier lent, NON-BLOQUANT : SITREP dans la boucle, le LLM part en thread) ---
        if tick % 5 == 1 and not qbusy[0]:
            try:
                sit = read_sit(st, tick)
                if sit:
                    emb = embed_theatre(sit); passe = mem.retrieve("theatre", emb, k=3)
                    prompt = format_retrieved(passe) + "\n\n" + OfficerState.to_text(sit)
                    thr = [(f["name"], f["contacts"]) for f in sit["fobs"] if f["threatened"]]
                    qbusy[0] = True
                    threading.Thread(target=qwen_worker, args=(prompt, sit, passe, tick, thr), daemon=True).start()
            except Exception as e:
                print("  [%04d] sitrep err: %s" % (tick, str(e)[:60]), flush=True)
        # --- ETAT agents + decision ---
        ag = q1(SENSE_AG, "HARMATTAN_AG")
        if not ag:
            time.sleep(1.0); continue
        feats = [row[:10] for row in ag]
        with torch.no_grad():
            logits, val = net(torch.tensor(feats, dtype=torch.float32)); tacs = logits.argmax(1).tolist()
            probs = torch.softmax(logits, 1)
        rr = b.query(SENSE_ENV, r"HARMATTAN_ENV (\[.*\]) \| (\[.*\])", want=1, timeout=25)
        mass, players = ([], [])
        if rr:
            try: mass = ast.literal_eval(rr[-1].group(1)); players = ast.literal_eval(rr[-1].group(2))
            except Exception: pass
        for i, row in enumerate(ag):
            fs.write(json.dumps({"t": tick, "ag": i, "obs": row[:10], "x": row[10], "y": row[11], "z": row[12], "dir": row[13],
                                 "vx": row[14], "vy": row[15], "stance": row[16], "dmg": row[17], "alive": row[18],
                                 "tac": tacs[i], "tac_probs": [round(p, 3) for p in probs[i].tolist()], "val": round(float(val[i]), 3)}) + "\n"); nS += 1
        fs.write(json.dumps({"t": tick, "kind": "env", "lambs": mass, "players": players}) + "\n"); fs.flush()
        # --- EVENTS ---
        ev = q1(DRAIN, "HARMATTAN_EV") or []
        for e in ev:
            fe.write(json.dumps({"t": tick, "ev": e}) + "\n"); nE += 1
        if ev: fe.flush()
        # --- ACT ---
        b.query(ACT % ",".join(str(int(x)) for x in tacs), r"HARMATTAN_LREW nw=(\d+) dmg=(\d+) na=(\d+)", want=1, timeout=25)
        if tick % 4 == 0:
            dist = Counter(TAC[t] for i, t in enumerate(tacs) if ag[i][18])
            print("  [%04d] etat=%d ev=%d qwen=%d | tac=%s | joueurs=%d" % (tick, nS, nE, nQ[0], dict(dist), len(players)), flush=True)
        time.sleep(2.5)


if __name__ == "__main__":
    main()
