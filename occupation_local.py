#!/usr/bin/env python3
"""occupation_local.py — FIX : 1 groupe = 1 LOCALITE (unites groupees sur place, PAS d'eparpillement).
Spawne les garnisons (+ elements) en groupes LOCAUX, grossis pour atteindre ~TARGET en <=144 groupes.
Mesure server FPS aux seuils. Env : SLOT(2), TARGET(2000), DYNSIM(0/1)."""
import os, sys, json, time, subprocess, re, statistics as st
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"; ROOT = "/home/younes/arma3-marl"
SLOT = int(os.environ.get("SLOT", 2)); DYNSIM = int(os.environ.get("DYNSIM", 0)); TARGET = int(os.environ.get("TARGET", 2000))
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
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 -config='%s/staging/server%d.cfg' -profiles='%s/profiles%d' -port=%d -world=Altis -autoInit >> '%s' 2>&1 < /dev/null & disown" % (SB, 5801 + SLOT, SB, SLOT, SB, SLOT, PORT, LOG))
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

def grp_local(x, y, n):
    """1 groupe, n unites GROUPEES autour de (x,y) — comme le spawn qui marche."""
    s = 'private _g = createGroup east;\nfor "_a" from 1 to %d do { _g createUnit ["O_Soldier_F", [%d+(random 40)-20, %d+(random 40)-20, 0], [], 0, "FORM"]; };\n' % (n, x, y)
    s += '{_x setSkill 0.5; _x setBehaviour "AWARE"; _x allowFleeing 0} forEach units _g;\n'
    s += '[_g, [%d,%d], 80] call BIS_fnc_taskPatrol;\n' % (x, y)
    if DYNSIM: s += '_g enableDynamicSimulation true;\n'
    return s

def main():
    lay = json.load(open(ROOT + "/staff/occupation_altis.json"))
    # 1 localite = 1 groupe local. Prendre les garnisons (111) + FOB/QG/checkpoints/OP, <=140 groupes.
    elems = [e for e in lay["elements"] if e["type"] in ("garrison", "fob", "theater_hq", "checkpoint", "op", "coastal", "qrf")]
    elems = elems[:140]                                                  # garde-fou <144 groupes
    base = sum(e["size"] for e in elems)
    scale = TARGET / base
    grp = [(e["pos"][0], e["pos"][1], max(3, round(e["size"] * scale))) for e in elems]
    total = sum(g[2] for g in grp)
    print("=== OCCUPATION LOCALE | slot=%d dynsim=%d | %d groupes, %d unites (cible %d) ===" % (SLOT, DYNSIM, len(grp), total, TARGET), flush=True)
    launch_server(); print("[%s] boot..." % time.strftime("%H:%M"), flush=True)
    if not wait_boot(): print("ECHEC boot", flush=True); return
    b = ArmaBridge(mission=MIS, log=LOG); time.sleep(3)
    if DYNSIM: b.send("enableDynamicSimulationSystem true;")
    table = []; spawned = 0; ti = 0; batch = ""
    for (x, y, n) in grp:
        batch += grp_local(x, y, n); spawned += n
        if len(batch) > 3000:                                            # BATCH (comme le test qui marche) : plusieurs groupes/cmd
            try: b.send(batch, timeout=45)
            except Exception as ex: print("  err:", ex, flush=True)
            batch = ""
        while ti < len(THRESH) and spawned >= THRESH[ti]:
            if batch:
                try: b.send(batch, timeout=45)
                except Exception: pass
                batch = ""
            time.sleep(6); r = measure(b, 30)
            if r: table.append((THRESH[ti], r[2], r[0], r[1])); print("[%s] N~%d | allUnits=%d | FPS moy=%.1f min=%.1f" % (time.strftime("%H:%M"), THRESH[ti], r[2], r[0], r[1]), flush=True)
            ti += 1
    if batch:
        try: b.send(batch, timeout=45)
        except Exception: pass
    time.sleep(6); r = measure(b, 30)
    if r: print("[%s] PLEIN | allUnits=%d | FPS moy=%.1f min=%.1f" % (time.strftime("%H:%M"), r[2], r[0], r[1]), flush=True)
    print("\n=== TABLE OCCUPATION LOCALE (dynsim=%d) ===" % DYNSIM, flush=True)
    print("seuil | allUnits | FPS_moy | FPS_min", flush=True)
    for n, au, m, fm in table: print("%5d | %7d  | %6.1f  | %6.1f" % (n, au, m, fm), flush=True)
    if r: print("%5s | %7d  | %6.1f  | %6.1f" % ("PLEIN", r[2], r[0], r[1]), flush=True)
    print("LOCAL_DONE", flush=True)

if __name__ == "__main__":
    main()
