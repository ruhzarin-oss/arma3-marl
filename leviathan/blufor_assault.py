#!/usr/bin/env python3
"""blufor_assault.py — INVERSION BLUFOR full-agent. Une escouade WEST (loadout 003) armee en COQUILLES
(corps appris reflex_r23wh_voyant.pt, LAMBS desactive, pilotage velocite) ASSAUT un FOB EAST tenu par LAMBS.

Reutilise TON pipeline prouve : load_body/synth_hm/parse_rx + AgentSwarm + FobDriver (cote WEST, enemy_side=east).
Pont coquille WEST = blufor_coquille.sqf (HMT_WARM/HMT_WREAD/HMT_WDVX). Le tir EMERGE (aucun doFire).

  setup   : compile le pont WEST, reveille la garnison EAST du FOB, spawn l'escouade WEST+003, l'arme en coquilles
  run     : boucle le corps appris -> velocite -> les coquilles assautent le FOB (REGARDE au spectateur)
  disarm  : retour LAMBS, nettoie

v1 = corps + focus objectif (assaut). L'orchestration (tactiques) se compose en v2."""
import sys, time, ast, math, argparse
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from fob_driver import load_body, synth_hm, parse_rx, FobDriver
from agent_swarm import AgentSwarm

MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
LOAD003 = "/home/younes/Bureau/003.ar"
NAG = 80                                  # force WEST full-agent (80 coquilles)
QMODEL = "qwen2.5:32b-instruct-q4_K_M"    # officier Qwen 32B
CKC = "/home/younes/compose-embodiment/commander.pt"          # SOUS-OFFICIER appris (placement des elements)
CKO = "/home/younes/arma3-marl/leviathan/orchestration_arma_voyant.pt"  # AGENT : tactique par soldat
TAC = ["TIR", "GRENADE", "FLANC", "FUMI", "SUPPR"]
import torch, torch.nn as nn
from collections import Counter


class CNet(nn.Module):                                         # commander.pt : obs17 -> 4 (2 elements x 2 coords)
    def __init__(self, obs=17, act=4, h=256):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(obs, h), nn.Tanh(), nn.Linear(h, h), nn.Tanh())
        self.mu = nn.Linear(h, act); self.v = nn.Linear(h, 1)
        self.log_std = nn.Parameter(torch.zeros(act) - 0.5)
    def forward(self, o):
        h = self.body(o); return self.mu(h), self.v(h).squeeze(-1)


class OrchNet(nn.Module):                                      # orchestration : 10 features -> 5 tactiques
    def __init__(s):
        super().__init__()
        s.b = nn.Sequential(nn.Linear(10, 128), nn.ReLU(), nn.Linear(128, 128), nn.ReLU())
        s.a = nn.Linear(128, 5); s.v = nn.Linear(128, 1)
    def forward(s, x):
        h = s.b(x); return s.a(h), s.v(h)


def loadout003():
    try:
        return str(ast.literal_eval(open(LOAD003).read().strip())[0]).replace("'", '"')
    except Exception as e:
        print("[003] illisible (%s) -> loadout par defaut" % e, flush=True); return None


