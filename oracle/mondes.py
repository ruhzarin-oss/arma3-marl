"""
Banc des Oracles ( criteres : oracle/CRITERES_BANC_ORACLE.md ). Mondes caches, episodes bruites, confirmation commune.
Situation theta = ( distance, moment, leurre ) dans [0, 1]^3 ; le leurre n'agit jamais.
La regle de l'Architecte est fixe ; r(theta) = P(reussite | autre option) - P(reussite | regle) est le regret signe.
Un episode tire l'option a pile ou face : z = 2 Y ( 1{autre option} - 1{regle} ), E[z | theta] = r(theta).
"""
import numpy as np

BASE = 0.35                       # reussite de l'option de la regle
SEUIL_FAILLE = 0.10               # une faille vraie : r > 0,10
PAR_TOUR, POINTS_PAR_TOUR, TOURS = 96, 24, 20     # 24 situations x 4 episodes, 20 tours = 1920 episodes
N_CANDIDATS, SEPARATION, N_CONFIRMATION, Z_DECLARE = 8, 0.15, 150, 2.326

MONDES = {
    "W0_nul":      dict(fond=-0.25, bosses=[]),
    "W1_aiguille": dict(fond=-0.25, bosses=[((0.72, 0.28), 0.80, 0.06)]),
    "W2_quatre":   dict(fond=-0.25, bosses=[((0.20, 0.20), 0.80, 0.08), ((0.80, 0.80), 0.75, 0.08),
                                            ((0.20, 0.80), 0.70, 0.08), ((0.78, 0.30), 0.65, 0.08)]),
    "W3_large_faible": dict(fond=-0.05, bosses=[((0.40, 0.60), 0.30, 0.20)]),
}


def regret(monde, T):
    """T : ( n, 3 ). Regret signe vrai."""
    T = np.atleast_2d(T)
    m = MONDES[monde]
    r = np.full(len(T), m["fond"], dtype=float)
    for (c, h, s) in m["bosses"]:
        d2 = (T[:, 0] - c[0]) ** 2 + (T[:, 1] - c[1]) ** 2
        r += h * np.exp(-d2 / (2 * s * s))
    return np.clip(r, -BASE + 0.02, 0.98 - BASE)


def region(monde, t):
    """Indice de la bosse dont la faille contient t ( r > seuil et bosse la plus proche ), sinon -1."""
    if regret(monde, t)[0] <= SEUIL_FAILLE:
        return -1
    b = MONDES[monde]["bosses"]
    return int(np.argmin([(t[0] - c[0]) ** 2 + (t[1] - c[1]) ** 2 for (c, _, _) in b])) if b else -1


def episodes(monde, T, n, rng):
    """n episodes par situation ; renvoie la moyenne de z par situation et le nombre d'episodes."""
    T = np.atleast_2d(T)
    r = regret(monde, T)
    p_regle, p_autre = np.full(len(T), BASE), BASE + r
    a_autre = rng.random((len(T), n)) < 0.5
    Y = rng.random((len(T), n)) < np.where(a_autre, p_autre[:, None], p_regle[:, None])
    z = 2.0 * Y * np.where(a_autre, 1.0, -1.0)
    return z.mean(axis=1), z.var(axis=1, ddof=1) if n > 1 else np.full(len(T), 2.0)


def separer(T, scores, k=N_CANDIDATS, sep=SEPARATION):
    """Les k meilleurs points, deux a deux a plus de sep en ( distance, moment )."""
    ordre = np.argsort(-np.asarray(scores))
    garde = []
    for i in ordre:
        if all(np.hypot(T[i][0] - T[j][0], T[i][1] - T[j][1]) > sep for j in garde):
            garde.append(i)
        if len(garde) == k:
            break
    return [list(map(float, T[i])) for i in garde]


def evaluer(monde, rep, oracle, explores, candidats):
    """Confirmation commune : N_CONFIRMATION episodes neufs par candidat, graine ( monde, rep, rang ), independante de l'oracle."""
    explores = np.array(explores, dtype=float)
    ids = list(MONDES).index(monde)
    declares = []
    for rang, t in enumerate(candidats):
        rng = np.random.default_rng(900_000 + 1000 * ids + 10 * rep + rang)   # meme tirage pour tous les oracles au meme rang
        zbar, zvar = episodes(monde, [t], N_CONFIRMATION, rng)
        se = np.sqrt(zvar[0] / N_CONFIRMATION)
        if zbar[0] - Z_DECLARE * se > 0:
            declares.append(dict(theta=t, r_vrai=float(regret(monde, [t])[0]), region=region(monde, t)))
    K = len(MONDES[monde]["bosses"])
    regions = sorted({d["region"] for d in declares if d["region"] >= 0})
    dans_faille = float(np.mean(regret(monde, explores[:, :3]) > SEUIL_FAILLE)) if len(explores) else 0.0
    return dict(oracle=oracle, monde=monde, rep=rep, K=K, regions_trouvees=len(regions), regions=regions,
                fausses=sum(d["r_vrai"] <= 0 for d in declares), faibles=sum(0 < d["r_vrai"] <= SEUIL_FAILLE for d in declares),
                declares=len(declares), part_budget_en_faille=dans_faille,
                meilleur_r_declare=max([d["r_vrai"] for d in declares], default=None))
