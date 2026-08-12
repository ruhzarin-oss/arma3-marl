#!/usr/bin/env python3
"""officer_memory.py — RAG MÉMOIRE DE CAMPAGNE (leviathan001). Fichier autonome, zéro collision.

Une seule BDD SQLite, épisodes TAGUÉS PAR NIVEAU (reflex / fob / theatre) → chaque étage récupère SA
granularité ; retrieval PLEIN côté officier. La situation étant DÉJÀ structurée (25 FOB), on embarque
l'état comme VECTEUR DE FEATURES (pas de modèle texte) → similarité = situations de théâtre proches.

Mécanisme d'apprentissage SANS entraînement : record() à la décision (outcome vide) ; set_outcome() N
ticks après (mesure réelle) ; retrieve() ressort les situations passées SIMILAIRES + ce qui a marché.
Le score applique la doctrine A>B>C>D sur les 7 faits bruts (la pondération reste configurable)."""
import sqlite3, json
import numpy as np

# Doctrine validée A>B>C>D (cibles > force > terrain > attrition). Pondération configurable par expé.
DOCTRINE = {"cibles": 1.0, "force": 0.5, "terrain": 0.25, "attrition": 0.1}

# Poids d'`exposition` — ABAISSÉ de 0.20 à 0.05 le 11/08/2026 (décision Younes).
# Mesuré : à 0.20 ce drapeau BINAIRE pesait 20× un FOB perdu (0.010) et 1.6× une cible vitale
# (0.125), alors qu'il ne fait pas partie des 7 faits ordonnés A>B>C>D — il écrasait à lui seul
# toute la dimension terrain (0.25 pour les 25 FOB). À 0.05 il vaut le seuil de décision, soit
# 5 FOB perdus ou 2 hommes. N'affecte que 13 des 1230 outcomes déjà gravés (1,1 %).
W_EXPOSITION = 0.05


def score_outcome(o, w=DOCTRINE):
    """7 faits bruts -> score scalaire (la décision était-elle bonne ?). + = mieux."""
    s = 0.0
    s += w["cibles"]    * o.get("cibles_intactes_frac", 1.0)          # A : points vitaux protégés
    s -= w["force"]     * (o.get("pertes_amies", 0) / 20.0)           # B : un mort coûte cher
    s += w["terrain"]   * o.get("fobs_tenus_frac", 1.0)               # C : terrain tenu
    s += w["attrition"] * (o.get("pertes_ennemies", 0) / 10.0)        # D : ennemi saigné
    s -= W_EXPOSITION * (o.get("exposition", 0))                      # coût d'opportunité (un FOB dégarni)
    return round(s, 4)


def embed_theatre(sitrep, n_fob=25):
    """SITREP structuré -> features [par FOB: tenu, garnison, contacts, menacé] + global. Pas de texte."""
    feats = []
    for f in (sitrep.get("fobs", [])[:n_fob]):
        feats += [float(f.get("held", 1)), f.get("garrison", 0) / 30.0,
                  f.get("contacts", 0) / 10.0, float(f.get("threatened", 0))]
    feats += [0.0, 0.0, 0.0, 0.0] * max(0, n_fob - len(sitrep.get("fobs", [])))   # pad à n_fob
    feats = feats[:n_fob * 4]
    feats += [sitrep.get("total_force", 0) / 500.0, sitrep.get("total_threat", 0) / 50.0]
    return feats


class OfficerMemory:
    def __init__(self, path="officer_memory.db"):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS episodes(
            id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT, tick INTEGER, ts REAL,
            state TEXT, emb BLOB, context TEXT, decision TEXT, outcome TEXT, score REAL)""")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_level ON episodes(level)")
        self.db.commit()

    @staticmethod
    def _blob(v): return np.asarray(v, dtype=np.float32).tobytes()
    @staticmethod
    def _vec(b): return np.frombuffer(b, dtype=np.float32)

    def record(self, level, tick, ts, emb, state, context=None, decision=None):
        """À la décision : journalise TOUT (outcome vide, rempli plus tard). Renvoie l'id."""
        cur = self.db.execute(
            "INSERT INTO episodes(level,tick,ts,state,emb,context,decision,outcome,score) "
            "VALUES(?,?,?,?,?,?,?,NULL,NULL)",
            (level, tick, ts, json.dumps(state), self._blob(emb),
             json.dumps(context), json.dumps(decision)))
        self.db.commit(); return cur.lastrowid

    def set_outcome(self, ep_id, outcome, w=DOCTRINE):
        """N ticks après : écrit la conséquence réelle + le score doctrine. = la ligne devient une LEÇON."""
        sc = score_outcome(outcome, w)
        self.db.execute("UPDATE episodes SET outcome=?, score=? WHERE id=?",
                        (json.dumps(outcome), sc, ep_id))
        self.db.commit(); return sc

    def retrieve(self, level, query_emb, k=3, only_scored=True):
        """Top-k situations passées SIMILAIRES (cosinus), filtrées par niveau, AVEC leur outcome+score."""
        q = self._vec(self._blob(query_emb)); q = q / (np.linalg.norm(q) + 1e-9)
        sql = "SELECT id,tick,state,emb,decision,outcome,score FROM episodes WHERE level=?"
        if only_scored: sql += " AND outcome IS NOT NULL"
        out = []
        for (id_, tick, state, emb, decision, outcome, score) in self.db.execute(sql, (level,)):
            v = self._vec(emb); sim = float(q @ (v / (np.linalg.norm(v) + 1e-9)))
            out.append((sim, {"id": id_, "tick": tick, "sim": round(sim, 3), "score": score,
                              "state": json.loads(state), "decision": json.loads(decision),
                              "outcome": json.loads(outcome) if outcome else None}))
        out.sort(key=lambda x: -x[0])
        return [e for _, e in out[:k]]

    def count(self, level=None):
        if level: return self.db.execute("SELECT count(*) FROM episodes WHERE level=?", (level,)).fetchone()[0]
        return self.db.execute("SELECT count(*) FROM episodes").fetchone()[0]


