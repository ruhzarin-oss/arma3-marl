#!/usr/bin/env python3
"""q8_cout_tir.py — LE PRIX D UN SEUL TIR QUAND PERSONNE NE REGARDE.

Mesure Q7, valide : un homme debout et arme est totalement connu a 30 m (4,00), a moitie a
60 m (1,72), INVISIBLE a 100 m et au-dela (0,00).

On place donc l attaquant a 150 m, hors de toute detection passive. Mode de tir REEL pour que
l ordre de tir fonctionne, mais CIBLAGE AUTOMATIQUE COUPE pour qu il ne se revele pas de
lui-meme — c est la faute qui a invalide la premiere tentative.

Puis un seul tir. De combien la connaissance monte-t-elle, chez qui, et combien de temps ?
C est le prix de l action que l agent devra arbitrer : tirer coute du renseignement.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

T = theatre.use('altis'); Q = chr(34)
b = NativeBridge(port=T.PORT)
fx, fy = T.FOB
D = 100   # distance exacte du banc de suppression qui MARCHE, et detection passive deja nulle


def q(sqf, motif, timeout=30):
    r = b.query(sqf, motif, want=1, timeout=timeout)
    return r[-1] if r else None


s = 'if (!isNil "HMT_AL") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL }; '
s += 'HMT_AL=[]; HMT_DEF=[]; HMT_TIR=0; HMT_TIRA=0; HMT_GD = createGroup east; '
for i in range(4):
    x = fx + (i - 2) * 30
    s += ('_u = HMT_GD createUnit ["O_Soldier_F", [%d,%d,0], [], 0, "NONE"]; '
          '_u setPosATL [%d,%d,0]; _u setSkill 0.7; _u setBehaviour "COMBAT"; '
          '_u setCombatMode "RED"; _u allowDamage false; '
          '_u addEventHandler ["Fired", { HMT_TIR = HMT_TIR + 1 }]; '
          'HMT_AL pushBack _u; HMT_DEF pushBack _u; ' % (x, fy, x, fy))
s += ('HMT_GA = createGroup west; '
      'HMT_ATT = HMT_GA createUnit ["B_Soldier_F", [%d,%d,0], [], 0, "NONE"]; '
      'HMT_ATT setPosATL [%d,%d,0]; HMT_ATT setSkill 0.7; HMT_ATT setUnitPos "UP"; '
      'HMT_ATT setBehaviour "COMBAT"; HMT_ATT setCombatMode "RED"; '
      'HMT_ATT disableAI "AUTOTARGET"; HMT_ATT disableAI "PATH"; HMT_ATT allowDamage false; HMT_ATT setVehicleAmmo 1; '
      'HMT_ATT addEventHandler ["Fired", { HMT_TIRA = HMT_TIRA + 1 }]; HMT_AL pushBack HMT_ATT; '
      % (fx, fy - D, fx, fy - D))
s += '(format ["PRET %1", count HMT_DEF]) call HMT_EMIT;'
print('pose a %d m :' % D, 'OK' if q(s, r'PRET (\d+)', 90) else 'MUET')

LIRE = ('private _t = 0; private _mx = 0; private _n = 0; '
        '{ private _k = _x knowsAbout HMT_ATT; _t = _t + _k; if (_k > _mx) then {_mx = _k}; '
        'if (_k > 0.05) then {_n = _n + 1}; } forEach HMT_DEF; '
        '(format ["K %1 %2 %3 %4 %5", round (_t / (count HMT_DEF) * 100), round (_mx * 100), '
        '_n, HMT_TIR, HMT_TIRA]) call HMT_EMIT;')


def etat():
    r = q(LIRE, r'K (\d+) (\d+) (\d+) (\d+) (\d+)')
    if not r:
        return None
    return (int(r.group(1)) / 100.0, int(r.group(2)) / 100.0,
            int(r.group(3)), int(r.group(4)), int(r.group(5)))


print()
print('  %6s %10s %8s %10s %10s %10s' % ('t', 'moyenne', 'max', 'alertes', 'tirs def', 'tirs att'))
for t in (0, 10):
    if t:
        time.sleep(10)
    e = etat()
    if e:
        print('  %5ds %9.2f %7.2f %10d %10d %10d  (avant le tir)' % (t, e[0], e[1], e[2], e[3], e[4]))

# REVEAL EST OBLIGATOIRE : sans revelation, le tireur ne connait pas sa cible et refuse de
# faire feu. Recette du banc de suppression du 28/07, omise a la premiere tentative — zero tir
# mesure. On repete l ordre jusqu a obtenir au moins un coup, puis on arrete immediatement.
ORDRE = ('HMT_ATT reveal [(HMT_DEF select 1), 4]; HMT_ATT doWatch (HMT_DEF select 1); '
         'HMT_ATT doTarget (HMT_DEF select 1); HMT_ATT doSuppressiveFire (HMT_DEF select 1);')
tire = 0
for essai in range(8):
    b.send(ORDRE, wait=False)
    time.sleep(2)
    e = etat()
    if e and e[4] > 0:
        tire = e[4]
        break
print('  -> tirs obtenus avant arret de l ordre : %d (essais %d)' % (tire, essai + 1))
for t, dt in ((3, 3), (6, 3), (10, 4), (20, 10), (40, 20), (70, 30), (110, 40), (170, 60)):
    time.sleep(dt)
    e = etat()
    if e:
        print('  %5ds %9.2f %7.2f %10d %10d %10d' % (t, e[0], e[1], e[2], e[3], e[4]), flush=True)

b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL; HMT_AL=[];', wait=False)
b.close()
print('Q8_DONE')
