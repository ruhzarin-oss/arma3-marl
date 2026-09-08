#!/usr/bin/env python3
"""FILE -> PLANE. Rend le verdict des runs finis a la tache qui les a demandes.

Lit chaque `runs/*/FIN.json` non encore rendu (temoin `.rendu`), retrouve le numero de tache
dans `job.json` (champs `plane` et `plane_projet`), ecrit un commentaire avec le verdict
CHIFFRE, et bascule
l etat :
    COMPLET -> « Fait »          ECHEC -> retour a « A faire », avec la cause
⚠️ Un run sans champ `plane` (job depose a la main) est ignore, pas rate : l ancien mode de
travail continue de fonctionner sans Plane.
"""
import json, os, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plane_orm as PL

H = "/mnt/data/hmt"


def refuses():
    """⛔ 08/09 — LE TROU QUI RENDAIT LE PONT MENTEUR. Un job refuse par le controle
    d avant-run ne cree aucun run, donc aucun FIN.json : la tache restait « En cours » dans
    Plane indefiniment, et l absence de nouvelle passait pour un travail en cours. On rend
    donc AUSSI les refus — avec leur raison — et la tache repart en « A faire »."""
    n = 0
    d = H + "/queue/refuses"
    if not os.path.isdir(d):
        return 0
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json") or os.path.exists("%s/%s.rendu" % (d, f)):
            continue
        try:
            J = json.load(open("%s/%s" % (d, f)))
        except Exception as e:
            print("  refus %s : illisible (%s)" % (f, e)); continue
        seq, proj = J.get("plane"), J.get("plane_projet", "HMT")
        if not seq:
            open("%s/%s.rendu" % (d, f), "w").write("sans plane"); continue
        try:
            raison = open("%s/%s.raison" % (d, f)).read().strip()
        except Exception:
            raison = "raison non enregistree (job refuse avant le 08/09)"
        PL.commenter(seq, "<p><b>REFUSE avant lancement</b> — job <code>%s</code> non joue.<br>"
                          "%s</p><p>La tache repart en « A faire » : rien n a ete mesure.</p>"
                          % (html.escape(f), html.escape(raison)), proj)
        PL.etat(seq, "A faire", proj)
        open("%s/%s.rendu" % (d, f), "w").write(raison[:200])
        print("  refus %s -> %s-%d remise en « A faire » : %s" % (f, proj, seq, raison[:70]))
        n += 1
    return n


def main():
    rendus = refuses()
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
        # ⚠️ 08/09 : les runs deposes AVANT la separation HMT/GYM n ont pas de
        # `plane_projet`. Ils viennent tous de HMT — c est le defaut, pas une devinette.
        proj = J.get("plane_projet", "HMT")
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
        PL.commenter(seq, corps, proj)
        if F.get("verdict") == "COMPLET":
            PL.etat(seq, "Fait", proj); etat = "Fait"
        else:
            PL.etat(seq, "A faire", proj); etat = "A faire (relance)"
        open(temoin, "w").write(F.get("verdict", "?"))
        print("  %s -> %s-%d : %s, tache %s" % (d, proj, seq, F.get("verdict"), etat))
        rendus += 1
    if not rendus:
        print("  aucun run neuf ni refus neuf a rendre")
    return 0


if __name__ == "__main__":
    sys.exit(main())