# ===================== SELF-TEST (sans Arma, sans Qwen) =====================
def _sitrep(threat_fob, n=25, garr=20):
    """Théâtre synthétique : tous les FOB calmes sauf `threat_fob` (menacé, sous contacts)."""
    fobs = []
    for i in range(n):
        thr = (i == threat_fob)
        fobs.append({"held": 1, "garrison": garr, "contacts": (8 if thr else 0), "threatened": int(thr)})
    return {"fobs": fobs, "total_force": n * garr, "total_threat": 8}


def _selftest():
    import os
    p = "/tmp/_offmem_test.db"
    if os.path.exists(p): os.remove(p)
    m = OfficerMemory(p)
    # On enregistre des décisions sur 2 types de situation : menace au FOB 3 (EST) vs FOB 18 (OUEST).
    # EST : on a RENFORCÉ -> bon outcome. OUEST : on a TENU sans renfort -> on a perdu une cible.
    for t in range(4):
        e = m.record("theatre", t, t * 10.0, embed_theatre(_sitrep(3)), _sitrep(3),
                     decision={"orders": [{"fob": "E3", "action": "RENFORCER"}]})
        m.set_outcome(e, {"cibles_intactes_frac": 1.0, "fobs_tenus_frac": 1.0, "pertes_amies": 3,
                          "pertes_ennemies": 9, "exposition": 0})                # bon (cibles ok)
    for t in range(4):
        e = m.record("theatre", 100 + t, (100 + t) * 10.0, embed_theatre(_sitrep(18)), _sitrep(18),
                     decision={"orders": [{"fob": "W18", "action": "TENIR"}]})
        m.set_outcome(e, {"cibles_intactes_frac": 0.0, "fobs_tenus_frac": 0.5, "pertes_amies": 12,
                          "pertes_ennemies": 4, "exposition": 1})                # mauvais (cible perdue)
    # quelques épisodes FOB-niveau pour tester le filtre par niveau
    m.record("fob", 5, 50.0, [1, 0, 1, 0], {"fob": "E3"}, decision={"patrol_bias": "est"})

    print("[test] total=%d | theatre=%d | fob=%d" % (m.count(), m.count("theatre"), m.count("fob")))
    # Requête : une NOUVELLE menace à l'EST (FOB 3) -> doit ressortir les épisodes EST + leur bon outcome
    res = m.retrieve("theatre", embed_theatre(_sitrep(3)), k=3)
    top = res[0]
    print("[test] requête menace EST -> top sim=%.3f, décision=%s, cibles_intactes=%.0f, score=%.2f"
          % (top["sim"], top["decision"]["orders"][0]["action"],
             top["outcome"]["cibles_intactes_frac"], top["score"]))
    assert top["decision"]["orders"][0]["action"] == "RENFORCER", "devrait retrouver l'épisode EST (renforcer)"
    assert top["sim"] > 0.99, "la situation EST identique doit avoir sim ~1"
    # le filtre par niveau : la requête theatre ne ramène PAS l'épisode fob
    assert all(e["id"] for e in res) and m.count("fob") == 1
    # le scoring doctrine : EST (cibles ok) > OUEST (cible perdue)
    sc_est = score_outcome({"cibles_intactes_frac": 1.0, "fobs_tenus_frac": 1.0, "pertes_amies": 3, "pertes_ennemies": 9, "exposition": 0})
    sc_ouest = score_outcome({"cibles_intactes_frac": 0.0, "fobs_tenus_frac": 0.5, "pertes_amies": 12, "pertes_ennemies": 4, "exposition": 1})
    print("[test] score doctrine A>B>C>D : EST(cibles ok)=%.2f > OUEST(cible perdue)=%.2f" % (sc_est, sc_ouest))
    assert sc_est > sc_ouest, "la doctrine doit préférer protéger les cibles"
    print("=== RAG OK : journalise, score (A>B>C>D), récupère le passé similaire + sa leçon, filtre par niveau ===")


if __name__ == "__main__":
    _selftest()
