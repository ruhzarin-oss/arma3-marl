"""Lecture UNIQUE de CALIBRATION-ADVERSAIRE-20-09 ( criteres : oracle/CRITERES_CALIBRATION.md, ecrits avant ).
Portes K1-K6, puis trois lectures : L1 controle negatif, L2 calibration de la periode, L3 admissibilite des mondes."""
import ast, glob, json, os, random, re, sys
H = "/mnt/data/hmt"; CAMPAGNE = os.environ.get("CAMPAGNE_LUE", "CALIBRATION-ADVERSAIRE-20-09")
MONDES = (4, 5, 6, 7, 8, 9, 11, 12); B, GRAINE = 10000, 20260920
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
RX_FIN = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[0-9.]+\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)')


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


def ent(x, d=None):
    try: return int(float(x))
    except Exception: return d


def bras_de(j):
    if j.get("oracle_cmd") == 0: return "T"
    if j.get("oracle_b") == 0: return "N"
    return "F" if j.get("oracle_delta") == 30 else "R"


E = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        e = dict(monde=int(re.search(r"/g(\d+)", d).group(1)), bras=bras_de(j), situation=j.get("situation"),
                 b=j.get("oracle_b"), delta=j.get("oracle_delta"), cmd=j.get("oracle_cmd"),
                 quand=os.path.basename(os.path.dirname(jf)), verdict=None, erreurs=0)
        try:
            e["verdict"] = json.load(open(d + "resultat.json")).get("verdict")
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: E.append(e); continue
        e["erreurs"] = len(RX_ERR.findall(t))
        m = RX_FIN.search(t)
        if m: e.update(issue=m.group(1), vivants=ent(m.group(2)), compromis=ent(m.group(3)), alarme=ent(m.group(4)))
        e["discrete"] = int(bool(m) and e.get("compromis") == 0 and e.get("alarme") == 0 and e.get("vivants") == 10)
        dec = [champs(x) for x in re.findall(r'"CHACAL\|O\|decision\|([^"]*)"', t)]
        e["n_dec_orc"] = len(dec)
        e["ordres"] = sum(1 for x in dec if (x.get("action") or "").startswith("PATROUILLE"))
        ts = [float(x.split("|")[0]) for x in re.findall(r'"CHACAL\|O\|decision\|([^"]*)"', t)]
        e["periode"] = round((ts[-1] - ts[0]) / max(1, len(ts) - 1)) if len(ts) > 2 else None
        dd = [ent(x.get("patrouille_a")) for x in dec]
        dd = [x for x in dd if x is not None and x >= 0]
        e["dpat_min"] = min(dd) if dd else None
        c = re.search(r'"CHACAL\|O\|carte\|([^"]*)"', t)
        if c:
            cc = champs(c.group(1)); e["cases_routieres"] = ent(cc.get("cases_routieres"))
            try: e["carte"] = ast.literal_eval(cc.get("detail", "[]").replace('"', ""))
            except Exception: e["carte"] = None
        E.append(e)

vus = set(); A = []
for e in sorted(E, key=lambda x: x["quand"]):
    if e["verdict"] != "ACCEPTE" or e["monde"] not in MONDES: continue
    cle = (e["bras"], e["monde"], e["situation"])
    if cle in vus: continue
    vus.add(cle); A.append(e)
BRAS = ("T", "N", "R", "F")
P = {b: [e for e in A if e["bras"] == b] for b in BRAS}
cases_prevues = {(b, w, s) for b in BRAS for w in MONDES for s in (1, 2, 3, 4)}
cases_avec = {(e["bras"], e["monde"], e["situation"]) for e in E if e["verdict"] is not None}
print(f"== CALIBRATION DE L ADVERSAIRE : {len(E)} episodes joues, {len(A)} lus "
      f"( T {len(P['T'])}, N {len(P['N'])}, R {len(P['R'])}, F {len(P['F'])} )")
ORC = [e for e in A if e["cmd"] == 1]
portes = [
    ("K1 zero erreur SQF", sum(e["erreurs"] for e in A) == 0, f"{sum(e['erreurs'] for e in A)} erreur(s)"),
    ("K2 aucune case sans le moindre resultat", len(cases_prevues - cases_avec) == 0,
     f"{len(cases_prevues - cases_avec)} case(s) vide(s) sur {len(cases_prevues)}"),
    ("K3 au moins 24 episodes valides par bras", all(len(P[b]) >= 24 for b in BRAS),
     " ".join(f"{b}:{len(P[b])}" for b in BRAS)),
    ("K4 ligne de carte presente a Oracle monte", bool(ORC) and all(e.get("cases_routieres") is not None for e in ORC),
     f"{sum(1 for e in ORC if e.get('cases_routieres') is None)} absente(s) sur {len(ORC)}"),
    ("K5 [ NEGATIF, MECANIQUE ] bras N : zero ordre de patrouille", bool(P["N"]) and all(e["ordres"] == 0 for e in P["N"]),
     f"{sum(e['ordres'] for e in P['N'])} ordre(s) sur {len(P['N'])} episodes"),
    ("K6 periode jouee conforme au job", all((e.get("periode") is None) or abs(e["periode"] - e["delta"]) <= 8 for e in A if e["cmd"] == 1),
     f"{sum(1 for e in A if e['cmd'] == 1 and e.get('periode') is not None and abs(e['periode'] - e['delta']) > 8)} ecart(s)"),
]
for nom, ok, d in portes: print(f"   {'PASSE ' if ok else 'ECHOUE'}  {nom} : {d}")
if not all(ok for _, ok, _ in portes):
    print("\n   LECTURE REFUSEE : une porte de qualite a echoue. Rien n est lu."); raise SystemExit


