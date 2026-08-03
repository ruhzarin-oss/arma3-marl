#!/usr/bin/env python3
"""hesite_t_il.py — L'AGENT HESITE-T-IL VRAIMENT ?

Ma lecture : l'appris va autant sur le flanc que le crochet scripte (18-20 % du temps
contre 22 %), mais son exposition par metre est le double. Donc ce n'est pas OU il va,
c'est COMMENT il y va — il derive au lieu de s'engager, parce qu'il rejuge son cap
toutes les 3,3 secondes et qu'a chaque pas la tentation locale est d'aller vers
l'objectif.

C'est une LECTURE, pas une mesure. Avant de construire un remede, on verifie la maladie.
Trois chiffres, sur les politiques DEJA enregistrees, sans reentrainer :

  PERSISTANCE DE CAP    combien de pas consecutifs le meme cap est-il tenu ?
                        le crochet scripte en tient 14 d'affilee par construction
  EFFICACITE DE TRAJET  metres parcourus pour un metre gagne vers l'objectif
                        ligne droite = 1 ; crochet propre ~1,6 ; zigzag = 3 et plus
  RENONCEMENT           part des pas qui ELOIGNENT franchement de l'objectif (>90 deg),
                        et surtout leur longueur en BLOCS — manoeuvrer, c'est s'eloigner
                        longtemps et expres, pas par accident

Si ces chiffres separent le scripte de l'appris, la lecture tient. Sinon elle est fausse
et il ne faut RIEN construire.
"""
import sys, os, json, math, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain
from train_koth_gpu import Net

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument('--eval', type=int, default=300)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='hesitation.json')
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
    """rejoue une politique et compte comment elle SE CONDUIT, pas ce qu'elle obtient"""
    e = monde(voyant, seed, a.eval)
    obs = e.reset(); N, A = e.N, e.A
    fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    prev = torch.full((N, A), -1, dtype=torch.long, device=DEV)
    tenue = torch.zeros(N, A, device=DEV)          # longueur du cap en cours
    somme_tenue = torch.zeros(N, A, device=DEV)    # somme des longueurs achevees
    n_tenues = torch.zeros(N, A, device=DEV)       # nombre de caps distincts
    chemin = torch.zeros(N, device=DEV)            # metres parcourus
    loin = torch.zeros(N, A, device=DEV)           # pas qui eloignent (>90 deg)
    bloc_loin = torch.zeros(N, A, device=DEV)      # bloc d'eloignement en cours
    somme_bloc = torch.zeros(N, A, device=DEV); n_blocs = torch.zeros(N, A, device=DEV)
    nsteps = torch.zeros(N, device=DEV)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()

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

        vivant = (~fini).unsqueeze(1).float() * e._aalive().float()

        # --- persistance : le cap change-t-il ? (les actions >=8 ne sont pas des caps)
        est_cap = (act < 8)
        change = (act != prev) & est_cap
        somme_tenue = somme_tenue + torch.where(change, tenue, torch.zeros_like(tenue)) * vivant
        n_tenues = n_tenues + (change & (prev >= 0)).float() * vivant
        tenue = torch.where(change, torch.ones_like(tenue), tenue + 1.0)
        prev = torch.where(est_cap, act, prev)

        # --- renoncement : le cap choisi eloigne-t-il de l'objectif ?
        cible = cap(-e.apx, -e.apy)
        ecart = (act - cible).abs()
        ecart = torch.minimum(ecart, 8 - ecart)              # ecart circulaire en octants
        eloigne = (ecart >= 3) & est_cap                     # >= 135 deg : franchement a l'oppose
        loin = loin + eloigne.float() * vivant
        fin_bloc = (~eloigne) & (bloc_loin > 0)
        somme_bloc = somme_bloc + torch.where(fin_bloc, bloc_loin, torch.zeros_like(bloc_loin)) * vivant
        n_blocs = n_blocs + fin_bloc.float() * vivant
        bloc_loin = torch.where(eloigne, bloc_loin + 1.0, torch.zeros_like(bloc_loin))

        ax, ay = e.apx.clone(), e.apy.clone()
        obs, _, done, info = e.step(act, auto_reset=False)
        pas = torch.sqrt((e.apx - ax) ** 2 + (e.apy - ay) ** 2).mean(1)
        chemin = chemin + pas * (~fini).float()
        nsteps = nsteps + (~fini).float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(~fini, d, dmin))
        fini = fini | done.bool()
        if bool(fini.all()):
            break

    gagne = (d0 - dmin).clamp(min=1.0)
    persist = (somme_tenue.sum() / n_tenues.sum().clamp(min=1)).item()
    bloc = (somme_bloc.sum() / n_blocs.sum().clamp(min=1)).item()
    return {
        'persistance_cap': persist,                       # pas consecutifs par cap
        'trajet_par_metre_gagne': (chemin / gagne).mean().item(),
        'part_pas_eloignants': (loin.sum() / (nsteps.sum() * A).clamp(min=1)).item(),
        'longueur_bloc_eloignement': bloc,                # s'eloigne-t-il LONGTEMPS d'affilee ?
    }


