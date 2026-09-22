"""La regle de l Architecte, telle que l Oracle la LIT. Interchangeable : fichier ETAT_DIR/architecte.json.
  {"type": "constante", "option": 1}
  {"type": "lineaire", "g0": ..., "g": {nom: coef}, "mu": {...}, "sd": {...}}   - attendre si g0 + somme g.z < 0
  {"type": "formule", "formule": "...", "noms": [...]}                          - formule EvoGP de P(compromis)
La regle choisit, pour une perception donnee, l option dont la compromission predite est la plus faible.
Elle ne lit QUE la perception de l Architecte a la decision ( champs p_* ) : jamais la verite du monde."""
import json, os
import numpy as np
from . import config as C

# ! 22/09 : les fonctions d EvoGP, TELLES QU IL LES CALCULE ( evogp/cuda/defs.h et forward.cu, en float32, DELTA = 1e-9 ).
# La v1 relisait l affichage d EvoGP ( « a max b », moins typographique, constantes arrondies a 2 decimales ) :
# 114 formules sur 400 seulement se relisaient a l identique. Les formules sont desormais traduites depuis l ARBRE.
_D = np.float32(1e-9)
def _f(x): return np.asarray(x, dtype=np.float32)
def _cmp(o): return lambda a, b: np.where(o(_f(a), _f(b)), np.float32(1), np.float32(-1))   # forward.cu : +1 ou -1, PAS 1 ou 0
FONCTIONS = {"tanh": np.tanh, "sin": np.sin, "cos": np.cos, "tan": np.tan, "sinh": np.sinh, "cosh": np.cosh, "exp": np.exp,
             "abs": np.abs, "neg": np.negative, "max": np.maximum, "min": np.minimum,
             "div": lambda a, b: np.where(_f(b) == 0, np.float32(np.nan), _f(a) / np.where(_f(b) == 0, np.float32(1), _f(b))),
             "loose_div": lambda a, b: _f(a) / np.where(np.abs(_f(b)) <= _D, np.copysign(_D, _f(b)), _f(b)),
             "log_": lambda x: np.log(_f(x)), "loose_log": lambda x: np.log(np.maximum(np.abs(_f(x)), _D)),
             "inv": lambda x: np.float32(1) / _f(x), "loose_inv": lambda x: np.float32(1) / np.where(np.abs(_f(x)) <= _D, np.copysign(_D, _f(x)), _f(x)),
             "sqrt_": lambda x: np.sqrt(_f(x)), "loose_sqrt": lambda x: np.sqrt(np.abs(_f(x))),
             "pow_": lambda a, b: np.power(_f(a), _f(b)), "loose_pow": lambda a, b: np.power(np.abs(_f(a)), _f(b)),
             "lt": _cmp(np.less), "gt": _cmp(np.greater), "le": _cmp(np.less_equal), "ge": _cmp(np.greater_equal),
             "si": lambda a, b, c: np.where(_f(a) > 0, _f(b), _f(c))}
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
                env[n] = np.full(len(E), att, dtype=np.float32) if n == "attendre" else colonne(E, n).astype(np.float32)
            with np.errstate(all="ignore"):
                return np.nan_to_num(np.asarray(eval(regle["formule"], {"__builtins__": {}}, env), dtype=float) * np.ones(len(E)), nan=0.5)
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
    return f"P(compromis) = {regle.get('affichage', regle['formule'])}   ; attendre si P(attendre) < P(traverser)"
