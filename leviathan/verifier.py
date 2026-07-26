#!/usr/bin/env python3
"""verifier.py — LE GARDE-FOU CONTRE LES BUGS SILENCIEUX.

Le 26/07, sept défauts ont traversé la journée SANS lever la moindre erreur :
  - le pont ne parlait qu'à un client (spawns fantômes)
  - une compilation SQF échouait en laissant les anciennes fonctions en mémoire
  - il faisait NUIT (les défenseurs ne voyaient rien -> l'exposition ne comptait plus)
  - le serveur mettait à jour SA copie de la position du joueur, pas celle du client
  - la position dans mission.sqm s'écrit {x, HAUTEUR, y} -> perso enterré
  - la valeur apprise avait supprimé l'appui (68 appuis identiques dans les 8 parties)
  - mon arrêt anticipé coupait chaque partie au tiers (150 -> 48 décisions)

Point commun : des fichiers valides, des métriques cohérentes, et des conclusions fausses.
Ce script cherche exactement ça. Il ne teste pas « est-ce que ça marche » mais
« est-ce que ça ressemble à ce qu'on attend, et est-ce que ça VARIE comme ça devrait ».

Usage : python verifier.py 'mix_*.json'          (vérifie un lot)
        python verifier.py 'mix_*.json' --ref banque/ex_*.json   (compare à une référence)
"""
import sys, os, json, glob, math, argparse, statistics as st

LEV = "/home/younes/arma3-marl/leviathan"

# Plages attendues, tirées de l'historique mesuré. Sortir de là = suspect, pas forcément faux.
ATTENDU = {
    "decisions_par_soldat": (6.0, 20.0, "coupé trop tôt / gigotement"),
    "steps": (40, 95, "partie tronquée ou horizon incohérent"),
    "west_losses": (0, 6, "carnage anormal ou aucun combat"),
    "min_fob_dist": (10, 130, "n'a pas bougé / valeur aberrante"),
}


def charge(paths):
    out = []
    for p in sorted(paths):
        try:
            d = json.load(open(p))
            m = dict(d.get("metrics", {}))
            m["_f"] = os.path.basename(p)
            m["_frames"] = len(d.get("frames", []))
            m["_fob"] = tuple(d.get("fob", (0, 0)))
            f0 = d["frames"][0] if d.get("frames") else {}
            m["_n_west"] = len(f0.get("west", []))
            m["_n_east"] = len(f0.get("east", []))
            out.append(m)
        except Exception as e:
            print("  !! illisible : %s (%s)" % (p, e))
    return out


def par_run(runs):
    """Chaque partie est-elle plausible en elle-même ?"""
    alertes = []
    for m in runs:
        n = m.get("nag", 12) or 12
        dps = (m.get("decisions", 0) or 0) / n
        vals = {"decisions_par_soldat": dps, "steps": m.get("steps", 0),
                "west_losses": m.get("west_losses", 0), "min_fob_dist": m.get("min_fob_dist", 0)}
        for k, v in vals.items():
            lo, hi, quoi = ATTENDU[k]
            if v is None or not (lo <= v <= hi):
                alertes.append((m["_f"], k, v, quoi))
        # cohérence interne : autant de frames que de pas annoncés
        if abs(m["_frames"] - (m.get("steps") or 0)) > 2:
            alertes.append((m["_f"], "frames vs steps", "%d/%s" % (m["_frames"], m.get("steps")), "enregistrement incomplet"))
    return alertes


# Constantes STRUCTURELLES (normales, à ne pas signaler) : « aucune » vaut toujours l'effectif,
# car chaque soldat n'a pas encore d'intention à son tout premier tour.
def _structurel(cle, valeur, runs):
    nags = {m.get("nag", 12) for m in runs}
    return cle == "fin:aucune" and len(nags) == 1 and valeur in nags


