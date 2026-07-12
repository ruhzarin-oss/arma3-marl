#!/usr/bin/env python3
"""blufor_full.py — LE MARIAGE : chaine complete (Qwen officier + commander + orchestration) sur le CORPS LAMBS.
Corps = coquilles armees LAMBS (enableAI ALL, elles TIRENT). Le cerveau assigne les ROLES par element,
mappes sur les fonctions LAMBS : ASSAUT->taskRush, APPUI->suppression, FLANC->contournement, RESERVE->tenir.
Orchestration = tactique par soldat (log + fumi). setup / run / disarm."""
import sys, time, ast, math, re, argparse, json, urllib.request
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import torch, torch.nn as nn
from collections import Counter

LOAD003 = "/home/younes/Bureau/003.ar"
QMODEL = "qwen2.5:32b-instruct-q4_K_M"
CKO = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]
NAG = 50
ENAMES = ["ALPHA", "BRAVO", "CHARLIE"]
EGROUPS = {"ALPHA": [0, 1], "BRAVO": [2, 3], "CHARLIE": [4]}            # indices de groupes LAMBS (5 groupes de 10 = 50)


class OrchNet(nn.Module):
    def __init__(s):
        super().__init__(); s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU()); s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def loadout003():
    try: return str(ast.literal_eval(open(LOAD003).read().strip())[0]).replace("'", '"')
    except Exception: return None


def officer_orders(status, n_en):
    lines = "\n".join("- %s: %d hommes, %dm du FOB, contact:%s" % (nm, status[nm]["alive"], status[nm]["dist"], "oui" if status[nm]["contact"] else "non") for nm in ENAMES)
    keys = ", ".join('"%s":"ASSAUT|APPUI|FLANC_G|FLANC_D|RESERVE"' % nm for nm in ENAMES)
    prompt = ("Tu es l'OFFICIER d'un assaut BLUFOR sur un FOB ennemi. Etat des elements:\n%s\nEnnemis: %d.\n"
              "Donne a CHAQUE element UN ordre : ASSAUT (prendre le FOB), APPUI (base de feu qui FIXE), FLANC_G, FLANC_D, RESERVE. "
              "Coordonne : en general 1 APPUI fixe pendant qu'un autre ASSAUT ou FLANC. "
              "JSON STRICT: {\"ordres\":{%s}, \"intention\":\"1 phrase\"}.") % (lines, n_en, keys)
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat",
            data=json.dumps({"model": QMODEL, "messages": [{"role": "user", "content": prompt}], "stream": False,
                             "format": "json", "keep_alive": "40m", "options": {"temperature": 0.2, "num_ctx": 4096}}).encode(),
            headers={"Content-Type": "application/json"})
        return json.loads(json.loads(urllib.request.urlopen(req, timeout=60).read())["message"]["content"])
    except Exception as e:
        return {"ordres": {nm: "ASSAUT" for nm in ENAMES}, "intention": "defaut(%s)" % str(e)[:40]}


def apply_roles(b, orders, fx, fy):
    for nm in ENAMES:
        role = orders.get(nm, "ASSAUT"); g = "[" + ",".join(map(str, EGROUPS[nm])) + "]"
        if role == "ASSAUT":
            b.send("{ [HMT_WGRPS select _x, 700] spawn lambs_wp_fnc_taskRush } forEach %s;" % g)
        elif role in ("FLANC_G", "FLANC_D"):
            tx = fx - 110 if role == "FLANC_G" else fx + 110
            b.send("{ private _gr=HMT_WGRPS select _x; { _x setSpeedMode \"FULL\"; _x doMove [%d,%d,0] } forEach units _gr } forEach %s;" % (tx, fy, g))
        elif role == "APPUI":
            b.send("{ private _gr=HMT_WGRPS select _x; { doStop _x; _x setUnitPos \"MIDDLE\"; _x doSuppressiveFire [%d,%d,0] } forEach units _gr } forEach %s;" % (fx, fy, g))
        elif role == "RESERVE":
            b.send("{ { doStop _x } forEach units (HMT_WGRPS select _x) } forEach %s;" % g)


def setup_sqf(sx, sy, ld):
    setl = ("{ _x setUnitLoadout %s } forEach HMT_WPILOT; " % ld) if ld else ""
    loop = ("private _try=0; while { count HMT_WPILOT < %d && _try < 500 } do { _try=_try+1; "
            "if ((count HMT_WPILOT) mod 10 == 0) then { HMT_WG = createGroup west }; "
            "private _px=%d+(random 70)-35; private _py=%d-(random 50); "
            "private _u = HMT_WG createUnit [\"B_soldier_F\",[_px,_py,0],[],0,\"NONE\"]; "
            "if (!isNull _u) then { _u allowDamage false; _u setPosATL [_px,_py,0]; HMT_WPILOT pushBack _u }; }; ") % (NAG, sx, sy)
    return ("[] spawn { if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[]; "
            + loop + setl + "call HMT_WARM; { if (!isNull _x) then { _x allowDamage true } } forEach HMT_WPILOT; "
            "(format [\"HARMATTAN_WL west=%1 grps=%2\", count HMT_WPILOT, count HMT_WGRPS]) call HMT_EMIT; };")


