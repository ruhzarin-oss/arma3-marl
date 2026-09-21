"""Lecture UNIQUE de CALIBRATION-P2-V2-21-09 ( criteres : oracle/CRITERES_CALIBRATION_V2.md, ecrits avant ).
Portes K1-K7, puis L2 ( periode, seulement si K7 passe ) et L3 ( validation du critere de la route sur mondes neufs )."""
import glob, json, os, random, re
H = "/mnt/data/hmt"; CAMPAGNE = os.environ.get("CAMPAGNE_LUE", "CALIBRATION-P2-V2-21-09")
CONNUS = (4, 5, 6, 7, 8, 9, 11, 12); B, GRAINE = 10000, 20260921
RX_ERR = re.compile(r"Error in expression|Error Undefined variable|Error Generic error|Error Missing|Error Type")
RX_FIN = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[0-9.]+\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)')


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


def ent(x, d=None):
    try: return int(float(x))
    except Exception: return d


def bras_de(j):
    if j.get("oracle_cmd") == 0: return "T"
    return "F" if j.get("oracle_delta") == 30 else "R"


E, MONDES, OPTIONS_JOB = [], set(), set()
for jf in sorted(glob.glob(f"{H}/runs/2026-09-2*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != CAMPAGNE: continue
    MONDES.update(j["graines"]); OPTIONS_JOB.add(j.get("traversee"))
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        e = dict(monde=int(re.search(r"/g(\d+)", d).group(1)), bras=bras_de(j), situation=j.get("situation"),
                 cmd=j.get("oracle_cmd"), delta=j.get("oracle_delta"), quand=os.path.basename(os.path.dirname(jf)),
                 verdict=None, erreurs=0)
        try:
            e["verdict"] = json.load(open(d + "resultat.json")).get("verdict")
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: E.append(e); continue
        e["erreurs"] = len(RX_ERR.findall(t))
        m = RX_FIN.search(t)
        if m: e.update(vivants=ent(m.group(2)), compromis=ent(m.group(3)), alarme=ent(m.group(4)))
        e["discrete"] = int(bool(m) and e.get("compromis") == 0 and e.get("alarme") == 0 and e.get("vivants") == 10)
        e["fin"] = bool(m)
        cj = [champs(x) for x in re.findall(r'"CHACAL\|E\|choix_joue\|([^"]*)"', t)]
        cj = [x for x in cj if x.get("point") == "TRAVERSEE"]
        e["choix_joue"] = ent(cj[0].get("choix")) if cj else None
        ts = [float(x.split("|")[0]) for x in re.findall(r'"CHACAL\|O\|decision\|([^"]*)"', t)]
        e["periode"] = round((ts[-1] - ts[0]) / max(1, len(ts) - 1)) if len(ts) > 2 else None
        e["ordres"] = len(re.findall(r'"CHACAL\|O\|decision\|[^"]*\|action\|PATROUILLE', t))
        c = re.search(r'CHACAL\|O\|carte\|[^"]*\|cases_routieres\|(\d+)\|', t)
        e["cases_rte"] = int(c.group(1)) if c else None
        E.append(e)

MONDES = sorted(MONDES); NEUFS = [w for w in MONDES if w not in CONNUS]
vus = set(); A = []
for e in sorted(E, key=lambda x: x["quand"]):
    if e["verdict"] != "ACCEPTE" or not e.get("fin"): continue
    cle = (e["bras"], e["monde"], e["situation"])
    if cle in vus: continue
    vus.add(cle); A.append(e)
BRAS = ("T", "R", "F")
P = {b: [e for e in A if e["bras"] == b] for b in BRAS}
prevues = {(b, w, s) for b in BRAS for w in MONDES for s in (1, 2, 3, 4)}
avec = {(e["bras"], e["monde"], e["situation"]) for e in E if e["verdict"] is not None}
ORC = [e for e in A if e["cmd"] == 1]


def taux(L, f): return sum(1 for e in L if f(e)) / len(L) if L else float("nan")


compr = lambda e: e.get("compromis") == 1
disc = lambda e: e["discrete"] == 1


def ecart_ic(a, b, f, graine=GRAINE):
    r = random.Random(graine)
    util = [w for w in MONDES if any(e["monde"] == w for e in P[a]) and any(e["monde"] == w for e in P[b])]
    moy = lambda br, ws: sum(taux([e for e in P[br] if e["monde"] == w], f) for w in ws) / len(ws)
    pt = moy(a, util) - moy(b, util); d = []
    for _ in range(B):
        tir = [r.choice(util) for _ in util]; d.append(moy(a, tir) - moy(b, tir))
    d.sort(); return pt, d[int(0.025 * B)], d[int(0.975 * B)]


print(f"== CALIBRATION P2 v2 : {len(E)} episodes joues, {len(A)} lus ( T {len(P['T'])}, R {len(P['R'])}, F {len(P['F'])} )")
print(f"   mondes {MONDES} ; neufs {NEUFS}")
k7 = ecart_ic("R", "T", compr)
portes = [
    ("K1 zero erreur SQF", sum(e["erreurs"] for e in A) == 0, f"{sum(e['erreurs'] for e in A)} erreur(s)"),
    ("K2 aucune case sans resultat", not (prevues - avec), f"{len(prevues - avec)} vide(s) sur {len(prevues)} : {sorted(prevues - avec)[:6]}"),
    ("K3 au moins 48 episodes valides par bras", all(len(P[b]) >= 48 for b in BRAS), " ".join(f"{b}:{len(P[b])}" for b in BRAS)),
    ("K4 ligne de carte a Oracle monte", bool(ORC) and all(e["cases_rte"] is not None for e in ORC),
     f"{sum(1 for e in ORC if e['cases_rte'] is None)} absente(s) sur {len(ORC)}"),
    ("K5 option jouee = traverser", OPTIONS_JOB == {1} and all(e["choix_joue"] in (None, 1) for e in A),
     f"options des jobs {sorted(OPTIONS_JOB)} ; {sum(1 for e in A if e['choix_joue'] not in (None, 1))} choix joue(s) non conforme(s)"),
    ("K6 periode conforme au job", all(e["periode"] is None or abs(e["periode"] - e["delta"]) <= 8 for e in ORC),
     f"{sum(1 for e in ORC if e['periode'] is not None and abs(e['periode'] - e['delta']) > 8)} ecart(s)"),
    ("K7 [ SENSIBILITE ] R compromet >= 10 points de plus que T, IC hors de zero",
     k7[0] >= 0.10 and k7[1] > 0, f"ecart {k7[0]:+.3f} IC [{k7[1]:+.3f} ; {k7[2]:+.3f}]"),
]
for nom, ok, d in portes: print(f"   {'PASSE ' if ok else 'ECHOUE'}  {nom} : {d}")
qualite = all(ok for _, ok, _ in portes[:6])
if not qualite:
    print("\n   LECTURE REFUSEE : une porte de qualite ( K1-K6 ) a echoue. Rien n est lu."); raise SystemExit

print(f"\n== L2  la periode de decision")
print(f"   {'bras':<4} {'reussite':>9} {'compromis':>10} {'ordres':>7}")
for b in BRAS:
    print(f"   {b:<4} {taux(P[b], disc):>9.3f} {taux(P[b], compr):>10.3f} {sum(e['ordres'] for e in P[b]) / max(1, len(P[b])):>7.1f}")
if not portes[6][1]:
    print("   K7 A ECHOUE : le bras de reference ne se reproduit pas. La campagne n a pas la sensibilite voulue ; delta N EST PAS LU.")
else:
    for b in ("R", "F"):
        pt, lo, hi = ecart_ic(b, "T", disc); print(f"   reussite {b} - T : {pt:+.3f} IC [{lo:+.3f} ; {hi:+.3f}]")
    cand = {b: taux(P[b], disc) for b in ("R", "F")}
    ret = min(cand, key=lambda b: abs(cand[b] - 0.50))
    print(f"   regle : le delta le plus proche de 0,50 -> retenu {ret} ( delta {30 if ret == 'F' else 60} s ), reussite {cand[ret]:.3f}")
    g = ecart_ic("F", "R", compr)
    print(f"   falsificateur : F - R en compromission {g[0]:+.3f} IC [{g[1]:+.3f} ; {g[2]:+.3f}] -> "
          f"{'FRANCHI : la periode n est PAS le levier.' if g[0] < 0.05 else 'non franchi : la periode est un levier.'}")

print(f"\n== L3  la route predit-elle la prise ? ( apport de l Oracle = compromission R+F moins T, par monde )")


def apport(w):
    rf = [e for e in A if e["monde"] == w and e["bras"] in ("R", "F")]
    t = [e for e in A if e["monde"] == w and e["bras"] == "T"]
    return taux(rf, compr) - taux(t, compr) if rf and t else None


def classe(w):
    c = [e["cases_rte"] for e in ORC if e["monde"] == w and e["cases_rte"] is not None]
    return c[0] if c else None


for titre, ws in (("mondes CONNUS ( ont inspire le critere, pas un test )", CONNUS), ("mondes NEUFS ( la validation )", NEUFS)):
    print(f"\n   {titre}")
    for w in ws:
        a = apport(w); print(f"     monde {w:>2}  cases_rte {str(classe(w)):>4}  apport {('%+.3f' % a) if a is not None else '  n/a'}")
    hautes = [apport(w) for w in ws if (classe(w) or 0) >= 6 and apport(w) is not None]
    basses = [apport(w) for w in ws if classe(w) is not None and classe(w) <= 5 and apport(w) is not None]
    if len(hautes) < 2 or len(basses) < 2:
        print(f"     haute prise {len(hautes)} monde(s), basse prise {len(basses)} : NON EVALUABLE ( moins de 2 mondes dans une classe )")
    else:
        dh, db = sum(hautes) / len(hautes), sum(basses) / len(basses)
        verdict = ("PREDICTION TENUE" if dh - db >= 0.10 else "PREDICTION ECHOUEE") if ws is NEUFS else "( reference )"
        print(f"     apport moyen : haute prise {dh:+.3f} ( {len(hautes)} mondes ), basse prise {db:+.3f} ( {len(basses)} ), "
              f"difference {dh - db:+.3f}  {verdict}")
