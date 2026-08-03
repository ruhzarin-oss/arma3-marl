#!/usr/bin/env python3
"""voir_arc.py — L'AGENT MANQUE-T-IL DE MANOEUVRE, OU DE VUE ?

Dans le monde mesure, l'agent apprend a gagner EN FORCE : 79 % de prise pour 0,032
d'exposition par metre, quand le crochet scripte fait 90 % pour 0,014. Constat de code :
la direction que regarde le defenseur n'est NULLE PART dans son observation. Il est dans
l'angle mort ou dans la ligne de mire — ce qu'il percoit est identique, seuls les degats
different. Et la geometrie est randomisee chaque episode, donc il ne peut meme pas
memoriser un cote.

Deux bras, meme monde, memes graines, tout identique SAUF l'observation :
  AVEUGLE  l'observation d'aujourd'hui
  VOYANT   la meme + ou regarde le defenseur le plus proche (sinus et cosinus de l'angle)

On donne la GEOMETRIE, pas le VERDICT.

Criteres figes AVANT le run : leviathan/CRITERES_ARC.md (empreinte 041baa1fed0aa96a).
  succes = exposition/m <= 0,023 dans le bras VOYANT, sans perdre en prise
  echec  = les deux bras restent dans le bruit -> ce n'est pas la perception
  contre-epreuve = le bras AVEUGLE doit reproduire la nuit (~79 % prise, ~0,032)
"""
import sys, os, json, math, time, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net
from train_soldier_pbt import ppo_iters

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233          # conversions mesurees sur Arma le 26/07

# repères de la nuit, dans le monde mesuré — servent de contre-epreuve
REF_AVEUGLE = {'prise': 0.788, 'expo': 0.032}
REF_CROCHET = {'prise': 0.897, 'expo': 0.014}
SEUIL_EXPO = 0.023                          # moitie de l'ecart comblee

ap = argparse.ArgumentParser()
ap.add_argument('--graines', type=int, default=3)
ap.add_argument('--rounds', type=int, default=150)
ap.add_argument('--K', type=int, default=8)
ap.add_argument('--ne', type=int, default=1024)
ap.add_argument('--eval', type=int, default=300)
ap.add_argument('--device', default='cuda:0')   # cuda:0 = la 3090 (PyTorch classe par puissance)
ap.add_argument('--out', default='voir_arc.json')
a = ap.parse_args()
DEV = a.device


def monde(voyant, seed, ne):
    return AssaultTerrain(num_envs=ne, A=4, D=4, seed=seed, device=DEV, max_steps=60,
                          postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
                          def_rand=True, secure_task=True, secure_only=True,
                          courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC,
                          degat_par_impact=DEG, arc_obs=voyant)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def part_angle_mort(e):
    """fraction des attaquants vivants situes HORS de l'arc du defenseur le plus proche.
    C'est le temoin de MECANISME : contourner, c'est passer dans l'angle mort."""
    if not hasattr(e, 'dface'):
        return torch.zeros(e.N, device=DEV)
    ex = e.dpx.unsqueeze(1) - e.apx.unsqueeze(2); ey = e.dpy.unsqueeze(1) - e.apy.unsqueeze(2)
    BIG = torch.tensor(1e18, device=DEV)
    ed2 = torch.where(e._dalive().unsqueeze(1), ex * ex + ey * ey, BIG)
    km = ed2.argmin(2)
    bx = torch.gather(e.dpx, 1, km); by = torch.gather(e.dpy, 1, km)
    df = torch.gather(e.dface, 1, km)
    az = torch.atan2(e.apx - bx, e.apy - by)
    rel = torch.atan2(torch.sin(az - df), torch.cos(az - df)).abs()
    dehors = (rel > e._dfarc).float() * e._aalive().float()
    return dehors.sum(1) / e._aalive().float().sum(1).clamp(min=1)


def evalue(net, voyant, seed, doctrine=None):
    e = monde(voyant, seed, a.eval)
    obs = e.reset(); N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=DEV); fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV); expo = torch.zeros(N, device=DEV)
    mort_cum = torch.zeros(N, device=DEV); nsteps = torch.zeros(N, device=DEV)
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
        vivant = ~fini
        mort_cum = mort_cum + part_angle_mort(e) * vivant.float()
        nsteps = nsteps + vivant.float()
        obs, _, done, info = e.step(act, auto_reset=False)
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
            'expo_par_metre': float((expo / gagne).mean()),
            'part_angle_mort': float((mort_cum / nsteps.clamp(min=1)).mean())}


def apprend(voyant, seed, etiquette):
    e = monde(voyant, seed, a.ne)
    obs = e.reset(); O = obs.shape[-1]
    net = Net(O, e.n_actions).to(DEV)
    opt = torch.optim.Adam(net.parameters(), lr=3e-4)
    piste = []
    for r in range(1, a.rounds + 1):
        obs = ppo_iters(net, opt, e, obs, a.K, O)
        if r % 30 == 0 or r == a.rounds:
            m = evalue(net, voyant, seed + 1000)
            m['ronde'] = r
            piste.append(m)
            print('    [%s g%d] ronde %3d/%d : prise %5.1f%%  expo/m %.4f  angle mort %4.1f%%'
                  % (etiquette, seed, r, a.rounds, 100 * m['prise'], m['expo_par_metre'],
                     100 * m['part_angle_mort']), flush=True)
            torch.save(net.state_dict(), '%s/arc_%s_g%d.pt' % (LEV, etiquette, seed))
    return net, piste


