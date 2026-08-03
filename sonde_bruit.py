#!/usr/bin/env python3
"""sonde_bruit — le canal BRUIT peut-il porter loin, et a quel prix pour le pont ?

Ce que la sonde FROLEMENT a etabli : `FiredNear` remonte bien, donne le tireur et la
distance, ne se declenche pas sur son propre tir — mais porte ~60 m, et il se MULTIPLIE
(20 tirs ont produit 85 evenements, un par voisin alerte).

Or la mesure du jour dit que l'agent doit savoir qu'il paie DES 170 m. A cette distance,
le frolement ne dit rien. Il faut le son.

Quatre questions, et rien d'autre :

  Q1  `FiredNear` porte-t-il au-dela de 60 m ? (on place des ecoutants a 60, 120, 250,
      500 et 900 m et on regarde qui est alerte)
  Q2  l'evenement `Fired` du TIREUR remonte-t-il, avec de quoi situer le coup ?
      C'est la voie alternative : UN evenement par coup, pas un par ecoutant.
  Q3  quel DEBIT sous rafale, dans chacune des deux voies ? C'est ce qui decide si le
      canal survit a 80 agents en contact.
  Q4  la voie « tireur » evite-t-elle vraiment la multiplication ?

Rien n'est branche. On pose des unites, on tire, on compte, on nettoie.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
DISTANCES = [60, 120, 250, 500, 900]
ZX, ZY = 23000, 17400


def _fermer(b):
    try:
        b.close()
    except Exception:
        pass


def main(nom='altis'):
    T = theatre.use(nom)
    b = NativeBridge(port=T.PORT)
    print('=== sonde BRUIT — theatre %s, port %d ===' % (nom, T.PORT), flush=True)
    r = b.query('(format [' + Q + 'PING ' + P + '1' + Q + ', round diag_tickTime]) call HMT_EMIT;',
                r'PING (\d+)', want=1, timeout=20)
    if not r:
        print('  pont MUET — rien d autre n a de sens.'); _fermer(b); return
    print('  pont OK', flush=True)

    # --- mise en place : 1 tireur + des ecoutants a distances croissantes ---
    c = ['if (!isNil ' + Q + 'HMT_B' + Q + ') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_B }; '
         'HMT_B = []; HMT_NEAR = []; HMT_FIRED = 0; '
         '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; '
         'private _gt = createGroup east; '
         'private _t = _gt createUnit [' + Q + 'O_Soldier_F' + Q + ', [' + str(ZX) + ',' + str(ZY) + ',0], [], 0, ' + Q + 'NONE' + Q + ']; '
         '_t setPosATL [' + str(ZX) + ',' + str(ZY) + ',0]; _t allowDamage false; '
         '_t disableAI ' + Q + 'PATH' + Q + '; _t setVehicleAmmo 1; '
         # Q2 : UN evenement par coup, cote tireur, avec sa position
         '_t addEventHandler [' + Q + 'Fired' + Q + ', { HMT_FIRED = HMT_FIRED + 1; }]; '
         'HMT_TT = _t; HMT_B pushBack _t; ']
    for i, d in enumerate(DISTANCES):
        c.append(
            'private _ge' + str(i) + ' = createGroup west; '
            'private _e' + str(i) + ' = _ge' + str(i) + ' createUnit [' + Q + 'B_Soldier_F' + Q + ', '
            '[' + str(ZX) + ',' + str(ZY + d) + ',0], [], 0, ' + Q + 'NONE' + Q + ']; '
            '_e' + str(i) + ' setPosATL [' + str(ZX) + ',' + str(ZY + d) + ',0]; '
            '_e' + str(i) + ' allowDamage false; _e' + str(i) + ' disableAI ' + Q + 'PATH' + Q + '; '
            '_e' + str(i) + ' addEventHandler [' + Q + 'FiredNear' + Q + ', { '
            '  HMT_NEAR pushBack ' + str(d) + '; }]; '
            'HMT_B pushBack _e' + str(i) + '; ')
    c.append('(format [' + Q + 'PRET ' + P + '1' + Q + ', count HMT_B]) call HMT_EMIT;')
    r = b.query(''.join(c), r'PRET (\d+)', want=1, timeout=90)
    print('  unites en place : %s (attendu %d)' % (r[-1].group(1) if r else 'ECHEC', 1 + len(DISTANCES)), flush=True)
    if not r:
        _fermer(b); return
    time.sleep(2)

    # --- un tir unique ---
    b.send('HMT_TT setDir 0; HMT_TT forceWeaponFire [currentMuzzle HMT_TT, currentWeaponMode HMT_TT];', wait=False)
    time.sleep(3)
    rr = b.query('(format [' + Q + 'R1 ' + P + '1 ' + P + '2' + Q + ', HMT_NEAR, HMT_FIRED]) call HMT_EMIT;',
                 r'R1 \[([^\]]*)\] (\d+)', want=1, timeout=25)
    near = [x.strip() for x in rr[-1].group(1).split(',') if x.strip()] if rr else []
    fired = int(rr[-1].group(2)) if rr else 0
    print('', flush=True)
    print('  -- un tir unique --', flush=True)
    print('  Q1  ecoutants alertes par FiredNear : %s' % (near if near else 'AUCUN'), flush=True)
    print('      distances non alertees          : %s'
          % [d for d in DISTANCES if str(d) not in near], flush=True)
    print('  Q2  evenement Fired cote tireur     : %s' % ('OUI (%d)' % fired if fired else 'NON'), flush=True)

    # --- rafale : on compare le debit des deux voies ---
    b.send('HMT_NEAR = []; HMT_FIRED = 0;', wait=False)
    time.sleep(1)
    t0 = time.time()
    for _ in range(20):
        b.send('HMT_TT setVehicleAmmo 1; HMT_TT forceWeaponFire [currentMuzzle HMT_TT, currentWeaponMode HMT_TT];', wait=False)
        time.sleep(0.3)
    time.sleep(3)
    dt = time.time() - t0
    rr = b.query('(format [' + Q + 'R2 ' + P + '1 ' + P + '2' + Q + ', count HMT_NEAR, HMT_FIRED]) call HMT_EMIT;',
                 r'R2 (\d+) (\d+)', want=1, timeout=25)
    n_near = int(rr[-1].group(1)) if rr else -1
    n_fired = int(rr[-1].group(2)) if rr else -1
    print('', flush=True)
    print('  -- rafale : 20 tirs en %.1f s --' % dt, flush=True)
    print('  Q3  voie FROLEMENT (un par ecoutant) : %d evenements' % n_near, flush=True)
    print('      voie TIREUR    (un par coup)     : %d evenements' % n_fired, flush=True)
    if n_fired > 0:
        print('  Q4  multiplication frolement/tireur  : x%.1f' % (n_near / float(n_fired)), flush=True)

    b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_B; HMT_B = []; '
           '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;', wait=False)
    time.sleep(2)
    _fermer(b)

    print('', flush=True)
    print('  === ce que ca decide ===', flush=True)
    loin = [d for d in DISTANCES if str(d) in near]
    if loin and max(loin) > 150:
        print('  FiredNear porte jusqu a %d m : le canal lointain existe nativement.' % max(loin), flush=True)
    else:
        print('  FiredNear ne porte PAS au-dela du contact. L alerte lointaine devra etre', flush=True)
        print('  CONSTRUITE : un evenement par COUP cote tireur, et c est nous qui decidons', flush=True)
        print('  qui entend quoi. Avantage : un evenement par coup au lieu d un par ecoutant.', flush=True)
    print('SONDE_BRUIT_DONE', flush=True)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'altis')
