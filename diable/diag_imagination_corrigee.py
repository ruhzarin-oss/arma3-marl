import numpy as np
from diable import config as C, donnees as Dn, monde as M
E = Dn.utilisables(Dn.episodes(lambda c: not str(c).startswith("DIABLE")))
m = M.Monde().apprendre(E)
sit = [{k: e[k] for k in C.ARMES} for e in E]
mu, sd = m.predire(sit, [e["graine"] for e in E], [e["option"] for e in E])
Y = np.array([e["compromis"] for e in E])
print(f"historique : taux reel {Y.mean():.3f}, prediction moyenne {mu.mean():.3f}, desaccord moyen {sd.mean():.3f}")
# le vrai juge : l imagination d AVANT chaque iteration du diable, sur cette iteration
for it in ("DIABLE-I001", "DIABLE-I002"):
    Ea = Dn.utilisables(Dn.episodes(lambda c, it=it: (not str(c).startswith("DIABLE")) or (str(c) < it)))
    Et = Dn.utilisables(Dn.episodes(lambda c, it=it: c == it))
    ma = M.Monde().apprendre(Ea)
    p, _ = ma.predire([{k: e[k] for k in C.ARMES} for e in Et], [e["graine"] for e in Et], [e["option"] for e in Et])
    y = np.array([e["compromis"] for e in Et])
    print(f"{it} rejoue avec la nouvelle imagination : Brier {np.mean((p - y) ** 2):.4f} contre constante {np.mean((ma.taux - y) ** 2):.4f} "
          f"( taux reel {y.mean():.3f}, predit {p.mean():.3f} )")
