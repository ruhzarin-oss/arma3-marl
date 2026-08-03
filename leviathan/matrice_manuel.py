#!/usr/bin/env python3
"""matrice_manuel.py — QUELLE MANŒUVRE POUR QUELLE MENACE ?

Six manœuvres du manuel (`manuel.py`) croisées avec six niveaux de menace.
C'est le patron de la brique 0 (géométrie × manœuvre → sélecteur adaptatif +13 contre
la meilleure fixe), transposé à l'axe qui compte ici : la densité adverse.

Monde figé au monde MESURÉ : courbe n1, courbe n2, cible_unique=True. Aucune courbe
n'est retouchée. Seul D varie. Doctrines SCRIPTÉES — le choix n'est pas appris ici,
c'est justement ce que la matrice doit rendre possible ensuite.

Sort deux choses :
  1. la MATRICE prise[manœuvre][D] et coût[manœuvre][D]
  2. la VALEUR DE SÉLECTION : ce que gagne un chef qui choisit la bonne manœuvre pour
     chaque menace, comparé au meilleur choix FIXE. C'est le chiffre qui dit si
     l'adaptabilité vaut quelque chose.

Critères figés AVANT le run dans CRITERES_MATRICE_MANUEL.md.
"""
import sys, os, json, math, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
import torch
from assault_terrain import AssaultTerrain
from manuel import MANOEUVRES, CONDITIONS

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument('--episodes', type=int, default=200)
ap.add_argument('--steps', type=int, default=60)
ap.add_argument('--seed', type=int, default=7)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--defenseurs', default='4,6,8,10,12,16')
ap.add_argument('--arc_deg', type=float, default=120.0, help='arc de tir defensif TOTAL en degres')
# def_rand=True TIRE l arc au hasard dans U(80,140) deg et IGNORE def_arc (mesure 2026-07-28).
# --fixe fige la geometrie aux valeurs MEDIANES du tirage, seul l arc varie alors.
ap.add_argument('--fixe', action='store_true', help='geometrie defensive figee : rend --arc_deg reellement actif')
ap.add_argument('--out', default='matrice_manuel.json')
a = ap.parse_args()

BANDE = (0.25, 0.75)


def monde(D, seed):
    k = dict(num_envs=a.episodes, A=4, D=D, seed=seed, device=a.device,
             max_steps=a.steps, postures=True, hull=True,
             def_line=True, def_arc=math.radians(a.arc_deg) / 2.0, def_rand=not a.fixe,
             def_spread=math.radians(20.0), def_rline=37.5,
             secure_task=True, secure_only=True)
    k.update(courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG)
    k.update(supp_residuel=0.08, supp_persist=0.35)
    k.update(cible_unique=True)
    return AssaultTerrain(**k)


def joue(D, nom, seed):
    e = monde(D, seed); e.reset()
    N = e.N
    f = MANOEUVRES[nom]
    pris = torch.zeros(N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(N, dtype=torch.bool, device=e.dev)
    pertes = torch.zeros(N, device=e.dev)
    expo = torch.zeros(N, device=e.dev)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()
    for t in range(a.steps):
        _, _, done, info = e.step(f(e, t), auto_reset=False)
        vivant = ~fini
        pris = pris | (info['took'] & vivant)
        pertes = torch.where(vivant, info['losses'].float(), pertes)
        expo = expo + info['exposed'] * vivant.float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(vivant, d, dmin))
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    gagne = (d0 - dmin).clamp(min=1.0)
    return {'prise': float(pris.float().mean()),
            'pertes_par_prise': float(pertes[pris].mean()) if bool(pris.any()) else float('nan'),
            'expo_par_metre': float((expo / gagne).mean())}


