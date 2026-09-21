"""La regle de l Architecte, telle que le diable la LIT. Interchangeable : fichier ETAT_DIR/architecte.json.
  {"type": "constante", "option": 1}
  {"type": "formule", "formule": "...", "noms": [...]}  - formule EvoGP sur la perception a la decision, P(compromis)
La regle choisit, pour une perception donnee, l option dont la compromission predite est la plus faible."""
import json, os
import numpy as np
from . import config as C

FONCTIONS = {"tanh": np.tanh, "exp": lambda x: np.exp(np.clip(x, -30, 30)), "abs": np.abs, "neg": np.negative,
             "min": np.minimum, "max": np.maximum,
             "loose_div": lambda a, b: np.where(np.abs(b) > 1e-9, a / np.where(np.abs(b) > 1e-9, b, 1), 1.0),
             "loose_log": lambda x: np.log(np.maximum(np.abs(x), 1e-9)), "log": lambda x: np.log(np.maximum(np.abs(x), 1e-9))}


def charger():
    f = f"{C.ETAT_DIR}/architecte.json"
    if not os.path.exists(f): return {"type": "constante", "option": 1}
    return json.load(open(f))


def choix(regle, E):
    """Option choisie par la regle pour chaque episode, d apres la perception journalisee a la decision.
    Episode sans ligne de decision : l option imposee ( le choix n a jamais eu lieu )."""
    if regle["type"] == "constante": return np.full(len(E), regle["option"])
    if regle["type"] == "formule":
        def evaluer(att):
            env = dict(FONCTIONS)
            for n in regle["noms"]:
                if n == "attendre": env[n] = np.full(len(E), att, dtype=float)
                elif n == "perception_etendue": env[n] = np.array([1.0 if e.get("p_moteur_entendu") is not None else 0.0 for e in E])
                else: env[n] = np.array([(e.get("p_" + n) if e.get("p_" + n) is not None else 0.0) for e in E], dtype=float)
            return np.asarray(eval(regle["formule"], {"__builtins__": {}}, env), dtype=float) * np.ones(len(E))
        p1, p2 = evaluer(0.0), evaluer(1.0)
        c = np.where(p2 < p1, 2, 1)
        return np.array([ci if e.get("atteint_decision") else e["option_imposee"] for ci, e in zip(c, E)])
    raise ValueError(f"regle inconnue : {regle['type']}")
