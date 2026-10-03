#!/usr/bin/env python3
"""ESSAI DE BOUT EN BOUT : une question -> fiches retrouvées ( savoir.rechercher ) + fiche de commandement -> Qwen local
( Ollama, qwen3.8:27b, celui qui est DÉJÀ chargé ) -> réponse. Mêmes options que cmo/chef_qwen.py ( pas de num_ctx :
ne jamais provoquer un rechargement du modèle ; keep_alive -1 ; think false ; stream false ; réponse courte ).

    .venv312/bin/python savoir/interroger_qwen.py "question 1" ["question 2" ...]
Sortie : /mnt/data/hmt/etat/cmo_savoir/essai_qwen.json
"""
import json
import os
import sys
import time
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import savoir as S                                         # noqa: E402

OLLAMA = "http://localhost:11434"
MODELE = "qwen3.8:27b"
SYSTEME = ("Tu es le chef d'état-major d'un camp dans Command: Modern Operations. Réponds en français, en 6 phrases au plus, "
           "UNIQUEMENT d'après les fiches fournies ; cite l'identifiant [id] de chaque fiche d'où vient un chiffre ; si les "
           "fiches ne suffisent pas, dis-le. Donne les portées en nm et en km.")


def modele_charge():
    with urllib.request.urlopen(OLLAMA + "/api/ps", timeout=10) as r:
        return [m["name"] for m in json.loads(r.read()).get("models", [])]


def demander(question, k=6):
    fiches = S.rechercher(question, k)
    c = S.commandement()
    ctx = [f"[{c['id']}] {c['titre']}\n{c['texte']}"] + [f"[{f['id']}] {f['titre']}\n{f['texte']}\nSource : {f['source']}"
                                                          for f in fiches if f["id"] != "commandement"]
    messages = [{"role": "system", "content": SYSTEME},
                {"role": "user", "content": "FICHES :\n\n" + "\n\n".join(ctx) + f"\n\nQUESTION : {question}"}]
    corps = json.dumps({"model": MODELE, "messages": messages, "stream": False, "keep_alive": -1, "think": False,
                        "options": {"temperature": 0.2, "num_predict": 450}}).encode()
    t0 = time.time()
    req = urllib.request.Request(OLLAMA + "/api/chat", data=corps, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        rep = json.loads(r.read())
    return {"question": question, "fiches": [f["id"] for f in fiches], "dense": fiches[0]["dense"] if fiches else None,
            "reponse": rep["message"]["content"], "duree_s": round(time.time() - t0, 1),
            "jetons_invite": rep.get("prompt_eval_count"), "jetons_reponse": rep.get("eval_count")}


if __name__ == "__main__":
    avant = modele_charge()
    if MODELE not in avant:
        sys.exit(f"{MODELE} n'est pas chargé ( {avant} ) : on ne charge pas un modèle pour un essai")
    out = {"date": time.strftime("%Y-%m-%d %H:%M:%S"), "modeles_avant": avant, "essais": []}
    for q in sys.argv[1:]:
        out["essais"].append(demander(q))
        print(json.dumps(out["essais"][-1], ensure_ascii=False, indent=1), flush=True)
    out["modeles_apres"] = modele_charge()
    json.dump(out, open(os.path.join(S.DOSSIER, "essai_qwen.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
