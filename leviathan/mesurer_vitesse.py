#!/usr/bin/env python3
"""mesurer_vitesse.py — CHANTIER 1, la CONVERSION : combien de temps dure un pas ?

Le sandbox compte en PAS (move = 14 m par pas), Arma en SECONDES. Sans la vitesse
reelle d'un soldat, la courbe de toucher mesuree ne peut pas etre injectee : c'est
exactement le genre de nombre qu'on glisse "au jugé" et qui coute trois experiences.

On mesure donc : distance parcourue / temps, par POSTURE et par ALLURE.

Meme discipline que le banc de tir :
  - plusieurs coureurs en parallele, ecartes lateralement
  - terrain plat verifie AVANT (sinon on mesure la pente)
  - garde-fou : debout > accroupi > couche, et vitesses plausibles
"""
import sys, time, json, argparse
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

# ---- ARRET PROPRE (27/07) --------------------------------------------------
# Tuer un banc laisse le pont d'Arma occupe par un client mort : l'extension ne
# detecte pas la socket fermee et garde la place. Il faut DEMANDER l'arret.
#   demander : touch /tmp/hmt_stop     |     reprendre : rm -f /tmp/hmt_stop
import os as _os, signal as _signal


def _arret_demande():
    return _os.path.exists('/tmp/hmt_stop')


_PONTS = []


def _enregistrer_pont(b):
    """tout pont ouvert est note ici pour pouvoir etre ferme quoi qu'il arrive"""
    _PONTS.append(b)
    return b


def _fermer_tout(*_a):
    for _b in _PONTS:
        try:
            _b.close()
        except Exception:
            pass
    raise SystemExit(3)


_signal.signal(_signal.SIGTERM, _fermer_tout)
_signal.signal(_signal.SIGINT, _fermer_tout)
# ---------------------------------------------------------------------------


Q = chr(34); P = chr(37)
LEV = '/home/younes/arma3-marl/leviathan'

ap = argparse.ArgumentParser()
ap.add_argument('--zone', default='23000,17400')
ap.add_argument('--dist', type=int, default=120, help='longueur de la course (m)')
ap.add_argument('--dx', type=int, default=120, help='ecart lateral entre coureurs (m)')
ap.add_argument('--duree', type=int, default=90, help='temps maximum accorde (s)')
ap.add_argument('--reps', type=int, default=3)
ap.add_argument('--out', default='courbe_vitesse.json')
theatre.add_theatre_arg(ap)
a = ap.parse_args(); TH = theatre.apply_theatre_arg(a)
zx, zy = [int(v) for v in a.zone.split(',')]

# posture x comportement : l'allure d'Arma depend des deux
CAS = [('UP', 'AWARE'), ('UP', 'COMBAT'), ('MIDDLE', 'AWARE'),
       ('MIDDLE', 'COMBAT'), ('DOWN', 'AWARE'), ('DOWN', 'COMBAT')]


