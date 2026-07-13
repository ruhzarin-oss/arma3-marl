#!/usr/bin/env python3
"""shamal_arma.py — L'EXECUTEUR : pilote de vrais soldats Arma WEST par la politique SHAMAL
(shamal_arma_win.pt), ZERO LAMBS. Boucle : 17 features/soldat depuis Arma -> Net -> commande Arma
(cap->doMove, SUPPRESS->doSuppressiveFire, posture->setUnitPos). Officier Qwen au-dessus (intention
+ point d'objectif par element). Reutilise le tuyau de blufor_full.py (pont natif, spawn, officier).

  setup : spawn NAG WEST (loadout 003), compile shamal_obs.sqf, coupe LAMBS (HMT_SHAMAL_ARM)
  run   : boucle capteur -> politique -> actuateur + officier Qwen
  disarm: nettoie
"""
import sys, time, ast, math, re, argparse, json, urllib.request
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import torch
from train_koth_gpu import Net

CKPT = "/home/younes/arma3-marl/shamal_arma_win.pt"
LOAD003 = "/home/younes/Bureau/003.ar"
QMODEL = "qwen2.5:32b-instruct-q4_K_M"
NAG = 50
SCALE = 200.0            # normalisation position/distance (doit matcher l'echelle d'entrainement)
D_TRAIN = 6              # garnison d'entrainement (pour normaliser la menace, suffer[1])
OBS_DIM, N_ACT = 17, 13
ENAMES = ["ALPHA", "BRAVO", "CHARLIE"]
# decoupage des NAG soldats en 3 elements (par index)
def egroups(nag):
    k = nag // 3
    return {"ALPHA": list(range(0, k)), "BRAVO": list(range(k, 2 * k)), "CHARLIE": list(range(2 * k, nag))}


def loadout003():
    try: return str(ast.literal_eval(open(LOAD003).read().strip())[0]).replace("'", '"')
    except Exception: return None


def officer_orders(status, n_en):
    lines = "\n".join("- %s: %d hommes, %dm du FOB, contact:%s" % (nm, status[nm]["alive"], status[nm]["dist"], "oui" if status[nm]["contact"] else "non") for nm in ENAMES)
    keys = ", ".join('"%s":"ASSAUT|APPUI|FLANC_G|FLANC_D|RESERVE"' % nm for nm in ENAMES)
    prompt = ("Tu es l'OFFICIER d'un assaut BLUFOR sur un FOB ennemi. Etat des elements:\n%s\nEnnemis: %d.\n"
              "Donne a CHAQUE element UN ordre : ASSAUT (prendre le FOB), APPUI (fixer par le feu), FLANC_G, FLANC_D, RESERVE. "
              "En general 1 APPUI fixe pendant qu'un autre ASSAUT ou FLANC. "
              "JSON STRICT: {\"ordres\":{%s}, \"intention\":\"1 phrase\"}.") % (lines, n_en, keys)
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat",
            data=json.dumps({"model": QMODEL, "messages": [{"role": "user", "content": prompt}], "stream": False,
                             "format": "json", "keep_alive": "40m", "options": {"temperature": 0.2, "num_ctx": 4096}}).encode(),
            headers={"Content-Type": "application/json"})
        return json.loads(json.loads(urllib.request.urlopen(req, timeout=60).read())["message"]["content"])
    except Exception as e:
        return {"ordres": {nm: "ASSAUT" for nm in ENAMES}, "intention": "defaut(%s)" % str(e)[:40]}


def role_target(role, fx, fy):
    """Ordre officier -> point d'objectif que SHAMAL vise pour cet element."""
    if role == "FLANC_G": return (fx - 90, fy)
    if role == "FLANC_D": return (fx + 90, fy)
    return (fx, fy)                     # ASSAUT / APPUI / RESERVE -> le FOB