def general_intent(dist, nguards, nalive):
    """OFFICIER Qwen : lit l'assaut -> intention. Pattern de full_stack (l'officier reflechit pendant que ca avance)."""
    import json, urllib.request
    prompt = ("Tu commandes un assaut BLUFOR : %d hommes (coquilles full-agent) a ~%dm d'un FOB ennemi tenu par "
              "~%d defenseurs. But : PRENDRE le FOB avec le moins de pertes. Choisis l'intention d'assaut. "
              "Reponds STRICT JSON {\"intent\":\"PRESSER|FLANC_G|FLANC_D\",\"raison\":\"court\"}.") % (nalive, dist, nguards)
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat",
            data=json.dumps({"model": QMODEL, "messages": [{"role": "user", "content": prompt}],
                             "stream": False, "format": "json", "keep_alive": "30m",
                             "options": {"temperature": 0.2, "num_ctx": 4096}}).encode(),
            headers={"Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return json.loads(r["message"]["content"])
    except Exception as e:
        return {"intent": "PRESSER", "raison": "defaut(%s)" % str(e)[:40]}


def officer_orders(status, enames, fobx, foby, n_en):
    """VRAI OFFICIER Qwen 32B : lit l'etat PAR ELEMENT -> un ordre PAR element. Re-decide periodiquement, realloue."""
    import json, urllib.request
    lines = "\n".join("- %s: %d hommes, %dm du FOB, contact:%s"
                      % (nm, status[nm]["alive"], status[nm]["dist"], "oui" if status[nm]["contact"] else "non") for nm in enames)
    keys = ", ".join('"%s":"ASSAUT|APPUI|FLANC_G|FLANC_D|RESERVE"' % nm for nm in enames)
    prompt = ("Tu es l'OFFICIER d'un assaut BLUFOR sur un FOB ennemi. Etat des elements:\n%s\n"
              "Ennemis detectes: %d.\n"
              "Donne a CHAQUE element UN ordre parmi : ASSAUT (prendre le FOB), APPUI (base de feu qui FIXE l'ennemi), "
              "FLANC_G (contourne par l'ouest), FLANC_D (par l'est), RESERVE (tenir en arriere, engager plus tard). "
              "COORDONNE : en general 1 element APPUI fixe pendant qu'un autre ASSAUT ou FLANC ; realloue selon les pertes. "
              "Reponds STRICT JSON : {\"ordres\":{%s}, \"intention\":\"1 phrase courte\"}.") % (lines, n_en, keys)
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat",
            data=json.dumps({"model": QMODEL, "messages": [{"role": "user", "content": prompt}],
                             "stream": False, "format": "json", "keep_alive": "30m",
                             "options": {"temperature": 0.2, "num_ctx": 4096}}).encode(),
            headers={"Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return json.loads(r["message"]["content"])
    except Exception as e:
        return {"ordres": {nm: "ASSAUT" for nm in enames}, "intention": "defaut(%s)" % str(e)[:40]}


def setup_sqf(fobx, foby, sx, sy, ld):
    setl = ("{ _x setUnitLoadout %s; } forEach HMT_WPILOT; " % ld) if ld else ""
    # spawn ROBUSTE : invulnerable PENDANT le placement (evite les morts a la creation : collision/relief), etale, boucle jusqu'a NAG
    loop = ("private _try=0; "
            "while { count HMT_WPILOT < %d && _try < 500 } do { _try = _try + 1; "
            "if ((count HMT_WPILOT) mod 10 == 0) then { HMT_WG = createGroup west }; "
            "private _px=%d+(random 70)-35; private _py=%d-(random 50); "
            "private _u = HMT_WG createUnit [\"B_soldier_F\", [_px,_py,0], [], 0, \"NONE\"]; "
            "if (!isNull _u) then { _u allowDamage false; _u setPosATL [_px,_py,0]; _u setSkill 0.7; _u setBehaviour \"AWARE\"; _u setCombatMode \"RED\"; HMT_WPILOT pushBack _u; }; }; ") % (NAG, sx, sy)
    gar = "count (allUnits select { side _x==east && _x distance2D [" + str(fobx) + "," + str(foby) + "] < 300 })"
    # PLACEMENT SEUL : on ne reveille NI ne revele la garnison. Le run s'en charge. Degats reactives une fois posees.
    return ("[] spawn { "
        "if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[]; "
        + loop + setl + "call HMT_WARM; { if (!isNull _x) then { _x allowDamage true } } forEach HMT_WPILOT; "
        "(format [\"HARMATTAN_WSETUP west=%1 mode=%2 essais=%3 gar=%4\", count HMT_WPILOT, HMT_WAGENT_MODE, _try, " + gar + "]) call HMT_EMIT; "
        "};")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["setup", "run", "disarm"])
    ap.add_argument("--fob", default="3253,2984")           # FOB EAST cible (Maxwell par defaut)
    ap.add_argument("--stage", default=None)                # point de depart WEST (defaut : 200 m au nord)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--no-officer", action="store_true")    # couper l'officier Qwen (corps seul)
    a = ap.parse_args()
    fobx, foby = [int(v) for v in a.fob.split(",")]
    if a.stage:
        sx, sy = [int(v) for v in a.stage.split(",")]
    else:
        sx, sy = fobx, foby + 200                           # depart 200 m nord, assaut vers le sud
    b = NativeBridge(port=5816)

    if a.cmd == "setup":
        b.send('call compile preprocessFileLineNumbers "blufor_coquille.sqf";'); time.sleep(0.5)
        ld = loadout003()
        r = b.query(setup_sqf(fobx, foby, sx, sy, ld), r"HARMATTAN_WSETUP west=(\d+) mode=(\w+) essais=(\d+) gar=(\d+)", want=1, timeout=120)
        if not r:
            time.sleep(4)                                   # spawn de 80 + loadout = lent : verifie l'etat reel
            rr = b.query("(format [\"HARMATTAN_WCHK west=%1 mode=%2\", count HMT_WPILOT, HMT_WAGENT_MODE]) call HMT_EMIT;",
                         r"HARMATTAN_WCHK west=(\d+) mode=(\w+)", want=1, timeout=20)
            if rr:
                print("=== FORCE EN PLACE (emit lent) : coquilles WEST=%s  arme=%s  loadout 003=%s ==="
                      % (rr[-1].group(1), rr[-1].group(2), "applique" if ld else "defaut"), flush=True)
            else:
                print("SETUP : pas de reponse (pont WEST compile ? serveur up ?)", flush=True)
            return
        m = r[-1]
        print("=== ESCOUADE BLUFOR full-agent EN PLACE ===", flush=True)
        print("  coquilles WEST=%s/%d  arme(mode)=%s  (%s essais de placement)" % (m.group(1), NAG, m.group(2), m.group(3)), flush=True)
        print("  loadout 003 = %s | garnison EAST a proximite=%s (endormie)" % ("applique" if ld else "defaut (003 illisible)", m.group(4)), flush=True)
        print("  objectif FOB EAST [%d,%d] | depart WEST [%d,%d]" % (fobx, foby, sx, sy), flush=True)
        print("  -> reconnecte-toi (:3902) pour animer, puis 'run'", flush=True)
        return

    if a.cmd == "disarm":
        b.query("call HMT_WDISARM; (format [\"HARMATTAN_WDIS ok\"]) call HMT_EMIT;", r"HARMATTAN_WDIS ok", want=1, timeout=15)
        b.send("if (!isNil \"HMT_WPILOT\") then { { if (!isNull _x) then { deleteVehicle _x } } forEach HMT_WPILOT }; HMT_WPILOT=[];")
        print("Desarme + escouade WEST nettoyee.", flush=True); return

    # --- run : le corps appris pilote les coquilles vers le FOB (assaut) ---
    HM, hx0, hy0, hres, HN = synth_hm()
    sw = AgentSwarm(load_body("cpu"), HM, hx0, hy0, hres, HN, group_var="HMT_WPILOT", enemy_side="east", device="cpu")
    drv = FobDriver(sw, [(fobx, foby)], speed=5.0)
    drv.focus = (fobx, foby)                                 # objectif de manoeuvre (AUCUNE menace : juste BLUFOR)
    # LES 2 MAILLONS : sous-officier (placement) + agent (tactique par soldat)
    cnet = CNet(17, 4); cnet.load_state_dict(torch.load(CKC, map_location="cpu")); cnet.eval()
    onet = OrchNet(); onet.load_state_dict(torch.load(CKO, map_location="cpu")); onet.eval()
    for _f in ("orch_features_v6.sqf", "tactics_exec_v2.sqf"):
        b.send('call compile preprocessFileLineNumbers "%s";' % _f)
    print("[CHAINE COMPLETE] officier Qwen 32B -> commander.pt -> orchestration -> corps reflex_r23wh", flush=True)
    # revele l'ennemi EAST aux coquilles (et inversement) pour que la chaine le DETECTE (necessaire a 0 joueur)
    b.send("private _es = allUnits select {side _x==east && alive _x}; "
           "{ private _e=_x; { _e reveal [_x,3] } forEach HMT_WPILOT } forEach _es; "
           "{ private _w=_x; { _w reveal [_x,3] } forEach _es } forEach HMT_WPILOT;")
    time.sleep(1)

    def read():
        r = b.query("call HMT_WREAD;", r"HARMATTAN_WRX (.+)", want=1, timeout=12)
        return parse_rx(r[-1].group(1)) if r else ([], [])

    print("=== ASSAUT BLUFOR full-agent -> FOB EAST [%d,%d] | OFFICIER 32B par elements ===" % (fobx, foby), flush=True)
    ENAMES = ["ALPHA", "BRAVO", "CHARLIE"]
    esize = (NAG + len(ENAMES) - 1) // len(ENAMES)
    elems = {ENAMES[k]: list(range(k * esize, min((k + 1) * esize, NAG))) for k in range(len(ENAMES))}
    TARGETS = {"ASSAUT": (fobx, foby), "APPUI": (fobx - 110, foby + 70),
               "FLANC_G": (fobx - 100, foby), "FLANC_D": (fobx + 100, foby), "RESERVE": (fobx, foby + 200)}

    def estatus(shells, enemies):
        st = {}
        for nm in ENAMES:
            al = [shells[i] for i in elems[nm] if i < len(shells) and len(shells[i]) >= 4 and shells[i][3] == 1]
            n = len(al)
            if n == 0:
                st[nm] = {"alive": 0, "dist": 999, "contact": False, "cx": fobx, "cy": foby}
            else:
                cx = sum(s[0] for s in al) / n; cy = sum(s[1] for s in al) / n
                d = sum(math.hypot(s[0] - fobx, s[1] - foby) for s in al) / n
                ct = any(math.hypot(cx - e[0], cy - e[1]) < 160 for e in enemies)
                st[nm] = {"alive": n, "dist": int(d), "contact": ct, "cx": cx, "cy": cy}
        return st

    def cmd_place(status, adv):                             # SOUS-OFFICIER commander.pt : ou vont les elements qui avancent
        S = 200.0; R = 95.0; parts = []
        for k in range(2):
            if k < len(adv):
                st = status[adv[k]]; sz = max(1, len(elems[adv[k]]))
                parts += [(st["cx"] - fobx) / S, (st["cy"] - foby) / S, min(st["alive"] / sz, 1.0), 0.0, 0.0, 0.0, 2.0]
            else:
                parts += [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]
        nliv = sum(status[nm]["alive"] for nm in ENAMES)
        parts += [0.0, min(nliv / float(NAG), 1.0), 0.5]    # guards=0 (aucun ennemi), fraction vivants, mi-course
        with torch.no_grad():
            mu, _ = cnet(torch.tensor(parts, dtype=torch.float32)); act = mu.clamp(-1, 1).view(2, 2)
        return [(fobx + float(act[k, 0]) * R, foby + float(act[k, 1]) * R) for k in range(2)]

    orders = {nm: "ASSAUT" for nm in ENAMES}
    odist = {}
    OFFICER_EVERY = 8                                        # l'officier re-decide tous les ~10 s (tier lent)
    for step in range(a.steps):
        shells, enemies = read()
        if not shells:
            print("  [%02d] 0 coquille active (setup fait ? arme ?)" % step, flush=True); time.sleep(0.8); continue
        # juste BLUFOR : ne garder que les EAST A PORTEE reelle (le monde persistant est connu de loin, hors menace)
        livepos = [(s[0], s[1]) for s in shells if len(s) >= 4 and s[3] == 1]
        enemies = [e for e in enemies if any(math.hypot(e[0] - x, e[1] - y) < 400 for x, y in livepos)]
        status = estatus(shells, enemies)
        if not a.no_officer and step % OFFICER_EVERY == 0:  # OFFICIER Qwen 32B : ordre par element (re-decision)
            oo = officer_orders(status, ENAMES, fobx, foby, len(enemies))
            orders = {nm: oo.get("ordres", {}).get(nm, orders[nm]) for nm in ENAMES}
            print("  [OFFICIER 32B] %s | %s" % (str(oo.get("intention", ""))[:70], orders), flush=True)
        adv = [nm for nm in ENAMES if orders.get(nm) in ("ASSAUT", "FLANC_G", "FLANC_D")][:2]
        cmdt = cmd_place(status, adv) if adv else []         # SOUS-OFFICIER : ou vont les elements qui avancent
        for nm in ENAMES:
            if nm in adv and cmdt:
                tx, ty = cmdt[adv.index(nm)]                 # placement appris (commander.pt)
            else:
                tx, ty = TARGETS.get(orders.get(nm, "ASSAUT"), (fobx, foby))
            for i in elems[nm]:
                drv.flank_goals[i] = [tx, ty]
        dvx, dvy, ddir = drv.tick(shells, enemies)
        b.send("HMT_WDVX = %s; HMT_WDVY = %s; HMT_WDDIR = %s;" % (dvx, dvy, ddir))
        if step % 3 == 0 and livepos:                        # AGENT orchestration : tactique par soldat (~4s)
            cfx = int(sum(x for x, y in livepos) / len(livepos)); cfy = int(sum(y for x, y in livepos) / len(livepos))
            rs = b.query("[[%d,%d,0],%d,west] call HMT_ORCH_SNAP;" % (cfx, cfy, NAG), r"HARMATTAN_ORCH (\[.*\]) \| (\[.*\])", want=1, timeout=8)
            if rs:
                try: vs = ast.literal_eval(rs[-1].group(1))
                except Exception: vs = []
                if vs:
                    with torch.no_grad(): tacs = onet(torch.tensor(vs, dtype=torch.float32))[0].argmax(1).tolist()
                    odist = dict(Counter(TAC[t] for t in tacs))
        nliv = sum(status[nm]["alive"] for nm in ENAMES)
        pen = min((math.hypot(s[0] - fobx, s[1] - foby) for s in shells if len(s) >= 4 and s[3] == 1), default=999)
        detail = " ".join("%s:%d@%dm(%s)" % (nm[0], status[nm]["alive"], status[nm]["dist"], str(orders.get(nm, "?"))[:4]) for nm in ENAMES)
        print("  [%02d] vivants=%d/%d ->FOB=%3.0fm | %s | tactiques=%s | ennemis=%d" % (step, nliv, NAG, pen, detail, odist or "-", len(enemies)), flush=True)
        if pen < 25:
            print("  >>> FOB ATTEINT par l'assaut full-agent !", flush=True); break
        if nliv == 0:
            print("  -> force aneantie.", flush=True); break
        time.sleep(1.2)
    b.send("{ HMT_WDVX set [_forEachIndex,0]; HMT_WDVY set [_forEachIndex,0]; } forEach HMT_WPILOT;")
    print("=== fin run (coquilles a l'arret ; 'disarm' pour rendre a LAMBS + nettoyer) ===", flush=True)


if __name__ == "__main__":
    main()
