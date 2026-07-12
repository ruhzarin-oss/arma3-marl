#!/usr/bin/env python3
"""bake_stratis.py — bake le VRAI relief de Stratis (getTerrainHeightASL) via le pont, sur un serveur DEJA lance (slot 14).
Sauve leviathan/stratis_heightmap.json {x0,y0,res,n,H} -> swap propre du heightmap dans traque_env (coque de perception du VRAI relief)."""
import sys, time, re, json
sys.path.insert(0, "/home/younes/arma3-marl")
from arma_bridge import ArmaBridge

SB = "/mnt/data/harmattan-sandbox"; SLOT = 14
MIS = SB + "/arma3server/mpmissions/HarmattanBridge14.Stratis"
LOG = SB + "/logs/server%d.out" % SLOT
X0, Y0, RES, N = 1000, 2000, 60, 90                 # couvre toute la zone de traque Stratis avec marge
OUT = "/home/younes/arma3-marl/leviathan/stratis_heightmap.json"

b = ArmaBridge(mission=MIS, log=LOG); time.sleep(2)
for _ in range(18):
    b.send('diag_log format ["HARMATTAN_PING %1",1];'); time.sleep(0.4)
    if any("HARMATTAN_PING 1" in l for l in b._log_lines(120)): print("[pont] handshake OK", flush=True); break
    time.sleep(1.5)
cmd = ('[] spawn { for "_ry" from 0 to %d do { private _y = %d + _ry*%d; private _r=[]; '
       'for "_c" from 0 to %d do { _r pushBack round(getTerrainHeightASL [%d + _c*%d, _y]) }; '
       'diag_log format ["HARMATTAN_HM %%1 %%2", _ry, _r]; }; diag_log "HARMATTAN_HM_DONE"; };' % (N - 1, Y0, RES, N - 1, X0, RES))
b.send(cmd, timeout=20)
t0 = time.time()
while time.time() - t0 < 90:
    if any("HARMATTAN_HM_DONE" in l for l in b._log_lines(6000)): break
    time.sleep(1)
rows = {}
for ln in b._log_lines(14000):
    m = re.search(r"HARMATTAN_HM (\d+) (\[.*\])", ln)
    if m:
        try: rows[int(m.group(1))] = json.loads(m.group(2).replace(" ", ""))
        except Exception: pass
H = [rows[i] for i in range(N) if i in rows]
ok = len(H) == N and all(len(r) == N for r in H)
print("rangees %d/%d | largeur_ok=%s" % (len(H), N, all(len(r) == N for r in H)), flush=True)
if ok:
    hmin = min(min(r) for r in H); hmax = max(max(r) for r in H)
    json.dump({"x0": X0, "y0": Y0, "res": RES, "n": N, "H": H}, open(OUT, "w"))
    print("ecrit %s | altitude %d..%d m | relief brut = %d m" % (OUT, hmin, hmax, hmax - hmin), flush=True)
else:
    print("ECHEC bake (rangees manquantes)", flush=True)
print("BAKE_DONE", flush=True)
