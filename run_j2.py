#!/usr/bin/env python3
"""run_j2.py — le banc des jambes II (bloc D)."""
import sys, os, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_socket_bridge import SocketBridge
from banc_live import SCENE, sans_commentaires
import arma_couture as C
SB = "/mnt/data/harmattan-sandbox"; EXT, PORT = 5830, 6062
LOG = SB + "/logs/serverJ2.out"
def sh(c): subprocess.run(c, shell=True, executable="/bin/bash")
if __name__ == "__main__":
    C.CX, C.CY = 4644.0, 5652.0; C.SCALE = 200.0
    open(LOG, "w").close()
    MES = []
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done"); time.sleep(4)
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid "
       "./arma3server_x64 -config='%s/staging/serverLV.cfg' -profiles='%s/profilesLV' "
       "-port=%d -world=Stratis -autoInit "
       "-mod='@CBA_A3;@rhsusaf;@rhsafrf;@LAMBS_Danger;@PinnedDown_BattleLines;@PinnedDown_CoverConcealment' "
       ">> '%s' 2>&1 < /dev/null & disown" % (SB, EXT, SB, SB, PORT, LOG))
    time.sleep(45)
    b = SocketBridge(EXT); time.sleep(3)
    b.send(sans_commentaires(SCENE), wait=False); time.sleep(6)
    b.send('call compile preprocessFileLineNumbers "socle.sqf";', wait=False); time.sleep(3)
    b.send('call compile preprocessFileLineNumbers "jambes2.sqf";', wait=False); time.sleep(3)
    b.send('HMT_J2 = nil; [] spawn { HMT_J2 = [8] call HMT_JAMBES2; };', wait=False)
    print("  banc lance — 2x2, 8 par condition", flush=True)
    t0 = time.time(); vu = 0
    while time.time() - t0 < 1500:
        time.sleep(15)
        try: txt = open(LOG, errors="ignore").read()
        except Exception: txt = ""
        n = txt.count("HMT|J2|lieu|")
        if n != vu: print("    %d essais" % n, flush=True); vu = n
        if "HMT|J2|FINI" in txt or "HMT|J2|ECHEC" in txt: break
    sh("for p in $(pgrep -f arma3server_x64); do kill $p; done")
    print("  termine — %d essais" % vu, flush=True)
