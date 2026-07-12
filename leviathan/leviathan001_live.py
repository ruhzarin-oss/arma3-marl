#!/usr/bin/env python3
"""leviathan001_live.py — BRANCHEMENT LIVE de leviathan001 sur server_fob.
(NB: ne PAS nommer leviathan_live.py — ce nom est pris par l'ancien projet faction.)

Double boucle qui partage `driver.focus` :
  RAPIDE (chaque tick) : le driver pilote les coquilles-agents (patrouille / masse / focus) via HMT_READ→HMT_DVX
  LENTE  (tous les N)  : l'officier Qwen lit le SITREP → ordonne → pose driver.focus → RAG record + outcome

Le pays DÉFEND les menaces injectées séparément (ton levier d'expé : spawn de FS ennemis).
Pour une menace de test : voir fob_driver.run_fight (spawn 9 FS). Spectateur : se connecter à :3902 (Stratis)."""
import sys, time, ast, math
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from arma_bridge import ArmaBridge
from native_bridge import NativeBridge
from fob_driver import FobDriver, AgentSwarm, PatrolBrain, parse_rx, load_body, synth_hm
from travel_body import TravelBody
from officer_state import OfficerState, FOBS
from officer_memory import OfficerMemory
from officer import OfficerLoop, qwen_ollama, make_apply
from orchestration_live import Orchestrator                       # ETAPE 4 : tete de selection de tactique

MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
NODES = [(f[1], f[2]) for f in FOBS]
OFFICER_EVERY = 10        # l'officier décide tous les 10 ticks (~10 s) — tier stratégique lent
REARM_EVERY = 30          # re-arme l'ensemble actif (capte les défenseurs nouvellement réveillés par le contact)
STEPS = 1000000        # run long (session de jeu) — ~indefini, le watchdog relance si besoin


def read_def(b):
    r = b.query('call HMT_READ;', r'HARMATTAN_RX (.+)', want=1, timeout=12)
    return parse_rx(r[-1].group(1)) if r else ([], [])


def wake_and_arm(b, points, radius=450, rearm=False):
    """Réveille (dyn-sim) les garnisons proches des `points` puis HMT_ARM. rearm=True -> HMT_DISARM d'abord."""
    if rearm:
        b.send("if (HMT_AGENT_MODE) then {call HMT_DISARM};", timeout=15); time.sleep(0.5)
    if points:
        pts = "[" + ",".join("[%d,%d,0]" % (p[0], p[1]) for p in points) + "]"
        b.send("{ private _u=_x select 0; if (!isNull _u && {(%s findIf {(_u distance _x) < %d}) >= 0}) "
               "then {_u enableSimulation true; _u hideObject false} } forEach HMT_FOB_MEN;" % (pts, radius), timeout=20)
        time.sleep(1.5)
    b.send("call HMT_ARM;", timeout=20); time.sleep(1.5)


def make_measure(st):
    """Mesure les 7 faits d'outcome N ticks après une décision (relit l'état) : cibles, pertes, exposition…"""
    def measure(sit0, now_tick):
        now = st.read(now_tick) or sit0
        thr0 = sum(1 for f in sit0["fobs"] if f["threatened"])
        thrN = sum(1 for f in now["fobs"] if f["threatened"])
        return {"cibles_intactes_frac": (now["targets_intact"] / now["targets_total"]) if now["targets_total"] else 1.0,
                "fobs_tenus_frac": sum(1 for f in now["fobs"] if f["held"]) / max(1, len(now["fobs"])),
                "pertes_amies": max(0, sit0["total_force"] - now["total_force"]),
                "pertes_ennemies": max(0, sit0["total_threat"] - now["total_threat"]),
                "exposition": 1 if thrN > thr0 else 0}
    return measure


def flank_point(pos, enemies):
    """ETAPE 4 : point de flanc = 80 m sur le cote de l'ennemi le plus proche (l'agent y manœuvre)."""
    e = min(enemies, key=lambda e: math.hypot(pos[0] - e[0], pos[1] - e[1]))
    ang = math.atan2(pos[1] - e[1], pos[0] - e[0]) + math.radians(70)
    return [round(e[0] + 80 * math.cos(ang), 1), round(e[1] + 80 * math.sin(ang), 1)]


