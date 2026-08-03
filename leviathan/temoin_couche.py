#!/usr/bin/env python3
"""temoin_couche.py — LE TEMOIN QUE J AVAIS SPECIFIE ET JAMAIS MESURE.

CRITERES_V6_REFLEXE.md exigeait : « les six politiques de reference passees A TRAVERS la
couche, seuils par defaut → le nouvel etalon ». Je ne l ai pas fait, et sans ce temoin on ne
peut pas separer deux causes tres differentes du 0,3 % d arrivee de l agent :

  - la couche est INNOCENTE  -> une doctrine y arrive encore, le probleme est l apprentissage
  - la couche est LA CAUSE   -> une doctrine s effondre elle aussi, et ce n est pas de
                                l apprentissage qu il s agit

Une doctrine ne lit aucune observation : si son taux d ARRIVEE chute en passant par la couche,
la chute est entierement imputable a la couche.

Seuils par defaut = 0,5 partout, soit le milieu des bornes, ce qu un reseau non entraine emet.
"""
import sys
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from monde_mission import fabrique
from reflexe import CoucheReflexe, N_SEUILS
from manuel import MANOEUVRES

DEV = 'cuda:0'
BUDGETS = [0.9, 2.2]


def passe(nom, f, B, avec_couche, seuil_val=0.5):
    m = fabrique(episodes=1024, D=8, seed=1000, device=DEV, steps=80,
                 mode_budget=True, budget_force=B)
    m.reset()
    c = CoucheReflexe(m.N, m.A, DEV)
    s = torch.full((m.N, m.A, N_SEUILS), seuil_val, device=DEV)
    subst = 0.0
    for t in range(80):
        a = f(m.env, t)
        b = a if not avec_couche else c.applique(a, s, m)[0]
        if avec_couche:
            subst += float((a != b).float().mean())
        m.step(b, auto_reset=False)
    return (100.0 * float(m.arrive.float().mean()),
            100.0 * float(m.succes.float().mean()),
            100.0 * subst / 80)


print('=== TEMOIN : LES DOCTRINES A TRAVERS LA COUCHE ===')
print('  %-22s %7s %11s %11s %11s %11s' %
      ('doctrine', 'budget', 'arr. SANS', 'arr. AVEC', 'succ. AVEC', 'substit.'))
pires = []
for nom, f in MANOEUVRES.items():
    for B in BUDGETS:
        a0, s0, _ = passe(nom, f, B, False)
        a1, s1, sub = passe(nom, f, B, True)
        pires.append((nom, B, a0, a1))
        print('  %-22s %7.1f %10.1f%% %10.1f%% %10.1f%% %10.1f%%' % (nom, B, a0, a1, s1, sub))

print('')
print('=== LECTURE ===')
ecarts = [(n, b, a0, a1, a0 - a1) for n, b, a0, a1 in pires if a0 > 20]
if not ecarts:
    print('  aucune doctrine n arrive assez sans la couche pour juger. Mesure inutilisable.')
else:
    pire = max(ecarts, key=lambda x: x[4])
    print('  chute maximale d ARRIVEE : %s a B=%.1f, de %.1f%% a %.1f%% (%.1f points)'
          % (pire[0], pire[1], pire[2], pire[3], pire[4]))
    if pire[4] > 40:
        print('  >>> LA COUCHE EST LA CAUSE. Une politique qui ne lit aucune observation')
        print('      s effondre en la traversant : ce n est pas un probleme d apprentissage.')
    elif pire[4] > 15:
        print('  >>> LA COUCHE COUTE CHER mais ne condamne pas. Les deux causes coexistent.')
    else:
        print('  >>> LA COUCHE EST INNOCENTE. Les doctrines la traversent sans dommage,')
        print('      donc le 0,3 pct de l agent vient de l APPRENTISSAGE. Prochain suspect :')
        print('      la penalite de depassement, payee tot quand le bonus arrive tard.')
print('TEMOIN_COUCHE_DONE')
