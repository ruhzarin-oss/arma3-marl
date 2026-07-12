import time, threading, sys
import officer_geo as OG, officer_live
from collect_geo_recon import geo_features

def probe(srv, brain, delay):
    time.sleep(delay)
    t0 = time.time()
    try:
        env, _ = OG.setup(srv, 6000 + srv, "standard")
        f = geo_features(env)
        for _ in range(15):
            env.step([officer_live._act(env, brain, si) for si in range(env.S)])
        return {"srv": srv, "ok": True, "n": f["n"] if f else 0, "dt": round(time.time() - t0, 1)}
    except Exception as e:
        return {"srv": srv, "ok": False, "err": type(e).__name__ + ":" + str(e)[:40], "dt": round(time.time() - t0, 1)}

brain = OG._brain()
STAGGER = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
N = int(sys.argv[2]) if len(sys.argv) > 2 else 12
print("=== %d concurrents, stagger %.1fs/worker ===" % (N, STAGGER), flush=True)
res = {}; lock = threading.Lock()
def w(srv):
    r = probe(srv, brain, srv * STAGGER)
    with lock: res[srv] = r
th = [threading.Thread(target=w, args=(s,)) for s in range(N)]
for t in th: t.start()
for t in th: t.join()
ok = sum(1 for r in res.values() if r["ok"])
for s in range(N):
    r = res[s]; print("  srv%2d: %-3s dt=%ss %s" % (s, "OK" if r["ok"] else "KO", r["dt"], r.get("err", "")), flush=True)
print("RESULTAT: %d/%d ok" % (ok, N), flush=True)
