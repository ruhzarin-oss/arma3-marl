#!/usr/bin/env python3
"""mesure_alerte2.py — DEUX QUESTIONS QUI RESTAIENT.

Q5  ETRE VU SANS TIRER : le compteur monte-t-il quand l attaquant est simplement visible ?
    On rapproche l attaquant par paliers, en silence, sans jamais tirer.
Q6  LE PLAFOND : que se passe-t-il en arrivant a 4 ? A partir de quel niveau les defenseurs
    ENGAGENT-ILS reellement ? On tire de facon repetee et on regarde a la fois le compteur et
    le nombre de defenseurs qui ouvrent le feu.

Deja mesure (mesure_alerte.py) : silence a 200 m -> 0,00 ; un tir -> 0,30 sur les HUIT
simultanement, sans decroissance avec la distance ; delai 2-5 s ; memoire 90-120 s.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

T = theatre.use('altis')
Q = chr(34)
b = NativeBridge(port=T.PORT)
fx, fy = T.FOB


def q(sqf, motif, timeout=30):
    r = b.query(sqf, motif, want=1, timeout=timeout)
    return r[-1] if r else None


pose = ('if (!isNil %sHMT_AL%s) then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL }; '
        'HMT_AL=[]; HMT_DEF=[]; HMT_TIR=0; private _gd = createGroup east; ' % (Q, Q))
for i in range(8):
    pose += ('private _d%d = _gd createUnit [%sO_Soldier_F%s, [%d,%d,0], [], 0, %sNONE%s]; '
             '_d%d setPosATL [%d,%d,0]; _d%d setSkill 0.5; _d%d setBehaviour %sCOMBAT%s; '
             '_d%d setCombatMode %sRED%s; _d%d disableAI %sPATH%s; _d%d allowDamage false; '
             '_d%d addEventHandler [%sFired%s, { HMT_TIR = HMT_TIR + 1 }]; '
             'HMT_AL pushBack _d%d; HMT_DEF pushBack _d%d; '
             % (i, Q, Q, fx + (i - 4) * 25, fy, Q, Q, i, fx + (i - 4) * 25, fy, i, i, Q, Q,
                i, Q, Q, i, Q, Q, i, i, Q, Q, i, i))
pose += ('private _ga = createGroup west; '
         'HMT_ATT = _ga createUnit [%sB_Soldier_F%s, [%d,%d,0], [], 0, %sNONE%s]; '
         'HMT_ATT setPosATL [%d,%d,0]; HMT_ATT setSkill 0.5; HMT_ATT setUnitPos %sUP%s; '
         'HMT_ATT setBehaviour %sCOMBAT%s; HMT_ATT setCombatMode %sBLUE%s; '
         'HMT_ATT disableAI %sPATH%s; HMT_ATT disableAI %sAUTOTARGET%s; HMT_ATT allowDamage false; '
         'HMT_AL pushBack HMT_ATT; '
         % (Q, Q, fx, fy - 250, Q, Q, fx, fy - 250, Q, Q, Q, Q, Q, Q, Q, Q, Q, Q))
pose += '(format [%sPRET %%1%s, count HMT_DEF]) call HMT_EMIT;' % (Q, Q)
print('pose :', 'OK' if q(pose, r'PRET (\d+)', 90) else 'MUET')

LIRE = ('private _s = 0; { _s = _s + (_x knowsAbout HMT_ATT) } forEach HMT_DEF; '
        '(format [%sK %%1 %%2%s, round (_s / (count HMT_DEF) * 100), HMT_TIR]) call HMT_EMIT;' % (Q, Q))


def etat():
    r = q(LIRE, r'K (\d+) (\d+)')
    return (int(r.group(1)) / 100.0, int(r.group(2))) if r else (None, None)


print()
print('=== Q5 — ETRE VU SANS TIRER : on approche en silence ===')
print('  %8s %14s %10s' % ('distance', 'connaissance', 'tirs def.'))
for d in (250, 200, 150, 100, 60, 30):
    b.send('HMT_ATT setPosATL [%d,%d,0];' % (fx, fy - d), wait=False)
    time.sleep(8)
    k, tir = etat()
    print('  %6d m %13.2f %10s' % (d, k if k is not None else -1, tir))

print()
print('=== Q6 — LE PLAFOND : tirs repetes, quand engagent-ils ? ===')
print('  %6s %14s %12s' % ('tirs', 'connaissance', 'tirs def.'))
b.send('HMT_ATT setPosATL [%d,%d,0];' % (fx, fy - 150), wait=False)
time.sleep(5)
for n in range(1, 9):
    b.send('HMT_ATT reveal [(HMT_DEF select 4), 0.1]; HMT_ATT doTarget (HMT_DEF select 4); '
           'HMT_ATT doFire (HMT_DEF select 4);', wait=False)
    time.sleep(6)
    k, tir = etat()
    print('  %6d %13.2f %12s' % (n, k if k is not None else -1, tir), flush=True)

b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL; HMT_AL=[];', wait=False)
b.close()
print('MESURE_ALERTE2_DONE')
