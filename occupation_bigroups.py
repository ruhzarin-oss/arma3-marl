#!/usr/bin/env python3
"""occupation_bigroups.py — casse le plafond ~144 groupes en PACKANT les unites dans <=NGROUPS groupes
(gros groupes statiques = OK pour garnisons). Test : atteint-on ~TARGET unites sur UN serveur, et a quel FPS ?
Env : SLOT(2), NGROUPS(140), TARGET(2000), DYNSIM(0/1)."""
import os, sys, json, time, subprocess, re, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"; ROOT = "/home/younes/arma3-marl"
SLOT = int(os.environ.get("SLOT", 2)); DYNSIM = int(os.environ.get("DYNSIM", 0))
NGROUPS = int(os.environ.get("NGROUPS", 140)); TARGET = int(os.environ.get("TARGET", 2000))
PORT = 2402 + SLOT * 100
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
THRESH = [500, 1000, 1500, 2000]

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)

def launch_server():
    sh("pkill -9 -f 'profiles%d'" % SLOT); time.sleep(3)
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
            if "Starting mission" in open(LOG, encoding="utf-8", errors="ignore").read(): time.sleep(10); return True
        except FileNotFoundError: pass
        time.sleep(4)
    return False

def measure(b, secs=30):
    b.send('[] spawn { for "_i" from 1 to %d do { diag_log format ["HARMATTAN_FPS %%1 %%2 %%3", round(diag_fps*10)/10, round(diag_fpsMin*10)/10, count allUnits]; sleep 5; }; };' % (secs // 5))
    time.sleep(secs + 5)
    rows = [m for ln in b._log_lines(4000) for m in [re.search(r"HARMATTAN_FPS ([\d.]+) ([\d.]+) (\d+)", ln)] if m][-(secs // 5):]
    if not rows: return None
    return st.mean(float(m.group(1)) for m in rows), min(float(m.group(2)) for m in rows), int(rows[-1].group(3))

def grp_sqf(points):
    s = 'private _g = createGroup east;\n'
    for (x, y) in points:
        s += '_g createUnit ["O_Soldier_F", [%d+(random 20)-10, %d+(random 20)-10, 0], [], 0, "FORM"];\n' % (x, y)
    s += '{_x setSkill 0.5; _x setBehaviour "AWARE"; _x allowFleeing 0} forEach units _g;\n'
    if DYNSIM: s += '_g enableDynamicSimulation true;\n'
    return s

def main():
    lay = json.load(open(ROOT + "/staff/occupation_altis.json"))
    pts = []
    for e in lay["elements"]:
        if e["type"] == "convoy": continue
        pts += [tuple(e["pos"])] * e["size"]
    pts = pts[:TARGET]
    groups = [pts[i::NGROUPS] for i in range(NGROUPS)]                   # repartition round-robin en NGROUPS groupes
    print("=== BIG-GROUPS | slot=%d dynsim=%d | %d unites en %d groupes ===" % (SLOT, DYNSIM, len(pts), NGROUPS), flush=True)
    launch_server(); print("[%s] boot..." % time.strftime("%H:%M"), flush=True)
    if not wait_boot(): print("ECHEC boot", flush=True); return
    b = ArmaBridge(mission=MIS, log=LOG); time.sleep(3)
    if DYNSIM: b.send("enableDynamicSimulationSystem true;")
    table = []; spawned = 0; ti = 0
    for gi, gpts in enumerate(groups):
        if not gpts: continue
        try: b.send(grp_sqf(gpts), timeout=30)
        except Exception as ex: print("  grp %d err: %s" % (gi, ex), flush=True)
        spawned += len(gpts)
        while ti < len(THRESH) and spawned >= THRESH[ti]:
            time.sleep(6); r = measure(b, 30)
            if r: table.append((THRESH[ti], r[2], r[0], r[1])); print("[%s] N~%d | allUnits=%d | FPS moy=%.1f min=%.1f | groupes~%d" % (time.strftime("%H:%M"), THRESH[ti], r[2], r[0], r[1], gi + 1), flush=True)
            ti += 1
    # mesure finale au plein
    time.sleep(6); r = measure(b, 30)
    if r: print("[%s] PLEIN | allUnits=%d | FPS moy=%.1f min=%.1f | %d groupes" % (time.strftime("%H:%M"), r[2], r[0], r[1], NGROUPS), flush=True)
    print("\n=== TABLE BIG-GROUPS (dynsim=%d, %d groupes) ===" % (DYNSIM, NGROUPS), flush=True)
    print("seuil | allUnits | FPS_moy | FPS_min", flush=True)
    for n, au, m, fm in table: print("%5d | %7d  | %6.1f  | %6.1f" % (n, au, m, fm), flush=True)
    if r: print("%5s | %7d  | %6.1f  | %6.1f" % ("PLEIN", r[2], r[0], r[1]), flush=True)
    print("BIGGROUPS_DONE", flush=True)

if __name__ == "__main__":
    main()
