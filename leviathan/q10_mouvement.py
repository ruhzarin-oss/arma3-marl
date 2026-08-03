#!/usr/bin/env python3
"""q10_mouvement.py — LA DETECTION D UN HOMME QUI COURT.

Mesure Q7, valide, mais sur un homme DEBOUT ET IMMOBILE :
    4,00 a 30 m | 1,72 a 60 m | 0,00 a partir de 100 m

Or l escouade COURT. Et le gymnase, avec le rayon immobile de 100 m, reste complaisant sur les
trois manoeuvres qui contournent : debordement a 27 % la ou le juge donne 0 %.

On mesure donc le meme balayage, mais avec un attaquant qui SE DEPLACE lateralement devant la
ligne — le mouvement est ce qui trahit. Meme instrument, meme pose, meme lecture : seule la
mobilite change. C est la comparaison qui donne le rayon a mettre dans le gymnase.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

T = theatre.use('altis')
b = NativeBridge(port=T.PORT)
fx, fy = T.FOB


def q(sqf, motif, timeout=30):
    r = b.query(sqf, motif, want=1, timeout=timeout)
    return r[-1] if r else None


def pose(dist):
    s = 'if (!isNil "HMT_AL") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL }; '
    s += 'HMT_AL=[]; HMT_DEF=[]; HMT_TIR=0; HMT_GD = createGroup east; '
    for i in range(4):
        x = fx + (i - 2) * 30
        s += ('_u = HMT_GD createUnit ["O_Soldier_F", [%d,%d,0], [], 0, "NONE"]; '
              '_u setPosATL [%d,%d,0]; _u setSkill 0.7; _u setBehaviour "COMBAT"; '
              '_u setCombatMode "RED"; _u allowDamage false; _u setVehicleAmmo 1; '
              '_u addEventHandler ["Fired", { HMT_TIR = HMT_TIR + 1 }]; '
              'HMT_AL pushBack _u; HMT_DEF pushBack _u; ' % (x, fy, x, fy))
    # attaquant : debout, arme, mais NE TIRE PAS (mode BLUE) — on isole la detection passive
    s += ('HMT_GA = createGroup west; '
          'HMT_ATT = HMT_GA createUnit ["B_Soldier_F", [%d,%d,0], [], 0, "NONE"]; '
          'HMT_ATT setPosATL [%d,%d,0]; HMT_ATT setSkill 0.7; HMT_ATT setUnitPos "UP"; '
          'HMT_ATT setBehaviour "COMBAT"; HMT_ATT setCombatMode "BLUE"; '
          'HMT_ATT allowDamage false; HMT_ATT setVehicleAmmo 1; HMT_AL pushBack HMT_ATT; '
          % (fx - 150, fy - dist, fx - 150, fy - dist))
    s += '(format ["PRET %1", count HMT_DEF]) call HMT_EMIT;'
    return q(s, r'PRET (\d+)', 90)


LIRE = ('private _t = 0; private _mx = 0; '
        '{ private _k = _x knowsAbout HMT_ATT; _t = _t + _k; if (_k > _mx) then {_mx = _k}; } forEach HMT_DEF; '
        '(format ["K %1 %2 %3", round (_t / (count HMT_DEF) * 100), round (_mx * 100), HMT_TIR]) call HMT_EMIT;')


def etat():
    r = q(LIRE, r'K (\d+) (\d+) (\d+)')
    return (int(r.group(1)) / 100.0, int(r.group(2)) / 100.0, int(r.group(3))) if r else None


print('=== Q10 — DETECTION D UN HOMME QUI COURT (deplacement lateral, ne tire pas) ===')
print('  rappel immobile : 4,00 a 30 m | 1,72 a 60 m | 0,00 a 100 m et au-dela')
print()
print('  %8s %11s %10s %12s' % ('distance', 'moyenne', 'max', 'tirs def.'))
seuil = None
for dist in (60, 100, 150, 200, 300):
    if not pose(dist):
        print('  %6d m  pose MUETTE' % dist); continue
    # il court lateralement devant la ligne, de -150 a +150 en x
    b.send('HMT_ATT forceSpeed 5; HMT_ATT doMove [%d,%d,0];' % (fx + 150, fy - dist), wait=False)
    time.sleep(30)
    e = etat()
    if e:
        if seuil is None and e[1] < 1.0:
            seuil = dist
        print('  %6d m %10.2f %9.2f %12d' % (dist, e[0], e[1], e[2]), flush=True)

print()
print('=== LECTURE ===')
print('  decrochage sous 1,0 en MOUVEMENT a partir de : %s'
      % (('%d m' % seuil) if seuil else 'jamais sur la plage testee'))
print('  contre 100 m a l arret. Si le rayon en mouvement est plus grand, c est lui qu il faut')
print('  mettre dans le gymnase : l escouade court, elle ne se promene pas.')
b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL; HMT_AL=[];', wait=False)
b.close()
print('Q10_DONE')
