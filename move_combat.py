#!/usr/bin/env python3
"""move_combat — hypothese : disableAI "MOVE"+combat (squad_deploy) ecrase setVelocity, vs disableAI "ALL" (rate_test2).
Harnais identique a rate_test2 (lecture fiable). 2 soldats, meme HMT_VEL, on compare le deplacement."""
import sys, time, subprocess, re, math
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
SB = "/mnt/data/harmattan-sandbox"; SLOT = 14; PORT = 2402 + SLOT * 100; EXT = 5801 + SLOT
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
FASTCTRL = ('if (isNil "HMT_VEL") then {HMT_VEL=[0,0,0]}; if (isNil "HMT_UNITS") then {HMT_UNITS=[]}; HMT_FC_FRAMES=0; '
            'addMissionEventHandler ["EachFrame", { HMT_FC_FRAMES = HMT_FC_FRAMES + 1; '
            '{ if (!isNull _x) then { _x setVelocity HMT_VEL } } forEach HMT_UNITS; }]; diag_log "HMT_FC on";')


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
    for ln in reversed(b._log_lines(4000)):
        m = re.search(r"HMT_%s (.+)" % tag, ln)
        if m:
            return m.group(1).strip()
    return None


def xy(s):
    m = re.search(r"\[([-\d.]+),([-\d.]+)", s or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


print("=== MOVE_COMBAT (slot %d) ===" % SLOT, flush=True)
launch(); print("boot...", flush=True)
if not wait_boot():
    print("ECHEC boot", flush=True); sys.exit()
b = SocketBridge(EXT); print("socket ok.", flush=True); time.sleep(2)
# A = disableAI ALL (baseline rate_test2) ; B = disableAI MOVE + combat (squad_deploy)
b.send('HMT_A=(createGroup east) createUnit ["O_Soldier_F",[7000,7000,0],[],0,"FORM"]; HMT_A disableAI "ALL"; HMT_A allowDamage false;')
b.send('HMT_B=(createGroup east) createUnit ["O_Soldier_F",[7020,7000,0],[],0,"FORM"]; HMT_B disableAI "MOVE"; HMT_B disableAI "PATH"; HMT_B enableAI "TARGET"; HMT_B enableAI "AUTOTARGET"; HMT_B setBehaviour "COMBAT"; HMT_B setCombatMode "RED"; HMT_B allowDamage false;')
b.send('HMT_UNITS=[HMT_A,HMT_B];'); time.sleep(2)
b.send(FASTCTRL); time.sleep(1.5)
b.send('diag_log format ["HMT_A0 %1", getPosATL HMT_A]; diag_log format ["HMT_B0 %1", getPosATL HMT_B];'); time.sleep(0.6)
a0 = xy(grab(b, "A0")); b0 = xy(grab(b, "B0"))
b.send('HMT_VEL=[0,6,0];'); time.sleep(5.0); b.send('HMT_VEL=[0,0,0];'); time.sleep(0.6)
b.send('diag_log format ["HMT_A1 %1", getPosATL HMT_A]; diag_log format ["HMT_B1 %1", getPosATL HMT_B];'); time.sleep(0.6)
a1 = xy(grab(b, "A1")); b1 = xy(grab(b, "B1"))
da = math.hypot(a1[0] - a0[0], a1[1] - a0[1]) if a0 and a1 else -1
db = math.hypot(b1[0] - b0[0], b1[1] - b0[1]) if b0 and b1 else -1
print("A (disableAI ALL)        : %s -> %s = %.1f m" % (a0, a1, da), flush=True)
print("B (disableAI MOVE+combat): %s -> %s = %.1f m" % (b0, b1, db), flush=True)
print(">>> VERDICT : ALL=%.0fm  MOVE+combat=%.0fm  (attendu ~30m si setVelocity passe)" % (da, db), flush=True)
sh("pkill -9 -f 'profiles%d'" % SLOT)
print("MOVE_COMBAT DONE", flush=True)
