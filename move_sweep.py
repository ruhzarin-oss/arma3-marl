#!/usr/bin/env python3
"""move_sweep — trouve la config disableAI qui laisse setVelocity DEPLACER le corps tout en gardant le TIR.
On coupe la locomotion mais on tente de re-activer visee/tir. 4 soldats, 1 config chacun, meme HMT_VEL."""
import sys, time, subprocess, re, math
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
SB = "/mnt/data/harmattan-sandbox"; SLOT = 14; PORT = 2402 + SLOT * 100; EXT = 5801 + SLOT
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
FASTCTRL = ('if (isNil "HMT_VEL") then {HMT_VEL=[0,0,0]}; if (isNil "HMT_UNITS") then {HMT_UNITS=[]}; '
            'addMissionEventHandler ["EachFrame", { { if (!isNull _x) then { _x setVelocity HMT_VEL } } forEach HMT_UNITS; }]; diag_log "HMT_FC on";')

CFG = {  # nom -> setup SQF applique a l unite _u
    "ALL":            '_u disableAI "ALL";',
    "ALL+fire":       '_u disableAI "ALL"; _u enableAI "TARGET"; _u enableAI "AUTOTARGET"; _u enableAI "AIMING"; _u enableAI "WEAPONAIM"; _u setBehaviour "COMBAT"; _u setCombatMode "RED";',
    "MOVE+FSM+ANIM":  '_u disableAI "MOVE"; _u disableAI "PATH"; _u disableAI "FSM"; _u disableAI "ANIM"; _u disableAI "AUTOCOMBAT"; _u setBehaviour "COMBAT"; _u setCombatMode "RED";',
    "MOVE(controle)": '_u disableAI "MOVE"; _u disableAI "PATH"; _u setBehaviour "COMBAT"; _u setCombatMode "RED";',
}


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
    for ln in reversed(b._log_lines(5000)):
        m = re.search(r"HMT_%s (.+)" % tag, ln)
        if m:
            return m.group(1).strip()
    return None


def xy(s):
    m = re.search(r"\[([-\d.]+),([-\d.]+)", s or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


print("=== MOVE_SWEEP (slot %d) ===" % SLOT, flush=True)
launch(); print("boot...", flush=True)
if not wait_boot():
    print("ECHEC boot", flush=True); sys.exit()
b = SocketBridge(EXT); print("socket ok.", flush=True); time.sleep(2)
names = list(CFG)
for i, n in enumerate(names):
    b.send('HMT_%d=(createGroup east) createUnit ["O_Soldier_F",[%d,7000,0],[],0,"FORM"]; private _u=HMT_%d; %s _u allowDamage false;' % (i, 7000 + i * 15, i, CFG[n]))
    time.sleep(0.4)
b.send('HMT_UNITS=[%s];' % ",".join("HMT_%d" % i for i in range(len(names)))); time.sleep(2)
b.send(FASTCTRL); time.sleep(1.5)
for i in range(len(names)):
    b.send('diag_log format ["HMT_S%d %%1", getPosATL HMT_%d];' % (i, i))
time.sleep(0.8)
p0 = [xy(grab(b, "S%d" % i)) for i in range(len(names))]
b.send('HMT_VEL=[0,6,0];'); time.sleep(5.0); b.send('HMT_VEL=[0,0,0];'); time.sleep(0.6)
for i in range(len(names)):
    b.send('diag_log format ["HMT_E%d %%1", getPosATL HMT_%d];' % (i, i))
time.sleep(0.8)
p1 = [xy(grab(b, "E%d" % i)) for i in range(len(names))]
print("--- deplacement (5s @ 6 m/s, cible ~30 m) ---", flush=True)
for i, n in enumerate(names):
    d = math.hypot(p1[i][0] - p0[i][0], p1[i][1] - p0[i][1]) if p0[i] and p1[i] else -1
    print("  %-16s : %.1f m" % (n, d), flush=True)
sh("pkill -9 -f 'profiles%d'" % SLOT)
print("MOVE_SWEEP DONE", flush=True)
