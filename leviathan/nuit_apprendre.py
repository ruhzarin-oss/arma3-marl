#!/usr/bin/env python3
"""nuit_apprendre.py — LE MONDE MESURE ENSEIGNE-T-IL LA BONNE LECON ?

Le re-verdict a repondu a « le monde JUGE-t-il juste ? » : oui, la courbe n1 seule suffit
a rendre le flanc payant. Deuxieme question, distincte : ce que le monde ENSEIGNE a une
politique qui y apprend de zero.

On entraine dans le monde MESURE, plusieurs graines, sur la ligne defensive a arc de tir,
puis on compare la politique apprise aux deux doctrines scriptees du re-verdict :
  - fait-elle mieux que l assaut frontal ? (sinon le monde n enseigne rien)
  - approche-t-elle le crochet ? decouvre-t-elle l angle mort toute seule ?
L exposition par metre gagne est relevee tout du long — c est la variable qui separe les
gagnants des perdants, et elle doit baisser si la politique apprend vraiment a manoeuvrer.

On entraine AUSSI un temoin dans l ANCIEN monde, evalue dans le NOUVEAU : c est la
demonstration chiffree que le sanctuaire enseignait une tactique suicidaire.

Ne demande ni Arma ni presence humaine. Concu pour tourner la nuit.
"""
import sys, os, json, math, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument('--graines', type=int, default=3)
ap.add_argument('--rounds', type=int, default=60, help='rondes PPO par graine')
ap.add_argument('--K', type=int, default=8, help='iterations PPO par ronde')
ap.add_argument('--ne', type=int, default=1024)
ap.add_argument('--eval', type=int, default=200)
ap.add_argument('--device', default='cuda:0')      # ATTENTION : cuda:0 = la 3090 (PyTorch classe par puissance)
ap.add_argument('--out', default='nuit_apprendre.json')
a = ap.parse_args()
DEV = a.device


def monde(nouveau, seed, ne):
    k = dict(num_envs=ne, A=4, D=4, seed=seed, device=DEV, max_steps=60,
             postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
             def_rand=True, secure_task=True, secure_only=True)
    if nouveau:
        k.update(courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG)
    return AssaultTerrain(**k)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def evalue(net, nouveau, seed, doctrine=None):
    """joue la politique (ou une doctrine scriptee) et rend les memes metriques que le re-verdict"""
    e = monde(nouveau, seed, a.eval)
    obs = e.reset(); N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=DEV); fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV); expo = torch.zeros(N, device=DEV)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()
    for t in range(60):
        if doctrine == 'frontal':
            act = cap(-e.apx, -e.apy)
        elif doctrine == 'flanc':
            act = cap(-e.apx, -e.apy)
            d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
            fixe = torch.zeros(N, e.A, dtype=torch.bool, device=DEV); fixe[:, :2] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            if t < 14:
                act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        else:
            with torch.no_grad():
                act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
        obs, _, done, info = e.step(act, auto_reset=False)
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
            'expo_par_metre': float(expo / gagne).__float__() if False else float((expo / gagne).mean())}


def apprend(nouveau, seed, etiquette):
    e = monde(nouveau, seed, a.ne)
    obs = e.reset(); O = obs.shape[-1]
    net = Net(O, e.n_actions).to(DEV)
    opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    piste = []
    for r in range(1, a.rounds + 1):
        obs = ppo_iters(net, opt, e, obs, a.K, O)
        if r % 10 == 0 or r == a.rounds:
            m = evalue(net, nouveau, seed + 1000)      # graine d evaluation DIFFERENTE de l entrainement
            m['ronde'] = r
            piste.append(m)
            print('    [%s g%d] ronde %2d/%d : prise %5.1f%%  expo/m %.3f'
                  % (etiquette, seed, r, a.rounds, 100 * m['prise'], m['expo_par_metre']), flush=True)
            torch.save(net.state_dict(), '%s/nuit_%s_g%d.pt' % (LEV, etiquette, seed))
    return net, piste


if __name__ == '__main__':
    t0 = time.time()
    print('=== LE MONDE MESURE ENSEIGNE-T-IL LA BONNE LECON ? ===', flush=True)
    print('    %d graines x %d rondes | 3090 | ni Arma ni presence humaine' % (a.graines, a.rounds), flush=True)
    res = {'reperes': {}, 'appris': {}}

    # --- reperes scriptes, dans le monde mesure : la barre a battre ---
    for doc in ('frontal', 'flanc'):
        res['reperes'][doc] = evalue(None, True, 7, doctrine=doc)
        print('  repere scripte %-8s : prise %5.1f%%  expo/m %.3f'
              % (doc, 100 * res['reperes'][doc]['prise'], res['reperes'][doc]['expo_par_metre']), flush=True)
    print('', flush=True)

    # --- apprentissage dans le monde MESURE ---
    for g in range(a.graines):
        seed = 7 + g
        print('  apprentissage dans le monde MESURE, graine %d' % seed, flush=True)
        try:
            net, piste = apprend(True, seed, 'mesure')
            res['appris']['mesure_g%d' % seed] = piste
        except Exception as x:
            print('    (echec graine %d : %s)' % (seed, str(x)[:90]), flush=True)
        json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)   # sauvegarde a chaque etape

    # --- temoin : appris dans l ANCIEN monde, juge dans le NOUVEAU ---
    print('', flush=True)
    print('  temoin : appris dans l ANCIEN monde, juge dans le MESURE', flush=True)
    try:
        net_a, piste_a = apprend(False, 7, 'ancien')
        res['appris']['ancien_g7_dans_son_monde'] = piste_a
        res['temoin_ancien_juge_dans_mesure'] = evalue(net_a, True, 1007)
        print('    -> juge dans le monde MESURE : prise %5.1f%%  expo/m %.3f'
              % (100 * res['temoin_ancien_juge_dans_mesure']['prise'],
                 res['temoin_ancien_juge_dans_mesure']['expo_par_metre']), flush=True)
    except Exception as x:
        print('    (temoin echoue : %s)' % str(x)[:90], flush=True)

    res['duree_s'] = round(time.time() - t0)
    json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s  (%.0f min)' % (LEV, a.out, (time.time() - t0) / 60.0), flush=True)
    print('NUIT_DONE', flush=True)
