"""Le diable imagine : il tire des milliers de situations, predit pour chacune le risque sous chaque option et ce
que la regle de l Architecte y choisirait, et garde celles ou la regle se trompe alors qu une autre option reste
sure ( exploitation ), celles qu il ne connait pas ( exploration ), et les pieges a confirmer."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from . import config as C
from . import monde as M
from .architecte import choix


def cle(s): return tuple(s[k] for k in C.ARMES)


def distance(a, b): return sum(1 for k in C.ARMES if a[k] != b[k])


def modele_du_choix(regle, E):
    """P( la regle choisit attendre | situation ), appris sur la perception journalisee des episodes deja joues."""
    if regle["type"] == "constante": return lambda sit, gr: np.full(len(sit), 1.0 if regle["option"] == 2 else 0.0)
    c = choix(regle, E); y = (c == 2).astype(int)
    if y.min() == y.max(): return lambda sit, gr, v=float(y[0]): np.full(len(sit), v)
    X = M.encoder([{k: e[k] for k in C.ARMES} for e in E], [e["graine"] for e in E], [1] * len(E))
    lr = LogisticRegression(max_iter=2000, C=1.0).fit(X, y)
    return lambda sit, gr: lr.predict_proba(M.encoder(sit, gr, [1] * len(sit)))[:, 1]


def evaluer(monde, p_choix, cands):
    sit, gr, op = [], [], []
    for s, g in cands:
        for gi in g:
            for o in (1, 2): sit.append(s); gr.append(gi); op.append(o)
    mu, sd = monde.predire(sit, gr, op)
    mu, sd = mu.reshape(len(cands), 2, 2), sd.reshape(len(cands), 2, 2)     # candidat x graine x option
    r = mu.mean(1); s_ = sd.mean((1, 2))
    p2 = p_choix([s for s, g in cands for gi in g], [gi for s, g in cands for gi in g]).reshape(len(cands), 2).mean(1)
    regret = (1 - p2) * r[:, 0] + p2 * r[:, 1] - r.min(1)
    return r, s_, p2, regret


def proposer(monde, regle, E_hist, deja_joue, a_confirmer, rng):
    p_choix = modele_du_choix(regle, E_hist)
    cands = []
    for _ in range(C.CANDIDATS_IMAGINES):
        s = {k: int(rng.choice(v)) for k, v in C.ARMES.items()}
        g = tuple(int(x) for x in rng.choice(C.GRAINES, 2, replace=False))
        cands.append((s, g))
    # le diable reprend aussi ses meilleurs pieges passes, legerement mutes
    for p in a_confirmer[:50]:
        for _ in range(20):
            s = dict(p["situation"])
            for k in rng.choice(list(C.ARMES), 2, replace=False): s[k] = int(rng.choice(C.ARMES[k]))
            cands.append((s, tuple(p["graines"])))
    # garde G_REJEU : jamais une ( situation, graine, option ) deja jouee, hors confirmation
    cands = [(s, g) for s, g in cands if not any((cle(s), gi, o) in deja_joue for gi in g for o in (1, 2))]
    r, sd, p2, regret = evaluer(monde, p_choix, cands)
    nouv = np.array([monde.nouveaute(s, g) for s, g in cands])
    jouable = r.min(1) <= C.SEUIL_JOUABLE_IMAGINE
    score = regret + C.KAPPA_INCERTITUDE * sd + C.KAPPA_NOUVEAUTE * nouv
    choisis = []

    def prendre(ordre, n, genre, filtre):
        for i in ordre:
            if len([c for c in choisis if c["genre"] == genre]) >= n: break
            if not filtre[i]: continue
            s, g = cands[i]
            if any(distance(s, c["situation"]) < C.DISTANCE_MIN_DIVERSITE for c in choisis): continue
            choisis.append(dict(genre=genre, situation=s, graines=list(g), risque_traverser=float(r[i, 0]),
                                risque_attendre=float(r[i, 1]), incertitude=float(sd[i]), p_regle_attend=float(p2[i]),
                                regret_imagine=float(regret[i]), nouveaute=float(nouv[i])))
    prendre(np.argsort(-score), C.K_EXPLOIT, "exploitation", jouable & (regret >= C.REGRET_MIN_PIEGE))
    prendre(np.argsort(-(nouv + sd)), C.K_EXPLORE, "exploration", np.ones(len(cands), bool))
    for p in a_confirmer[:C.K_CONFIRME]:
        choisis.append(dict(genre="confirmation", situation=p["situation"], graines=list(p["graines"]),
                            regret_observe=p.get("regret_observe"), regret_imagine=None))
    n_pieges = int((jouable & (regret >= C.REGRET_MIN_PIEGE)).sum())
    return choisis, dict(imagines=len(cands), pieges_imagines=n_pieges, regret_max=float(regret.max()) if len(regret) else 0.0)
