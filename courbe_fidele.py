#!/usr/bin/env python3
"""courbe_fidele — LA COURBE DE TOUCHER, REPAREE AU LIEU D ETRE CONTOURNEE.

La mesure Arma du 26/07 (`courbe_toucher.json`) porte sa propre alerte :

    « a 100 m, un homme COUCHE est touche autant qu un homme DEBOUT »

et `assault_terrain` REFUSE toute courbe dont le verificateur a parle. Il existe a cote un
`courbe_toucher_juge.json` qui porte EXACTEMENT LES MEMES CHIFFRES avec `alertes: []`. C est
l alerte qui a ete effacee, pas l anomalie qui a ete corrigee — et tous les bancs de leviathan
tournent dessus. On ne fait pas ca ici.

CE QU ON FAIT A LA PLACE. Le mecanisme est certain la ou la mesure est bruitee : une silhouette
PLUS PETITE ne peut pas etre PLUS FACILE a toucher. C est de la geometrie, pas une hypothese.
On impose donc la monotonie EN POSTURE a chaque distance, par moyennes pondérées des blocs qui
la violent (Pool Adjacent Violators), et on REFUSE la correction si elle depasse le bruit de
comptage — car alors ce ne serait plus du bruit, mais un phenomene qu il faudrait comprendre.

⚠️ CE QUI FERAIT ECHOUER CETTE REPARATION — ecrit avant :
  · une correction depassant 2 ecarts-types binomiaux -> on s arrete, on ne lisse pas.
  · une cellule sous 30 balles -> mesure trop bruitee, on le dit.
  · la monotonie EN DISTANCE n est PAS imposee : elle est seulement SIGNALEE. On ne connait
    pas de raison mecanique qui interdise une bosse a 50 m, donc on ne la corrige pas.
"""
import json, math, sys, pathlib

BRUT = "/home/younes/arma3-marl/leviathan/courbe_toucher.json"


def _se(p, n):
    """ecart-type binomial de la proportion p sur n balles"""
    return math.sqrt(max(p * (1.0 - p), 1e-9) / max(n, 1))


def _pava(p, n):
    """monotonie DECROISSANTE imposee sur p, ponderee par n. Renvoie la suite corrigee."""
    blocs = [[p[i], n[i], [i]] for i in range(len(p))]
    i = 0
    while i < len(blocs) - 1:
        if blocs[i][0] < blocs[i + 1][0] - 1e-12:          # violation : debout < couche
            a, b = blocs[i], blocs[i + 1]
            poids = a[1] + b[1]
            fusion = [(a[0] * a[1] + b[0] * b[1]) / poids, poids, a[2] + b[2]]
            blocs[i:i + 2] = [fusion]
            i = max(i - 1, 0)
        else:
            i += 1
    out = [0.0] * len(p)
    for val, _, idx in blocs:
        for j in idx:
            out[j] = val
    return out


def charger(chemin=BRUT, bavard=True):
    c = json.load(open(chemin))
    D = [int(x) for x in c["distances"]]
    POST = c["postures"]
    corrigees, changements, refus, maigres = {}, [], [], []
    for d in D:
        p = [c["pct_au_but"][str(d)][i] / 100.0 for i in range(len(POST))]
        n = [c["balles"][str(d)][i] for i in range(len(POST))]
        for i, ni in enumerate(n):
            if ni < 30:
                maigres.append((d, POST[i], ni))
        q = _pava(p, n)
        for i in range(len(p)):
            ecart = abs(q[i] - p[i])
            if ecart > 1e-9:
                s = _se(p[i], n[i])
                changements.append((d, POST[i], 100 * p[i], 100 * q[i], ecart / s if s else 99))
                if ecart > 2.0 * s:
                    refus.append((d, POST[i], ecart / s))
        corrigees[str(d)] = [100 * x for x in q]

    if bavard:
        print("\n  LA COURBE DE TOUCHER — reparee, pas contournee")
        print("  " + "-" * 66)
        print(f"    {'dist':>6}" + "".join(f"{x:>12}" for x in POST))
        for d in D:
            av = c["pct_au_but"][str(d)]
            ap = corrigees[str(d)]
            ligne = f"    {d:>5}m"
            for i in range(len(POST)):
                marque = "*" if abs(av[i] - ap[i]) > 1e-9 else " "
                ligne += f"{ap[i]:>11.1f}{marque}"
            print(ligne)
        print("  " + "-" * 66)
        print(f"    {len(changements)} cellules corrigees (*), toutes en POSTURE")
        for d, po, a, b, z in changements:
            print(f"      {d:>4}m {po:<7} {a:5.1f} % -> {b:5.1f} %   ecart = {z:.2f} sigma")
        if maigres:
            print(f"    ⚠ cellules sous 30 balles : {maigres}")
        # la monotonie EN DISTANCE est SIGNALEE, jamais imposee
        bosses = []
        for i, po in enumerate(POST):
            v = [corrigees[str(d)][i] for d in D]
            for k in range(len(v) - 1):
                if v[k] < v[k + 1] - 1e-9:
                    bosses.append((po, D[k], D[k + 1], v[k], v[k + 1]))
        if bosses:
            print("    ⚠ non-monotonies EN DISTANCE, signalees et NON corrigees :")
            for po, d1, d2, v1, v2 in bosses:
                print(f"      {po:<7} {d1}m {v1:.1f} % < {d2}m {v2:.1f} %")

    if refus:
        raise SystemExit(
            "\n  REFUS : une correction depasse deux ecarts-types binomiaux -> "
            f"{refus}\n  Ce n est plus du bruit. On ne lisse pas un phenomene qu on n a pas compris.")

    c2 = dict(c)
    c2["pct_au_but"] = corrigees
    c2["alertes"] = []
    c2["reparation"] = {
        "quoi": "monotonie imposee EN POSTURE par PAVA pondere par les balles",
        "pourquoi": "une silhouette plus petite ne peut pas etre plus facile a toucher",
        "alerte_dorigine": c.get("alertes"),
        "cellules_corrigees": [[d, po, round(a, 2), round(b, 2), round(z, 2)]
                               for d, po, a, b, z in changements],
        "refuse_si": "une correction depasse 2 sigma binomiaux",
    }
    return c2


if __name__ == "__main__":
    c = charger()
    out = pathlib.Path("/home/younes/arma3-marl/leviathan/courbe_toucher_monotone.json")
    out.write_text(json.dumps(c, indent=1))
    print(f"\n  ecrite : {out}")
    print("  Elle porte sa reparation en clair dans le champ `reparation` — un lecteur")
    print("  futur verra ce qui a ete change, de combien, et pourquoi.")
