"""PORTE G1 DE L ARCHIPEL ( plans/plan-archipel.md, ecrite avant la mesure ) : chaque ile vit SEULE comme un pays.

Chacune des six iles, seule, avec tous les domaines livres, JOURS jours : aucun plantage, la conservation du socle
( argent et biens ) TENUE chaque soir. On note la faim, les morts et les vivants, sans seuil : un pays pauvre peut
souffrir, c est une mesure, pas un echec. Controle positif : une ile dont la carte n a plus de capitale doit echouer
des l installation ( la porte sait echouer ).

   python -m monde.porte_iles --echelle 20 --jours 30"""
import argparse, copy, json, os, sys, time, traceback
from multiprocessing import Pool
from . import monde as W, tests as T, carte as K
from .pays import pays as P
from .porte_domaines import LIVRES

ILES = ("Altis", "Malden", "Stratis", "Tanoa", "Enoch", "Sara")


def vivre(args):
    ile, echelle, jours = args
    t0 = time.perf_counter()
    try:
        w = W.Monde(iles=(ile,), echelle=echelle); P.installer(w, LIVRES)
        t_inst = time.perf_counter() - t0
        rompus, faims, n0 = [], [], w.table.n
        morts0 = int((w.table.vivant[:n0] == 0).sum())
        for j in range(jours):
            T.jours(w, 1)
            tenue, msg = w.pays.socle.conservation.tenue()
            if not tenue: rompus.append((w.jour, msg[:120]))
            faims.append(w.stats_jour.get("menages_sans_nourriture", 0) / max(1, len(w.menages)))
        n = w.table.n; viv = int(w.table.vivant[:n].sum())
        return {"ile": ile, "ok": not rompus, "habitants": n0, "vivants_fin": viv, "nes": n - n0,
                "morts": int((w.table.vivant[:n] == 0).sum()) - morts0, "faim_moyenne": sum(faims) / len(faims),
                "faim_max": max(faims), "rompus": rompus[:3], "installation_s": round(t_inst, 1),
                "jour_s": round((time.perf_counter() - t0 - t_inst) / jours, 2), "gouvernement": w.carte.gouvernement.id}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-3:]
        return {"ile": ile, "ok": False, "erreur": f"{type(e).__name__} : {str(e)[:150]} | "
                + " <- ".join(f"{f.filename.split('/')[-1]}:{f.lineno}" for f in reversed(tb))}


def controle_positif():
    """Une ile dont la carte de pays n a plus de capitale doit echouer a l installation."""
    reel = K.carte_du_pays
    def sans_capitale(ile):
        c = reel(ile)
        if c is not None: c = copy.deepcopy(c); c["lieux"] = [l for l in c["lieux"] if l["type"] != "capitale"]
        return c
    K.carte_du_pays = sans_capitale
    try:
        W.Monde(iles=("Malden",), echelle=1)
        return False, "une ile sans capitale s est installee : la porte ne sait pas echouer"
    except Exception as e:
        return True, f"une ile sans capitale echoue bien ( {type(e).__name__} )"
    finally:
        K.carte_du_pays = reel


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--echelle", type=float, default=20)
    a.add_argument("--jours", type=int, default=30)
    a.add_argument("--sortie", default=None)
    x = a.parse_args()
    ok_c, msg_c = controle_positif()
    print(f"controle positif : {'OK' if ok_c else 'ECHEC'} - {msg_c}", flush=True)
    with Pool(len(ILES)) as pool:
        res = pool.map(vivre, [(ile, x.echelle, x.jours) for ile in ILES])
    for r in res:
        if "erreur" in r: print(f"ECHOUE  {r['ile']:8s} {r['erreur']}"); continue
        print(f"{'PASSE ' if r['ok'] else 'ECHOUE'}  {r['ile']:8s} {r['habitants']:6d} hab. -> {r['vivants_fin']:6d} vivants "
              f"( {r['nes']} nes, {r['morts']} morts ) | faim moyenne {r['faim_moyenne']:.1%}, max {r['faim_max']:.1%} | "
              f"conservation {'tenue' if r['ok'] else r['rompus']} | installation {r['installation_s']} s, {r['jour_s']} s/jour "
              f"| gouvernement {r['gouvernement']}", flush=True)
    passe = ok_c and all(r.get("ok") for r in res)
    print(f"PORTE G1 ( chaque ile seule, {x.jours} jours ) : {'FRANCHIE' if passe else 'ECHOUEE'}", flush=True)
    if x.sortie: json.dump({"controle_positif": msg_c, "iles": res}, open(x.sortie, "w"), indent=1)
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
