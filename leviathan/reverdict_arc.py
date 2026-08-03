#!/usr/bin/env python3
"""reverdict_arc — LE FLANC PAIE-T-IL ENCORE QUAND L'ARC N'EST PLUS UN MUR ?

Mesure Arma du 27/07 : le defenseur riposte TOUJOURS (100 % a tous les angles), mais
2,5 a 3,3 s plus tard quand ca vient du flanc ou du dos. L'angle mort n'est pas une zone
d'impunite — c'est un SURSIS d'environ 3 secondes, soit UN pas de sandbox.

Le cone dur du sandbox est donc une fiction. On la remplace par ce qui a ete mesure :
le cone se REORIENTE vers la menace percue apres la latence.

CE TEST PEUT DETRUIRE LE RE-VERDICT DE CETTE NUIT. On le fait quand meme.
L'avantage du flanc, dans le sandbox, vient aujourd'hui du mur. Si l'avantage s'effondre
avec l'arc dynamique, cela ne dit PAS que le flanc ne paie pas — le verdict Arma « le
flanc paie 2-3x a un tiers du cout » a ete mesure sur Arma par le banc FIBUA certifie, il
tient tout seul. Cela dirait que le sandbox le rendait par un MECANISME FAUX, et que le
vrai mecanisme est ailleurs : l'element d'appui ne distrait pas l'ennemi, il RETIENT SON
ATTENTION. Tant qu'il tire, le cone reste braque sur lui — et les trois secondes deviennent
permanentes pour celui qui contourne. C'est la suppression, et elle n'est pas dans ce monde.

Doctrines SCRIPTEES des deux cotes : on teste le MONDE, pas la politique.
Banc fige : 8 defenseurs (DURETE_FIGEE.md, 0eeae9efcdd67572).
"""
import sys, json, math, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument('--eval', type=int, default=2048)
ap.add_argument('--latences', default='3.0', help='latences en s, separees par des virgules')
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='reverdict_arc.json')
a = ap.parse_args()
DEV = a.device


def monde(lat, seed):
    k = dict(num_envs=a.eval, A=4, D=8, seed=seed, device=DEV, max_steps=60, R_spawn=170.0,
             postures=True, hull=True, def_line=True, def_rand=True,
             secure_task=True, secure_only=True, courbe=COURBE,
             tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG, arc_obs=True)
    if lat is not None:
        k['arc_latence_s'] = lat
    return AssaultTerrain(**k)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


@torch.no_grad()
def joue(lat, doctrine, seed):
    e = monde(lat, seed)
    e.reset(); N, A = e.N, e.A
    pris = torch.zeros(N, dtype=torch.bool, device=DEV); fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV); expo = torch.zeros(N, device=DEV)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()
    for t in range(60):
        d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        act = cap(-e.apx, -e.apy)
        if doctrine == 'flanc':
            fixe = torch.zeros(N, A, dtype=torch.bool, device=DEV); fixe[:, :2] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            if t < 14:
                act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        vv = ~fini
        _, _, done, info = e.step(act, auto_reset=False)
        pris = pris | (info['took'] & vv)
        pertes = torch.where(vv, info['losses'].float(), pertes)
        expo = expo + info['exposed'] * vv.float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(vv, d, dmin))
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    gagne = (d0 - dmin).clamp(min=1.0)
    pr = float(pris.float().mean())
    pe = float(pertes[pris].mean()) if bool(pris.any()) else float('nan')
    return {'prise': pr, 'pertes_par_prise': pe, 'expo_par_metre': float((expo / gagne).mean())}


def bras(lat):
    f = [joue(lat, 'frontal', s) for s in (7, 8, 9)]
    c = [joue(lat, 'flanc', s) for s in (7, 8, 9)]
    m = lambda v, k: sum(x[k] for x in v) / len(v)      # noqa: E731
    pf, pc = m(f, 'prise'), m(c, 'prise')
    cf, cc = m(f, 'pertes_par_prise'), m(c, 'pertes_par_prise')
    return {'frontal_prise': pf, 'crochet_prise': pc,
            'frontal_cout': cf, 'crochet_cout': cc,
            'rapport_prise': pc / pf if pf > 0 else float('inf'),
            'rapport_cout': cc / cf if cf and cf == cf and cf > 0 else float('nan'),
            'frontal_expo': m(f, 'expo_par_metre'), 'crochet_expo': m(c, 'expo_par_metre')}


if __name__ == '__main__':
    t0 = time.time()
    lats = [None] + [float(x) for x in a.latences.split(',') if x.strip()]
    print('=== LE FLANC PAIE-T-IL ENCORE SANS LE MUR ? ===', flush=True)
    print('    doctrines scriptees | 8 defenseurs | reference Arma : prise x2-3, cout ~1/3', flush=True)
    print('', flush=True)
    res = {}
    print('%-22s %10s %10s %12s %12s' % ('monde', 'frontal', 'crochet', 'x prise', 'x cout'), flush=True)
    for lat in lats:
        nom = 'cone DUR (fiction)' if lat is None else ('arc dynamique %.1f s' % lat)
        r = bras(lat)
        res[nom] = r
        print('%-22s %9.1f%% %9.1f%% %11.2f %11.2f'
              % (nom, 100 * r['frontal_prise'], 100 * r['crochet_prise'],
                 r['rapport_prise'], r['rapport_cout']), flush=True)

    print('', flush=True)
    print('=== LECTURE ===', flush=True)
    dur = res['cone DUR (fiction)']
    for nom, r in res.items():
        if nom.startswith('cone'):
            continue
        chute = 1.0 - (r['rapport_prise'] - 1.0) / max(dur['rapport_prise'] - 1.0, 1e-6)
        print('  %s : l avantage du flanc passe de x%.2f a x%.2f (%.0f %% de l avantage perdu)'
              % (nom, dur['rapport_prise'], r['rapport_prise'], 100 * chute), flush=True)
        if r['rapport_prise'] >= 2.0 and r['rapport_cout'] <= 0.5:
            print('    >>> LE FLANC PAIE ENCORE. Le mur n etait pas necessaire : le sandbox', flush=True)
            print('        rendait le bon verdict par le bon mecanisme.', flush=True)
        elif r['rapport_prise'] >= 1.5:
            print('    >>> AVANTAGE REDUIT MAIS PRESENT. Le mur portait une partie du verdict.', flush=True)
        else:
            print('    >>> L AVANTAGE S EFFONDRE. Le sandbox rendait le verdict par une FICTION.', flush=True)
            print('        Le verdict Arma tient (banc FIBUA certifie) — c est le MECANISME qui', flush=True)
            print('        etait faux. Le vrai est ailleurs, et le candidat est la SUPPRESSION :', flush=True)
            print('        l appui ne distrait pas, il RETIENT l attention. Tant qu il tire, le', flush=True)
            print('        cone reste braque sur lui et les 3 secondes deviennent permanentes.', flush=True)
    json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s  (%.0f s)' % (LEV, a.out, time.time() - t0), flush=True)
    print('REVERDICT_ARC_DONE', flush=True)
