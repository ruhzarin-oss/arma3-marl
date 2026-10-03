#!/usr/bin/env python3
"""LA BASE DE CONNAISSANCE CMO de l'état-major ( Qwen ) : recherche HYBRIDE dans les fiches de
/mnt/data/hmt/etat/cmo_savoir/ ( fiches.jsonl, index/ ).

    from savoir import rechercher, fiche, commandement
    for f in rechercher("Quelle est la portée du missile Meteor ?", k=8):
        print(f["id"], f["titre"], f["score"])

Deux classements fusionnés par rang réciproque ( RRF, k = 60 ) :
  - BM25 sur les mots ( titre compté deux fois, texte, étiquettes, texte anglais du manuel ) ; les noms composés
    donnent aussi leurs préfixes collés ( « F-16CJ » -> f, f16, f16cj ; « AIM-120D » -> aim, aim120, aim120d ) ;
  - EMBEDDINGS ( modèle multilingue e5 du manifeste, cosinus ) : vecteurs des fiches précalculés ; la question est
    encodée soit dans ce processus ( si sentence_transformers est importable : venv /mnt/data/hmt/savoir_env ), soit
    par un PONT : un processus fils persistant /mnt/data/hmt/savoir_env/bin/python savoir/encodeur.py qui lit des
    questions en JSON sur son entrée et rend les vecteurs ( premier appel ≈ 5-15 s, ensuite ≈ 0,1 s ). C'est le cas
    depuis le venv du moteur ( /mnt/data/hmt/atelier-cmo/.venv312 ), qui n'a que numpy.
  Si l'encodeur échoue, la recherche continue en BM25 seul ( champ « dense » = False dans chaque résultat ).

Ne dépend que de numpy ( et de la bibliothèque standard ). Ligne de commande :
    .venv312/bin/python savoir/savoir.py "question" [k]
"""
import atexit
import json
import os
import re
import subprocess
import sys
import threading
import unicodedata

import numpy as np

DOSSIER = os.environ.get("SAVOIR_DOSSIER", "/mnt/data/hmt/etat/cmo_savoir")
PY_SAVOIR = os.environ.get("SAVOIR_PYTHON", "/mnt/data/hmt/savoir_env/bin/python")
ICI = os.path.dirname(os.path.abspath(__file__))
K1, B = 1.2, 0.75                     # BM25 classique
RRF_K = 60                            # fusion par rang réciproque
PROFONDEUR = 200                      # candidats retenus par chaque méthode avant fusion
POIDS_TITRE = 2                       # le titre compte deux fois dans BM25

STOP = set("""
a au aux avec ce ces cet cette d da dans de des du elle en et est etre eux il ils je l la le les leur leurs lui ma mais me
meme mes moi mon ne nos notre nous on ou par pas pour qu que quel quelle quelles quels qui sa sans se ses son sont sur ta
te tes toi ton tu un une vos votre vous y combien comment pourquoi quoi quand ou est-ce sont-ils peut peuvent faut doit
cela ca celui celle ceux the of and to in is are be for on with as by at an or from that this it its which what how
when who whom why do does did not can will would should may into than then there their these those has have had was were
""".split())
_TOK = re.compile(r"[a-z0-9]+(?:[-/.+][a-z0-9]+)*")
_FRONT = re.compile(r"[a-z]+|[0-9]+")