if __name__ == '__main__':
    if not os.path.exists(LEV + '/CRITERES_MATRICE_MANUEL.md'):
        print('!! les criteres ne sont pas figes — ARRET.'); sys.exit(2)
    Ds = [int(x) for x in a.defenseurs.split(',')]
    noms = list(MANOEUVRES)
    print('=== MATRICE DU MANUEL : six manoeuvres x six menaces ===')
    print('    A=4 | D=%s | arc %.0f deg (geometrie %s) | %d episodes/cellule | graine %d | monde MESURE fige\n' % (Ds, a.arc_deg, 'FIGEE' if a.fixe else 'aleatoire — arc INERTE', a.episodes, a.seed))
    t0 = time.time(); M = {}
    entete = '  %-20s' % 'manoeuvre \\ D' + ''.join(['%8d' % D for D in Ds])
    print(entete); print('  ' + '-' * (len(entete) - 2))
    for nom in noms:
        M[nom] = {}
        ligne = '  %-20s' % nom
        for D in Ds:
            r = joue(D, nom, a.seed)
            M[nom][D] = r
            ligne += '%7.0f%%' % (100 * r['prise'])
        print(ligne, flush=True)

    print('\n  coût (pertes par prise réussie)')
    for nom in noms:
        ligne = '  %-20s' % nom
        for D in Ds:
            c = M[nom][D]['pertes_par_prise']
            ligne += '%8s' % ('%.2f' % c if c == c else '  -  ')
        print(ligne)

    # --- bande discriminante : on ne lit que les colonnes ou le REPERTOIRE separe ---
    bande = []
    for D in Ds:
        prises = [M[n][D]['prise'] for n in noms]
        if BANDE[0] <= max(prises) <= 1.0 and (max(prises) - min(prises)) >= 0.10:
            bande.append(D)

    print('\n=== LECTURE (critères figés) ===')
    print('  colonnes exploitables (écart >= 10 pts entre la meilleure et la pire) : D = %s'
          % (bande if bande else 'AUCUNE'))
    if bande:
        meilleures = {D: max(noms, key=lambda n: M[n][D]['prise']) for D in bande}
        print('  meilleure manoeuvre par menace :')
        for D in bande:
            n = meilleures[D]
            print('     D=%-3d -> %-20s (prise %.0f%%)' % (D, n, 100 * M[n][D]['prise']))
        # valeur de selection : chef adaptatif contre meilleur choix FIXE
        adaptatif = sum(M[meilleures[D]][D]['prise'] for D in bande) / len(bande)
        fixes = {n: sum(M[n][D]['prise'] for D in bande) / len(bande) for n in noms}
        meilleur_fixe = max(fixes, key=fixes.get)
        vs = 100 * (adaptatif - fixes[meilleur_fixe])
        print('\n  chef ADAPTATIF (bonne manoeuvre a chaque menace) : %.0f%% de prise' % (100 * adaptatif))
        print('  meilleur choix FIXE (%s) : %.0f%%' % (meilleur_fixe, 100 * fixes[meilleur_fixe]))
        print('  >>> VALEUR DE SELECTION : %+.1f points' % vs)
        if vs >= 8:
            print('      L ADAPTABILITE PAIE. Le repertoire justifie un selecteur appris.')
        elif vs > 0:
            print('      Adaptabilite MARGINALE : une seule manoeuvre suffit presque partout.')
        else:
            print('      AUCUNE valeur : la meme manoeuvre gagne partout. Le repertoire ne sert a rien ici.')
        print('\n  --- conditions du manuel, confrontees ---')
        for n in noms:
            best = [D for D in bande if meilleures[D] == n]
            print('    %-20s %s' % (n, ('gagne a D=%s' % best) if best else 'ne gagne nulle part'))
            print('      manuel : %s' % CONDITIONS[n])
    json.dump({'criteres': 'CRITERES_MATRICE_MANUEL.md (3c86c7051e57cbad)', 'episodes': a.episodes,
               'graine': a.seed, 'defenseurs': Ds,
               'matrice': {n: {str(D): M[n][D] for D in Ds} for n in noms},
               'duree_s': round(time.time() - t0)},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('\n-> %s/%s  (%.0f s)' % (LEV, a.out, time.time() - t0))
    print('MATRICE_DONE')
