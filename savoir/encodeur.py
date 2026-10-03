#!/usr/bin/env python3
"""Le PONT d'encodage des questions ( venv /mnt/data/hmt/savoir_env ) : processus persistant lancé par savoir.py
quand le venv appelant n'a pas sentence_transformers. Protocole : il écrit {"pret": true, "modele": …} puis, pour chaque
ligne JSON {"textes": [...]} reçue sur son entrée, une ligne JSON {"vecteurs": [[...], ...]} ( vecteurs normalisés ).

    /mnt/data/hmt/savoir_env/bin/python savoir/encodeur.py [--dossier /mnt/data/hmt/etat/cmo_savoir]
"""
import json
import os
import sys


def main():
    dossier = sys.argv[sys.argv.index("--dossier") + 1] if "--dossier" in sys.argv else "/mnt/data/hmt/etat/cmo_savoir"
    os.environ.setdefault("HF_HOME", "/mnt/data/hmt/savoir_env/hf")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    try:
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))
        man = json.load(open(os.path.join(dossier, "index", "manifeste.json"), encoding="utf-8"))
        m = SentenceTransformer(man["modele"], device="cpu")
        m.max_seq_length = man["longueur"]
    except Exception as e:                                  # le parent passera en BM25 seul
        print(json.dumps({"pret": False, "erreur": repr(e)}), flush=True)
        return
    print(json.dumps({"pret": True, "modele": man["modele"]}), flush=True)
    for ligne in sys.stdin:
        try:
            textes = json.loads(ligne)["textes"]
            v = m.encode(textes, normalize_embeddings=True, batch_size=16)
            print(json.dumps({"vecteurs": [[round(float(x), 6) for x in r] for r in v]}), flush=True)
        except Exception as e:
            print(json.dumps({"erreur": repr(e)}), flush=True)


if __name__ == "__main__":
    main()
