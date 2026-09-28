"""Une minute d'endurance contre faux_cmo : intervalles courts, une mort provoquée, une pause de 4 s."""
import json, os, sys, tempfile, threading, time
sys.path.insert(0, "cmo")
import cmo_labo as CL, endurance as E, porte_cmo as P
from faux_cmo import FauxCMO
racine = tempfile.mkdtemp(prefix="essai_nuit_")
f = FauxCMO(racine); f.installer(); f.demarrer()
etat = os.path.join(racine, "etat"); CL.certifier("1.10.1900.20", {}, etat)
kw = dict(pont=f.pont, sortie=f.sortie, etat=etat, **P.RAPIDE)
n = E.Nuit(40 / 3600, labo_kw=kw, intervalles=(0.3, 1.0, 5.0, 3.0), dossier=os.path.join(racine, "nuit"), logs=racine)
def perturber():
    time.sleep(8); f.detruire(101)
    time.sleep(8); f.pause(); time.sleep(4); f.reprendre()
threading.Thread(target=perturber, daemon=True).start()
r = n.tourner()
f.arreter()
print(json.dumps({k: r[k] for k in ("canaris_ok", "erreurs", "rtt_ms", "morts", "morts_doubles", "pannes_s")}, ensure_ascii=False))
evs = [json.loads(l)["quoi"] for l in open(r["journal"])]
print({q: evs.count(q) for q in sorted(set(evs))})
