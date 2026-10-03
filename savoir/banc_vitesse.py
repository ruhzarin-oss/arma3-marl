#!/usr/bin/env python3
"""Banc de VITESSE des encodeurs ( pas de qualité : aucune question de la porte n'est utilisée ) : fiches encodées par
seconde sur 2 fils, pour choisir le modèle selon une règle fixée d'avance : le plus gros modèle et la plus longue
fenêtre dont l'indexation complète tient en 45 min ( ordre : e5-base 256, e5-base 128, e5-small 256, e5-small 128 ).

    OMP_NUM_THREADS=2 taskset -c 0,1 nice -n 19 /mnt/data/hmt/savoir_env/bin/python savoir/banc_vitesse.py
"""
import json
import os
import random
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import indexer as I                                       # noqa: E402

CANDIDATS = [("intfloat/multilingual-e5-base", 256), ("intfloat/multilingual-e5-base", 128),
             ("intfloat/multilingual-e5-small", 256), ("intfloat/multilingual-e5-small", 128)]
BUDGET_S = 45 * 60


def main():
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(2)
    fiches = [json.loads(l) for l in open(os.path.join(I.DOSSIER, "fiches.jsonl"), encoding="utf-8")]
    ech = [I.texte_dense(f) for f in random.Random(7).sample(fiches, 96)]
    res, choix = [], None
    for modele, longueur in CANDIDATS:
        m = SentenceTransformer(modele, device="cpu")
        m.max_seq_length = longueur
        m.encode(ech[:8], batch_size=8)
        t0 = time.time()
        m.encode(ech, batch_size=32, normalize_embeddings=True)
        v = len(ech) / (time.time() - t0)
        total = len(fiches) / v
        res.append({"modele": modele, "longueur": longueur, "fiches_par_s": round(v, 2), "total_estime_min": round(total / 60, 1)})
        print(res[-1], flush=True)
        if choix is None and total <= BUDGET_S:
            choix = (modele, longueur)
            break
    print(json.dumps({"bancs": res, "choix": choix}, ensure_ascii=False))
    json.dump({"bancs": res, "choix": choix, "n_fiches": len(fiches)}, open(os.path.join(I.DOSSIER, "banc_vitesse.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
