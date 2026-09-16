import glob, os, re, json, statistics, random
from collections import defaultdict, Counter

CAMP = "PORTE-RENSEIGNEE-15-09"
RX_CH = re.compile(r"choix_ouverture\|([\d.]+)\|indice\|(\d+)\|gardes\|\[([-\d]+),([-\d]+)\]\|distances\|\[(\d+),(\d+)\]\|score\|[\d.]+\|renseignement\|(\d+)\|dgarde\|\[([-\d]+),([-\d]+)\]")
RX_FIN = re.compile(r"CHACAL\|FINI\|([A-Z_]+)\|([A-Z_]+)\|")
RX_DET = re.compile(r"\|detruits_scriptes\|(\d+)")
RX_CHG = re.compile(r"\|charges\|(\d+)\|sur\|(\d+)")
RX_AZ  = re.compile(r"couture_azimut\|[\d.]+\|mode\|(\d+)\|decideur\|([A-Z]+)\|candidats\|\d+\|choisi\|(\d+)")

ep = []
for d in sorted(glob.glob("/mnt/data/hmt/runs/*/")):
    jf = d + "job.json"
    if not os.path.exists(jf): continue
    try: j = json.load(open(jf))
    except Exception: continue
    if j.get("campagne") != CAMP: continue
    v = str(j.get("version", "")); g = (j.get("graines") or [None])[0]
    porte = "A" if "-A-" in v else ("B" if "-B-" in v else "?")
    for gd in sorted(glob.glob(d + "g*/")):
        f = gd + "serveur.rpt"
        if not os.path.exists(f): continue
        txt = open(f, "rb").read().decode("latin-1", "ignore")
        if "CHACAL|FINI|" not in txt: continue
        rj = gd + "resultat.json"
        verdict = "?"
        if os.path.exists(rj) and os.path.getsize(rj) > 0:
            try: verdict = json.load(open(rj)).get("verdict", "?")
            except Exception: pass
        m, fin, det, chg, az = RX_CH.search(txt), RX_FIN.search(txt), RX_DET.search(txt), RX_CHG.search(txt), RX_AZ.search(txt)
        ep.append(dict(
            monde=g, porte=porte, dossier=os.path.basename(gd.rstrip('/')), verdict=verdict,
            coupee=("observation_coupee" in txt),
            rens=int(m.group(7)) if m else None,
            gA=int(m.group(3)) if m else None, gB=int(m.group(4)) if m else None,
            dgA=int(m.group(8)) if m else None, dgB=int(m.group(9)) if m else None,
            issue=fin.group(2) if fin else "?",
            detruits=int(det.group(1)) if det else None,
            charges=int(chg.group(1)) if chg else None,
            az_joue=int(az.group(3)) if az else None, az_mode=az.group(2) if az else "?",
            atteint=("issue|ATTEINT" in txt)))

print(f"\n{'='*92}\n  PORTE-RENSEIGNEE-15-09  —  {len(ep)} episodes termines sur 160\n{'='*92}")

# ---------- 0. CONTROLE POSITIF, AVANT TOUT TAUX ----------
coupes = [e for e in ep if e["coupee"]]
bons   = [e for e in ep if not e["coupee"]]
print(f"\n-- 0. CONTROLE POSITIF ( a lire en premier ) --")
print(f"   episodes avec la phase 3 COUPEE ( obs=0, nuls, ecartes ) : {len(coupes)}")
print(f"   episodes exploitables                                    : {len(bons)}")
if not bons:
    print("\n   AUCUN episode exploitable. L instrument n a rien produit : on ne conclut RIEN.")
    raise SystemExit
nz = [e for e in bons if (e["rens"] or 0) > 0]
diff = [e for e in bons if e["gA"] is not None and e["gA"] != e["gB"]]
print(f"   renseignement > 0                                        : {len(nz)}/{len(bons)} = {100*len(nz)/len(bons):.0f} %")
print(f"   gardes DIFFERENTS entre les deux ouvertures              : {len(diff)}/{len(bons)} = {100*len(diff)/len(bons):.0f} %")
print(f"   distribution du renseignement : {dict(sorted(Counter(e['rens'] for e in bons).items(), key=lambda x: (x[0] is None, x[0])))}")
if len(nz) < 0.15 * len(bons):
    print("\n   ! L OBSERVABLE EST QUASI DEGENERE. C est une panne d instrument, pas un resultat.")
