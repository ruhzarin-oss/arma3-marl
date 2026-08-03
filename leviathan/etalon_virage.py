#!/usr/bin/env python3
"""etalon_virage.py — COMBIEN COUTE UN VIRAGE TARDIF ?

C'est la mesure qui peut TUER ma theorie, et c'est pour ca qu'elle passe en premier.

Ma theorie : l'agent appris contourne autant que le crochet scripte et dans les memes
secteurs, mais a 132 m au lieu de 184 m — donc il achete son ecart au TARIF FORT.
« Meme manoeuvre, meme quantite, mauvais moment. »

C'est une correlation, tiree de distributions mesurees. Ce n'est pas encore une cause.
Pour en faire un mecanisme au tarif connu, il faut un ETALON : la MEME doctrine, seule
la distance du virage change. Si le prix chute regulierement quand on vire plus loin, on
saura combien coute exactement « virer a 132 au lieu de 184 ». Si virer a 130 coute
presque autant qu'a 184, la theorie ne tient plus et le champ qui tourne repare peut-etre
quelque chose qui n'est pas casse.

Aucune politique apprise ici : que du scripte, pour que SEULE la distance de virage varie.
"""
import sys, json, math, argparse
sys.path.insert(0, '/home/younes/arma3-marl')
import torch
from assault_terrain import AssaultTerrain

LEV = '/home/younes/arma3-marl/leviathan'
COURBE = LEV + '/courbe_toucher_juge.json'
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument('--eval', type=int, default=400)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='etalon_virage.json')
a = ap.parse_args()
DEV = a.device

# distances de virage a comparer : on vire vers l'objectif DES QUE la distance passe
# sous le seuil. Seuil grand = on contourne tot et loin ; seuil petit = on contourne tard.
# distance a laquelle on COMMENCE a contourner (le depart est a ~170 m)
SEUILS = [170, 150, 130, 110, 90, 70]
PAS_ECART = 14        # duree de l'ecart, identique partout : SEULE la distance varie
FRONTAL = 'frontal'


def monde(seed, ne):
    return AssaultTerrain(num_envs=ne, A=4, D=4, seed=seed, device=DEV, max_steps=60,
                          postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
                          def_rand=True, secure_task=True, secure_only=True,
                          courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC,
                          degat_par_impact=DEG, arc_obs=True)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def joue(seuil, seed, n_fixe=2):
    """Crochet scripte parametre : les crocheteurs filent en TANGENTE tant qu'ils sont
    au-dela de `seuil` metres de l'objectif, puis rentrent. Seuil grand = virage tot et
    loin. `seuil=None` = assaut frontal pur (temoin bas)."""
    e = monde(seed, a.eval)
    e.reset(); N, A = e.N, e.A
    pris = torch.zeros(N, dtype=torch.bool, device=DEV); fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV); expo = torch.zeros(N, device=DEV)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()
    lat_tot = torch.zeros((), device=DEV); lat_dist = torch.zeros((), device=DEV)
    ecart_en_cours = torch.zeros(N, A, device=DEV)                       # pas d'ecart restants
    ecart_fait = torch.zeros(N, A, dtype=torch.bool, device=DEV)         # l'ecart a deja eu lieu

    for t in range(60):
        d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        act = cap(-e.apx, -e.apy)
        if seuil is not None:
            fixe = torch.zeros(N, A, dtype=torch.bool, device=DEV); fixe[:, :n_fixe] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            # APPROCHER DROIT, puis contourner PENDANT PAS_ECART pas des qu'on passe
            # sous `seuil`, puis rentrer. La duree de l'ecart est la meme partout :
            # seule la DISTANCE a laquelle il est paye change.
            declenche = (~fixe) & (d_obj <= seuil) & (~ecart_fait)
            ecart_en_cours = ecart_en_cours + declenche.float() * PAS_ECART
            en_ecart = ecart_en_cours > 0
            act = torch.where(en_ecart, cap(-e.apy, e.apx), act)
            ecart_en_cours = (ecart_en_cours - en_ecart.float()).clamp(min=0)
            ecart_fait = ecart_fait | declenche

        _ax, _ay = e.apx.clone(), e.apy.clone()
        _dav = torch.sqrt(_ax ** 2 + _ay ** 2)
        vivant = (~fini).unsqueeze(1).float() * e._aalive().float()
        _, _, done, info = e.step(act, auto_reset=False)

        _ux = -_ax / _dav.clamp(min=1e-6); _uy = -_ay / _dav.clamp(min=1e-6)
        _lat = ((e.apx - _ax) * (-_uy) + (e.apy - _ay) * _ux).abs()
        lat_tot = lat_tot + (_lat * vivant).sum()
        lat_dist = lat_dist + (_lat * _dav * vivant).sum()

        vv = ~fini
        pris = pris | (info['took'] & vv)
        pertes = torch.where(vv, info['losses'].float(), pertes)
        expo = expo + info['exposed'] * vv.float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(vv, d, dmin))
        fini = fini | done.bool()
        if bool(fini.all()):
            break

    gagne = (d0 - dmin).clamp(min=1.0)
    return {'prise': float(pris.float().mean()),
            'expo_par_metre': float((expo / gagne).mean()),
            'pertes_par_prise': float(pertes[pris].mean()) if bool(pris.any()) else float('nan'),
            'distance_du_detour': float(lat_dist / lat_tot.clamp(min=1e-6))}


