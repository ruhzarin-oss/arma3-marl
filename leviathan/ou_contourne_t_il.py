#!/usr/bin/env python3
"""ou_contourne_t_il.py — A QUELLE DISTANCE LE DETOUR EST-IL PAYE ?

Ce que les mesures precedentes ont etabli :
  - l'appris va autant sur le flanc que le crochet scripte (19-20 % contre 22 %)
  - il fait le meme detour en distance (2,2-2,5 contre 2,0 de trajet par metre gagne)
  - et il paie DEUX FOIS plus cher en exposition (0,022-0,031 contre 0,014)

Meme quantite de detour, meme endroit dans le cone, double du risque. Il ne reste
qu'une variable : LE MOMENT.

L'exposition n'a pas le meme prix partout — c'est la courbe mesuree sur Arma : etre vu
a 200 m coute 0,07 par pas, a 25 m il coute 0,20. Trois fois plus cher.

HYPOTHESE : le crochet scripte contourne LOIN, des le depart, la ou etre vu est bon
marche. L'appris contourne TARD, pres de l'objectif, au tarif fort. Meme manoeuvre,
mauvais moment.

On mesure donc, pour chaque doctrine :
  - a quelle distance de l'objectif se produit le mouvement LATERAL (le detour)
  - a quelle distance se paie l'exposition (ou l'agent est-il vu, et combien ca coute)
  - le profil complet : distance -> part de mouvement lateral, et exposition subie

⚠️ Correction des deux defauts de l'instrument precedent :
  - le lateral se mesure a 90 deg (tangente), pas a 135 deg. Le crochet CONTOURNE,
    il ne RECULE pas — mon seuil precedent ratait exactement ce qu'il visait.
  - on ne compte plus des caps identiques (pollue par la geometrie de convergence)
    mais la composante REELLEMENT laterale du deplacement.
"""
import sys, os, json, math, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233
BANDES = [(0, 40), (40, 80), (80, 120), (120, 160), (160, 260)]   # distances a l'objectif

ap = argparse.ArgumentParser()
ap.add_argument('--eval', type=int, default=300)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='ou_contourne.json')
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


def joue(net, voyant, seed, doctrine=None):
    e = monde(voyant, seed, a.eval)
    obs = e.reset(); N, A = e.N, e.A
    fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    nb = len(BANDES)
    lat = torch.zeros(nb, device=DEV)      # deplacement lateral cumule par bande
    rad = torch.zeros(nb, device=DEV)      # deplacement vers l'objectif par bande
    expo = torch.zeros(nb, device=DEV)     # exposition subie par bande
    pas_b = torch.zeros(nb, device=DEV)    # pas passes dans la bande

    for t in range(60):
        if doctrine == 'frontal':
            act = cap(-e.apx, -e.apy)
        elif doctrine == 'flanc':
            act = cap(-e.apx, -e.apy)
            d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
            fixe = torch.zeros(N, A, dtype=torch.bool, device=DEV); fixe[:, :2] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            if t < 14:
                act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        else:
            with torch.no_grad():
                act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()

        ax, ay = e.apx.clone(), e.apy.clone()
        d_av = torch.sqrt(ax ** 2 + ay ** 2)                   # (N,A) distance avant le pas
        vivant = (~fini).unsqueeze(1).float() * e._aalive().float()
        obs, _, done, info = e.step(act, auto_reset=False)

        dx = e.apx - ax; dy = e.apy - ay
        # direction vers l'objectif (l'objectif est a l'origine)
        ux = -ax / d_av.clamp(min=1e-6); uy = -ay / d_av.clamp(min=1e-6)
        radial = dx * ux + dy * uy                              # progression vers l'objectif
        lateral = (dx * (-uy) + dy * ux).abs()                  # composante perpendiculaire = LE DETOUR
        ex = info['exposed'].unsqueeze(1).expand(N, A)

        for i, (lo, hi) in enumerate(BANDES):
            m = ((d_av >= lo) & (d_av < hi)).float() * vivant
            lat[i] += (lateral * m).sum(); rad[i] += (radial.clamp(min=0) * m).sum()
            expo[i] += (ex * m).sum(); pas_b[i] += m.sum()

        fini = fini | done.bool()
        if bool(fini.all()):
            break

    tot_lat = lat.sum().clamp(min=1e-6)
    return {
        'bandes': ['%d-%d m' % b for b in BANDES],
        'part_du_lateral': [float(x) for x in (lat / tot_lat)],          # OU se fait le detour
        'lateral_sur_radial': [float(x) for x in (lat / rad.clamp(min=1e-6))],
        'expo_par_pas': [float(x) for x in (expo / pas_b.clamp(min=1))],
        'part_de_l_expo': [float(x) for x in (expo / expo.sum().clamp(min=1e-6))],
        'distance_mediane_du_detour': float((lat * torch.tensor([(b[0] + b[1]) / 2.0 for b in BANDES],
                                                                device=DEV)).sum() / tot_lat),
    }


