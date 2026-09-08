#!/usr/bin/env python3
"""agreger - un run, un taux, et l INTERVALLE qui va avec.

Usage : agreger.py /mnt/data/hmt/runs/<run>

Ce que ce script existe pour empecher : lire " 3 succes sur 4 " comme " 75 % ".
A n=4 l intervalle a 95 pour cent va de 30 a 95 pour cent - la phrase ne dit
rien. Un taux sans son intervalle n est pas une mesure, c est une impression.

L intervalle est celui de WILSON, pas l approximation normale. La normale ment
exactement la ou on l interroge : a n=20 et p=0, elle rend [0 ; 0] - un zero
certifie sur vingt episodes - alors que Wilson rend [0 ; 0,16]. Un zero n est
pas un accord, et ce n est pas non plus une impossibilite.

Il REFUSE de conclure sous 5 episodes acceptes. Il les compte quand meme et il
le dit : c est un run trop court, pas un run casse.
"""
import json, glob, os, sys, math, statistics

Z = 1.959963984540054      # 95 pour cent, bilateral

def wilson(k, n, z=Z):
    """Intervalle de Wilson pour k succes sur n. Rend (bas, haut)."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    demi = (z / d) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, centre - demi), min(1.0, centre + demi))

def pc(x):
    return round(100.0 * x, 1)

def main(run):
    run = run.rstrip("/")
    if not os.path.isdir(run):
        print("dossier introuvable :", run); return 1

    # Le motif `g*` attrape g7 comme g7_r1 : les deux nommages coexistent.
    fichiers = sorted(glob.glob(os.path.join(run, "g*", "resultat.json")))
    episodes = []
    for f in fichiers:
        try:
            d = json.load(open(f))
        except Exception as e:
            episodes.append({"nom": os.path.basename(os.path.dirname(f)),
                             "verdict": "ILLISIBLE", "cause": str(e)})
            continue
        e = d.get("entete", {}) or {}
        episodes.append({
            "nom": os.path.basename(os.path.dirname(f)),
            "verdict": d.get("verdict", "?"),
            "cause_refus": d.get("cause_refus"),
            "portes_fausses": sorted(k for k, v in (d.get("portes") or {}).items() if not v),
            "issue": e.get("issue"), "cause": e.get("cause"),
            "graine": e.get("graine"), "palier": e.get("palier"),
            "phase_max": e.get("phase_max"),
            "charges": e.get("charges"), "sur": e.get("sur"),
            "vivants": e.get("vivants"), "duree": e.get("duree"),
            "alarme": e.get("alarme"), "compromis": e.get("compromis"),
        })

    acc = [e for e in episodes if e["verdict"] == "ACCEPTE"]
    n_tot, n_acc = len(episodes), len(acc)

    def entier(v):
        try: return int(float(v))
        except (TypeError, ValueError): return None

    succes  = [e for e in acc if e["issue"] == "SUCCES"]
    charges = [entier(e["charges"]) for e in acc]
    sur     = [entier(e["sur"]) for e in acc]
    vivants = [x for x in (entier(e["vivants"]) for e in acc) if x is not None]
    durees  = [x for x in (entier(e["duree"])   for e in acc) if x is not None]
    k_ch = sum(c for c in charges if c is not None)
    n_ch = sum(s for s in sur if s is not None)

    a = {"run": os.path.basename(run),
         "episodes_trouves": n_tot, "episodes_acceptes": n_acc,
         "episodes_refuses": [{"nom": e["nom"], "portes_fausses": e.get("portes_fausses"),
                               "cause_refus": e.get("cause_refus")}
                              for e in episodes if e["verdict"] != "ACCEPTE"],
         "methode_intervalle": "Wilson 95 pour cent",
         "conclusion": None, "detail": episodes}

    if n_acc:
        b, h = wilson(len(succes), n_acc)
        a["issue_succes"] = {"k": len(succes), "n": n_acc, "taux_pc": pc(len(succes) / n_acc),
                             "ic95_pc": [pc(b), pc(h)]}
        a["issues"] = {i: sum(1 for e in acc if e["issue"] == i)
                       for i in sorted({e["issue"] for e in acc if e["issue"]})}
        if n_ch:
            b, h = wilson(k_ch, n_ch)
            # ! L INTERVALLE SUR LES CHARGES EST OPTIMISTE, ET C EST DIT ICI.
            # Wilson suppose n tirages independants. Les trois charges d un meme
            # episode ne le sont pas : elles partagent le monde, l element et la
            # nuit. Le vrai intervalle est PLUS LARGE que celui-ci. On le donne
            # parce qu il borne par le bas, jamais comme une preuve d etroitesse.
            a["charges"] = {"posees": k_ch, "sur": n_ch, "taux_pc": pc(k_ch / n_ch),
                            "ic95_pc": [pc(b), pc(h)],
                            "avertissement": "charges d un meme episode non independantes : intervalle optimiste",
                            "par_episode": sorted(c for c in charges if c is not None)}
        if vivants:
            a["vivants"] = {"mediane": statistics.median(vivants),
                            "min": min(vivants), "max": max(vivants), "valeurs": sorted(vivants)}
        if durees:
            a["duree_s"] = {"mediane": statistics.median(durees),
                            "min": min(durees), "max": max(durees), "valeurs": sorted(durees)}

    if n_acc < 5:
        a["conclusion"] = "REFUS_TROP_PEU"
        a["pourquoi"] = ("%d episode(s) accepte(s), 5 au minimum. "
                         "Les chiffres sont ecrits, ils ne sont pas concluants." % n_acc)
    else:
        a["conclusion"] = "LISIBLE"

    with open(os.path.join(run, "AGREGE.json"), "w") as f:
        json.dump(a, f, indent=1, ensure_ascii=False)

    # ---- le resume de cinq lignes ----
    print("run       : %s   %d episodes, %d acceptes (%s)"
          % (a["run"], n_tot, n_acc, "%.0f %%" % (100.0 * n_acc / n_tot) if n_tot else "-"))
    if n_acc:
        s = a["issue_succes"]
        print("issue     : SUCCES %d/%d = %.1f %%   IC95 [%.1f ; %.1f]   %s"
              % (s["k"], s["n"], s["taux_pc"], s["ic95_pc"][0], s["ic95_pc"][1],
                 " ".join("%s=%d" % kv for kv in a["issues"].items())))
        c = a.get("charges")
        print("charges   : %s" % ("%d/%d = %.1f %%   IC95 [%.1f ; %.1f]  (intervalle optimiste)"
              % (c["posees"], c["sur"], c["taux_pc"], c["ic95_pc"][0], c["ic95_pc"][1]) if c else "aucune lue"))
        v, d = a.get("vivants"), a.get("duree_s")
        mv = "mediane %s, etendue [%s ; %s]" % (v["mediane"], v["min"], v["max"]) if v else "aucun"
        md = "mediane %s s, etendue [%s ; %s] s" % (d["mediane"], d["min"], d["max"]) if d else "aucune"
        print("vivants   : %s   |   duree : %s" % (mv, md))
    else:
        print("issue     : aucun episode accepte")
        print("charges   : -")
        print("vivants   : -   |   duree : -")
    print("conclusion: %s%s" % (a["conclusion"], "  " + a.get("pourquoi", "") if a["conclusion"] != "LISIBLE" else ""))
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    sys.exit(main(sys.argv[1]))
