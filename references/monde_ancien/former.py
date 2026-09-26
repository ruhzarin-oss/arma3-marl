"""FORMER les menages - points 1 a 4 des douze manques.

Instruction, exercice, debrief, correction, qualification : ici l eleve n est pas interroge, il AGIT. Chaque soir il
choisit combien stocker ; chaque lendemain il apprend s il a mange. La doctrine ( poids partages ) est ecrite sur
disque et rechargee : c est ce qui reste du pays quand la machine s arrete.

   python -m monde.former --epoques 6                 # forme, puis qualifie
   python -m monde.former --qualifier seulement       # qualifie une doctrine deja ecrite
Porte, ecrite d avance ( plans/plan-12-manques.md, point 1 ) : moins de jours de faim que la regle sur les 10 mondes
d examen, et dans au moins 7 d entre eux. Falsificateur : si la regle est deja sans faim, l epreuve est nulle."""
import argparse, json, os, time
from multiprocessing import Pool
from . import agents as A, apprenti as AP, config as C

DOCTRINE = "/mnt/data/hmt/monde/doctrine/menages.json"
ECOLE = list(range(1, 9))
EXAMEN = list(range(101, 111))


def jouer(graine, doctrine=None, jours=20, apprend=False):
    """Un monde entier avec sa secheresse. Rend la faim, les morts, l argent - et la doctrine enrichie si elle apprend."""
    w = AP.monde_epreuve(graine)
    w.doctrine, w.apprentissage = doctrine, apprend
    argent0 = w.argent_total()
    faim = 0.0
    for _ in range(jours):
        for _ in range(C.PAS_PAR_JOUR): w.pas_suivant()
        faim += w.stats_jour.get("menages_sans_nourriture", 0) / len(w.menages)
    d_arg, d_b = w.verifier_conservation()
    return {"graine": graine, "faim": faim / jours, "morts": sum(1 for h in w.habitants if not h.vivant),
            "argent": w.argent_total() - argent0,
            "conservation": max(abs(d_arg), max(abs(v) for v in d_b.values()))}


def _un(a): return jouer(*a)


def mesurer(graines, doctrine, jours, procs):
    taches = [(g, doctrine, jours, False) for g in graines]
    if procs <= 1: return [ _un(t) for t in taches ]
    with Pool(procs) as p: return p.map(_un, taches)


def resume(nom, rs):
    return (f"{nom:26s} faim {sum(r['faim'] for r in rs) / len(rs):6.2%}  morts {sum(r['morts'] for r in rs) / len(rs):4.1f}  "
            f"argent {sum(r['argent'] for r in rs) / len(rs):9.0f}  conservation {max(r['conservation'] for r in rs):.1e}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--epoques", type=int, default=6)
    p.add_argument("--jours", type=int, default=20)
    p.add_argument("--procs", type=int, default=10)
    p.add_argument("--doctrine", default=DOCTRINE)
    p.add_argument("--qualifier", action="store_true", help="ne pas former : qualifier la doctrine deja ecrite")
    a = p.parse_args()
    t0 = time.time()

    if a.qualifier:
        doctrine = A.Doctrine.lire(a.doctrine, epsilon=0.0)
        print(f"doctrine relue : {doctrine.n_lecons} lecons", flush=True)
    else:
        doctrine = A.Doctrine(alpha=0.05, epsilon=0.15)
        for e in range(a.epoques):
            for g in ECOLE:
                jouer(g, doctrine, a.jours, apprend=True)
            doctrine.epsilon = max(0.02, doctrine.epsilon * 0.75)
            print({"epoque": e, "lecons": doctrine.n_lecons, "recompense_moyenne": round(doctrine.moyenne(), 4),
                   "exploration": round(doctrine.epsilon, 3)}, flush=True)
        doctrine.ecrire(a.doctrine)
        print(f"doctrine ecrite : {a.doctrine}", flush=True)
        doctrine = A.Doctrine.lire(a.doctrine, epsilon=0.0)      # on qualifie CE QUI A ETE ECRIT, pas ce qu on a en memoire

    regle = mesurer(EXAMEN, None, a.jours, a.procs)
    hasard = mesurer(EXAMEN, A.Doctrine(epsilon=1.0), a.jours, a.procs)     # temoin : choisir au hasard
    formes = mesurer(EXAMEN, doctrine, a.jours, a.procs)
    gagnes = sum(1 for r, f in zip(regle, formes) if f["faim"] < r["faim"])
    print(resume("regle d origine", regle), flush=True)
    print(resume("choix au hasard", hasard), flush=True)
    print(resume("menages formes", formes), flush=True)
    print(f"mondes ou les formes ont moins faim : {gagnes}/{len(EXAMEN)} | {time.time() - t0:.0f} s", flush=True)
    sortie = os.path.join(os.path.dirname(a.doctrine), "qualification.json")
    with open(sortie, "w") as f:
        json.dump({"regle": regle, "hasard": hasard, "formes": formes, "gagnes": gagnes}, f, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
