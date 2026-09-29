"""Une minute d'endurance de la guerre des blocs contre faux_cmo ( plomberie seulement : le faux n'écrit pas de journal
de messages, donc B2, B5 et B7 ne se jugent que dans le vrai CMO )."""
import json, os, sys, tempfile, threading, time
sys.path.insert(0, "cmo")
import cmo_labo as CL, endurance_blocs as EB, porte_cmo as P, porte_blocs as PB
from faux_cmo import FauxCMO
racine = tempfile.mkdtemp(prefix="essai_blocs_")
f = FauxCMO(racine, camps=PB.CAMPS); f.installer(); f.demarrer()
etat = os.path.join(racine, "etat"); CL.certifier("1.10.1900.20", {}, etat)
e = EB.EnduranceBlocs(60 / 3600, dossier=os.path.join(racine, "blocs"), periode_s=0.5, logs=racine,
                      labo_kw=dict(pont=f.pont, sortie=f.sortie, etat=etat, **P.RAPIDE),
                      catalogue={"Poland": [PB.F16], "United States": [dict(PB.F16, dbid=3497, famille="F-35", prix_m=100)],
                                 "Russia [1992-]": [PB.SU35]}, guerre_kw={"masse": 4})
def combat():
    time.sleep(15)
    for _ in range(3):
        k = f.lua("for _, u in pairs(FAUX.unites) do if string.match(u.name, '^HMT%-1') then return u.name end end return ''")
        if k: f.detruire(int(k.split("-")[1]))
        time.sleep(5)
threading.Thread(target=combat, daemon=True).start()
v = e.tourner(); f.arreter()
print(json.dumps({k: x for k, x in v.items() if k.startswith("B")}, ensure_ascii=False))
for m in v["_mesures"]["manches"]:
    print({k: m[k] for k in ("manche", "tours", "victoire", "score", "achats", "pertes_comptees", "drapeaux_pris")})
print("erreurs", v["_mesures"]["erreurs"], "plantage", v["_mesures"]["plantage"])
