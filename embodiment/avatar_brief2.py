"""avatar_brief2 — BRIEFING (officier-LLM, langage naturel) + MÉMOIRE = CONTEXTE, version complète.
L'officier (qwen2.5:14b) rédige un briefing en LANGAGE NATUREL ; le soldat l'ingère dans sa mémoire, AVANCE vers
l'objectif, et ANTICIPE une menace de flanc encore CACHÉE (il surveille la bonne direction avant de la voir).
Métrique : erreur de cap vers la menace réelle, dans la fenêtre AVANT le 1er contact visuel, puis AU contact.
args: mode(briefed/blind) server_idx seed cycles.   La chaîne : officier -> mémoire -> orientation du corps."""
import time, re, sys, math, json
import urllib.request
sys.path.insert(0, "/home/younes/arma3-marl")
from op_arma import OpArma
from memory_system import MemorySystem
import paros as M
SB = "/mnt/data/harmattan-sandbox"
MODE = sys.argv[1] if len(sys.argv) > 1 else "briefed"
SRV = int(sys.argv[2]) if len(sys.argv) > 2 else 7
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 90
CYCLES = int(sys.argv[4]) if len(sys.argv) > 4 else 170
cx, cy = (M.COMPLEXE[0], M.COMPLEXE[1] - 180)
OBJ = (cx, cy)
E_FLANC = (cx + 52, cy + 8)            # ennemi RÉEL : flanc droit (nord-est), caché au départ
START = (cx, cy - 75)
SIGHT = 68.0                           # portée de perception (l'ennemi est au-delà au départ -> non vu)


def officier_briefing():
    """L'officier-LLM rédige le briefing en langage naturel + la direction de la menace."""
    sys_p = ("Tu es un officier d'infanterie qui briefe un soldat avant un assaut. Sois bref, clair, ton militaire. "
             "Réponds STRICTEMENT en JSON : {\"briefing\":\"2-3 phrases\",\"direction_menace\":\"nord-est|est|nord|nord-ouest\",\"consigne\":\"posture\"}")
    usr = ("Mission : progresser vers un objectif plein NORD, à découvert. Renseignement : un tireur ennemi est "
           "présumé sur le FLANC DROIT (nord-est), non encore visible. Briefe le soldat.")
    body = json.dumps({"model": "qwen2.5:14b", "stream": False, "format": "json",
                       "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": usr}]}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/chat", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(json.loads(r.read())["message"]["content"])
        return d
    except Exception as e:
        return {"briefing": "Soldat, objectif plein nord. Tireur présumé sur ton flanc droit, nord-est. Surveille-le en progressant, reste bas.",
                "direction_menace": "nord-est", "consigne": "prudence, surveiller le flanc droit", "_fallback": str(e)}


DIRS = {"nord": (0, 1), "nord-est": (0.7, 0.7), "est": (1, 0), "nord-ouest": (-0.7, 0.7)}
env = OpArma(squads=(("AV", 1),), mission=SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SRV,
             log=SB + "/logs/server%d.out" % SRV, acc=1.0, seed=SEED)
env.spawn({"AV": START}, [(E_FLANC[0], E_FLANC[1], 1, 1)])
env.b.send('private _g = group (AV select 0); while {count waypoints _g > 0} do {deleteWaypoint [_g, 0]};'
           '{ _x setVariable ["lambs_danger_disableGroupAI", true]; _x allowFleeing 0; } forEach units _g;'
           'private _av = AV select 0; _av setBehaviour "AWARE"; _av setCombatMode "BLUE"; _av forceSpeed 3;'
           '{ _x enableAI "ALL"; _x setSkill 0.55; _x setBehaviour "COMBAT"; _x setCombatMode "RED"; _x setUnitPos "UP"; } forEach HMT_EN;', wait=True)
time.sleep(2)
mem = MemorySystem(14, OBJ, plan=[("rejoindre", OBJ)])
presume = None
if MODE == "briefed":
    b = officier_briefing()
    print("=== BRIEFING DE L'OFFICIER (langage naturel, qwen2.5:14b) ===", flush=True)
    print("   « %s »" % b.get("briefing", ""), flush=True)
    print("   [direction menace: %s | consigne: %s]%s" % (b.get("direction_menace"), b.get("consigne"), " (LLM indispo, fallback)" if b.get("_fallback") else ""), flush=True)
    dx, dy = DIRS.get(str(b.get("direction_menace", "")).lower(), (0.7, 0.7))   # direction -> point présumé à ~95 m
    presume = (cx + int(95 * dx), (cy - 75) + int(95 * dy))
    mem.episodique.tau = 1e9
    mem.episodique.slots[99] = {"x": presume[0], "y": presume[1], "t_last": 0.0, "conf": 0.6, "dmg": 0, "seen_count": 0}
