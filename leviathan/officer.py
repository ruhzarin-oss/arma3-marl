#!/usr/bin/env python3
"""officer.py — LA BOUCLE de l'officier Qwen (le chef d'orchestre). Ferme le cycle :

  distill (SITREP) -> RAG.retrieve (leçons) -> Qwen (ordres) -> apply (focus) -> RAG.record
                                                                      ... N ticks après -> set_outcome

Bâti avec un Qwen BOUCHON (règle) pour tester toute la boucle sans vLLM ni Arma. Brancher le vrai Qwen =
remplacer `stub_qwen` par un appel vLLM (voir `qwen_vllm`). Fichier autonome."""
import sys, json
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from officer_state import OfficerState, FOBS
from officer_memory import OfficerMemory, embed_theatre

_FOB_NAMES = ", ".join(f[0] for f in FOBS)                            # M1..M6, O1..O19 (depuis officer_state)
SYSTEM = (
    "Tu es l'officier supérieur commandant la défense de Stratis (RHS AFRF), 25 FOB, ~500 hommes.\n"
    "DOCTRINE par priorité : 1) protéger les CIBLES vitales (QG/HVT/otage) 2) préserver la FORCE "
    "3) tenir le TERRAIN 4) saigner l'ennemi.\n"
    "Les SEULS FOB que tu commandes (utilise UNIQUEMENT ces noms EXACTS, n'en invente AUCUN) :\n"
    + _FOB_NAMES + ".\n"
    "N'émets d'ordre que pour les FOB qui en ont besoin (menacés, ou pour réallouer la force) — pas les 25. "
    "Chaque `fob` DOIT être un de ces noms ; chaque `cible` = la position [x,y] d'un FOB existant, ou null.\n"
    "Tu reçois des LEÇONS (situations passées + résultat), puis la SITUATION. Rends UNIQUEMENT ce JSON :\n"
    '{"appreciation":"<2 phrases>","ordres":[{"fob":"<nom>","action":"TENIR|RENFORCER|QRF|REPLIER|MASSER",'
    '"cible":[x,y] ou null,"priorite":1-5}]}'
)


def format_retrieved(passe):
    if not passe: return "LEÇONS PASSÉES : aucune."
    L = ["LEÇONS PASSÉES (situations similaires + résultat réel) :"]
    for e in passe:
        o = e.get("outcome") or {}
        act = (e["decision"].get("ordres") or [{}])[0].get("action", "?")
        L.append("- sim %.2f : on a %s -> score %.2f (cibles %.0f%%, pertes %d)" %
                 (e.get("sim", 0), act, e.get("score") or 0,
                  100 * o.get("cibles_intactes_frac", 0), o.get("pertes_amies", 0)))
    return "\n".join(L)


def stub_qwen(prompt, sit):
    """Qwen BOUCHON (règle) : masse sur le FOB le plus menacé (RENFORCER), sinon TENIR. Remplaçable par vLLM."""
    thr = [f for f in sit["fobs"] if f["contacts"] > 0]
    if not thr:
        return {"appreciation": "Théâtre calme, patrouilles en cours.", "ordres": []}
    top = max(thr, key=lambda f: f["contacts"])
    return {"appreciation": "Poussée ennemie sur %s." % top["name"],
            "ordres": [{"fob": top["name"], "action": "RENFORCER", "cible": top["pos"], "priorite": 1}]}


