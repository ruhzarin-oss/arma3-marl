#!/usr/bin/env python3
"""bilan_blocs — après une endurance des blocs : recompte les pertes dans le journal de CMO avec causes_cmo À JOUR ( B2, B7 )
et, si le pont est libre, dit qui vole encore ( altitude des avions HMT restés dans le scénario ). Ajoute une section à
rapport_blocs.md, sans toucher aux mesures de l'endurance.

30/09 : l'endurance du 29/09 lisait les pertes avec un causes_cmo qui ignorait « [Russie-Chine] » ( tiret ) ; ses B2 et B7
sont donc faux par construction, ce bilan les refait sur les mêmes journaux.

    .venv312/bin/python cmo/bilan_blocs.py [<dossier cmo_blocs/…>] [--attendre] [--ciel]
"""
import collections
import glob
import json
import os
import subprocess
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import causes_cmo                                         # noqa: E402
import cmo_labo as CL                                     # noqa: E402
import guerre_blocs as GB                                 # noqa: E402

EN_VOL_M = 1000.0                                         # au-dessus : en l'air ( les bases du théâtre sont sous 250 m )


def pertes(journal, pays):
    """{ pays : { cause : n } } lus dans le journal de CMO."""
    c, _ = causes_cmo.causes(open(journal, errors="ignore").read())
    out = collections.defaultdict(collections.Counter)
    for k, cause in c.items():
        i = (k - GB.DEC_AVION) // 100_000 - 1
        out[pays[i] if GB.DEC_AVION <= k < GB.DEC_BASE and 0 <= i < len(pays) else "?"][cause] += 1
    return {p: dict(v) for p, v in out.items()}


def recompter(dossier, theatre="baltique"):
    pays = list(__import__(f"theatres.{theatre}", fromlist=["PAYS"]).PAYS)
    lignes = [json.loads(l) for l in open(os.path.join(dossier, "tours.jsonl"))]
    journaux = [x["journal"] for x in lignes if x["quoi"] == "manche"]
    rapport = open(os.path.join(dossier, "rapport_blocs.md")).read()
    manches = json.loads(rapport.split("```")[1])["manches"]
    out, b2, sec, total = [], True, 0, 0
    for i, (j, m) in enumerate(zip(journaux, manches), 1):
        cz = pertes(j, pays)
        n_cmo, n_moteur = sum(sum(v.values()) for v in cz.values()), sum(m["pertes_comptees"].values())
        b2 &= n_cmo == n_moteur
        sec += sum(v.get("carburant", 0) for v in cz.values())
        total += n_cmo
        out.append({"manche": i, "pertes_cmo": cz, "cmo": n_cmo, "moteur": n_moteur})
    return {"B2_morts_une_fois": b2, "B7_les_bases_servent": total == 0 or sec / total < 0.10,
            "a_sec": sec, "pertes": total, "manches": out}


def ciel(camps=("OTAN", "Russie-Chine")):
    """{ camp : { en_vol, au_sol } } des avions HMT encore dans le scénario ( HMT_positions, outil du pont )."""
    with CL.Labo(camps=camps) as labo:
        vivants = labo.positions()["vivants"]
    out = {}
    for camp, L in vivants.items():
        avions = [x for x in L if GB.DEC_AVION <= x[0] < GB.DEC_BASE]
        out[camp] = {"en_vol": sum(1 for x in avions if x[3] > EN_VOL_M), "au_sol": sum(1 for x in avions if x[3] <= EN_VOL_M)}
    return out


def endurance_vivante():
    # Ancré au début de la ligne de commande : le serveur tmux garde celle de sa première session ( « tmux new-session …
    # endurance_blocs.py » ) et vit tant qu'une session existe, dont celle de ce bilan.
    return subprocess.run(["pgrep", "-f", r"^\S*python\S* \S*endurance_blocs\.py"], capture_output=True).returncode == 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dossier = args[0] if args else max(glob.glob(os.path.join(CL.ETAT, "cmo_blocs", "*/")), key=os.path.getmtime)
    while "--attendre" in sys.argv and endurance_vivante():
        time.sleep(30)
    r = recompter(dossier)
    if "--ciel" in sys.argv:
        try:
            r["ciel"] = ciel()
        except CL.ErreurLabo as e:
            r["ciel"] = f"{type(e).__name__}: {e}"
    l = ["", f"## Bilan recompté le {time.strftime('%Y-%m-%d %H:%M')} ( causes_cmo corrigé, 8529657 )", "",
         f"- {'✅' if r['B2_morts_une_fois'] else '❌'} B2_morts_une_fois",
         f"- {'✅' if r['B7_les_bases_servent'] else '❌'} B7_les_bases_servent ( {r['a_sec']} à sec sur {r['pertes']} )",
         "", "```", json.dumps(r, ensure_ascii=False, indent=1), "```"]
    with open(os.path.join(dossier, "rapport_blocs.md"), "a") as g:
        g.write("\n".join(l) + "\n")
    print(json.dumps(r, ensure_ascii=False, indent=1))
