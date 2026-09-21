"""L imagination de l Oracle : un modele du monde qui predit la compromission d une situation sous chaque option.
Ensemble de 10 modeles appris chacun sur un tirage des episodes : leur moyenne est le risque imagine, leur
desaccord l incertitude ( la curiosite ).

! 21/09 17 h 40 - BOGUE CORRIGE. La v1 utilisait 10 MLPClassifier avec early_stopping=True. Sklearn arrete alors sur
la JUSTESSE de validation ; avec 16 % de cas positifs, la justesse plafonne des que tout est predit « non
compromis », et les reseaux s arretaient AVANT d etre calibres : prediction moyenne 0,335 sur leurs PROPRES
situations d apprentissage, pour un taux reel de 0,162. D ou une imagination pire que la constante aux iterations 1
et 2 - ce n etait pas de l ignorance, c etait ce bogue. Remplace par des regressions logistiques L2 avec les
interactions arme x option : calibrees par construction, et une valeur rare ou jamais vue a un coefficient
rabattu vers zero, donc une prediction ramenee au taux de base au lieu d un decalage aleatoire. C est aussi la
forme que le point 1 a trouvee la moins mauvaise ( le reseau y faisait pire que la constante ).
Au-dela de ce qui a ete joue, les reseaux se trompent avec assurance : la NOUVEAUTE ( armes jamais essayees ) est
donc mesuree a part, sans reseau."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from . import config as C

N_RESEAUX = 10
C_L2 = 0.3        # inverse de la penalite : plus petit = rabat plus fort vers le taux de base


def encoder_colonnes():
    cols = [("graine", g) for g in C.GRAINES]
    for k in C.CATEGORIELLES: cols += [(k, v) for v in C.ARMES[k]]
    cols += [(k, None) for k in C.NUMERIQUES + C.BINAIRES] + [("attendre", None)]
    return cols


COLS = encoder_colonnes()
ECHELLES = {k: (min(C.ARMES[k]), max(C.ARMES[k]) - min(C.ARMES[k]) or 1) for k in C.NUMERIQUES}


def encoder(situations, graines, options):
    X = np.zeros((len(situations), len(COLS)), dtype=np.float32)
    idx = {c: i for i, c in enumerate(COLS)}
    for r, (s, g, o) in enumerate(zip(situations, graines, options)):
        if ("graine", g) in idx: X[r, idx[("graine", g)]] = 1
        for k in C.CATEGORIELLES:
            if (k, s[k]) in idx: X[r, idx[(k, s[k])]] = 1
        for k in C.NUMERIQUES:
            lo, et = ECHELLES[k]; X[r, idx[(k, None)]] = (float(s[k]) - lo) / et
        for k in C.BINAIRES: X[r, idx[(k, None)]] = float(s[k])
        X[r, idx[("attendre", None)]] = 1.0 if o == 2 else 0.0
    return X


IA = [i for i, c in enumerate(COLS) if c == ("attendre", None)][0]


def interactions(X):
    """Chaque arme, et chaque arme croisee avec l option : c est ce qui permet a l imagination de voir qu une option
    vaut mieux que l autre DANS une situation - la definition meme d un piege."""
    return np.hstack([X, X * X[:, [IA]]])


class Monde:
    def __init__(self):
        self.reseaux, self.vu, self.configs, self.taux = [], set(), [], None

    def apprendre(self, E):
        sit = [{k: e[k] for k in C.ARMES} for e in E]
        X = encoder(sit, [e["graine"] for e in E], [e["option"] for e in E])
        Y = np.array([e["compromis"] for e in E])
        self.taux = float(Y.mean())
        self.reseaux = []
        Xi = interactions(X)
        for s in range(N_RESEAUX):
            r = np.random.default_rng(C.GRAINE + s); idx = r.integers(0, len(Y), len(Y))   # amorce : chaque modele voit un tirage
            if Y[idx].min() == Y[idx].max(): idx = np.arange(len(Y))
            m = LogisticRegression(C=C_L2, max_iter=5000, solver="lbfgs")
            m.fit(Xi[idx], Y[idx]); self.reseaux.append(m)
        self.vu = {(k, e[k]) for e in E for k in C.ARMES} | {("graine", e["graine"]) for e in E}
        self.configs = [tuple(e[k] for k in C.ARMES) for e in E]
        return self

    def predire(self, situations, graines, options):
        X = interactions(encoder(situations, graines, options))
        P = np.array([m.predict_proba(X)[:, 1] for m in self.reseaux])
        return P.mean(0), P.std(0)

    def nouveaute(self, s, graines=()):
        """Nombre d armes reglees sur une valeur jamais jouee, plus la distance a la situation jouee la plus proche."""
        jamais = sum(1 for k in C.ARMES if (k, s[k]) not in self.vu) + sum(1 for g in graines if ("graine", g) not in self.vu)
        v = tuple(s[k] for k in C.ARMES)
        if not self.configs: return float(jamais + len(v))
        cfg = np.array(self.configs); d = (cfg != np.array(v, dtype=object)).sum(1).min()
        return float(jamais + d)
