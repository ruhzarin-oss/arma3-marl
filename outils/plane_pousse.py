#!/usr/bin/env python3
"""PLANE -> FILE. Prend la prochaine tache prete et la depose dans la file d execution.

Une tache est PRETE si : etat « A faire » · etiquette `run` · sa description contient un bloc
    ```json { "banc": ..., "graines": [...], "instance": N, "plafond_s": S }
Le job ecrit porte `plane` = le numero de la tache : c est ce numero qui permettra au retour
de savoir a qui rendre le verdict.

⚠️ NE TOUCHE PAS `file.sh`. Le pont est DECOUPLE : Plane remplit la file, `file.sh` la vide,
et rien ne change dans le chemin d execution deja eprouve. Un job depose a la main continue
de marcher exactement comme avant, sans Plane.

⚠️ NE DEPOSE RIEN si la file n est pas vide ou si un job tourne : `file.sh` n en avale qu un
a la fois, et empiler ici ne ferait qu ordonner a l aveugle.
"""
import json, os, re, sys, datetime, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plane_orm as PL

H = "/mnt/data/hmt"
CHAMPS = ("banc", "graines", "instance", "plafond_s")


def specs(html_desc):
    """Le bloc de job dans la description. On accepte ```json ... ``` ou un objet nu."""
    t = re.sub(r"<[^>]+>", "\n", html_desc or "")
    t = html.unescape(t)
    for m in re.finditer(r"\{[^{}]*\"banc\"[^{}]*\}", t, re.S):
        try:
            return json.loads(m.group(0))
        except Exception:
            continue
    return None


def main():
    if os.listdir(H + "/queue/en_cours"):
        print("  un job tourne deja — rien depose"); return 0
    if [f for f in os.listdir(H + "/queue") if f.endswith(".json")]:
        print("  la file n est pas vide — rien depose"); return 0

    pretes = []
    for t in PL.taches(etat="A faire", etiquette="run"):
        s = specs(t["html"])
        if not s:
            continue
        manque = [c for c in CHAMPS if c not in s]
        if manque:
            print("  HMT-%d ignoree : champs manquants %s" % (t["seq"], manque)); continue
        if len(set(s["graines"])) < 2:
            print("  HMT-%d ignoree : il faut au moins deux graines distinctes" % t["seq"]); continue
        pretes.append((t, s))

    if not pretes:
        print("  aucune tache prete (etat « A faire », etiquette `run`, bloc json valide)"); return 0

    t, s = pretes[0]                      # la plus ancienne : le numero fait l ordre
    s["plane"] = t["seq"]
    s.setdefault("note", "depuis Plane HMT-%d : %s" % (t["seq"], t["nom"][:80]))
    nom = "%s_HMT-%d_%s.json" % (datetime.date.today().isoformat(), t["seq"], s["banc"])
    chem = "%s/queue/%s" % (H, nom)
    json.dump(s, open(chem, "w"), ensure_ascii=False)
    os.chmod(chem, 0o644)
    PL.etat(t["seq"], "En cours")
    PL.commenter(t["seq"], "<p>Job depose dans la file : <code>%s</code><br>%s</p>"
                 % (nom, html.escape(json.dumps(s, ensure_ascii=False))))
    print("  depose %s  ->  HMT-%d passe En cours" % (nom, t["seq"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
