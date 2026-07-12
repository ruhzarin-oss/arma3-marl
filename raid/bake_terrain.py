#!/usr/bin/env python3
"""bake_terrain.py — extrait UNE FOIS un heightmap FIN (20 m/cellule) autour de l'objectif du raid,
depuis Arma (getTerrainHeightASL), pour la LOS de l'env rapide fidele. Sauve raid/obj_heightmap.json.
altis_relief.json est trop grossier (240 m) pour le combat 100-300 m -> ce bake donne la cote terrain reelle."""
import os, sys, time, subprocess, re, json
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"; SLOT = 2; PORT = 2402 + SLOT * 100
MIS = SB + "/arma3server/mpmissions/HarmattanBridge%d.Altis" % SLOT
LOG = SB + "/logs/server%d.out" % SLOT
X0, Y0, RES, N = 13300, 15400, 20, 90          # 90x90 a 20 m = 1800 m autour de l'objectif (14038,16143)
OUT = "/home/younes/arma3-marl/raid/obj_heightmap.json"

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)
def launch():
    sh("pkill -9 -f 'profiles%d'" % SLOT); time.sleep(3)
    sh("rm -rf '%s'; cp -r '%s/arma3server/mpmissions/HarmattanBridge.Altis' '%s'" % (MIS, SB, MIS))
    sh("rm -f '%s/hmt_bridge/'cmd_*.sqf" % MIS)
    sh("sed 's/HarmattanBridge\\.Altis/HarmattanBridge%d.Altis/g' '%s/staging/server.cfg' > '%s/staging/server%d.cfg'" % (SLOT, SB, SB, SLOT))
    sh("mkdir -p '%s/profiles%d'; : > '%s'" % (SB, SLOT, LOG))
    sh("cd '%s/arma3server' && HMT_EXT_PORT=%d LD_LIBRARY_PATH=.:./linux64 setsid ./arma3server_x64 -config='%s/staging/server%d.cfg' -profiles='%s/profiles%d' -port=%d -world=Altis -autoInit >> '%s' 2>&1 < /dev/null & disown" % (SB, 5801 + SLOT, SB, SLOT, SB, SLOT, PORT, LOG))
def wait_boot(t=200):
    t0 = time.time()
    while time.time() - t0 < t:
        try:
            if "Starting mission" in open(LOG, encoding="utf-8", errors="ignore").read(): time.sleep(10); return True
        except FileNotFoundError: pass
        time.sleep(4)
    return False

def main():
    print("=== BAKE HEIGHTMAP %dx%d @ %dm autour de (14038,16143) ===" % (N, N, RES), flush=True)
    launch(); print("boot...", flush=True)
    if not wait_boot(): print("ECHEC boot", flush=True); return
    b = ArmaBridge(mission=MIS, log=LOG); time.sleep(3)
    for _ in range(18):                                   # handshake
        b.send('diag_log format ["HARMATTAN_PING %1",1];'); time.sleep(0.4)
        if any("HARMATTAN_PING 1" in l for l in b._log_lines(80)): break
        time.sleep(1.5)
    # bake : une boucle (enveloppee [] spawn -> pile fraiche), 1 ligne diag_log par rangee
    cmd = ('[] spawn { for "_ry" from 0 to %d do { private _y = %d + _ry*%d; private _r=[]; '
           'for "_c" from 0 to %d do { _r pushBack round(getTerrainHeightASL [%d + _c*%d, _y]) }; '
           'diag_log format ["HARMATTAN_HM %%1 %%2", _ry, _r]; }; diag_log "HARMATTAN_HM_DONE"; };' % (N - 1, Y0, RES, N - 1, X0, RES))
    b.send(cmd, timeout=20)
    t0 = time.time()
    while time.time() - t0 < 60:
        if any("HARMATTAN_HM_DONE" in l for l in b._log_lines(4000)): break
        time.sleep(1)
    rows = {}
    for ln in b._log_lines(8000):
        m = re.search(r"HARMATTAN_HM (\d+) (\[.*\])", ln)
        if m:
            try: rows[int(m.group(1))] = json.loads(m.group(2).replace(" ", ""))
            except Exception: pass
    H = [rows[i] for i in range(N) if i in rows]
    ok = len(H) == N and all(len(r) == N for r in H)
    print("rangees recues : %d/%d  largeur ok=%s" % (len(H), N, all(len(r) == N for r in H)), flush=True)
    if ok:
        hmin = min(min(r) for r in H); hmax = max(max(r) for r in H)
        json.dump({"x0": X0, "y0": Y0, "res": RES, "n": N, "H": H}, open(OUT, "w"))
        print("ecrit %s | altitude %d..%d m | relief brut=%d m" % (OUT, hmin, hmax, hmax - hmin), flush=True)
    else:
        print("ECHEC bake (rangees manquantes)", flush=True)
    sh("pkill -9 -f 'profiles%d'" % SLOT)
    print("BAKE_DONE", flush=True)

if __name__ == "__main__":
    main()
