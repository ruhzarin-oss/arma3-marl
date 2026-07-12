#!/usr/bin/env python3
"""occupation_scale.py — TABLE DE MONTEE EN CHARGE. Un serveur frais (slot dedie), spawn incremental
du laydown, mesure server FPS aux seuils N. Trouve le point d'effondrement + effet dyn-sim.
Env : SLOT (def 2), DYNSIM (0/1). NE pkill QUE le slot cible (profilesN), jamais global."""
import os, sys, json, time, subprocess, re, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"; ROOT = "/home/younes/arma3-marl"
SLOT = int(os.environ.get("SLOT", 2)); DYNSIM = int(os.environ.get("DYNSIM", 0))
PORT = 2402 + SLOT * 100
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
THRESH = [250, 500, 1000, 1500, 2000]

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)

def launch_server():
    sh("pkill -9 -f 'profiles%d'" % SLOT); time.sleep(3)            # tue UNIQUEMENT ce slot
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
            if "Starting mission" in open(LOG, encoding="utf-8", errors="ignore").read():
                time.sleep(10); return True
        except FileNotFoundError: pass
        time.sleep(4)
    return False

def spawn_sqf(e):
    x, y = e["pos"]; n = e["size"]; r = e.get("radius", 120)
    ds = "_g enableDynamicSimulation true;\n" if DYNSIM else ""
    return ('private _g = createGroup east;\n'
            'for "_a" from 1 to %d do { _g createUnit ["O_Soldier_F", [%d+(random 24)-12, %d+(random 24)-12, 0], [], 0, "FORM"]; };\n'
            '{_x setSkill 0.5; _x setBehaviour "AWARE"; _x allowFleeing 0} forEach units _g;\n'
            '[_g, [%d,%d], %d] call BIS_fnc_taskPatrol;\n%s' % (n, x, y, x, y, r, ds))

def measure(b, secs=30):
    b.send('[] spawn { for "_i" from 1 to %d do { diag_log format ["HARMATTAN_FPS %%1 %%2 %%3", round(diag_fps*10)/10, round(diag_fpsMin*10)/10, count allUnits]; sleep 5; }; };' % (secs // 5))
    time.sleep(secs + 5)
    rows = [m for ln in b._log_lines(4000) for m in [re.search(r"HARMATTAN_FPS ([\d.]+) ([\d.]+) (\d+)", ln)] if m]
    rows = rows[-(secs // 5):]                                      # derniere fenetre de mesure
    if not rows: return None
    fps = [float(m.group(1)) for m in rows]; fmin = [float(m.group(2)) for m in rows]; au = int(rows[-1].group(3))
    return st.mean(fps), min(fmin), au

def main():
    lay = json.load(open(ROOT + "/staff/occupation_altis.json"))
    elems = [e for e in lay["elements"] if e["type"] != "convoy"]
    print("=== TABLE MONTEE EN CHARGE | slot=%d dynsim=%d | seuils=%s ===" % (SLOT, DYNSIM, THRESH), flush=True)
    launch_server()
    print("[%s] boot..." % time.strftime("%H:%M"), flush=True)
    if not wait_boot(): print("ECHEC boot", flush=True); return
    print("[%s] pret. enableDynSimSystem=%d" % (time.strftime("%H:%M"), DYNSIM), flush=True)
    b = ArmaBridge(mission=MIS, log=LOG); time.sleep(3)
    if DYNSIM: b.send("enableDynamicSimulationSystem true;")
    table = []; spawned = 0; batch = ""; ti = 0
    for e in elems:
        batch += spawn_sqf(e); spawned += e["size"]
        if len(batch) > 2500:
            try: b.send(batch, timeout=30)
            except Exception as ex: print("  spawn err:", ex, flush=True)
            batch = ""
        while ti < len(THRESH) and spawned >= THRESH[ti]:
            if batch:
                try: b.send(batch, timeout=30)
                except Exception: pass
                batch = ""
            time.sleep(8)
            r = measure(b, 30)
            if r: table.append((THRESH[ti], r[2], r[0], r[1])); print("[%s] N~%d | allUnits=%d | FPS moy=%.1f min=%.1f" % (time.strftime("%H:%M"), THRESH[ti], r[1], r[0], r[2]), flush=True)
            ti += 1
        if ti >= len(THRESH): break
    print("\n=== TABLE FPS (dynsim=%d) ===" % DYNSIM, flush=True)
    print("seuil_N | allUnits | FPS_moy | FPS_min", flush=True)
    for n, au, m, fm in table:
        print("%6d  | %7d  | %6.1f  | %6.1f" % (n, au, m, fm), flush=True)
    coll = next((n for n, au, m, fm in table if m < 20), None)
    print("Point d'effondrement (FPS<20) : %s" % (coll if coll else "non atteint"), flush=True)
    print("SCALE_TABLE_DONE", flush=True)

if __name__ == "__main__":
    main()
