"""CONTRE-EPREUVE de la clause « la patrouille prend pour cible la case d arrivee ».
Combien de fois, SANS aucune teleportation, la patrouille vise-t-elle une case donnee dans une fenetre de 5
decisions ? Si c est le meme taux, la clause ne detecte pas la triche : elle detecte le hasard du commandant."""
import ast, glob, json, os, re
from collections import Counter
H = "/mnt/data/hmt"


def champs(t):
    p = t.split("|"); return {p[i]: p[i + 1] for i in range(len(p) - 1) if re.fullmatch(r"[a-z_]+", p[i])}


# --- 1. les episodes Oracle SANS teleport ( ORACLE-P2-19-09, niveau 1 ) ---
n, viseCRETE, cibles = 0, 0, Counter()
for jf in sorted(glob.glob(f"{H}/runs/2026-09-1*/job.json") + glob.glob(f"{H}/runs/2026-09-20_*/job.json")):
    j = json.load(open(jf))
    if j.get("campagne") != "ORACLE-P2-19-09" or j.get("oracle_cmd") != 1: continue
    for d in sorted(glob.glob(os.path.dirname(jf) + "/g*/")):
        try: t = open(d + "serveur.rpt", encoding="utf-8", errors="ignore").read()
        except Exception: continue
        dec = []
        for m in re.findall(r'"CHACAL\|O\|decision\|([^"]*)"', t):
            c = champs(m); c["t"] = float(m.split("|")[0]); dec.append(c)
        f = [x for x in dec if x["t"] > 175][:5]
        if len(f) < 2: continue
        n += 1
        noms = {x.get("cible_patrouille") for x in f}
        cibles.update(noms)
        if "CRETE" in noms: viseCRETE += 1
print(f"episodes Oracle SANS teleport, fenetre de 5 decisions apres t=175 s : {n}")
print(f"   la patrouille vise CRETE dans {viseCRETE} / {n} = {viseCRETE / n:.3f} des episodes" if n else "aucun")
print("   cases visees, tous episodes confondus :", dict(cibles.most_common()))