print("=== AVANCE + ANTICIPATION : MODE=%s ===" % MODE, flush=True)
t0 = time.time(); first_seen = None; err_avant = []; ori_avant = 0; n_avant = 0; err_at_contact = None; last_send = -9


def capv(px, py, tx, ty):
    return (math.degrees(math.atan2(tx - px, ty - py)) + 360) % 360


def errc(a, b):
    return abs((a - b + 180) % 360 - 180)


for c in range(CYCLES):
    ls = env._query('private _u = AV select 0; private _p = getPosATL _u;'
                    ' diag_log format ["AV %1 %2 %3 %4", round(_p#0), round(_p#1), round(getDir _u), round((getDammage _u)*100)];'
                    ' private _e = HMT_EN select 0; private _q = getPosATL _e; private _d = (AV select 0) distance _e; private _vis = 0;'
                    ' if (alive _e && {_d < ' + str(int(SIGHT)) + '} && {(count (lineIntersectsSurfaces [eyePos _u, eyePos _e, _u, _e])) == 0}) then { _vis = 1; };'
                    ' diag_log format ["EN %1 %2 %3", round(_q#0), round(_q#1), _vis];', settle=0.08)
    px, py, hdir, dmg, ex, ey, vis = START[0], START[1], 0, 0.0, E_FLANC[0], E_FLANC[1], 0
    for l in ls:
        m = re.search(r"AV (-?\d+) (-?\d+) (\d+) (\d+)", l)
        if m:
            px = int(m.group(1)); py = int(m.group(2)); hdir = int(m.group(3)); dmg = int(m.group(4)) / 100.0
        me = re.search(r"EN (-?\d+) (-?\d+) (\d+)", l)
        if me:
            ex = int(me.group(1)); ey = int(me.group(2)); vis = int(me.group(3))
    now = time.time() - t0
    if MODE == "briefed":
        mem.episodique.observe([(99, ex, ey, 0, vis == 1)], now)
    cap_menace = capv(px, py, ex, ey); e = errc(hdir, cap_menace)
    if vis and first_seen is None:
        first_seen = now; err_at_contact = e
    if first_seen is None:
        err_avant.append(e); n_avant += 1
        if e < 45:
            ori_avant += 1
    # --- avance + orientation ---
    if MODE == "briefed":
        watch = (mem.episodique.nearest(now, px, py) or {"x": OBJ[0], "y": OBJ[1]})
        wx, wy = int(watch["x"]), int(watch["y"])
    else:
        wx, wy = OBJ                                   # aveugle : regarde l'objectif
    if c - last_send >= 6:
        env.b.send('private _u = AV select 0; _u forceSpeed 3; _u doMove [%d,%d,0]; _u doWatch [%d,%d,0];' % (OBJ[0], OBJ[1], wx, wy), wait=True); last_send = c
    if c % 6 == 0:
        do = math.hypot(OBJ[0] - px, OBJ[1] - py)
        tag = "VU" if vis else ("présumé" if (MODE == "briefed" and first_seen is None) else "caché")
        print("  t=%4.1fs|obj %3.0fm|cap %3d°|menace %s (cap %3d°, erreur %3d°)|orienté=%s" % (
            now, do, hdir, tag, int(cap_menace), int(e), "OUI" if e < 45 else "non"), flush=True)
    time.sleep(0.05)
moy = sum(err_avant) / max(len(err_avant), 1); frac = 100.0 * ori_avant / max(n_avant, 1)
print(">>> MODE=%s | AVANT contact: erreur cap moy=%.0f° orienté=%.0f%% | AU 1er contact: erreur=%s | contact à %s" % (
    MODE, moy, frac, ("%.0f°" % err_at_contact) if err_at_contact is not None else "—", ("%.0fs" % first_seen) if first_seen else "jamais"), flush=True)
print("BRIEF2 FINI", flush=True)
