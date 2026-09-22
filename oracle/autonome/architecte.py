"""La regle de l Architecte, telle que l Oracle la LIT. Interchangeable : fichier ETAT_DIR/architecte.json.
  {"type": "constante", "option": 1}
  {"type": "lineaire", "g0": ..., "g": {nom: coef}, "mu": {...}, "sd": {...}}   - attendre si g0 + somme g.z < 0
  {"type": "formule", "formule": "...", "noms": [...]}                          - formule EvoGP de P(compromis)
La regle choisit, pour une perception donnee, l option dont la compromission predite est la plus faible.
Elle ne lit QUE la perception de l Architecte a la decision ( champs p_* ) : jamais la verite du monde."""
import json, os
import numpy as np
from . import config as C

FONCTIONS = {"tanh": np.tanh, "exp": lambda x: np.exp(np.clip(x, -30, 30)), "abs": np.abs, "neg": np.negative,
             "min": np.minimum, "max": np.maximum,
             "loose_div": lambda a, b: np.where(np.abs(b) > 1e-9, a / np.where(np.abs(b) > 1e-9, b, 1), 1.0),
             "loose_log": lambda x: np.log(np.maximum(np.abs(x), 1e-9)), "log": lambda x: np.log(np.maximum(np.abs(x), 1e-9))}
# ce que l Architecte percoit a la decision - et RIEN d autre ( 21/09 : verite_*, moteur_allume, erreur_position interdits )
PERMISES = ["alarme", "depuis_alarme", "vivants", "defenseurs_connus", "vehicule_vu", "vehicule_connu", "menace_percue",
            "menaces_vues", "menaces_connues", "menaces_camp", "menaces_homme", "distance_menace", "menace_mobile", "vue_depuis",
            "moteur_entendu", "distance_moteur", "vue_vehicule", "n_vues_menace", "menace_mobile_vue", "moteur_depuis_fenetre"]
INTERDITES = {"verite_distance_menace", "verite_menaces", "moteur_allume", "erreur_position", "compromis"}


def colonne(E, n):
    if n == "perception_etendue": return np.array([1.0 if e.get("p_moteur_entendu") is not None else 0.0 for e in E])
    if n in INTERDITES: raise ValueError(f"variable interdite a l Architecte : {n}")
    return np.array([(e.get("p_" + n) if e.get("p_" + n) is not None else 0.0) for e in E], dtype=float)


def charger():
    f = f"{C.ETAT_DIR}/architecte.json"
    if not os.path.exists(f): return {"type": "constante", "option": 1}
    return json.load(open(f))


def choix(regle, E):
    """Option choisie par la regle pour chaque episode, d apres la perception journalisee a la decision.
    Episode sans ligne de decision : l option imposee ( le choix n a jamais eu lieu )."""
    if regle["type"] == "constante": return np.full(len(E), regle["option"])
    if regle["type"] == "lineaire":
        s = np.full(len(E), float(regle["g0"]))
        for n, g in regle["g"].items():
            s += g * (colonne(E, n) - regle["mu"][n]) / regle["sd"][n]
        c = np.where(s < 0, 2, 1)
    elif regle["type"] == "formule":
        def evaluer(att):
            env = dict(FONCTIONS)
            for n in regle["noms"]:
                env[n] = np.full(len(E), att, dtype=float) if n == "attendre" else colonne(E, n)
            return np.asarray(eval(regle["formule"], {"__builtins__": {}}, env), dtype=float) * np.ones(len(E))
        p1, p2 = evaluer(0.0), evaluer(1.0)
        c = np.where(p2 < p1 - 1e-9, 2, 1)
    else:
        raise ValueError(f"regle inconnue : {regle['type']}")
    return np.array([ci if e.get("atteint_decision") else e["option_imposee"] for ci, e in zip(c, E)])


def texte(regle):
    """La regle, lisible par un humain."""
    if regle["type"] == "constante": return "toujours " + ("traverser" if regle["option"] == 1 else "attendre")
    if regle["type"] == "lineaire":
        termes = " ".join(f"{g:+.2f}·{n}" for n, g in sorted(regle["g"].items(), key=lambda kv: -abs(kv[1])) if abs(g) >= 0.05)
        return f"attendre si {regle['g0']:+.2f} {termes} < 0   ( variables centrees-reduites )"
    return f"P(compromis) = {regle['formule']}   ; attendre si P(attendre) < P(traverser)"
