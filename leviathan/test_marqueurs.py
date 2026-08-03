#!/usr/bin/env python3
"""test_marqueurs.py — les points de couleur existent-ils VRAIMENT ?

Je lui ai dit trois fois de regarder sa carte sans jamais verifier qu'un seul marqueur
etait cree. C'est exactement le defaut silencieux qu'on traque depuis ce matin : un
script qui ne leve aucune erreur et ne fait rien.

On pose donc trois marqueurs de controle, on RELIT ce que le serveur en dit, et on en
met un a cote du joueur pour qu'il n'ait pas a chercher a 8 km.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
b = NativeBridge(port=theatre.use('altis').PORT)

# ou est le joueur ?
r = b.query('private _p = objNull; { if (isPlayer _x) then { _p = _x } } forEach allUnits; '
            '(format [' + Q + 'J ' + P + '1 ' + P + '2' + Q + ', round ((getPos _p) select 0), round ((getPos _p) select 1)]) call HMT_EMIT;',
            r'J (-?\d+) (-?\d+)', want=1, timeout=25)
if not r:
    print('pas de reponse'); sys.exit(1)
jx, jy = int(r[-1].group(1)), int(r[-1].group(2))
print('joueur en (%d, %d)' % (jx, jy))

# trois marqueurs de controle : un SUR lui, deux a 200 m
poses = [('hmttest_toi', jx, jy, 'ColorGreen', 'TOI'),
         ('hmttest_a', jx + 200, jy, 'ColorRed', 'test ROUGE 200m est'),
         ('hmttest_b', jx, jy + 200, 'ColorBlue', 'test BLEU 200m nord')]
c = '{ deleteMarker _x } forEach (allMapMarkers select { _x find ' + Q + 'hmttest' + Q + ' == 0 }); '
for nom, x, y, col, txt in poses:
    c += ('private _m = createMarker [' + Q + nom + Q + ', [' + str(x) + ',' + str(y) + ']]; '
          '_m setMarkerType ' + Q + 'mil_dot' + Q + '; '
          '_m setMarkerColor ' + Q + col + Q + '; '
          '_m setMarkerSize [1.2, 1.2]; '
          '_m setMarkerText ' + Q + txt + Q + '; ')
c += ('(format [' + Q + 'MK ' + P + '1' + Q + ', count (allMapMarkers select { _x find ' + Q + 'hmttest' + Q + ' == 0 })]) call HMT_EMIT;')
rr = b.query(c, r'MK (\d+)', want=1, timeout=30)
n = int(rr[-1].group(1)) if rr else -1
print('marqueurs relus par le serveur : %d sur 3' % n)

# et ce que le serveur dit de chacun
r3 = b.query('private _o = ' + Q + Q + '; '
             '{ _o = _o + format [' + Q + P + '1@' + P + '2,' + P + '3|' + Q + ', _x, round ((getMarkerPos _x) select 0), round ((getMarkerPos _x) select 1)] } '
             'forEach (allMapMarkers select { _x find ' + Q + 'hmttest' + Q + ' == 0 }); '
             '(format [' + Q + 'L ' + P + '1' + Q + ', _o]) call HMT_EMIT;', r'L (.*)', want=1, timeout=25)
if r3:
    for t in r3[-1].group(1).strip().rstrip('|').split('|'):
        if t.strip():
            print('   ' + t)
b.close()
print()
if n == 3:
    print('>>> les marqueurs SONT crees cote serveur.')
    print('    Ouvre ta carte : un point VERT sur toi, un ROUGE 200 m a l est, un BLEU 200 m au nord.')
    print('    Si tu ne vois rien, le probleme est la DIFFUSION vers le client, pas la creation.')
else:
    print('>>> les marqueurs ne sont PAS crees : le probleme est cote serveur.')
