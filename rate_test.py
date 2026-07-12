#!/usr/bin/env python3
"""rate_test.py — MESURE le debit de pilotage Arma via le PONT NATIF TCP (hmt_native).
Question : peut-on piloter un soldat a 30-60 Hz depuis l'exterieur ? (vs ~1 Hz du pont-fichier)
Lance un serveur sur un slot LIBRE (14), connecte le SocketBridge, spawne 1 unite,
mesure (1) le debit aller-retour, (2) confirme un pilotage temps reel (setVelocity), (3) le FPS serveur."""
import os, sys, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge

SB = "/mnt/data/harmattan-sandbox"; SLOT = 14; PORT = 2402 + SLOT * 100; EXT = 5801 + SLOT
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT

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

def main():
    print("=== TEST DEBIT PILOTAGE (pont natif TCP, slot %d, ext %d) ===" % (SLOT, EXT), flush=True)
    launch(); print("boot...", flush=True)
    if not wait_boot(): print("ECHEC boot", flush=True); return
    try:
        b = SocketBridge(EXT)
    except Exception as e:
        print("ECHEC connexion socket: %s" % e, flush=True); return
    print("socket connecte.", flush=True); time.sleep(2)
    # 1 unite a piloter
    b.send('HMT_U = (createGroup east) createUnit ["O_Soldier_F", [7000,7000,0], [], 0, "FORM"]; HMT_U disableAI "ALL"; HMT_U allowDamage false;')
    time.sleep(2)
    # (1) DEBIT aller-retour : N envois avec attente du RECV
    N = 400; t0 = time.time()
    for _ in range(N):
        b.send('diag_log "p";')          # aller-retour trivial
    dt = time.time() - t0
    print("DEBIT aller-retour : %.1f Hz  (%d envois en %.2fs)" % (N / dt, N, dt), flush=True)
    # (2) PILOTAGE reel : setVelocity vers +x a chaque envoi pendant ~5s, mesure le deplacement
    b.send('diag_log format ["HARMATTAN_P0 %1", getPosATL HMT_U];')
    t0 = time.time(); steps = 0
    while time.time() - t0 < 5.0:
        b.send('HMT_U setVelocity [6,0,0];')      # pousse a 6 m/s vers +x
        steps += 1
    b.send('diag_log format ["HARMATTAN_P1 %1", getPosATL HMT_U];')
    print("PILOTAGE : %d commandes setVelocity en 5s = %.1f Hz" % (steps, steps / 5.0), flush=True)
    time.sleep(0.5)
    # lit P0/P1 pour confirmer le mouvement
    p0 = p1 = None
    for ln in b._log_lines(3000):
        if "HARMATTAN_P0" in ln: p0 = ln
        if "HARMATTAN_P1" in ln: p1 = ln
    print("pos debut:", p0, flush=True); print("pos fin  :", p1, flush=True)
    # (3) FPS serveur
    b.send('diag_log format ["HARMATTAN_FPS %1", round diag_fps];')
    time.sleep(0.4)
    for ln in reversed(b._log_lines(500)):
        if "HARMATTAN_FPS" in ln: print("FPS serveur:", ln.strip(), flush=True); break
    sh("pkill -9 -f 'profiles%d'" % SLOT)
    print("RATE_DONE", flush=True)

if __name__ == "__main__":
    main()
