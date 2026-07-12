#!/usr/bin/env python3
"""hc_driver.py — driver MULTI-HEADLESS-CLIENT pour leviathan001.
Répartit le pilotage des agents sur K headless clients (K cœurs) → la physique setVelocity se SPLIT.
1 bridge serveur (officier/SITREP, port 5816) + K bridges HC (5817..5816+K, chacun pilote sa tranche locale).
Le cerveau (cheap) calcule par tranche ; chaque HC applique setVelocity sur SES unités locales (son cœur)."""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from fob_driver import FobDriver, AgentSwarm, PatrolBrain, parse_rx, load_body, synth_hm
from officer_state import OfficerState, FOBS
from officer_memory import OfficerMemory
from officer import OfficerLoop, qwen_ollama, make_apply

NODES = [(f[1], f[2]) for f in FOBS]
K = 4                                                                # nombre de headless clients
STEPS = 300


def read_hc(b):
    r = b.query('call HMT_READ;', r'HARMATTAN_RX (.+)', want=1, timeout=12)
    return parse_rx(r[-1].group(1)) if r else ([], [])


def main():
    # 1 bridge serveur (officier) + K bridges HC (un par cœur)
    srv = NativeBridge(port=5816)
    hcs = [NativeBridge(port=5816 + i) for i in range(1, K + 1)]     # 5817..5816+K
    print("[hc] %d headless clients + serveur connectés" % len(hcs), flush=True)

    # un cerveau (réflexe) PAR HC — léger, juste pour vectoriser sa tranche
    HM, hx0, hy0, hres, HN = synth_hm()
    body = load_body("cpu")
    brains, planners = [], []
    for _ in hcs:
        sw = AgentSwarm(body, HM, hx0, hy0, hres, HN, group_var="HMT_PILOT", enemy_side="west", device="cpu")
        brain = PatrolBrain(NODES)
        brains.append(FobDriver(sw, NODES, planner=brain.planner(0)))
        planners.append(brain)

    # officier (la tête) sur le SERVEUR
    st = OfficerState(bridge=srv)
    mem = OfficerMemory("/home/younes/arma3-marl/leviathan/leviathan_officer.db")
    loop = OfficerLoop(mem, qwen=qwen_ollama, apply_fn=lambda o: _broadcast_focus(o, brains), outcome_lag=3)

    # 1) DISTRIBUER les groupes sur les HC (server-side) puis ARMER chaque HC (sa tranche locale)
    srv.send("call HMT_DISTRIBUTE;", timeout=20); time.sleep(3)      # transfert d'ownership
    for b in hcs:
        b.send("call HMT_ARM_LOCAL;", timeout=20)
    time.sleep(2)
    print("=== LEVIATHAN001 LIVE MULTI-HC (physique répartie sur %d cœurs) ===" % K, flush=True)

    for tick in range(STEPS):
        # RAPIDE : chaque HC pilote SA tranche (lecture + cerveau + écriture, en parallèle des cœurs)
        for j, b in enumerate(hcs):
            shells, enemies = read_hc(b)
            if not shells:
                continue
            for e in enemies:
                planners[j].note_threat(e, tick)
            dvx, dvy, ddir = brains[j].tick(shells, enemies)
            b.send("HMT_DVX = %s; HMT_DVY = %s; HMT_DDIR = %s;" % (dvx, dvy, ddir))
            if tick % 20 == 0:
                brains[j].planner = planners[j].planner(tick)
        # LENT : l'officier sur le serveur (état GLOBAL)
        if tick % 10 == 0:
            sit = st.read(tick)
            if sit:
                orders = loop.decide(sit, tick, float(tick))
                loop.settle_outcomes(tick, _make_measure(st))
                print("  [%03d] officier: %s | focus=%s" %
                      (tick, (orders.get("ordres") or [{}])[0].get("action", "—"),
                       brains[0].focus), flush=True)
        time.sleep(1.0)

    for b in hcs:
        b.send("call HMT_DISARM;", timeout=15)
    print("=== FIN multi-HC : retour LAMBS, %d décisions ===" % mem.count("theatre"), flush=True)


def _broadcast_focus(orders, brains):
    """L'officier pose le même focus sur TOUS les cerveaux-HC (la réserve converge partout)."""
    foc = None
    for o in orders.get("ordres", []):
        if o.get("action") in ("RENFORCER", "MASSER", "QRF") and o.get("cible"):
            foc = o["cible"]; break
    for drv in brains:
        drv.focus = foc


def _make_measure(st):
    def measure(sit0, now_tick):
        now = st.read(now_tick) or sit0
        thr0 = sum(1 for f in sit0["fobs"] if f["threatened"]); thrN = sum(1 for f in now["fobs"] if f["threatened"])
        return {"cibles_intactes_frac": (now["targets_intact"] / now["targets_total"]) if now["targets_total"] else 1.0,
                "fobs_tenus_frac": sum(1 for f in now["fobs"] if f["held"]) / max(1, len(now["fobs"])),
                "pertes_amies": max(0, sit0["total_force"] - now["total_force"]),
                "pertes_ennemies": max(0, sit0["total_threat"] - now["total_threat"]),
                "exposition": 1 if thrN > thr0 else 0}
    return measure


if __name__ == "__main__":
    main()
