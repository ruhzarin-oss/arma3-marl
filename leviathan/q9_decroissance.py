#!/usr/bin/env python3
"""q9_decroissance.py — LA MEMOIRE : combien de temps l alerte dure-t-elle si on CESSE ?

Q8 a mesure le prix d un tir : 1,35 sur 4 en trois secondes, propage aux quatre defenseurs,
sature a 4,00 en dix secondes. Mais le plateau observe ensuite ne mesurait rien : l attaquant
n avait jamais cesse de tirer, 302 coups en 170 secondes.

Ici on coupe net. Recette du banc de suppression pour ARRETER un tireur, ligne 336 :
    doWatch objNull ; doTarget objNull ; setCombatMode BLUE
Puis on l ecarte hors de portee de detection passive — mesuree a 100 m — et on regarde
combien de temps la position reste alertee.

C est la duree qui dira si l alerte est une ressource recuperable ou definitive.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl')
sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

T = theatre.use('altis')
b = NativeBridge(port=T.PORT)
fx, fy = T.FOB
D = 100
LOIN = 400


def q(sqf, motif, timeout=30):
    r = b.query(sqf, motif, want=1, timeout=timeout)
    return r[-1] if r else None


s = 'if (!isNil "HMT_AL") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL }; '
s += 'HMT_AL=[]; HMT_DEF=[]; HMT_TIR=0; HMT_TIRA=0; HMT_GD = createGroup east; '
for i in range(4):
    x = fx + (i - 2) * 30
    s += ('_u = HMT_GD createUnit ["O_Soldier_F", [%d,%d,0], [], 0, "NONE"]; '
          '_u setPosATL [%d,%d,0]; _u setSkill 0.7; _u setBehaviour "COMBAT"; '
          '_u setCombatMode "RED"; _u allowDamage false; _u setVehicleAmmo 1; '
          '_u addEventHandler ["Fired", { HMT_TIR = HMT_TIR + 1 }]; '
          'HMT_AL pushBack _u; HMT_DEF pushBack _u; ' % (x, fy, x, fy))
s += ('HMT_GA = createGroup west; '
      'HMT_ATT = HMT_GA createUnit ["B_Soldier_F", [%d,%d,0], [], 0, "NONE"]; '
      'HMT_ATT setPosATL [%d,%d,0]; HMT_ATT setSkill 0.7; HMT_ATT setUnitPos "UP"; '
      'HMT_ATT setBehaviour "COMBAT"; HMT_ATT setCombatMode "RED"; '
      'HMT_ATT disableAI "AUTOTARGET"; HMT_ATT disableAI "PATH"; HMT_ATT allowDamage false; '
      'HMT_ATT setVehicleAmmo 1; '
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


# --- on alerte ---
ORDRE = ('HMT_ATT reveal [(HMT_DEF select 1), 4]; HMT_ATT doWatch (HMT_DEF select 1); '
         'HMT_ATT doTarget (HMT_DEF select 1); HMT_ATT doFire (HMT_DEF select 1);')
for essai in range(8):
    b.send(ORDRE, wait=False)
    time.sleep(2)
    e = etat()
    if e and e[4] > 0:
        break
e = etat()
print('  alerte obtenue : connaissance %.2f | %d tirs attaquant' % (e[0], e[4]) if e else '  MUET')

# --- ON COUPE NET, recette du banc de suppression ---
b.send('HMT_ATT doWatch objNull; HMT_ATT doTarget objNull; HMT_ATT setCombatMode "BLUE"; '
       'HMT_ATT disableAI "AUTOTARGET"; HMT_ATT setPosATL [%d,%d,0];' % (fx, fy - LOIN), wait=False)
time.sleep(3)
e = etat()
print('  tir coupe et attaquant ecarte a %d m | tirs attaquant figes a %d' % (LOIN, e[4]) if e else '  MUET')
base = e[4] if e else 0

print()
print('  %6s %10s %8s %10s %12s' % ('t', 'moyenne', 'max', 'alertes', 'tirs att.'))
for t, dt in ((0, 0), (15, 15), (30, 15), (60, 30), (90, 30), (120, 30),
              (180, 60), (240, 60), (300, 60)):
    if dt:
        time.sleep(dt)
    e = etat()
    if e:
        drapeau = '  (il retire !)' if e[4] > base else ''
        print('  %5ds %9.2f %7.2f %10d %12d%s' % (t, e[0], e[1], e[2], e[4], drapeau), flush=True)
        if e[1] < 0.05:
            print('  -> RETOMBE A ZERO a t=%ds' % t)
            break

b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_AL; HMT_AL=[];', wait=False)
b.close()
print('Q9_DONE')