def normaliser(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _racine(t):
    if t.isalpha() and len(t) > 4 and t[-1] in "sx":
        return t[:-1]
    return t


def tokens(s):
    """Les mots d'un texte : minuscules sans accents, mots vides retirés, pluriels simples ramenés au singulier ; un nom
    composé ou mêlé de chiffres ( « F-16CJ », « 9M723 » ) donne ses morceaux et ses préfixes collés."""
    out = []
    for m in _TOK.finditer(normaliser(s)):
        t = m.group(0)
        morceaux = [x for p in re.split(r"[-/.+]", t) for x in _FRONT.findall(p)]
        if len(morceaux) > 1:
            acc = ""
            for x in morceaux:
                acc += x
                if acc != x:
                    out.append(acc)
        for x in morceaux:
            if x and x not in STOP:
                out.append(_racine(x))
    return out


# ==================================================================================================== l'index
class Index:
    def __init__(self, dossier=DOSSIER):
        self.dossier = dossier
        self.fiches = [json.loads(l) for l in open(os.path.join(dossier, "fiches.jsonl"), encoding="utf-8")]
        self.ids = [f["id"] for f in self.fiches]
        self.rang = {i: k for k, i in enumerate(self.ids)}
        d = np.load(os.path.join(dossier, "index", "bm25.npz"))
        self.ptr, self.docs, self.tf, self.dl = d["ptr"], d["docs"], d["tf"], d["dl"].astype(np.float32)
        self.avgdl = float(self.dl.mean())
        self.idf = d["idf"]
        self.vocab = json.load(open(os.path.join(dossier, "index", "vocab.json"), encoding="utf-8"))
        self.manifeste = json.load(open(os.path.join(dossier, "index", "manifeste.json"), encoding="utf-8"))
        chemin = os.path.join(dossier, "index", "embeddings.npy")
        self.emb = np.load(chemin).astype(np.float32) if os.path.exists(chemin) else None
        if self.emb is not None and self.emb.shape[0] != len(self.fiches):
            raise RuntimeError(f"embeddings ( {self.emb.shape[0]} ) et fiches ( {len(self.fiches)} ) ne correspondent pas")

    def bm25(self, question, n=PROFONDEUR):
        score = np.zeros(len(self.fiches), dtype=np.float32)
        for t in set(tokens(question)):
            j = self.vocab.get(t)
            if j is None:
                continue
            a, b = self.ptr[j], self.ptr[j + 1]
            docs, tf = self.docs[a:b], self.tf[a:b].astype(np.float32)
            score[docs] += self.idf[j] * tf * (K1 + 1) / (tf + K1 * (1 - B + B * self.dl[docs] / self.avgdl))
        n = min(n, int((score > 0).sum()))
        if n == 0:
            return np.zeros(0, dtype=np.int64), score
        top = np.argpartition(-score, n - 1)[:n]
        return top[np.argsort(-score[top], kind="stable")], score

    def dense(self, vecteur, n=PROFONDEUR):
        sim = self.emb @ vecteur
        top = np.argpartition(-sim, n - 1)[:n]
        return top[np.argsort(-sim[top], kind="stable")], sim


_INDEX = None
_VERROU = threading.Lock()


def charger(dossier=DOSSIER):
    global _INDEX
    with _VERROU:
        if _INDEX is None or _INDEX.dossier != dossier:
            _INDEX = Index(dossier)
    return _INDEX


# ==================================================================================================== l'encodeur
class _EncodeurLocal:
    def __init__(self, modele, longueur):
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "2")))
        self.m = SentenceTransformer(modele, device="cpu")
        self.m.max_seq_length = longueur

    def encoder(self, textes):
        return np.asarray(self.m.encode(textes, normalize_embeddings=True, batch_size=16), dtype=np.float32)


