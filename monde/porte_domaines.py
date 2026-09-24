"""PORTE D IDENTITE DES DOMAINES : un domaine reecrit en colonnes doit laisser le pays IDENTIQUE, au bit pres.

Deux mondes avec tous les domaines du pays installes tournent quelques jours ; on prend l empreinte de chaque colonne
du moteur ( habitants, menages ), de chaque colonne des domaines, des stocks, des prix, de l argent et du journal, jour
par jour. `--ecrire` fixe la reference ( le code d origine ), `--comparer` la confronte au code reecrit.
   python -m monde.porte_domaines --ecrire   /mnt/data/hmt/ref_domaines.json
   python -m monde.porte_domaines --comparer /mnt/data/hmt/ref_domaines.json"""
import argparse, hashlib, importlib.util, json, sys, time
import numpy as np
from . import monde as W, tests as T, population as PO, apprenti as AP
from .pays import pays as P

# ( graine, echelle, jours, secheresse ) : 2 000, 2 000 et 1 000 habitants, puis 500 sous secheresse et epidemie
# ( apprenti.monde_epreuve ) pour forcer la faim, donc les migrations
# ( graine, echelle, jours, secheresse, domaines : None = tous les livres ) ; le dernier, sans agenda, fait passer les
# domaines par leur chemin « sans agenda » ( la medecine lit alors le poste du moteur )
MONDES = ((11, 4, 8, False, None), (23, 4, 8, False, None), (7, 2, 40, False, None), (5, 1, 30, True, None),
          (13, 4, 10, False, ("medecine",)))
# les evenements rares dont on affiche le compte : une branche jamais empruntee n est pas prouvee
RARES = ("retraite", "fin_etudes", "entree_vie_active", "migration_interne", "naissance", "deces", "union",
         "divorce", "embauche", "licenciement", "faillite", "placement", "desherence", "fin_de_grossesse")
# les domaines livres : ceux dont le module existe ( 13 livraisons sur 28 au 24/09 )
LIVRES = [nom for nom, mod, _ in P.DOMAINES if importlib.util.find_spec(f"monde.pays.{mod}") is not None]


def _h(x):
    if isinstance(x, np.ndarray): return hashlib.sha1(np.ascontiguousarray(x).tobytes()).hexdigest()[:16]
    return hashlib.sha1(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()[:16]


def empreinte(w):
    t, mt, p = w.table, w.table.menages, w.pays
    e = {f"habitant.{c}": _h(getattr(t, c)[:t.n]) for c in PO.Table.CHAMPS}
    e.update({f"menage.{c}": _h(getattr(mt, c)[:mt.n]) for c in PO.TableMenages.CHAMPS})
    for genre, cols in p.colonnes.items():
        for nom, a in cols.cols.items(): e[f"pays.{genre}.{nom}"] = _h(a)
    e["entreprises"] = _h({k: (en.stocks, en.activite) for k, en in w.entreprises.items()})
    e["marches"] = _h({k: (m.stocks, m.prix) for k, m in w.marches.items()})
    e["publics"] = _h(w.publics)
    e["argent"] = repr(w.argent_total())
    e["journal"] = f"{len(w.evenements)} {_h(w.evenements)}"
    e["sejours"] = _h(w.sejours)
    e["journal_du_pays"] = _h(list(p.socle.journal.recents))
    return e


def jouer(graine, echelle, jours, secheresse=False, domaines=None, saboter=False):
    w = AP.monde_epreuve(graine) if secheresse else W.Monde(graine=graine, echelle=echelle)
    P.installer(w, list(domaines) if domaines else LIVRES)
    J = w.pays.socle.journal
    rares, serie, t0 = {}, [], time.perf_counter()
    for j in range(jours):
        if saboter and j == 3: w.table.menages.caisse[3] += 1e-9   # le controle positif : un milliardieme de drachme
        T.jours(w, 1); serie.append(empreinte(w))
    # les evenements rares, dans les deux journaux ( le moteur garde tout ; le pays, ses 10 000 plus recents )
    for e in list(J.recents) + w.evenements:
        if e["type"] in RARES: rares[e["type"]] = rares.get(e["type"], 0) + 1
    return serie, (time.perf_counter() - t0) / jours, len(w.habitants), rares


def main():
    a = argparse.ArgumentParser()
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--ecrire"); g.add_argument("--comparer")
    a.add_argument("--saboter", action="store_true", help="controle positif : la porte doit echouer")
    x = a.parse_args()
    res = {}
    print(f"{len(LIVRES)} domaines : {', '.join(LIVRES)}", flush=True)
    for graine, echelle, jours, secheresse, domaines in MONDES:
        serie, dt, n, rares = jouer(graine, echelle, jours, secheresse, domaines, x.saboter)
        res[f"{graine}"] = serie
        print(f"monde {graine} : {n} habitants, {jours} jours, {dt:.2f} s par jour | evenements rares {rares}", flush=True)
    if x.ecrire:
        json.dump(res, open(x.ecrire, "w")); print("reference ecrite"); return 0
    ref = json.load(open(x.comparer))
    ok = True
    for cle, serie in res.items():
        for j, (a_, b_) in enumerate(zip(ref[cle], serie)):
            diff = sorted(k for k in set(a_) | set(b_) if a_.get(k) != b_.get(k))
            if diff:
                ok = False
                print(f"  monde {cle} jour {j + 1} : ECART sur {len(diff)} empreintes : {diff[:12]}")
                break
        else: print(f"  monde {cle} : IDENTIQUE sur {len(serie)} jours ( {len(serie[0])} empreintes par jour )")
    print("PORTE DES DOMAINES :", "FRANCHIE" if ok else "ECHOUEE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
