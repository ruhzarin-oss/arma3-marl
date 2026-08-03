#!/usr/bin/env python3
"""porte_v6.py — LES DEUX PORTES DE v6, avant tout entrainement.

PORTE 1 — CONTROLE NUL. Seuils pousses a l infini : la couche ne se declenche jamais et doit
reproduire la politique EXACTEMENT. Ecart attendu 0,000. Une couche qui ne prouve pas son
inertie ne peut pas prouver son effet.

PORTE 2 — L OBEISSANCE AVANT L APPRENTISSAGE. Seuils ALEATOIRES, politique ALEATOIRE, aucun
gradient. La dose consommee doit deja croitre avec le budget : rho de Spearman >= 0,80 sur
8 niveaux. Si le corps ne produit pas l obeissance sans apprendre, le dispositif a echoue
avant d avoir commence et on n entraine RIEN.

On a passe deux versions a esperer qu un agent apprenne a obeir. Cette fois ca se verifie
sur piece avant le premier pas de gradient.
"""
import sys
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from monde_mission import fabrique
from reflexe import CoucheReflexe, N_SEUILS
from manuel import MANOEUVRES

DEV = 'cuda:0'
BUDGETS = [0.6, 0.9, 1.2, 1.6, 2.2, 3.0, 3.6, 4.2]


def spearman(x, y):
    def rang(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for k, i in enumerate(o):
            r[i] = float(k)
        return r
    rx, ry = rang(x), rang(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def porte1():
    print('=== PORTE 1 — CONTROLE NUL (seuils a l infini, ecart attendu 0,000) ===')
    pire = 0.0
    for nom, f in MANOEUVRES.items():
        m = fabrique(episodes=512, D=8, seed=77, device=DEV, steps=80, mode_budget=True)
        m.reset()
        c = CoucheReflexe(m.N, m.A, DEV)
        inf = torch.zeros(m.N, m.A, N_SEUILS, device=DEV)
        inf[..., 0] = 1e9; inf[..., 1] = 1e9; inf[..., 2] = 0.0; inf[..., 3] = -1.0
        diff = 0
        for t in range(60):
            a = f(m.env, t)
            b, taux = c.applique(a, inf, m, brut=True)
            diff += int((a != b).sum())
            m.step(b, auto_reset=False)
        pire = max(pire, diff)
        print('  %-22s substitutions : %d' % (nom, diff))
    print('')
    if pire == 0:
        print('  >>> ZERO EXACT. La couche eteinte est un pur passe-plat.')
        return True
    print('  >>> LA COUCHE MODIFIE LA POLITIQUE ALORS QU ELLE EST ETEINTE. On repare.')
    return False


def porte2():
    print('')
    print('=== PORTE 2 — OBEISSANCE SANS APPRENTISSAGE (seuils et politique aleatoires) ===')
    print('  %8s %12s %12s' % ('budget', 'dose', 'substitutions'))
    doses = []
    g = torch.Generator(device=DEV); g.manual_seed(4242)
    for B in BUDGETS:
        m = fabrique(episodes=1024, D=8, seed=88, device=DEV, steps=80,
                     mode_budget=True, budget_force=B)
        m.reset()
        c = CoucheReflexe(m.N, m.A, DEV)
        seuils = torch.rand(m.N, m.A, N_SEUILS, generator=g, device=DEV)
        tot = 0.0
        for t in range(60):
            a = torch.randint(0, m.n_actions, (m.N, m.A), generator=g, device=DEV)
            b, taux = c.applique(a, seuils, m)
            tot += float(taux)
            m.step(b, auto_reset=False)
        d = float(m.expo_cum.mean())
        doses.append(d)
        print('  %8.1f %12.3f %11.1f%%' % (B, d, 100 * tot / 60))
    rho = spearman(BUDGETS, doses)
    print('')
    print('  rho de Spearman entre budget et dose : %.3f  (seuil 0,80)' % rho)
    if rho >= 0.80:
        print('  >>> LE CORPS OBEIT SANS AVOIR APPRIS. Le budget agit mecaniquement.')
        return True
    print('  >>> LE CORPS N OBEIT PAS. Le dispositif a echoue avant d avoir commence :')
    print('      on n entraine RIEN tant que ce rho n est pas atteint.')
    return False


if __name__ == '__main__':
    ok1 = porte1()
    ok2 = porte2()
    print('')
    print('=== VERDICT v6 ===')
    print('  porte 1 controle nul   : %s' % ('FRANCHIE' if ok1 else 'REFUSEE'))
    print('  porte 2 obeissance     : %s' % ('FRANCHIE' if ok2 else 'REFUSEE'))
    print('PORTE_V6_DONE')
    sys.exit(0 if (ok1 and ok2) else 1)
