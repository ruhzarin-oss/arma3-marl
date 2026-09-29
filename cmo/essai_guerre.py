"""Une minute d'endurance de guerre contre faux_cmo : périodes courtes, une « mort au combat » provoquée quand les deux
camps patrouillent la même zone. Ne prouve que la plomberie ; le vrai combat, seul CMO le fait."""
import json, os, sys, tempfile, threading, time
sys.path.insert(0, "cmo"); sys.path.insert(0, ".")
import cmo_labo as CL, endurance_guerre as EG, porte_cmo as P, porte_guerre_cmo as PG
from faux_cmo import FauxCMO
racine = tempfile.mkdtemp(prefix="essai_guerre_")
f = FauxCMO(racine); f.installer(); f.demarrer()
etat = os.path.join(racine, "etat"); CL.certifier("1.10.1900.20", {}, etat)
kw = dict(pont=f.pont, sortie=f.sortie, etat=etat, **P.RAPIDE)
g = EG.GuerreLongue(60 / 3600, {"ile": "Malden", "zones": PG.ZONES}, dossier=os.path.join(racine, "guerre"), labo_kw=kw,
                    periode_s=1.0, suivi_s=0.4, point_s=10.0, recettes={"Stratis": 4e8, "Malden": 2.5e8}, logs=racine)
def combat():
    time.sleep(20)
    k = f.lua("for _, u in pairs(FAUX.unites) do if u.side == 'Stratis' then return u.name end end return ''")
    if k: f.detruire(int(k.split("-")[1]))
threading.Thread(target=combat, daemon=True).start()
v = g.tourner()
f.arreter()
print(json.dumps({k: x for k, x in v.items() if k.startswith("E")}, ensure_ascii=False))
m = v["_mesures"]; print({k: m[k] for k in ("tours", "achats", "pertes", "morts_moteur", "morts_combat_estimees", "changements_de_zone", "payes", "depenses", "vitesse_mediane")})