class _EncodeurPont:
    """Le processus fils persistant ( savoir_env ) : une ligne JSON par requête, une ligne JSON par réponse."""

    def __init__(self):
        env = dict(os.environ, OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2",
                   TOKENIZERS_PARALLELISM="false", HF_HOME="/mnt/data/hmt/savoir_env/hf", HF_HUB_OFFLINE="1")
        self.p = subprocess.Popen(["nice", "-n", "10", PY_SAVOIR, os.path.join(ICI, "encodeur.py"), "--dossier", charger().dossier],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env, text=True,
                                  bufsize=1)
        pret = json.loads(self.p.stdout.readline())
        if not pret.get("pret"):
            raise RuntimeError(f"encodeur : {pret}")
        atexit.register(self.fermer)

    def encoder(self, textes):
        self.p.stdin.write(json.dumps({"textes": textes}, ensure_ascii=False) + "\n")
        self.p.stdin.flush()
        r = json.loads(self.p.stdout.readline())
        if "vecteurs" not in r:
            raise RuntimeError(f"encodeur : {r}")
        return np.asarray(r["vecteurs"], dtype=np.float32)

    def fermer(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


_ENC = None


def encodeur():
    """L'encodeur des questions : dans ce processus si possible, sinon le pont vers savoir_env."""
    global _ENC
    if _ENC is None:
        man = charger().manifeste
        try:
            _ENC = _EncodeurLocal(man["modele"], man["longueur"])
        except ImportError:
            _ENC = _EncodeurPont()
    return _ENC


def vecteur_question(question):
    return encodeur().encoder([charger().manifeste["prefixe_question"] + question])[0]


# ==================================================================================================== la recherche
def classer(question, mode="hybride", profondeur=PROFONDEUR):
    """[ ( position, score ) ] du meilleur au moins bon ; positions dans index.fiches. Rend aussi si le dense a servi."""
    ix = charger()
    rangs_b, _ = ix.bm25(question, profondeur) if mode in ("hybride", "bm25") else (np.zeros(0, dtype=np.int64), None)
    dense_ok = False
    rangs_d = np.zeros(0, dtype=np.int64)
    if mode in ("hybride", "dense") and ix.emb is not None:
        try:
            rangs_d, _ = ix.dense(vecteur_question(question), profondeur)
            dense_ok = True
        except Exception as e:                           # BM25 seul plutôt que rien
            print(f"[savoir] encodeur indisponible ( {e} ) : BM25 seul", file=sys.stderr)
    score = {}
    for liste in (rangs_b, rangs_d):
        for r, pos in enumerate(liste):
            score[int(pos)] = score.get(int(pos), 0.0) + 1.0 / (RRF_K + r + 1)
    return sorted(score.items(), key=lambda x: (-x[1], x[0])), dense_ok


def rechercher(question: str, k: int = 8, mode: str = "hybride") -> list:
    """Les k fiches les plus pertinentes pour la question ( français ou anglais ). Chaque résultat est la fiche
    complète ( id, type, titre, texte, source, tags, chiffres ) plus « score » ( RRF ), « rang » et « dense »
    ( True si les embeddings ont servi ). mode : « hybride » ( défaut ), « bm25 » ou « dense »."""
    ix = charger()
    classes, dense_ok = classer(question, mode)
    out = []
    for r, (pos, s) in enumerate(classes[:k], 1):
        f = dict(ix.fiches[pos])
        f.update(score=round(s, 5), rang=r, dense=dense_ok)
        out.append(f)
    return out


def fiche(fid):
    ix = charger()
    return ix.fiches[ix.rang[fid]] if fid in ix.rang else None


def commandement():
    """La fiche de commandement, toujours jointe au contexte de Qwen."""
    return fiche("commandement")


def contexte(question, k=8, mots_max=None):
    """Le texte prêt à donner à Qwen : la fiche de commandement puis les k fiches retrouvées, chacune avec son id et sa
    source."""
    morceaux = []
    c = commandement()
    if c:
        morceaux.append(f"[{c['id']}] {c['titre']}\n{c['texte']}\nSource : {c['source']}")
    for f in rechercher(question, k):
        if f["id"] == "commandement":
            continue
        morceaux.append(f"[{f['id']}] {f['titre']}\n{f['texte']}\nSource : {f['source']}")
    return "\n\n".join(morceaux)


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Quelle est la portée du missile Meteor ?"
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    for f in rechercher(q, k):
        print(f"{f['rang']:2d} {f['score']:.4f} {'D' if f['dense'] else '-'} {f['id']:28s} {f['titre'][:90]}")