print(f"   azimut joue conforme au mode IMPOSE : {sum(1 for e in bons if e['az_mode']=='IMPOSE')}/{len(bons)}")
print(f"   ouverture demandee ATTEINTE          : {sum(1 for e in bons if e['atteint'])}/{len(bons)}")

# ---------- 1. C1 : ecart apparie par monde ----------
def apparie(sortie, titre):
    par = defaultdict(lambda: defaultdict(list))
    for e in bons:
        if e[sortie] is None: continue
        par[e["monde"]][e["porte"]].append(e[sortie])
    print(f"\n-- {titre} --")
    print("    monde |        porte A |        porte B |   ecart B-A")
    ecarts = []
    for g in sorted(par):
        a, b = par[g].get("A", []), par[g].get("B", [])
        if not a or not b:
            print(f"    {str(g):>5} | {('%.2f (n=%d)'%(statistics.mean(a),len(a))) if a else '-':>14} | {('%.2f (n=%d)'%(statistics.mean(b),len(b))) if b else '-':>14} |")
            continue
        d = statistics.mean(b) - statistics.mean(a); ecarts.append(d)
        print(f"    {str(g):>5} | {statistics.mean(a):8.2f} (n={len(a):2d}) | {statistics.mean(b):8.2f} (n={len(b):2d}) | {d:+10.2f}")
    if len(ecarts) >= 2:
        m = statistics.mean(ecarts)
        boot = sorted(statistics.mean(random.choices(ecarts, k=len(ecarts))) for _ in range(4000))
        pos = sum(1 for d in ecarts if d > 0)
        from math import comb
        k = min(pos, len(ecarts) - pos)
        p = sum(comb(len(ecarts), i) for i in range(0, k + 1)) * 2 / 2**len(ecarts)
        print(f"    ECART APPARIE sur {len(ecarts)} mondes : {m:+.3f} | IC 95 % [{boot[100]:+.3f} ; {boot[3900]:+.3f}] | signes {pos}/{len(ecarts)} p={min(p,1):.3f}")
    return ecarts

random.seed(7)
apparie("detruits", "1. C1 — DETRUITS 0..3   ( SORTIE PRIMAIRE ENREGISTREE D AVANCE )")
apparie("charges",  "2. C1 bis — CHARGES 0..3   ( lecture secondaire )")

# ---------- 2. C2 : le signe suit-il l observable ? ----------
print("\n-- 3. C2 — LA MEILLEURE PORTE SUIT-ELLE L OBSERVABLE ? --")
print("   Pour chaque episode informatif, la porte jouee est-elle la MOINS gardee ?")
moins, plus = [], []
for e in bons:
    if e["gA"] is None or e["gA"] == e["gB"] or e["detruits"] is None: continue
    moins_gardee = "A" if e["gA"] < e["gB"] else "B"
    (moins if e["porte"] == moins_gardee else plus).append(e["detruits"])
if len(moins) >= 3 and len(plus) >= 3:
    print(f"   porte la MOINS gardee jouee : n={len(moins):3d}  detruits moyen {statistics.mean(moins):.2f}")
    print(f"   porte la PLUS  gardee jouee : n={len(plus):3d}  detruits moyen {statistics.mean(plus):.2f}")
    d = statistics.mean(moins) - statistics.mean(plus)
    boot = sorted(statistics.mean(random.choices(moins, k=len(moins))) - statistics.mean(random.choices(plus, k=len(plus))) for _ in range(4000))
    print(f"   ECART {d:+.3f}  IC 95 % [{boot[100]:+.3f} ; {boot[3900]:+.3f}]")
    print("   ( C2 tient si cet ecart est POSITIF et que l IC exclut zero )")
else:
    print(f"   pas encore assez d episodes informatifs : moins_gardee n={len(moins)}, plus_gardee n={len(plus)}")

# ---------- 3. par ou l echec passe ----------
print("\n-- 4. PAR OU L ECHEC PASSE --")
for k, v in Counter(e["issue"] for e in bons).most_common(): print(f"   {v:4d}  {k}")
print(f"\n   verdicts du lecteur : {dict(Counter(e['verdict'] for e in ep))}")
