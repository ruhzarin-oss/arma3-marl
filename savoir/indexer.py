#!/usr/bin/env python3
"""Construit l'INDEX de la base de connaissance à partir de /mnt/data/hmt/etat/cmo_savoir/fiches.jsonl :
  index/bm25.npz      liste inversée ( ptr, docs, tf ), longueurs, idf ;
  index/vocab.json    mot -> numéro ;
  index/embeddings.npy vecteurs des fiches ( float16, normalisés ) ;
  index/manifeste.json modèle, longueur, préfixes, nombre de fiches, empreinte du fichier.

Embeddings sur CPU SEULEMENT ( la 3090 est à Qwen ) et à 2 fils au plus ( la guerre CMO tourne sur la même station ) :
    OMP_NUM_THREADS=2 taskset -c 0,1 nice -n 19 /mnt/data/hmt/savoir_env/bin/python savoir/indexer.py \
        [--modele intfloat/multilingual-e5-small] [--longueur 256] [--sans-embeddings]
Le calcul des embeddings reprend où il s'était arrêté ( index/embeddings_partiel.npy ) si on le relance.
"""
import collections
import hashlib
import json
import os
import sys
import time

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import savoir as S                                         # noqa: E402

DOSSIER = S.DOSSIER
PREFIXE_FICHE, PREFIXE_QUESTION = "passage: ", "query: "   # convention des modèles e5


def texte_bm25(f):
    return " ".join([f["titre"]] * S.POIDS_TITRE + [f["texte"], " ".join(f.get("tags", [])), f.get("texte_en", "")])


def texte_dense(f):
    return PREFIXE_FICHE + f["titre"] + ". " + f["texte"]


def bm25(fiches, sortie):
    vocab, post = {}, collections.defaultdict(list)
    dl = np.zeros(len(fiches), dtype=np.int32)
    for d, f in enumerate(fiches):
        c = collections.Counter(S.tokens(texte_bm25(f)))
        dl[d] = sum(c.values())
        for t, n in c.items():
            j = vocab.setdefault(t, len(vocab))
            post[j].append((d, min(n, 65535)))
    n_doc = len(fiches)
    ptr = np.zeros(len(vocab) + 1, dtype=np.int64)
    docs, tf = [], []
    idf = np.zeros(len(vocab), dtype=np.float32)
    for j in range(len(vocab)):
        p = post[j]
        ptr[j + 1] = ptr[j] + len(p)
        docs.extend(x[0] for x in p)
        tf.extend(x[1] for x in p)
        df = len(p)
        idf[j] = np.log(1.0 + (n_doc - df + 0.5) / (df + 0.5))
    np.savez(os.path.join(sortie, "bm25.npz"), ptr=ptr, docs=np.asarray(docs, dtype=np.int32),
             tf=np.asarray(tf, dtype=np.uint16), dl=dl, idf=idf)
    json.dump(vocab, open(os.path.join(sortie, "vocab.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"BM25 : {n_doc} fiches, {len(vocab)} mots, {len(docs)} entrées, longueur moyenne {dl.mean():.0f}", flush=True)
    return len(vocab), len(docs)


def embeddings(fiches, sortie, modele, longueur, lot=32):
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    m = SentenceTransformer(modele, device="cpu")
    m.max_seq_length = longueur
    textes = [texte_dense(f) for f in fiches]
    ordre = np.argsort([len(t) for t in textes], kind="stable")      # lots de longueurs voisines : moins de remplissage
    partiel = os.path.join(sortie, "embeddings_partiel.npy")
    etat = os.path.join(sortie, "embeddings_partiel.json")
    dim = m.get_sentence_embedding_dimension()
    E = np.zeros((len(fiches), dim), dtype=np.float32)
    fait = 0
    if os.path.exists(partiel) and os.path.exists(etat):
        e = json.load(open(etat))
        if e.get("n") == len(fiches) and e.get("modele") == modele and e.get("longueur") == longueur:
            E = np.load(partiel).astype(np.float32)
            fait = e["fait"]
            print(f"reprise à {fait}/{len(fiches)}", flush=True)
    t0 = time.time()
    for a in range(fait, len(fiches), lot):
        idx = ordre[a:a + lot]
        E[idx] = m.encode([textes[i] for i in idx], normalize_embeddings=True, batch_size=lot)
        fait = min(a + lot, len(fiches))
        if (a // lot) % 25 == 0 or fait == len(fiches):
            np.save(partiel, E.astype(np.float16))
            json.dump({"n": len(fiches), "fait": fait, "modele": modele, "longueur": longueur}, open(etat, "w"))
            print(f"  {fait}/{len(fiches)} fiches, {time.time() - t0:.0f} s", flush=True)
    np.save(os.path.join(sortie, "embeddings.npy"), E.astype(np.float16))
    for p in (partiel, etat):
        if os.path.exists(p):
            os.remove(p)
    return dim


def main():
    modele = sys.argv[sys.argv.index("--modele") + 1] if "--modele" in sys.argv else "intfloat/multilingual-e5-small"
    longueur = int(sys.argv[sys.argv.index("--longueur") + 1]) if "--longueur" in sys.argv else 256
    chemin = os.path.join(DOSSIER, "fiches.jsonl")
    brut = open(chemin, "rb").read()
    fiches = [json.loads(l) for l in brut.decode("utf-8").splitlines() if l.strip()]
    sortie = os.path.join(DOSSIER, "index")
    os.makedirs(sortie, exist_ok=True)
    n_mots, n_entrees = bm25(fiches, sortie)
    man_chemin = os.path.join(sortie, "manifeste.json")
    ancien = json.load(open(man_chemin)) if os.path.exists(man_chemin) else {}
    man = {"modele": modele, "longueur": longueur, "prefixe_fiche": PREFIXE_FICHE, "prefixe_question": PREFIXE_QUESTION,
           "n_fiches": len(fiches), "sha256_fiches": hashlib.sha256(brut).hexdigest(), "bm25_mots": n_mots,
           "bm25_entrees": n_entrees, "bm25_k1": S.K1, "bm25_b": S.B, "poids_titre": S.POIDS_TITRE, "rrf_k": S.RRF_K,
           "date": time.strftime("%Y-%m-%d %H:%M:%S")}
    if "--sans-embeddings" in sys.argv:
        man.update({k: ancien[k] for k in ("modele", "longueur", "dim") if k in ancien})
    else:
        man["dim"] = embeddings(fiches, sortie, modele, longueur)
    json.dump(man, open(man_chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(man, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