def main():
    try:                                                            # SOLUTION 2 : pont NATIF (TCP, fin de la troncature -> 500 pilotables)
        b = NativeBridge(port=5816); BR = "NATIF TCP 5816"
    except Exception as e:
        b = ArmaBridge(mission=MIS, log=LOG); BR = "FICHIER (natif indispo: %s)" % e
    try:
        b.send('diag_log "HARMATTAN_PING ok";', timeout=20)
    except Exception as e:
        print("[pont] PAS DE PING:", e, "-> reboot: bash /mnt/data/harmattan-sandbox/launch_fob.sh"); return
    print("[pont] OK (%s)" % BR, flush=True)
    r = b.query('(format ["HARMATTAN_HASARM %1", !(isNil "HMT_ARM")]) call HMT_EMIT;', r'HARMATTAN_HASARM (\w+)', want=1)
    if (r[-1].group(1) if r else "?") != "true":
        print(">>> arm_shells pas chargé -> reboot server_fob (bash launch_fob.sh)"); return
    # glue : officer_state lit HMT_TARGET (singulier) ; la mission ne pose que HMT_TARGETS (pluriel, [nom,obj])
    b.send('if (isNil "HMT_TARGET") then { HMT_TARGET = HMT_TARGETS apply {_x select 1}; };', timeout=15)

    # ---- officier (la tête) ----
    st = OfficerState(bridge=b)
    mem = OfficerMemory("/home/younes/arma3-marl/leviathan/leviathan_officer.db")
    # ---- driver (le corps) ----
    HM, hx0, hy0, hres, HN = synth_hm()        # TODO: remplacer par le heightmap Stratis baké (meilleur cover-sense)
    sw = AgentSwarm(load_body("cpu"), HM, hx0, hy0, hres, HN, group_var="HMT_PILOT", enemy_side="west", device="cpu")
    brain = PatrolBrain(NODES)
    drv = FobDriver(sw, NODES, planner=brain.planner(0))
    orch = Orchestrator()                                            # ETAPE 4 : orchestration_voyant.pt (selecteur)
    loop = OfficerLoop(mem, qwen=qwen_ollama, apply_fn=make_apply(drv), outcome_lag=3)
    measure = make_measure(st)

    # armement initial : réveille+arme là où il y a des contacts (sinon tout est gelé = pays en paix)
    sit0 = st.read(0)
    # SOLUTION 1 : corps de VOYAGE — bake les obstacles statiques (1x, après _ensure_anchors) + branche sur le driver
    tb = TravelBody()
    ro = b.query(TravelBody.query_obstacles_sqf(), r'HARMATTAN_OBST (\[.*\])', want=1, timeout=12)
    if ro: tb.set_obstacles([tuple(o) for o in ast.literal_eval(ro[-1].group(1))])
    drv.travel = tb
    print("[voyage] %d obstacles bakes -> patrouille marche/contourne (corps de voyage)" % int(tb.obs.shape[0]), flush=True)
    thr_pts = [f["pos"] for f in (sit0["fobs"] if sit0 else []) if f["threatened"]] or NODES[:1]   # nb d'agents pilotes <-> FPS : 1 FOB ~jouable ; 4 FOB ~428 (8 FPS) ; NODES entier = 500 (5 FPS). Natif = limite = FPS, plus la lecture.
    wake_and_arm(b, thr_pts)
    print("=== LEVIATHAN001 LIVE — défense par agents + officier Qwen (spectateur :3902) ===", flush=True)

    for tick in range(STEPS):
        shells, enemies = read_def(b)
        for e in enemies:
            brain.note_threat(e, tick)
        if shells:                                                  # RAPIDE : pilote les agents (patrouille/masse/focus)
            dvx, dvy, ddir = drv.tick(shells, enemies)
            b.send("HMT_DVX = %s; HMT_DVY = %s; HMT_DDIR = %s;" % (dvx, dvy, ddir))
        if enemies and shells and tick % 5 == 0:                     # ETAPE 4 : ORCHESTRATION (au contact) -> tactique/agent -> dispatch
            agents = []; idxs = []
            for i, s in enumerate(shells):
                if len(s) >= 4 and s[3] == 1:
                    pos = [s[0], s[1]]
                    d = min(math.hypot(pos[0] - e[0], pos[1] - e[1]) for e in enemies)
                    thr = 1.0 if d < 80 else (0.5 if d < 150 else 0.2)
                    agents.append({"pos": pos, "enemies": enemies, "thr": thr, "cover": 0.3}); idxs.append(i)
            tacs = orch.select(agents)
            L = [[], [], [], [], []]; new_flank = {}
            for j, t in enumerate(tacs):
                if t == 2:                                          # FLANC -> route Python (le driver y va via setVelocity)
                    new_flank[idxs[j]] = flank_point(agents[j]["pos"], enemies)
                else:                                               # grenade/fumi/suppress/vise -> dispatch SQF
                    L[t].append(idxs[j])
            drv.flank_goals = new_flank                             # remplace : les non-flank reviennent au but normal
            b.send("[%s,%s,[],%s,%s] call HMT_DISPATCH;" % (L[0], L[1], L[3], L[4]))
            print("  [%03d] TACTIQUES vise=%d grenade=%d flanc=%d fumi=%d suppr=%d"
                  % (tick, len(L[0]), len(L[1]), len(new_flank), len(L[3]), len(L[4])), flush=True)
        if tick % OFFICER_EVERY == 0:                               # LENT : l'officier Qwen
            sit = st.read(tick)
            if sit:
                orders = loop.decide(sit, tick, float(tick))        # Qwen → ordres → pose drv.focus
                loop.settle_outcomes(tick, measure)                 # grave les leçons mûres
                nag = sum(1 for s in shells if len(s) >= 4 and s[3] == 1)
                act = (orders.get("ordres") or [{}])[0].get("action", "—")
                print("  [%03d] %d agents | %d contacts | cibles %d/%d | officier: %s -> focus=%s"
                      % (tick, nag, len(enemies), sit["targets_intact"], sit["targets_total"], act, drv.focus), flush=True)
        if tick % REARM_EVERY == 0 and tick > 0:                    # capte les défenseurs nouvellement réveillés
            sit = st.read(tick)
            pts = [f["pos"] for f in (sit["fobs"] if sit else []) if f["threatened"]] or thr_pts
            wake_and_arm(b, pts, rearm=True)
            drv.patrol_wp.clear(); drv.prone.clear()                # HMT_PILOT a changé -> reset l'état par-agent
        if tick % 20 == 0:
            drv.planner = brain.planner(tick)                       # la patrouille réapprend l'axe de menace
        time.sleep(1.0)

    b.send('{HMT_DVX set [_forEachIndex,0]; HMT_DVY set [_forEachIndex,0];} forEach HMT_PILOT; call HMT_DISARM;', timeout=15)
    print("=== FIN : retour LAMBS | %d décisions journalisées dans le RAG ===" % mem.count("theatre"), flush=True)


if __name__ == "__main__":
    main()