def qwen_vllm(prompt, sit, model="Qwen/Qwen2.5-7B-Instruct", url="http://localhost:8000/v1/chat/completions"):
    """Le VRAI Qwen (inférence vLLM, 3090). À utiliser quand le serveur vLLM tourne."""
    import requests
    r = requests.post(url, json={"model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "temperature": 0.3, "response_format": {"type": "json_object"}}, timeout=30)
    return json.loads(r.json()["choices"][0]["message"]["content"])


def qwen_ollama(prompt, sit, model="qwen2.5:14b", url="http://localhost:11434/v1/chat/completions"):
    """Le VRAI Qwen via OLLAMA (qwen2.5:14b déjà chargé sur le 3090). Endpoint OpenAI-compatible."""
    import requests, re as _re
    r = requests.post(url, json={
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "temperature": 0.2, "response_format": {"type": "json_object"}}, timeout=120)
    txt = r.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(txt)
    except Exception:                                              # filet : extraire le 1er objet JSON
        m = _re.search(r"\{.*\}", txt, _re.DOTALL)
        return json.loads(m.group(0)) if m else {"appreciation": txt[:200], "ordres": []}


def make_apply(driver):
    """orders -> pose driver.focus (RENFORCER/MASSER/QRF sur un FOB). TENIR/REPLIER -> pas de focus."""
    _pos = {f[0]: [f[1], f[2]] for f in FOBS}
    def apply(orders):
        if driver is None: return
        foc = None
        for o in orders.get("ordres", []):
            if o.get("action") in ("RENFORCER", "MASSER", "QRF"):
                foc = o.get("cible") or _pos.get(o.get("fob"))
                if foc: break
        driver.focus = foc
    return apply


class OfficerLoop:
    def __init__(self, memory, qwen=stub_qwen, apply_fn=None, outcome_lag=3):
        self.mem = memory; self.qwen = qwen
        self.apply = apply_fn or (lambda o: None)
        self.lag = outcome_lag
        self.pending = []                                            # (ep_id, tick, sit) en attente d'outcome

    def decide(self, sit, tick, ts):
        emb = embed_theatre(sit)
        passe = self.mem.retrieve("theatre", emb, k=3)              # les leçons
        prompt = format_retrieved(passe) + "\n\n" + OfficerState.to_text(sit)
        orders = self.qwen(prompt, sit)                             # le cerveau
        self.apply(orders)                                         # l'exécution (focus)
        ep = self.mem.record("theatre", tick, ts, emb, sit, context=passe, decision=orders)
        self.pending.append((ep, tick, sit))
        return orders

    def settle_outcomes(self, tick, measure_fn):
        """Pour les décisions dont le lag est écoulé : mesure la conséquence -> grave la leçon."""
        still = []
        for (ep, t0, sit0) in self.pending:
            if tick - t0 >= self.lag: self.mem.set_outcome(ep, measure_fn(sit0, tick))
            else: still.append((ep, t0, sit0))
        self.pending = still


# ===================== SELF-TEST : la boucle complète, sans vLLM ni Arma =====================
def _make_sit(tick, threat="M3", c=8):
    fobs = [{"name": nm, "pos": [x, y], "tier": ti, "held": 1,
             "garrison": (12 if ti == "MAIN" else 6),
             "contacts": (c if nm == threat else 0), "threatened": (1 if nm == threat else 0)}
            for (nm, x, y, ti) in FOBS]
    return {"tick": tick, "fobs": fobs, "targets_intact": 8, "targets_total": 8,
            "daytime": 2.0, "is_night": True, "total_force": 480, "total_threat": c}


def _selftest():
    mem = OfficerMemory(":memory:")
    loop = OfficerLoop(mem, qwen=stub_qwen, outcome_lag=1)

    def measure(sit0, now):                                         # outcome synthétique : on a renforcé -> cibles tenues
        return {"cibles_intactes_frac": 1.0, "fobs_tenus_frac": 1.0,
                "pertes_amies": 3, "pertes_ennemies": 9, "exposition": 0}

    # 6 cycles : menace récurrente à l'EST (M3)
    for t in range(0, 60, 10):
        orders = loop.decide(_make_sit(t), t, float(t))
        loop.settle_outcomes(t + 5, measure)                       # le lag s'écoule -> grave la leçon
    print("[test] %d décisions journalisées + outcome gravé" % mem.count("theatre"))

    # une NOUVELLE menace EST -> la boucle doit RÉCUPÉRER les leçons passées
    sit = _make_sit(100)
    passe = mem.retrieve("theatre", embed_theatre(sit), k=3)
    assert passe, "devrait récupérer des leçons"
    top = passe[0]
    print("[test] nouvelle menace EST -> récupère %d leçons ; meilleure = %s (score %.2f, sim %.2f)" %
          (len(passe), top["decision"]["ordres"][0]["action"], top["score"], top["sim"]))
    assert top["decision"]["ordres"][0]["action"] == "RENFORCER"

    # le prompt que verrait Qwen (avec les leçons injectées)
    print("---- PROMPT QWEN (extrait) ----")
    print(format_retrieved(passe))
    print("=== BOUCLE COMPLÈTE OK : distill -> RAG -> (Qwen) -> ordres -> record -> outcome -> ré-apprend ===")


def run_real():
    """Test du VRAI Qwen (qwen2.5:14b via Ollama) sur un SITREP synthétique + une leçon passée."""
    mem = OfficerMemory(":memory:")
    # on sème UNE leçon passée (menace EST gérée par RENFORCER -> cibles tenues) pour la voir réinjectée
    s0 = _make_sit(0)
    e = mem.record("theatre", 0, 0.0, embed_theatre(s0), s0,
                   decision={"ordres": [{"fob": "M3", "action": "RENFORCER"}]})
    mem.set_outcome(e, {"cibles_intactes_frac": 1.0, "fobs_tenus_frac": 1.0,
                        "pertes_amies": 3, "pertes_ennemies": 9, "exposition": 0})
    loop = OfficerLoop(mem, qwen=qwen_ollama)
    sit = _make_sit(142)                                          # menace forte sur M3
    print("---- SITREP envoyé à Qwen ----")
    print(OfficerState.to_text(sit))
    print("---- réflexion de Qwen2.5:14b ... ----", flush=True)
    orders = loop.decide(sit, 142, 142.0)
    print("APPRÉCIATION :", orders.get("appreciation"))
    print("ORDRES       :", json.dumps(orders.get("ordres"), ensure_ascii=False, indent=2))
    valid = {f[0] for f in FOBS}
    bad = [o.get("fob") for o in orders.get("ordres", []) if o.get("fob") not in valid]
    print("NOMS INVENTÉS :", bad if bad else "AUCUN ✓ (grounding OK)")
    print("=== VRAI QWEN OK : SITREP+leçons -> ordres JSON exécutables ===")


if __name__ == "__main__":
    import sys
    if "--real" in sys.argv: run_real()
    else: _selftest()
