"""Etape 0 de la poche : QUI compromet en phase 2, et QUAND par rapport a la decision. Zero episode."""
import glob, json, os, re
from collections import Counter, defaultdict
H = "/mnt/data/hmt"
RX_C = re.compile(r'"CHACAL\|E\|compromis\|([0-9.]+)\|cause\|([A-Z_]+)\|phase\|(\d+)')
RX_D = re.compile(r'"CHACAL\|E\|decision\|([0-9.]+)\|phase\|2\|point\|TRAVERSEE')
RX_F = re.compile(r'"CHACAL\|E\|fenetre\|([0-9.]+)\|([A-Z_]+)\|attente\|(\d+)')
RX_P = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)')
RX_P0 = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|debut\|([0-9.]+)')
tab = defaultdict(Counter); quand = defaultdict(list); n = Counter(); attentes = defaultdict(list); duree = defaultdict(list)
for jf in glob.glob(f"{H}/runs/2026-09-*/job.json"):
    try: j = json.load(open(jf))
    except Exception: continue
    if not j.get("menace_p2") or int(j.get("depart", 0)) != 2 or int(j.get("arret", 0)) != 2 or int(j.get("oracle_ctrl") or 0) != 0: continue
    o = int(j.get("traversee") or 0)
    if o not in (1, 2): continue
    for d in glob.glob(os.path.dirname(jf) + "/g*/"):
        try:
            if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        p = RX_P.search(t)
        if not p: continue
        n[o] += 1
        dec = RX_D.search(t); fen = RX_F.search(t); p0 = RX_P0.search(t)
        if fen: attentes[o].append(int(fen.group(3)))
        if p0: duree[o].append(float(p.group(1)) - float(p0.group(1)))
        c = [m for m in RX_C.findall(t) if m[2] == "2"]
        if not c or p.group(4) != "1": tab[o]["pas compromis"] += 1; continue
        tc, cause = float(c[0][0]), c[0][1]
        moment = "AVANT la decision" if (not dec or tc < float(dec.group(1))) else "apres la decision"
        tab[o][f"{cause} | {moment}"] += 1
        if dec and tc >= float(dec.group(1)): quand[(o, cause)].append(tc - float(dec.group(1)))
import numpy as np
for o in (1, 2):
    print(f"\n=== option {o} ( {'traverser' if o == 1 else 'attendre'} ) : {n[o]} episodes ; attente mediane {np.median(attentes[o]) if attentes[o] else 0:.0f} s ; duree mediane de la phase 2 {np.median(duree[o]) if duree[o] else 0:.0f} s")
    for k, v in tab[o].most_common(): print(f"   {k:<44} {v:>5}  ( {v / n[o]:.1%} )")
print("\n=== delai decision -> compromission ( s ), mediane [ quartiles ] ===")
for (o, cause), v in sorted(quand.items()):
    if len(v) >= 5: print(f"   option {o} {cause:<22} n {len(v):>4}  {np.median(v):6.0f}  [ {np.percentile(v, 25):.0f} ; {np.percentile(v, 75):.0f} ]")
