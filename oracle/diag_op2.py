"""Les episodes sans ligne de decision : qui sont-ils, et que leur est-il arrive ? ( conformite seule )"""
import glob, json, os, re
H = "/mnt/data/hmt"
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != "ORACLE-P2-19-09": continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try:
            v = json.load(open(d + "resultat.json")).get("verdict")
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if v != "ACCEPTE": continue
        if re.search(r'"CHACAL\|E\|decision\|[^"]*point\|TRAVERSEE', t): continue
        fini = re.search(r'"CHACAL\|FINI\|([^"]*)"', t)
        ph2 = re.findall(r'"CHACAL\|PH\|2\|APPROCHE\|(debut|fin)\|([0-9.]+)\|?([A-Z_]*)', t)
        orc = re.findall(r'"CHACAL\|O\|decision\|[^"]*\|action\|([A-Z_]+)', t)
        print(f"   oracle {j['oracle_cmd']} option {j['traversee']} sit {j['situation']} monde {os.path.basename(d.rstrip('/'))} "
              f": FINI {fini.group(1)[:45] if fini else 'aucun'}")
        print(f"      phase 2 : {ph2} | ordres de l Oracle : {len(orc)}")
