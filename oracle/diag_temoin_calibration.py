"""Le temoin de la calibration compromet 0,258 ; celui d ORACLE-P2 compromettait 0,082. Pourquoi ?
Hypothese : dans la calibration l option est CONFONDUE avec la situation ( s1-s2 traverser, s3-s4 attendre ),
alors qu ORACLE-P2 croisait les deux. On decompose par ( option, situation )."""
import glob, json, os, re
from collections import defaultdict
H = "/mnt/data/hmt"
RX_FIN = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[0-9.]+\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)')


def lire(campagne, filtre):
    vus, out = set(), []
    for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
        j = json.load(open(jf))
        if j.get("campagne") != campagne or not filtre(j): continue
        for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
            w = int(re.search(r"/g(\d+)", d).group(1))
            cle = (w, j.get("traversee"), j.get("situation"))
            if cle in vus: continue
            try:
                if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
                t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
            except Exception: continue
            m = RX_FIN.search(t)
            if not m: continue
            vus.add(cle)
            out.append(dict(monde=w, option=j.get("traversee"), situation=j.get("situation"),
                            compromis=int(m.group(3)), issue=m.group(1)))
    return out


def tableau(nom, L):
    par = defaultdict(list)
    for e in L: par[(e["option"], e["situation"])].append(e["compromis"])
    print(f"\n{nom} : {len(L)} episodes, compromission globale {sum(e['compromis'] for e in L) / len(L):.3f}")
    print(f"   {'option':>7} {'situation':>10} {'n':>4} {'compromis':>10}")
    for k in sorted(par): print(f"   {k[0]:>7} {k[1]:>10} {len(par[k]):>4} {sum(par[k]) / len(par[k]):>10.3f}")
    for o in (1, 2):
        v = [e["compromis"] for e in L if e["option"] == o]
        if v: print(f"   option {o} tout confondu : {sum(v) / len(v):.3f} ( n = {len(v)} )")


A = lire("ORACLE-P2-19-09", lambda j: j.get("oracle_cmd") == 0)
B_ = lire("CALIBRATION-ADVERSAIRE-20-09", lambda j: j.get("oracle_cmd") == 0)
tableau("TEMOIN d ORACLE-P2-19-09", A)
tableau("TEMOIN de la CALIBRATION", B_)
print("\n--- les memes cases, dans les deux campagnes ---")
ca = {(e["option"], e["situation"]) for e in A}; cb = {(e["option"], e["situation"]) for e in B_}
print("   cases d ORACLE-P2 :", sorted(ca))
print("   cases de la calibration :", sorted(cb))
com = ca & cb
if com:
    for k in sorted(com):
        va = [e["compromis"] for e in A if (e["option"], e["situation"]) == k]
        vb = [e["compromis"] for e in B_ if (e["option"], e["situation"]) == k]
        print(f"   {k} : P2 {sum(va) / len(va):.3f} ( n {len(va)} )   calibration {sum(vb) / len(vb):.3f} ( n {len(vb)} )")