def taux(L, f): return sum(1 for e in L if f(e)) / len(L) if L else float("nan")


def ic(a, b, f, graine=GRAINE):
    r = random.Random(graine); d = []
    util = [w for w in MONDES if [e for e in P[a] if e["monde"] == w] and [e for e in P[b] if e["monde"] == w]]
    for _ in range(B):
        tir = [r.choice(util) for _ in util]
        d.append(sum(taux([e for e in P[a] if e["monde"] == w], f) for w in tir) / len(tir)
                 - sum(taux([e for e in P[b] if e["monde"] == w], f) for w in tir) / len(tir))
    d.sort(); return d[int(0.025 * B)], d[int(0.975 * B)]


disc = lambda e: e["discrete"] == 1
compr = lambda e: e.get("compromis") == 1
lo, hi = ic("N", "T", disc)
print(f"\n== L1  controle negatif : l Oracle sans budget agit-il quand meme ?")
print(f"   reussite N {taux(P['N'], disc):.3f}   T {taux(P['T'], disc):.3f}   ecart {taux(P['N'], disc) - taux(P['T'], disc):+.3f}  IC [{lo:+.3f} ; {hi:+.3f}]")
print(f"   {'PASSE : indiscernable du temoin.' if lo <= 0 <= hi else 'ECHOUE : l Oracle agit AUTREMENT que par ses ordres. Toute mesure faite avec lui est suspecte.'}")

print(f"\n== L2  calibration de la periode de decision")
print(f"   {'bras':<4} {'reussite':>9} {'compromis':>10} {'ordres':>7} {'periode':>8}  IC de l ecart au temoin")
for b in BRAS:
    e_ic = ("     —" if b == "T" else "[%+.3f ; %+.3f]" % ic(b, "T", disc))
    per = [e["periode"] for e in P[b] if e.get("periode")]
    print(f"   {b:<4} {taux(P[b], disc):>9.3f} {taux(P[b], compr):>10.3f} "
          f"{sum(e['ordres'] for e in P[b]) / max(1, len(P[b])):>7.1f} "
          f"{(sum(per) / len(per) if per else float('nan')):>8.0f}  {e_ic}")
cand = {b: taux(P[b], disc) for b in ("R", "F")}
hauts = {b: ic(b, "T", disc) for b in ("R", "F")}
retenu = min(cand, key=lambda b: abs(cand[b] - 0.50))
print(f"\n   regle ecrite d avance : le delta dont la reussite est la plus proche de 0,50, borne haute de son IC < 0,85")
print(f"   R {cand['R']:.3f}   F {cand['F']:.3f}   -> retenu : {retenu} ( delta {30 if retenu == 'F' else 60} s )")
gain = taux(P["R"], compr) - taux(P["F"], compr)
print(f"   falsificateur : F doit gagner >= 5 points de compromission sur R -> "
      f"{taux(P['F'], compr) - taux(P['R'], compr):+.3f} "
      f"{'FRANCHI : la periode n est PAS le levier, chercher ailleurs.' if (taux(P['F'], compr) - taux(P['R'], compr)) < 0.05 else 'non franchi : la periode est bien un levier.'}")

print(f"\n== L3  admissibilite des mondes ( mesuree, aucune exclusion ici )")
print(f"   {'monde':>5} {'cases_rte':>10} {'dist_max_a_la_route':>20} {'compr_R+F':>10} {'dpat_min':>9}")
for w in MONDES:
    ce = [e for e in ORC if e["monde"] == w and e.get("carte")]
    n_rte = ce[0]["cases_routieres"] if ce else None
    dmax = max((x[2] for x in ce[0]["carte"] if x[2] is not None and x[2] >= 0), default=None) if ce else None
    rf = [e for e in A if e["monde"] == w and e["bras"] in ("R", "F")]
    dd = [e["dpat_min"] for e in rf if e.get("dpat_min") is not None]
    print(f"   {w:>5} {str(n_rte):>10} {str(dmax):>20} {taux(rf, compr):>10.2f} {(min(dd) if dd else -1):>9}")
