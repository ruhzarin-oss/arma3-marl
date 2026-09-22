"""L APPRENTI MARCHAND : un petit reseau qui decide le commerce entre marches, la ou une regle decidait.

Le monde est son ecole : il joue des mondes entiers ( population, production, maladies, gouvernement ), avec une
SECHERESSE regionale tiree de la graine. Sa note est ce que le pays y gagne : des menages nourris et de l argent.
Il est jugé contre la regle d origine ( `Monde.commerce_regle` ) sur des mondes JAMAIS VUS pendant l apprentissage.

   python -m monde.apprenti --mesure          # ce que font la regle et ses temoins ( avant d apprendre )
   python -m monde.apprenti --apprendre       # apprentissage par strategie d evolution, puis examen
La porte et le falsificateur sont ecrits d avance dans plans/porte-apprenti-marchand.md."""
import argparse, json, math, os, time
from multiprocessing import Pool
import numpy as np
from . import config as C, monde as W

N_CACHE = 10
ENTREES = ("prix_ici", "prix_la_bas", "ecart", "cout_route", "surplus", "stock_cible_la_bas", "manque_la_bas",
           "prix_carburant", "heure", "biais")
N_ENTREES = len(ENTREES)
N_POIDS = N_ENTREES * N_CACHE + N_CACHE + N_CACHE * 2 + 2


# --------------------------------------------------------------------------- le monde d examen
def monde_epreuve(graine, jours_max=20):
    """Un monde avec sa secheresse. VERSION 2 du 22/09 : la premiere epreuve ( recolte a 20-45 %, 7 jours ) ne separait
    pas ses temoins - regle 50,22 / aucun commerce 49,73 / commerce aveugle 50,39, moins d un point d ecart, faim au
    plancher. Son propre falsificateur l a annulee. Ici la region touchee perd presque toute sa recolte pendant douze
    jours : la nourriture existe ailleurs, et c est au marchand de l y amener."""
    w = W.Monde(graine=graine)
    rng = np.random.default_rng(graine)
    touchees = list(rng.choice(sorted(w.marches), size=2, replace=False))    # DEUX capitales sur trois
    lieux = {l.id for l in w.carte.lieux.values() if getattr(l.marche, "id", None) in touchees}
    w.chocs = [{"debut": int(rng.integers(2, 5)), "jours": 12, "lieux": lieux, "facteur": float(rng.uniform(0.02, 0.12))}]
    return w


def jouer(graine, politique=None, jours=20):
    """Joue un monde entier et rend sa note. La note est ECRITE D AVANCE : des menages nourris d abord, de l argent ensuite."""
    w = monde_epreuve(graine)
    if politique is not None: w.marchand = politique
    argent0 = w.argent_total()
    faim, morts0 = 0.0, sum(1 for h in w.habitants if not h.vivant)
    for j in range(jours):
        for _ in range(C.PAS_PAR_JOUR): w.pas_suivant()
        faim += w.stats_jour.get("menages_sans_nourriture", 0) / len(w.menages)
    d_arg, d_b = w.verifier_conservation()
    morts = sum(1 for h in w.habitants if not h.vivant) - morts0
    # la note, version 2 : le pays est juge sur ses HABITANTS. L argent avait ete retire apres la mesure des temoins du
    # 22/09 : il vient des exportations au port et ne depend presque pas du marchand - il noyait le signal.
    return {"faim": faim / jours, "argent": w.argent_total() - argent0, "morts": morts,
            "conservation": max(abs(d_arg), max(abs(v) for v in d_b.values())),
            "note": -100.0 * (faim / jours) - 5.0 * morts}


# --------------------------------------------------------------------------- les temoins
def marchand_muet(w, h): pass


def marchand_aveugle(w, h):
    """Il expedie toujours vers le marche le plus cher, sans regarder ce que coute la route : le temoin du bas."""
    for a in w.marches.values():
        for b in C.BIENS_COMMERCE:
            surplus = a.stocks[b] - w.reserve_marche(a, b)
            if surplus < 10: continue
            cible = max((x for x in w.marches.values() if x is not a), key=lambda x: x.prix[b])
            q = min(surplus, C.CAPACITE_CAMION)
            if w.lancer_convoi(a.lieu, cible.lieu, {b: q}, a, "commerce", a): a.stocks[b] -= q


# --------------------------------------------------------------------------- le reseau
class Politique:
    """Un perceptron a une couche cachee. Pour chaque ( marche de depart, bien, marche d arrivee ) il donne une envie
    d expedier et une part du camion. Il expedie vers la destination la plus desiree, si l envie est positive."""

    def __init__(self, theta):
        self.theta = np.asarray(theta, dtype=np.float64)
        i = 0
        self.W1 = self.theta[i:i + N_ENTREES * N_CACHE].reshape(N_CACHE, N_ENTREES); i += N_ENTREES * N_CACHE
        self.b1 = self.theta[i:i + N_CACHE]; i += N_CACHE
        self.W2 = self.theta[i:i + N_CACHE * 2].reshape(2, N_CACHE); i += N_CACHE * 2
        self.b2 = self.theta[i:i + 2]

    def sortie(self, X):
        z = np.tanh(X @ self.W1.T + self.b1)
        y = z @ self.W2.T + self.b2
        return y[:, 0], 1.0 / (1.0 + np.exp(-y[:, 1]))

    def __call__(self, w, h):
        marches = list(w.marches.values())
        for a in marches:
            for b in C.BIENS_COMMERCE:
                surplus = a.stocks[b] - w.reserve_marche(a, b)
                if surplus < 10: continue
                cibles = [x for x in marches if x is not a]
                X = np.array([caracteristiques(w, a, x, b, surplus, h) for x in cibles])
                envie, part = self.sortie(X)
                k = int(np.argmax(envie))
                if envie[k] <= 0: continue
                q = min(surplus, C.CAPACITE_CAMION * float(part[k]))
                if q < 10: continue
                if w.lancer_convoi(a.lieu, cibles[k].lieu, {b: q}, a, "commerce", a): a.stocks[b] -= q


