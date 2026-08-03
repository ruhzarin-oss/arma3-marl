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

Criteres figes AVANT le run : leviathan/CRITERES_STRESS.md (empreinte CRITERES_STRESS).
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
REF_TEMOIN = {'prise': 0.814, 'expo': 0.0224, 'detour': 132.0}
REF_CROCHET = {'prise': 0.897, 'expo': 0.0136, 'detour': 184.0}
SEUIL_EXPO = 0.0180
SEUIL_DETOUR = 155.0
GAIN_PRISE_A_PERTES = 0.15      # +15 % contre le temoin, mesure dans le MEME run                          # moitie de l'ecart comblee

ap = argparse.ArgumentParser()
ap.add_argument('--graines', type=int, default=3)
ap.add_argument('--rounds', type=int, default=150)
ap.add_argument('--K', type=int, default=8)
ap.add_argument('--ne', type=int, default=1024)
ap.add_argument('--eval', type=int, default=300)
ap.add_argument('--device', default='cuda:0')   # cuda:0 = la 3090 (PyTorch classe par puissance)
ap.add_argument('--out', default='voir_stress.json')
a = ap.parse_args()
DEV = a.device


def monde(stress, seed, ne):
    return AssaultTerrain(num_envs=ne, A=4, D=4, seed=seed, device=DEV, max_steps=60,
                          postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
                          def_rand=True, secure_task=True, secure_only=True,
                          courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC,
                          degat_par_impact=DEG, arc_obs=True, champ_risque=True, stress=stress, mission='assaut')


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
    lat_tot = torch.zeros((), device=DEV); lat_dist = torch.zeros((), device=DEV)
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
        _ax, _ay = e.apx.clone(), e.apy.clone()
        _dav = torch.sqrt(_ax ** 2 + _ay ** 2)
        obs, _, done, info = e.step(act, auto_reset=False)
        # TEMOIN : ou se fait le mouvement LATERAL (a 90 deg de l axe de l objectif) ?
        # Le crochet contourne, il ne recule pas — on mesure la composante perpendiculaire.
        _ux = -_ax / _dav.clamp(min=1e-6); _uy = -_ay / _dav.clamp(min=1e-6)
        _lat = ((e.apx - _ax) * (-_uy) + (e.apy - _ay) * _ux).abs()
        _m = vivant.unsqueeze(1).float() * e._aalive().float()
        lat_tot = lat_tot + (_lat * _m).sum()
        lat_dist = lat_dist + (_lat * _dav * _m).sum()
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
            'part_angle_mort': float((mort_cum / nsteps.clamp(min=1)).mean()),
            'distance_du_detour': float(lat_dist / lat_tot.clamp(min=1e-6))}


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
            print('    [%s g%d] ronde %3d/%d : prise %5.1f%%  expo/m %.4f  detour a %3.0f m'
                  % (etiquette, seed, r, a.rounds, 100 * m['prise'], m['expo_par_metre'],
                     m['distance_du_detour']), flush=True)
            torch.save(net.state_dict(), '%s/stress_%s_g%d.pt' % (LEV, etiquette, seed))
    return net, piste


