"""CALIBRATION, PAS UN VERDICT. Combien l Oracle punit-il A SON BUDGET NORMAL, tout seul, sans qu on lui amene
personne ? On compare le bras Oracle au bras temoin d ORACLE-P2-19-09 sur des issues d ADVERSAIRE ( compromission,
pertes, abandon ), pas sur l effet du choix de traversee : cette campagne est close et sa question ne sera pas lue.
Regles de lecture reprises telles quelles : premier episode ACCEPTE de chaque ( niveau, option, monde, situation )."""
import glob, json, os, random, re
H = "/mnt/data/hmt"; CAMPAGNE = "ORACLE-P2-19-09"
MONDES = (4, 5, 6, 7, 8, 9, 11, 12)
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


def entier(x, d=None):
    try: return int(float(x))
    except Exception: return d


E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-1*/job.json") + glob.glob(f"{H}/runs/2026-09-20_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        e = dict(monde=int(re.search(r"/g(\d+)", d).group(1)), option=j.get("traversee"), niveau=j.get("oracle_cmd"),
                 situation=j.get("situation"), quand=os.path.basename(os.path.dirname(jf)))
        try:
            if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
        if not fin: continue
        e.update(t_fin=float(fin.group(1)), issue=fin.group(2), vivants=entier(fin.group(3)),
                 compromis=entier(fin.group(4)), alarme=entier(fin.group(5)))
        e["discrete"] = int(e["compromis"] == 0 and e["alarme"] == 0 and e["vivants"] == 10)
        dec = [champs(m) for m in re.findall(r'"CHACAL\|E\|decision\|([^"]*)"', t)]
        e["n_decisions"] = len([x for x in dec if x.get("point") == "TRAVERSEE"])
        orc = re.findall(r'"CHACAL\|O\|decision\|[^"]*\|action\|([A-Z_]+)\|[^"]*\|budget\|(\d+)', t)
        e["ordres"] = sum(1 for a, _ in orc if a.startswith("PATROUILLE"))
        e["budget_fin"] = entier(orc[-1][1]) if orc else None
        E.append(e)

vus = set(); A = []
for e in sorted(E, key=lambda x: x["quand"]):
    cle = (e["niveau"], e["option"], e["monde"], e["situation"])
    if cle in vus or e["monde"] not in MONDES: continue
    vus.add(cle); A.append(e)
O = [e for e in A if e["niveau"] == 1]; T = [e for e in A if e["niveau"] == 0]
print(f"CALIBRATION de l adversaire sur {CAMPAGNE} : {len(A)} episodes lus ( Oracle {len(O)}, temoin {len(T)} )\n")


def taux(L, f): return sum(1 for e in L if f(e)) / len(L) if L else float("nan")


def bootstrap(f, B=10000, graine=20260920):
    r = random.Random(graine); d = []
    par = {w: ([e for e in O if e["monde"] == w], [e for e in T if e["monde"] == w]) for w in MONDES}
    utiles = [w for w in MONDES if par[w][0] and par[w][1]]
    for _ in range(B):
        tir = [par[r.choice(utiles)] for _ in utiles]
        d.append(sum(taux(o, f) for o, _ in tir) / len(tir) - sum(taux(t, f) for _, t in tir) / len(tir))
    d.sort(); return d[int(0.025 * B)], d[int(0.975 * B)]


LIGNES = [
    ("compromis en phase 2", lambda e: e["compromis"] == 1),
    ("alarme donnee", lambda e: e["alarme"] == 1),
    ("au moins un homme perdu", lambda e: e["vivants"] < 10),
    ("pris AVANT la decision", lambda e: e["n_decisions"] == 0),
    ("phase discrete ( issue primaire )", lambda e: e["discrete"] == 1),
]
print(f"{'issue':<36} {'Oracle':>8} {'temoin':>8} {'ecart':>8}   IC 95 % apparie par monde")
for nom, f in LIGNES:
    a, b = taux(O, f), taux(T, f); lo, hi = bootstrap(f)
    etoile = "  <<<" if (lo > 0 or hi < 0) else ""
    print(f"{nom:<36} {a:>8.3f} {b:>8.3f} {a - b:>+8.3f}   [{lo:+.3f} ; {hi:+.3f}]{etoile}")

print(f"\ndetail Oracle : ordres de patrouille par episode {sum(e['ordres'] for e in O) / len(O):.1f} ; "
      f"budget restant a la fin {sum(e['budget_fin'] for e in O if e['budget_fin'] is not None) / max(1, sum(1 for e in O if e['budget_fin'] is not None)):.1f} sur 6")
from collections import Counter
print("issues Oracle :", dict(Counter(e["issue"] for e in O)))
print("issues temoin :", dict(Counter(e["issue"] for e in T)))
print("\npar monde ( compromis Oracle / temoin ) :",
      {w: (round(taux([e for e in O if e["monde"] == w], lambda e: e["compromis"] == 1), 2),
           round(taux([e for e in T if e["monde"] == w], lambda e: e["compromis"] == 1), 2)) for w in MONDES})