if __name__ == '__main__':
    if not os.path.exists(LEV + '/CRITERES_ARC.md'):
        print('!! les criteres ne sont pas figes — ARRET.'); sys.exit(2)
    t0 = time.time()
    print('=== L AGENT MANQUE-T-IL DE MANOEUVRE, OU DE VUE ? ===', flush=True)
    print('    2 bras x %d graines x %d rondes | criteres figes (041baa1fed0aa96a)'
          % (a.graines, a.rounds), flush=True)
    res = {'reperes': {}, 'bras': {'aveugle': [], 'voyant': []}}

    for doc in ('frontal', 'flanc'):
        res['reperes'][doc] = evalue(None, False, 7, doctrine=doc)
        r = res['reperes'][doc]
        print('  repere scripte %-8s : prise %5.1f%%  expo/m %.4f  angle mort %4.1f%%'
              % (doc, 100 * r['prise'], r['expo_par_metre'], 100 * r['part_angle_mort']), flush=True)
    print('', flush=True)

    for voyant, nom in ((False, 'aveugle'), (True, 'voyant')):
        print('  --- bras %s ---' % nom.upper(), flush=True)
        for g in range(a.graines):
            seed = 7 + g
            try:
                _, piste = apprend(voyant, seed, nom)
                res['bras'][nom].append({'graine': seed, 'piste': piste, 'fin': piste[-1] if piste else None})
            except Exception as x:
                print('    (graine %d echouee : %s)' % (seed, str(x)[:90]), flush=True)
            json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)

    def moy(nom, cle):
        v = [b['fin'][cle] for b in res['bras'][nom] if b.get('fin')]
        return sum(v) / len(v) if v else float('nan')

    print('', flush=True)
    print('=== RESULTAT (moyenne des graines, fin d entrainement) ===', flush=True)
    print('  %-10s %10s %12s %12s' % ('', 'prise', 'expo/m', 'angle mort'), flush=True)
    for nom in ('aveugle', 'voyant'):
        print('  %-10s %9.1f%% %12.4f %11.1f%%'
              % (nom, 100 * moy(nom, 'prise'), moy(nom, 'expo_par_metre'), 100 * moy(nom, 'part_angle_mort')), flush=True)
    print('  %-10s %9.1f%% %12.4f %11.1f%%'
          % ('crochet', 100 * res['reperes']['flanc']['prise'], res['reperes']['flanc']['expo_par_metre'],
             100 * res['reperes']['flanc']['part_angle_mort']), flush=True)

    ea, ev = moy('aveugle', 'expo_par_metre'), moy('voyant', 'expo_par_metre')
    pa, pv = moy('aveugle', 'prise'), moy('voyant', 'prise')
    print('', flush=True)
    print('=== CONTRE-EPREUVE : le bras aveugle reproduit-il la nuit ? ===', flush=True)
    ok_ref = abs(pa - REF_AVEUGLE['prise']) < 0.12 and abs(ea - REF_AVEUGLE['expo']) < 0.010
    print('  attendu prise ~%.0f%% expo ~%.3f | obtenu %.1f%% %.4f -> %s'
          % (100 * REF_AVEUGLE['prise'], REF_AVEUGLE['expo'], 100 * pa, ea,
             'INSTRUMENT VALIDE' if ok_ref else 'DERIVE — la comparaison ne vaut rien'), flush=True)

    print('', flush=True)
    print('=== CONCLUSION (criteres figes, non negociables) ===', flush=True)
    if not ok_ref:
        print('  >>> le bras temoin ne reproduit pas la nuit : autre chose a bouge.', flush=True)
        print('      On ne conclut RIEN sur la perception tant que ce n est pas compris.', flush=True)
    elif ev <= SEUIL_EXPO and pv >= pa - 0.05:
        print('  >>> VOIR L ARC SUFFIT. L exposition tombe a %.4f (seuil %.3f) sans perdre' % (ev, SEUIL_EXPO), flush=True)
        print('      en prise. L agent ne manquait pas de manoeuvre : il manquait de VUE.', flush=True)
    elif ev < ea - 0.004:
        print('  >>> EFFET REEL MAIS PARTIEL : %.4f contre %.4f, sans atteindre %.3f.' % (ev, ea, SEUIL_EXPO), flush=True)
        print('      La vue compte, elle ne suffit pas. On enchaine sur l horizon.', flush=True)
    else:
        print('  >>> CE N EST PAS LA PERCEPTION : %.4f contre %.4f, dans le bruit.' % (ev, ea), flush=True)
        print('      Hypothese la moins chere ELIMINEE. On passe a l horizon.', flush=True)
        print('      Ce n est pas un echec : c est un resultat qui oriente la suite.', flush=True)

    res['bilan'] = {'expo_aveugle': ea, 'expo_voyant': ev, 'prise_aveugle': pa, 'prise_voyant': pv,
                    'seuil_expo': SEUIL_EXPO, 'contre_epreuve_ok': bool(ok_ref),
                    'duree_s': round(time.time() - t0)}
    json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s  (%.0f min)' % (LEV, a.out, (time.time() - t0) / 60.0), flush=True)
    print('ARC_DONE', flush=True)