def setup_sqf(sx, sy, fx, fy, ld):
    setl = ("{ _x setUnitLoadout %s } forEach HMT_WPILOT; " % ld) if ld else ""
    loop = ("private _try=0; while { count HMT_WPILOT < %d && _try < 500 } do { _try=_try+1; "
            "if ((count HMT_WPILOT) mod 10 == 0) then { HMT_WG = createGroup west }; "
            "private _px=%d+(random 70)-35; private _py=%d-(random 50); "
            "private _u = HMT_WG createUnit [\"B_soldier_F\",[_px,_py,0],[],0,\"NONE\"]; "
            "if (!isNull _u) then { _u allowDamage false; _u setPosATL [_px,_py,0]; HMT_WPILOT pushBack _u }; }; ") % (NAG, sx, sy)
    return ("[] spawn { if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[]; "
            "HMT_FOB=[%d,%d]; " % (fx, fy)
            + loop + setl + "call HMT_SHAMAL_ARM; { if (!isNull _x) then { _x allowDamage true } } forEach HMT_WPILOT; "
            "(format [\"HARMATTAN_SHL west=%1\", count HMT_WPILOT]) call HMT_EMIT; };")


def parse_sense(payload):
    """'n=NN | px,py,al,cov,los,nd,dmg,thr,pos ; ...' -> liste de dicts (ordre = HMT_WPILOT)."""
    _, _, right = payload.partition("|")
    rows = []
    for t in right.strip().rstrip(";").split(";"):
        f = t.strip().split(",")
        if len(f) >= 9 and f[0].lstrip("-").isdigit():
            rows.append([float(v) for v in f[:9]])   # px,py,al,cov,los,nd,dmg,thr,pos
    return rows


