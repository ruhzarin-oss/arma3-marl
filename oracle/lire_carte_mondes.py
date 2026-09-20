"""L3 seule, avec l analyse de la carte reparee ( le lecteur cassait les guillemets avant literal_eval ).
Descriptif : aucune exclusion, aucun effet lu."""
import glob, json, os, re
from collections import defaultdict
H = "/mnt/data/hmt"
RX_FIN = re.compile(r'CHACAL\|PH\|2\|APPROCHE\|fin\|[0-9.]+\|([A-Z_]+)\|vivants\|(\d+)\|compromis\|(\d+)\|alarme\|(\d+)')
par = defaultdict(lambda: dict(carte=None, n_rte=None, compr=[], dpat=[]))
for jf in sorted(glob.glob(f"{H}/runs/2026-09-*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != "CALIBRATION-ADVERSAIRE-20-09" or j.get("oracle_cmd") != 1 or j.get("oracle_b") == 0: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        w = int(re.search(r"/g(\d+)", d).group(1))
        try:
            if json.load(open(d + "resultat.json")).get("verdict") != "ACCEPTE": continue
            t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        p = par[w]
        c = re.search(r'"CHACAL\|O\|carte\|[^"]*\|cases_routieres\|(\d+)\|detail\|(\[.*?\])"', t)
        if c and p["carte"] is None:
            p["n_rte"] = int(c.group(1))
            p["carte"] = re.findall(r'\[\s*""?([A-Z_]+)""?\s*,\s*(\d)\s*,\s*(-?\d+)\s*\]', c.group(2))
        m = RX_FIN.search(t)
        if m: p["compr"].append(int(m.group(3)))
        for x in re.findall(r'patrouille_a\|(-?\d+)', t):
            v = int(x)
            if v >= 0: p["dpat"].append(v)
print(f"{'monde':>5} {'cases_rte':>10} {'compr':>7} {'dpat_min':>9}  cases HORS route ( nom : distance a la route la plus proche )")
for w in sorted(par):
    p = par[w]
    hors = [f"{n}:{d}" for n, ok, d in (p["carte"] or []) if ok == "0"]
    print(f"{w:>5} {str(p['n_rte']):>10} {(sum(p['compr']) / len(p['compr']) if p['compr'] else -1):>7.2f} "
          f"{(min(p['dpat']) if p['dpat'] else -1):>9}  {', '.join(hors) if hors else 'aucune'}")
