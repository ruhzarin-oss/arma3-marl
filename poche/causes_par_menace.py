import glob, json, os, re
from collections import Counter, defaultdict
H = "/mnt/data/hmt"
RX_C = re.compile(r'"CHACAL\|E\|compromis\|([0-9.]+)\|cause\|([A-Z_]+)\|phase\|2\|latence_oracle\|(-?[0-9.]+)')
RX_P = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)')
n = Counter(); c = defaultdict(Counter); lat = Counter()
for jf in glob.glob(f"{H}/runs/2026-09-*/job.json"):
    try: j = json.load(open(jf))
    except Exception: continue
    if not j.get("menace_p2") or int(j.get("depart", 0)) != 2 or int(j.get("arret", 0)) != 2 or int(j.get("oracle_ctrl") or 0) != 0: continue
    for d in glob.glob(os.path.dirname(jf) + "/g*/"):
        try:
            if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if not RX_P.search(t): continue
        k = (int(j["menace_p2"]), int(j.get("oracle_cmd") or 0)); n[k] += 1
        m = RX_C.search(t)
        if m:
            c[k][m.group(2)] += 1
            if m.group(2) == "ENNEMI_VU_EN_COMBAT": lat["alarme deja donnee" if float(m.group(3)) >= 0 else "SANS alarme"] += 1
TY = {1: "patrouille", 2: "poste", 3: "les deux pres", 4: "patrouille pres", 5: "poste pres"}
print(f"{'menace':<16} {'oracle':>6} {'n':>5}  {'vu en combat':>13} {'touche':>8} {'feu proche':>11}")
for k in sorted(n):
    if n[k] < 20: continue
    print(f"{TY[k[0]]:<16} {k[1]:>6} {n[k]:>5}  {c[k]['ENNEMI_VU_EN_COMBAT'] / n[k]:>13.1%} {c[k]['COUP_RECU'] / n[k]:>8.1%} {c[k]['FEU_PROCHE'] / n[k]:>11.1%}")
print("\n« vu en combat » :", dict(lat))
