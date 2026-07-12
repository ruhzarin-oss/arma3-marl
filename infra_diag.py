"""infra_diag — TRANCHE la cause de l'infra flaky. Phase A : sonde CHAQUE serveur seul (sequentiel,
concurrence 1) = sont-ils sains individuellement ? Phase B : 12 sondes CONCURRENTES = la concurrence casse-t-elle ?
Verdict : A=16 sains + B casse -> CONCURRENCE ; A montre des KO -> SERVEURS pas remontes sains."""
import time, threading
import officer_geo as OG
import officer_live
from collect_geo_recon import geo_features

NSRV = 16


def probe(srv, brain, steps=15):
    """spawn + lecture + quelques pas (exerce le pont en continu). OK si tout passe."""
    t0 = time.time()
    try:
        env, garr = OG.setup(srv, 5000 + srv, "standard")
        f = geo_features(env)
        n0 = f["n"] if f else 0
        for _ in range(steps):
            env.step([officer_live._act(env, brain, si) for si in range(env.S)])
        return {"srv": srv, "ok": True, "n": n0, "dt": round(time.time() - t0, 1)}
    except Exception as e:
        return {"srv": srv, "ok": False, "err": type(e).__name__ + ":" + str(e)[:40], "dt": round(time.time() - t0, 1)}


brain = OG._brain()

print("=== PHASE A : sonde par serveur (SEQUENTIEL, concurrence 1) ===", flush=True)
resA = []
for srv in range(NSRV):
    r = probe(srv, brain)
    resA.append(r)
    print("  srv%2d : %-3s n=%-2s dt=%4ss %s" % (r["srv"], "OK" if r["ok"] else "KO", r.get("n", "-"), r["dt"], r.get("err", "")), flush=True)
okA = sum(1 for r in resA if r["ok"])
print("PHASE A : %d/%d serveurs sains en solo" % (okA, NSRV), flush=True)

print("\n=== PHASE B : 12 sondes CONCURRENTES (test concurrence) ===", flush=True)
resB = {}; lock = threading.Lock()
def w(srv):
    r = probe(srv, brain)
    with lock: resB[srv] = r
th = [threading.Thread(target=w, args=(s,)) for s in range(12)]
t0 = time.time()
for t in th: t.start()
for t in th: t.join()
okB = sum(1 for r in resB.values() if r["ok"])
for s in range(12):
    r = resB[s]; print("  srv%2d : %-3s dt=%4ss %s" % (s, "OK" if r["ok"] else "KO", r["dt"], r.get("err", "")), flush=True)
print("PHASE B : %d/12 ok en concurrence (en %.0fs)" % (okB, time.time() - t0), flush=True)

print("\n=== VERDICT INFRA ===", flush=True)
if okA >= NSRV - 1 and okB >= 11:
    print("SAINE : serveurs OK en solo ET en concurrence -> le harnais de mesure avait un autre defaut", flush=True)
elif okA >= NSRV - 1 and okB < 11:
    print("CAUSE = CONCURRENCE : serveurs sains en solo (%d/16) mais la concurrence casse (%d/12) -> capper la concurrence + retry/backoff sur timeout" % (okA, okB), flush=True)
else:
    bad = [r["srv"] for r in resA if not r["ok"]]
    print("CAUSE = SERVEURS pas remontes sains : KO en solo = %s -> reparer le demarrage flotte (mission/pont par serveur)" % bad, flush=True)
print("INFRADIAG FINI", flush=True)
