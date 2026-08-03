#!/usr/bin/env python3
"""mesure_alerte3.py — LES DEUX VRAIES QUESTIONS, avec un instrument VALIDE.

L instrument a passe son controle positif : a 30 m, debout et arme, la connaissance monte a
4,00 en moins de dix secondes et les defenseurs tirent 228 fois par minute. Les deux mesures
precedentes rendaient zero parce que j avais desactive le mode de tir de l attaquant — je
mesurais mes propres reglages, pour la treizieme fois.

Q7  LA COURBE DE DETECTION PASSIVE : a quelle distance la connaissance decroche de 4 ?
    Attaquant debout, arme, IMMOBILE, qui NE TIRE PAS. On balaie la distance.
    -> c est la loi de detection que le gymnase remplacera par son cone de camera.

Q8  LE COUT D UN TIR QUAND PERSONNE NE REGARDE : attaquant hors de portee de detection
    passive (distance trouvee en Q7), qui tire UNE FOIS. De combien monte la connaissance,
    chez qui, et pendant combien de temps ?
    -> c est le prix de l action que l agent devra arbitrer.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

T = theatre.use('altis'); Q = chr(34)
b = NativeBridge(port=T.PORT)
fx, fy = T.FOB


def q(sqf, motif, timeout=30):
    r = b.query(sqf, motif, want=1, timeout=timeout)
    return r[-1] if r else None


def pose(n_def=4, dist=30, tir_att=True):
    s = ('if (!isNil %sHMT_AL%s) then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL }; '
         'HMT_AL=[]; HMT_DEF=[]; HMT_TIR=0; HMT_TIRA=0; private _gd = createGroup east; ' % (Q, Q))
    for i in range(n_def):
        s += ('private _d%d = _gd createUnit [%sO_Soldier_F%s, [%d,%d,0], [], 0, %sNONE%s]; '
              '_d%d setPosATL [%d,%d,0]; _d%d setSkill 0.7; _d%d setBehaviour %sCOMBAT%s; '
              '_d%d setCombatMode %sRED%s; _d%d allowDamage false; '
              '_d%d addEventHandler [%sFired%s, { HMT_TIR = HMT_TIR + 1 }]; '
              'HMT_AL pushBack _d%d; HMT_DEF pushBack _d%d; '
              % (i, Q, Q, fx + (i - n_def // 2) * 30, fy, Q, Q, i,
                 fx + (i - n_def // 2) * 30, fy, i, i, Q, Q, i, Q, Q, i, i, Q, Q, i, i))
    # MODE DE TIR REEL POUR QUE doFire FONCTIONNE, MAIS CIBLAGE AUTOMATIQUE COUPE :
    # sinon l attaquant tire de lui-meme et se revele avant l ordre. Mesure invalidee
    # une premiere fois par cette faute — connaissance deja a 4,00 avant le tir.
    mode = 'RED' if tir_att else 'BLUE'
    auto = '' if not tir_att else 'HMT_ATT disableAI %sAUTOTARGET%s; ' % (Q, Q)
    s += ('private _ga = createGroup west; '
          'HMT_ATT = _ga createUnit [%sB_Soldier_F%s, [%d,%d,0], [], 0, %sNONE%s]; '
          'HMT_ATT setPosATL [%d,%d,0]; HMT_ATT setSkill 0.7; HMT_ATT setUnitPos %sUP%s; '
          'HMT_ATT setBehaviour %sCOMBAT%s; HMT_ATT setCombatMode %s%s%s; HMT_ATT allowDamage false; '
          'HMT_ATT disableAI %sPATH%s; '
          + auto + 'HMT_ATT addEventHandler [%sFired%s, { HMT_TIRA = HMT_TIRA + 1 }]; HMT_AL pushBack HMT_ATT; '
          % (Q, Q, fx, fy - dist, Q, Q, fx, fy - dist, Q, Q, Q, Q, Q, mode, Q, Q, Q, Q, Q))
    s += '(format [%sPRET %%1%s, count HMT_DEF]) call HMT_EMIT;' % (Q, Q)
    return q(s, r'PRET (\d+)', 90)


LIRE = ('private _s = 0; private _mx = 0; '
        '{ private _k = _x knowsAbout HMT_ATT; _s = _s + _k; if (_k > _mx) then {_mx = _k}; } forEach HMT_DEF; '
        '(format [%sK %%1 %%2 %%3 %%4%s, round (_s / (count HMT_DEF) * 100), round (_mx * 100), '
        'HMT_TIR, HMT_TIRA]) call HMT_EMIT;' % (Q, Q))


def etat():
    r = q(LIRE, r'K (\d+) (\d+) (\d+) (\d+)')
    if not r:
        return None
    return (int(r.group(1)) / 100.0, int(r.group(2)) / 100.0, int(r.group(3)), int(r.group(4)))


SAUTER_Q7 = True
print('=== Q7 — DETECTION PASSIVE : debout, arme, immobile, NE TIRE PAS ===')
print('  %8s %11s %10s %12s' % ('distance', 'moyenne', 'max', 'tirs def.'))
seuil = None
for d in ([] if SAUTER_Q7 else [30, 60, 100, 150, 200, 300, 400]):
    if not pose(4, d, tir_att=False):
        print('  %6d m  pose MUETTE' % d); continue
    time.sleep(20)
    e = etat()
    if e:
        moy, mx, td, _ = e
        if seuil is None and mx < 1.0:
            seuil = d
        print('  %6d m %10.2f %9.2f %12d' % (d, moy, mx, td), flush=True)
print('  -> decrochage sous 1,0 a partir de : %s' % (('%d m' % seuil) if seuil else 'jamais sur la plage'))

d_loin = 150   # mesure Q7 : invisible des 100 m, on prend 150 pour la marge
print()
print('=== Q8 — UN SEUL TIR, hors de portee de detection passive (%d m) ===' % d_loin)
pose(4, d_loin, tir_att=True)
time.sleep(15)
e = etat(); print('  avant le tir : moyenne %.2f  max %.2f' % (e[0], e[1]) if e else '  MUET')
b.send('HMT_ATT doTarget (HMT_DEF select 1); HMT_ATT doFire (HMT_DEF select 1);', wait=False)
print('  %6s %11s %10s %12s %12s' % ('t', 'moyenne', 'max', 'tirs def.', 'tirs att.'))
for t in (3, 6, 10, 20, 40, 70, 110):
    time.sleep(3 if t == 3 else (3 if t == 6 else (4 if t == 10 else (10 if t == 20 else (20 if t == 40 else 30)))))
    e = etat()
    if e:
        print('  %5ds %10.2f %9.2f %12d %12d' % (t, e[0], e[1], e[2], e[3]), flush=True)

b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL; HMT_AL=[];', wait=False)
b.close()
print('MESURE_ALERTE3_DONE')
