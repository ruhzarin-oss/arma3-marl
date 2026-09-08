#!/usr/bin/env python3
"""PLANE -> FILE. Prend la prochaine tache prete et la depose dans la file d execution.

Une tache est PRETE si : etat « A faire » · etiquette `run` · sa description contient un bloc
    ```json { "banc": ..., "graines": [...], "instance": N, "plafond_s": S }
Le job ecrit porte `plane` = le numero de la tache et `plane_projet` = son projet (HMT ou GYM) :
c est ce couple qui permettra au retour de savoir a qui rendre le verdict.

⚠️ NE TOUCHE PAS `file.sh` / `file2.sh`. Le pont est DECOUPLE : Plane remplit la file, la file
la vide, et rien ne change dans le chemin d execution deja eprouve. Un job depose a la main
continue de marcher exactement comme avant, sans Plane.

⚠️ 08/09 — LE VERROU EST PAR INSTANCE, PLUS GLOBAL. L ancien code refusait de deposer des
qu un job tournait, n importe lequel : une mesure du gymnase attendait des heures derriere une
mesure HARMATTAN qui ne la concernait pas. Une instance Arma est occupee si un job la vise
DEJA — en cours ou en attente ; les autres restent libres. Ce verrou doit dire la meme chose
que celui de `file2.sh`, sinon le pont empile ce que la file refusera d avaler.
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


def instances_occupees():
    """Les instances Arma deja visees par un job — en cours d execution ou en attente.
    Un job illisible compte comme occupant TOUTES les instances : on ne devine pas."""
    occ = set()
    for d in (H + "/queue/en_cours", H + "/queue"):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith(".json"):
                continue
            try:
                occ.add(json.load(open(os.path.join(d, f))).get("instance"))
            except Exception:
                print("  ⚠️ %s/%s illisible — toutes les instances tenues pour occupees" % (d, f))
                return None
    return occ


def main():
    occ = instances_occupees()
    if occ is None:
        return 0

    pretes = []
    for t in PL.taches(etat="A faire", etiquette="run"):
        s = specs(t["html"])
        if not s:
            continue
        manque = [c for c in CHAMPS if c not in s]
        if manque:
            print("  %s-%d ignoree : champs manquants %s" % (t["projet"], t["seq"], manque)); continue
        if len(set(s["graines"])) < 2:
            print("  %s-%d ignoree : il faut au moins deux graines distinctes"
                  % (t["projet"], t["seq"])); continue
        pretes.append((t, s))

    if not pretes:
        print("  aucune tache prete (etat « A faire », etiquette `run`, bloc json valide)"); return 0

    choisi = None
    for t, s in pretes:                   # la plus ancienne d abord : le numero fait l ordre
        if s["instance"] in occ:
            print("  %s-%d attend : l instance %s est occupee" % (t["projet"], t["seq"], s["instance"]))
            continue
        choisi = (t, s); break
    if not choisi:
        print("  toutes les taches pretes visent une instance occupee — rien depose"); return 0

    t, s = choisi
    s["plane"] = t["seq"]
    s["plane_projet"] = t["projet"]
    s.setdefault("note", "depuis Plane %s-%d : %s" % (t["projet"], t["seq"], t["nom"][:70]))
    nom = "%s_%s-%d_%s.json" % (datetime.date.today().isoformat(), t["projet"], t["seq"], s["banc"])
    chem = "%s/queue/%s" % (H, nom)
    json.dump(s, open(chem, "w"), ensure_ascii=False)
    os.chmod(chem, 0o644)
    PL.etat(t["seq"], "En cours", t["projet"])
    PL.commenter(t["seq"], "<p>Job depose dans la file : <code>%s</code> (instance %s)<br>%s</p>"
                 % (nom, s["instance"], html.escape(json.dumps(s, ensure_ascii=False))), t["projet"])
    print("  depose %s  ->  %s-%d passe En cours" % (nom, t["projet"], t["seq"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
