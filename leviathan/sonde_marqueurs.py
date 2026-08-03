#!/usr/bin/env python3
"""sonde_marqueurs.py — pourquoi les marqueurs du banc ne se creent pas ?

Ceux poses a la main pres du joueur marchent (3 sur 3). Ceux du banc n'en creent aucun.
La seule difference est la BOUCLE sur les unites : nom construit par format, position
prise sur l'objet. On teste donc les deux etapes separement, au meme endroit, pour voir
laquelle echoue.
"""
import sys, time
sys.path.insert(0, '/home/younes/arma3-marl'); sys.path.insert(0, '/home/younes/arma3-marl/leviathan')
from native_bridge import NativeBridge
import theatre

Q = chr(34); P = chr(37)
b = NativeBridge(port=theatre.use('altis').PORT)
b.send('{ deleteMarker _x } forEach (allMapMarkers select { (_x find ' + Q + 'sonde' + Q + ') == 0 });')
time.sleep(1)

# --- etape 1 : deux unites au banc, comme le fait le vrai banc ---
c = ('HMT_SONDE = []; '
     'private _g = createGroup east; '
     'private _u1 = _g createUnit [' + Q + 'O_Soldier_F' + Q + ', [23000,17400,0], [], 0, ' + Q + 'NONE' + Q + ']; '
     '_u1 setPosATL [23000,17400,0]; _u1 disableAI ' + Q + 'PATH' + Q + '; _u1 allowDamage false; '
     'private _u2 = _g createUnit [' + Q + 'O_Soldier_F' + Q + ', [23150,17400,0], [], 0, ' + Q + 'NONE' + Q + ']; '
     '_u2 setPosATL [23150,17400,0]; _u2 disableAI ' + Q + 'PATH' + Q + '; _u2 allowDamage false; '
     'HMT_SONDE pushBack _u1; HMT_SONDE pushBack _u2; '
     '(format [' + Q + 'U ' + P + '1' + Q + ', count HMT_SONDE]) call HMT_EMIT;')
r = b.query(c, r'U (\d+)', want=1, timeout=60)
print('1. unites posees au banc : %s' % (r[-1].group(1) if r else 'ECHEC'))
if not r:
    sys.exit(1)
time.sleep(2)

# --- etape 2 : un marqueur a position FIXE (sans boucle) ---
c2 = ('private _m = createMarker [' + Q + 'sonde_fixe' + Q + ', [23000,17400]]; '
      '_m setMarkerType ' + Q + 'mil_dot' + Q + '; _m setMarkerColor ' + Q + 'ColorRed' + Q + '; '
      '_m setMarkerSize [1.5, 1.5]; _m setMarkerText ' + Q + 'BANC' + Q + '; '
      '(format [' + Q + 'A ' + P + '1' + Q + ', count (allMapMarkers select { (_x find ' + Q + 'sonde' + Q + ') == 0 })]) call HMT_EMIT;')
r2 = b.query(c2, r'A (\d+)', want=1, timeout=30)
print('2. marqueur a position fixe : %s' % (r2[-1].group(1) if r2 else 'ECHEC'))

# --- etape 3 : marqueurs par BOUCLE sur les unites, comme le banc ---
c3 = ('{ private _m = createMarker [format [' + Q + 'sonde_b' + P + '1' + Q + ', _forEachIndex], getPos _x]; '
      '  _m setMarkerType ' + Q + 'mil_dot' + Q + '; _m setMarkerColor ' + Q + 'ColorBlue' + Q + '; '
      '  _m setMarkerSize [1.5, 1.5]; _m setMarkerText format [' + Q + 'boucle ' + P + '1' + Q + ', _forEachIndex]; '
      '} forEach HMT_SONDE; '
      '(format [' + Q + 'B ' + P + '1' + Q + ', count (allMapMarkers select { (_x find ' + Q + 'sonde' + Q + ') == 0 })]) call HMT_EMIT;')
r3 = b.query(c3, r'B (\d+)', want=1, timeout=30)
print('3. marqueurs par boucle    : %s  (2 de plus attendus)' % (r3[-1].group(1) if r3 else 'ECHEC'))

# --- ce que le serveur voit finalement ---
r4 = b.query('private _o = ' + Q + Q + '; { _o = _o + format [' + Q + P + '1@' + P + '2,' + P + '3|' + Q +
             ', _x, round ((getMarkerPos _x) select 0), round ((getMarkerPos _x) select 1)] } '
             'forEach (allMapMarkers select { (_x find ' + Q + 'sonde' + Q + ') == 0 }); '
             '(format [' + Q + 'L ' + P + '1' + Q + ', _o]) call HMT_EMIT;', r'L (.*)', want=1, timeout=25)
print('4. liste vue par le serveur :')
if r4:
    for t in r4[-1].group(1).strip().rstrip('|').split('|'):
        if t.strip():
            print('     ' + t)
b.send('{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_SONDE; HMT_SONDE = []; '
       '{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;')
b.close()
print()
print('>>> Regarde ta carte vers 23000/17400 (plein est, cote Kavala) :')
print('    un point ROUGE "BANC" et deux points BLEUS "boucle 0" et "boucle 1".')
