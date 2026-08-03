#!/usr/bin/env python3
"""test_arc_integral — UNE SEULE VARIABLE ORDONNE-T-ELLE TOUT LE MONDE ?

Trois explications proposees aujourd'hui, trois dementies par leur propre mesure. Les trois
interventions ont pourtant marche. On sait quoi donner a l'agent ; on ne sait pas raconter
pourquoi. Ce banc essaie de fermer ca.

L'INDICE, dans nos propres chiffres : mes crochets de balayage coutent 0,0251 a 0,0285 ;
le crochet ORIGINAL coute 0,0136. Le double, a distance de virage comparable. Donc mes
copies ne font pas ce que fait l'original — et ce n'est pas le moment du virage, le
balayage vient de le prouver (amplitude x1,13 seulement).

L'HYPOTHESE UNIFIANTE :
    le prix = le TEMPS PASSE DANS UN ARC EFFICACE, pondere par le TARIF de la distance.
Le crochet le minimise en UN grand changement d'axe. L'agent au champ le minimise
CELLULE PAR CELLULE — et lui seul peut exploiter les fenetres qui s'ouvrent quand un
defenseur tombe ou tourne.

Si cette seule variable ordonne temoin, champ, crochet original, crochets balayes ET les
graines effondrees, « il se faufile » cesse d'etre une histoire et devient un chiffre.
Si elle n'ordonne pas : on arrete d'expliquer, on le note, et on laisse Arma juger.

Aucun reentrainement : on rejoue ce qui est deja enregistre.
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
ap.add_argument('--eval', type=int, default=400)
ap.add_argument('--device', default='cuda:0')
ap.add_argument('--out', default='arc_integral.json')
a = ap.parse_args()
DEV = a.device


def monde(seed, ne, champ=False, arc=True):
    return AssaultTerrain(num_envs=ne, A=4, D=4, seed=seed, device=DEV, max_steps=60,
                          postures=True, hull=True, def_line=True, def_arc=math.pi / 3,
                          def_rand=True, secure_task=True, secure_only=True,
                          courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC,
                          degat_par_impact=DEG, arc_obs=arc, champ_risque=champ)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


@torch.no_grad()
def temps_dans_arc(e):
    """Pour chaque attaquant vivant : est-il dans un arc EFFICACE, et a quel tarif ?

    « efficace » = un defenseur vivant l'a dans son cone ET le voit. Le tarif est le prix
    mesure sur Arma a cette distance — etre vu a 200 m coute 0,07 le pas, a 25 m 0,20.
    On rend deux nombres : la part d'agents dans un arc, et la meme ponderee par le tarif.
    """
    N, A, D = e.N, e.A, e.D
    brut = torch.zeros(N, A, device=DEV)
    tarife = torch.zeros(N, A, device=DEV)
    vivant = e._aalive().float()
    for di in range(D):
        bx = e.dpx[:, di:di + 1].expand(N, A); by = e.dpy[:, di:di + 1].expand(N, A)
        act = e._dalive()[:, di:di + 1].float().expand(N, A).clone()
        if e.def_line and hasattr(e, 'dface'):
            ang = torch.atan2(e.apx - bx, e.apy - by)
            adf = torch.atan2(torch.sin(ang - e.dface[:, di:di + 1]),
                              torch.cos(ang - e.dface[:, di:di + 1]))
            act = act * (adf.abs() <= e._dfarc).float()
        los = e._losc(e.hm, e.apx, e.apy, bx, by, e.scale, eye_a=e._eye(), eye_b=1.7)
        dist = torch.sqrt((e.apx - bx) ** 2 + (e.apy - by) ** 2)
        vu = (los * act).clamp(max=1.0)
        brut = torch.maximum(brut, vu)
        tarife = tarife + vu * e._p_balle(dist)          # le TARIF mesure sur Arma
    return (brut * vivant).sum(1), (tarife * vivant).sum(1)


def joue(net, seed, doctrine=None, champ=False, seuil_virage=None):
    e = monde(seed, a.eval, champ=champ)
    obs = e.reset(); N, A = e.N, e.A
    pris = torch.zeros(N, dtype=torch.bool, device=DEV); fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV); expo = torch.zeros(N, device=DEV)
    arc_brut = torch.zeros(N, device=DEV); arc_tar = torch.zeros(N, device=DEV)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()
    lat_tot = torch.zeros((), device=DEV); lat_dist = torch.zeros((), device=DEV)

    for t in range(60):
        d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        if doctrine == 'frontal':
            act = cap(-e.apx, -e.apy)
        elif doctrine == 'flanc':
            act = cap(-e.apx, -e.apy)
            fixe = torch.zeros(N, A, dtype=torch.bool, device=DEV); fixe[:, :2] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            if seuil_virage is None:
                if t < 14:                                    # LE CROCHET ORIGINAL : 14 pas de tangente
                    act = torch.where(~fixe, cap(-e.apy, e.apx), act)
            else:                                             # crochet BALAYE : tangente tant qu'on est loin
                act = torch.where((~fixe) & (d_obj > seuil_virage), cap(-e.apy, e.apx), act)
        else:
            with torch.no_grad():
                act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()

        vv = ~fini
        ab, at = temps_dans_arc(e)
        arc_brut = arc_brut + ab * vv.float()
        arc_tar = arc_tar + at * vv.float()
        _ax, _ay = e.apx.clone(), e.apy.clone(); _dav = torch.sqrt(_ax ** 2 + _ay ** 2)
        obs, _, done, info = e.step(act, auto_reset=False)
        _ux = -_ax / _dav.clamp(min=1e-6); _uy = -_ay / _dav.clamp(min=1e-6)
        _lat = ((e.apx - _ax) * (-_uy) + (e.apy - _ay) * _ux).abs()
        _m = vv.unsqueeze(1).float() * e._aalive().float()
        lat_tot = lat_tot + (_lat * _m).sum(); lat_dist = lat_dist + (_lat * _dav * _m).sum()
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
            'arc_par_metre': float((arc_brut / gagne).mean()),
            'arc_tarife_par_metre': float((arc_tar / gagne).mean()),
            'detour_a': float(lat_dist / lat_tot.clamp(min=1e-6))}


if __name__ == '__main__':
    print('=== UNE SEULE VARIABLE ORDONNE-T-ELLE TOUT LE MONDE ? ===', flush=True)
    print('    arc tarife = temps passe dans un arc efficace, pondere par le prix Arma', flush=True)
    print('    aucun reentrainement : on rejoue ce qui existe', flush=True)
    print('', flush=True)
    res = {}

    def m3(f):
        v = [f(s) for s in (7, 8, 9)]
        return {k: sum(x[k] for x in v) / len(v) for k in v[0]}

    res['frontal'] = m3(lambda s: joue(None, s, doctrine='frontal'))
    res['crochet_original'] = m3(lambda s: joue(None, s, doctrine='flanc'))
    for sv in (100, 140, 180):
        res['crochet_vire_%d' % sv] = m3(lambda s, q=sv: joue(None, s, doctrine='flanc', seuil_virage=q))

    for nom, champ, motif in (('appris_arc', False, 'champ_temoin_arc_g%d.pt'),
                              ('appris_champ', True, 'champ_arc_plus_champ_g%d.pt')):
        v = []
        for g in (7, 8, 9):
            f = LEV + '/' + (motif % g)
            if not os.path.exists(f):
                continue
            e = monde(g, 8, champ=champ); O = e.reset().shape[-1]
            net = Net(O, e.n_actions).to(DEV)
            net.load_state_dict(torch.load(f, map_location=DEV))
            v.append(joue(net, g + 1000, champ=champ))
        if v:
            res[nom] = {k: sum(x[k] for x in v) / len(v) for k in v[0]}

    print('%-20s %9s %11s %12s %13s' % ('', 'prise', 'expo/m', 'ARC TARIFE', 'detour a'), flush=True)
    for k, r in sorted(res.items(), key=lambda kv: kv[1]['arc_tarife_par_metre']):
        print('%-20s %8.1f%% %11.4f %12.4f %11.0f m'
              % (k, 100 * r['prise'], r['expo_par_metre'], r['arc_tarife_par_metre'], r['detour_a']), flush=True)

    print('', flush=True)
    print('=== LA VARIABLE ORDONNE-T-ELLE ? ===', flush=True)
    par_arc = sorted(res.items(), key=lambda kv: kv[1]['arc_tarife_par_metre'])
    par_expo = sorted(res.items(), key=lambda kv: kv[1]['expo_par_metre'])
    memes = [k for k, _ in par_arc] == [k for k, _ in par_expo]
    print('  classement par arc tarife  : %s' % ' < '.join(k for k, _ in par_arc), flush=True)
    print('  classement par exposition  : %s' % ' < '.join(k for k, _ in par_expo), flush=True)
    print('', flush=True)
    if memes:
        print('  >>> LES DEUX CLASSEMENTS COINCIDENT. Le temps dans un arc tarife EST le prix.', flush=True)
        print('      « il se faufile » devient un chiffre : le mecanisme est nomme.', flush=True)
    else:
        print('  >>> LES CLASSEMENTS DIFFERENT. Cette variable n explique pas tout.', flush=True)
        print('      On arrete d expliquer, on le note, et on laisse Arma juger.', flush=True)
    json.dump(res, open(LEV + '/' + a.out, 'w'), indent=1)
    print('', flush=True)
    print('-> %s/%s' % (LEV, a.out), flush=True)
    print('ARCINT_DONE', flush=True)
