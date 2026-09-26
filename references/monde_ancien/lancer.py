"""Fait vivre le monde N jours, hors d Arma ( etape E1 ), et ecrit son journal.
   python -m monde.lancer --jours 3 --gouvernement llm --eleve llm --sortie /mnt/data/hmt/monde/essai
Instantane : le monde entier est sauve chaque jour ( pickle ) ; --reprendre repart du dernier."""
import argparse, json, os, pickle, sys, time
from . import monde as W, ecole as S, config as C

p = argparse.ArgumentParser()
p.add_argument("--jours", type=int, default=3)
p.add_argument("--gouvernement", choices=["regles", "llm"], default="regles")
p.add_argument("--eleve", choices=["aucun", "sans_memoire", "memoire", "llm", "llm_sans_notes"], default="memoire")
p.add_argument("--sortie", default="/mnt/data/hmt/monde/essai")
p.add_argument("--reprendre", action="store_true")
a = p.parse_args()
os.makedirs(a.sortie, exist_ok=True)
inst = os.path.join(a.sortie, "instantane.pkl")
if a.reprendre and os.path.exists(inst):
    w = pickle.load(open(inst, "rb")); print("repris au jour", w.jour)
else:
    eleve = {"aucun": None, "sans_memoire": S.EleveSansMemoire(), "memoire": S.EleveMemoire(), "llm": S.EleveLLM(),
             "llm_sans_notes": S.EleveLLM(sans_notes=True)}[a.eleve]
    w = W.Monde(cerveau=a.gouvernement, eleve=eleve, journal=os.path.join(a.sortie, "journal.jsonl"))
t0 = time.time()
for j in range(a.jours):
    for _ in range(C.PAS_PAR_JOUR): w.pas_suivant()
    pickle.dump(w, open(inst + ".tmp", "wb")); os.replace(inst + ".tmp", inst)
    r = w.resume_jour()
    print(f"jour {w.jour} ( {time.time() - t0:.0f} s ) : {json.dumps(r, ensure_ascii=False)}", flush=True)
d_arg, d_b = w.verifier_conservation()
print("conservation : argent", round(d_arg, 6), "biens", {k: round(v, 6) for k, v in d_b.items() if abs(v) > 1e-6})
if w.ecole: print("bulletin :", [(b["jour"], round(b["score"], 2)) for b in w.ecole.bulletin])
