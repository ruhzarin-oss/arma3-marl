#!/usr/bin/env python3
"""q11_survie.py — COMBIEN DE TEMPS SURVIT UN HOMME DETECTE SOUS LE FEU ?

Le probleme s est deplace. Ce n est plus << etre vu >> : le modele d alerte mesure a ramene
l ecart de 95 a 27 points. C est << survivre une fois vu >>. A A=4, l alerte du gymnase est a
3,72 — les defenseurs tirent quasiment a pleine puissance sur un contourneur detecte — et il
passe quand meme 27 % du temps. Chez le juge, jamais.

On mesure donc le TEMPS DE SURVIE d un attaquant detecte, a plusieurs distances, sous le feu de
huit defenseurs. Meme instrument que les mesures precedentes, validees par controle positif.

L attaquant est VULNERABLE ici (pas de allowDamage false), c est tout l objet de la mesure.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

T = theatre.use('altis')
b = NativeBridge(port=T.PORT)
fx, fy = T.FOB
N_ESSAIS = 12


def q(sqf, motif, timeout=30):
    r = b.query(sqf, motif, want=1, timeout=timeout)
    return r[-1] if r else None


def pose(dist, n_def=8):
    s = 'if (!isNil "HMT_AL") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL }; '
    s += 'HMT_AL=[]; HMT_DEF=[]; HMT_GD = createGroup east; '
    for i in range(n_def):
        x = fx + (i - n_def // 2) * 25
        s += ('_u = HMT_GD createUnit ["O_Soldier_F", [%d,%d,0], [], 0, "NONE"]; '
              '_u setPosATL [%d,%d,0]; _u setSkill 0.5; _u setBehaviour "COMBAT"; '
              '_u setCombatMode "RED"; _u allowDamage false; _u setVehicleAmmo 1; '
              'HMT_AL pushBack _u; HMT_DEF pushBack _u; ' % (x, fy, x, fy))
    # ATTAQUANT VULNERABLE : c est l objet de la mesure. Debout, il ne tire pas, il est revele.
    s += ('HMT_GA = createGroup west; '
          'HMT_ATT = HMT_GA createUnit ["B_Soldier_F", [%d,%d,0], [], 0, "NONE"]; '
          'HMT_ATT setPosATL [%d,%d,0]; HMT_ATT setSkill 0.5; HMT_ATT setUnitPos "UP"; '
          'HMT_ATT setBehaviour "COMBAT"; HMT_ATT setCombatMode "BLUE"; '
          'HMT_ATT setVehicleAmmo 1; HMT_ATT disableAI "PATH"; HMT_AL pushBack HMT_ATT; '
          '{ _x reveal [HMT_ATT, 4] } forEach HMT_DEF; '
          % (fx, fy - dist, fx, fy - dist))
    s += '(format ["PRET %1", count HMT_DEF]) call HMT_EMIT;'
    return q(s, r'PRET (\d+)', 90)


VIVANT = '(format ["V %1 %2", (alive HMT_ATT), round ((damage HMT_ATT) * 100)]) call HMT_EMIT;'


def survie(dist, limite=40):
    if not pose(dist):
        return None
    t0 = time.time()
    for _ in range(limite):
        time.sleep(1)
        r = q(VIVANT, r'V (\w+) (\d+)', 12)
        if not r:
            continue
        if r.group(1).lower() == 'false':
            return time.time() - t0, 100
    r = q(VIVANT, r'V (\w+) (\d+)', 12)
    return None, int(r.group(2)) if r else -1


print('=== Q11 — SURVIE D UN HOMME DETECTE, debout, sous le feu de 8 defenseurs ===')
print('  (il ne tire pas, il est revele, il est VULNERABLE)')
print()
print('  %8s %14s %14s' % ('distance', 'survie mediane', 'degats a 40 s'))
for dist in (30, 60):
    temps = []
    degats = []
    for e in range(N_ESSAIS):
        r = survie(dist)
        if r is None:
            continue
        t, dg = r
        if t is not None:
            temps.append(t)
        else:
            degats.append(dg)
    if temps:
        temps.sort()
        med = temps[len(temps) // 2]
        print('  %6d m %11.1f s  %5d morts sur %d' % (dist, med, len(temps), N_ESSAIS), flush=True)
    else:
        moy = sum(degats) / len(degats) if degats else -1
        print('  %6d m    survit 40 s   degats moyens %.0f %%' % (dist, moy), flush=True)

b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL; HMT_AL=[];', wait=False)
b.close()
print('Q11_DONE')
