#!/usr/bin/env python3
"""LA PORTE de la base de connaissance CMO : critères écrits AVANT la mesure dans
/mnt/data/hmt/etat/cmo_savoir/CRITERES.md, questions dans porte_questions.jsonl ( questions_porte.py ).

Mesures ( k = 8 ) :
  C1  rappel@8 sur les questions ( au moins une fiche attendue dans les 8 premières )     >= 0,85
  C2  MRR@8 ( 1 / rang de la première fiche attendue, 0 si absente des 8 )                >= 0,60
  C3  CONTRÔLE POSITIF : le titre exact d'une fiche, pour 300 fiches tirées au sort
      ( graine 2026, toutes origines, au prorata ), retrouve cette fiche ( ou une fiche au titre identique ) >= 0,98
  C4  CONTRÔLE NÉGATIF : mêmes questions sur un index aux textes MÉLANGÉS entre fiches
      ( permutation aléatoire, graine 2026 : la fiche i reçoit le texte de la fiche π(i) )  rappel@8 <= 0,20
  C5  toutes les fiches attendues existent dans l'index ( sinon la porte échoue )
Diagnostics ( non critères ) : BM25 seul, embeddings seuls, résultats par catégorie, questions manquées.

Rien n'est réglé sur ces questions : modèle, longueur, k1, b, poids du titre, RRF k sont fixés dans savoir.py /
indexer.py avant la mesure.

    /mnt/data/hmt/savoir_env/bin/python savoir/porte_savoir.py   ( 2 fils, taskset -c 0,1, nice -n 19 )
Sorties : porte_resultats.json et le tableau imprimé ( VERDICT.md est écrit à la main d'après ces chiffres ).
"""
import collections
import json
import os
import random
import sys
import time

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import savoir as S                                         # noqa: E402

K = 8
SEUILS = {"C1_rappel": 0.85, "C2_mrr": 0.60, "C3_positif": 0.98, "C4_negatif": 0.20}
GRAINE = 2026
N_POSITIF = 300


def mesurer(questions, classer, ids_de):
    """( rappel@K, MRR@K, détails ) ; classer(question) -> positions ; ids_de(position) -> id."""
    touches, rr, det = 0, 0.0, []
    for q in questions:
        att = set(q["attendues"])
        rangs = [ids_de(p) for p in classer(q["question"])[:K]]
        r = next((i + 1 for i, x in enumerate(rangs) if x in att), None)
        touches += r is not None
        rr += 1.0 / r if r else 0.0
        det.append({"id": q["id"], "categorie": q["categorie"], "rang": r, "top3": rangs[:3]})
    n = max(1, len(questions))
    return touches / n, rr / n, det


def main():
    t0 = time.time()
    ix = S.charger()
    questions = [json.loads(l) for l in open(os.path.join(S.DOSSIER, "porte_questions.jsonl"), encoding="utf-8")]
    absentes = sorted({a for q in questions for a in q["attendues"] if a not in ix.rang})
    res = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "n_questions": len(questions), "n_fiches": len(ix.fiches),
           "manifeste": ix.manifeste, "k": K, "seuils": SEUILS, "C5_attendues_absentes": absentes}

    cache = {}

    def classer(mode):
        def f(question):
            cle = (mode, question)
            if cle not in cache:
                cache[cle] = [p for p, _ in S.classer(question, mode)[0]]
            return cache[cle]
        return f

    normal = lambda p: ix.ids[p]                            # noqa: E731
    # C1, C2 : hybride
    r, m, det = mesurer(questions, classer("hybride"), normal)
    res.update(C1_rappel=round(r, 4), C2_mrr=round(m, 4), details=det)
    # diagnostics
    for mode in ("bm25", "dense"):
        r2, m2, _ = mesurer(questions, classer(mode), normal)
        res[f"diag_{mode}"] = {"rappel": round(r2, 4), "mrr": round(m2, 4)}
    par_cat = collections.defaultdict(list)
    for d in det:
        par_cat[d["categorie"]].append(d["rang"] is not None)
    res["par_categorie"] = {c: {"n": len(v), "rappel": round(sum(v) / len(v), 3)} for c, v in sorted(par_cat.items())}
    res["manquees"] = [{"id": d["id"], "question": next(q["question"] for q in questions if q["id"] == d["id"]),
                        "top3": d["top3"]} for d in det if d["rang"] is None]
    # C3 : contrôle positif ( titres exacts )
    rnd = random.Random(GRAINE)
    tirage = rnd.sample(range(len(ix.fiches)), N_POSITIF)
    meme_titre = collections.defaultdict(set)
    for f in ix.fiches:
        meme_titre[f["titre"]].add(f["id"])
    qpos = [{"id": f"pos-{ix.ids[p]}", "categorie": ix.fiches[p]["type"], "question": ix.fiches[p]["titre"],
             "attendues": sorted(meme_titre[ix.fiches[p]["titre"]])} for p in tirage]
    r3, m3, det3 = mesurer(qpos, classer("hybride"), normal)
    res.update(C3_positif=round(r3, 4), C3_mrr=round(m3, 4), C3_ratees=[d["id"] for d in det3 if d["rang"] is None])
    # C4 : contrôle négatif ( textes mélangés entre fiches )
    perm = np.random.RandomState(GRAINE).permutation(len(ix.fiches))
    melange = lambda p: ix.ids[perm[p]]                     # noqa: E731
    r4, m4, _ = mesurer(questions, classer("hybride"), melange)
    res.update(C4_negatif=round(r4, 4), C4_mrr=round(m4, 4))
    res["verdicts"] = {
        "C1": res["C1_rappel"] >= SEUILS["C1_rappel"],
        "C2": res["C2_mrr"] >= SEUILS["C2_mrr"],
        "C3": res["C3_positif"] >= SEUILS["C3_positif"],
        "C4": res["C4_negatif"] <= SEUILS["C4_negatif"],
        "C5": not absentes,
    }
    res["porte"] = all(res["verdicts"].values())
    res["duree_s"] = round(time.time() - t0, 1)
    json.dump(res, open(os.path.join(S.DOSSIER, "porte_resultats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("n_questions", "n_fiches", "C1_rappel", "C2_mrr", "C3_positif", "C3_mrr", "C4_negatif",
                                         "diag_bm25", "diag_dense", "par_categorie", "verdicts", "porte", "duree_s")},
                     ensure_ascii=False, indent=1))
    print("MANQUÉES :")
    for x in res["manquees"]:
        print(f"  {x['id']} {x['question']} -> {x['top3']}")
    print("C3 ratées :", res["C3_ratees"][:20])


if __name__ == "__main__":
    main()
