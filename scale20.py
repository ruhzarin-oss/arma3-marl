#!/usr/bin/env python3
"""scale20 — setVelocity scale-t-il a 20 fantassins ? Harnais fiable (rate_test2). 20 soldats a plat, espaces,
HMT_VEL global, on mesure le deplacement de CHACUN + FPS serveur. Tranche le mystere du 3/20."""
import sys, time, subprocess, re, math
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
SB = "/mnt/data/harmattan-sandbox"; SLOT = 14; PORT = 2402 + SLOT * 100; EXT = 5801 + SLOT
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
N = 20
FIX = '_u disableAI "MOVE"; _u disableAI "PATH"; _u disableAI "FSM"; _u disableAI "ANIM"; _u disableAI "AUTOCOMBAT"; _u allowDamage false;'


def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)


def launch():
    sh("pkill -9 -f 'profiles%d'" % SLOT); time.sleep(3)
    sh("rm -rf '%s'; cp -r '%s/arma3server/mpmissions/HarmattanBridge.Altis' '%s'" % (MIS, SB, MIS))
    sh("rm -f '%s/hmt_bridge/'cmd_*.sqf" % MIS)
    sh("sed 's/HarmattanBridge\\.Altis/HarmattanBridge%d.Altis/g' '%s/staging/server.cfg' > '%s/staging/server%d.cfg'" % (SLOT, SB, SB, SLOT))
    sh("mkdir -p '%s/profiles%d'; : > '%s'" % (SB, SLOT, LOG))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 -config='%s/staging/server%d.cfg' -profiles='%s/profiles%d' -port=%d -world=Altis -autoInit >> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SLOT, SB, SLOT, PORT, LOG))


def wait_boot(t=200):
    t0 = time.time()
    while time.time() - t0 < t:
        try:
            if "Starting mission" in open(LOG, encoding="utf-8", errors="ignore").read():
                time.sleep(10); return True
        except FileNotFoundError:
            pass
        time.sleep(4)
    return False


def grab(b, tag):
    for ln in reversed(b._log_lines(8000)):
        m = re.search(r"HMT_%s (.+)" % tag, ln)
        if m:
            return m.group(1).strip()
    return None


def xy(s):
    m = re.search(r"\[([-\d.]+),([-\d.]+)", s or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


print("=== SCALE20 (slot %d) ===" % SLOT, flush=True)
launch(); print("boot...", flush=True)
if not wait_boot():
    print("ECHEC boot", flush=True); sys.exit()
b = SocketBridge(EXT); print("socket ok.", flush=True); time.sleep(2)
for i in range(N):
    x = 7000 + (i % 5) * 12; y = 7000 + (i // 5) * 12
    b.send('HMT_%d=(createGroup east) createUnit ["O_Soldier_F",[%d,%d,0],[],0,"FORM"]; private _u=HMT_%d; %s' % (i, x, y, i, FIX))
    time.sleep(0.25)
b.send('HMT_UNITS=[%s]; if (isNil "HMT_VEL") then {HMT_VEL=[0,0,0]};' % ",".join("HMT_%d" % i for i in range(N))); time.sleep(2)
b.send('addMissionEventHandler ["EachFrame", { { if (!isNull _x) then {_x setVelocity HMT_VEL} } forEach HMT_UNITS; }]; diag_log "HMT_FC on";'); time.sleep(1.5)
for i in range(N):
    b.send('diag_log format ["HMT_A%d %%1", getPosATL HMT_%d];' % (i, i))
time.sleep(1.0)
p0 = [xy(grab(b, "A%d" % i)) for i in range(N)]
b.send('HMT_VEL=[6,0,0];'); time.sleep(5.0); b.send('HMT_VEL=[0,0,0];')
b.send('diag_log format ["HMT_FPS %1", round diag_fps];'); time.sleep(0.6)
for i in range(N):
    b.send('diag_log format ["HMT_B%d %%1", getPosATL HMT_%d];' % (i, i))
time.sleep(1.0)
p1 = [xy(grab(b, "B%d" % i)) for i in range(N)]
fps = grab(b, "FPS")
ds = []
for i in range(N):
    if p0[i] and p1[i]:
        ds.append(math.hypot(p1[i][0] - p0[i][0], p1[i][1] - p0[i][1]))
nm = sum(1 for d in ds if d > 5)
print(">>> %d/%d soldats ont avance >5m (5s @6m/s, cible ~30) | moy=%.1f m | FPS serveur=%s" % (nm, len(ds), (sum(ds) / len(ds) if ds else -1), fps), flush=True)
print("   deplacements: %s" % " ".join("%.0f" % d for d in ds), flush=True)
sh("pkill -9 -f 'profiles%d'" % SLOT)
print("SCALE20 DONE", flush=True)