if __name__ == '__main__':
    print('=== ETALON : COMBIEN COUTE UN VIRAGE TARDIF ? ===', flush=True)
    print('    meme doctrine, SEULE la distance de virage change | %d episodes x 3 graines' % a.eval, flush=True)
    print('', flush=True)
    res = {}

    def moy3(seuil):
        v = [joue(seuil, s) for s in (7, 8, 9)]
        return {k: sum(x[k] for x in v) / len(v) for k in v[0]}

    res['frontal'] = moy3(None)
    print('%-16s %10s %12s %14s' % ('virage a', 'prise', 'expo/m', 'detour a'), flush=True)
    print('%-16s %9.1f%% %12.4f %11.0f m'
          % ('(frontal pur)', 100 * res['frontal']['prise'], res['frontal']['expo_par_metre'],
             res['frontal']['distance_du_detour']), flush=True)
    for s in SEUILS:
        r = moy3(s)
        res['virage_%d' % s] = r
        lab = '%d m' % s
        print('%-16s %9.1f%% %12.4f %11.0f m'
              % (lab, 100 * r['prise'], r['expo_par_metre'], r['distance_du_detour']), flush=True)

    print('', flush=True)
    print('=== LECTURE ===', flush=True)
    util = [(s, res['virage_%d' % s]) for s in SEUILS]
    e_bas = min(r['expo_par_metre'] for _, r in util)
    e_haut = max(r['expo_par_metre'] for _, r in util)
    s_best = min(util, key=lambda x: x[1]['expo_par_metre'])[0]
    print('  le virage le moins cher est a %d m (%.4f) ; le plus cher a %.4f' % (s_best, e_bas, e_haut), flush=True)
    print('  amplitude du prix selon le SEUL moment du virage : x%.2f' % (e_haut / max(e_bas, 1e-6)), flush=True)
    r120 = res.get('virage_90', {}).get('expo_par_metre')
    r180 = res.get('virage_170', {}).get('expo_par_metre')
    print('', flush=True)
    if r120 and r180 and r120 > 1.25 * r180:
        print('  >>> LA THEORIE TIENT UN ETALON : virer tard (90 m) coute %.0f %% de plus'
              % (100 * (r120 / r180 - 1)), flush=True)
        print('      que virer loin (170 m), a doctrine IDENTIQUE. « Le moment » est un', flush=True)
        print('      mecanisme au tarif connu, plus seulement une correlation.', flush=True)
    elif r120 and r180:
        print('  >>> LA THEORIE EST EN DANGER : virer a 90 m coute %.4f, virer a 170 m %.4f.'
              % (r120, r180), flush=True)
        print('      Le moment du virage n explique PAS l ecart de l agent appris.', flush=True)
        print('      Il faut chercher ailleurs — horizon, oscillations, postures.', flush=True)
    # GARDE-FOU (leçon de la v1) : des reglages differents qui rendent le MEME chiffre
    # ne sont pas un balayage, c'est une seule experience deguisee.
    vals = [round(res['virage_%d' % s]['expo_par_metre'], 4) for s in SEUILS]
    if len(set(vals)) < len(vals) - 1:
        print('', flush=True)
        print('  [!] %d reglages sur %d rendent la MEME exposition : le balayage est factice.'
              % (len(vals) - len(set(vals)) + 1, len(vals)), flush=True)
        print('      NE RIEN CONCLURE — la doctrine ne varie pas comme on le croit.', flush=True)
    json.dump({'seuils': SEUILS, 'pas_ecart': PAS_ECART, 'resultats': res},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s' % (LEV, a.out), flush=True)
    print('ETALON_DONE', flush=True)
