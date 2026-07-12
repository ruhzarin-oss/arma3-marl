#!/usr/bin/env python3
"""agents_hold.py — RALLUME les soldats du pays en AGENTS qui TIENNENT (mode paix, pas de FS).
Reveille un echantillon de garnisons, les arme en coquilles, les pilote pour tenir leur secteur
(ou le focus du GENERAL Qwen). Aucun combat scenarise. Reutilise FobDriver/AgentSwarm/arm_shells."""
import sys, time, argparse
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from fob_driver import FobDriver, load_body, synth_hm, parse_rx, read_general_focus, write_world_state, SECTORS
from agent_swarm import AgentSwarm
from arma_bridge import ArmaBridge

MIS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions/HarmattanFOB.Stratis"
LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
NODES = [(x, y) for _, x, y in SECTORS]


def main(steps=1200, wake=90):
    b = ArmaBridge(mission=MIS, log=LOG)
    b.send('diag_log "HARMATTAN_PING ok";', timeout=20)
    print("[pont] OK", flush=True)
    b.send('call compile preprocessFileLineNumbers "arm_shells.sqf";', timeout=20); time.sleep(1)  # recharge HMT_ARM (tous-east)
    # reveiller 500 garnisons en agents (LAMBS gere patrouilles/convois)
    b.send('{ if (!isNull _x) then { _x enableSimulation true; _x enableDynamicSimulation false } } forEach ((HMT_FOB_MEN apply {_x select 0}) select [0,%d]);' % wake, timeout=40)
    time.sleep(2)
    b.send('call HMT_ARM;', timeout=20)
    time.sleep(2)
    HM, hx0, hy0, hres, HN = synth_hm()
    sw = AgentSwarm(load_body("cpu"), HM, hx0, hy0, hres, HN, group_var="HMT_PILOT", enemy_side="west", device="cpu")
    drv = FobDriver(sw, NODES, speed=4.0)   # nodes = les 25 secteurs : chacun tient le sien
    print("=== SOLDATS = AGENTS : ils tiennent le pays (general Qwen aux commandes), pas de combat ===", flush=True)
    for step in range(steps):
        r = b.query('call HMT_READ;', r'HARMATTAN_RX (.+)', want=1, timeout=12)
        shells, enemies = parse_rx(r[-1].group(1)) if r else ([], [])
        if not shells:
            print("  [%04d] 0 coquille (personne d'eveille ?)" % step, flush=True); time.sleep(1.5); continue
        drv.focus = read_general_focus() if enemies else None   # focus SEULEMENT sous menace ; en paix -> chacun tient son secteur
        write_world_state(shells, enemies)         # j'expose la situation au GENERAL
        dvx, dvy, ddir = drv.tick(shells, enemies)
        b.send("HMT_DVX = %s; HMT_DVY = %s; HMT_DDIR = %s;" % (dvx, dvy, ddir))
        nlive = sum(1 for s in shells if len(s) >= 4 and s[3] == 1)
        print("  [%04d] soldats-agents %d | focus %s | ennemis vus %d" % (step, nlive, drv.focus, len(enemies)), flush=True)
        time.sleep(1.0)
    b.send('{ HMT_DVX set [_forEachIndex,0]; HMT_DVY set [_forEachIndex,0]; } forEach HMT_PILOT;', timeout=15)
    b.send('call HMT_DISARM;', timeout=15)
    print("=== FIN : retour LAMBS ===", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=1200)
    ap.add_argument("--wake", type=int, default=90)
    a = ap.parse_args()
    main(a.steps, a.wake)
