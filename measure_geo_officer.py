"""measure_geo_officer — LE LIVRABLE chiffre : officier ADAPTATIF (lit la geometrie -> manoeuvre championne)
vs meilleure FIXE (M2), sur les 5 geometries. Renversement du -12 : l'adaptatif bat-il enfin le tetu ?"""
import argparse, threading, json, time
import numpy as np
import officer_geo as OG
from officer_geo import GEOS, SH, BEST_FIXED


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reps", type=int, default=10); p.add_argument("--servers", type=int, default=16)
    p.add_argument("--out", type=str, default="geo_officer.jsonl")
    p.add_argument("--seed0", type=int, default=900); p.add_argument("--append", action="store_true")
    a = p.parse_args()
    jobs = []
    for rep in range(a.reps):
        for gi, geo in enumerate(GEOS):
            seed = a.seed0 + rep * 5 + gi
            jobs.append((seed, geo, "adaptatif")); jobs.append((seed, geo, "fixe"))
    if not a.append:
        open(a.out, "w").close()
    lock = threading.Lock(); cur = [0]; results = []
    print("=== MESURE GEO-OFFICIER : %d ops (%d geo x %d reps x 2) ===" % (len(jobs), len(GEOS), a.reps), flush=True)

    def worker(srv):
        time.sleep(srv * 1.5)                 # stagger : etale les spawns initiaux
        brain = OG._brain()                   # UN cerveau par worker
        env = OG.make_env(srv, 9000 + srv)    # UN env/pont par worker -> REUTILISE (1 connexion/serveur, anti-timeout)
        try:
            while True:
                with lock:
                    if cur[0] >= len(jobs): return
                    seed, geo, cond = jobs[cur[0]]; cur[0] += 1
                try:
                    garrison = OG.respawn(env, geo, seed)     # re-spawn sur le MEME pont (reset monde + deleteGroup)
                    m = (OG.run_adaptive(env, garrison, geo, brain) if cond == "adaptatif"
                         else OG.run_fixed(env, garrison, geo, brain, BEST_FIXED))
                    rec = {"geo": geo, "cond": cond, "mil": bool(m["mil"]), "man": m["man"],
                           "reco_ok": m.get("reco_ok"), "pred": m.get("pred_geo")}
                except Exception as e:
                    rec = {"geo": geo, "cond": cond, "err": type(e).__name__ + ":" + str(e)[:60]}
                with lock:
                    results.append(rec)
                    with open(a.out, "a") as f: f.write(json.dumps(rec) + "\n")
                    ok = [r for r in results if "mil" in r]
                    na = sum(1 for r in ok if r["cond"] == "adaptatif" and r["mil"]); da = sum(1 for r in ok if r["cond"] == "adaptatif")
                    nf = sum(1 for r in ok if r["cond"] == "fixe" and r["mil"]); df = sum(1 for r in ok if r["cond"] == "fixe")
                    print("[%d/%d] %s/%s mil=%s (adapt %d/%d, fixe %d/%d)" % (len(results), len(jobs), SH[geo], cond, rec.get("mil"), na, da, nf, df), flush=True)
        finally:
            OG.close_env(env)

    th = [threading.Thread(target=worker, args=(s,)) for s in range(a.servers)]
    for t in th: t.start()
    for t in th: t.join()
    analyse(a.out)


def analyse(path):
    rows = [json.loads(l) for l in open(path)]; ok = [r for r in rows if "mil" in r]
    ad = [r for r in ok if r["cond"] == "adaptatif"]; fx = [r for r in ok if r["cond"] == "fixe"]
    def pct(rs): return 100 * sum(r["mil"] for r in rs) / max(1, len(rs))
    print("\n===== LIVRABLE : OFFICIER ADAPTATIF vs FIXE (M2) =====", flush=True)
    print("ADAPTATIF : %d/%d = %.0f%%" % (sum(r["mil"] for r in ad), len(ad), pct(ad)))
    print("FIXE (M2) : %d/%d = %.0f%%" % (sum(r["mil"] for r in fx), len(fx), pct(fx)))
    print("ECART = %+.0f points   (hier, sur les postures comportementales : -12)" % (pct(ad) - pct(fx)))
    rok = [r for r in ad if r.get("reco_ok") is not None]
    if rok:
        print("reconnaissance EN BOUCLE : %.0f%% (%d/%d)" % (100 * sum(r["reco_ok"] for r in rok) / len(rok), sum(r["reco_ok"] for r in rok), len(rok)))
    print("\npar geometrie (adaptatif | fixe | manoeuvre(s) lue(s)) :")
    for g in GEOS:
        aa = [r for r in ad if r["geo"] == g]; ff = [r for r in fx if r["geo"] == g]
        mans = sorted(set(r["man"] for r in aa))
        print("  %-5s adapt %d/%d | fixe %d/%d | %s" % (SH[g], sum(r["mil"] for r in aa), len(aa), sum(r["mil"] for r in ff), len(ff), mans))


if __name__ == "__main__":
    main()
