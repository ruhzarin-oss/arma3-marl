"""Quelles cases manquent, et quels jobs les remplissent ? ( couverture seule, aucun effet )"""
import glob, json, os, re
H = "/mnt/data/hmt"
E = {}
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != "ORACLE-P2-19-09": continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        w = int(re.search(r"/g(\d+)", d).group(1))
        try: v = json.load(open(d + "resultat.json")).get("verdict")
        except Exception: v = None
        cle = (w, j["oracle_cmd"], j["traversee"], j["situation"])
        E.setdefault(cle, []).append(v)
print("== cases ( monde, niveau, option ) a moins de 3 episodes acceptes")
from collections import defaultdict
C = defaultdict(list)
for (w, n, o, s), vs in E.items():
    C[(w, n, o)].extend([v for v in vs if v == "ACCEPTE"])
manquants = []
for (w, n, o), vs in sorted(C.items()):
    if len(vs) < 3:
        print(f"   monde {w} niveau {n} option {o} : {len(vs)} accepte(s)")
        for s in (1, 2, 3, 4):
            if not [v for v in E.get((w, n, o, s), []) if v == "ACCEPTE"]:
                manquants.append((w, n, o, s))
print("\n== episodes a rejouer ( monde, niveau, option, situation )")
for m in manquants: print("   ", m)
print(f"\n== jobs correspondants ( une paire de mondes par job )")
paires = {4: [4, 5], 5: [4, 5], 6: [6, 7], 7: [6, 7], 8: [8, 9], 9: [8, 9], 11: [11, 12], 12: [11, 12]}
jobs = sorted({(tuple(paires[w]), n, o, s) for w, n, o, s in manquants})
for p, n, o, s in jobs: print(f"    OP2 n{n} t{o} s{s} g{p[0]}g{p[1]}")
print(f"   soit {len(jobs)} jobs, {2 * len(jobs)} episodes")
