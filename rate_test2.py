#!/usr/bin/env python3
"""rate_test2.py — PILOTAGE HAUT DEBIT par handler EachFrame (HARMATTAN).
Idee experte : un handler EachFrame (env NON-planifie, ~49 Hz) applique la DERNIERE action a chaque frame.
La politique ne met a jour l'action qu'a ~10 Hz -> execution LISSE 49 Hz avec une politique lente.
=> resout le "fige entre 2 decisions". Mesure : frames/s d'application, deplacement reel, debit de MAJ commande."""
import os, sys, time, subprocess, re
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"; SLOT = 14; PORT = 2402 + SLOT * 100; EXT = 5801 + SLOT
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT

# handler EachFrame : applique la derniere action (HMT_VEL) a chaque frame, compte les frames
FASTCTRL = ('if (isNil "HMT_VEL") then {HMT_VEL=[0,0,0]}; if (isNil "HMT_UNITS") then {HMT_UNITS=[]}; HMT_FC_FRAMES=0; '
            'addMissionEventHandler ["EachFrame", { HMT_FC_FRAMES = HMT_FC_FRAMES + 1; '
            '{ if (!isNull _x) then { _x setVelocity HMT_VEL } } forEach HMT_UNITS; }]; '
            'diag_log "HARMATTAN_FASTCTRL on";')

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
            if "Starting mission" in open(LOG, encoding="utf-8", errors="ignore").read(): time.sleep(10); return True
        except FileNotFoundError: pass
        time.sleep(4)
    return False
def grab(b, tag):
    for ln in reversed(b._log_lines(4000)):
        m = re.search(r"HARMATTAN_%s (.+)" % tag, ln)
        if m: return m.group(1).strip()
    return None

def main():
    print("=== PILOTAGE EACHFRAME (slot %d, ext %d) ===" % (SLOT, EXT), flush=True)
    launch(); print("boot...", flush=True)
    if not wait_boot(): print("ECHEC boot", flush=True); return
    try: b = SocketBridge(EXT)
    except Exception as e: print("ECHEC socket: %s" % e, flush=True); return
    print("socket connecte.", flush=True); time.sleep(2)
    b.send('HMT_U=(createGroup east) createUnit ["O_Soldier_F",[7000,7000,0],[],0,"FORM"]; HMT_U disableAI "ALL"; HMT_U allowDamage false; HMT_UNITS=[HMT_U];')
    time.sleep(2)
    b.send(FASTCTRL); time.sleep(1.5)
    if not any("HARMATTAN_FASTCTRL on" in l for l in b._log_lines(2000)):
        print("handler EachFrame non confirme", flush=True)
    # (1) APPLICATION : frames sur 5 s + deplacement
    b.send('HMT_VEL=[6,0,0]; HMT_FC_FRAMES=0; diag_log format ["HARMATTAN_P0 %1", getPosATL HMT_U];')
    time.sleep(5.0)
    b.send('diag_log format ["HARMATTAN_FR %1", HMT_FC_FRAMES]; diag_log format ["HARMATTAN_P1 %1", getPosATL HMT_U]; HMT_VEL=[0,0,0];')
    time.sleep(0.6)
    fr = grab(b, "FR"); p0 = grab(b, "P0"); p1 = grab(b, "P1")
    hz = (float(fr) / 5.0) if fr else 0
    print("APPLICATION EachFrame : %s frames en 5s = %.1f Hz" % (fr, hz), flush=True)
    print("  pos debut: %s | pos fin: %s" % (p0, p1), flush=True)
    # (2) DEBIT de mise a jour de la commande (fire-and-forget)
    t0 = time.time(); c = 0
    while time.time() - t0 < 3.0:
        b.send('HMT_VEL=[6,0,0];', wait=False); c += 1
    print("DEBIT MAJ commande (fire-and-forget) : %.1f Hz" % (c / 3.0), flush=True)
    # (3) FPS serveur
    b.send('diag_log format ["HARMATTAN_FPS %1", round diag_fps];'); time.sleep(0.4)
    print("FPS serveur:", grab(b, "FPS"), flush=True)
    sh("pkill -9 -f 'profiles%d'" % SLOT)
    print("RATE2_DONE", flush=True)

if __name__ == "__main__":
    main()
