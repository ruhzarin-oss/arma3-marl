"""PORTES G2 ET G3 DE L ARCHIPEL ( plans/plan-archipel.md, phase D ; ecrites avant la mesure ).

G2 ISOLEMENT : l archipel, pont FERME, donne six iles identiques au bit aux six iles simulees seules ( meme graine,
   meme echelle, memes domaines ), jour apres jour. Controle positif : un milliardieme de drachme ajoute dans UNE ile
   est vu dans cette ile, et dans aucune autre.
G3 DETERMINISME : six processus = sequentiel, au bit ; deux passages = identiques ; panne + reprise depuis
   l instantane = sans panne.
   ( Le controle « inverser deux messages d un meme pas change le resultat » demande des messages : phase E. )

   python -m monde.porte_archipel --jours 3 --echelle 2"""
import argparse, os, shutil, sys, time
from . import tests as T, config as C
from .porte_domaines import empreinte
from .archipel import Archipel, creer_ile, DOSSIER

ILES = C.ILES_ARCHIPEL


def seules(graine, echelle, jours):
    serie = {}
    for n in ILES:
        w = creer_ile(n, graine, echelle); serie[n] = []
        for _ in range(jours): T.jours(w, 1); serie[n].append(empreinte(w))
    return serie


def archipel(graine, echelle, jours, parallele=True, perturber=None):
    arc = Archipel(graine=graine, echelle=echelle, parallele=parallele)
    serie = {n: [] for n in ILES}
    for j in range(jours):
        if perturber and j == 1: arc.perturber(perturber)
        arc.jours(1)
        for n, e in arc.empreintes().items(): serie[n].append(e)
    arc.fermer()
    return serie


def ecarts(a, b):
    """Par ile : le premier jour ou les empreintes different, et combien d empreintes ( ou None si identiques )."""
    out = {}
    for n in ILES:
        out[n] = None
        for j, (x, y) in enumerate(zip(a[n], b[n])):
            d = [k for k in x if x.get(k) != y.get(k)]
            if d: out[n] = (j + 1, len(d), d[:4]); break
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jours", type=int, default=3)
    p.add_argument("--echelle", type=float, default=2.0)
    p.add_argument("--graine", type=int, default=C.GRAINE)
    x = p.parse_args()
    g, e, J = x.graine, x.echelle, x.jours
    ok, t0 = {}, time.time()
    ref = seules(g, e, J)
    print(f"iles seules : {time.time() - t0:.0f} s", flush=True)
    t0 = time.time(); par = archipel(g, e, J); print(f"archipel parallele : {time.time() - t0:.0f} s", flush=True)
    d = ecarts(ref, par)
    ok["G2 isolement : archipel ferme = iles seules"] = all(v is None for v in d.values())
    if not ok["G2 isolement : archipel ferme = iles seules"]: print("   ecarts :", {k: v for k, v in d.items() if v})
    pert = archipel(g, e, J, perturber="Malden")
    dp = ecarts(par, pert)
    ok["G2 controle positif : la perturbation de Malden vue a Malden seulement"] = (
        dp["Malden"] is not None and all(v is None for k, v in dp.items() if k != "Malden"))
    t0 = time.time(); seq = archipel(g, e, J, parallele=False); print(f"archipel sequentiel : {time.time() - t0:.0f} s", flush=True)
    ok["G3 parallele = sequentiel"] = all(v is None for v in ecarts(par, seq).values())
    bis = archipel(g, e, J)
    ok["G3 deux passages identiques"] = all(v is None for v in ecarts(par, bis).values())
    # panne + reprise : 1 jour, instantane, on ferme tout ; on repart de l instantane pour les jours restants
    dossier = os.path.join(DOSSIER, "porte_reprise")
    shutil.rmtree(dossier, ignore_errors=True)
    arc = Archipel(graine=g, echelle=e); arc.jours(1); arc.instantane(dossier); arc.fermer()
    arc = Archipel(graine=g, echelle=e, reprise=dossier); arc.jours(J - 1); fin = arc.empreintes(); arc.fermer()
    ok["G3 panne + reprise = sans panne"] = all(fin[n] == par[n][-1] for n in ILES)
    for k, v in ok.items(): print(f"{'PASSE ' if v else 'ECHOUE'} {k}")
    print(f"   ( perturbation : Malden differe au jour {dp['Malden'][0] if dp['Malden'] else '-'} ; "
          f"{J} jours, {e * 500:.0f} habitants par ile )")
    passe = all(ok.values())
    print(f"PORTES G2 ET G3 : {'FRANCHIES' if passe else 'ECHOUEES'}")
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