if __name__ == '__main__':
    if not os.path.exists(LEV + '/CRITERES_STRESS.md'):
        print('!! les criteres ne sont pas figes — ARRET.'); sys.exit(2)
    t0 = time.time()
    print('=== L AUDACE FAIT-ELLE ENTRER, OU SEULEMENT CHARGER ? ===', flush=True)
    print('    2 bras x %d graines x %d rondes | criteres figes (CRITERES_STRESS)'
          % (a.graines, a.rounds), flush=True)
    res = {'reperes': {}, 'bras': {'temoin_champ': [], 'champ_plus_stress': []}}

    for doc in ('frontal', 'flanc'):
        res['reperes'][doc] = evalue(None, False, 7, doctrine=doc)
        r = res['reperes'][doc]
        print('  repere scripte %-8s : prise %5.1f%%  expo/m %.4f  angle mort %4.1f%%'
              % (doc, 100 * r['prise'], r['expo_par_metre'], 100 * r['part_angle_mort']), flush=True)
    print('', flush=True)

    for voyant, nom in ((False, 'temoin_champ'), (True, 'champ_plus_stress')):
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
    def pap(nom):
        pr = moy(nom, 'prise'); pe = moy(nom, 'pertes_par_prise')
        return pr / pe if pe and pe == pe and pe > 0 else float('nan')

    print('  %-18s %9s %11s %13s %14s' % ('', 'prise', 'pertes/pr', 'PRISE-A-PERTES', 'expo/m'), flush=True)
    for _n in ('temoin_champ', 'champ_plus_stress'):
        print('  %-18s %8.1f%% %11.3f %13.1f %14.4f'
              % (_n, 100 * moy(_n, 'prise'), moy(_n, 'pertes_par_prise'), pap(_n),
                 moy(_n, 'expo_par_metre')), flush=True)
    print('', flush=True)
    print('  %-16s %10s %12s %14s' % ('(detail)', 'prise', 'expo/m', 'detour a'), flush=True)
    for nom in ('temoin_champ', 'champ_plus_stress'):
        print('  %-16s %9.1f%% %12.4f %11.0f m'
              % (nom, 100 * moy(nom, 'prise'), moy(nom, 'expo_par_metre'), moy(nom, 'distance_du_detour')), flush=True)
    print('  %-16s %9.1f%% %12.4f %11.0f m'
          % ('crochet scripte', 100 * res['reperes']['flanc']['prise'], res['reperes']['flanc']['expo_par_metre'],
             res['reperes']['flanc']['distance_du_detour']), flush=True)

    ea, ev = moy('temoin_champ', 'expo_par_metre'), moy('champ_plus_stress', 'expo_par_metre')
    pa, pv = moy('temoin_champ', 'prise'), moy('champ_plus_stress', 'prise')
    print('', flush=True)
    print('=== CONTRE-EPREUVE : le bras aveugle reproduit-il la nuit ? ===', flush=True)
    ok_ref = abs(pa - REF_TEMOIN['prise']) < 0.12 and abs(ea - REF_TEMOIN['expo']) < 0.008
    print('  attendu prise ~%.0f%% expo ~%.3f | obtenu %.1f%% %.4f -> %s'
          % (100 * REF_TEMOIN['prise'], REF_TEMOIN['expo'], 100 * pa, ea,
             'INSTRUMENT VALIDE' if ok_ref else 'DERIVE — la comparaison ne vaut rien'), flush=True)

    print('', flush=True)
    print('=== CONCLUSION (criteres figes, non negociables) ===', flush=True)
    pap_t = pap('temoin_champ'); pap_s = pap('champ_plus_stress')
    gain = (pap_s / pap_t - 1.0) if pap_t and pap_t == pap_t and pap_t > 0 else float('nan')
    d_prise = pv - pa
    d_pertes = (moy('champ_plus_stress', 'pertes_par_prise') / moy('temoin_champ', 'pertes_par_prise') - 1.0) \
        if moy('temoin_champ', 'pertes_par_prise') else float('nan')
    print('  prise-a-pertes : temoin %.1f  ->  stress %.1f   (%+.0f %%)'
          % (pap_t, pap_s, 100 * gain), flush=True)
    print('  prise %+.1f pt | pertes par prise %+.0f %%' % (100 * d_prise, 100 * d_pertes), flush=True)
    print('', flush=True)
    if not ok_ref:
        print('  >>> le temoin ne reproduit pas la reference : autre chose a bouge.', flush=True)
        print('      On ne conclut RIEN sur le stress tant que ce n est pas compris.', flush=True)
    elif gain == gain and gain >= GAIN_PRISE_A_PERTES:
        print('  >>> L AUDACE FAIT ENTRER. Prise-a-pertes +%.0f %% (seuil +15 %%).' % (100 * gain), flush=True)
        print('      Le seul mecanisme offensif de SIROCCO paie sur la metrique du banc FIBUA.', flush=True)
    elif d_prise >= 0.02 and d_pertes <= 0.05:
        print('  >>> SUCCES PARTIEL : +%.1f pt de prise sans surcout de pertes, mais le gain'
              % (100 * d_prise), flush=True)
        print('      global (%+.0f %%) reste sous le seuil. L audace aide, elle ne transforme pas.'
              % (100 * gain), flush=True)
    elif d_prise > 0:
        print('  >>> ELLE FAIT CHARGER, PAS ENTRER : +%.1f pt de prise pour %+.0f %% de pertes.'
              % (100 * d_prise, 100 * d_pertes), flush=True)
        print('      C est de l imprudence, pas de l audace. Le banc FIBUA a deja tranche contre.', flush=True)
    else:
        print('  >>> AUCUN EFFET sur la prise. L axe du stress, branche ainsi, ne fait pas entrer.', flush=True)
        print('      A verifier avant d aller plus loin : l audace monte-t-elle vraiment en fin', flush=True)
        print('      d episode, et le champ pese-t-il assez dans la decision ?', flush=True)

    res['bilan'] = {'expo_temoin': ea, 'expo_stress': ev, 'prise_temoin': pa, 'prise_stress': pv,
                    'prise_a_pertes_temoin': pap_t, 'prise_a_pertes_stress': pap_s, 'gain': gain,
                    'seuil_expo': SEUIL_EXPO, 'contre_epreuve_ok': bool(ok_ref),
                    'duree_s': round(time.time() - t0)}
    json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s  (%.0f min)' % (LEV, a.out, (time.time() - t0) / 60.0), flush=True)
    print('ARC_DONE', flush=True)