def parse(payload):
    m = re.search(r"east=(\d+)", payload); east = int(m.group(1)) if m else -1
    left, _, right = payload.partition("|")
    shells = [[int(f[0]), int(f[1]), int(f[2]), int(f[3])] for f in (t.split(",") for t in right.strip().rstrip(";").split(";")) if len(f) >= 4 and f[0].lstrip("-").isdigit()]
    me = re.search(r"en=(\[.*\])", left)
    try: enemies = ast.literal_eval(me.group(1)) if me else []
    except Exception: enemies = []
    return shells, enemies, east


def estatus(shells, enemies, fx, fy):
    st = {}
    for k, nm in enumerate(ENAMES):
        idx = range(EGROUPS[nm][0] * 10, (EGROUPS[nm][-1] + 1) * 10)
        al = [shells[i] for i in idx if i < len(shells) and shells[i][3] == 1]
        n = len(al)
        if n == 0: st[nm] = {"alive": 0, "dist": 999, "contact": False}
        else:
            cx = sum(s[0] for s in al) / n; cy = sum(s[1] for s in al) / n
            d = sum(math.hypot(s[0] - fx, s[1] - fy) for s in al) / n
            st[nm] = {"alive": n, "dist": int(d), "contact": any(math.hypot(cx - e[0], cy - e[1]) < 170 for e in enemies)}
    return st


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["setup", "run", "disarm"])
    ap.add_argument("--fob", default="3253,2984"); ap.add_argument("--steps", type=int, default=30)
    a = ap.parse_args(); fx, fy = [int(v) for v in a.fob.split(",")]; sx, sy = fx, fy + 200
    b = NativeBridge(port=5816)

    if a.cmd == "setup":
        b.send('call compile preprocessFileLineNumbers "blufor_coquille_lambs.sqf";'); time.sleep(0.5)
        for f in ("orch_features_v6.sqf", "tactics_exec_v2.sqf"): b.send('call compile preprocessFileLineNumbers "%s";' % f)
        ld = loadout003()
        r = b.query(setup_sqf(sx, sy, ld), r"HARMATTAN_WL west=(\d+) grps=(\d+)", want=1, timeout=120)
        print("MARIAGE en place : coquilles=%s groupes=%s | loadout 003=%s" % (r[-1].group(1), r[-1].group(2), "ok" if ld else "defaut") if r else "setup: pas de reponse")
        return

    if a.cmd == "disarm":
        b.send("if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[];")
        print("nettoye"); return

    onet = OrchNet(); onet.load_state_dict(torch.load(CKO, map_location="cpu")); onet.eval()
    b.send("private _es = allUnits select {side _x==east && alive _x}; { private _e=_x; { _e reveal [_x,3] } forEach HMT_WPILOT } forEach _es; { private _w=_x; { _w reveal [_x,3] } forEach _es } forEach HMT_WPILOT;")
    time.sleep(1)
    print("=== MARIAGE : Qwen officier -> commander/roles -> orchestration -> CORPS LAMBS ===", flush=True)
    orders = {nm: "ASSAUT" for nm in ENAMES}; odist = {}; east0 = None
    for step in range(a.steps):
        r = b.query("call HMT_WREAD;", r"HARMATTAN_WRX (.+)", want=1, timeout=12)
        if not r: time.sleep(1); continue
        shells, enemies, east = parse(r[-1].group(1))
        if east0 is None: east0 = east
        st = estatus(shells, enemies, fx, fy)
        if step % 8 == 0:                                    # OFFICIER Qwen 32B
            oo = officer_orders(st, len(enemies)); orders = {nm: oo.get("ordres", {}).get(nm, orders[nm]) for nm in ENAMES}
            print("  [OFFICIER 32B] %s | %s" % (str(oo.get("intention", ""))[:60], orders), flush=True)
        if step % 4 == 0: apply_roles(b, orders, fx, fy)     # execution LAMBS par element
        if step % 3 == 0:                                    # ORCHESTRATION : tactique par soldat
            live = [(s[0], s[1]) for s in shells if s[3] == 1]
            if live:
                cx = int(sum(x for x, y in live) / len(live)); cy = int(sum(y for x, y in live) / len(live))
                rs = b.query("[[%d,%d,0],%d,west] call HMT_ORCH_SNAP;" % (cx, cy, NAG), r"HARMATTAN_ORCH (\[.*\]) \| (\[.*\])", want=1, timeout=8)
                if rs:
                    try: vs = ast.literal_eval(rs[-1].group(1))
                    except Exception: vs = []
                    if vs:
                        with torch.no_grad(): tacs = onet(torch.tensor(vs, dtype=torch.float32))[0].argmax(1).tolist()
                        odist = dict(Counter(TAC[t] for t in tacs))
        nliv = sum(st[nm]["alive"] for nm in ENAMES)
        pen = min((math.hypot(s[0]-fx, s[1]-fy) for s in shells if s[3] == 1), default=999)
        det = " ".join("%s:%d@%dm(%s)" % (nm[0], st[nm]["alive"], st[nm]["dist"], str(orders.get(nm))[:4]) for nm in ENAMES)
        print("  [%02d] vivants=%d/%d ->FOB=%3.0fm | %s | LAMBS EAST=%d (dep %s) | tac=%s" % (step, nliv, NAG, pen, det, east, east0, odist or "-"), flush=True)
        if nliv == 0: print("  -> aneantie"); break
        if pen < 25: print("  -> FOB PRIS !"); break
        time.sleep(1.3)
    print("=== fin ===", flush=True)


if __name__ == "__main__":
    main()
