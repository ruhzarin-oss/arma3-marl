#!/usr/bin/env python3
"""audit_ordre.py — L AGENT LIT-IL SON ORDRE DE MISSION ? (jalon 1, E6-E7)

ORCHESTRATEUR. Il ne contient plus aucune boucle d evaluation : il appelle `banc_mission.joue`
et delegue les taux a `analyse_journal`. Une seule boucle de mesure existe dans le projet.

Principe : on rejoue les MEMES episodes en permutant le verbe AFFICHE dans l ordre de mission,
sans rien changer d autre. Le predicat de succes continue d utiliser le verbe VRAI.

  - Sur une DOCTRINE scriptee, qui ne lit aucune observation, l ecart attendu n est pas
    « petit » : il est EXACTEMENT 0,000. C est le CONTROLE NUL. Toute valeur non nulle prouve
    que le chemin de permutation contamine l etat du monde, et alors aucun verdict sur un
    agent n est recevable.
  - Sur un RESEAU, un ecart >= 20 points sur au moins un verbe prouve qu il lit son ordre.

Lu PAR VERBE, jamais moyenne : permuter fait bouger les deux verbes en sens OPPOSES et une
moyenne les annule (faute commise et documentee au contrat, amendement 3).
"""
import sys, os, argparse, collections
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')

LEV = '/home/younes/arma3-marl/leviathan'
SEUIL_LECTURE = 20.0
VERBES = ['prendre', 'infiltrer']


def taux_du_journal(chemin):
    from analyse_journal import lire, taux, controle
    ent, eps = lire(chemin)
    if not eps:
        return None
    if not controle(eps, chemin):
        print('  !! predicat recalcule != monde — arret.'); sys.exit(4)
    return taux(eps)


def audite(pilote, graines, base, episodes, D, pas, hidden, layers, device):
    from banc_mission import joue
    vrai = collections.defaultdict(list)
    perm = collections.defaultdict(list)
    for s in range(graines):
        g = base + s
        for v in VERBES:
            for k in (0, 1):
                j, _ = joue(pilote, verbe=v, permute=k, episodes=episodes, graine=g,
                            D=D, pas=pas, mode='episode', hidden=hidden, layers=layers,
                            device=device, silencieux=True)
                t = taux_du_journal(j)
                if t is None or v not in t:
                    print('  !! passe vide : %s' % j); sys.exit(4)
                (vrai if k == 0 else perm)[v].append(t[v]['succes'])
    return vrai, perm


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilote', required=True, help='doctrine:<nom> ou reseau:<chemin.pt>')
    ap.add_argument('--graines', type=int, default=5)
    ap.add_argument('--base', type=int, default=1000, help='graines tenues a l ecart')
    ap.add_argument('--episodes', type=int, default=1024)
    ap.add_argument('--D', type=int, default=8)
    ap.add_argument('--pas', type=int, default=80)
    ap.add_argument('--hidden', type=int, default=256)
    ap.add_argument('--layers', type=int, default=3)
    ap.add_argument('--device', default='cuda:0')
    a = ap.parse_args()

    est_doctrine = a.pilote.startswith('doctrine:')
    vrai, perm = audite(a.pilote, a.graines, a.base, a.episodes, a.D, a.pas,
                        a.hidden, a.layers, a.device)

    print('  %-26s %-10s %10s %10s %9s' % ('pilote', 'verbe', 'ordre vrai', 'permute', 'ecart'))
    ecarts = {}
    for v in VERBES:
        mv = sum(vrai[v]) / len(vrai[v]); mp = sum(perm[v]) / len(perm[v])
        ecarts[v] = abs(mv - mp)
        print('  %-26s %-10s %9.3f%% %9.3f%% %8.3f' % (a.pilote, v, mv, mp, ecarts[v]))
    emax = max(ecarts.values())
    print('')
    if est_doctrine:
        print('=== CONTROLE NUL (attendu : EXACTEMENT 0,000) ===')
        print('  ecart maximal : %.3f point' % emax)
        if emax == 0.0:
            print('  >>> ZERO EXACT. Le chemin de permutation ne touche pas le monde.')
            sys.exit(0)
        print('  >>> CONTAMINATION : une doctrine ne lit aucune observation, son taux ne peut')
        print('      pas bouger. Le chemin de permutation modifie l etat du monde.')
        print('      Aucun verdict sur un agent n est recevable. On repare.')
        sys.exit(5)
    print('=== LECTURE DE L ORDRE (seuil pre-enregistre : >= %.0f points sur un verbe) ==='
          % SEUIL_LECTURE)
    print('  ecart maximal par verbe : %.1f points' % emax)
    if emax >= SEUIL_LECTURE:
        print('  >>> L AGENT LIT SON ORDRE.')
        faibles = [v for v in VERBES if sum(vrai[v]) / len(vrai[v]) < 10.0]
        if faibles:
            print('  !! mais il le lit MAL pour %s : moins de 10 %% en ordre correct.' % faibles)
            print('     Un verbe lu et mal execute est un probleme de recompense, pas de lecture.')
    else:
        print('  >>> L AGENT IGNORE SON ORDRE : il joue la meme chose quel que soit le verbe.')
    print('AUDIT_ORDRE_DONE')
