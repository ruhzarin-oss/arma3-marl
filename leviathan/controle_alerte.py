#!/usr/bin/env python3
"""controle_alerte.py — LE CONTROLE POSITIF QUE J AURAIS DU FAIRE D ABORD.

Deux mesures d alerte ont rendu des zeros invraisemblables, et la premiere mesurait en realite
mon propre ordre `reveal`. Avant de faire dire quoi que ce soit a cet instrument, il doit
detecter un cas CONNU POSITIF.

Cas positif : un attaquant debout a 30 m, arme, en mode de tir reel, rien de desactive.
S ils riposent et que le compteur reste a zero -> ma LECTURE est fausse.
S ils ne riposent pas -> la POSE est fausse.
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


pose = ('if (!isNil %sHMT_AL%s) then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL }; '
        'HMT_AL=[]; HMT_DEF=[]; HMT_TIR=0; HMT_TIRA=0; private _gd = createGroup east; ' % (Q, Q))
for i in range(4):
    pose += ('private _d%d = _gd createUnit [%sO_Soldier_F%s, [%d,%d,0], [], 0, %sNONE%s]; '
             '_d%d setPosATL [%d,%d,0]; _d%d setSkill 0.7; _d%d setBehaviour %sCOMBAT%s; '
             '_d%d setCombatMode %sRED%s; _d%d allowDamage false; '
             '_d%d addEventHandler [%sFired%s, { HMT_TIR = HMT_TIR + 1 }]; '
             'HMT_AL pushBack _d%d; HMT_DEF pushBack _d%d; '
             % (i, Q, Q, fx + (i - 2) * 15, fy, Q, Q, i, fx + (i - 2) * 15, fy, i, i, Q, Q,
                i, Q, Q, i, i, Q, Q, i, i))
pose += ('private _ga = createGroup west; '
         'HMT_ATT = _ga createUnit [%sB_Soldier_F%s, [%d,%d,0], [], 0, %sNONE%s]; '
         'HMT_ATT setPosATL [%d,%d,0]; HMT_ATT setSkill 0.7; HMT_ATT setUnitPos %sUP%s; '
         'HMT_ATT setBehaviour %sCOMBAT%s; HMT_ATT setCombatMode %sRED%s; HMT_ATT allowDamage false; '
         'HMT_ATT addEventHandler [%sFired%s, { HMT_TIRA = HMT_TIRA + 1 }]; '
         'HMT_AL pushBack HMT_ATT; '
         % (Q, Q, fx, fy - 30, Q, Q, fx, fy - 30, Q, Q, Q, Q, Q, Q, Q, Q))
pose += '(format [%sPRET %%1%s, count HMT_DEF]) call HMT_EMIT;' % (Q, Q)
print('pose :', 'OK' if q(pose, r'PRET (\d+)', 90) else 'MUET')

LIRE = ('private _s = 0; private _mx = 0; '
        '{ private _k = _x knowsAbout HMT_ATT; _s = _s + _k; if (_k > _mx) then {_mx = _k}; } forEach HMT_DEF; '
        '(format [%sK %%1 %%2 %%3 %%4%s, round (_s / (count HMT_DEF) * 100), round (_mx * 100), '
        'HMT_TIR, HMT_TIRA]) call HMT_EMIT;' % (Q, Q))

print()
print('=== CONTROLE POSITIF : attaquant debout, arme, a 30 m, RIEN de desactive ===')
print('  %5s %12s %10s %12s %12s' % ('t', 'moyenne', 'max', 'tirs def.', 'tirs att.'))
for t in range(0, 61, 10):
    if t:
        time.sleep(10)
    r = q(LIRE, r'K (\d+) (\d+) (\d+) (\d+)')
    if r:
        print('  %4ds %11.2f %9.2f %10s %12s'
              % (t, int(r.group(1)) / 100.0, int(r.group(2)) / 100.0, r.group(3), r.group(4)), flush=True)
    else:
        print('  %4ds  MUET' % t)

print()
print('=== LECTURE ===')
r = q(LIRE, r'K (\d+) (\d+) (\d+) (\d+)')
if r:
    moy, mx, td, ta = int(r.group(1)) / 100.0, int(r.group(2)) / 100.0, int(r.group(3)), int(r.group(4))
    if td > 0 and mx == 0.0:
        print('  >>> LA LECTURE EST FAUSSE. Ils riposent (%d tirs) et le compteur reste a zero.' % td)
    elif td == 0 and mx == 0.0:
        print('  >>> LA POSE EST FAUSSE. A 30 m, debout, arme, ils ne voient rien et ne tirent pas.')
    else:
        print('  >>> INSTRUMENT VALIDE : connaissance max %.2f, %d tirs defenseurs, %d tirs attaquant.'
              % (mx, td, ta))
        print('      On peut maintenant mesurer la dynamique d alerte.')
b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL; HMT_AL=[];', wait=False)
b.close()
print('CONTROLE_ALERTE_DONE')