def caracteristiques(w, a, x, b, surplus, h):
    """Ce que le marchand VOIT : des prix, une route, un stock - jamais l avenir, jamais la verite du monde."""
    pm = C.PRIX_MONDE[b]
    km = w.carte.km_route(a.lieu, x.lieu)
    cout_u = 2 * km * C.CARBURANT_PAR_KM * a.prix["carburant"] / C.CAPACITE_CAMION
    garde = max(1.0, w.reserve_marche(x, b))
    return [a.prix[b] / pm, x.prix[b] / pm, (x.prix[b] - a.prix[b]) / pm, cout_u / pm,
            surplus / C.CAPACITE_CAMION, min(3.0, x.stocks[b] / garde), max(0.0, 1.0 - x.stocks[b] / garde),
            a.prix["carburant"] / C.PRIX_MONDE["carburant"], (h - 7) / 8.0, 1.0]


# --------------------------------------------------------------------------- mesurer, apprendre, examiner
def _un(args): return jouer(*args)


def mesurer(graines, politique=None, jours=20, procs=1):
    if procs <= 1: return [jouer(g, politique, jours) for g in graines]
    with Pool(procs) as p: return p.map(_un, [(g, politique, jours) for g in graines])


def resume(nom, rs):
    n = [r["note"] for r in rs]
    return (f"{nom:22s} note mediane {np.median(n):8.2f}  faim {np.mean([r['faim'] for r in rs]):6.2%}  "
            f"argent {np.mean([r['argent'] for r in rs]):10.0f}  morts {np.mean([r['morts'] for r in rs]):4.1f}  "
            f"conservation {max(r['conservation'] for r in rs):.1e}")


def apprendre(graines, generations=12, enfants=16, sigma=0.3, jours=20, journal=None, procs=8):
    """Strategie d evolution simple : on garde le meilleur, on tire ses enfants autour de lui. Le monde n est pas
    derivable ; on n a pas besoin qu il le soit."""
    rng = np.random.default_rng(7)
    theta = rng.normal(0, 0.3, N_POIDS)
    meilleur = float(np.median([r["note"] for r in mesurer(graines, Politique(theta), jours, procs)]))
    print({"generation": -1, "note_depart": round(meilleur, 2)}, flush=True)
    for g in range(generations):
        enfants_theta = [theta + sigma * rng.normal(0, 1, N_POIDS) for _ in range(enfants)]
        # tous les ( enfant, monde ) en une seule fournee : c est la ferme de coeurs de la station qui travaille
        taches = [(gr, Politique(t), jours) for t in enfants_theta for gr in graines]
        with Pool(procs) as p: plat = p.map(_un, taches)
        notes = [float(np.median([r["note"] for r in plat[i * len(graines):(i + 1) * len(graines)]]))
                 for i in range(len(enfants_theta))]
        k = int(np.argmax(notes))
        if notes[k] > meilleur:
            theta, meilleur = enfants_theta[k], notes[k]
        else:
            sigma *= 0.8
        ligne = {"generation": g, "meilleure_note": round(meilleur, 2), "sigma": round(sigma, 3)}
        print(ligne, flush=True)
        if journal: journal.write(json.dumps(ligne) + "\n"); journal.flush()
    return theta, meilleur


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mesure", action="store_true", help="les temoins seuls, sans rien apprendre")
    p.add_argument("--apprendre", action="store_true")
    p.add_argument("--jours", type=int, default=20)
    p.add_argument("--generations", type=int, default=12)
    p.add_argument("--procs", type=int, default=8)
    p.add_argument("--sortie", default="/mnt/data/hmt/monde/apprenti")
    a = p.parse_args()
    os.makedirs(a.sortie, exist_ok=True)
    ecole = list(range(1, 9))            # les mondes de l ecole
    examen = list(range(101, 111))       # les mondes jamais vus
    t0 = time.time()
    if a.mesure or not a.apprendre:
        print(resume("regle", mesurer(examen, None, a.jours, a.procs)), flush=True)
        print(resume("aucun commerce", mesurer(examen, marchand_muet, a.jours, a.procs)), flush=True)
        print(resume("commerce aveugle", mesurer(examen, marchand_aveugle, a.jours, a.procs)), flush=True)
        print(f"{time.time() - t0:.0f} s", flush=True)
        return 0
    with open(os.path.join(a.sortie, "apprentissage.jsonl"), "a") as j:
        theta, note = apprendre(ecole, generations=a.generations, jours=a.jours, journal=j, procs=a.procs)
    np.save(os.path.join(a.sortie, "marchand.npy"), theta)
    regle = mesurer(examen, None, a.jours, a.procs)
    aveugle = mesurer(examen, marchand_aveugle, a.jours, a.procs)
    appris = mesurer(examen, Politique(theta), a.jours, a.procs)
    gagnes = sum(1 for r, s in zip(regle, appris) if s["note"] > r["note"])
    print(resume("regle ( examen )", regle), flush=True)
    print(resume("aveugle ( examen )", aveugle), flush=True)
    print(resume("appris ( examen )", appris), flush=True)
    print(f"mondes gagnes {gagnes}/{len(examen)} | {time.time() - t0:.0f} s", flush=True)
    with open(os.path.join(a.sortie, "examen.json"), "w") as f:
        json.dump({"regle": regle, "aveugle": aveugle, "appris": appris, "gagnes": gagnes, "note_ecole": note}, f, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