def build_obs(rows, targets, fx, fy, prev_dmg, sup_mem):
    """Assemble l'obs 17 features/soldat, MEME ordre que le sandbox arma_obs :
       base8 [x,y,dgx,dgy,al,dcov,los,nd] + suffer2 [dmg_delta,thr] + team4 [adx,ady,asup,tf] + posture3."""
    n = len(rows)
    ax = [fx + r[0] for r in rows]; ay = [fy + r[1] for r in rows]   # positions absolues
    alive = [r[2] for r in rows]
    tf = (sum(sup_mem[:n]) / max(sum(alive), 1)) if n else 0.0       # fraction de l'escouade qui supprime
    obs = []
    for i, r in enumerate(rows):
        tx, ty = targets[i]
        relx = (ax[i] - tx) / SCALE; rely = (ay[i] - ty) / SCALE     # position relative a l'objectif de l'element
        al = r[2]
        dcov = min(r[3] / 30.0, 1.0)
        los = r[4]
        nd = min(r[5] / SCALE, 1.0)
        dmg = r[6] / 100.0
        ddmg = max(0.0, dmg - prev_dmg[i]); prev_dmg[i] = dmg
        suf0 = min(1.0, ddmg * 5.0); suf1 = min(1.0, r[7] / D_TRAIN)
        # allie vivant le plus proche
        best = -1; bd = 1e18
        for j in range(n):
            if j != i and alive[j] > 0.5:
                d = (ax[i] - ax[j]) ** 2 + (ay[i] - ay[j]) ** 2
                if d < bd: bd = d; best = j
        if best >= 0:
            adx = (ax[best] - ax[i]) / SCALE; ady = (ay[best] - ay[i]) / SCALE
            asup = 1.0 if sup_mem[best] else 0.0
        else:
            adx = ady = asup = 0.0
        p = int(r[8]); post = [1.0 if p == 0 else 0.0, 1.0 if p == 1 else 0.0, 1.0 if p == 2 else 0.0]
        obs.append([relx, rely, -relx, -rely, al, dcov, los, nd, suf0, suf1, adx, ady, asup, tf] + post)
    return torch.tensor(obs, dtype=torch.float32)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["setup", "run", "disarm"])
    ap.add_argument("--fob", default="3253,2984"); ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--noofficer", action="store_true")
    a = ap.parse_args(); fx, fy = [int(v) for v in a.fob.split(",")]; sx, sy = fx, fy + 140
    b = NativeBridge(port=5816)
    EG = egroups(NAG)

    if a.cmd == "setup":
        b.send('call compile preprocessFileLineNumbers "shamal_obs.sqf";'); time.sleep(0.5)
        ld = loadout003()
        r = b.query(setup_sqf(sx, sy, fx, fy, ld), r"HARMATTAN_SHL west=(\d+)", want=1, timeout=120)
        print("SHAMAL en place : soldats=%s | loadout 003=%s | ZERO LAMBS (FSM coupee)" % (r[-1].group(1) if r else "?", "ok" if ld else "defaut"))
        return

    if a.cmd == "disarm":
        b.send("if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[];")
        print("nettoye"); return

    # --- run ---
    net = Net(OBS_DIM, N_ACT, 512, 3); net.load_state_dict(torch.load(CKPT, map_location="cpu")); net.eval()
    b.send("private _es = allUnits select {side _x==east && alive _x}; { private _e=_x; { _e reveal [_x,4] } forEach HMT_WPILOT } forEach _es; { private _w=_x; { _w reveal [_x,4] } forEach _es } forEach HMT_WPILOT;")
    time.sleep(1)
    print("=== SHAMAL sur ARMA : cerveau appris pilote WEST, ZERO LAMBS%s ===" % ("" if a.noofficer else " + officier Qwen"), flush=True)
    orders = {nm: "ASSAUT" for nm in ENAMES}
    prev_dmg = [0.0] * NAG; sup_mem = [False] * NAG
    for step in range(a.steps):
        r = b.query("call HMT_SHAMAL_SENSE;", r"HARMATTAN_SHS (.+)", want=1, timeout=12)
        if not r: time.sleep(1); continue
        rows = parse_sense(r[-1].group(1))
        if not rows: time.sleep(1); continue
        n = len(rows)
        # etat par element (pour l'officier + le log)
        ax = [fx + row[0] for row in rows]; ay = [fy + row[1] for row in rows]
        st = {}
        for nm in ENAMES:
            idx = [i for i in EG[nm] if i < n]
            al = [i for i in idx if rows[i][2] > 0.5]
            if al:
                d = sum(math.hypot(ax[i] - fx, ay[i] - fy) for i in al) / len(al)
                ctc = any(rows[i][4] > 0.5 for i in al)     # au moins un en LOS ennemie
                st[nm] = {"alive": len(al), "dist": int(d), "contact": ctc}
            else:
                st[nm] = {"alive": 0, "dist": 999, "contact": False}
        # OFFICIER Qwen (intention + roles -> point d'objectif par element)
        if (not a.noofficer) and step % 8 == 0:
            oo = officer_orders(st, sum(st[nm]["contact"] for nm in ENAMES))
            orders = {nm: oo.get("ordres", {}).get(nm, orders[nm]) for nm in ENAMES}
            print("  [OFFICIER 32B] %s | %s" % (str(oo.get("intention", ""))[:60], orders), flush=True)
        # cible par soldat selon l'ordre de son element
        targets = [(fx, fy)] * n
        for nm in ENAMES:
            tgt = role_target(orders[nm], fx, fy)
            for i in EG[nm]:
                if i < n: targets[i] = tgt
        # POLITIQUE SHAMAL -> actions
        obs = build_obs(rows, targets, fx, fy, prev_dmg, sup_mem)
        with torch.no_grad():
            acts = net.a_logits(obs).argmax(-1).tolist()
        sup_mem = [False] * NAG
        for i, ac in enumerate(acts):
            if ac == 9 and i < NAG: sup_mem[i] = True
        # ACTUATEUR
        b.send("HMT_ACTS=%s; call HMT_SHAMAL_APPLY;" % json.dumps(acts))
        # log
        from collections import Counter
        adist = dict(Counter(acts))
        nliv = sum(st[nm]["alive"] for nm in ENAMES)
        pen = min((math.hypot(ax[i] - fx, ay[i] - fy) for i in range(n) if rows[i][2] > 0.5), default=999)
        det = " ".join("%s:%d@%dm(%s)" % (nm[0], st[nm]["alive"], st[nm]["dist"], str(orders.get(nm))[:4]) for nm in ENAMES)
        fire = adist.get(9, 0)
        print("  [%02d] vivants=%d/%d ->FOB=%3.0fm | %s | tirent=%d actions=%s" % (step, nliv, NAG, pen, det, fire, adist), flush=True)
        if nliv == 0: print("  -> aneantie"); break
        if pen < 25: print("  -> FOB PRIS !"); break
        time.sleep(1.2)
    print("=== fin ===", flush=True)


if __name__ == "__main__":
    main()
