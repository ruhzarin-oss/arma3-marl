#!/usr/bin/env python3
"""coordination.py — MESURER LA COORDINATION (étage 2).

Le problème : toutes nos métriques sont des RÉSULTATS (objectif pris, pertes). Aucune ne dit si
l'escouade s'est entraidée. Donc quand elle gagne, on ne sait pas si c'est GRÂCE à sa coordination
ou MALGRÉ son absence — et on ne peut rien améliorer qu'on ne mesure pas.

Cinq mesures, toutes calculées depuis les enregistrements existants :

  ASSAUT       part de l'escouade qui progresse réellement        (0 = personne ne clôt)
  REDONDANCE   part qui fait LA MÊME chose au même instant        (1 = troupeau)
  APPUI UTILE  instants où l'un bondit PENDANT qu'un autre couvre (le feu-et-mouvement)
  ENGAGEMENT   défenseurs vivants que personne ne prend à partie  (les trous)
  BASCULE      fréquence des changements de rôle                  (0 = figé, 1 = agité)

PREUVE EXIGÉE (sinon la mesure ne vaut rien) : elle DOIT séparer une escouade coordonnée
d'une escouade chacun-pour-soi. C'est ce que fait `python coordination.py --valider`.
"""
import sys, os, json, glob, math, argparse

AVANCER, ABRITER, APPUYER = 0, 1, 2


def roles_par_tick(d):
    """Qui fait quoi à chaque instant. Marche AUSSI sur les runs sans intentions :
    on déduit alors le rôle du comportement (il bouge = il avance, il tire = il appuie)."""
    F = d["frames"]; out = []
    for k, f in enumerate(F):
        n = len(f["west"])
        vivants = [i for i in range(n) if f["west"][i][2]]
        if "intent" in f:
            adv = [i for i in vivants if f["intent"][i] == AVANCER]
            sup = [i for i in vivants if f["intent"][i] == APPUYER]
            abr = [i for i in vivants if f["intent"][i] == ABRITER]
        else:
            prev = F[k - 1]["west"] if k > 0 else f["west"]
            fw = f.get("firew", [0] * n)
            adv, sup, abr = [], [], []
            for i in vivants:
                bouge = math.hypot(f["west"][i][0] - prev[i][0], f["west"][i][1] - prev[i][1]) > 1.5
                tire = bool(fw[i]) if i < len(fw) else False
                (adv if bouge else (sup if tire else abr)).append(i)
        out.append(dict(t=f["t"], vivants=vivants, adv=adv, sup=sup, abr=abr))
    return out


_TERR = {}


def terrain_pour(d):
    """le plan de la zone (pour les vraies lignes de vue). Chargé une fois, mis en cache."""
    fx, fy = d["fob"]
    key = (fx, fy)
    if key not in _TERR:
        _TERR[key] = None
        for p in glob.glob("/home/younes/arma3-marl/leviathan/map_*.json"):
            try:
                m = json.load(open(p))
                if abs(m.get("cx", 0) - fx) + abs(m.get("cy", 0) - fy) < 500:
                    sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
                    import intentions as IN
                    _TERR[key] = IN.Terrain(m)
                    break
            except Exception:
                pass
    return _TERR[key]


def mesurer(path):
    d = json.load(open(path))
    fx, fy = d["fob"]; F = d["frames"]; R = roles_par_tick(d)
    n_ticks = max(len(F), 1)
    terr = terrain_pour(d)

    def los(ax, ay, bx, by):
        if terr is None:
            return True
        return terr.los(ax - fx, ay - fy, bx - fx, by - fy, steps=16)

    assaut, stagn, appui_c, trous = [], [], [], []
    dmin_prec = None
    for k, r in enumerate(R):
        nv = max(len(r["vivants"]), 1)
        assaut.append(len(r["adv"]) / nv)
        W = F[k]["west"]
        est = [e for e in F[k].get("east", []) if len(e) < 3 or e[2]]

        # STAGNATION : l'escouade s'agite (des rôles actifs) mais ne gagne PAS de terrain.
        # C'est ça, la pathologie « tout le monde appuie, personne ne clôt ».
        dmin = min((math.hypot(W[i][0] - fx, W[i][1] - fy) for i in r["vivants"]), default=None)
        if dmin is not None and dmin_prec is not None:
            actif = len(r["adv"]) + len(r["sup"]) > 0
            stagn.append(1.0 if (actif and (dmin_prec - dmin) < 1.0) else 0.0)
        dmin_prec = dmin if dmin is not None else dmin_prec

        # APPUI COUVRANT : l'appui SERT-IL vraiment à celui qui bondit ?
        # -> un appuyeur doit VOIR (plan réel) un ennemi proche de l'agent qui avance.
        for i in r["adv"]:
            wi = W[i]
            couvert = False
            for j in r["sup"]:
                wj = W[j]
                for e in est:
                    if math.hypot(e[0] - wi[0], e[1] - wi[1]) < 130 and los(wj[0], wj[1], e[0], e[1]):
                        couvert = True; break
                if couvert:
                    break
            appui_c.append(1.0 if couvert else 0.0)

        # TROUS : défenseurs vivants que PERSONNE ne voit (ni appuyeur, ni avanceur)
        if est:
            vus = 0
            for e in est:
                for i in r["vivants"]:
                    w = W[i]
                    if math.hypot(w[0] - e[0], w[1] - e[1]) < 250 and los(w[0], w[1], e[0], e[1]):
                        vus += 1; break
            trous.append(1.0 - vus / len(est))

    # BASCULE : à quelle fréquence un soldat change de rôle
    chg = 0; tot = 0
    for k in range(1, len(R)):
        p = {i: ("a" if i in R[k - 1]["adv"] else "s" if i in R[k - 1]["sup"] else "c") for i in R[k - 1]["vivants"]}
        for i in R[k]["vivants"]:
            if i in p:
                tot += 1
                c = "a" if i in R[k]["adv"] else "s" if i in R[k]["sup"] else "c"
                if c != p[i]:
                    chg += 1

    m = d.get("metrics", {})
    return dict(
        fichier=os.path.basename(path), mode=d.get("mode", "?"),
        pris=bool(m.get("took")), pertes=m.get("west_losses", "?"), approche=m.get("min_fob_dist", "?"),
        assaut=sum(assaut) / len(assaut) if assaut else 0.0,
        stagnation=sum(stagn) / len(stagn) if stagn else 0.0,
        appui_couvrant=sum(appui_c) / len(appui_c) if appui_c else 0.0,
        trous=sum(trous) / len(trous) if trous else 0.0,
        bascule=chg / tot if tot else 0.0,
    )


