#!/usr/bin/env python3
"""FILE -> PLANE. Rend le verdict des runs finis a la tache qui les a demandes.

Lit chaque `runs/*/FIN.json` non encore rendu (temoin `.rendu`), retrouve le numero de tache
dans `job.json` (champ `plane`), ecrit un commentaire avec le verdict CHIFFRE, et bascule
l etat :
    COMPLET -> « Fait »          ECHEC -> retour a « A faire », avec la cause
⚠️ Un run sans champ `plane` (job depose a la main) est ignore, pas rate : l ancien mode de
travail continue de fonctionner sans Plane.
"""
import json, os, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plane_orm as PL

H = "/mnt/data/hmt"


def main():
    rendus = 0
    for d in sorted(os.listdir(H + "/runs")):
        r = "%s/runs/%s" % (H, d)
        fin, job, temoin = r + "/FIN.json", r + "/job.json", r + "/.rendu"
        if not os.path.exists(fin) or os.path.exists(temoin):
            continue
        try:
            J = json.load(open(job)); F = json.load(open(fin))
        except Exception as e:
            print("  %s : illisible (%s)" % (d, e)); continue
        seq = J.get("plane")
        if not seq:
            open(temoin, "w").write("sans plane")
            continue

        lignes = []
        for g, res in sorted(F.get("resultats", {}).items()):
            v = res.get("verdict", "?") if isinstance(res, dict) else str(res)
            det = ""
            if isinstance(res, dict):
                det = " · ".join("%s=%s" % (k, res[k]) for k in list(res)[:6] if k != "verdict")
            lignes.append("<li><b>%s</b> : %s%s</li>"
                          % (html.escape(g), html.escape(str(v)),
                             (" — " + html.escape(det)) if det else ""))
        corps = ("<p><b>%s</b> — run <code>%s</code>, %d s, %d/%d graines lues.</p><ul>%s</ul>"
                 % (F.get("verdict", "?"), html.escape(d), F.get("duree_s", 0),
                    F.get("graines_lues", 0), F.get("graines_attendues", 0),
                    "".join(lignes) or "<li>aucun resultat</li>"))
        PL.commenter(seq, corps)
        if F.get("verdict") == "COMPLET":
            PL.etat(seq, "Fait"); etat = "Fait"
        else:
            PL.etat(seq, "A faire"); etat = "A faire (relance)"
        open(temoin, "w").write(F.get("verdict", "?"))
        print("  %s -> HMT-%d : %s, tache %s" % (d, seq, F.get("verdict"), etat))
        rendus += 1
    if not rendus:
        print("  aucun run neuf a rendre")
    return 0


if __name__ == "__main__":
    sys.exit(main())