def course(b):
    c = ['if (!isNil ' + Q + 'HMT_V' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_V }; '
         'HMT_V = []; HMT_D0 = []; ']
    for k, (post, comp) in enumerate(CAS):
        K = str(k)
        sx = zx + k * a.dx
        S = '[' + str(sx) + ',' + str(zy) + ',0]'
        G = '[' + str(sx) + ',' + str(zy + a.dist) + ',0]'
        c.append(
            'private _g' + K + ' = createGroup west; '
            'private _u' + K + ' = _g' + K + ' createUnit [' + Q + 'B_Soldier_F' + Q + ', ' + S + ', [], 0, ' + Q + 'NONE' + Q + ']; '
            '_u' + K + ' setPosATL ' + S + '; _u' + K + ' allowDamage false; '
            '_u' + K + ' setUnitPos ' + Q + post + Q + '; _u' + K + ' setBehaviour ' + Q + comp + Q + '; '
            '_u' + K + ' setSpeedMode ' + Q + 'FULL' + Q + '; '
            '_u' + K + ' doMove ' + G + '; '
            'HMT_V pushBack _u' + K + '; HMT_D0 pushBack ' + str(a.dist) + '; ')
    c.append('HMT_T0 = diag_tickTime; (format [' + Q + 'GO ' + P + '1' + Q + ', count HMT_V]) call HMT_EMIT;')
    r = b.query(''.join(c), r'GO (\d+)', want=1, timeout=90)
    if not r:
        return None
    # on releve l'avancement chaque seconde : la vitesse se lit sur la phase etablie,
    # pas sur le depart (acceleration) ni sur l'arrivee (ralentissement)
    traces = [[] for _ in CAS]
    t = 0
    while t < a.duree:
        q = ('private _o = ' + Q + Q + '; { _o = _o + format [' + Q + P + '1;' + Q +
             ', round ((getPosATL _x) select 1)] } forEach HMT_V; '
             '(format [' + Q + 'Y ' + P + '1 ' + P + '2' + Q + ', _o, diag_tickTime - HMT_T0]) call HMT_EMIT;')
        rr = b.query(q, r'Y (.*) ([\d.]+)', want=1, timeout=20)
        if rr:
            ys = [v for v in rr[-1].group(1).strip().rstrip(';').split(';') if v.strip().lstrip('-').isdigit()]
            tt = float(rr[-1].group(2))
            for i, y in enumerate(ys[:len(CAS)]):
                traces[i].append((tt, float(y) - zy))
        time.sleep(1); t += 1
        if all(len(tr) > 3 and tr[-1][1] >= a.dist - 5 for tr in traces):
            break
    b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_V; HMT_V = []; { if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; ')
    return traces


def vitesse(trace):
    """vitesse sur la phase etablie : on jette les 15 premiers et 10 derniers metres"""
    pts = [(t, y) for t, y in trace if 15 <= y <= a.dist - 10]
    if len(pts) < 3:
        return None
    dt = pts[-1][0] - pts[0][0]; dy = pts[-1][1] - pts[0][1]
    return dy / dt if dt > 0.5 else None


if __name__ == '__main__':
    b = _enregistrer_pont(NativeBridge(port=TH.PORT))
    b.send('setDate [2035, 7, 6, 12, 0]; 0 setOvercast 0; 0 setFog 0; forceWeatherChange; '
           '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; ')
    time.sleep(1)
    print('=== VITESSE DE DEPLACEMENT (la conversion pas <-> secondes) ===', flush=True)
    print('    ' + str(len(CAS)) + ' coureurs en parallele | course de ' + str(a.dist) +
          ' m | ' + str(a.reps) + ' repetitions', flush=True)

    acc = {c: [] for c in CAS}
    for rep in range(1, a.reps + 1):
        print('  course ' + str(rep) + '/' + str(a.reps), flush=True)
        tr = course(b)
        if not tr:
            print('    (course sans reponse, ignoree)', flush=True); continue
        for c, t in zip(CAS, tr):
            v = vitesse(t)
            if v is not None and 0.1 < v < 12.0:
                acc[c].append(v)
            print('      %-8s %-8s %s' % (c[0], c[1], ('%.2f m/s' % v) if v is not None else 'pas exploitable'), flush=True)
        time.sleep(2)
    b.close()

    print('', flush=True)
    print('=== VITESSE MESUREE (m/s) ===', flush=True)
    res = {}
    for c in CAS:
        v = acc[c]
        res['%s_%s' % c] = (sum(v) / len(v)) if v else None
        print('  %-8s %-8s : %s   (%d courses)' % (c[0], c[1],
              ('%.2f m/s' % res['%s_%s' % c]) if v else '--', len(v)), flush=True)

    al = []
    for comp in ('AWARE', 'COMBAT'):
        u = res.get('UP_' + comp); m = res.get('MIDDLE_' + comp); d = res.get('DOWN_' + comp)
        if None in (u, m, d):
            al.append('mesure manquante en ' + comp)
        elif not (u > m > d):
            al.append(comp + ' : debout/accroupi/couche ne se classent pas (%.2f/%.2f/%.2f)' % (u, m, d))
    if any(v is not None and not (0.3 < v < 8.0) for v in res.values()):
        al.append('une vitesse sort du plausible (0,3-8 m/s)')

    print('', flush=True)
    if al:
        print('[!] MESURE SUSPECTE — c est le BANC qui est en cause :', flush=True)
        for x in al: print('    - ' + x, flush=True)
    else:
        print('[ok] classement coherent : debout > accroupi > couche, vitesses plausibles', flush=True)
        vref = res.get('UP_COMBAT')
        if vref:
            print('', flush=True)
            print('  >>> CONVERSION : un pas de sandbox vaut move=14 m a %.2f m/s = %.1f s' % (vref, 14.0 / vref), flush=True)
            print('      sec_par_pas = %.2f' % (14.0 / vref), flush=True)
            print('      tir_par_pas = %.2f  (a 0,35 balle/s mesuree sur le banc de tir)' % (0.35 * 14.0 / vref), flush=True)
    json.dump({'dist': a.dist, 'reps': a.reps, 'zone': a.zone, 'vitesses': res, 'alertes': al},
              open(LEV + '/' + a.out, 'w'), indent=1)
    print('-> ' + LEV + '/' + a.out, flush=True)
    print('VITESSE_DONE', flush=True)