# Seules les mesures VALIDÉES sont affichées (elles séparent les 3 familles de comportement).
# « appui_couvrant » et « trous » sont calculés mais NON AFFICHÉS : ils reposent sur une ligne de vue
# reconstruite depuis le plan, qui s'est révélée bien plus pessimiste que le moteur (8 % de visibilité
# annoncée là où Arma produit du vrai combat). Cause : emprises rectangulaires pleines + relief ignoré.
# Les afficher reviendrait à publier des chiffres faux. Correctif propre = demander la vue à Arma
# (lineIntersects) en post-traitement, une fois par run — voir le rapport du 25/07.
COLS = [("assaut", "ASSAUT"), ("stagnation", "STAGNATION"), ("bascule", "BASCULE")]


def tableau(rows, titre):
    print("\n=== %s ===" % titre, flush=True)
    print("%-26s %5s %7s" % ("run", "pris", "pertes") + "".join("%12s" % c[1] for c in COLS), flush=True)
    for r in rows:
        print("%-26s %5s %7s" % (r["fichier"][:26], "OUI" if r["pris"] else "non", r["pertes"])
              + "".join("%12.2f" % r[c[0]] for c in COLS), flush=True)


def moyenne(rows, cle):
    v = [r[cle] for r in rows]
    return sum(v) / len(v) if v else 0.0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--valider", action="store_true", help="la mesure sépare-t-elle coordonné / chacun-pour-soi ?")
    a = ap.parse_args()
    D = "/home/younes/arma3-marl/leviathan"

    if a.valider:
        # LE TEST DE LA MESURE ELLE-MÊME : trois familles au comportement connu.
        fam = {
            "INTENTIONS qui RÉUSSISSENT": sorted(glob.glob(D + "/rep_intent_1.json")) + sorted(glob.glob(D + "/rep_intent_3.json")) + sorted(glob.glob(D + "/pyrgos_INTENT2.json")),
            "INTENTIONS qui ÉCHOUENT (tous appuient)": sorted(glob.glob(D + "/rep_intent_2.json")) + sorted(glob.glob(D + "/rep_intent_4.json")) + sorted(glob.glob(D + "/rep_intent_5.json")) + sorted(glob.glob(D + "/pyrgos_MARK.json")),
            "CLASSIQUE (chacun fonce)": sorted(glob.glob(D + "/rep_class_*.json")),
        }
        res = {}
        for nom, paths in fam.items():
            rows = []
            for p in paths:
                try: rows.append(mesurer(p))
                except Exception as e: print("  (ignoré %s : %s)" % (p, e))
            if rows:
                tableau(rows, nom)
                res[nom] = rows
        print("\n=== MOYENNES PAR FAMILLE ===", flush=True)
        print("%-42s" % "famille" + "".join("%12s" % c[1] for c in COLS), flush=True)
        for nom, rows in res.items():
            print("%-42s" % nom[:42] + "".join("%12.2f" % moyenne(rows, c[0]) for c in COLS), flush=True)
        print("\nLECTURE — ce que chaque mesure doit montrer si elle est bonne :", flush=True)
        print("  ASSAUT      haut chez les réussites, bas en classique   (qui clôt vraiment)", flush=True)
        print("  STAGNATION  HAUT chez les échecs 'tous appuient'        (ça s'agite sans gagner de terrain)", flush=True)
        print("  APPUI COUV  haut = l'appui protège vraiment le bond, bas = il tire dans le vide", flush=True)
        print("  TROUS       part des défenseurs que PERSONNE ne voit    (bas = couverture complète)", flush=True)
        print("  BASCULE     bas = rôles tenus, haut = papillonnage      (les intentions doivent être basses)", flush=True)
    else:
        paths = list(a.files) or sorted(glob.glob(D + "/*.json"))
        rows = []
        for p in paths:
            try: rows.append(mesurer(p))
            except Exception: pass
        tableau(rows, "coordination")
    print("COORD_DONE", flush=True)
