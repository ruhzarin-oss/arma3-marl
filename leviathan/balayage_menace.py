#!/usr/bin/env python3
"""balayage_menace.py — A PARTIR DE QUELLE MENACE LA MANOEUVRE REDEVIENT-ELLE PAYANTE ?

Le re-verdict du 28/07 dit : a 4 defenseurs, dans le monde correctement letal, le flanc
n achete plus la prise (x1,00), seulement des vies (cout x0,39). Ce n est pas un verdict
sur la manoeuvre, c est un verdict A UN NIVEAU DE MENACE. On balaie le cadran.

Monde FIGE au monde mesure (courbe n1 + courbe n2 + cible_unique=True). Aucune courbe
n est retouchee. Seul D, le nombre de defenseurs, varie.

Criteres figes AVANT le run dans CRITERES_BALAYAGE_MENACE.md (empreinte cfe67bb4d459d5dd).
"""
import sys, os, json, math, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233          # mesures Arma du 26/07

ap = argparse.ArgumentParser()
ap.add_argument('--episodes', type=int, default=200)
ap.add_argument('--steps', type=int, default=60)
ap.add_argument('--seed', type=int, default=7)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--defenseurs', default='4,6,8,10,12,16')
ap.add_argument('--out', default='balayage_menace.json')
a = ap.parse_args()

BANDE = (0.25, 0.75)      # bande discriminante, figee d avance
SEUIL_PRISE = 1.50        # le flanc "paie" en prise
SEUIL_COUT = 0.60         # le flanc "paie" en cout


def monde(D, seed):
    k = dict(num_envs=a.episodes, A=4, D=D, seed=seed, device=a.device,
             max_steps=a.steps, postures=True, hull=True,
             def_line=True, def_arc=math.pi / 3, def_rand=True,
             secure_task=True, secure_only=True)
    k.update(courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG)
    k.update(supp_residuel=0.08, supp_persist=0.35)
    k.update(cible_unique=True)          # certifie par Arma le 2026-07-28
    return AssaultTerrain(**k)


def cap(dx, dy):
    ang = torch.atan2(dx, dy)
    return (torch.round(ang / (math.pi / 4.0)).long() % 8)


def doctrine_frontal(e, t):
    return cap(-e.apx, -e.apy)


def doctrine_flanc(e, t, n_fixe=2, pas_crochet=14):
    N, A = e.N, e.A
    act = cap(-e.apx, -e.apy)
    d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
    fixe = torch.zeros(N, A, dtype=torch.bool, device=e.dev); fixe[:, :n_fixe] = True
    a_portee = d_obj < e.fire_range * 0.9
    act = torch.where(fixe & a_portee, torch.full_like(act, 9), act)
    act = torch.where(fixe & ~a_portee, cap(-e.apx, -e.apy), act)
    if t < pas_crochet:
        tang = cap(-e.apy, e.apx)
        act = torch.where(~fixe, tang, act)
    return act


DOCTRINES = {'frontal': doctrine_frontal, 'flanc': doctrine_flanc}


def joue(D, doctrine, seed):
    e = monde(D, seed)
    e.reset()
    N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(N, dtype=torch.bool, device=e.dev)
    pertes = torch.zeros(N, device=e.dev)
    expo_cum = torch.zeros(N, device=e.dev)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
    dmin = d0.clone()
    f = DOCTRINES[doctrine]
    for t in range(a.steps):
        _, _, done, info = e.step(f(e, t), auto_reset=False)
        vivant = ~fini
        pris = pris | (info['took'] & vivant)
        pertes = torch.where(vivant, info['losses'].float(), pertes)
        expo_cum = expo_cum + info['exposed'] * vivant.float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(vivant, d, dmin))
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    gagne = (d0 - dmin).clamp(min=1.0)
    return {'prise': float(pris.float().mean()),
            'pertes_par_prise': float(pertes[pris].mean()) if bool(pris.any()) else float('nan'),
            'expo_par_metre': float((expo_cum / gagne).mean()),
            'n': int(N)}


