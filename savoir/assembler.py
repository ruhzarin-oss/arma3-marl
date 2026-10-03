#!/usr/bin/env python3
"""ASSEMBLE toutes les fiches en un seul fichier /mnt/data/hmt/etat/cmo_savoir/fiches.jsonl et les vérifie :
identifiants uniques, champs obligatoires ( id, type, titre, texte, source, tags ), types connus, texte non vide.

Sources : fiches/db_*.jsonl ( fiches_db.py ), fiches/manuel_*.jsonl ( fiches_manuel.py ), et les fiches écrites à la
main ( ecrites_mecanismes.py, ecrites_atelier.py, commandement.py ).

    .venv312/bin/python savoir/assembler.py
"""
import collections
import glob
import json
import os
import statistics
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import commandement                                         # noqa: E402
import ecrites_atelier                                      # noqa: E402
import ecrites_mecanismes                                   # noqa: E402

DOSSIER = "/mnt/data/hmt/etat/cmo_savoir"
TYPES = {"plateforme", "arme", "capteur", "chargement", "mecanisme", "doctrine", "lua", "atelier", "regle"}
CHAMPS = ("id", "type", "titre", "texte", "source", "tags")


def main():
    fiches = [commandement.FICHE] + ecrites_mecanismes.FICHES + ecrites_atelier.FICHES
    for x in fiches:
        x["origine"] = "écrite à la main"
    for f in sorted(glob.glob(os.path.join(DOSSIER, "fiches", "*.jsonl"))):
        for l in open(f, encoding="utf-8"):
            if l.strip():
                x = json.loads(l)
                x["origine"] = os.path.basename(f)
                fiches.append(x)
    vus, erreurs = set(), []
    for x in fiches:
        x.setdefault("chiffres", {})
        for c in CHAMPS:
            if not x.get(c):
                erreurs.append(f"{x.get('id')} : champ {c} vide")
        if x["type"] not in TYPES:
            erreurs.append(f"{x['id']} : type {x['type']} inconnu")
        if x["id"] in vus:
            erreurs.append(f"{x['id']} : identifiant en double")
        vus.add(x["id"])
    if erreurs:
        print("\n".join(erreurs[:50]))
        sys.exit(f"{len(erreurs)} erreurs : fiches.jsonl NON écrit")
    with open(os.path.join(DOSSIER, "fiches.jsonl"), "w", encoding="utf-8") as f:
        for x in fiches:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    par_type = collections.Counter(x["type"] for x in fiches)
    par_origine = collections.Counter(x["origine"] for x in fiches)
    mots = [len(x["texte"].split()) for x in fiches]
    stats = {"total": len(fiches), "par_type": dict(par_type.most_common()), "par_origine": dict(par_origine.most_common()),
             "mots_mediane": statistics.median(mots), "mots_min": min(mots), "mots_max": max(mots)}
    json.dump(stats, open(os.path.join(DOSSIER, "fiches_stats.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
