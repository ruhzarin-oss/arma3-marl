"""LA BASE DE CONNAISSANCE, l index ( HMT-198, chantier K ) : chercher une fiche par les mots ( BM25 ) et par le sens
( bge-m3, en local par Ollama ), puis fondre les deux classements ( fusion des rangs reciproques, k = 60 ).

   python -m guerre.connaissance.index construire       les vecteurs de toutes les fiches ( une fois )
   python -m guerre.connaissance.index « question »     les 5 meilleures fiches"""
import json
import math
import os
import re
import sys
import unicodedata
import urllib.request
from collections import Counter

import numpy as np

DOSSIER = "/mnt/data/hmt/connaissance"
FICHES = os.path.join(DOSSIER, "fiches.jsonl")
VECTEURS = os.path.join(DOSSIER, "vecteurs.npy")
HOTE = os.environ.get("HMT_OLLAMA", "http://localhost:11434")
MODELE_SENS = "bge-m3"
K_RRF = 60
LOT = 32
TEXTE_VECTEUR = 2000                      # caracteres donnes au modele de sens par fiche
MOTS_VIDES = set("""a au aux avec ce ces cet cette d de des du elle en est et il ils je la le les leur lui ma mais me
meme mes moi mon ne ni nos notre nous on ou par pas pour qu que qui sa se ses si son sur ta te tes toi ton tu un une
vos votre vous y l s n c j m t quel quelle quels quelles comment combien quand est-ce dont lequel laquelle cela ca
fait faire sont etre avoir ont the of to and in is for on""".split())


def mots(texte):
    t = unicodedata.normalize("NFKD", texte.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    brut = re.findall(r"[a-z0-9_]+", t)
    out = []
    for w in brut:
        parts = [w] + ([x for x in w.split("_") if x] if "_" in w else [])
        for x in parts:
            if x in MOTS_VIDES or len(x) < 2: continue
            if len(x) > 4 and x.endswith("s"): x = x[:-1]          # un pluriel
            out.append(x)
    return out


def charger(fichier=FICHES):
    return [json.loads(l) for l in open(fichier, encoding="utf-8")]


def _texte_index(f):
    return f"{f['fichier']} {f['nom']} {f.get('contexte', '')} {f['texte']}"


class Index:
    def __init__(self, fiches, vecteurs=None, k1=1.4, b=0.75):
        self.fiches = fiches; self.k1, self.b = k1, b
        self.docs = [Counter(mots(_texte_index(f))) for f in fiches]
        self.long = np.array([sum(d.values()) for d in self.docs], np.float64)
        self.moy = float(self.long.mean()) if len(self.long) else 1.0
        df = Counter()
        for d in self.docs: df.update(d.keys())
        N = len(fiches)
        self.idf = {w: math.log(1.0 + (N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
        self.inverse = {}
        for i, d in enumerate(self.docs):
            for w, c in d.items(): self.inverse.setdefault(w, []).append((i, c))
        self.vecteurs = vecteurs

    def bm25(self, question):
        s = np.zeros(len(self.fiches))
        for w in set(mots(question)):
            idf = self.idf.get(w)
            if idf is None: continue
            for i, c in self.inverse[w]:
                s[i] += idf * c * (self.k1 + 1) / (c + self.k1 * (1 - self.b + self.b * self.long[i] / self.moy))
        return s

    def sens(self, question):
        if self.vecteurs is None: return None
        q = vecteurs([question])[0]
        return self.vecteurs @ q

    def chercher(self, question, k=5, mode="hybride"):
        """[ ( fiche, score ) ] : les k meilleures. mode : hybride, mots, sens."""
        sm = self.bm25(question) if mode in ("hybride", "mots") else None
        ss = self.sens(question) if mode in ("hybride", "sens") else None
        if mode == "mots": score = sm
        elif mode == "sens": score = ss
        else:
            score = np.zeros(len(self.fiches))
            for s in (sm, ss):
                if s is None: continue
                rang = np.empty(len(s), np.int64); rang[np.argsort(-s, kind="stable")] = np.arange(len(s))
                score += 1.0 / (K_RRF + 1 + rang)
        top = np.argsort(-score, kind="stable")[:k]
        return [(self.fiches[i], float(score[i])) for i in top]


def vecteurs(textes, modele=MODELE_SENS):
    """Les vecteurs normes ( bge-m3 par Ollama, /api/embed )."""
    out = []
    for a in range(0, len(textes), LOT):
        lot = [t[:TEXTE_VECTEUR] for t in textes[a:a + LOT]]
        req = urllib.request.Request(HOTE + "/api/embed", data=json.dumps({"model": modele, "input": lot}).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            e = json.loads(r.read())["embeddings"]
        out.extend(e)
    v = np.array(out, np.float32)
    v /= np.maximum(1e-9, np.linalg.norm(v, axis=1, keepdims=True))
    return v


def construire(fichier=FICHES, sortie=VECTEURS):
    fs = charger(fichier)
    v = vecteurs([_texte_index(f) for f in fs])
    np.save(sortie, v)
    print(len(fs), "fiches,", v.shape, "vecteurs ->", sortie)
    return v


def ouvrir(fichier=FICHES, vect=VECTEURS):
    fs = charger(fichier)
    v = np.load(vect) if os.path.exists(vect) else None
    if v is not None and len(v) != len(fs): v = None             # des vecteurs d une autre extraction : on n en veut pas
    return Index(fs, v)


if __name__ == "__main__":
    if sys.argv[1:] == ["construire"]: construire()
    else:
        I = ouvrir()
        for f, s in I.chercher(" ".join(sys.argv[1:])): print(f"{s:.4f}  {f['id']}  ({f['fichier']}:{f['ligne']})")
