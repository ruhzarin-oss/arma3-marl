#!/usr/bin/env python3
"""move_pervar — global HMT_VEL vs getVariable par-unite (le mecanisme de squad_deploy), meme config disableAI(fix).
Si global bouge 30m et per-var bouge 0 -> le bug squad = getVariable par-unite."""
import sys, time, subprocess, re, math
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
SB = "/mnt/data/harmattan-sandbox"; SLOT = 14; PORT = 2402 + SLOT * 100; EXT = 5801 + SLOT
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
FIX = '_u disableAI "MOVE"; _u disableAI "PATH"; _u disableAI "FSM"; _u disableAI "ANIM"; _u disableAI "AUTOCOMBAT"; _u enableAI "TARGET"; _u enableAI "AUTOTARGET"; _u setBehaviour "COMBAT"; _u setCombatMode "RED"; _u allowDamage false;'


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


print("=== MOVE_PERVAR (slot %d) ===" % SLOT, flush=True)
launch(); print("boot...", flush=True)
if not wait_boot():
    print("ECHEC boot", flush=True); sys.exit()
b = SocketBridge(EXT); print("socket ok.", flush=True); time.sleep(2)
b.send('HMT_G=(createGroup east) createUnit ["O_Soldier_F",[7000,7000,0],[],0,"FORM"]; private _u=HMT_G; %s' % FIX)
b.send('HMT_P=(createGroup east) createUnit ["O_Soldier_F",[7020,7000,0],[],0,"FORM"]; private _u=HMT_P; %s HMT_P setVariable ["vx",0]; HMT_P setVariable ["vy",0];' % FIX)
b.send('HMT_UNITS=[HMT_G,HMT_P]; if (isNil "HMT_VEL") then {HMT_VEL=[0,0,0]};'); time.sleep(2)
# handler : HMT_G pilote par global HMT_VEL, HMT_P pilote par getVariable (mecanisme squad_deploy)
b.send('addMissionEventHandler ["EachFrame", { HMT_G setVelocity HMT_VEL; HMT_P setVelocity [HMT_P getVariable ["vx",0], HMT_P getVariable ["vy",0], (velocity HMT_P)#2]; }]; diag_log "HMT_FC on";'); time.sleep(1.5)
b.send('diag_log format ["HMT_G0 %1", getPosATL HMT_G]; diag_log format ["HMT_P0 %1", getPosATL HMT_P];'); time.sleep(0.6)
g0 = xy(grab(b, "G0")); p0 = xy(grab(b, "P0"))
b.send('HMT_VEL=[0,6,0]; HMT_P setVariable ["vx",0]; HMT_P setVariable ["vy",6];'); time.sleep(5.0)
b.send('HMT_VEL=[0,0,0]; HMT_P setVariable ["vx",0]; HMT_P setVariable ["vy",0];'); time.sleep(0.6)
b.send('diag_log format ["HMT_G1 %1", getPosATL HMT_G]; diag_log format ["HMT_P1 %1", getPosATL HMT_P];'); time.sleep(0.6)
g1 = xy(grab(b, "G1")); p1 = xy(grab(b, "P1"))
dg = math.hypot(g1[0] - g0[0], g1[1] - g0[1]) if g0 and g1 else -1
dp = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) if p0 and p1 else -1
print("GLOBAL HMT_VEL    : %.1f m" % dg, flush=True)
print("getVariable/unite : %.1f m" % dp, flush=True)
print(">>> VERDICT : global=%.0fm  per-var=%.0fm" % (dg, dp), flush=True)
sh("pkill -9 -f 'profiles%d'" % SLOT)
print("MOVE_PERVAR DONE", flush=True)
