#!/usr/bin/env python3
"""durcir — TROUVER LA DURETE QUI DISCRIMINE, pas la plus dure.

Le banc est sature : le meilleur bras prend 96 % des objectifs. A ce niveau aucun
mecanisme ne peut prouver quoi que ce soit — l'axe du stress a ete teste sur une tache
ou il n'y avait plus rien a gagner, et il n'a evidemment rien montre.

Mais durcir au hasard mene au plancher, qui est aussi aveugle que le plafond.

LE CRITERE : maximiser l'ECART entre l'assaut frontal et le crochet. Cet ecart EST la
place que la manoeuvre a pour exister. S'il se referme — les deux a 95 % ou les deux a
5 % — le banc ne mesure plus rien, quelle que soit la difficulte.

ON CALIBRE SUR LES DOCTRINES SCRIPTEES, JAMAIS SUR LES AGENTS APPRIS. Deux raisons :
elles ne changent pas d'un run a l'autre, et surtout on ne peut pas se soupconner d'avoir
choisi la durete qui arrange un mecanisme. La durete se fige AVANT qu'un mecanisme ne soit
teste — sinon on fabrique un banc qui dit ce qu'on veut.

Un levier a la fois. Sinon on ne saura pas lequel a fait quoi.

Aucun entrainement : 60 pas par configuration. Le balayage entier tient en minutes.
"""
import sys, json, math, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument('--eval', type=int, default=2048, help='la 3090 est a 14 % : plus d envs est gratuit')
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='durete.json')
a = ap.parse_args()
DEV = a.device

BASE = dict(A=4, D=4, max_steps=60, R_spawn=170.0, arc=math.pi / 3)


def monde(cfg, seed):
    return AssaultTerrain(num_envs=a.eval, A=cfg['A'], D=cfg['D'], seed=seed, device=DEV,
                          max_steps=cfg['max_steps'], R_spawn=cfg['R_spawn'],
                          postures=True, hull=True, def_line=True, def_arc=cfg['arc'],
                          def_rand=True, secure_task=True, secure_only=True,
                          courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC,
                          degat_par_impact=DEG, arc_obs=True)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


@torch.no_grad()
def joue(cfg, doctrine, seed):
    e = monde(cfg, seed)
    e.reset(); N, A = e.N, e.A
    pris = torch.zeros(N, dtype=torch.bool, device=DEV); fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV)
    for t in range(cfg['max_steps']):
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
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    pr = float(pris.float().mean())
    pe = float(pertes[pris].mean()) if bool(pris.any()) else float('nan')
    return {'prise': pr, 'pertes_par_prise': pe,
            'prise_a_pertes': pr / pe if pe and pe == pe and pe > 0 else float('nan')}


def evalue(cfg):
    """l'ecart frontal/crochet EST la place que la manoeuvre a pour exister"""
    f = [joue(cfg, 'frontal', s) for s in (7, 8, 9)]
    c = [joue(cfg, 'flanc', s) for s in (7, 8, 9)]
    mf = sum(x['prise'] for x in f) / 3.0
    mc = sum(x['prise'] for x in c) / 3.0
    return {'frontal': mf, 'crochet': mc, 'ecart': mc - mf,
            'pap_frontal': sum(x['prise_a_pertes'] for x in f) / 3.0,
            'pap_crochet': sum(x['prise_a_pertes'] for x in c) / 3.0}


if __name__ == '__main__':
    t0 = time.time()
    print('=== QUELLE DURETE DISCRIMINE ? ===', flush=True)
    print('    critere : maximiser l ecart frontal <-> crochet (= la place de la manoeuvre)', flush=True)
    print('    cible   : le crochet entre 50 et 70 %% — ni plafond ni plancher', flush=True)
    print('    calibre sur les doctrines SCRIPTEES, jamais sur les agents appris', flush=True)
    print('', flush=True)

    LEVIERS = [
        ('actuel',              dict(BASE)),
        ('defenseurs 6',        dict(BASE, D=6)),
        ('defenseurs 8',        dict(BASE, D=8)),
        ('defenseurs 10',       dict(BASE, D=10)),
        ('temps 45',            dict(BASE, max_steps=45)),
        ('temps 35',            dict(BASE, max_steps=35)),
        ('temps 28',            dict(BASE, max_steps=28)),
        ('depart 220 m',        dict(BASE, R_spawn=220.0)),
        ('depart 280 m',        dict(BASE, R_spawn=280.0)),
        ('arc 90 deg',          dict(BASE, arc=math.pi / 2)),
        ('arc 120 deg',         dict(BASE, arc=2 * math.pi / 3)),
    ]

    res = {}
    print('%-18s %10s %10s %10s   %s' % ('configuration', 'frontal', 'crochet', 'ECART', 'lecture'), flush=True)
    for nom, cfg in LEVIERS:
        r = evalue(cfg)
        res[nom] = {'cfg': {k: (float(v) if isinstance(v, float) else v) for k, v in cfg.items()}, **r}
        lect = ''
        if r['crochet'] > 0.90:
            lect = 'PLAFOND'
        elif r['crochet'] < 0.25:
            lect = 'PLANCHER'
        elif 0.50 <= r['crochet'] <= 0.70:
            lect = '<-- bande visee'
        print('%-18s %9.1f%% %9.1f%% %9.1f pt   %s'
              % (nom, 100 * r['frontal'], 100 * r['crochet'], 100 * r['ecart'], lect), flush=True)

    print('', flush=True)
    util = {k: v for k, v in res.items() if 0.35 <= v['crochet'] <= 0.80}
    print('=== CE QUE CA DECIDE ===', flush=True)
    if not util:
        print('  Aucune configuration ne place le crochet dans une bande exploitable.', flush=True)
        print('  Il faudra combiner deux leviers — mais alors on saura lesquels, pas au hasard.', flush=True)
    else:
        best = max(util.items(), key=lambda kv: kv[1]['ecart'])
        print('  Meilleur ecart dans la bande : %s' % best[0], flush=True)
        print('    frontal %.1f%% | crochet %.1f%% | ecart %.1f points'
              % (100 * best[1]['frontal'], 100 * best[1]['crochet'], 100 * best[1]['ecart']), flush=True)
        print('    prise-a-pertes : frontal %.1f | crochet %.1f'
              % (best[1]['pap_frontal'], best[1]['pap_crochet']), flush=True)
        print('', flush=True)
        print('  A FIGER avant de tester le moindre mecanisme. Ne plus y toucher ensuite.', flush=True)
    json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s  (%.0f s)' % (LEV, a.out, time.time() - t0), flush=True)
    print('DURETE_DONE', flush=True)