def constantes(runs, cles=("west_losses", "east_neutralized", "decisions", "steps", "min_fob_dist")):
    """LE détecteur le plus utile : une métrique IDENTIQUE partout = un mécanisme bloqué.
    C'est ce qui a démasqué les « 68 appuis » dans les 8 parties."""
    figees = []
    for k in cles:
        v = [m.get(k) for m in runs if m.get(k) is not None]
        if len(v) >= 4 and len(set(v)) == 1:
            figees.append((k, v[0], len(v)))
    # les raisons de fin sont le meilleur capteur de mécanisme bloqué
    fins = [m.get("fins") for m in runs if isinstance(m.get("fins"), dict)]
    if len(fins) >= 4:
        for raison in set().union(*[set(f) for f in fins]):
            v = [f.get(raison, 0) for f in fins]
            if len(set(v)) == 1 and v[0] > 0 and not _structurel("fin:" + raison, v[0], runs):
                figees.append(("fin:" + raison, v[0], len(v)))
    return figees


def conditions(runs):
    """Les parties d'un même lot étaient-elles COMPARABLES ?"""
    pbs = []
    for k, lab in (("_n_east", "défenseurs"), ("_n_west", "attaquants"), ("_fob", "objectif")):
        v = [m[k] for m in runs]
        if len(set(v)) > 1:
            pbs.append((lab, sorted(set(v))))
    return pbs


def compare(runs, ref):
    """Régression par rapport à une référence : c'est ce qui a démasqué 150 -> 48 décisions."""
    out = []
    for k in ("decisions", "steps", "min_fob_dist", "west_losses"):
        a = [m.get(k) for m in runs if m.get(k) is not None]
        b = [m.get(k) for m in ref if m.get(k) is not None]
        if len(a) >= 3 and len(b) >= 3:
            ma, mb = st.mean(a), st.mean(b)
            if mb > 0 and (ma < 0.6 * mb or ma > 1.7 * mb):
                out.append((k, ma, mb, ma / mb))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("motif")
    ap.add_argument("--ref", default=None, help="lot de référence pour détecter une régression")
    a = ap.parse_args()
    runs = charge(glob.glob(os.path.join(LEV, a.motif)))
    print("=== VÉRIFICATION DE %d PARTIES (%s) ===" % (len(runs), a.motif), flush=True)
    if not runs:
        print("  aucune partie."); sys.exit(1)

    ok = True
    al = par_run(runs)
    if al:
        ok = False
        print("\n[!] PARTIES HORS PLAGE :", flush=True)
        for f, k, v, quoi in al[:12]:
            print("    %-24s %-22s = %-8s (%s)" % (f, k, v, quoi), flush=True)
    else:
        print("\n[ok] toutes les parties dans les plages attendues", flush=True)

    fig = constantes(runs)
    if fig:
        ok = False
        print("\n[!] VALEURS FIGÉES (signature d'un mécanisme bloqué) :", flush=True)
        for k, v, n in fig:
            print("    %-24s = %-8s à l'identique sur %d parties" % (k, v, n), flush=True)
    else:
        print("[ok] aucune métrique figée (les parties varient comme elles doivent)", flush=True)

    cd = conditions(runs)
    if cd:
        ok = False
        print("\n[!] CONDITIONS NON COMPARABLES :", flush=True)
        for lab, vals in cd:
            print("    %s varie : %s" % (lab, vals), flush=True)
    else:
        print("[ok] conditions identiques d'une partie à l'autre", flush=True)

    if a.ref:
        ref = charge(glob.glob(os.path.join(LEV, a.ref)))
        rg = compare(runs, ref)
        if rg:
            ok = False
            print("\n[!] RÉGRESSION vs référence (%d parties) :" % len(ref), flush=True)
            for k, ma, mb, r in rg:
                print("    %-18s %.1f  vs  %.1f attendu   (x%.2f)" % (k, ma, mb, r), flush=True)
        else:
            print("[ok] pas de régression vs la référence", flush=True)

    print("\n>>> %s" % ("BASE SAINE — on peut conclure sur ces données" if ok else
                        "NE PAS CONCLURE sur ce lot tant que les alertes ne sont pas levées"), flush=True)
    sys.exit(0 if ok else 2)
