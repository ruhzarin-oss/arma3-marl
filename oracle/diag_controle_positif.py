import glob, json, os, re
H = "/mnt/data/hmt"


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


lignes = []
for jf in sorted(glob.glob(f"{H}/runs/2026-09-20_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != "CONTROLES-ORACLE-20-09" or j.get("oracle_ctrl") != 1: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try:
            if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        w = int(re.search(r"/g(\d+)", d).group(1))
        pos = re.search(r'"CHACAL\|O\|ctrl\|positif\|([^"]*)"', t)
        c = champs(pos.group(1)) if pos else {}
        fin = re.search(r'CHACAL\|PH\|2\|APPROCHE\|fin\|([0-9.]+)\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)', t)
        # la patrouille, vue par le journal de l Oracle : sa distance a sa cible au fil du temps
        dpat = [champs(m).get("patrouille_a") for m in re.findall(r'"CHACAL\|O\|decision\|([^"]*)"', t)]
        vues = len(re.findall(r'CHACAL\|E\|situation\|[^"]*menace_mobile_vue\|1', t))
        lignes.append((w, j["situation"], c.get("patrouille_a"), fin.group(2) if fin else "?",
                       fin.group(4) if fin else "?", fin.group(3) if fin else "?", vues, dpat[:4]))
print(f"{'monde':>5} {'sit':>3} {'pose_a':>7} {'issue':>16} {'compr':>5} {'vivants':>7} {'vues':>4}  distances patrouille")
for l in sorted(lignes): print(f"{l[0]:>5} {l[1]:>3} {str(l[2]):>7} {l[3]:>16} {l[4]:>5} {l[5]:>7} {l[6]:>4}  {l[7]}")
