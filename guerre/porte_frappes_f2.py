"""Rejugement de F2 de la porte des frappes ( HMT-192, 1b ). Premier rejugement ( graine 1933 ) : REFUSE, 0,500 pile sur
les jours 4 a 6 pour « plus de 50 % » ( la reparation finit dans la fenetre ). Deuxieme rejugement, critere ecrit avant la
mesure ( Plane, 02/10 22 h 05 ), place apres une sonde hors porte ( graine 7 ) : Malden, graine neuve 1934, 200 t d acier
au stock du site fonderie01 dans les DEUX bras ( un montage d essai identique ). A degats 1, la production des 5 premiers
jours <= 5 % du jumeau, jumeau positif ; a reparation raccourcie ( 2 journees de poste ), jours 7 a 10 >= 80 % du jumeau
sur les memes jours, jumeau positif.

python -m guerre.porte_frappes_f2"""
import json
import pickle
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d10_industrie as IN
from . import frappes as FR, objectifs as OB

SORTIE = "/mnt/data/hmt/arsenal/porte_frappes_f2_bis.json"
PROD = {}
_ORIG = IN._produire_bien


def _compter(p, D_, s, b, q):
    k = (id(p.w), s.entreprise.lieu.id); PROD[k] = PROD.get(k, 0.0) + q
    return _ORIG(p, D_, s, b, q)


IN._produire_bien = _compter


def approvisionner(w, lieu="fonderie01", tonnes=200.0):
    """Le montage d essai : de l acier au stock du site, par le grand livre ( une entree importee, motif du domaine 10 )."""
    p = w.pays; D_ = IN._dom(p)
    s = next(x for x in D_.sites if x.entreprise.lieu.id == lieu)
    return p.socle.livre.importer(s.stock, p.socle.catalogue.id("acier"), tonnes, IN.MOTIF_INTRANT)


def prod(w): return PROD.get((id(w), "fonderie01"), 0.0)


def main():
    t0 = time.time()
    print("PORTE DES FRAPPES, deuxieme rejugement de F2 : Malden 1934, 200 t d acier dans les deux bras", flush=True)
    w0 = AR.creer_ile("Malden", 1934, 20)
    approvisionner(w0)
    octets = pickle.dumps(w0, protocol=4)
    f = next(o for o in OB.objectifs_carte("malden") if o["id"] == "fonderie01")
    tout = {c["i"]: 1.0 for c in f["composants"]}
    wa, wt = pickle.loads(octets), pickle.loads(octets)
    base = {id(x): prod(x) for x in (wa, wt)}
    FR.frapper(wa, f, tout)
    for _ in range(5): T.jours(wa, 1); T.jours(wt, 1)
    pa, pt = prod(wa) - base[id(wa)], prod(wt) - base[id(wt)]
    sauve = FR.DUREE_REPARATION_J["fonderie"]; FR.DUREE_REPARATION_J["fonderie"] = 2.0
    try:
        ws, wt2 = pickle.loads(octets), pickle.loads(octets)
        base.update({id(x): prod(x) for x in (ws, wt2)})
        FR.frapper(ws, f, tout)
    finally:
        FR.DUREE_REPARATION_J["fonderie"] = sauve
    for _ in range(6): T.jours(ws, 1); T.jours(wt2, 1)
    s6, t6 = prod(ws), prod(wt2)
    for _ in range(4): T.jours(ws, 1); T.jours(wt2, 1)
    s710, t710 = prod(ws) - s6, prod(wt2) - t6
    F2 = bool(pt > 0 and pa <= 0.05 * pt and t710 > 0 and s710 >= 0.8 * t710)
    R = {"ok": F2, "frappee_5j": float(pa), "jumeau_5j": float(pt), "reparee_j7_10": float(s710),
         "jumeau_j7_10": float(t710), "rapport_j7_10": float(s710 / t710) if t710 else None, "duree_s": round(time.time() - t0)}
    print(f"  F2 fonderie : {'OUI' if F2 else 'NON'} {R}", flush=True)
    verdict = "FRANCHIE" if F2 else "REFUSEE"
    R["verdict"] = verdict
    json.dump(R, open(SORTIE, "w"), indent=1)
    print(f"PORTE DES FRAPPES ( F2 rejuge ; F0, F1, F3 a F6 acquis ) : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_FRAPPES_F2", flush=True)
    return 0 if F2 else 1


if __name__ == "__main__":
    sys.exit(main())