if __name__ == '__main__':
    if not os.path.exists(LEV + '/CRITERES_BALAYAGE_MENACE.md'):
        print('!! les criteres ne sont pas figes — ARRET.'); sys.exit(2)
    Ds = [int(x) for x in a.defenseurs.split(',')]
    print('=== BALAYAGE DE LA MENACE : ou la manoeuvre redevient-elle payante ? ===', flush=True)
    print('    A=4 | D=%s | %d episodes/bras/point | graine %d | monde MESURE fige'
          % (Ds, a.episodes, a.seed), flush=True)
    print('', flush=True)
    print('    D   prise frontal   prise flanc   prise fl/fr   cout fl/fr   bande ?', flush=True)
    t0 = time.time(); res = {}
    for D in Ds:
        fr = joue(D, 'frontal', a.seed)
        fl = joue(D, 'flanc', a.seed)
        rp = fl['prise'] / fr['prise'] if fr['prise'] > 0 else float('inf')
        rc = (fl['pertes_par_prise'] / fr['pertes_par_prise']
              if fr['pertes_par_prise'] == fr['pertes_par_prise'] and fr['pertes_par_prise'] else float('nan'))
        dans = BANDE[0] <= fr['prise'] <= BANDE[1]
        res[str(D)] = {'frontal': fr, 'flanc': fl, 'rapport_prise': rp,
                       'rapport_cout': rc, 'dans_bande': bool(dans)}
        print('   %3d      %5.1f%%        %5.1f%%        x%4.2f        x%4.2f      %s'
              % (D, 100 * fr['prise'], 100 * fl['prise'], rp, rc,
                 'OUI' if dans else 'non'), flush=True)

    print('', flush=True)
    print('=== LECTURE (criteres figes, non negociables) ===', flush=True)
    bande = [D for D in Ds if res[str(D)]['dans_bande']]
    if not bande:
        print('  >>> AUCUN POINT DANS LA BANDE 25-75 %% : le banc ne separe rien sur cette plage.', flush=True)
        print('      Ne pas interpreter les ratios. Elargir la plage de D dans un run SUIVANT,', flush=True)
        print('      pas dans celui-ci.', flush=True)
    else:
        print('  bande discriminante (frontal 25-75 %%) : D = %s' % bande, flush=True)
        seuil = [D for D in bande if res[str(D)]['rapport_prise'] >= SEUIL_PRISE]
        if seuil:
            print('  >>> SEUIL DE MANOEUVRE : D = %d.' % seuil[0], flush=True)
            print('      Au-dessus de cette menace, le flanc achete la PRISE, pas seulement des vies.', flush=True)
        else:
            print('  >>> PAS DE SEUIL SOUS D=%d : dans toute la bande, le flanc n achete pas la prise.' % Ds[-1], flush=True)
            print('      On l ecrit tel quel. On n etend pas la plage pour en trouver un.', flush=True)
        couts = [(D, res[str(D)]['rapport_cout']) for D in bande]
        mauvais = [D for D, c in couts if c == c and c > SEUIL_COUT]
        if mauvais:
            print('  !! avantage de cout PERDU en D = %s (rapport > %.2f) — a signaler, pas a lisser.'
                  % (mauvais, SEUIL_COUT), flush=True)
        else:
            print('  avantage de cout conserve sur toute la bande (rapport <= %.2f).' % SEUIL_COUT, flush=True)

    json.dump({'criteres': 'CRITERES_BALAYAGE_MENACE.md (cfe67bb4d459d5dd)',
               'episodes': a.episodes, 'graine': a.seed, 'defenseurs': Ds,
               'points': res, 'duree_s': round(time.time() - t0)},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s  (%.0f s)' % (LEV, a.out, time.time() - t0), flush=True)
    print('BALAYAGE_DONE', flush=True)
