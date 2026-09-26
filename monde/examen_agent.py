"""L EXAMEN D UN GOUVERNEMENT ECRIT PAR L AGENT ( 26/09 ) : le code, fige, joue des mondes qu il n a jamais vus.

Critere ecrit AVANT la mesure :
  - chaque monde ( ile x graine ) joue trois gouvernements sur la meme graine : le code examine, les regles, rien ;
  - le code PASSE si la difference moyenne de jours de faim ( code - regles ) est negative avec un intervalle de
    confiance a 95 % ( bootstrap apparie, 10 000 tirages ) qui ne touche pas zero, ET s il fait mieux que les regles
    sur au moins 70 % des mondes ;
  - dette et morts sont rapportees a cote ( pas de critere ).
Les graines d examen ne sont pas celle de l entrainement ( C.GRAINE ).

   python -m monde.examen_agent --code /mnt/data/hmt/agent_codeur/Malden/v015.py --graines 10 --jours 30"""
import argparse, json, os, sys, time
import numpy as np
from multiprocessing import get_context
from . import config as C, agent_codeur as AC

ILES = C.ILES_ARCHIPEL
GRAINES_EXAMEN = tuple(range(1001, 1051))


def _un(args):
    ile, graine, source, nom, jours, echelle = args
    t0 = time.time()
    m = AC.evaluer(source, ile, echelle, jours, graine)
    return {"ile": ile, "graine": graine, "gouvernement": nom, "faim": m["jours_de_faim"], "morts": m["morts_nets"],
            "dette": m["dette"], "refus": m["refus"], "plantages": m["jours_joues_par_les_regles"],
            "conservation": m["conservation"], "secondes": round(time.time() - t0)}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--code", required=True); a.add_argument("--graines", type=int, default=10)
    a.add_argument("--jours", type=int, default=30); a.add_argument("--echelle", type=float, default=20.0)
    a.add_argument("--travailleurs", type=int, default=4); a.add_argument("--sortie", default=None)
    x = a.parse_args()
    # --code : un .py ( le meme code sur toutes les iles ) ou un dossier <Ile>/meilleur.py ( le code de chaque ile )
    if os.path.isdir(x.code):
        codes = {ile: open(os.path.join(x.code, ile, "meilleur.py")).read() for ile in ILES
                 if os.path.exists(os.path.join(x.code, ile, "meilleur.py"))}
        sortie = x.sortie or os.path.join(x.code, "examen.jsonl")
    else:
        codes = {ile: open(x.code).read() for ile in ILES}
        sortie = x.sortie or os.path.splitext(x.code)[0] + "_examen.jsonl"
    graines = GRAINES_EXAMEN[:x.graines]
    taches = [(ile, g, s, nom, x.jours, x.echelle) for ile in codes for g in graines
              for nom, s in (("code", codes[ile]), ("regles", AC.REGLES), ("rien", AC.RIEN))]
    print(f"examen de {x.code} : {len(ILES)} iles x {len(graines)} graines x 3 gouvernements = {len(taches)} mondes, "
          f"{x.jours} jours, {int(x.echelle * 500)} habitants", flush=True)
    res = []
    with get_context("fork").Pool(x.travailleurs, maxtasksperchild=4) as pool, open(sortie, "w") as f:
        for r in pool.imap_unordered(_un, taches):
            res.append(r); f.write(json.dumps(r) + "\n"); f.flush()
            if len(res) % 15 == 0: print(f"   {len(res)}/{len(taches)} mondes", flush=True)
    par = {}
    for r in res: par.setdefault((r["ile"], r["graine"]), {})[r["gouvernement"]] = r
    mondes = [k for k, v in par.items() if len(v) == 3]
    d = np.array([par[k]["code"]["faim"] - par[k]["regles"]["faim"] for k in mondes])
    rng = np.random.default_rng(0)
    boot = np.array([rng.choice(d, len(d)).mean() for _ in range(10_000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    mieux = float(np.mean(d < 0))
    passe = hi < 0 and mieux >= 0.70
    moy = lambda g, k: np.mean([par[m][g][k] for m in mondes])
    print(f"\n{len(mondes)} mondes. Jours de faim moyens : code {moy('code', 'faim'):.3f}, regles {moy('regles', 'faim'):.3f}, "
          f"rien {moy('rien', 'faim'):.3f}")
    print(f"difference code - regles : {d.mean():+.3f} IC95 [{lo:+.3f} ; {hi:+.3f}] ; le code fait mieux sur {mieux:.0%} des mondes")
    for ile in [i for i in ILES if i in codes]:
        di = [par[m]["code"]["faim"] - par[m]["regles"]["faim"] for m in mondes if m[0] == ile]
        print(f"   {ile:8s} : {np.mean(di):+.3f} ( mieux {np.mean(np.array(di) < 0):.0%} )")
    print(f"dette moyenne : code {moy('code', 'dette') / 1e6:.2f} M, regles {moy('regles', 'dette') / 1e6:.2f} M ; "
          f"morts nets : code {moy('code', 'morts'):.1f}, regles {moy('regles', 'morts'):.1f} ; "
          f"plantages {sum(par[m]['code']['plantages'] for m in mondes)}, refus {sum(par[m]['code']['refus'] for m in mondes)} ; "
          f"conservation tenue partout : {all(par[m][g]['conservation'] for m in mondes for g in par[m])}")
    print(f"EXAMEN : {'PASSE' if passe else 'ECHOUE'}")
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
