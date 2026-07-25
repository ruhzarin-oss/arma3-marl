#!/usr/bin/env python3
"""analyse_banque.py — LA QUESTION QUI DÉCIDE DE TOUT :
l'exposition mesurée du chemin choisi prédit-elle l'issue de la partie ?

Si OUI  -> la fonction de valeur a de quoi apprendre, on passe au rejeu inversé.
Si NON  -> le résultat se joue ailleurs, et il faut trouver la vraie variable AVANT d'entraîner.
           (entraîner sur une variable qui ne prédit rien = des semaines perdues)

On recalcule l'exposition pour TOUTES les parties, y compris les premières (elle se déduit des
positions de défenseurs enregistrées + du relevé de terrain). On ne se fie pas au nom du secteur :
les défenseurs bougent d'une partie à l'autre, donc « le sud » ne veut rien dire.
"""
import sys, os, json, glob, math
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
import intentions as IN

LEV = "/home/younes/arma3-marl/leviathan"
terr = IN.charger_terrain(LEV, "Altis", 16781, 12604)


def expo_du_chemin(d):
    """Exposition RÉELLEMENT SUBIE : part des instants-soldat où un défenseur vivant voyait l'homme.
    C'est la mesure honnête — pas l'exposition théorique d'un secteur, mais celle du trajet parcouru."""
    fx, fy = d["fob"]; F = d["frames"]
    vus = 0; tot = 0
    for f in F:
        est = [(e[0] - fx, e[1] - fy) for e in f.get("east", []) if len(e) < 3 or e[2]]
        if not est:
            continue
        for w in f["west"]:
            if not w[2]:
                continue
            tot += 1
            px, py = w[0] - fx, w[1] - fy
            if any(terr.los(px, py, ex, ey) for ex, ey in est):
                vus += 1
    return vus / tot if tot else None


rows = []
for f in sorted(glob.glob(os.path.join(LEV, "banque/ex_*.json"))):
    try:
        d = json.load(open(f)); m = d["metrics"]
        rows.append(dict(
            nom=os.path.basename(f)[3:-5],
            secteur=os.path.basename(f).split("_")[1],
            pris=bool(m.get("took")), pertes=m.get("west_losses", 0),
            approche=m.get("min_fob_dist", 999), tick=m.get("took_tick"),
            expo=expo_du_chemin(d)))
    except Exception as e:
        print("  ignoré %s (%s)" % (f, e))

rows = [r for r in rows if r["expo"] is not None]
print("=== %d parties analysées ===" % len(rows), flush=True)

gag = [r for r in rows if r["pris"]]
per = [r for r in rows if not r["pris"]]


def moy(L, k):
    return sum(r[k] for r in L) / len(L) if L else float("nan")


print("\n=== L'EXPOSITION SUBIE PRÉDIT-ELLE L'ISSUE ? ===", flush=True)
print("%-22s %8s %14s %10s %10s" % ("", "parties", "exposition", "pertes", "approche"), flush=True)
print("%-22s %8d %13.1f%% %10.1f %9.0f m" % ("parties GAGNÉES", len(gag), 100 * moy(gag, "expo"), moy(gag, "pertes"), moy(gag, "approche")), flush=True)
print("%-22s %8d %13.1f%% %10.1f %9.0f m" % ("parties PERDUES", len(per), 100 * moy(per, "expo"), moy(per, "pertes"), moy(per, "approche")), flush=True)

if gag and per:
    ecart = moy(per, "expo") - moy(gag, "expo")
    print("\n  écart d'exposition perdues - gagnées : %+.1f point" % (100 * ecart), flush=True)
    verdict = ("L'EXPOSITION PRÉDIT -> on peut apprendre dessus" if ecart > 0.03 else
               "l'exposition ne sépare PAS -> chercher la vraie variable avant d'entraîner")
    print("  >>> %s" % verdict, flush=True)

print("\n=== le détail, trié du moins exposé au plus exposé ===", flush=True)
print("%-18s %-11s %10s %8s %9s" % ("partie", "secteur", "exposition", "issue", "pertes"), flush=True)
for r in sorted(rows, key=lambda r: r["expo"]):
    print("%-18s %-11s %9.1f%% %8s %9d" % (r["nom"], r["secteur"], 100 * r["expo"],
                                           ("PRIS" if r["pris"] else "non"), r["pertes"]), flush=True)
json.dump(rows, open(os.path.join(LEV, "banque/analyse.json"), "w"), indent=1)
print("\nANALYSE_DONE", flush=True)