if __name__ == '__main__':
    print('=== OU LE DETOUR EST-IL PAYE ? ===', flush=True)
    print('    lateral mesure a 90 deg (le crochet CONTOURNE, il ne RECULE pas)', flush=True)
    print('', flush=True)
    res = {}
    for doc in ('frontal', 'flanc'):
        res['scripte_' + doc] = joue(None, False, 7, doctrine=doc)
    for nom, voyant in (('aveugle', False), ('voyant', True)):
        vals = []
        for g in (7, 8, 9):
            f = '%s/arc_%s_g%d.pt' % (LEV, nom, g)
            if not os.path.exists(f):
                continue
            e = monde(voyant, g, 8); O = e.reset().shape[-1]
            net = Net(O, e.n_actions).to(DEV)
            net.load_state_dict(torch.load(f, map_location=DEV))
            vals.append(joue(net, voyant, g + 1000))
        if vals:
            res['appris_' + nom] = {
                'bandes': vals[0]['bandes'],
                'part_du_lateral': [sum(v['part_du_lateral'][i] for v in vals) / len(vals) for i in range(len(BANDES))],
                'expo_par_pas': [sum(v['expo_par_pas'][i] for v in vals) / len(vals) for i in range(len(BANDES))],
                'part_de_l_expo': [sum(v['part_de_l_expo'][i] for v in vals) / len(vals) for i in range(len(BANDES))],
                'distance_mediane_du_detour': sum(v['distance_mediane_du_detour'] for v in vals) / len(vals),
            }

    ordre = [k for k in ('scripte_frontal', 'appris_aveugle', 'appris_voyant', 'scripte_flanc') if k in res]
    b = res[ordre[0]]['bandes']

    print('OU SE FAIT LE DETOUR (part du mouvement lateral, par bande de distance)', flush=True)
    print('%-18s' % '' + ''.join('%11s' % x for x in b), flush=True)
    for k in ordre:
        print('%-18s' % k + ''.join('%10.0f%%' % (100 * x) for x in res[k]['part_du_lateral']), flush=True)

    print('', flush=True)
    print('OU SE PAIE L EXPOSITION (part de l exposition totale)', flush=True)
    print('%-18s' % '' + ''.join('%11s' % x for x in b), flush=True)
    for k in ordre:
        print('%-18s' % k + ''.join('%10.0f%%' % (100 * x) for x in res[k]['part_de_l_expo']), flush=True)

    print('', flush=True)
    print('DISTANCE MOYENNE A LAQUELLE LE DETOUR EST FAIT', flush=True)
    for k in ordre:
        print('  %-18s %6.0f m' % (k, res[k]['distance_mediane_du_detour']), flush=True)

    print('', flush=True)
    print('=== LECTURE ===', flush=True)
    if 'scripte_flanc' in res and 'appris_voyant' in res:
        df = res['scripte_flanc']['distance_mediane_du_detour']
        da = res['appris_voyant']['distance_mediane_du_detour']
        print('  le crochet scripte contourne a %.0f m, l appris a %.0f m' % (df, da), flush=True)
        if df > da * 1.25:
            print('  >>> CONFIRME : le scripte paie son detour LOIN, ou etre vu est bon marche ;', flush=True)
            print('      l appris contourne TARD, au tarif fort. Meme manoeuvre, mauvais moment.', flush=True)
        elif da > df * 1.25:
            print('  >>> INVERSE : l appris contourne PLUS LOIN que le scripte. L ecart vient', flush=True)
            print('      d ailleurs — probablement de la maniere de RENTRER, pas de sortir.', flush=True)
        else:
            print('  >>> ILS CONTOURNENT AU MEME ENDROIT (%.0f contre %.0f m).' % (df, da), flush=True)
            print('      Ni le lieu, ni la quantite, ni le moment. Il faut chercher ailleurs :', flush=True)
            print('      regarder OU SE PAIE l exposition plutot que ou se fait le detour.', flush=True)
    json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s' % (LEV, a.out), flush=True)
    print('OU_DONE', flush=True)
