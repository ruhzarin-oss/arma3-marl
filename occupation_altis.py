#!/usr/bin/env python3
"""occupation_altis.py — ORCHESTRATEUR : lance une instance Arma sur SLOT libre (sans toucher les autres),
injecte le laydown (capé a N unites, Dynamic Simulation optionnelle), mesure le server FPS, ecrit un rapport.
Config par variables d'env : SLOT (def 2), N (def 250), DYNSIM (0/1). NE FAIT JAMAIS de pkill global."""
import os, sys, json, time, subprocess, re, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"; ROOT = "/home/younes/arma3-marl"
SLOT = int(os.environ.get("SLOT", 2)); N = int(os.environ.get("N", 250)); DYNSIM = int(os.environ.get("DYNSIM", 0))
PORT = 2402 + SLOT * 100
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)

def launch_server():
    sh("rm -rf '%s'; cp -r '%s/arma3server/mpmissions/HarmattanBridge.Altis' '%s'" % (MIS, SB, MIS))
    sh("rm -f '%s/hmt_bridge/'cmd_*.sqf" % MIS)
    sh("sed 's/HarmattanBridge\\.Altis/HarmattanBridge%d.Altis/g' '%s/staging/server.cfg' > '%s/staging/server%d.cfg'" % (SLOT, SB, SB, SLOT))
    sh("mkdir -p '%s/profiles%d'; : > '%s'" % (SB, SLOT, LOG))
    cmd = ("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 "
           "-config='%s/staging/server%d.cfg' -profiles='%s/profiles%d' -port=%d -world=Altis -autoInit "
           ">> '%s' 2>&1 < /dev/null & disown" % (SB, 5801 + SLOT, SB, SLOT, SB, SLOT, PORT, LOG))
    sh(cmd)

def wait_boot(timeout=200):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            d = open(LOG, encoding="utf-8", errors="ignore").read()
            if "Starting mission" in d or "read from directory" in d:
                time.sleep(10); return True
        except FileNotFoundError:
            pass
        time.sleep(4)
    return False

def spawn_sqf(e):
    x, y = e["pos"]; n = e["size"]; r = e.get("radius", 120)
    ds = "_g enableDynamicSimulation true;\n" if DYNSIM else ""
    return ('private _g = createGroup east;\n'
            'for "_a" from 1 to %d do { _g createUnit ["O_Soldier_F", [%d+(random 24)-12, %d+(random 24)-12, 0], [], 0, "FORM"]; };\n'
            '{_x setSkill 0.5; _x setBehaviour "AWARE"; _x allowFleeing 0} forEach units _g;\n'
            '[_g, [%d,%d], %d] call BIS_fnc_taskPatrol;\n%s' % (n, x, y, x, y, r, ds))

def main():
    lay = json.load(open(ROOT + "/staff/occupation_altis.json"))
    print("=== ORCHESTRATEUR OCCUPATION | slot=%d port=%d N=%d dynsim=%d ===" % (SLOT, PORT, N, DYNSIM), flush=True)
    launch_server()
    print("[%s] serveur lance, attente boot..." % time.strftime("%H:%M"), flush=True)
    if not wait_boot():
        print("ECHEC boot serveur", flush=True); return
    print("[%s] mission chargee, pont pret." % time.strftime("%H:%M"), flush=True)
    b = ArmaBridge(mission=MIS, log=LOG)
    time.sleep(3)
    if DYNSIM:
        b.send("enableDynamicSimulationSystem true;")
    spawned = 0; batch = ""; nb = 0
    for e in lay["elements"]:
        if e["type"] == "convoy": continue
        if spawned >= N: break
        batch += spawn_sqf(e); spawned += e["size"]
        if len(batch) > 2500:
            try: b.send(batch, timeout=25); nb += 1
            except Exception as ex: print("  spawn batch err:", ex, flush=True)
            batch = ""
    if batch:
        try: b.send(batch, timeout=25); nb += 1
        except Exception as ex: print("  spawn last err:", ex, flush=True)
    print("[%s] ~%d unites spawnees en %d paquets, settle 30s..." % (time.strftime("%H:%M"), spawned, nb), flush=True)
    time.sleep(30)
    b.send('[] spawn { for "_i" from 1 to 12 do { diag_log format ["HARMATTAN_FPS %1 %2 %3", round(diag_fps*10)/10, round(diag_fpsMin*10)/10, count allUnits]; sleep 5; }; };')
    print("[%s] mesure FPS 60s..." % time.strftime("%H:%M"), flush=True)
    time.sleep(66)
    lines = b._log_lines(3000); fps = []; fmin = []; au = 0
    for ln in lines:
        m = re.search(r"HARMATTAN_FPS ([\d.]+) ([\d.]+) (\d+)", ln)
        if m: fps.append(float(m.group(1))); fmin.append(float(m.group(2))); au = int(m.group(3))
    if fps:
        print(">>> RESULT | slot=%d N=%d dynsim=%d | allUnits=%d | FPS moy=%.1f | FPS min=%.1f | (%d mesures)"
              % (SLOT, N, DYNSIM, au, st.mean(fps), min(fmin), len(fps)), flush=True)
    else:
        print(">>> AUCUN FPS LU — verifier %s" % LOG, flush=True)
    print("OCC_DONE", flush=True)

if __name__ == "__main__":
    main()