if __name__ == '__main__':
    print('=== L AGENT HESITE-T-IL ? (rejeu des politiques deja enregistrees) ===', flush=True)
    print('    aucun reentrainement — on compte comment elles SE CONDUISENT', flush=True)
    print('', flush=True)
    res = {}

    for doc in ('frontal', 'flanc'):
        res['scripte_' + doc] = joue(None, False, 7, doctrine=doc)

    for nom, voyant in (('aveugle', False), ('voyant', True)):
        vals = []
        for g in (7, 8, 9):
            f = '%s/arc_%s_g%d.pt' % (LEV, nom, g)
            if not os.path.exists(f):
                print('  (manquant : %s)' % f, flush=True); continue
            e = monde(voyant, g, 8)
            O = e.reset().shape[-1]
            net = Net(O, e.n_actions).to(DEV)
            net.load_state_dict(torch.load(f, map_location=DEV))
            vals.append(joue(net, voyant, g + 1000))
        if vals:
            res['appris_' + nom] = {k: sum(v[k] for v in vals) / len(vals) for k in vals[0]}

    print('%-18s %12s %12s %12s %12s' % ('', 'persistance', 'trajet/m', 'part loin', 'bloc loin'), flush=True)
    ordre = ['scripte_frontal', 'appris_aveugle', 'appris_voyant', 'scripte_flanc']
    for k in ordre:
        if k not in res:
            continue
        r = res[k]
        print('%-18s %12.2f %12.2f %11.1f%% %12.2f'
              % (k, r['persistance_cap'], r['trajet_par_metre_gagne'],
                 100 * r['part_pas_eloignants'], r['longueur_bloc_eloignement']), flush=True)

    print('', flush=True)
    print('=== LECTURE ===', flush=True)
    if 'scripte_flanc' in res and 'appris_voyant' in res:
        pf = res['scripte_flanc']['persistance_cap']; pa = res['appris_voyant']['persistance_cap']
        tf = res['scripte_flanc']['trajet_par_metre_gagne']; ta = res['appris_voyant']['trajet_par_metre_gagne']
        bf = res['scripte_flanc']['longueur_bloc_eloignement']; ba = res['appris_voyant']['longueur_bloc_eloignement']
        print('  persistance de cap : scripte %.2f  vs  appris %.2f  (x%.1f)' % (pf, pa, pf / max(pa, 1e-6)), flush=True)
        print('  trajet par metre   : scripte %.2f  vs  appris %.2f' % (tf, ta), flush=True)
        print('  bloc d eloignement : scripte %.2f  vs  appris %.2f' % (bf, ba), flush=True)
        print('', flush=True)
        if pf > 1.8 * pa and ba < 0.7 * bf:
            print('  >>> L HESITATION EST CONFIRMEE. Le scripte TIENT un cap et s ELOIGNE par blocs ;', flush=True)
            print('      l appris rejuge sans cesse et ne s eloigne que par accident.', flush=True)
            print('      Construire un moyen de S ENGAGER a un sens.', flush=True)
        elif pf > 1.8 * pa:
            print('  >>> il rejuge plus souvent, mais il s eloigne autant. L hesitation est PARTIELLE :', flush=True)
            print('      le probleme est la CONTINUITE du cap, pas le renoncement.', flush=True)
        else:
            print('  >>> LA LECTURE EST FAUSSE : l appris ne rejuge pas plus que le scripte.', flush=True)
            print('      L ecart d exposition vient d ailleurs. NE RIEN CONSTRUIRE sur cette base.', flush=True)
    json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s' % (LEV, a.out), flush=True)
    print('HESITE_DONE', flush=True)
