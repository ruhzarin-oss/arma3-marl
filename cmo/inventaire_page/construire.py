"""Assemble la page de l'inventaire : les données de cmo/inventaire.py ( inventaire_2026.json ), compactées dans la page."""
import json, os
from noms_fr import NOMS_FR
ICI = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.environ.get("INVENTAIRE", "/mnt/data/hmt/etat/cmo_db/inventaire_2026.json")))
GENRES = ["avion", "navire", "sous-marin", "unité terrestre", "installation", "satellite"]
pays = [dict(p, fr=NOMS_FR.get(p["pays"], p["pays"])) for p in d["pays"]]
indice = {p["pays"]: i for i, p in enumerate(pays)}
chaines, ic = [], {}
def c(t):
    if t not in ic: ic[t] = len(chaines); chaines.append(t)
    return ic[t]
plates = [[x["dbid"], GENRES.index(x["genre"]), x["nom"], indice[x["pays"]], c(x["categorie"]), c(x["type"]), x["debut"], x["fin"], c(x["service"])]
          for x in d["plateformes"]]
manquants = sorted({p["pays"] for p in pays} - set(NOMS_FR))
donnees = json.dumps({"base": d["base"], "pays": pays, "chaines": chaines, "plates": plates}, ensure_ascii=False, separators=(",", ":"))
page = open(os.path.join(ICI, "gabarit.html"), encoding="utf-8").read().replace("__DONNEES__", donnees.replace("</", "<\\/"))
open(os.path.join(ICI, "inventaire-db3000-2026.html"), "w", encoding="utf-8").write(page)
print(f"{len(page) / 1e6:.2f} Mo, {len(pays)} pays, {len(plates)} matériels, noms sans traduction : {manquants}")
