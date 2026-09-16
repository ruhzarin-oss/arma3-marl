import glob, os, re, json, statistics, random
from collections import defaultdict, Counter
from math import comb
random.seed(11)
CAMP = "PORTE-RENSEIGNEE-15-09"
RX_CH = re.compile(r"choix_ouverture\|([\d.]+)\|indice\|(\d+)\|gardes\|\[([-\d]+),([-\d]+)\]\|distances\|\[(\d+),(\d+)\]\|score\|[\d.]+\|renseignement\|(\d+)\|dgarde\|\[([-\d]+),([-\d]+)\]")
RX_FIN = re.compile(r"CHACAL\|FINI\|([A-Z_]+)\|([A-Z_]+)\|")
ep = []
for d in sorted(glob.glob("/mnt/data/hmt/runs/*/")):
    jf = d + "job.json"
    if not os.path.exists(jf): continue
    try: j = json.load(open(jf))
    except Exception: continue
    if j.get("campagne") != CAMP: continue
    v = str(j.get("version","")); g = (j.get("graines") or [None])[0]
    porte = "A" if "-A-" in v else "B"
    for gd in sorted(glob.glob(d + "g*/")):
        f = gd + "serveur.rpt"
        if not os.path.exists(f): continue
        txt = open(f,"rb").read().decode("latin-1","ignore")
        if "CHACAL|FINI|" not in txt or "observation_coupee" in txt: continue
        m = RX_CH.search(txt)
        det = re.search(r"\|detruits_scriptes\|(\d+)", txt)
        chg = re.search(r"\|charges\|(\d+)\|sur\|3", txt)
        fin = RX_FIN.search(txt)
        rj = gd + "resultat.json"; verd = "?"
        if os.path.exists(rj) and os.path.getsize(rj) > 0:
            try: verd = json.load(open(rj)).get("verdict","?")
            except Exception: pass
        ep.append(dict(monde=g, porte=porte, dossier=gd,
            gA=int(m.group(3)) if m else None, gB=int(m.group(4)) if m else None,
            rens=int(m.group(7)) if m else 0,
            det=int(det.group(1)) if det else None, chg=int(chg.group(1)) if chg else None,
            issue=fin.group(2) if fin else "?", verdict=verd,
            atteint=("issue|ATTEINT" in txt)))

def ic(v, n=4000):
    b = sorted(statistics.mean(random.choices(v, k=len(v))) for _ in range(n)); return b[int(.025*n)], b[int(.975*n)]

print(f"\n{'='*90}\n  APPROFONDISSEMENT — {len(ep)} episodes exploitables\n{'='*90}")

print("\n-- A. C2 version FORTE : par monde, le signe suit-il l observable ? --")
print("   ( dans chaque monde : quelle porte la crete a-t-elle le plus souvent designee comme la moins gardee,")
print("     et est-ce celle qui obtient le meilleur score ? )")
print("    monde | porte designee moins gardee | ecart reel B-A | signe conforme")
ok = 0; tot = 0
for g in sorted({e["monde"] for e in ep}):
    sub = [e for e in ep if e["monde"] == g]
    inf = [e for e in sub if e["gA"] is not None and e["gA"] != e["gB"]]
    if not inf: print(f"    {g:>5} | aucun episode informatif |"); continue
    votes = Counter("A" if e["gA"] < e["gB"] else "B" for e in inf)
    design = votes.most_common(1)[0][0]
    a = [e["det"] for e in sub if e["porte"]=="A" and e["det"] is not None]
    b = [e["det"] for e in sub if e["porte"]=="B" and e["det"] is not None]
    if not a or not b: continue
    d = statistics.mean(b) - statistics.mean(a)
    meilleure = "B" if d > 0 else ("A" if d < 0 else "=")
    conf = (design == meilleure); tot += 1; ok += conf
    print(f"    {g:>5} | {design}  ({votes[design]}/{len(inf)} episodes)        | {d:+.2f}  -> {meilleure:2s}    | {'OUI' if conf else 'non'}")
if tot:
    p = sum(comb(tot,i) for i in range(0, min(ok, tot-ok)+1)) * 2 / 2**tot
    print(f"    concordance : {ok}/{tot}  p={min(p,1):.3f}   ( le hasard donne 50 % )")

print("\n-- B. C2 restreint aux episodes ou la crete a vu le PLUS ( renseignement >= 2 ) --")
for seuil in (1, 2):
    moins = [e["det"] for e in ep if e["gA"] is not None and e["gA"]!=e["gB"] and e["rens"]>=seuil and e["det"] is not None and e["porte"]==("A" if e["gA"]<e["gB"] else "B")]
    plus  = [e["det"] for e in ep if e["gA"] is not None and e["gA"]!=e["gB"] and e["rens"]>=seuil and e["det"] is not None and e["porte"]!=("A" if e["gA"]<e["gB"] else "B")]
    if len(moins)>=3 and len(plus)>=3:
        d = statistics.mean(moins)-statistics.mean(plus)
        bo = sorted(statistics.mean(random.choices(moins,k=len(moins)))-statistics.mean(random.choices(plus,k=len(plus))) for _ in range(4000))
        print(f"   renseignement >= {seuil} : moins gardee n={len(moins):3d} ({statistics.mean(moins):.2f}) | plus gardee n={len(plus):3d} ({statistics.mean(plus):.2f}) | ecart {d:+.3f} IC [{bo[100]:+.3f} ; {bo[3900]:+.3f}]")

print("\n-- C. QUELLE TAILLE D EFFET CE PLAN POUVAIT-IL VOIR ? --")
par = defaultdict(lambda: defaultdict(list))
for e in ep:
    if e["det"] is not None: par[e["monde"]][e["porte"]].append(e["det"])
ecarts = [statistics.mean(v["B"]) - statistics.mean(v["A"]) for v in par.values() if v.get("A") and v.get("B")]
sd = statistics.stdev(ecarts)
print(f"   ecart-type des ecarts par monde : {sd:.3f} sur {len(ecarts)} mondes")
print(f"   demi-largeur de l IC a 95 %     : {1.96*sd/len(ecarts)**.5:.3f} objet")
print(f"   -> le plan ecartait tout effet vrai superieur a environ {1.96*sd/len(ecarts)**.5:.2f} objet. Le seuil annonce etait 0,30.")

print("\n-- D. DETRUITS CONTRE CHARGES : l ecart se creuse-t-il quelque part ? --")
for g in sorted(par):
    sub = [e for e in ep if e["monde"]==g]
    c = statistics.mean([e["chg"] for e in sub if e["chg"] is not None])
    d = statistics.mean([e["det"] for e in sub if e["det"] is not None])
    print(f"    monde {g:>2} : charges {c:.2f}  detruits {d:.2f}  perte {c-d:+.2f}")

print("\n-- E. LES 6 EPISODES REFUSES ET LES 2 OUVERTURES NON ATTEINTES --")
for e in ep:
    if e["verdict"] != "ACCEPTE" or not e["atteint"]:
        print(f"    {e['dossier'].split('/')[-3]}/{e['dossier'].split('/')[-2]}  monde {e['monde']} porte {e['porte']}  verdict={e['verdict']} atteint={e['atteint']} issue={e['issue']}")
print(f"\n   issues : {dict(Counter(e['issue'] for e in ep))}")
