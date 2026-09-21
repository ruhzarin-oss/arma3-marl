"""Pourquoi l imagination de l Oracle fait-elle pire que la constante ? Hypothese : pour une valeur d arme rare ou
jamais vue, les poids du reseau n ont presque pas ete entraines ; leurs decalages aleatoires, moyennes en
probabilite autour d un taux bas ( 16 % ), tirent la prediction VERS LE HAUT ( la sigmoide est convexe ici )."""
import numpy as np
from oracle.autonome import config as C, donnees as Dn, monde as M
E = Dn.utilisables(Dn.episodes(lambda c: not str(c).startswith(("DIABLE-I", "ORACLE-I"))))
m = M.Monde().apprendre(E)
sit = [{k: e[k] for k in C.ARMES} for e in E]
mu, _ = m.predire(sit, [e["graine"] for e in E], [e["option"] for e in E])
print(f"historique : taux reel {np.mean([e['compromis'] for e in E]):.3f}, prediction moyenne sur ses propres situations {mu.mean():.3f}")
from collections import Counter
freq = Counter((k, e[k]) for e in E for k in C.ARMES)
rng = np.random.default_rng(0); base = sit[:300]; gr = [e["graine"] for e in E[:300]]
for titre, choisir in (("valeur FREQUENTE ( >= 200 episodes )", lambda k: [v for v in C.ARMES[k] if freq[(k, v)] >= 200]),
                       ("valeur RARE ( 1 a 20 episodes )", lambda k: [v for v in C.ARMES[k] if 0 < freq[(k, v)] <= 20]),
                       ("valeur JAMAIS vue", lambda k: [v for v in C.ARMES[k] if freq[(k, v)] == 0])):
    preds = []
    for s, g in zip(base, gr):
        ks = [k for k in C.ARMES if choisir(k)]
        if not ks: continue
        k = ks[rng.integers(len(ks))]; s2 = dict(s); s2[k] = int(rng.choice(choisir(k)))
        p, _ = m.predire([s2], [g], [1]); preds.append(p[0])
    print(f"   une arme changee vers une {titre:<38} : prediction moyenne {np.mean(preds):.3f} ( n {len(preds)} )" if preds else f"   {titre} : aucune")
E_d = Dn.utilisables(Dn.episodes(lambda c: str(c).startswith(("DIABLE-I", "ORACLE-I"))))
print(f"episodes de l Oracle joues : {len(E_d)}, compromission reelle {np.mean([e['compromis'] for e in E_d]):.3f}")
