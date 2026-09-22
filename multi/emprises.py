"""Emprise v2 : segments poser-route-crete-site-regroupement + base de la reserve ( point ). Ensembles compatibles."""
import glob, json, math, re, itertools, os
H = "/mnt/data/hmt"
M, SRC = {}, {}
for rf in sorted(glob.glob(f"{H}/runs/2026-09-*/g*/resultat.json"), reverse=True):
    mm = re.search(r"runs/([^/]+)/g(\d+)/resultat", rf)
    if not mm: continue
    w = int(mm.group(2))
    if w in M: continue
    try: o = json.load(open(rf)).get("entete", {}).get("opord") or []
    except Exception: continue
    d = {}
    for i in range(0, len(o) - 1):
        if o[i] in ("site", "crete", "route", "reserve", "depose", "rally"):
            try: d[o[i]] = [float(x) for x in str(o[i + 1]).strip("[]").split(",")[:2]]
            except Exception: pass
    if len(d) == 6: M[w] = d; SRC[w] = mm.group(1)
def seg(a, b, pas=250):
    n = max(1, int(math.dist(a, b) / pas)); return [[a[0] + (b[0] - a[0]) * t / n, a[1] + (b[1] - a[1]) * t / n] for t in range(n + 1)]
def pts(d): return seg(d["depose"], d["route"]) + seg(d["route"], d["crete"]) + seg(d["crete"], d["site"]) + seg(d["site"], d["rally"]) + [d["reserve"]]
P = {w: pts(M[w]) for w in M}
W = sorted(M)
D = {}
for a, b in itertools.combinations(W, 2):
    D[(a, b)] = min(math.dist(p, q) for p in P[a] for q in P[b])
json.dump({"mondes": M, "source": SRC, "distances": {f"{a}-{b}": round(v) for (a, b), v in D.items()}}, open(f"{H}/depot/multi/emprises.json", "w"))
A = set(range(4, 10)) | set(range(11, 25))
for seuil in (3000, 2500, 2000):
    ok = {k for k, v in D.items() if v >= seuil}
    best = []
    def ext(cl, cand):
        global best
        if len(cl) > len(best): best = cl[:]
        for i, c in enumerate(cand):
            if len(cl) + len(cand) - i <= len(best): return
            ext(cl + [c], [x for x in cand[i + 1:] if (min(c, x), max(c, x)) in ok])
    ext([], W)
    bA = []
    def extA(cl, cand):
        global bA
        if len(cl) > len(bA): bA = cl[:]
        for i, c in enumerate(cand):
            if len(cl) + len(cand) - i <= len(bA): return
            extA(cl + [c], [x for x in cand[i + 1:] if (min(c, x), max(c, x)) in ok])
    extA([], [w for w in W if w in A])
    print(f"seuil {seuil} m : {len(ok)}/{len(D)} paires ; max tous mondes {len(best)} {best} ; max mondes A {len(bA)} {bA}")
print("sources :", sorted(set(SRC.values()))[:3], "...", len(set(SRC.values())), "runs")
print("A presents :", sorted(w for w in W if w in A))
print("paires les plus proches ( controle positif du journal croise ) :", sorted((round(v), k) for k, v in D.items())[:6])
